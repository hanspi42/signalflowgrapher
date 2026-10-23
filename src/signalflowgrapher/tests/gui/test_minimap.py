"""
Tests of the mini map (step 6 of the V3.0 plan).

The mini map shows all nodes and branches (no labels, no arrows) and a
rectangle for the part that the graph field shows; a click or drag moves the
view. It is drawn from the model.
"""
import os
import subprocess
import sys
import tempfile
from unittest import TestCase

from PySide6.QtCore import QPoint, QPointF, QRectF, QSettings, Qt
from PySide6.QtGui import QColor

from signalflowgrapher.gui.mini_map import MiniMapWidget
from signalflowgrapher.tests.gui import test_gui_operations as ops
from signalflowgrapher.tests.gui.consistency import (
    bezier_points, check_consistency)
from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.test_golden import (
    example_files, example_name)
from signalflowgrapher.tests.gui.test_view_transform import VIEWS
from signalflowgrapher.utils.settings import AppSettings


def luminance(image, x, y):
    c = QColor(image.pixel(x, y))
    return (c.red() + c.green() + c.blue()) / 3


class MiniMapTestCase(ops.GuiTestCase):
    def setUp(self):
        super().setUp()
        self.a = self.h.double_click(150, 150)
        self.b = self.h.double_click(630, 270)
        self.c = self.h.double_click(300, 450)
        self.ab = self.h.ctrl_click_branch(self.a, self.b)
        self.bc = self.h.ctrl_click_branch(self.b, self.c)
        self.h.drag_label(self.ab, 30, 20)
        self.h.field.set_minimap_visible(True)
        self.mm = self.h.field.minimap

    def picture(self):
        self.h.process_events()
        return self.mm.grab().toImage()

    def minimap_of(self, node_or_point):
        mapping = self.mm.mapping()
        if hasattr(node_or_point, "x") and not isinstance(node_or_point, QPointF):
            node_or_point = QPointF(node_or_point.x, node_or_point.y)
        return mapping.to_minimap(node_or_point)


