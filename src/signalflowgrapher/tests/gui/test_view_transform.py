"""
Tests of the ViewTransform (step 3 of the V3.0 plan).

The application itself still runs at zoom 1 / offset (0, 0) in this step.
These tests set other values on the GraphField's transform to prove that
every place that converts between model (world) and screen coordinates
does so: widget placement, mouse input, grid snapping, paste, pan.
The sizes of glyphs (node circle, pen widths, font) do not scale yet; that
is step 5.
"""
import math
from unittest import TestCase

from PySide6.QtCore import QPoint, QPointF, Qt

from signalflowgrapher.gui.grid import GRID_SIZE
from signalflowgrapher.gui.view_transform import ViewTransform
from signalflowgrapher.tests.gui import test_gui_operations as ops
from signalflowgrapher.tests.gui.consistency import check_consistency
from signalflowgrapher.tests.gui.snapshot import (
    geometry_snapshot, snapshots_close)

VIEWS = [
    (1.0, (0, 0)),          # V2.0
    (1.0, (40, -30)),       # only shifted
    (2.0, (0, 0)),          # not available in the app (max 100%) but valid
    (0.5, (0, 0)),
    (0.5, (37, -12)),
    (0.25, (100, 50)),
    (0.3, (-20, 15)),       # zoom that is not a power of two
    (0.1, (5, 5)),          # smallest zoom of the plan
]


class TestViewTransformClass(TestCase):
    def test_default_is_identity(self):
        v = ViewTransform()
        self.assertEqual(1.0, v.zoom)
        self.assertEqual(QPointF(0, 0), v.offset)
        self.assertTrue(v.is_identity)
        p = QPointF(123.5, -7.25)
        self.assertEqual(p, v.to_screen(p))
        self.assertEqual(p, v.to_world(p))
        self.assertEqual(7.5, v.to_world_delta(7.5))
        self.assertEqual(7.5, v.to_screen_delta(7.5))

    def test_known_values(self):
        v = ViewTransform(0.5, QPointF(10, 20))
        self.assertEqual(QPointF(55, 65), v.to_screen(QPointF(90, 90)))
        self.assertEqual(QPointF(90, 90), v.to_world(QPointF(55, 65)))
        self.assertEqual(50.0, v.to_screen_delta(100))
        self.assertEqual(100.0, v.to_world_delta(50))
        self.assertFalse(v.is_identity)

    def test_round_trip(self):
        for zoom, offset in VIEWS:
            v = ViewTransform(zoom, QPointF(*offset))
            for p in (QPointF(0, 0), QPointF(90, 150), QPointF(-33.5, 1e4),
                      QPointF(0.1, 0.7)):
                back = v.to_world(v.to_screen(p))
                self.assertAlmostEqual(p.x(), back.x(), places=9)
                self.assertAlmostEqual(p.y(), back.y(), places=9)

    def test_screen_point_is_rounded_down(self):
        v = ViewTransform(0.5)
        self.assertEqual(QPoint(97, -1), v.to_screen_point(QPointF(195, -1)))
        self.assertEqual(QPoint(97, -2), v.to_screen_point(QPointF(195, -3)))
        self.assertEqual(QPoint(98, 0), v.to_screen_point(QPointF(196.9, 1)))

    def test_move_by_whole_pixels_is_an_exact_translation(self):
        v = ViewTransform(1.0)
        for p in (QPointF(10.5, -3.25), QPointF(-0.5, 0.5), QPointF(7, 7)):
            for d in (-5, -1, 1, 4, 100):
                a = v.to_screen_point(p)
                b = v.to_screen_point(QPointF(p.x() + d, p.y() + d))
                self.assertEqual(a + QPoint(d, d), b)

    def test_changed_signal(self):
        v = ViewTransform()
        count = []
        v.changed.connect(lambda: count.append(1))
        v.set(0.5)
        self.assertEqual(1, len(count))
        v.set(0.5)                              # same value: no signal
        v.set(0.5, QPointF(0, 0))
        self.assertEqual(1, len(count))
        v.set(offset=QPointF(3, 4))             # zoom stays
        self.assertEqual(2, len(count))
        self.assertEqual(0.5, v.zoom)
        v.reset()
        self.assertEqual(3, len(count))
        self.assertTrue(v.is_identity)
        v.reset()
        self.assertEqual(3, len(count))

    def test_invalid_zoom_is_rejected(self):
        for bad in (0, -1, -0.5, float("nan")):
            with self.assertRaises(ValueError, msg=repr(bad)):
                ViewTransform(bad)
        v = ViewTransform()
        with self.assertRaises(ValueError):
            v.set(0)
        self.assertEqual(1.0, v.zoom)

    def test_offset_is_a_copy(self):
        v = ViewTransform(1.0, QPointF(1, 2))
        o = v.offset
        o.setX(99)
        self.assertEqual(QPointF(1, 2), v.offset)


