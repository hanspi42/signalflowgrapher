from unittest import TestCase
from unittest.mock import MagicMock, patch
from signalflow_algorithms.algorithms.graph import Branch, Node
from signalflow_algorithms.algorithms.graph_operations \
    import ChainingOperation, CombineParallelOperation, \
    EliminateNodeOperation, EliminateSelfLoopOperation, \
    InvertPathOperation, ScalePathOperation


class TestChainingOperation(TestCase):
    def test_get_nodes_in_order(self):
        branch_1 = MagicMock(Branch)
        branch_2 = MagicMock(Branch)
        node = MagicMock(Node)

        operation = ChainingOperation()
        self.assertEqual(None,
                         operation.get_nodes_in_order(branch_1, branch_2))
        branch_1.end = node
        branch_2.start = node
        self.assertEqual(None,
                         operation.get_nodes_in_order(branch_1, branch_2))
        node.ingoing = {branch_1}
        node.outgoing = {branch_2}
        self.assertEqual((branch_1.start, node, branch_2.end),
                         operation.get_nodes_in_order(branch_1, branch_2))
        self.assertEqual((branch_1.start, node, branch_2.end),
                         operation.get_nodes_in_order(branch_2, branch_1))

    def test_get_new_weight(self):
        branch_1 = MagicMock(Branch)
        branch_2 = MagicMock(Branch)
        branch_1.weight = "a"
        branch_2.weight = "b"
        operation = ChainingOperation()

        self.assertEqual("a*b",
                         operation.get_new_weight(branch_1, branch_2))


class TestCombineParallelOperation(TestCase):
    def test_combineable(self):
        branch_1 = MagicMock(Branch)
        branch_2 = MagicMock(Branch)
        node_1 = MagicMock(Node)
        node_2 = MagicMock(Node)

        operation = CombineParallelOperation()
        self.assertEqual(False,
                         operation.combinable(branch_1, branch_2))
        branch_1.end = node_1
        branch_2.end = node_1
        self.assertEqual(False,
                         operation.combinable(branch_1, branch_2))
        branch_1.start = node_2
        branch_2.start = node_2
        self.assertEqual(True,
                         operation.combinable(branch_1, branch_2))

    def test_get_new_weight(self):
        branch_1 = MagicMock(Branch)
        branch_2 = MagicMock(Branch)
        branch_1.weight = "a"
        branch_2.weight = "b"
        operation = CombineParallelOperation()

        self.assertEqual("a + b",
                         operation.get_new_weight(branch_1, branch_2))


class TestEliminateNodeOperation(TestCase):
    def test_get_self_loops(self):
        node = MagicMock(Node)
        simple_cycles = MagicMock()
        branch_1 = MagicMock(Branch)
        branch_2 = MagicMock(Branch)
        branch_1.start = node
        branch_1.weight = "a"
        branch_2.weight = "b"
        simple_cycles.return_value = [[branch_1, branch_2]]

        operation = EliminateNodeOperation()
        with patch("signalflow_algorithms.algorithms"
                   ".graph_operations.simple_cycles",
                   simple_cycles):
            res = operation.get_self_loops(node)
            self.assertEqual({(branch_2.start, "a*b")}, res)

        simple_cycles.assert_called_once_with(node.graph)

    def test_get_new_paths(self):
        node = MagicMock(Node)
        branch_1 = MagicMock(Branch)
        branch_2 = MagicMock(Branch)
        node.ingoing = {branch_1}
        node.outgoing = {branch_2}
        chaining_operation = MagicMock(ChainingOperation)
        chaining_operation.get_new_weight.return_value = "X"
        operation = EliminateNodeOperation()
        with patch("signalflow_algorithms.algorithms"
                   ".graph_operations.ChainingOperation",
                   MagicMock(return_value=chaining_operation)):
            res = operation.get_new_paths(node)
            self.assertEqual({(branch_1.start, branch_2.end, "X")}, res)
        chaining_operation.get_new_weight.assert_called_once_with(branch_1,
                                                                  branch_2)