class TestWhatTheMapShows(MiniMapTestCase):
    def test_the_rectangle_of_the_graph_contains_nodes_and_whole_curves(self):
        rect = self.mm.graph_rect()
        for node in self.h.nodes:
            self.assertTrue(rect.adjusted(-0.01, -0.01, 0.01, 0.01).contains(
                QPointF(node.x, node.y)))
        xs = [x for br in self.h.branches for x, y in bezier_points(br, 400)]
        ys = [y for br in self.h.branches for x, y in bezier_points(br, 400)]
        xs += [n.x for n in self.h.nodes]
        ys += [n.y for n in self.h.nodes]
        self.assertAlmostEqual(min(xs), rect.left(), delta=0.5)
        self.assertAlmostEqual(max(xs), rect.right(), delta=0.5)
        self.assertAlmostEqual(min(ys), rect.top(), delta=0.5)
        self.assertAlmostEqual(max(ys), rect.bottom(), delta=0.5)

    def test_a_curve_that_bulges_beyond_its_nodes_is_inside_the_rectangle(self):
        node = self.h.nodes[0]
        loop_node = self.h.double_click(900, 90)
        self.h.select(loop_node)
        self.h.click(self.h.widget_of(loop_node), Qt.ControlModifier)
        loop = [b for b in self.h.branches if b.start is b.end][0]
        rect = self.mm.graph_rect()
        for x, y in bezier_points(loop, 200):
            self.assertTrue(rect.adjusted(-0.5, -0.5, 0.5, 0.5).contains(
                QPointF(x, y)))
        self.assertGreater(rect.top(), -10 ** 6)
        self.ok("loop")

    def test_empty_graph_has_no_graph_rectangle(self):
        self.h.io.new_graph()
        self.h.process_events()
        self.assertIsNone(self.mm.graph_rect())
        # the map then shows the part that is shown, and nothing else
        self.assertEqual(self.mm.visible_rect(), self.mm.world_rect())
        self.ok("empty graph")

    def test_a_single_node_is_shown(self):
        self.h.io.new_graph()
        node = self.h.double_click(300, 300)
        rect = self.mm.graph_rect()
        self.assertEqual((node.x, node.y), (rect.left(), rect.top()))
        self.assertEqual((0, 0), (rect.width(), rect.height()))
        self.ok("one node")

    def test_labels_do_not_count(self):
        before = self.mm.graph_rect()
        self.h.drag_label(self.a, -90, -300)
        self.h.drag_label(self.bc, 400, 400)
        self.assertEqual(before, self.mm.graph_rect())

    def test_the_dots_of_the_nodes_are_not_cut_off_at_the_border(self):
        self.assertGreaterEqual(MiniMapWidget.PADDING,
                                MiniMapWidget.NODE_RADIUS + 1)

    def test_the_part_that_is_shown_is_the_graph_field_in_world_units(self):
        for zoom, offset in VIEWS:
            with self.subTest(zoom=zoom, offset=offset):
                self.h.set_view(zoom, offset)
                shown = self.mm.visible_rect()
                self.assertAlmostEqual(self.h.field.width() / zoom,
                                       shown.width(), places=6)
                self.assertAlmostEqual(self.h.field.height() / zoom,
                                       shown.height(), places=6)
                self.assertAlmostEqual(-offset[0] / zoom, shown.left(),
                                       places=6)
                self.assertAlmostEqual(-offset[1] / zoom, shown.top(),
                                       places=6)

    def test_everything_is_inside_the_map_at_every_zoom_and_offset(self):
        for zoom, offset in VIEWS + [(0.1, (-4000, 900)), (2.0, (-3000, -50))]:
            with self.subTest(zoom=zoom, offset=offset):
                self.h.set_view(zoom, offset)
                self.assertEqual([], check_consistency(self.h))

    def test_the_content_fills_the_map_in_one_direction(self):
        for zoom, offset in VIEWS:
            with self.subTest(zoom=zoom, offset=offset):
                self.h.set_view(zoom, offset)
                rect = self.mm.world_rect()
                scale = self.mm.mapping().scale
                available = (self.mm.width() - 2 * MiniMapWidget.PADDING,
                             self.mm.height() - 2 * MiniMapWidget.PADDING)
                self.assertTrue(
                    abs(rect.width() * scale - available[0]) < 0.01
                    or abs(rect.height() * scale - available[1]) < 0.01)

    def test_the_map_follows_changes_of_the_graph(self):
        before = self.mm.graph_rect()
        far = self.h.double_click(900, 600)
        self.assertGreater(self.mm.graph_rect().right(), before.right() - 1)
        self.h.drag_node(far, 300, 120)
        self.assertNotEqual(before, self.mm.graph_rect())
        self.h.undo()
        self.h.undo()
        self.assertEqual(before, self.mm.graph_rect())