class ViewTestCase(ops.GuiTestCase):
    def setUp(self):
        super().setUp()
        h = self.h
        self.a = h.double_click(100, 100)
        self.b = h.double_click(400, 220)
        self.c = h.double_click(250, 400)
        self.ab = h.ctrl_click_branch(self.a, self.b)
        self.bc = h.ctrl_click_branch(self.b, self.c)
        h.drag_label(self.ab, 20, 20)
        h.drag_label(self.a, -30, 30)
        h.select_branch(self.ab)                 # handles are visible

    def set_view(self, zoom, offset=(0, 0)):
        self.h.set_view(zoom, offset)

    def world_of_click(self, sx, sy):
        return self.h.view.to_world(QPointF(sx, sy))

    def assert_on_grid(self, x, y, msg=""):
        gx, gy = self.h.model.get_grid_position()
        self.assertEqual(0, (x - gx) % GRID_SIZE, "x off grid " + msg)
        self.assertEqual(0, (y - gy) % GRID_SIZE, "y off grid " + msg)


class TestWidgetPlacement(ViewTestCase):
    def test_widgets_follow_the_view_for_every_zoom_and_offset(self):
        before_model = ops.coords(self.h)
        undo_depth = self.h.command_handler.can_undo.get()
        for zoom, offset in VIEWS:
            with self.subTest(zoom=zoom, offset=offset):
                self.set_view(zoom, offset)
                self.ok("view %s %s" % (zoom, offset))
                self.assertEqual(before_model, ops.coords(self.h),
                                 "the model must not depend on the view")
                self.assertEqual(undo_depth,
                                 self.h.command_handler.can_undo.get(),
                                 "a view change is not an undoable command")

    def test_node_widget_centre_is_the_mapped_node_position(self):
        self.set_view(0.5, (10, 20))
        for node in (self.a, self.b, self.c):
            expected = QPoint(math.floor(node.x * 0.5 + 10),
                              math.floor(node.y * 0.5 + 20))
            self.assertEqual(QPointF(expected),
                             self.h.widget_of(node).get_center())

    def test_back_to_identity_gives_the_original_geometry(self):
        original = geometry_snapshot(self.h)
        for zoom, offset in VIEWS:
            self.set_view(zoom, offset)
        self.h.view.reset()
        self.h.process_events()
        self.assertEqual([], snapshots_close(original,
                                             geometry_snapshot(self.h), 0))
        self.ok("after the round trip")

    def test_label_offsets_scale_with_the_zoom(self):
        self.set_view(0.5, (0, 0))
        node_center = self.h.widget_of(self.a).get_center()
        label = self.h.label_of(self.a)
        centre = QPointF(label.x() + label.width() / 2,
                         label.y() + label.height() / 2)
        self.assertAlmostEqual(node_center.x() + self.a.label_dx * 0.5,
                               centre.x(), delta=1.5)
        self.assertAlmostEqual(node_center.y() + self.a.label_dy * 0.5,
                               centre.y(), delta=1.5)

    def test_new_widgets_are_created_at_the_mapped_position(self):
        self.set_view(0.25, (100, 50))
        n = self.h.double_click(300, 250)
        self.ok("node created while zoomed")
        br = self.h.ctrl_click_branch(self.a, n)
        self.ok("branch created while zoomed")
        self.assertIn(br, self.h.branches)

    def test_pan_is_cheap_also_when_zoomed(self):
        self.set_view(0.5, (10, 10))
        self.h.pan(40, 20)
        self.ok("pan while zoomed")


