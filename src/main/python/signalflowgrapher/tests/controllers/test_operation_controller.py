from unittest import TestCase
from unittest.mock import MagicMock, patch
from signalflowgrapher.model.model import Model, CurvedBranch
from signalflowgrapher.commands.command_handler import CommandHandler
from signalflowgrapher.controllers.main_controller import MainController
from signalflowgrapher.controllers.operation_controller \
    import OperationController
from signalflow_algorithms.algorithms.graph import Node
from signalflow_algorithms.algorithms.graph_operations \
    import ChainingOperation, CombineParallelOperation, \
    EliminateNodeOperation, EliminateSelfLoopOperation, InvertPathOperation, \
    ScalePathOperation


class TestOperationController(TestCase):
    def setUp(self):
        self.model = MagicMock(Model)
        self.command_handler = MagicMock(CommandHandler)
        self.main_controller = MagicMock(MainController)
        self.controller = OperationController(self.model,
                                              self.command_handler,
                                              self.main_controller)

    def test_chain_branches(self):
        operation = MagicMock(ChainingOperation)
        branch_1 = MagicMock(CurvedBranch)
        branch_2 = MagicMock(CurvedBranch)

        n1 = MagicMock(Node)
        n2 = MagicMock(Node)
        n3 = MagicMock(Node)

        operation.get_nodes_in_order.return_value = (n1, n2, n3)
        operation.get_new_weight.return_value = "New Weight"

        with patch("signalflowgrapher.controllers.operation_controller."
                   "ChainingOperation",
                   MagicMock(return_value=operation)):
            self.controller.chain_branches(branch_1, branch_2)

        operation.get_nodes_in_order.assert_called_once_with(branch_1,
                                                             branch_2)
        self.main_controller.remove_nodes_and_branches.assert_called_once_with([n2])
        operation.get_new_weight.assert_called_once_with(branch_1,
                                                  branch_2)
        self.main_controller.create_branch_auto_pos.assert_called_once_with(
            n1, n3, "New Weight")
        self.command_handler.start_script.assert_called_once()
        self.command_handler.end_script.assert_called_once()

    def test_chain_branches_loop(self):
        operation = MagicMock(ChainingOperation)
        branch_1 = MagicMock(CurvedBranch)
        branch_2 = MagicMock(CurvedBranch)

        n1 = MagicMock(Node)
        n2 = MagicMock(Node)

        operation.get_nodes_in_order.return_value = (n1, n2, n1)
        operation.get_new_weight.return_value = "New Weight"

        with patch("signalflowgrapher.controllers.operation_controller."
                   "ChainingOperation",
                   MagicMock(return_value=operation)):
            self.controller.chain_branches(branch_1, branch_2)

        operation.get_nodes_in_order.assert_called_once_with(branch_1,
                                                             branch_2)
        self.main_controller.remove_nodes_and_branches.assert_called_once_with([n2])
        operation.get_new_weight.assert_called_once_with(branch_1,
                                                  branch_2)
        self.main_controller.create_branch_auto_pos.assert_not_called()
        self.main_controller.create_self_loop.assert_called_once_with(
            n1, "New Weight")
        self.command_handler.start_script.assert_called_once()
        self.command_handler.end_script.assert_called_once()

    def test_combine_parallel(self):
        operation = MagicMock(CombineParallelOperation)
        branch_1 = MagicMock(CurvedBranch)
        branch_2 = MagicMock(CurvedBranch)

        n1 = MagicMock(Node)
        n2 = MagicMock(Node)
        branch_1.start = n1
        branch_1.end = n2
        branch_2.start = n1
        branch_2.end = n2

        operation.get_new_weight.return_value = "New Weight"

        with patch("signalflowgrapher.controllers.operation_controller."
                   "CombineParallelOperation",
                   MagicMock(return_value=operation)):
            self.controller.combine_parallel(branch_1, branch_2)

        self.main_controller.remove_nodes_and_branches.assert_called_once_with(
            [branch_1, branch_2])
        operation.get_new_weight.assert_called_once_with(branch_1,
                                                  branch_2)
        self.main_controller.create_branch_auto_pos.assert_called_once_with(
            n1, n2, "New Weight")
        self.command_handler.start_script.assert_called_once()
        self.command_handler.end_script.assert_called_once()

    def test_combine_parallel_self_loops(self):
        operation = MagicMock(CombineParallelOperation)
        branch_1 = MagicMock(CurvedBranch)
        branch_2 = MagicMock(CurvedBranch)

        n1 = MagicMock(Node)
        branch_1.start = n1
        branch_1.end = n1
        branch_2.start = n1
        branch_2.end = n1

        operation.get_new_weight.return_value = "New Weight"

        with patch("signalflowgrapher.controllers.operation_controller."
                   "CombineParallelOperation",
                   MagicMock(return_value=operation)):
            self.controller.combine_parallel(branch_1, branch_2)

        self.main_controller.remove_nodes_and_branches.assert_called_once_with(
            [branch_1, branch_2])
        operation.get_new_weight.assert_called_once_with(branch_1,
                                                  branch_2)
        self.main_controller.create_self_loop.assert_called_once_with(
            n1, "New Weight")
        self.command_handler.start_script.assert_called_once()
        self.command_handler.end_script.assert_called_once()

    def test_transpose(self):
        branch_1 = MagicMock(CurvedBranch)
        branch_2 = MagicMock(CurvedBranch)

        self.model.graph.branches = {branch_1, branch_2}

        self.controller.transpose()
        self.main_controller.create_branch.assert_any_call(
            branch_1.end,
            branch_1.start,
            branch_1.spline2_x,
            branch_1.spline2_y,
            branch_1.spline1_x,
            branch_1.spline1_y,
            branch_1.label_dx,
            branch_1.label_dy,
            branch_1.weight
        )

        self.main_controller.create_branch.assert_any_call(
            branch_2.end,
            branch_2.start,
            branch_2.spline2_x,
            branch_2.spline2_y,
            branch_2.spline1_x,
            branch_2.spline1_y,
            branch_2.label_dx,
            branch_2.label_dy,
            branch_2.weight
        )

        self.main_controller.remove_nodes_and_branches.assert_any_call(
            [branch_1])
        self.main_controller.remove_nodes_and_branches.assert_any_call(
            [branch_2])
        self.command_handler.start_script.assert_called_once()
        self.command_handler.end_script.assert_called_once()

    def test_eliminate_node(self):
        operation = MagicMock(EliminateNodeOperation)

        n1 = MagicMock(Node)
        n2 = MagicMock(Node)
        n3 = MagicMock(Node)

        operation.get_self_loops.return_value = \
            [[n2, "Weight 1"], [n3, "Weight 2"]]

        operation.get_new_paths.return_value = \
            [[n2, n3, "Path 1"], [n3, n2, "Path 2"]]

        with patch("signalflowgrapher.controllers.operation_controller."
                   "EliminateNodeOperation",
                   MagicMock(return_value=operation)):
            self.controller.eliminate_node(n1)

        self.main_controller.remove_nodes_and_branches.assert_called_once_with(
            [n1])

        self.main_controller.create_self_loop.assert_any_call(n2, "Weight 1")
        self.main_controller.create_self_loop.assert_any_call(n3, "Weight 2")
        self.main_controller.create_branch_auto_pos.assert_any_call(
            n2, n3, "Path 1")
        self.main_controller.create_branch_auto_pos.assert_any_call(
            n3, n2, "Path 2")

        operation.get_self_loops.assert_called_once_with(n1)
        operation.get_new_paths.assert_called_once_with(n1)

        self.command_handler.start_script.assert_called_once()
        self.command_handler.end_script.assert_called_once()

    def test_eliminate_self_loop(self):
        operation = MagicMock(EliminateSelfLoopOperation)

        self_loop = MagicMock(CurvedBranch)
        branch = MagicMock(CurvedBranch)
        operation.get_affected_branches.return_value = \
            [branch]
        operation.get_new_affected_branch_weight.return_value = "New Weight"

        with patch("signalflowgrapher.controllers.operation_controller."
                   "EliminateSelfLoopOperation",
                   MagicMock(return_value=operation)):
            self.controller.eliminate_self_loop(self_loop)

        self.assertEqual("New Weight", branch.weight)
        operation.get_affected_branches.assert_called_once()
        self_loop.remove.assert_called_once()
        operation.get_new_affected_branch_weight.assert_called_once()

    def test_eliminate_self_loop_no_loop(self):
        operation = MagicMock(EliminateSelfLoopOperation)

        self_loop = MagicMock(CurvedBranch)
        operation.is_self_loop.return_value = False

        with patch("signalflowgrapher.controllers.operation_controller."
                   "EliminateSelfLoopOperation",
                   MagicMock(return_value=operation)):
            def call_method():
                self.controller.eliminate_self_loop(self_loop)

            self.assertRaises(ValueError, call_method)

    def test_invert_path(self):
        operation = MagicMock(InvertPathOperation)
        branch = MagicMock(CurvedBranch)
        branch.start.x = 10
        branch.start.y = 20
        branch.end.x = 50
        branch.end.y = 60
        branch2 = MagicMock(CurvedBranch)
        branch2.start.x = 90
        branch2.start.y = 100
        branch2.end.x = 30
        branch2.end.y = 40
        branch2.spline2_x = 0
        branch2.spline2_y = 0
        path = [branch]

        new_branch = MagicMock()

        operation.get_affected_branches.return_value = [branch2]
        operation.get_new_affected_branch_weight.return_value = "New Weight"

        with patch("signalflowgrapher.controllers.operation_controller."
                   "InvertPathOperation",
                   MagicMock(return_value=operation)):
            with patch("signalflowgrapher.controllers.operation_controller."
                       "CurvedBranch",
                       new_branch):
                self.controller.invert_path(path)

        new_branch.assert_any_call(
            branch2.start,
            branch.start,
            branch2.spline1_x,
            branch2.spline1_y,
            -20,
            -20,
            branch2.label_dx,
            branch2.label_dy,
            "New Weight"
        )

        new_branch.assert_any_call(
           branch.end,
           branch.start,
           branch.spline2_x,
           branch.spline2_y,
           branch.spline1_x,
           branch.spline1_y,
           branch.label_dx,
           branch.label_dy,
           operation.get_new_branch_weight()
        )

        operation.get_affected_branches.assert_called_once()
        branch2.remove.assert_called_once()
        operation.get_new_affected_branch_weight.assert_called_once()

    def test_scale_path(self):
        operation = MagicMock(ScalePathOperation)
        node = MagicMock(Node)
        branch_1 = MagicMock(CurvedBranch)
        branch_2 = MagicMock(CurvedBranch)
        node.ingoing = {branch_1}
        node.outgoing = {branch_2}

        operation.get_outgoing_branch_weight.return_value = "Weight out"
        operation.get_ingoing_branch_weight.return_value = "Weight in"

        with patch("signalflowgrapher.controllers.operation_controller."
                   "ScalePathOperation",
                   MagicMock(return_value=operation)):
            self.controller.scale_path([node], "x")

        operation.get_ingoing_branch_weight.assert_called_once_with(
            branch_1, "x")
        operation.get_outgoing_branch_weight.assert_called_once_with(
            branch_2, "x")
        self.assertEqual("Weight in", branch_1.weight)
        self.assertEqual("Weight out", branch_2.weight)
