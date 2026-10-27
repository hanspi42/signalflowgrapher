"""
Tests of the zoom (step 5 of the V3.0 plan): zoom operations and their
limits, mouse wheel, keyboard actions, that everything drawn scales with the
zoom, the minimum click areas, zoom to fit, and that no file or export
depends on the zoom.
"""
import json
import math
import os
import random
import tempfile
from unittest import TestCase

from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QAction, QColor

from signalflowgrapher.gui import glyphs
from signalflowgrapher.gui.view_transform import (
    MAX_ZOOM, MIN_ZOOM, ZOOM_STEP)
from signalflowgrapher.tests.gui import test_gui_operations as ops
from signalflowgrapher.tests.gui.consistency import check_consistency
from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.test_golden import example_files


class TestZoomOperations(ops.GuiTestCase):
    def setUp(self):
        super().setUp()
        self.make_two_nodes_and_branch()

    def zoom(self):
        return self.h.view.zoom

    def test_the_limits_are_10_and_200_percent(self):
        self.assertEqual(2.0, MAX_ZOOM)
        self.assertEqual(0.1, MIN_ZOOM)
        self.assertEqual(1.0, self.zoom())              # start at 100%

    def test_zoom_in_goes_beyond_100_percent_up_to_exactly_200_percent(self):
        seen = []
        for _ in range(10):
            self.h.field.zoom_in()
            seen.append(self.zoom())
        self.assertGreater(seen[0], 1.0)
        self.assertEqual(seen, sorted(seen))             # never down
        self.assertEqual(2.0, seen[3])                   # four steps double
        self.assertEqual(2.0, seen[-1])
        self.ok("at the largest zoom")

    def test_zoom_in_at_200_percent_does_nothing(self):
        self.h.field.set_zoom(2.0)
        before = (self.zoom(), self.h.view.offset)
        self.h.field.zoom_in()
        self.assertEqual(before, (self.zoom(), self.h.view.offset))

    def test_zoom_out_reaches_exactly_10_percent_and_stops(self):
        seen = []
        for _ in range(40):
            self.h.field.zoom_out()
            seen.append(self.zoom())
        self.assertEqual(0.1, seen[-1])
        self.assertEqual(seen, sorted(seen, reverse=True))   # never up
        self.assertEqual(0.1, min(seen))
        self.ok("at the smallest zoom")

    def test_zoom_in_from_10_percent_reaches_exactly_200_percent(self):
        self.h.field.set_zoom(0.1)
        for _ in range(60):
            self.h.field.zoom_in()
        self.assertEqual(2.0, self.zoom())
        self.ok("at 200%")

    def test_steps_out_and_in_return_to_exactly_100_percent(self):
        for steps in (1, 2, 4, 7, 13):
            with self.subTest(steps=steps):
                for _ in range(steps):
                    self.h.field.zoom_out()
                self.assertLess(self.zoom(), 1.0)
                for _ in range(steps):
                    self.h.field.zoom_in()
                self.assertEqual(1.0, self.zoom())

    def test_steps_in_and_out_return_to_exactly_100_percent(self):
        for steps in (1, 2, 3, 4):
            with self.subTest(steps=steps):
                for _ in range(steps):
                    self.h.field.zoom_in()
                self.assertGreater(self.zoom(), 1.0)
                for _ in range(steps):
                    self.h.field.zoom_out()
                self.assertEqual(1.0, self.zoom())

    def test_small_steps_out_and_in_return_to_exactly_100_percent(self):
        """
        A touchpad turns the wheel in small parts of a step. Without care
        the rounding error of 'out and in again' leaves 0.9999999999999999,
        which the status bar shows as 100% but which is not.
        """
        for part in (0.1, 0.3, 0.7):
            for count in (1, 3, 8):
                with self.subTest(part=part, count=count):
                    for _ in range(count):
                        self.h.field.zoom_by_steps(-part)
                    for _ in range(count):
                        self.h.field.zoom_by_steps(part)
                    self.assertEqual(1.0, self.zoom())

    def test_four_steps_halve_or_double_the_zoom(self):
        self.assertAlmostEqual(2 ** 0.25, ZOOM_STEP)
        for _ in range(4):
            self.h.field.zoom_out()
        self.assertAlmostEqual(0.5, self.zoom(), places=9)
        self.h.field.zoom_reset()
        for _ in range(4):
            self.h.field.zoom_in()
        self.assertEqual(2.0, self.zoom())

    def test_set_zoom_is_limited(self):
        self.h.field.set_zoom(5)
        self.assertEqual(2.0, self.zoom())
        self.h.field.set_zoom(0.01)
        self.assertEqual(0.1, self.zoom())
        self.h.field.set_zoom(0.3)
        self.assertEqual(0.3, self.zoom())
        self.h.field.set_zoom(1.5)
        self.assertEqual(1.5, self.zoom())

    def test_reset_returns_to_100_percent_from_every_zoom(self):
        for start in (0.1, 0.3, 0.9, 1.5, 2.0):
            with self.subTest(start=start):
                self.h.field.set_zoom(start)
                self.h.field.zoom_reset()
                self.assertEqual(1.0, self.zoom())
                self.ok("reset from %s" % start)

    def test_reset_keeps_the_centre_of_the_window_also_when_zooming_out(self):
        centre = QPointF(self.h.field.width() / 2, self.h.field.height() / 2)
        for start in (0.3, 2.0):
            self.h.view.reset()
            self.h.field.set_zoom(start)
            world = self.h.view.to_world(centre)
            self.h.field.zoom_reset()
            after = self.h.view.to_world(centre)
            self.assertAlmostEqual(world.x(), after.x(), places=6)
            self.assertAlmostEqual(world.y(), after.y(), places=6)

    def test_the_point_under_the_anchor_stays_where_it_is(self):
        """
        The world position under the mouse pointer (or the window centre)
        is the same before and after a zoom, for any zoom and offset.
        """
        rnd = random.Random(42)
        for _ in range(200):
            zoom = rnd.choice([0.1, 0.25, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0])
            offset = (rnd.randint(-400, 400), rnd.randint(-400, 400))
            self.h.view.set(zoom, QPointF(*offset))
            anchor = QPointF(rnd.randint(0, 1000), rnd.randint(0, 700))
            world = self.h.view.to_world(anchor)
            self.h.field.set_zoom(rnd.uniform(0.1, 2.0), anchor)
            after = self.h.view.to_world(anchor)
            self.assertAlmostEqual(world.x(), after.x(), places=6)
            self.assertAlmostEqual(world.y(), after.y(), places=6)

    def test_without_anchor_the_centre_of_the_window_stays(self):
        self.h.view.set(0.5, QPointF(37, -12))
        centre = QPointF(self.h.field.width() / 2, self.h.field.height() / 2)
        world = self.h.view.to_world(centre)
        self.h.field.zoom_out()
        after = self.h.view.to_world(centre)
        self.assertAlmostEqual(world.x(), after.x(), places=6)
        self.assertAlmostEqual(world.y(), after.y(), places=6)

    def test_a_node_under_the_anchor_stays_under_it(self):
        node = self.h.nodes[0]
        for zoom in (2.0, 1.5, 0.8, 0.5, 0.25, 0.1):
            self.h.view.reset()
            screen = self.h.view.to_screen(QPointF(node.x, node.y))
            self.h.field.set_zoom(zoom, screen)
            centre = self.h.widget_of(node).get_center()
            self.assertAlmostEqual(screen.x(), centre.x(), delta=1.01)
            self.assertAlmostEqual(screen.y(), centre.y(), delta=1.01)

    def test_zoom_is_not_part_of_the_graph_or_the_undo_history(self):
        before = ops.coords(self.h)
        undo = self.h.command_handler.can_undo.get()
        for _ in range(6):
            self.h.field.zoom_out()
        self.h.field.zoom_to_fit()
        self.h.field.zoom_reset()
        self.assertEqual(before, ops.coords(self.h))
        self.assertEqual(undo, self.h.command_handler.can_undo.get())

    def test_zoomed_everything_stays_consistent(self):
        for steps in range(-4, 14):
            self.h.field.set_zoom(ZOOM_STEP ** -steps)
            self.ok("zoom step %d" % steps)

    def test_the_zoom_is_not_saved_and_a_loaded_file_is_at_100_percent(self):
        self.h.field.set_zoom(0.3)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "g.sfg")
            self.h.save(path)
            with open(path, encoding="utf-8") as f:
                self.assertNotIn("zoom", f.read())
            self.h.load(path)
        self.assertEqual(1.0, self.zoom())