class TestInputConversion(ViewTestCase):
    def test_double_click_creates_the_node_at_the_world_position(self):
        for zoom, offset in VIEWS:
            with self.subTest(zoom=zoom, offset=offset):
                self.set_view(zoom, offset)
                sx, sy = 321, 267
                n = self.h.double_click(sx, sy)
                world = self.world_of_click(sx, sy)
                self.assert_on_grid(n.x, n.y, "double click")
                self.assertLessEqual(abs(n.x - world.x()), GRID_SIZE / 2 + 2)
                self.assertLessEqual(abs(n.y - world.y()), GRID_SIZE / 2 + 2)
                self.assertIsInstance(n.x, int)
                self.ok("double click at %s %s" % (zoom, offset))

    def test_dragging_a_node_moves_it_by_the_world_distance(self):
        for zoom, offset in VIEWS:
            with self.subTest(zoom=zoom, offset=offset):
                self.set_view(zoom, offset)
                x, y = self.c.x, self.c.y
                # 5 grid cells in x, 2 in y, as screen pixels
                self.h.drag_node(self.c, round(150 * zoom), round(60 * zoom))
                self.assert_on_grid(self.c.x, self.c.y)
                self.assertAlmostEqual(x + 150, self.c.x,
                                       delta=GRID_SIZE if zoom < 0.5 else 0)
                self.assertAlmostEqual(y + 60, self.c.y,
                                       delta=GRID_SIZE if zoom < 0.5 else 0)
                self.ok("node drag at %s %s" % (zoom, offset))
                self.h.undo()
                self.assertEqual((x, y), (self.c.x, self.c.y))

    def test_free_move_is_exact_and_loses_nothing(self):
        """Ctrl: no grid. 1 px of the screen is 1 / zoom world units."""
        for zoom in (1.0, 0.5, 0.25, 0.3, 0.1):
            with self.subTest(zoom=zoom):
                self.set_view(zoom, (0, 0))
                self.h.field.on_ctrl_press()
                x, y = self.c.x, self.c.y
                self.h.drag_node(self.c, 30, 20, steps=30)  # 1 px at a time
                self.h.field.on_ctrl_release()
                self.assertEqual((x + round(30 / zoom), y + round(20 / zoom)),
                                 (self.c.x, self.c.y))
                self.assertIsInstance(self.c.x, int)
                self.ok("free move at %s" % zoom)

    def test_label_offsets_of_nodes_stay_integers(self):
        """The file format requires integer label offsets for nodes."""
        for zoom in (0.5, 0.3, 0.1):
            for ctrl in (False, True):
                with self.subTest(zoom=zoom, ctrl=ctrl):
                    self.set_view(zoom, (13, -7))
                    if ctrl:
                        self.h.field.on_ctrl_press()
                    self.h.drag_label(self.b, 17, -9, steps=7)
                    if ctrl:
                        self.h.field.on_ctrl_release()
                    self.assertIsInstance(self.b.label_dx, int)
                    self.assertIsInstance(self.b.label_dy, int)
                    self.ok("label drag")

    def test_label_drag_moves_the_offset_by_the_world_distance(self):
        self.set_view(0.5, (0, 0))
        self.h.field.on_ctrl_press()
        dx, dy = self.a.label_dx, self.a.label_dy
        self.h.drag_label(self.a, 20, 10)
        self.h.field.on_ctrl_release()
        self.assertEqual((dx + 40, dy + 20),
                         (self.a.label_dx, self.a.label_dy))

    def test_handle_drag_moves_the_spline_by_the_world_distance(self):
        self.set_view(0.5, (20, 20))
        self.h.field.on_ctrl_press()
        handle = self.h.selected_handles()[0]
        s1 = (self.ab.spline1_x, self.ab.spline1_y)
        s2 = (self.ab.spline2_x, self.ab.spline2_y)
        self.h.drag_handle(handle, 10, 6)       # screen px; mirrored
        self.h.field.on_ctrl_release()
        self.assertEqual((s1[0] - 20, s1[1] - 12),
                         (self.ab.spline1_x, self.ab.spline1_y))
        self.assertEqual(s2, (self.ab.spline2_x, self.ab.spline2_y))
        self.ok("handle drag while zoomed")

    def test_handle_knob_snaps_to_the_grid_when_zoomed(self):
        self.set_view(0.5, (20, 20))
        handle = self.h.selected_handles()[1]
        self.h.drag_handle(handle, 33, 21)
        knob = self.h.selected_handles()[1].get_world_center()
        self.assert_on_grid(round(knob.x()), round(knob.y()), "knob")

    def test_pan_moves_the_model_by_the_world_distance(self):
        for zoom in (0.5, 0.25, 0.3):
            with self.subTest(zoom=zoom):
                self.set_view(zoom, (0, 0))
                x, y = self.a.x, self.a.y
                gx, gy = self.h.model.get_grid_position()
                self.h.pan(30, 15, steps=30)        # 1 px at a time
                self.assertEqual((x + round(30 / zoom), y + round(15 / zoom)),
                                 (self.a.x, self.a.y))
                self.assertEqual((gx + round(30 / zoom), gy + round(15 / zoom)),
                                 tuple(self.h.model.get_grid_position()))
                self.ok("pan at %s" % zoom)

    def test_center_graph_while_zoomed(self):
        for zoom, offset in VIEWS:
            with self.subTest(zoom=zoom, offset=offset):
                self.set_view(zoom, offset)
                self.h.field.center_graph()
                self.h.process_events()
                widgets = list(self.h.model_widget_map.values())
                cx = (min(w.x() for w in widgets)
                      + max(w.x() + w.width() for w in widgets)) / 2
                cy = (min(w.y() for w in widgets)
                      + max(w.y() + w.height() for w in widgets)) / 2
                self.assertAlmostEqual(self.h.field.width() / 2, cx,
                                       delta=max(2, zoom))
                self.assertAlmostEqual(self.h.field.height() / 2, cy,
                                       delta=max(2, zoom))
                self.ok("center graph")

    def test_paste_goes_to_the_world_position_of_the_mouse(self):
        for zoom, offset in ((0.5, (0, 0)), (0.5, (37, -12)), (0.25, (100, 50))):
            with self.subTest(zoom=zoom, offset=offset):
                self.set_view(zoom, offset)
                self.h.select(self.a, self.b, self.ab)
                self.h.copy()
                known = set(self.h.nodes)
                self.h.paste_at(300, 200)
                new = [n for n in self.h.nodes if n not in known]
                self.assertEqual(2, len(new))
                world = self.world_of_click(300, 200)
                gx, gy = self.h.model.get_grid_position()
                expect_x = gx + GRID_SIZE * round((world.x() - gx - 2)
                                                  / GRID_SIZE)
                expect_y = gy + GRID_SIZE * round((world.y() - gy - 2)
                                                  / GRID_SIZE)
                self.assertEqual((expect_x, expect_y),
                                 (min(n.x for n in new),
                                  min(n.y for n in new)))
                self.ok("paste while zoomed")

    def test_undo_redo_while_zoomed_and_after_changing_the_view(self):
        self.set_view(0.5, (10, 10))
        before = ops.coords(self.h)
        self.h.drag_node(self.b, 60, 30)
        after = ops.coords(self.h)
        self.set_view(0.25, (0, 0))                 # view changes, then undo
        self.h.undo()
        self.assertEqual(before, ops.coords(self.h))
        self.ok("undo")
        self.set_view(1.0, (0, 0))
        self.h.redo()
        self.assertEqual(after, ops.coords(self.h))
        self.ok("redo")

    def test_saved_file_does_not_depend_on_the_view(self):
        import json
        import os
        import tempfile
        texts = []
        for zoom, offset in ((1.0, (0, 0)), (0.5, (37, -12)), (0.1, (5, 5))):
            self.set_view(zoom, offset)
            with tempfile.TemporaryDirectory() as tmp:
                p = os.path.join(tmp, "g.sfg")
                self.h.save(p)
                with open(p, encoding="utf-8") as f:
                    texts.append(json.load(f))
        self.assertEqual(texts[0], texts[1])
        self.assertEqual(texts[0], texts[2])


