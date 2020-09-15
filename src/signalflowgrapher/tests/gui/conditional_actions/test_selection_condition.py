from unittest import TestCase
from unittest.mock import MagicMock, patch
from signalflowgrapher.model.model import CurvedBranch, PositionedNode
from signalflowgrapher.gui.conditional_actions.selection_condition \
    import SpecificNumBranchesSelected, SpecificNumNodesSelected, \
    MaxNumNodesSelected, SubsequentBranchesSelected, \
    MinNumNodesOrBranchesSelected, TwoParallelBranchesSelected, \
    BranchIsSelfLoop, MinNumNodesSelected, PathHasIndependentStartVar, \
    AllNodesScalable, SelectedBranchesWeighted, BranchesNextToNodesWeighted, \
    NeighbourBranchesWeighted, NodesHaveNoSelfLoops, \
    AllBranchesWeighted, MiddleNodeHasNumBranches
from signalflow_algorithms.algorithms.graph_operations \
    import CombineParallelOperation, InvertPathOperation, \
    ScalePathOperation


class TestSpecificNumNodesSelected(TestCase):
    def test_is_fulfilled(self):
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)
        n3 = MagicMock(PositionedNode)
        b1 = MagicMock(CurvedBranch)

        condition = SpecificNumNodesSelected(0)
        condition.update_selection([])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())

        condition = SpecificNumNodesSelected(1)
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, n2])
        self.assertFalse(condition.is_fulfilled())

        condition = SpecificNumNodesSelected(3)
        condition.update_selection([n1, n2])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, n2, n3])
        self.assertTrue(condition.is_fulfilled())


class TestMinNumNodesSelected(TestCase):
    def test_is_fulfilled(self):
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)
        n3 = MagicMock(PositionedNode)
        b1 = MagicMock(CurvedBranch)

        condition = MinNumNodesSelected(0)
        condition.update_selection([])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())

        condition = MinNumNodesSelected(1)
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, n2])
        self.assertTrue(condition.is_fulfilled())

        condition = MinNumNodesSelected(3)
        condition.update_selection([n1, n2])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, n2, n3])
        self.assertTrue(condition.is_fulfilled())


class TestMaxNumNodesSelected(TestCase):
    def test_is_fulfilled(self):
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)
        n3 = MagicMock(PositionedNode)
        b1 = MagicMock(CurvedBranch)

        condition = MaxNumNodesSelected(0)
        condition.update_selection([])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())

        condition = MaxNumNodesSelected(1)
        condition.update_selection([])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, n2])
        self.assertFalse(condition.is_fulfilled())

        condition = MaxNumNodesSelected(3)
        condition.update_selection([])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1, n2])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1, n2, n3])
        self.assertTrue(condition.is_fulfilled())


class TestSpecificNumBranchesSelected(TestCase):
    def test_is_fulfilled(self):
        n1 = MagicMock(PositionedNode)
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b3 = MagicMock(CurvedBranch)

        condition = SpecificNumBranchesSelected(0)
        condition.update_selection([])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertFalse(condition.is_fulfilled())

        condition = SpecificNumBranchesSelected(1)
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1, b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1, b2])
        self.assertFalse(condition.is_fulfilled())

        condition = SpecificNumBranchesSelected(3)
        condition.update_selection([b1, b2, b3])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1, b3])
        self.assertFalse(condition.is_fulfilled())


class TestSubsequentBranchesSelected(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b3 = MagicMock(CurvedBranch)

        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)

        b1.end = n1
        b2.start = n1
        b2.end = n2
        b3.start = n2

        condition = SubsequentBranchesSelected()
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1, b2])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1, b2, b3])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b3])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b3, b2])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1, b3])
        self.assertFalse(condition.is_fulfilled())


class TestMiddleNodeHasNumBranches(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b3 = MagicMock(CurvedBranch)

        n1 = MagicMock(PositionedNode)

        b1.end = n1
        b2.start = n1

        n1.ingoing = [b1]
        n1.outgoing = [b2]

        condition = MiddleNodeHasNumBranches(2)
        condition.update_selection([b1, b2])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b2, b1])
        self.assertFalse(condition.is_fulfilled())

        n1.outgoing = [b2, b3]
        condition.update_selection([b1, b2])
        self.assertFalse(condition.is_fulfilled())


