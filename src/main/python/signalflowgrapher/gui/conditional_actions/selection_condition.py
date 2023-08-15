from abc import ABC, abstractmethod
from signalflowgrapher.model.model import CurvedBranch, PositionedNode
from signalflow_algorithms.algorithms.graph_operations import (
    CombineParallelOperation, InvertPathOperation, ScalePathOperation)
from typing import List


class SelectionCondition(ABC):
    def __init__(self):
        self._num_nodes_selected = 0
        self._num_branches_selected = 0
        self._selected_nodes: List[PositionedNode] = []
        self._selected_branches: List[CurvedBranch] = []

    def update_selection(self, selection):
        """
        Updates the selection of the selection condition.
        """
        self._selected_nodes: List[PositionedNode] = []
        self._selected_branches: List[CurvedBranch] = []
        for widget in selection:
            if isinstance(widget, PositionedNode):
                self._selected_nodes.append(widget)
            if isinstance(widget, CurvedBranch):
                self._selected_branches.append(widget)
        self._num_nodes_selected = len(self._selected_nodes)
        self._num_branches_selected = len(self._selected_branches)

    @abstractmethod
    def is_fulfilled(self) -> bool:
        pass


class SpecificNumNodesSelected(SelectionCondition):
    """
    Is fulfilled if the number of selected nodes equals the given number.
    If one or more branches are part of the selection the condition
    is not fulfilled.
    """

    def __init__(self, number: int):
        super().__init__()
        self.__number = number

    def is_fulfilled(self) -> bool:
        return self._num_nodes_selected == self.__number \
            and self._num_branches_selected == 0


class MinNumNodesSelected(SelectionCondition):
    """
    Is fulfilled if the number of selected nodes is the same or higher than
    the given minimum. If one or more branches are part of the selection
    the condition is not fulfilled.
    """

    def __init__(self, min):
        super().__init__()
        self.__min = min

    def is_fulfilled(self) -> bool:
        return self._num_nodes_selected >= self.__min \
            and self._num_branches_selected == 0


class MaxNumNodesSelected(SelectionCondition):
    """
    Is fulfilled if the selected number of nodes does not exceed
    the given maximum.
    If one or more branches are part of the selection the condition
    is not fulfilled.
    """

    def __init__(self, max):
        super().__init__()
        self.__max = max

    def is_fulfilled(self) -> bool:
        return self._num_nodes_selected <= self.__max \
            and self._num_branches_selected == 0


class SpecificNumBranchesSelected(SelectionCondition):
    """
    Is fulfilled if the number of selected branches equals the given number.
    If one or more nodes are part of the selection the condition
    is not fulfilled.
    """

    def __init__(self, number: int):
        super().__init__()
        self.__number = number

    def is_fulfilled(self) -> bool:
        return self._num_branches_selected == self.__number \
            and self._num_nodes_selected == 0


class SubsequentBranchesSelected(SelectionCondition):
    """
    Is fulfilled if every except for the first in the selection has the
    end node of the previous as start node.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        # Abort if no branch has been selected
        if self._num_branches_selected == 0:
            return False

        # Fail as soon as a branch is found that has a different node
        # than the one on the end of the previous branch
        last_end = self._selected_branches[0].start
        for branch in self._selected_branches:
            if last_end is not branch.start:
                return False
            # Set end of this branch for next iteration
            last_end = branch.end

        return True


class MiddleNodeHasNumBranches(SelectionCondition):
    """
    Is fulfilled if the selection consists of two subsequent branches
    and the node in the middle has the specified amount of connected
    branches
    """
    def __init__(self, number: int):
        super().__init__()
        self.__number = number

    def is_fulfilled(self) -> bool:
        if self._num_branches_selected != 2:
            return False

        middle_node = self._selected_branches[0].end
        if middle_node != self._selected_branches[1].start:
            return False

        return (len(middle_node.ingoing) +
                len(middle_node.outgoing)) == self.__number


class TwoParallelBranchesSelected(SelectionCondition):
    """
    Is fulfilled if exactly two branches are combineable.
    To determine if the branches are combineable the
    CombineParallelOperation is used.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        if (self._num_branches_selected != 2 or self._num_nodes_selected > 0):
            return False

        branch_1: CurvedBranch = self._selected_branches[0]
        branch_2: CurvedBranch = self._selected_branches[1]

        operation = CombineParallelOperation()
        return operation.combinable(branch_1, branch_2)


class MinNumNodesOrBranchesSelected(SelectionCondition):
    """
    Is fulfilled if the number of selected branches or the number of
    the selected nodes is the same or higher than the given minimum.
    """

    def __init__(self, min):
        super().__init__()
        self.__min = min

    def is_fulfilled(self) -> bool:
        return self._num_nodes_selected >= self.__min or \
            self._num_branches_selected >= self.__min


