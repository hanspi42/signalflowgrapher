"""
Scenario tests for the GraphField: create / move / pan / copy / paste /
delete / undo / save / load, driven with synthetic mouse events.

After every user-visible step the consistency checker compares all widgets
with the model (see consistency.py). These tests pin down the behaviour of
the application *before* the V3.0 refactoring and must keep passing after
every step of the plan (DEVDOCU.md).

Tests named test_known_bug_* document defects that exist today and are
decorated with @expectedFailure. The step of the plan that fixes a defect
must remove the decorator (an unexpected success is reported as a failure,
so the decorator cannot be forgotten).
"""
import math
import os
import tempfile
import signal
from unittest import TestCase, expectedFailure

from PySide6.QtCore import QPoint, Qt

from signalflowgrapher.gui.grid import GRID_SIZE
from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.consistency import (
    assert_consistent, check_consistency)

GRID = GRID_SIZE


def coords(h: Harness):
    """Order-independent snapshot of all model coordinates."""
    d = h.model.graph.to_dict()
    nodes = sorted((n["id"], n["x"], n["y"], n["label_dx"], n["label_dy"],
                    n["name"]) for n in d["nodes"])
    branches = sorted((b["id"], b["start"], b["end"], b["weight"],
                       b["spline1_x"], b["spline1_y"], b["spline2_x"],
                       b["spline2_y"], b["label_dx"], b["label_dy"])
                      for b in d["branches"])
    return nodes, branches, tuple(h.model.get_grid_position())


class GuiTestCase(TestCase):
    def setUp(self):
        self.h = Harness()

    def tearDown(self):
        self.h.close()

    def ok(self, context=""):
        assert_consistent(self, self.h, context)

    def make_two_nodes_and_branch(self, p1=(100, 100), p2=(300, 190)):
        a = self.h.double_click(*p1)
        b = self.h.double_click(*p2)
        br = self.h.ctrl_click_branch(a, b)
        return a, b, br