class TestTwoParallelBranchesSelected(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b3 = MagicMock(CurvedBranch)
        n1 = MagicMock(PositionedNode)

        operation = MagicMock(CombineParallelOperation)
        operation.combinable.return_value = True
        condition = TwoParallelBranchesSelected()
        with patch("signalflowgrapher.gui.conditional_actions."
                   "selection_condition.CombineParallelOperation",
                   MagicMock(return_value=operation)):
            condition.update_selection([b1, b2])
            self.assertTrue(condition.is_fulfilled())
            condition.update_selection([b1, b2, b3])
            self.assertFalse(condition.is_fulfilled())
            condition.update_selection([b1])
            self.assertFalse(condition.is_fulfilled())
            condition.update_selection([b1, b2, n1])
            self.assertFalse(condition.is_fulfilled())

        operation.combinable.assert_called_once_with(b1, b2)


class TestMinNumNodesOrBranchesSelected(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)

        condition = MinNumNodesOrBranchesSelected(0)
        condition.update_selection([])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1, b1])
        self.assertTrue(condition.is_fulfilled())

        condition = MinNumNodesOrBranchesSelected(1)
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1, n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1, b2])
        self.assertTrue(condition.is_fulfilled())

        condition = MinNumNodesOrBranchesSelected(2)
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1, n1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1, b2])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1, b2, n1, n2])
        self.assertTrue(condition.is_fulfilled())


class TestBranchIsSelfLoop(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)

        b1.start = n1
        b1.end = n1
        b2.start = n1
        b2.end = n2

        condition = BranchIsSelfLoop()
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b2])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1, n1])
        self.assertFalse(condition.is_fulfilled())


class TestPathHasIndependentStartVar(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        n1 = MagicMock(PositionedNode)

        operation = MagicMock(InvertPathOperation)
        operation.start_is_independent_var.return_value = True
        condition = PathHasIndependentStartVar()
        with patch("signalflowgrapher.gui.conditional_actions."
                   "selection_condition.InvertPathOperation",
                   MagicMock(return_value=operation)):
            condition.update_selection([b1])
            self.assertTrue(condition.is_fulfilled())
            condition.update_selection([b1, n1])
            self.assertFalse(condition.is_fulfilled())
        operation.start_is_independent_var.assert_called_once_with([b1])


class TestAllNodesScalable(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)

        operation = MagicMock(ScalePathOperation)
        operation.scalable.return_value = True
        condition = AllNodesScalable()
        with patch("signalflowgrapher.gui.conditional_actions."
                   "selection_condition.ScalePathOperation",
                   MagicMock(return_value=operation)):
            condition.update_selection([b1, n1])
            self.assertFalse(condition.is_fulfilled())
            condition.update_selection([n1, n2])
            self.assertTrue(condition.is_fulfilled())

        operation.scalable.assert_any_call(n1)
        operation.scalable.assert_any_call(n2)


class TestSelectedBranchesWeighted(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b1.weight = "a"
        b2.weight = ""
        condition = SelectedBranchesWeighted()

        condition.update_selection([b1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b2])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b1, b2])
        self.assertFalse(condition.is_fulfilled())


class TestBranchesNextToNodesWeighted(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b1.weight = "a"
        b2.weight = ""
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)
        n1.ingoing = set()
        n1.ingoing.add(b1)
        n1.outgoing = set()
        n2.ingoing = set()
        n2.outgoing = set()
        n2.outgoing.add(b2)

        condition = BranchesNextToNodesWeighted()
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n2])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([n1, n2])
        self.assertFalse(condition.is_fulfilled())


class TestNeighbourBranchesWeighted(TestCase):
    def test_is_fulfilled(self):
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b3 = MagicMock(CurvedBranch)
        b1.weight = "a"
        b2.weight = ""
        b3.weight = "c"

        b1.start.ingoing = [b3]
        b2.end.outgoing = [b1]
        b3.start.outgoing = [b2]
        n1 = MagicMock(PositionedNode)

        condition = NeighbourBranchesWeighted()
        condition.update_selection([b1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b1, n1])
        self.assertFalse(condition.is_fulfilled())
        condition.update_selection([b2])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([b3])
        self.assertFalse(condition.is_fulfilled())


class TestAllBranchesWeighted(TestCase):
    def test_is_fulfilled(self):
        condition = AllBranchesWeighted()
        condition.update_selection([])
        self.assertFalse(condition.is_fulfilled())

        n1 = MagicMock(PositionedNode)
        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b3 = MagicMock(CurvedBranch)
        b1.weight = "1"
        b2.weight = "2"
        b3.weight = ""
        n1.graph.branches = [b1, b2, b3]
        b1.graph.branches = [b1, b2]

        condition.update_selection([n1])
        self.assertFalse(condition.is_fulfilled())

        condition.update_selection([b1])
        self.assertTrue(condition.is_fulfilled())


class TestNodesHaveNoSelfLoops(TestCase):
    def test_is_fulfilled(self):
        n1 = MagicMock(PositionedNode)
        n2 = MagicMock(PositionedNode)
        n3 = MagicMock(PositionedNode)

        b1 = MagicMock(CurvedBranch)
        b2 = MagicMock(CurvedBranch)
        b2.start = b2.end
        n1.ingoing = [b1]
        n2.ingoing = [b1]
        n3.ingoing = [b2]

        condition = NodesHaveNoSelfLoops()
        condition.update_selection([n1])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1, n2])
        self.assertTrue(condition.is_fulfilled())
        condition.update_selection([n1, n2, n3])
        self.assertFalse(condition.is_fulfilled())
