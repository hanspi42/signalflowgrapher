"""
Tests for the consistency checker itself ("who watches the watchmen").

Each test builds a healthy GUI state, asserts that the checker is silent,
then breaks exactly one invariant behind the application's back and asserts
that the checker reports it. If one of these tests fails, the checker has
become blind to that class of error and cannot protect the refactoring.
"""
from unittest import TestCase

from PySide6.QtCore import QPoint

from signalflowgrapher.tests.gui.harness import Harness, _private
from signalflowgrapher.tests.gui.consistency import check_consistency


class TestConsistencyChecker(TestCase):
    def setUp(self):
        self.h = Harness()
        self.a = self.h.double_click(150, 150)
        self.b = self.h.double_click(450, 330)
        self.br = self.h.ctrl_click_branch(self.a, self.b)

    def tearDown(self):
        self.h.close()

    def assert_problem(self, fragment):
        problems = check_consistency(self.h)
        self.assertTrue(any(fragment in p for p in problems),
                        "expected a problem containing %r, got %r"
                        % (fragment, problems))

    def test_healthy_state_is_clean(self):
        self.assertEqual([], check_consistency(self.h))

    def test_detects_stale_node_widget(self):
        self.h.widget_of(self.a).move_relative(3, 0)
        self.assert_problem("widget centre")

    def test_detects_model_change_without_event(self):
        # bypass the observable graph: widgets cannot know
        self.a.move(5, 5)
        self.assert_problem("widget centre")

    def test_detects_stale_branch_cache(self):
        self.b.move(10, 0)      # model only, no event
        self.assert_problem("cached end")

    def test_detects_stale_branch_geometry(self):
        w = self.h.widget_of(self.br)
        w.move_relative(0, 40)
        self.assert_problem("mid point")

    def test_detects_stale_label(self):
        self.h.label_of(self.a).move(self.h.label_of(self.a).pos()
                                     + QPoint(9, 0))
        self.assert_problem("label of")

    def test_detects_stale_branch_label(self):
        self.h.label_of(self.br).move(self.h.label_of(self.br).pos()
                                      + QPoint(0, -9))
        self.assert_problem("label of")

    def test_detects_stale_handle(self):
        handles = self.h.select_branch(self.br)
        self.assertEqual(2, len(handles))
        handles[0].move_relative(7, 7)
        # handle geometry itself is derived; break the cached spline
        handles[0]._spline_abs = handles[0]._spline_abs + QPoint(4, 0)
        self.assert_problem("handle spline")

    def test_detects_grid_offset_mismatch_in_field(self):
        self.h.pan(30, 30)
        self.assertEqual([], check_consistency(self.h))
        offset = self.h.grid_offset
        offset += QPoint(1, 0)
        self.assert_problem("GraphField grid offset")

    def test_detects_grid_widget_offset_mismatch(self):
        self.h.pan(10, 10)
        gw = self.h.private("grid_widget")
        gw.set_offset(QPoint(3, 3))
        self.assert_problem("FixedGridWidget offset")

    def test_detects_missing_widget(self):
        self.h.model_widget_map.pop(self.a)
        self.assert_problem("model->widget map")

    def test_detects_missing_label(self):
        self.h.model_label_map.pop(self.a)
        self.assert_problem("model->label map")

    def test_detects_non_integer_node_coordinates(self):
        self.h.model.graph.move_node_relative(self.a, 0.5, 0)
        self.assert_problem("non-integer")

    def test_detects_broken_graph_topology(self):
        self.a._Node__outgoing.discard(self.br)   # damage the model graph
        self.assert_problem("missing in start.outgoing")