class BranchIsSelfLoop(SelectionCondition):
    """
    Is fulfilled if start and end of the branch is the same node.
    If more than one branch is selected the condition is not fulfilled.
    If one or more nodes are part of the selection the condition
    is also not fulfilled.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        if self._num_branches_selected == 1 and \
                self._num_nodes_selected == 0:
            branch = self._selected_branches[0]
            if branch.start == branch.end:
                return True

        return False


class PathHasIndependentStartVar(SelectionCondition):
    """
    Is fulfilled if the start variable is independent.
    The InvertPathOperation is used to determine if a start variable is
    independent.
    If one or more nodes are part of the selection the condition
    is not fulfilled.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        # Path consists of branches only, at least 1
        if self._num_branches_selected > 0 and self._num_nodes_selected == 0:
            operation = InvertPathOperation()
            return operation.start_is_independent_var(self._selected_branches)

        return False


class AllNodesScalable(SelectionCondition):
    """
    Is fulfilled if only scalable nodes have been selected.
    ScalePathOperation is used to determine if a node is scalable.
    If one or more branches are part of the selection the condition
    is not fulfilled.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        # Make sure only nodes have been selected
        if self._num_nodes_selected == 0 or \
                self._num_branches_selected > 0:
            return False

        # Check if every node is scalable
        operation = ScalePathOperation()
        for node in self._selected_nodes:
            if not operation.scalable(node):
                return False

        # Return true if all are scalable
        return True


class SelectedBranchesWeighted(SelectionCondition):
    """
    Is fulfilled if all selected branches have a non-empty weight.
    Non-empty means the weight is not None and not an empty string.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        # Fail as soon as a selected branch with empty weight is found
        for branch in self._selected_branches:
            if weight_is_empty(branch.weight):
                return False

        return True


class BranchesNextToNodesWeighted(SelectionCondition):
    """
    Is fulfilled if all ingoing and outgoing branches of the selected
    nodes have a non-empty weight.
    Non-empty means the weight is not None and not an empty string.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        # Fail if any ingoing or outgoing branch has empty weight
        for node in self._selected_nodes:
            for branch in node.outgoing.union(node.ingoing):
                if weight_is_empty(branch.weight):
                    return False

        return True


class NeighbourBranchesWeighted(SelectionCondition):
    """
    Is fulfilled if all direct neighbours of the selected branches have a
    non-empty weight. Direct neighbours are branches that are connected to
    start and/or end of the selected branch.
    Non-empty means the weight is not None and not an empty string.
    If the selection contains nodes, the result is always false
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        if self._num_branches_selected > 0 and self._num_nodes_selected == 0:
            # Collect all branches that touch the start or end node
            neighbour_branches = set()
            for branch in self._selected_branches:
                neighbour_branches.update(branch.start.outgoing)
                neighbour_branches.update(branch.start.ingoing)
                neighbour_branches.update(branch.end.outgoing)

            # Fail if any neighbour branch has empty weight
            for branch in neighbour_branches:
                if weight_is_empty(branch.weight):
                    return False

            return True
        else:
            return False


class AllBranchesWeighted(SelectionCondition):
    """
    Is fulfilled if all branches contained in the graph of the first selected
    branch or node have a non-empty weigth. Non-empty means the weight
    is not None and not an empty string.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        graph = None
        if self._num_branches_selected > 0:
            graph = self._selected_branches[0].graph
        elif self._num_nodes_selected > 0:
            graph = self._selected_nodes[0].graph

        # Return false if no selection has been made
        if graph is None:
            return False

        # Fail if any branch has empty weight
        for branch in graph.branches:
            if weight_is_empty(branch.weight):
                return False

        # Pass if all branches have weigth
        return True


class NodesHaveNoSelfLoops(SelectionCondition):
    """
    Is fulfilled if all selected nodes are without self loops.
    If zero nodes have been selected the condition is also fulfilled.
    """

    def __init__(self):
        super().__init__()

    def is_fulfilled(self) -> bool:
        # Ignore if no node selected
        if self._num_nodes_selected == 0:
            return True

        # Fail for first self loop
        for node in self._selected_nodes:
            for branch in node.ingoing:
                if branch.start == branch.end:
                    return False

        return True


def weight_is_empty(weight: str) -> bool:
    """
    Check if a branch weight is empty.
    Returns true if branch weight is None or
    empty string.
    """
    if not isinstance(weight, str):
        raise ValueError("Weight is not of type str.")

    return weight is None or weight == ''
