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
from unittest import TestCase, expectedFailure

from PySide6.QtCore import Qt

from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.consistency import (
    check_consistency, STALE_BRANCH_LABELS)

SEEDS = int(os.environ.get("SFG_FUZZ_SEEDS", "6"))
STEPS = int(os.environ.get("SFG_FUZZ_STEPS", "80"))
# Seeds that expose the stale-branch-label defect (undo/redo of node moves
# leaves branch labels at the old position; see
# test_gui_operations.test_known_bug_redo_of_move_leaves_branch_label_stale)
STALE_LABEL_SEEDS = (9, 11)


def _key(model_obj):
    return model_obj.id.int


def run_sequence(seed, steps, allow_redo, known_issues=()):
    """
    Returns (ops, problems) of the first failing step, or (ops, []) if the
    whole sequence stayed consistent.
    """
    rnd = random.Random(seed)
    h = Harness()
    ops_done = []
    try:
        for step in range(steps):
            nodes = sorted(h.nodes, key=_key)
            branches = sorted(h.branches, key=_key)
            everything = nodes + branches
            choices = ["node", "node", "undo", "pan"]
            if allow_redo:
                choices.append("redo")
            if nodes:
                choices += ["move", "move", "label", "center", "copy",
                            "loop", "delete"]
            if len({(n.x, n.y) for n in nodes}) >= 2:
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
                if (a.x, a.y) == (b.x, b.y):
                    op = "branch(skipped: coincident nodes)"
                else:
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
            elif op == "undo":
                h.undo()
            elif op == "redo":
                h.redo()
            ops_done.append(op)

            problems = check_consistency(h, known_issues)
            if problems:
                return ops_done, problems
        return ops_done, []
    finally:
        h.close()


class TestFuzz(TestCase):
    def assert_sequences_clean(self, seeds, allow_redo, known_issues=()):
        for seed in seeds:
            ops, problems = run_sequence(seed, STEPS, allow_redo,
                                         known_issues)
            self.assertEqual(
                [], problems,
                "seed %d failed at step %d (ops: ...%s)\n  %s"
                % (seed, len(ops), ops[-5:], "\n  ".join(problems[:5])))

    def test_random_operations_stay_consistent(self):
        """Strict, except for the one documented branch-label defect."""
        self.assert_sequences_clean(range(SEEDS), allow_redo=True,
                                    known_issues=(STALE_BRANCH_LABELS,))

    @expectedFailure
    def test_known_bug_random_operations_branch_labels(self):
        """Same sequences without tolerance: stale branch labels."""
        self.assert_sequences_clean(STALE_LABEL_SEEDS, allow_redo=True)

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
                        if (a.x, a.y) != (b.x, b.y):
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