class TestMouseWheel(ops.GuiTestCase):
    def setUp(self):
        super().setUp()
        self.a, self.b, self.br = self.make_two_nodes_and_branch()

    def test_ctrl_wheel_zooms_out_and_in(self):
        self.h.wheel(400, 300, -120)
        self.assertAlmostEqual(1 / ZOOM_STEP, self.h.view.zoom, places=9)
        self.h.wheel(400, 300, 120)
        self.assertEqual(1.0, self.h.view.zoom)
        self.ok("wheel")

    def test_one_notch_is_one_step_and_small_turns_are_parts_of_a_step(self):
        self.h.wheel(400, 300, -360)
        self.assertAlmostEqual(ZOOM_STEP ** -3, self.h.view.zoom, places=9)
        self.h.field.zoom_reset()
        self.h.wheel(400, 300, -30)
        self.assertAlmostEqual(ZOOM_STEP ** -0.25, self.h.view.zoom, places=9)

    def test_wheel_events_that_come_together_are_one_zoom(self):
        """
        Zooming rebuilds every widget; a fast turn of the wheel must not do
        that once per notch.
        """
        changes = []
        self.h.view.changed.connect(lambda: changes.append(self.h.view.zoom))
        from PySide6.QtCore import QPoint as P
        from PySide6.QtCore import QPointF as PF
        from PySide6.QtGui import QWheelEvent
        from PySide6.QtWidgets import QApplication
        for _ in range(5):                  # no event processing in between
            glob = self.h.field.mapToGlobal(P(300, 200))
            QApplication.sendEvent(self.h.field, QWheelEvent(
                PF(300, 200), PF(glob), P(0, 0), P(0, -120), Qt.NoButton,
                Qt.ControlModifier, Qt.NoScrollPhase, False))
        self.assertEqual([], changes)       # nothing yet
        self.h.process_events()
        self.assertEqual(1, len(changes))
        self.assertAlmostEqual(ZOOM_STEP ** -5, self.h.view.zoom, places=9)
        self.ok("coalesced wheel")

    def test_the_wheel_without_ctrl_does_nothing(self):
        before = (self.h.view.zoom, self.h.view.offset)
        for mods in (Qt.NoModifier, Qt.ShiftModifier, Qt.AltModifier):
            self.h.wheel(400, 300, -120, modifiers=mods)
        self.assertEqual(before, (self.h.view.zoom, self.h.view.offset))

    def test_the_wheel_zooms_around_the_mouse_pointer(self):
        point = QPointF(620, 140)
        world = self.h.view.to_world(point)
        self.h.wheel(620, 140, -240)
        after = self.h.view.to_world(point)
        self.assertAlmostEqual(world.x(), after.x(), places=6)
        self.assertAlmostEqual(world.y(), after.y(), places=6)

    def test_widgets_on_the_canvas_do_not_take_the_wheel(self):
        """
        A wheel turned over a node, branch, label or spline handle must
        reach the canvas. Qt hands a wheel event that a widget does not
        accept on to its parent, so none of these widgets may accept it.
        (A synthetic event is not handed on by Qt, only one from the window
        system is, so the hand over itself has to be tried by hand: see the
        manual checklist in DEVDOCU.md.)
        """
        self.h.select_branch(self.br)               # shows the handles
        widgets = [self.h.widget_of(self.h.nodes[0]),
                   self.h.widget_of(self.br),
                   self.h.label_of(self.h.nodes[0]),
                   self.h.label_of(self.br)] + self.h.selected_handles()
        for widget in widgets:
            with self.subTest(widget=type(widget).__name__):
                event = self.h.wheel(10, 10, -120, widget=widget)
                self.assertFalse(event.isAccepted())

    def test_the_canvas_accepts_the_ctrl_wheel_and_ignores_the_plain_wheel(self):
        accepted = self.h.wheel(400, 300, -120, modifiers=Qt.ControlModifier)
        self.assertTrue(accepted.isAccepted())
        plain = self.h.wheel(400, 300, -120, modifiers=Qt.NoModifier)
        self.assertFalse(plain.isAccepted())

    def test_the_wheel_at_the_limits_does_not_go_beyond(self):
        self.h.wheel(400, 300, 1200)
        self.assertEqual(2.0, self.h.view.zoom)
        self.h.wheel(400, 300, 12000)
        self.assertEqual(2.0, self.h.view.zoom)
        self.h.wheel(400, 300, -12000)
        self.assertEqual(0.1, self.h.view.zoom)

    def test_ctrl_wheel_away_from_you_zooms_in_beyond_100_percent(self):
        self.h.wheel(400, 300, 120)
        self.assertAlmostEqual(ZOOM_STEP, self.h.view.zoom, places=9)
        self.ok("zoomed in with the wheel")