class TestHowTheMapIsDrawn(MiniMapTestCase):
    """The picture of the map is examined."""

    def test_every_node_is_a_dark_dot(self):
        image = self.picture()
        for node in self.h.nodes:
            p = self.minimap_of(node)
            self.assertLess(luminance(image, round(p.x()), round(p.y())), 110,
                            "node at %s" % p)

    def test_every_branch_is_visible_along_its_whole_curve(self):
        image = self.picture()
        mapping = self.mm.mapping()
        for branch in self.h.branches:
            for x, y in bezier_points(branch, 8)[1:-1]:
                p = mapping.to_minimap(QPointF(x, y))
                darkest = min(luminance(image, int(p.x()) + dx, int(p.y()) + dy)
                              for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                self.assertLess(darkest, 150, "curve point %s" % p)

    def test_the_map_of_all_examples_shows_all_nodes_and_branches(self):
        for path in example_files():
            with self.subTest(example=example_name(path)):
                h = Harness(900, 600)
                try:
                    h.load(path)
                    h.field.on_esc_press()
                    h.field.set_minimap_visible(True)
                    h.process_events()
                    mm = h.field.minimap
                    image = mm.grab().toImage()
                    mapping = mm.mapping()
                    for node in h.nodes:
                        p = mapping.to_minimap(QPointF(node.x, node.y))
                        self.assertLess(
                            luminance(image, round(p.x()), round(p.y())), 130)
                    for branch in h.branches:
                        x, y = bezier_points(branch, 4)[2]
                        p = mapping.to_minimap(QPointF(x, y))
                        darkest = min(
                            luminance(image, int(p.x()) + dx, int(p.y()) + dy)
                            for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                        self.assertLess(darkest, 150)
                finally:
                    h.close()

    def test_branches_have_no_arrows(self):
        """A long straight branch is as thick in the middle as at its ends."""
        h = Harness(1000, 500)
        try:
            a = h.double_click(150, 150)
            b = h.double_click(900, 150)
            h.ctrl_click_branch(a, b)
            h.field.set_minimap_visible(True)
            h.process_events()
            mm = h.field.minimap
            image = mm.grab().toImage()
            start = mm.mapping().to_minimap(QPointF(a.x, a.y))
            end = mm.mapping().to_minimap(QPointF(b.x, b.y))

            # dark pixels in a band around the line (the blue rectangle of
            # the shown part is light and does not count as ink)
            def thickness(x):
                return sum(1 for y in range(int(start.y()) - 12,
                                            int(start.y()) + 13)
                           if luminance(image, x, y) < 110)
            xs = list(range(int(start.x()) + 6, int(end.x()) - 6))
            widths = [thickness(x) for x in xs]
            self.assertGreater(len(xs), 100)
            self.assertGreaterEqual(min(widths), 1)       # a line all along
            self.assertLessEqual(max(widths), 3, set(widths))   # no arrow
        finally:
            h.close()

    def test_names_and_weights_are_not_drawn_the_picture_does_not_change(self):
        before = self.picture()
        for node in self.h.nodes:
            self.h.controller.set_node_name(node, "Name of node")
        for branch in self.h.branches:
            self.h.controller.set_branch_weight(branch, "w")
        self.h.process_events()
        self.assertEqual(before, self.picture())

    def test_moving_labels_does_not_change_the_picture(self):
        before = self.picture()
        self.h.drag_label(self.a, -120, -90)
        self.h.drag_label(self.bc, 300, 200)
        self.assertEqual(before, self.picture())

    def test_the_rectangle_of_the_shown_part_is_drawn_where_it_is_reported(self):
        for zoom, offset in VIEWS:
            with self.subTest(zoom=zoom, offset=offset):
                self.h.set_view(zoom, offset)
                shown = self.mm.visible_rect_in_minimap()
                image = self.picture()
                row = int(min(max(shown.center().y(), 3), self.mm.height() - 4))

                def blue(x):
                    c = QColor(image.pixel(x, row))
                    return c.blue() - c.red() > 40
                columns = [x for x in range(self.mm.width()) if blue(x)]
                self.assertTrue(columns, "no rectangle in the picture")
                if shown.left() >= 2:
                    self.assertAlmostEqual(shown.left(), min(columns),
                                           delta=2.0)
                if shown.right() <= self.mm.width() - 3:
                    self.assertAlmostEqual(shown.right(), max(columns),
                                           delta=2.0)

    def test_the_rectangle_is_in_the_picture_also_for_an_empty_graph(self):
        self.h.io.new_graph()
        self.h.process_events()
        image = self.picture()
        blue = [x for x in range(self.mm.width())
                if QColor(image.pixel(x, self.mm.height() // 2)).blue()
                - QColor(image.pixel(x, self.mm.height() // 2)).red() > 40]
        self.assertTrue(blue)

    def test_nothing_of_the_graph_underneath_shines_through(self):
        """
        A node whose dark ring lies under an empty part of the map is not
        visible in the picture of the graph field.
        """
        x = self.mm.x() + 3 + 9          # the ring is 9 pixels from the centre
        y = self.mm.y() + 3
        self.h.controller.create_node(x, y)
        self.h.process_events()
        image = self.h.field.grab().toImage()
        window = self.mm.palette().window().color()
        pixel = QColor(image.pixel(self.mm.x() + 3, self.mm.y() + 3))
        self.assertEqual((window.red(), window.green(), window.blue()),
                         (pixel.red(), pixel.green(), pixel.blue()))


class TestUsingTheMap(MiniMapTestCase):
    def shown_centre(self):
        shown = self.mm.visible_rect()
        return shown.center()

    def test_a_click_outside_the_rectangle_shows_the_part_around_it(self):
        self.h.set_view(2.0, (-100, -100))
        shown = self.mm.visible_rect_in_minimap()
        target = QPointF(self.mm.width() - 12, self.mm.height() - 12)
        self.assertFalse(shown.contains(target))
        frozen = self.mm.mapping()
        world = frozen.to_world(target)
        self.h.minimap_press(target.x(), target.y())
        self.h.minimap_release(target.x(), target.y())
        centre = self.shown_centre()
        self.assertAlmostEqual(world.x(), centre.x(), delta=1.5 / 2.0 + 0.01)
        self.assertAlmostEqual(world.y(), centre.y(), delta=1.5 / 2.0 + 0.01)
        self.assertEqual(2.0, self.h.view.zoom)
        self.ok("click in the map")

    def test_a_press_inside_the_rectangle_does_not_make_it_jump(self):
        self.h.set_view(2.0, (-100, -100))
        shown = self.mm.visible_rect_in_minimap()
        inside = shown.center() + QPointF(shown.width() / 4,
                                          shown.height() / 4)
        before = self.shown_centre()
        self.h.minimap_press(inside.x(), inside.y())
        self.h.minimap_release(inside.x(), inside.y())
        after = self.shown_centre()
        self.assertAlmostEqual(before.x(), after.x(), delta=1.0)
        self.assertAlmostEqual(before.y(), after.y(), delta=1.0)

    def test_dragging_moves_the_rectangle_with_the_mouse(self):
        self.h.set_view(2.0, (-100, -100))
        shown = self.mm.visible_rect_in_minimap()
        start = shown.center() + QPointF(10, 5)
        self.h.minimap_press(start.x(), start.y())
        self.h.minimap_move(start.x() + 20, start.y() + 12)
        moved = self.mm.visible_rect_in_minimap()
        self.assertAlmostEqual(shown.left() + 20, moved.left(), delta=1.5)
        self.assertAlmostEqual(shown.top() + 12, moved.top(), delta=1.5)
        self.h.minimap_release(start.x() + 20, start.y() + 12)
        self.ok("drag")

    def test_the_map_does_not_rescale_while_the_mouse_drags(self):
        self.h.set_view(2.0, (-100, -100))
        scale = self.mm.mapping().scale
        shown = self.mm.visible_rect_in_minimap()
        self.h.minimap_press(shown.center().x(), shown.center().y())
        # drag far away from the graph: the world rectangle would grow
        self.h.minimap_move(self.mm.width() + 400, -300)
        self.assertEqual(scale, self.mm.mapping().scale)
        self.h.minimap_release(self.mm.width() + 400, -300)
        self.h.process_events()
        self.assertNotEqual(scale, self.mm.mapping().scale)   # fits again
        self.ok("after the drag")

    def test_clicking_never_changes_graph_zoom_selection_or_history(self):
        self.h.select(self.a, self.b)
        selected = set(self.h.field.selection.get())
        before = ops.coords(self.h)
        undo = self.h.command_handler.can_undo.get()
        self.h.set_view(0.5, (30, 40))
        for x, y in ((10, 10), (200, 150), (110, 80)):
            self.h.minimap_drag(x, y, x + 30, y - 20)
        self.assertEqual(before, ops.coords(self.h))
        self.assertEqual(0.5, self.h.view.zoom)
        self.assertEqual(selected, set(self.h.field.selection.get()))
        self.assertEqual(undo, self.h.command_handler.can_undo.get())
        self.ok("after clicks in the map")

    def test_a_double_click_in_the_map_does_not_create_a_node(self):
        from PySide6.QtCore import QEvent
        nodes = len(self.h.nodes)
        glob = self.h.minimap_global(30, 30)
        self.h._send(self.mm, self.h._event(
            QEvent.MouseButtonDblClick, self.mm, glob))
        self.h.release(self.mm, glob)
        self.assertEqual(nodes, len(self.h.nodes))

    def test_only_the_left_button_moves_the_view(self):
        from PySide6.QtCore import QEvent
        from PySide6.QtWidgets import QApplication
        # a position outside of the shown rectangle: a left click there
        # would move the view
        self.h.set_view(2.0, (-100, -100))
        shown = self.mm.visible_rect_in_minimap()
        corner = [QPoint(x, y) for x in (6, self.mm.width() - 6)
                  for y in (6, self.mm.height() - 6)
                  if not shown.contains(QPointF(x, y))][0]
        offset = self.h.view.offset
        glob = self.h.minimap_global(corner.x(), corner.y())
        for button in (Qt.RightButton, Qt.MiddleButton):
            event = self.h._event(QEvent.MouseButtonPress, self.mm, glob,
                                  button=button, buttons=button)
            QApplication.sendEvent(self.mm, event)
            self.assertEqual(offset, self.h.view.offset, str(button))
        # ... and the left button does move it from there
        self.h.minimap_press(corner.x(), corner.y())
        self.h.minimap_release(corner.x(), corner.y())
        self.assertNotEqual(offset, self.h.view.offset)

    def test_the_view_moves_in_whole_pixels_and_branch_widgets_are_only_moved(self):
        from signalflowgrapher.gui.branch_widget import BranchWidget
        rebuilt = []
        original = BranchWidget.updateGeometry

        def counting(widget):
            rebuilt.append(widget)
            return original(widget)
        BranchWidget.updateGeometry = counting
        try:
            for zoom in (1.0, 0.5):
                self.h.set_view(zoom, (0, 0))
                rebuilt.clear()
                self.h.minimap_drag(100, 80, 140, 120, steps=7)
                offset = self.h.view.offset
                self.assertEqual(round(offset.x()), offset.x())
                self.assertEqual(round(offset.y()), offset.y())
                self.assertEqual([], rebuilt, "zoom %s" % zoom)
        finally:
            BranchWidget.updateGeometry = original

    def test_dragging_works_at_every_zoom(self):
        for zoom in (0.1, 0.5, 1.0, 2.0):
            with self.subTest(zoom=zoom):
                self.h.set_view(zoom, (0, 0))
                shown = self.mm.visible_rect_in_minimap()
                start = shown.center()
                self.h.minimap_press(start.x(), start.y())
                self.h.minimap_move(start.x() + 8, start.y() + 4)
                self.h.minimap_move(start.x() + 16, start.y() + 9)
                # while the mouse drags the mapping does not change, so the
                # rectangle follows the mouse exactly
                moved = self.mm.visible_rect_in_minimap()
                self.assertAlmostEqual(shown.left() + 16, moved.left(),
                                       delta=1.5)
                self.assertAlmostEqual(shown.top() + 9, moved.top(),
                                       delta=1.5)
                self.h.minimap_release(start.x() + 16, start.y() + 9)
                self.assertEqual(zoom, self.h.view.zoom)
                self.ok("zoom %s" % zoom)

    def test_a_click_outside_the_rectangle_works_at_every_zoom(self):
        for zoom in (0.1, 0.5, 1.0, 2.0):
            with self.subTest(zoom=zoom):
                self.h.set_view(zoom, (0, 0))
                shown = self.mm.visible_rect_in_minimap()
                # a corner of the map that is not covered by the rectangle,
                # if there is one
                free = [QPointF(x, y) for x in (6, self.mm.width() - 6)
                        for y in (6, self.mm.height() - 6)
                        if not shown.contains(QPointF(x, y))]
                if not free:
                    continue
                target = free[0]
                world = self.mm.mapping().to_world(target)
                self.h.minimap_press(target.x(), target.y())
                self.h.minimap_release(target.x(), target.y())
                centre = self.shown_centre()
                self.assertAlmostEqual(world.x(), centre.x(),
                                       delta=1.0 / zoom + 0.5)
                self.assertAlmostEqual(world.y(), centre.y(),
                                       delta=1.0 / zoom + 0.5)
                self.assertEqual(zoom, self.h.view.zoom)
                self.ok("zoom %s" % zoom)

    def test_the_wheel_is_left_to_the_graph_field(self):
        event = self.h.wheel(10, 10, -120, widget=self.mm)
        self.assertFalse(event.isAccepted())


class TestOverlay(MiniMapTestCase):
    def test_it_is_not_shown_until_it_is_asked_for(self):
        h = Harness()
        try:
            self.assertFalse(h.field.minimap_visible)
            self.assertFalse(h.field.minimap.isVisible())
            h.field.set_minimap_visible(True)
            self.assertTrue(h.field.minimap_visible)
            h.field.set_minimap_visible(False)
            self.assertFalse(h.field.minimap_visible)
        finally:
            h.close()

    def test_it_stays_in_the_bottom_right_corner_when_the_window_changes(self):
        for width, height in ((1000, 700), (500, 350), (900, 400), (1400, 900)):
            self.h.field.resize(width, height)
            self.h.process_events()
            self.assertEqual(QPoint(width - 220 - 10, height - 160 - 10),
                             self.mm.pos())
            self.ok("size %s x %s" % (width, height))

    def test_it_stays_over_everything_that_is_created_later(self):
        self.h.field.resize(1000, 700)
        # a node, a branch and a label under the map, then spline handles
        under = self.h.double_click(900, 650)
        other = self.h.double_click(800, 600)
        self.h.ctrl_click_branch(under, other)
        self.h.select_branch(self.ab)
        self.h.process_events()
        self.assertEqual([], check_consistency(self.h))
        centre = QPoint(self.mm.x() + self.mm.width() // 2,
                        self.mm.y() + self.mm.height() // 2)
        self.assertIs(self.mm, self.h.field.childAt(centre))

    def test_it_never_takes_the_keyboard_focus(self):
        self.assertEqual(Qt.NoFocus, self.mm.focusPolicy())
        self.h.minimap_drag(100, 80, 120, 90)
        self.assertFalse(self.mm.hasFocus())

    def test_it_is_repainted_when_the_view_or_the_graph_changes(self):
        """
        (A grab always paints, so it cannot show whether the map is told to
        repaint; the calls of update() are counted.)
        """
        calls = []
        original = MiniMapWidget.update
        MiniMapWidget.update = lambda widget, *a: (calls.append(1),
                                                   original(widget, *a))[1]
        try:
            self.h.process_events()
            for change, label in (
                    (lambda: self.h.view.set(offset=QPointF(7, 3)), "pan"),
                    (lambda: self.h.field.set_zoom(0.5), "zoom"),
                    (lambda: self.h.double_click(450, 300), "new node"),
                    (lambda: self.h.drag_node(self.a, 60, 30), "move node"),
                    (lambda: self.h.drag_label(self.a, 10, 10), "move label"),
                    (lambda: self.h.undo(), "undo"),
                    (lambda: self.h.io.new_graph(), "new graph")):
                calls.clear()
                change()
                self.assertTrue(calls, "no repaint after: " + label)
        finally:
            MiniMapWidget.update = original

    def test_it_is_not_a_widget_of_the_graph(self):
        self.assertNotIn(self.mm, self.h.model_widget_map.values())
        self.assertNotIn(self.mm, self.h.model_label_map.values())
        self.assertEqual([], check_consistency(self.h))

    def test_center_graph_and_the_rubber_band_ignore_it(self):
        self.h.field.center_graph()
        with_map = (self.h.view.zoom, self.h.view.offset)
        self.h.field.set_minimap_visible(False)
        self.h.view.reset()
        self.h.field.center_graph()
        self.assertEqual(with_map, (self.h.view.zoom, self.h.view.offset))
        self.h.field.set_minimap_visible(True)
        self.h.field.on_esc_press()
        g0 = self.h.field.mapToGlobal(QPoint(2, 2))
        self.h.press(self.h.field, g0, modifiers=Qt.AltModifier)
        self.h.move(self.h.field, g0 + QPoint(900, 600),
                    modifiers=Qt.AltModifier)
        self.h.release(self.h.field, g0 + QPoint(900, 600),
                       modifiers=Qt.AltModifier)
        self.assertEqual(3, len(set(self.h.field.selection.get())
                                & set(self.h.nodes)))

    def test_pictures_of_the_graph_do_not_contain_the_map(self):
        from PySide6.QtGui import QPixmap
        self.h.field.set_minimap_visible(False)
        off = QPixmap(self.h.field.size())
        off.fill()
        self.h.field.render_graph(off)
        self.h.field.set_minimap_visible(True)
        on = QPixmap(self.h.field.size())
        on.fill()
        self.h.field.render_graph(on)
        self.assertEqual(off.toImage(), on.toImage())
        self.assertTrue(self.h.field.minimap_visible)     # shown again
        # whereas a grab of the window shows it
        plain = QPixmap(self.h.field.size())
        plain.fill()
        self.h.field.render(plain)
        self.assertNotEqual(off.toImage(), plain.toImage())

    def test_nothing_changes_for_the_graph_when_the_map_is_switched(self):
        before = ops.coords(self.h)
        undo = self.h.command_handler.can_undo.get()
        for visible in (False, True, False, True):
            self.h.field.set_minimap_visible(visible)
            self.assertEqual(before, ops.coords(self.h))
            self.assertEqual(undo, self.h.command_handler.can_undo.get())
            self.ok("minimap %s" % visible)


class TestSettings(TestCase):
    def test_the_map_is_off_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = AppSettings(QSettings(
                os.path.join(tmp, "s.ini"), QSettings.IniFormat))
            self.assertFalse(settings.minimap_visible())

    def test_the_choice_is_remembered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.ini")
            AppSettings(QSettings(path, QSettings.IniFormat)) \
                .set_minimap_visible(True)
            again = AppSettings(QSettings(path, QSettings.IniFormat))
            self.assertTrue(again.minimap_visible())
            again.set_minimap_visible(False)
            self.assertFalse(AppSettings(QSettings(
                path, QSettings.IniFormat)).minimap_visible())

    def test_it_is_not_saved_in_graph_files(self):
        import json
        h = Harness()
        try:
            h.double_click(100, 100)
            h.field.set_minimap_visible(True)
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, "g.sfg")
                h.save(path)
                with open(path, encoding="utf-8") as f:
                    self.assertNotIn("minimap", f.read().lower())
        finally:
            h.close()


class TestInTheMainWindow(TestCase):
    """The real main window: menu entry, shortcut, remembered choice."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        from signalflowgrapher.containers import MainWindows
        from signalflowgrapher.gui.graph_field import GraphField
        cls.app = QApplication.instance() or QApplication([])
        cls.window = MainWindows.main_window()
        cls.window.show()
        cls.window.activateWindow()
        cls.app.processEvents()
        cls.field = cls.window.findChild(GraphField)

    @classmethod
    def tearDownClass(cls):
        cls.window.close()

    def setUp(self):
        # settings of this test, not those of the user
        self.tmp = tempfile.TemporaryDirectory()
        self.settings_path = os.path.join(self.tmp.name, "s.ini")
        self.original = self.window._MainWindow__settings
        self.window._MainWindow__settings = AppSettings(
            QSettings(self.settings_path, QSettings.IniFormat))
        self.window._ui.action_minimap.setChecked(False)
        self.app.processEvents()

    def tearDown(self):
        self.window._MainWindow__settings = self.original
        self.window._ui.action_minimap.setChecked(False)
        self.tmp.cleanup()

    def stored(self):
        return AppSettings(QSettings(
            self.settings_path, QSettings.IniFormat)).minimap_visible()

    def test_the_action_is_checkable_and_has_a_shortcut(self):
        action = self.window._ui.action_minimap
        self.assertTrue(action.isCheckable())
        self.assertEqual("Mini Map", action.text())
        self.assertEqual(["Alt+N"], [k.toString() for k in action.shortcuts()])

    def test_the_view_menu_has_the_entry(self):
        from PySide6.QtWidgets import QMenu
        menus = {m.title(): m for m in self.window.findChildren(QMenu)}
        self.assertIn("Mini Map",
                      [a.text() for a in menus["View"].actions()])

    def test_the_action_shows_and_hides_the_map_and_remembers_it(self):
        action = self.window._ui.action_minimap
        action.trigger()
        self.app.processEvents()
        self.assertTrue(self.field.minimap_visible)
        self.assertTrue(action.isChecked())
        self.assertTrue(self.stored())
        action.trigger()
        self.app.processEvents()
        self.assertFalse(self.field.minimap_visible)
        self.assertFalse(action.isChecked())
        self.assertFalse(self.stored())

    def test_alt_n_switches_the_map(self):
        from PySide6.QtGui import QKeySequence
        from PySide6.QtTest import QTest
        QTest.keySequence(self.window, QKeySequence("Alt+N"))
        self.app.processEvents()
        self.assertTrue(self.field.minimap_visible)
        self.assertTrue(self.stored())
        QTest.keySequence(self.window, QKeySequence("Alt+N"))
        self.app.processEvents()
        self.assertFalse(self.field.minimap_visible)

    def export_png(self, path):
        """The menu action 'Save as PNG' with the file dialog answered."""
        from unittest.mock import patch
        with patch("signalflowgrapher.gui.main_window.QFileDialog") as dialog:
            dialog.getSaveFileName.return_value = (path, "PNG Files (*.png)")
            self.window._ui.action_save_png.trigger()
        self.app.processEvents()

    def test_the_picture_export_does_not_contain_the_map(self):
        from PySide6.QtGui import QImage
        with tempfile.TemporaryDirectory() as tmp:
            self.window._ui.action_minimap.setChecked(False)
            self.app.processEvents()
            off = os.path.join(tmp, "off.png")
            self.export_png(off)
            self.window._ui.action_minimap.setChecked(True)
            self.app.processEvents()
            on = os.path.join(tmp, "on.png")
            self.export_png(on)
            self.assertTrue(self.field.minimap_visible)   # shown again
            self.assertEqual(QImage(off), QImage(on))


class TestRememberedAtStart(TestCase):
    """A fresh program start shows the map as it was left."""

    SCRIPT = """
import sys
from PySide6.QtCore import QSettings
QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, sys.argv[1])
from signalflowgrapher.utils.settings import AppSettings
if len(sys.argv) > 2:
    AppSettings().set_minimap_visible(sys.argv[2] == "on")
from PySide6.QtWidgets import QApplication
from signalflowgrapher.containers import MainWindows
from signalflowgrapher.gui.graph_field import GraphField
app = QApplication([])
window = MainWindows.main_window()
window.show()
app.processEvents()
field = window.findChild(GraphField)
print("MINIMAP", field.minimap_visible, window._ui.action_minimap.isChecked())
"""

    def start(self, directory, setting=None):
        import signalflowgrapher
        src = os.path.dirname(os.path.dirname(signalflowgrapher.__file__))
        args = [sys.executable, "-c", self.SCRIPT, directory]
        if setting:
            args.append(setting)
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=src)
        result = subprocess.run(args, env=env, capture_output=True,
                                text=True, timeout=120)
        self.assertEqual(0, result.returncode, result.stderr[-1500:])
        line = [l for l in result.stdout.splitlines()
                if l.startswith("MINIMAP")][0]
        return line.split()[1:]

    def test_a_program_start_applies_the_remembered_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(["False", "False"], self.start(tmp))      # default
            self.assertEqual(["True", "True"], self.start(tmp, "on"))
            self.assertEqual(["True", "True"], self.start(tmp))        # kept
            self.assertEqual(["False", "False"], self.start(tmp, "off"))
            self.assertEqual(["False", "False"], self.start(tmp))
