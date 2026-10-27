"""
Tests of the idempotent widget refresh (step 2 of the V3.0 plan).

Widgets derive position and shape from the model. The result must not
depend on which events arrived, how often, or in which order. These
properties are what the later steps (view transform, zoom) build on:
a zoom change is "refresh everything".
"""
from unittest import TestCase

from PySide6.QtCore import QPoint

from signalflowgrapher.gui.branch_widget import BranchWidget
from signalflowgrapher.model.model import (
    CurvedBranchTransformedEvent, PositionedNodeMovedEvent)
from signalflowgrapher.tests.gui import test_gui_operations as ops
from signalflowgrapher.tests.gui.consistency import check_consistency
from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.snapshot import (
    geometry_snapshot, snapshots_close)


class RefreshTestCase(ops.GuiTestCase):
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
        h.drag_handle(h.select_branch(self.bc)[1], 40, -30)   # handles shown

    def dispatch(self, event):
        """Deliver an event to the GraphField like the model does."""
        self.h.field._GraphField__handle_model_change(event)
        self.h.process_events()

    def geometry(self):
        return geometry_snapshot(self.h)


class TestIdempotence(RefreshTestCase):
    def test_refresh_changes_nothing_when_up_to_date(self):
        before = self.geometry()
        self.h.field.refresh_widgets()
        self.h.field.refresh_widgets()
        self.assertEqual([], snapshots_close(before, self.geometry(), 0))
        self.ok("refresh")

    def test_forced_refresh_changes_nothing_when_up_to_date(self):
        before = self.geometry()
        self.h.field.refresh_widgets(force=True)
        self.h.field.refresh_widgets(force=True)
        self.assertEqual([], snapshots_close(before, self.geometry(), 0))
        self.ok("forced refresh")

    def test_forced_refresh_repairs_displaced_widgets(self):
        h = self.h
        for obj in (self.a, self.ab):
            w = h.widget_of(obj)
            w.move(w.pos() + QPoint(5, -7))
        lw = h.label_of(self.b)
        lw.move(lw.pos() + QPoint(9, 9))
        handle = h.selected_handles()[0]
        handle.move(handle.pos() + QPoint(3, 3))
        self.assertTrue(check_consistency(h), "displacement not detected")
        h.field.refresh_widgets(force=True)
        self.ok("forced refresh after displacing widgets")


class TestEventsDoNotCarryState(RefreshTestCase):
    """Widgets read the model; the content of an event does not matter."""

    def test_node_moved_event_with_wrong_delta(self):
        before = self.geometry()
        self.dispatch(PositionedNodeMovedEvent(self.b, 50, -50))
        self.assertEqual([], snapshots_close(before, self.geometry(), 0))
        self.ok("spurious node moved event")

    def test_duplicate_node_moved_event(self):
        before = self.geometry()
        for _ in range(3):
            self.dispatch(PositionedNodeMovedEvent(self.b, 0, 0))
        self.assertEqual([], snapshots_close(before, self.geometry(), 0))
        self.ok("duplicate node moved events")

    def test_repeated_view_changed_signals(self):
        """The view signal carries nothing; every handling shows the view."""
        before = self.geometry()
        for _ in range(3):
            self.h.field._GraphField__on_view_changed()
        self.h.process_events()
        self.assertEqual([], snapshots_close(before, self.geometry(), 0))
        self.ok("repeated view changed signals")

    def test_branch_transformed_event_with_wrong_delta(self):
        before = self.geometry()
        self.dispatch(CurvedBranchTransformedEvent(self.ab, 9, 9, 9, 9))
        self.assertEqual([], snapshots_close(before, self.geometry(), 0))
        self.ok("spurious branch transformed event")

    def test_model_changed_without_the_matching_event_is_picked_up(self):
        """
        Any later event of the same objects shows the current model state,
        not only the change that the event describes.
        """
        self.a.move(30, 0)                      # no event for this change
        self.dispatch(PositionedNodeMovedEvent(self.a, 0, 0))
        self.ok("late event")


class TestOrderOfEvents(TestCase):
    """
    Undo and redo apply the parts of a move in a different order than the
    original move (K1). The final widgets must be identical.
    """

    def build(self):
        h = Harness()
        a = h.double_click(120, 120)
        b = h.double_click(420, 240)
        br = h.ctrl_click_branch(a, b)
        h.drag_label(br, 30, 30)
        return h, a, b, br

    def test_node_first_or_branch_first_gives_the_same_widgets(self):
        results = []
        for node_first in (True, False):
            h, a, b, br = self.build()
            try:
                g = h.model.graph
                if node_first:
                    g.move_node_relative(b, 60, 30)
                    g.transform_branch(br, 0, 0, 60, 30)
                else:
                    g.transform_branch(br, 0, 0, 60, 30)
                    g.move_node_relative(b, 60, 30)
                h.process_events()
                self.assertEqual([], check_consistency(h),
                                 "node_first=%s" % node_first)
                results.append(geometry_snapshot(h))
            finally:
                h.close()
        self.assertEqual([], snapshots_close(results[0], results[1], 0))


class TestPanIsCheap(RefreshTestCase):
    def count_geometry_rebuilds(self, action):
        calls = []
        original = BranchWidget.updateGeometry

        def counting(widget):
            calls.append(widget)
            return original(widget)

        BranchWidget.updateGeometry = counting
        try:
            action()
        finally:
            BranchWidget.updateGeometry = original
        return len(calls)

    def test_pan_moves_branch_widgets_without_rebuilding_their_shape(self):
        n = self.count_geometry_rebuilds(lambda: self.h.pan(37, -21))
        self.assertEqual(0, n)
        self.ok("pan")

    def test_moving_a_node_rebuilds_only_the_attached_branches(self):
        n = self.count_geometry_rebuilds(
            lambda: self.h.drag_node(self.c, 60, 30))
        self.assertGreater(n, 0)
        # only bc is attached to c; every mouse move rebuilds it a few times
        # (node move and spline move), never the unrelated branch ab
        calls = []
        original = BranchWidget.updateGeometry

        def counting(widget):
            calls.append(widget)
            return original(widget)

        BranchWidget.updateGeometry = counting
        try:
            self.h.drag_node(self.c, -60, -30)
        finally:
            BranchWidget.updateGeometry = original
        self.assertNotIn(self.h.widget_of(self.ab), calls)
        self.ok("move node")

    def test_pan_moves_every_label_by_exactly_the_pan(self):
        """Also with negative coordinates (labels use floor, not int)."""
        h = self.h
        before = {o: lw.pos() for o, lw in h.model_label_map.items()}
        h.pan(-560, -330)
        for obj, lw in h.model_label_map.items():
            self.assertEqual(before[obj] + QPoint(-560, -330), lw.pos(),
                             "label moved by a different amount than the pan")
        self.ok("pan to negative coordinates")