class TestZoomInTheMainWindow(TestCase):
    """The real main window: menu actions, shortcuts, status bar."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication, QLabel
        from signalflowgrapher.containers import MainWindows
        from signalflowgrapher.gui.graph_field import GraphField
        cls.app = QApplication.instance() or QApplication([])
        cls.window = MainWindows.main_window()
        cls.window.show()
        cls.window.activateWindow()
        cls.app.processEvents()
        cls.field = cls.window.findChild(GraphField)
        cls.label = cls.window.statusBar().findChildren(QLabel)[-1]

    @classmethod
    def tearDownClass(cls):
        cls.window.close()

    def setUp(self):
        self.field.view.reset()
        self.app.processEvents()

    def test_actions_and_their_shortcuts(self):
        ui = self.window._ui
        keys = {a.text(): [k.toString() for k in a.shortcuts()]
                for a in (ui.action_zoom_in, ui.action_zoom_out,
                          ui.action_zoom_reset, ui.action_zoom_fit)}
        # The first shortcut is the one that the menu shows. The Alt keys
        # need no numpad and no Shift (+ is Shift+1 on a Swiss keyboard);
        # Ctrl++, Ctrl+= and Ctrl+- are the usual keys of other programs.
        self.assertEqual({"Zoom In": ["Alt+I", "Ctrl++", "Ctrl+="],
                          "Zoom Out": ["Alt+U", "Ctrl+-"],
                          "Zoom 100%": ["Alt+O"],
                          "Zoom to Fit": ["Alt+Z"]}, keys)

    def press(self, sequence):
        from PySide6.QtGui import QKeySequence
        from PySide6.QtTest import QTest
        QTest.keySequence(self.window, QKeySequence(sequence))
        self.app.processEvents()
        return self.field.view.zoom

    def test_pressing_the_keys_zooms(self):
        """The real key presses, not only the list of shortcuts."""
        for sequence in ("Alt+I", "Ctrl++", "Ctrl+="):
            with self.subTest(sequence=sequence):
                self.field.view.reset()
                self.assertAlmostEqual(ZOOM_STEP, self.press(sequence))
        for sequence in ("Alt+U", "Ctrl+-"):
            with self.subTest(sequence=sequence):
                self.field.view.reset()
                self.assertAlmostEqual(1 / ZOOM_STEP, self.press(sequence))

    def test_alt_o_sets_the_zoom_to_100_percent_from_anywhere(self):
        for start in (0.1, 0.5, 1.5, 2.0):
            with self.subTest(start=start):
                self.field.set_zoom(start)
                self.assertEqual(1.0, self.press("Alt+O"))

    def test_ctrl_0_is_not_used_any_more(self):
        self.field.set_zoom(0.5)
        self.assertEqual(0.5, self.press("Ctrl+0"))

    def test_alt_z_zooms_to_fit(self):
        from PySide6.QtCore import QPointF
        from signalflowgrapher.tests.gui.test_golden import example_files
        from signalflowgrapher.containers import Controllers
        Controllers.io_controller().load_graph(example_files()[-1])
        self.app.processEvents()
        try:
            self.field.view.set(0.3, QPointF(500, 400))
            self.field.zoom_to_fit()
            expected = (self.field.view.zoom, self.field.view.offset)
            self.field.view.set(0.3, QPointF(500, 400))
            self.press("Alt+Z")
            self.assertEqual(expected, (self.field.view.zoom,
                                        self.field.view.offset))
            self.assertNotEqual((0.3, QPointF(500, 400)), expected)
        finally:
            Controllers.io_controller().new_graph()
            self.app.processEvents()

    def test_no_shortcut_is_used_twice(self):
        seen = {}
        for action in self.window.findChildren(QAction):
            for key in action.shortcuts():
                name = key.toString()
                self.assertNotIn(name, seen, "%s used by %r and %r" % (
                    name, seen.get(name), action.text()))
                seen[name] = action.text()

    def test_the_actions_zoom(self):
        ui = self.window._ui
        ui.action_zoom_out.trigger()
        self.assertAlmostEqual(1 / ZOOM_STEP, self.field.view.zoom)
        ui.action_zoom_in.trigger()
        self.assertEqual(1.0, self.field.view.zoom)
        for _ in range(30):
            ui.action_zoom_out.trigger()
        self.assertEqual(0.1, self.field.view.zoom)
        for _ in range(60):
            ui.action_zoom_in.trigger()
        self.assertEqual(2.0, self.field.view.zoom)
        ui.action_zoom_reset.trigger()
        self.assertEqual(1.0, self.field.view.zoom)

    def test_the_status_bar_shows_the_zoom(self):
        self.assertEqual("100%", self.label.text())
        self.field.set_zoom(0.5)
        self.assertEqual("50%", self.label.text())
        self.field.set_zoom(0.1)
        self.assertEqual("10%", self.label.text())
        self.field.set_zoom(2.0)
        self.assertEqual("200%", self.label.text())
        self.field.zoom_reset()
        self.assertEqual("100%", self.label.text())

    def test_the_view_menu_has_the_zoom_entries(self):
        from PySide6.QtWidgets import QMenu
        menus = {m.title(): m for m in self.window.findChildren(QMenu)}
        view = [a.text() for a in menus["View"].actions() if a.text()]
        for text in ("Zoom In", "Zoom Out", "Zoom 100%", "Zoom to Fit"):
            self.assertIn(text, view)


def ink(image, x, y, background_luminance=None):
    """Darkness of a pixel from 0 (background) to 1 (black)."""
    c = QColor(image.pixel(x, y))
    luminance = (c.red() + c.green() + c.blue()) / 3
    return max(0.0, min(1.0, (background_luminance - luminance)
                        / background_luminance))


class TestEverythingScales(TestCase):
    """
    Node size, line widths, arrow and text are measured in the rendered
    picture: each is the size at 100% times the zoom, so their relation is
    the same at every zoom (as in the TikZ output).
    """

    ZOOMS = (2.0, 1.5, 1.0, 0.75, 0.5, 0.25)

    def build(self, zoom):
        h = Harness(1700, 600)
        a = h.double_click(150, 150)
        b = h.double_click(630, 150)
        br = h.ctrl_click_branch(a, b)
        h.controller.set_node_name(a, "Vin")        # a label with text ...
        h.field.on_esc_press()
        h.field.toggle_grid_visibility()           # uniform background
        h.set_view(zoom, (20, 20))
        return h, a, b, br

    def measure(self, zoom):
        h, a, b, br = self.build(zoom)
        try:
            image = h.field.grab().toImage()
            bg = QColor(image.pixel(5, 5))
            bg_l = (bg.red() + bg.green() + bg.blue()) / 3
            ca = h.widget_of(a).get_center()
            cb = h.widget_of(b).get_center()

            # node: dark rows in the column through the centre, between the
            # branch (horizontal) and the label (below): the ring top/bottom
            reach = math.ceil(15 * zoom) + 1
            rows = [y for y in range(int(ca.y()) - reach,
                                     int(ca.y()) + reach + 1)
                    if ink(image, int(ca.x()), y, bg_l) > 0.5]
            node_outer = max(rows) - min(rows) + 1

            # line: total darkness in a column a quarter of the way along
            x = int(ca.x() + (cb.x() - ca.x()) * 0.25)
            line_reach = math.ceil(8 * max(zoom, 1))
            line = sum(ink(image, x, y, bg_l)
                       for y in range(int(ca.y()) - line_reach,
                                      int(ca.y()) + line_reach + 1))

            # arrow: tallest dark column around the middle of the branch
            mid = h.widget_of(br).get_center()
            half = math.ceil(14 * zoom) + 1
            arrow_reach = math.ceil(14 * max(zoom, 1)) + 2
            arrow = 0
            for xx in range(int(mid.x()) - half, int(mid.x()) + half + 1):
                dark = [y for y in range(int(mid.y()) - arrow_reach,
                                         int(mid.y()) + arrow_reach + 1)
                        if ink(image, xx, y, bg_l) > 0.5]
                if dark:
                    arrow = max(arrow, max(dark) - min(dark) + 1)

            label = h.label_of(a)
            return {"node_outer": node_outer, "line": line, "arrow": arrow,
                    "font": label.font().pointSizeF(),
                    "label_height": label.height(),
                    "node_widget": h.widget_of(a).width()}
        finally:
            h.close()

    @classmethod
    def setUpClass(cls):
        cls.measured = {z: cls().measure(z) for z in cls.ZOOMS}

    def test_node_circle_is_the_size_at_100_percent_times_the_zoom(self):
        # outer diameter at 100%: (radius 8 + half of the line width 3) * 2
        outer = (glyphs.NODE_RADIUS + glyphs.NODE_CIRCLE_WIDTH / 2) * 2
        self.assertEqual(19, outer)
        for zoom in self.ZOOMS:
            self.assertAlmostEqual(outer * zoom,
                                   self.measured[zoom]["node_outer"],
                                   delta=1.6, msg="zoom %s" % zoom)

    def test_branch_line_width_is_the_width_at_100_percent_times_the_zoom(self):
        full = self.measured[1.0]["line"]
        self.assertAlmostEqual(3, full, delta=0.4)
        for zoom in self.ZOOMS:
            self.assertAlmostEqual(3 * zoom, self.measured[zoom]["line"],
                                   delta=0.4, msg="zoom %s" % zoom)

    def test_arrow_is_the_size_at_100_percent_times_the_zoom(self):
        full = self.measured[1.0]["arrow"]
        self.assertGreater(full, 14)
        for zoom in self.ZOOMS:
            self.assertAlmostEqual(full * zoom,
                                   self.measured[zoom]["arrow"],
                                   delta=2.0, msg="zoom %s" % zoom)

    def test_text_is_the_size_at_100_percent_times_the_zoom(self):
        full = self.measured[1.0]
        self.assertEqual(13, full["font"])
        for zoom in self.ZOOMS:
            m = self.measured[zoom]
            self.assertAlmostEqual(13 * zoom, m["font"], places=2)
            self.assertAlmostEqual(full["label_height"] * zoom,
                                   m["label_height"], delta=2.5,
                                   msg="zoom %s" % zoom)

    def test_the_relation_between_node_line_and_text_is_the_same(self):
        full = self.measured[1.0]
        for zoom in (0.75, 0.5):
            m = self.measured[zoom]
            self.assertAlmostEqual(full["node_outer"] / full["line"],
                                   m["node_outer"] / m["line"],
                                   delta=0.8, msg="zoom %s" % zoom)
            self.assertAlmostEqual(full["label_height"] / full["node_outer"],
                                   m["label_height"] / m["node_outer"],
                                   delta=0.35, msg="zoom %s" % zoom)

    def test_labels_without_text_scale_too(self):
        """
        A node without a name has a label without text (it can still be
        grabbed); QLabel does not update the size of such a label by itself.
        """
        h = Harness()
        try:
            node = h.double_click(150, 150)
            self.assertEqual("", node.name)
            label = h.label_of(node)
            full = (label.width(), label.height())
            for zoom in (0.75, 0.5, 0.25):
                h.set_view(zoom, (0, 0))
                self.assertAlmostEqual(full[1] * zoom, label.height(),
                                       delta=3, msg="zoom %s" % zoom)
                self.assertAlmostEqual(full[0] * zoom, label.width(),
                                       delta=3, msg="zoom %s" % zoom)
            h.set_view(1.0, (0, 0))
            self.assertEqual(full, (label.width(), label.height()))
        finally:
            h.close()

    def test_branch_is_rebuilt_when_only_the_zoom_changes(self):
        """
        A branch whose four points are the same on the screen at two zooms
        (here: all at the origin of the world, shown with offset 0) still
        has an arrow, a line width and click areas of the new size.
        """
        h = Harness()
        try:
            node = h.controller.create_node(0, 0)
            branch = h.controller.create_branch(
                node, node, 0, 0, 0, 0, 0, 30, "w")
            h.process_events()
            for zoom in (0.5, 0.25, 1.0):
                h.set_view(zoom, (0, 0))
                self.assertEqual([], check_consistency(h), "zoom %s" % zoom)
                self.assertEqual(zoom,
                                 h.widget_of(branch)._BranchWidget__zoom)
        finally:
            h.close()

    def test_spline_handle_knob_is_the_size_at_100_percent_times_the_zoom(self):
        h = Harness(1900, 500)
        try:
            a = h.double_click(150, 150)
            b = h.double_click(630, 150)
            br = h.ctrl_click_branch(a, b)
            handles = h.select_branch(br)
            h.field.toggle_grid_visibility()
            extents = {}
            for zoom in (2.0, 1.0, 0.5):
                h.set_view(zoom, (20, 20))
                image = h.field.grab().toImage()
                bg = QColor(image.pixel(5, 5))
                bg_l = (bg.red() + bg.green() + bg.blue()) / 3
                knob = h.view.to_screen_point(handles[1].get_world_center())
                reach = math.ceil(10 * zoom) + 2
                rows = [y for y in range(knob.y() - reach, knob.y() + reach + 1)
                        if ink(image, knob.x(), y, bg_l) > 0.5]
                extents[zoom] = max(rows) - min(rows) + 1
            self.assertAlmostEqual(12, extents[1.0], delta=1.5)   # (5 + 1) * 2
            self.assertAlmostEqual(6, extents[0.5], delta=1.6)
            self.assertAlmostEqual(24, extents[2.0], delta=1.6)
        finally:
            h.close()

    def test_node_widget_has_an_even_size_and_the_node_is_in_its_middle(self):
        for zoom in self.ZOOMS:
            width = self.measured[zoom]["node_widget"]
            self.assertEqual(0, width % 2)
            self.assertEqual(2 * glyphs.node_half_size(zoom), width)


class TestMinimumClickAreas(ops.GuiTestCase):
    def setUp(self):
        super().setUp()
        self.a = self.h.double_click(150, 150)
        self.b = self.h.double_click(630, 150)
        self.br = self.h.ctrl_click_branch(self.a, self.b)

    def test_nodes_can_be_hit_at_every_zoom(self):
        for zoom in (2.0, 1.0, 0.5, 0.25, 0.1):
            with self.subTest(zoom=zoom):
                self.h.set_view(zoom, (20, 20))
                widget = self.h.widget_of(self.a)
                self.assertGreaterEqual(widget.width(),
                                        2 * glyphs.MIN_NODE_HIT_RADIUS)
                centre = QPoint(widget.width() // 2, widget.height() // 2)
                self.assertTrue(widget.mask().contains(centre))
                # 4 pixels from the centre is still on the node
                self.assertTrue(widget.mask().contains(
                    centre + QPoint(4, 0)))

    def test_the_node_is_drawn_smaller_than_its_click_area_when_tiny(self):
        self.h.set_view(0.1, (20, 20))
        self.assertEqual(10, self.h.widget_of(self.a).width())
        # but at normal sizes the widget is as big as the drawn node
        self.h.set_view(1.0, (0, 0))
        self.assertEqual(22, self.h.widget_of(self.a).width())

    def test_branches_can_be_hit_at_every_zoom(self):
        for zoom in (2.0, 1.0, 0.5, 0.25, 0.1):
            with self.subTest(zoom=zoom):
                self.h.set_view(zoom, (20, 20))
                widget = self.h.widget_of(self.br)
                start = self.h.widget_of(self.a).get_center()
                end = self.h.widget_of(self.b).get_center()
                x = int(start.x() + (end.x() - start.x()) * 0.25)
                local = widget.mapFromParent(QPoint(x, int(start.y())))
                # on the line and 2 pixels beside it
                self.assertTrue(widget.mask().contains(local))
                self.assertTrue(widget.mask().contains(
                    local + QPoint(0, 2)))
                self.assertTrue(widget.mask().contains(
                    local - QPoint(0, 2)))

    def test_the_click_area_of_a_branch_is_8_pixels_wide_at_100_percent(self):
        widget = self.h.widget_of(self.br)
        start = self.h.widget_of(self.a).get_center()
        end = self.h.widget_of(self.b).get_center()
        x = int(start.x() + (end.x() - start.x()) * 0.25)
        local = widget.mapFromParent(QPoint(x, int(start.y())))
        self.assertTrue(widget.mask().contains(local + QPoint(0, 3)))
        self.assertFalse(widget.mask().contains(local + QPoint(0, 6)))

    def test_handles_can_be_hit_at_every_zoom(self):
        self.h.select_branch(self.br)
        for zoom in (2.0, 1.0, 0.5, 0.25, 0.1):
            with self.subTest(zoom=zoom):
                self.h.set_view(zoom, (20, 20))
                for handle in self.h.selected_handles():
                    knob = self.h.view.to_screen_point(
                        handle.get_world_center())
                    local = handle.mapFromParent(knob)
                    self.assertTrue(handle.mask().contains(local))
                    self.assertTrue(handle.mask().contains(
                        local + QPoint(4, 0)))

    def test_alt_drag_rubber_band_selects_when_zoomed(self):
        for zoom in (1.0, 0.5, 0.25):
            with self.subTest(zoom=zoom):
                self.h.set_view(zoom, (20, 20))
                self.h.field.on_esc_press()
                g0 = self.h.field.mapToGlobal(QPoint(2, 2))
                self.h.press(self.h.field, g0, modifiers=Qt.AltModifier)
                self.h.move(self.h.field, g0 + QPoint(500, 120),
                            modifiers=Qt.AltModifier)
                self.h.release(self.h.field, g0 + QPoint(500, 120),
                               modifiers=Qt.AltModifier)
                selected = set(self.h.field.selection.get())
                # both nodes are inside (the rectangle is in screen pixels)
                needed = {self.a, self.b}
                for node in needed:
                    centre = self.h.widget_of(node).get_center()
                    inside = (2 <= centre.x() <= 502
                              and 2 <= centre.y() <= 122)
                    self.assertEqual(inside, node in selected,
                                     "zoom %s" % zoom)


class TestGridHidingWhenTooDense(ops.GuiTestCase):
    def lines_drawn(self):
        img = self.h.private("grid_widget").grab().toImage()
        bg = img.pixel(0, 0)
        return any(img.pixel(x, y) != bg
                   for x in range(img.width()) for y in range(img.height()))

    def test_grid_is_drawn_when_the_lines_are_6_pixels_apart_or_more(self):
        self.h.model.set_grid_position((13, 7))     # no line at the corner
        for zoom, drawn in ((1.0, True), (0.5, True), (0.25, True),
                            (0.2, True), (0.19, False), (0.1, False)):
            with self.subTest(zoom=zoom):
                self.h.set_view(zoom, (3, 3))
                self.assertEqual(drawn, self.lines_drawn())

    def test_snapping_still_works_when_the_grid_is_not_shown(self):
        self.h.set_view(0.1, (0, 0))
        n = self.h.double_click(100, 100)           # world (1000, 1000)
        self.assertEqual((0, 0), (n.x % 30, n.y % 30))


class TestZoomToFit(TestCase):
    def fit(self, path, width, height):
        h = Harness(width, height)
        h.load(path)
        h.field.on_esc_press()
        h.field.zoom_to_fit()
        h.process_events()
        return h

    def test_the_whole_graph_is_visible_and_centred(self):
        for path in example_files():
            for width, height in ((1000, 700), (500, 350), (260, 200)):
                with self.subTest(example=os.path.basename(path),
                                  size=(width, height)):
                    h = self.fit(path, width, height)
                    try:
                        self.assertLessEqual(h.view.zoom, 1.0)
                        self.assertGreaterEqual(h.view.zoom, 0.1)
                        widgets = list(h.model_widget_map.values())
                        left = min(w.x() for w in widgets)
                        right = max(w.x() + w.width() for w in widgets)
                        top = min(w.y() for w in widgets)
                        bottom = max(w.y() + w.height() for w in widgets)
                        self.assertGreaterEqual(left, 0)
                        self.assertGreaterEqual(top, 0)
                        self.assertLessEqual(right, width)
                        self.assertLessEqual(bottom, height)
                        self.assertEqual([], check_consistency(h))
                    finally:
                        h.close()

    def test_a_graph_that_fits_is_shown_at_100_percent(self):
        h = Harness(1000, 700)
        try:
            h.double_click(150, 150)
            h.double_click(330, 240)
            h.field.zoom_to_fit()
            self.assertEqual(1.0, h.view.zoom)
        finally:
            h.close()

    def test_a_big_graph_is_zoomed_out_as_far_as_needed(self):
        h = Harness(800, 600)
        try:
            h.double_click(150, 150)
            n = h.double_click(600, 400)
            h.controller.move_node(n, 3000, 1500)     # far away
            h.process_events()
            h.field.zoom_to_fit()
            self.assertLess(h.view.zoom, 0.3)
            self.assertGreater(h.view.zoom, 0.1)
            self.assertEqual([], check_consistency(h))
            # even further away: limited to 10%, but still centred
            h.controller.move_node(n, 30000, 15000)
            h.field.zoom_to_fit()
            self.assertEqual(0.1, h.view.zoom)
        finally:
            h.close()

    def test_an_empty_graph_stays_as_it_is(self):
        h = Harness(800, 600)
        try:
            h.field.set_zoom(0.5)
            offset = h.view.offset
            h.field.zoom_to_fit()
            self.assertEqual((0.5, offset), (h.view.zoom, h.view.offset))
        finally:
            h.close()

    def test_zoom_to_fit_changes_neither_graph_nor_undo_history(self):
        h = self.fit(example_files()[-1], 500, 350)
        try:
            self.assertFalse(h.command_handler.can_undo.get())
        finally:
            h.close()


class TestNothingSavedOrExportedDependsOnTheZoom(TestCase):
    def test_tikz_clipboard_and_file_are_the_same_at_every_zoom(self):
        path = [p for p in example_files() if p.endswith("fig_08.sfg")][0]
        outputs = []
        for zoom, offset in ((1.0, (0, 0)), (0.3, (-40, 25)), (0.1, (7, 7))):
            h = Harness(900, 500)
            try:
                h.load(path)
                h.set_view(zoom, offset)
                with tempfile.TemporaryDirectory() as tmp:
                    tex = os.path.join(tmp, "g.tex")
                    h.io.generate_tikz(tex)
                    with open(tex, encoding="utf-8") as f:
                        tikz = f.read()
                    sfg = os.path.join(tmp, "g.sfg")
                    h.save(sfg)
                    with open(sfg, encoding="utf-8") as f:
                        data = json.load(f)
                data.pop("view_origin")
                h.field.select_all()
                h.copy()
                from PySide6.QtWidgets import QApplication
                clipboard = json.loads(QApplication.clipboard().text())
                for d in (data, clipboard):          # lists are in set order
                    d["nodes"].sort(key=lambda n: n["id"])
                    d["branches"].sort(key=lambda b: b["id"])
                outputs.append((tikz, data, clipboard))
            finally:
                h.close()
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])
