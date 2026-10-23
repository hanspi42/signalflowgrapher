"""
Seeded random operation sequences against the real GraphField.

After every operation the consistency checker compares all widgets with
the model. The sequences are reproducible (deterministic ids, seeded
random generator), so a failing seed can be replayed and minimised.

Environment variables:
    SFG_FUZZ_SEEDS   number of seeds per test (default 6)
    SFG_FUZZ_STEPS   operations per seed      (default 80)
For a long soak run before a release:  SFG_FUZZ_SEEDS=300 SFG_FUZZ_STEPS=150
"""
import os
import random
from unittest import TestCase

from PySide6.QtCore import QPointF, Qt

from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.consistency import check_consistency

SEEDS = int(os.environ.get("SFG_FUZZ_SEEDS", "6"))
STEPS = int(os.environ.get("SFG_FUZZ_STEPS", "80"))
# zoom factors used by the sequences with a random view (the plan allows
# 10% to 100%; 2.0 is included because the transform supports it)
ZOOMS = (0.1, 0.25, 0.3, 0.5, 0.75, 1.0, 1.0, 2.0)
# Seeds that used to expose the stale-branch-label defect (undo/redo of node
# moves left branch labels at the old position, K1, fixed in step 2)
FORMER_STALE_LABEL_SEEDS = (9, 11)


def _key(model_obj):
    return model_obj.id.int


def run_sequence(seed, steps, allow_redo, random_views=False,
                 minimap=False):
    """
    Returns (ops, problems) of the first failing step, or (ops, []) if the
    whole sequence stayed consistent.
    """
    rnd = random.Random(seed)
    h = Harness()
    ops_done = []

    def change_view():
        h.set_view(rnd.choice(ZOOMS),
                   (rnd.randint(-150, 150), rnd.randint(-150, 150)))

    try:
        if random_views:
            change_view()
        if minimap:
            h.field.set_minimap_visible(True)
        for step in range(steps):
            nodes = sorted(h.nodes, key=_key)
            branches = sorted(h.branches, key=_key)
            everything = nodes + branches
            choices = ["node", "node", "undo", "pan"]
            if allow_redo:
                choices.append("redo")
            if minimap:
                choices += ["minimap_drag", "minimap_drag", "minimap_toggle"]
            if random_views:
                # directly set views, and the zoom operations of the user
                choices += ["view", "view", "zoom_step", "zoom_step",
                            "wheel", "fit"]
            if nodes:
                choices += ["move", "move", "label", "center", "copy",
                            "loop", "delete"]
            if len(nodes) >= 2:
                choices += ["branch", "branch"]
            if branches:
                choices += ["handle", "handle", "branch_label"]
            op = rnd.choice(choices)

            if op == "node":
                h.double_click(rnd.randint(20, 950), rnd.randint(20, 650))
            elif op == "move":
                picked = rnd.sample(nodes, min(len(nodes), rnd.randint(1, 3)))
                h.select(*picked)
                h.drag_node(picked[0], rnd.randint(-120, 120),
                            rnd.randint(-120, 120))
            elif op == "label":
                h.drag_label(rnd.choice(nodes), rnd.randint(-50, 50),
                             rnd.randint(-50, 50))
            elif op == "branch_label":
                h.drag_label(rnd.choice(branches), rnd.randint(-50, 50),
                             rnd.randint(-50, 50))
            elif op == "pan":
                h.pan(rnd.randint(-200, 200), rnd.randint(-200, 200))
            elif op == "center":
                h.field.center_graph()
            elif op == "delete":
                picked = rnd.sample(everything,
                                    min(len(everything), rnd.randint(1, 3)))
                h.select(*picked)
                h.delete_selection()
            elif op == "copy":
                picked = rnd.sample(nodes, min(len(nodes), rnd.randint(1, 3)))
                h.select(*picked)
                h.copy()
                h.paste_at(rnd.randint(20, 900), rnd.randint(20, 600))
            elif op == "branch":
                a, b = rnd.sample(nodes, 2)
                h.ctrl_click_branch(a, b)
            elif op == "loop":
                n = rnd.choice(nodes)
                h.select(n)
                h.click(h.widget_of(n), Qt.ControlModifier)
            elif op == "handle":
                handles = h.select_branch(rnd.choice(branches))
                if handles:
                    h.drag_handle(rnd.choice(handles), rnd.randint(-80, 80),
                                  rnd.randint(-80, 80))
            elif op == "view":
                change_view()
            elif op == "minimap_drag":
                if h.field.minimap_visible:
                    h.minimap_drag(rnd.randint(0, 219), rnd.randint(0, 159),
                                   rnd.randint(-60, 280),
                                   rnd.randint(-60, 220))
            elif op == "minimap_toggle":
                h.field.set_minimap_visible(not h.field.minimap_visible)
            elif op == "zoom_step":
                h.field.zoom_by_steps(
                    rnd.uniform(-3, 3),
                    QPointF(rnd.randint(0, 1000), rnd.randint(0, 700)))
            elif op == "wheel":
                h.wheel(rnd.randint(0, 990), rnd.randint(0, 690),
                        rnd.choice([-360, -120, -30, 30, 120, 240]))
            elif op == "fit":
                h.field.zoom_to_fit()
            elif op == "undo":
                h.undo()
            elif op == "redo":
                h.redo()
            ops_done.append(op)

            problems = check_consistency(h)
            if problems:
                return ops_done, problems
        return ops_done, []
    finally:
        h.close()