class TestGridDrawing(TestCase):
    """The grid lines are drawn where the view maps the world grid."""

    def setUp(self):
        from signalflowgrapher.tests.gui.harness import Harness
        self.h = Harness(400, 300)

    def tearDown(self):
        self.h.close()

    @staticmethod
    def expected_lines(zoom, view_offset, pan, extent):
        """Screen positions of the grid lines in one direction."""
        lines = set()
        world_offset = pan % GRID_SIZE
        first = -int(abs(view_offset) / (GRID_SIZE * zoom)) - 5
        last = int(extent / (GRID_SIZE * zoom)) + int(
            abs(view_offset) / (GRID_SIZE * zoom)) + 5
        for k in range(first, last):
            screen = zoom * (world_offset + k * GRID_SIZE) + view_offset
            x = math.floor(screen + 0.5)
            if 0 <= screen and x < extent:
                lines.add(x)
        return lines

    def detected_lines(self, expected_x, expected_y):
        """
        Positions of the drawn vertical and horizontal lines, read from the
        picture: along a row that has no horizontal line every pixel that
        differs from the background is on a vertical line, and the other
        way round.
        """
        img = self.h.private("grid_widget").grab().toImage()
        width, height = img.width(), img.height()
        free_x = next(x for x in range(width) if x not in expected_x)
        free_y = next(y for y in range(height) if y not in expected_y)
        background = img.pixel(free_x, free_y)
        columns = {x for x in range(width)
                   if img.pixel(x, free_y) != background}
        rows = {y for y in range(height)
                if img.pixel(free_x, y) != background}
        return columns, rows

    def test_grid_lines_follow_zoom_offset_and_pan(self):
        for zoom, offset in VIEWS:
            for pan in ((0, 0), (13, 7)):
                with self.subTest(zoom=zoom, offset=offset, pan=pan):
                    self.h.model.set_grid_position(pan)
                    self.h.set_view(zoom, offset)
                    expected_x = self.expected_lines(zoom, offset[0],
                                                     pan[0], 400)
                    expected_y = self.expected_lines(zoom, offset[1],
                                                     pan[1], 300)
                    xs, ys = self.detected_lines(expected_x, expected_y)
                    self.assertEqual(expected_x, xs)
                    self.assertEqual(expected_y, ys)