class TestEliminateSelfLoopOperation(TestCase):
    def test_is_self_loop(self):
        operation = EliminateSelfLoopOperation()
        self.assertFalse(operation.is_self_loop(MagicMock(Branch)))
        branch = MagicMock(Branch)
        branch.end = branch.start
        self.assertTrue(operation.is_self_loop(branch))

    def test_get_affected_branches(self):
        in_1 = MagicMock(Branch)
        in_2 = MagicMock(Branch)
        out = MagicMock(Branch)
        loop = MagicMock(Branch)
        node = MagicMock(Node)
        node.ingoing = {in_1, in_2, loop}
        node.outgoing = {out, loop}
        loop.start = node
        loop.end = node
        operation = EliminateSelfLoopOperation()
        self.assertSetEqual({in_1, in_2},
                            operation.get_affected_branches(loop))

    def test_get_new_affected_branch_weight(self):
        branch_1 = MagicMock(Branch)
        loop = MagicMock(Branch)
        branch_1.weight = "a"
        loop.weight = "b"
        operation = EliminateSelfLoopOperation()
        self.assertEqual(
            "-a/(b - 1)",
            operation.get_new_affected_branch_weight(loop, branch_1))


class TestInvertPathOperation(TestCase):
    def test_start_is_independent_var(self):
        branch = MagicMock(Branch)
        branch.start.ingoing = {}
        operation = InvertPathOperation()
        self.assertFalse(operation.start_is_independent_var([]))
        self.assertTrue(operation.start_is_independent_var([branch]))
        branch.start.ingoing = {MagicMock(Branch)}
        self.assertFalse(operation.start_is_independent_var([branch]))

    def test_get_new_branch_weight(self):
        branch = MagicMock(Branch)
        branch.weight = "a"
        operation = InvertPathOperation()

        self.assertEqual("1/a", operation.get_new_branch_weight(branch))

    def test_get_new_affected_branch_weight(self):
        branch_1 = MagicMock(Branch)
        branch_1.weight = "a"
        branch_2 = MagicMock(Branch)
        branch_2.weight = "b"
        operation = InvertPathOperation()

        self.assertEqual(
            "-b/a",
            operation.get_new_affected_branch_weight(branch_1, branch_2))

    def test_get_affected_branches(self):
        in_1 = MagicMock(Branch)
        in_2 = MagicMock(Branch)
        out = MagicMock(Branch)
        branch = MagicMock(Branch)
        node = MagicMock(Node)
        node.ingoing = {in_1, in_2, branch}
        node.outgoing = {out, branch}
        branch.end = node
        operation = InvertPathOperation()
        self.assertSetEqual({in_1, in_2},
                            operation.get_affected_branches(branch))


class TestScalePathOperation(TestCase):
    def test_scalable(self):
        node = MagicMock(Node)
        node.ingoing = {}
        node.outgoing = {}
        operation = ScalePathOperation()
        self.assertFalse(operation.scalable(node))

        node.ingoing = {MagicMock(Branch)}
        self.assertFalse(operation.scalable(node))

        node.ingoing = set()
        node.outgoing = {MagicMock(Branch)}
        self.assertFalse(operation.scalable(node))

        node.ingoing = {MagicMock(Branch)}
        node.outgoing = {MagicMock(Branch)}
        self.assertTrue(operation.scalable(node))

    def test_get_ingoing_branch_weight(self):
        branch = MagicMock(Branch)
        branch.weight = "a"
        operation = ScalePathOperation()
        self.assertEqual("a/b",
                         operation.get_ingoing_branch_weight(branch, "b"))

    def test_get_outgoing_branch_weight(self):
        branch = MagicMock(Branch)
        branch.weight = "a"
        operation = ScalePathOperation()
        self.assertEqual("a*b",
                         operation.get_outgoing_branch_weight(branch, "b"))