class TestFuzz(TestCase):
    def assert_sequences_clean(self, seeds, allow_redo=True):
        for seed in seeds:
            ops, problems = run_sequence(seed, STEPS, allow_redo)
            self.assertEqual(
                [], problems,
                "seed %d failed at step %d (ops: ...%s)\n  %s"
                % (seed, len(ops), ops[-5:], "\n  ".join(problems[:5])))

    def test_random_operations_stay_consistent(self):
        self.assert_sequences_clean(range(SEEDS))

    def test_random_operations_with_random_zoom_and_offset(self):
        """
        The same operations, but the view (zoom and offset) is random and
        changes during the sequence. Everything must stay consistent with
        the model through the transform, and the model must stay valid
        (integer node coordinates).
        """
        for seed in range(SEEDS):
            ops, problems = run_sequence(5000 + seed, STEPS, True,
                                         random_views=True)
            self.assertEqual(
                [], problems,
                "seed %d failed at step %d (ops: ...%s)\n  %s"
                % (5000 + seed, len(ops), ops[-5:],
                   "\n  ".join(problems[:5])))

    def test_random_operations_with_the_mini_map(self):
        """
        The mini map is shown, switched on and off and dragged in between
        all the other operations (and zoom operations): it must stay in its
        corner, over everything, and show the whole graph.
        """
        for seed in range(SEEDS):
            ops, problems = run_sequence(7000 + seed, STEPS, True,
                                         random_views=True, minimap=True)
            self.assertEqual(
                [], problems,
                "seed %d failed at step %d (ops: ...%s)\n  %s"
                % (7000 + seed, len(ops), ops[-5:],
                   "\n  ".join(problems[:5])))

    def test_sequences_that_used_to_leave_stale_branch_labels(self):
        self.assert_sequences_clean(FORMER_STALE_LABEL_SEEDS)

    def test_undo_everything_returns_to_empty_graph(self):
        for seed in range(min(SEEDS, 4)):
            rnd = random.Random(1000 + seed)
            h = Harness()
            try:
                for _ in range(25):
                    nodes = sorted(h.nodes, key=_key)
                    r = rnd.random()
                    if r < 0.45 or len(nodes) < 2:
                        h.double_click(rnd.randint(20, 950),
                                       rnd.randint(20, 650))
                    elif r < 0.75:
                        a, b = rnd.sample(nodes, 2)
                        h.ctrl_click_branch(a, b)
                    elif r < 0.9:
                        h.drag_node(rnd.choice(nodes), rnd.randint(-90, 90),
                                    rnd.randint(-90, 90))
                    else:
                        h.pan(rnd.randint(-100, 100), rnd.randint(-100, 100))
                while h.command_handler.can_undo.get():
                    h.undo()
                self.assertEqual(0, len(h.nodes), "seed %d" % seed)
                self.assertEqual(0, len(h.branches), "seed %d" % seed)
                self.assertEqual([], check_consistency(h), "seed %d" % seed)
            finally:
                h.close()