class TestCreate(GuiTestCase):
    def test_create_node_snaps_to_grid(self):
        n = self.h.double_click(100, 100)
        self.assertEqual((90, 90), (n.x, n.y))      # 30*round((100-2)/30)
        self.assertEqual((0, 30), (n.label_dx, n.label_dy))
        self.ok("create node")

    def test_create_node_undo_redo(self):
        n = self.h.double_click(100, 100)
        self.h.undo()
        self.assertEqual(0, len(self.h.nodes))
        self.ok("undo create node")
        self.h.redo()
        self.assertEqual(1, len(self.h.nodes))
        self.assertEqual((90, 90), (self.h.nodes[0].x, self.h.nodes[0].y))
        self.ok("redo create node")

    def test_create_node_on_panned_grid(self):
        self.h.pan(13, 7)
        n = self.h.double_click(200, 200)
        gx, gy = self.h.model.get_grid_position()
        self.assertEqual((13, 7), (gx, gy))
        self.assertEqual(0, (n.x - gx) % GRID)
        self.assertEqual(0, (n.y - gy) % GRID)
        self.ok("create node on panned grid")

    def test_create_branch_between_two_nodes(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.assertIs(a, br.start)
        self.assertIs(b, br.end)
        self.assertIn(br, a.outgoing)
        self.assertIn(br, b.ingoing)
        # splines lie on the straight line between the nodes
        self.assertAlmostEqual((a.x + b.x) / 2, br.spline1_x, delta=1)
        self.assertAlmostEqual((a.y + b.y) / 2, br.spline1_y, delta=1)
        self.assertAlmostEqual(30, math.hypot(br.label_dx, br.label_dy),
                               delta=1)
        self.ok("create branch")

    def test_create_branch_undo_redo(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.undo()
        self.assertEqual(0, len(self.h.branches))
        self.ok("undo create branch")
        self.h.redo()
        self.assertEqual(1, len(self.h.branches))
        self.ok("redo create branch")

    def test_create_self_loop(self):
        n = self.h.double_click(300, 300)
        self.h.select(n)
        self.h.click(self.h.widget_of(n), Qt.ControlModifier)
        self.assertEqual(1, len(self.h.branches))
        loop = self.h.branches[0]
        self.assertIs(loop.start, loop.end)
        self.assertAlmostEqual(
            100, math.hypot(loop.spline1_x - n.x, loop.spline1_y - n.y),
            delta=1)
        self.ok("create self loop")

    def test_parallel_branches_get_different_shapes(self):
        a, b, br1 = self.make_two_nodes_and_branch()
        br2 = self.h.ctrl_click_branch(a, b)
        self.assertNotEqual((br1.spline1_x, br1.spline1_y),
                            (br2.spline1_x, br2.spline1_y))
        self.ok("parallel branches")


class TestMove(GuiTestCase):
    def test_move_node_moves_attached_spline_points(self):
        a, b, br = self.make_two_nodes_and_branch()
        s1 = (br.spline1_x, br.spline1_y)
        s2 = (br.spline2_x, br.spline2_y)
        a0, b0 = (a.x, a.y), (b.x, b.y)
        self.h.drag_node(b, 60, 30)
        self.assertEqual((b0[0] + 60, b0[1] + 30), (b.x, b.y))
        self.assertEqual(a0, (a.x, a.y))
        self.assertEqual(s1, (br.spline1_x, br.spline1_y))   # start side
        self.assertEqual((s2[0] + 60, s2[1] + 30),
                         (br.spline2_x, br.spline2_y))       # end side
        self.ok("move end node")

    def test_move_start_node_moves_spline1(self):
        a, b, br = self.make_two_nodes_and_branch()
        s1 = (br.spline1_x, br.spline1_y)
        s2 = (br.spline2_x, br.spline2_y)
        self.h.drag_node(a, -30, 60)
        self.assertEqual((s1[0] - 30, s1[1] + 60),
                         (br.spline1_x, br.spline1_y))
        self.assertEqual(s2, (br.spline2_x, br.spline2_y))
        self.ok("move start node")

    def test_move_selection_moves_everything_by_same_delta(self):
        a, b, br = self.make_two_nodes_and_branch()
        before = coords(self.h)
        self.h.select(a, b)
        self.h.drag_node(a, 30, 30)
        d = self.h.model.graph.to_dict()
        for n in d["nodes"]:
            orig = next(x for x in before[0] if x[0] == n["id"])
            self.assertEqual((orig[1] + 30, orig[2] + 30), (n["x"], n["y"]))
        # both spline points moved with their node
        self.assertEqual(before[1][0][4] + 30, br.spline1_x)
        self.assertEqual(before[1][0][6] + 30, br.spline2_x)
        self.ok("move selection")

    def test_move_snaps_to_grid_and_ctrl_moves_freely(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.field.on_ctrl_press()                     # grid off
        x, y = a.x, a.y
        self.h.drag_node(a, 7, 5)
        self.assertEqual((x + 7, y + 5), (a.x, a.y))
        self.ok("free move")
        self.h.field.on_ctrl_release()                   # grid on
        self.h.drag_node(a, 20, 20)
        gx, gy = self.h.model.get_grid_position()
        self.assertEqual(0, (a.x - gx) % GRID)
        self.assertEqual(0, (a.y - gy) % GRID)
        self.ok("snapped move")

    def test_move_undo_restores_everything(self):
        a, b, br = self.make_two_nodes_and_branch()
        before = coords(self.h)
        self.h.drag_node(b, 60, 30)
        self.assertNotEqual(before, coords(self.h))
        self.h.undo()
        self.assertEqual(before, coords(self.h))
        self.ok("undo move")

    def test_move_is_one_undo_step(self):
        a, b, br = self.make_two_nodes_and_branch()
        before = coords(self.h)
        self.h.drag_node(b, 90, 60, steps=7)       # many mouse-move events
        self.h.undo()                              # ... but a single undo
        self.assertEqual(before, coords(self.h))
        self.ok("undo of a multi-step drag")

    @expectedFailure
    def test_known_bug_redo_of_move_leaves_branch_label_stale(self):
        """
        move node -> undo -> redo: the branch label stays at the old place.
        Cause: redo applies the branch transform before the node move and
        branch labels do not react to node events. Fix: step 2 (idempotent
        widget refresh) or earlier in step 1.
        """
        a, b, br = self.make_two_nodes_and_branch()
        self.h.drag_node(b, 60, 30)
        self.h.undo()
        self.h.redo()
        self.ok("redo move")


class TestHandlesAndLabels(GuiTestCase):
    def test_handles_appear_for_single_branch_selection(self):
        a, b, br = self.make_two_nodes_and_branch()
        handles = self.h.select_branch(br)
        self.assertEqual(2, len(handles))
        self.ok("branch selected")

    def test_handle_drag_moves_one_spline_mirrored_and_on_grid(self):
        a, b, br = self.make_two_nodes_and_branch()
        s2 = (br.spline2_x, br.spline2_y)
        s1 = (br.spline1_x, br.spline1_y)
        handle = self.h.select_branch(br)[0]
        knob_before = handle.get_center()
        self.h.drag_handle(handle, 45, 31)
        self.assertEqual(s2, (br.spline2_x, br.spline2_y))
        # handle is mirrored: moving the knob right/down moves spline
        # left/up
        self.assertLess(br.spline1_x, s1[0])
        self.assertLess(br.spline1_y, s1[1])
        knob = self.h.selected_handles()[0].get_center()
        self.assertEqual(0, (round(knob.x()) - self.h.grid_offset.x()) % GRID)
        self.assertEqual(0, (round(knob.y()) - self.h.grid_offset.y()) % GRID)
        self.ok("handle drag")

    def test_handle_follows_node_with_integer_origin(self):
        """The handle origin is an int point even for float coordinates."""
        a, b, br = self.make_two_nodes_and_branch()
        handles = self.h.select_branch(br)
        self.h.model.graph.move_node_relative(a, 0.5, 0.5)
        self.h.process_events()
        handle = next(x for x in self.h.selected_handles()
                      if x.get_node() is a)
        self.assertEqual(QPoint(int(a.x), int(a.y)), handle._origin_abs)

    def test_handle_drag_undo_redo(self):
        a, b, br = self.make_two_nodes_and_branch()
        handle = self.h.select_branch(br)[1]
        before = coords(self.h)
        self.h.drag_handle(handle, -60, 40)
        after = coords(self.h)
        self.assertNotEqual(before, after)
        self.h.undo()
        self.assertEqual(before, coords(self.h))
        self.ok("undo handle")
        self.h.redo()
        self.assertEqual(after, coords(self.h))
        self.ok("redo handle")

    def test_node_label_drag_only_changes_offset(self):
        a, b, br = self.make_two_nodes_and_branch()
        before = coords(self.h)
        pos = (a.x, a.y)
        self.h.drag_label(a, 20, -33)
        self.assertEqual(pos, (a.x, a.y))
        self.assertNotEqual((0, 30), (a.label_dx, a.label_dy))
        self.assertEqual(before[1], coords(self.h)[1])   # branches untouched
        self.ok("node label drag")
        self.h.undo()
        self.assertEqual(before, coords(self.h))
        self.ok("undo node label drag")
        self.h.redo()
        self.ok("redo node label drag")

    def test_branch_label_drag_and_undo_redo(self):
        a, b, br = self.make_two_nodes_and_branch()
        before = coords(self.h)
        self.h.drag_label(br, -30, 45)
        after = coords(self.h)
        self.assertNotEqual(before, after)
        self.ok("branch label drag")
        self.h.undo()
        self.assertEqual(before, coords(self.h))
        self.ok("undo branch label drag")
        self.h.redo()
        self.assertEqual(after, coords(self.h))
        self.ok("redo branch label drag")

    def test_label_moves_with_node_and_branch(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.drag_label(br, 15, 15)
        offset = (br.label_dx, br.label_dy)
        self.h.drag_node(a, 60, 60)
        self.assertEqual(offset, (br.label_dx, br.label_dy))  # relative
        self.ok("label follows branch")


class TestPan(GuiTestCase):
    def test_pan_shifts_every_model_coordinate(self):
        a, b, br = self.make_two_nodes_and_branch()
        n0, b0, g0 = coords(self.h)
        self.h.pan(33, 17)
        n1, b1, g1 = coords(self.h)
        for o, n in zip(n0, n1):
            self.assertEqual((o[1] + 33, o[2] + 17, o[3], o[4]),
                             (n[1], n[2], n[3], n[4]))   # labels unchanged
        for o, n in zip(b0, b1):
            self.assertEqual((o[4] + 33, o[5] + 17, o[6] + 33, o[7] + 17),
                             (n[4], n[5], n[6], n[7]))
            self.assertEqual((o[8], o[9]), (n[8], n[9]))
        self.assertEqual((33, 17), g1)
        self.ok("pan")

    def test_pan_accumulates_and_is_not_undoable(self):
        a, b, br = self.make_two_nodes_and_branch()
        undo_depth = self.h.command_handler.can_undo.get()
        self.h.pan(33, 17)
        self.h.pan(-50, 40)
        self.assertEqual((-17, 57), tuple(self.h.model.get_grid_position()))
        self.assertEqual(undo_depth, self.h.command_handler.can_undo.get())
        self.ok("two pans")

    def test_move_after_pan_snaps_to_panned_grid(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.pan(13, 7)
        self.h.drag_node(a, 31, 29)
        gx, gy = self.h.model.get_grid_position()
        self.assertEqual(0, (a.x - gx) % GRID)
        self.assertEqual(0, (a.y - gy) % GRID)
        self.ok("move on panned grid")

    def test_center_graph(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.pan(300, 200)
        self.h.field.center_graph()
        widgets = list(self.h.model_widget_map.values())
        min_x = min(w.x() for w in widgets)
        max_x = max(w.x() + w.width() for w in widgets)
        min_y = min(w.y() for w in widgets)
        max_y = max(w.y() + w.height() for w in widgets)
        self.assertAlmostEqual(self.h.field.width() / 2,
                               (min_x + max_x) / 2, delta=1)
        self.assertAlmostEqual(self.h.field.height() / 2,
                               (min_y + max_y) / 2, delta=1)
        self.ok("center graph")

    def test_center_empty_graph_is_noop(self):
        self.h.field.center_graph()
        self.ok("center empty graph")

    def test_pan_with_handles_visible(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.select_branch(br)
        self.h.pan(-20, 45)
        self.ok("pan with handles")


class TestCopyPaste(GuiTestCase):
    def test_copy_paste_translates_whole_block_to_grid(self):
        a, b, br = self.make_two_nodes_and_branch()
        n0, b0, _ = coords(self.h)
        self.h.select(a, b, br)
        self.h.copy()
        self.h.paste_at(500, 400)
        self.assertEqual(4, len(self.h.nodes))
        self.assertEqual(2, len(self.h.branches))
        new_nodes = [n for n in self.h.nodes if n not in (a, b)]
        dx = min(n.x for n in new_nodes) - min(a.x, b.x)
        dy = min(n.y for n in new_nodes) - min(a.y, b.y)
        # relative geometry is preserved
        self.assertEqual({(a.x + dx, a.y + dy), (b.x + dx, b.y + dy)},
                         {(n.x, n.y) for n in new_nodes})
        new_br = next(x for x in self.h.branches if x is not br)
        self.assertEqual((br.spline1_x + dx, br.spline1_y + dy),
                         (new_br.spline1_x, new_br.spline1_y))
        self.assertEqual((br.label_dx, br.label_dy),
                         (new_br.label_dx, new_br.label_dy))
        self.ok("paste")

    def test_paste_selects_pasted_items_and_is_one_undo_step(self):
        a, b, br = self.make_two_nodes_and_branch()
        before = coords(self.h)
        self.h.select(a, b, br)
        self.h.copy()
        self.h.paste_at(500, 400)
        self.assertEqual(3, len(self.h.field.get_selection()))
        self.h.undo()
        self.assertEqual(before, coords(self.h))
        self.ok("undo paste")

    def test_paste_restores_names_and_weights(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.controller.set_node_name(a, "in")
        self.h.controller.set_node_name(b, "out")
        self.h.controller.set_branch_weight(br, "H1")
        self.h.select(a, b, br)
        self.h.copy()
        self.h.paste_at(600, 300)
        names = sorted(n.name for n in self.h.nodes)
        self.assertEqual(["in", "in", "out", "out"], names)
        self.assertEqual(["H1", "H1"], sorted(x.weight
                                              for x in self.h.branches))
        self.ok("paste names")

    def test_only_branches_with_both_nodes_selected_are_copied(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.select(a, br)
        self.h.copy()
        self.h.paste_at(600, 300)
        self.assertEqual(3, len(self.h.nodes))
        self.assertEqual(1, len(self.h.branches))
        self.ok("paste without branch")

    def test_cut_and_paste(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.select(a, b, br)
        self.h.field.cut_to_clipboard()
        self.h.process_events()
        self.assertEqual(0, len(self.h.nodes))
        self.ok("cut")
        self.h.paste_at(400, 300)
        self.assertEqual(2, len(self.h.nodes))
        self.assertEqual(1, len(self.h.branches))
        self.ok("paste after cut")

    def test_paste_after_pan_stays_on_the_panned_grid(self):
        """Paste used to snap to a grid that ignored the pan (K2, 1b)."""
        a, b, br = self.make_two_nodes_and_branch()
        self.h.pan(13, 7)
        self.h.select(a, b, br)
        self.h.copy()
        self.h.paste_at(500, 400)
        gx, gy = self.h.model.get_grid_position()
        for n in self.h.nodes:
            self.assertEqual(0, (n.x - gx) % GRID, "node off grid in x")
            self.assertEqual(0, (n.y - gy) % GRID, "node off grid in y")

    def test_paste_keeps_node_label_offset(self):
        """Pasted nodes used to get the default label offset (K3, 1b)."""
        a, b, br = self.make_two_nodes_and_branch()
        self.h.drag_label(a, 30, -60)
        offset = (a.label_dx, a.label_dy)
        self.assertNotEqual((0, 30), offset)
        self.h.select(a)
        self.h.copy()
        self.h.paste_at(600, 450)
        pasted = [n for n in self.h.nodes if n not in (a, b)][0]
        self.assertEqual(offset, (pasted.label_dx, pasted.label_dy))


class TestDelete(GuiTestCase):
    def test_delete_node_removes_attached_branches(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.select(b)
        self.h.delete_selection()
        self.assertEqual(1, len(self.h.nodes))
        self.assertEqual(0, len(self.h.branches))
        self.ok("delete node")

    def test_delete_undo_redo(self):
        a, b, br = self.make_two_nodes_and_branch()
        before = coords(self.h)
        self.h.select(b)
        self.h.delete_selection()
        self.h.undo()
        self.assertEqual(before, coords(self.h))
        self.ok("undo delete")
        self.h.redo()
        self.assertEqual(1, len(self.h.nodes))
        self.ok("redo delete")
        self.h.undo()
        self.assertEqual(before, coords(self.h))
        self.ok("second undo delete")

    def test_undo_delete_after_pan_restores_at_panned_position(self):
        """The 'gridpos_atCreation' pan compensation of the commands."""
        a, b, br = self.make_two_nodes_and_branch()
        before_nodes, before_branches, _ = coords(self.h)
        self.h.select(b)
        self.h.delete_selection()
        self.h.pan(40, 25)
        self.h.undo()
        nodes, branches, grid = coords(self.h)
        self.assertEqual((40, 25), grid)
        for o, n in zip(before_nodes, nodes):
            self.assertEqual((o[1] + 40, o[2] + 25), (n[1], n[2]))
        for o, n in zip(before_branches, branches):
            self.assertEqual((o[4] + 40, o[5] + 25, o[6] + 40, o[7] + 25),
                             (n[4], n[5], n[6], n[7]))
        self.ok("undo delete after pan")

    def test_undo_create_after_pan_then_redo(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.undo()                      # remove branch
        self.h.pan(-30, 60)
        self.h.redo()                      # re-add branch
        self.ok("redo create branch after pan")
        n = self.h.model.get_grid_position()
        self.assertEqual((-30, 60), tuple(n))


class TestCoincidentNodes(GuiTestCase):
    """
    Two nodes on the same grid point can be connected (K4, 1e). Before, the
    first branch raised 'Unable to calculate angle' and a second branch
    would have looped forever in create_branch_auto_pos.
    """

    def setUp(self):
        super().setUp()
        # a hang must fail the test instead of blocking the test run
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, self._timeout)
            signal.alarm(30)

    def tearDown(self):
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
        super().tearDown()

    @staticmethod
    def _timeout(signum, frame):
        raise TimeoutError("create_branch_auto_pos does not terminate")

    def test_branch_between_coincident_nodes(self):
        a = self.h.double_click(150, 150)
        b = self.h.double_click(150, 150)
        self.assertEqual((a.x, a.y), (b.x, b.y))
        br = self.h.ctrl_click_branch(a, b)
        # bent below the nodes, not a zero length line
        self.assertNotEqual((a.x, a.y), (br.spline1_x, br.spline1_y))
        self.assertEqual((0, 30), (br.label_dx, br.label_dy))
        self.ok("branch between coincident nodes")

    def test_parallel_and_opposite_branches_between_coincident_nodes(self):
        a = self.h.double_click(150, 150)
        b = self.h.double_click(150, 150)
        first = self.h.ctrl_click_branch(a, b)
        second = self.h.ctrl_click_branch(a, b)
        third = self.h.ctrl_click_branch(b, a)
        shapes = {(x.spline1_x, x.spline1_y, x.spline2_x, x.spline2_y)
                  for x in (first, second, third)}
        self.assertEqual(3, len(shapes), "branches lie on top of each other")
        self.ok("three branches between coincident nodes")

    def test_nearby_nodes_get_a_branch_with_the_old_rules(self):
        a = self.h.double_click(150, 150)
        b = self.h.double_click(180, 150)
        br = self.h.ctrl_click_branch(a, b)
        self.assertEqual((a.x + b.x) / 2, br.spline1_x)   # straight line
        self.ok("branch between nearby nodes")


class TestSaveLoad(GuiTestCase):
    def test_roundtrip_with_pan_keeps_coordinates_and_grid(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.drag_label(br, 20, 20)
        self.h.pan(13, 7)
        before = coords(self.h)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "g.sfg")
            self.h.save(path)
            h2 = Harness()
            try:
                h2.load(path)
                self.assertEqual(before, coords(h2))
                self.assertEqual([], check_consistency(h2))
                # grid phase survives: new nodes are on the same grid
                n = h2.double_click(210, 210)
                gx, gy = h2.model.get_grid_position()
                self.assertEqual(0, (n.x - gx) % GRID)
                self.assertEqual(0, (n.y - gy) % GRID)
                self.assertEqual([], check_consistency(h2))
            finally:
                h2.close()

    def test_new_graph_clears_widgets(self):
        self.make_two_nodes_and_branch()
        self.h.io.new_graph()
        self.h.process_events()
        self.assertEqual(0, len(self.h.model_widget_map))
        self.assertEqual(0, len(self.h.model_label_map))
        self.ok("new graph")
