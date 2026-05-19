from unittest import TestCase
from unittest.mock import MagicMock, patch
from signalflowgrapher.model.model import Model
from signalflowgrapher.commands.command_handler import CommandHandler
from signalflowgrapher.controllers.main_controller import MainController
from signalflowgrapher.commands.create_node_command import CreateNodeCommand
from signalflowgrapher.commands.transform_branch_command \
    import TransformBranchCommand
from signalflowgrapher.commands.move_node_command import MoveNodeCommand
from signalflowgrapher.commands.move_label_command import MoveLabelCommand
from signalflowgrapher.commands.command_handler import ScriptCommand
from signalflowgrapher.commands.change_branch_weight_command \
    import ChangeBranchWeightCommand
from signalflowgrapher.commands.change_node_name_command \
    import ChangeNodeNameCommand
from signalflowgrapher.commands.create_branch_command \
    import CreateBranchCommand
from signalflowgrapher.model.model \
    import PositionedNode, CurvedBranch, LabeledObject


class TestMainController(TestCase):

    def setUp(self):
        self.model = MagicMock(Model)
        self.command_handler = MagicMock(CommandHandler)
        self.controller = MainController(self.model, self.command_handler)

    def test_create_node(self):
        node = MagicMock(PositionedNode)
        command = MagicMock(CreateNodeCommand)
        with patch("signalflowgrapher.controllers.main_controller."
                   "PositionedNode",
                   node):
            with patch("signalflowgrapher.controllers.main_controller."
                       "CreateNodeCommand",
                       command):
                self.controller.create_node(10, 20)

        node.assert_called_once_with(self.model.graph, 10, 20, 0, 30)
        command.assert_called_once_with(self.model.graph, node(), self.model)
        self.command_handler.add_command.assert_called_once_with(command())

    def test_remove_nodes_and_branches(self):
        node1 = MagicMock(PositionedNode)
        node2 = MagicMock(PositionedNode)
        node3 = MagicMock(PositionedNode)
        branch1 = MagicMock(CurvedBranch)
        branch2 = MagicMock(CurvedBranch)
        branch3 = MagicMock(CurvedBranch)
        branch_in = MagicMock(CurvedBranch)
        branch_out = MagicMock(CurvedBranch)

        node3.outgoing = {branch_in}
        node3.ingoing = {branch_out}

        script_command = MagicMock(ScriptCommand)

        nodes_and_branches = [
            node1,
            node2,
            node3,
            branch1,
            branch2,
            branch3
        ]

        with patch("signalflowgrapher.controllers.main_controller."
                   "ScriptCommand",
                   script_command):
            self.controller.remove_nodes_and_branches(nodes_and_branches)

        branch1.remove.assert_called_once()
        branch2.remove.assert_called_once()
        branch3.remove.assert_called_once()
        node1.remove.assert_called_once()
        node2.remove.assert_called_once()
        node3.remove.assert_called_once()
        branch_in.remove.assert_called_once()
        branch_out.remove.assert_called_once()
        script_command.assert_called_once()

    def test_move_node(self):
        node = MagicMock(PositionedNode)
        branch1 = MagicMock(CurvedBranch)
        branch2 = MagicMock(CurvedBranch)
        node.ingoing = {branch1}
        node.outgoing = {branch2}
        transform_command = MagicMock(TransformBranchCommand)
        move_command = MagicMock(MoveNodeCommand)
        with patch("signalflowgrapher.controllers.main_controller."
                   "TransformBranchCommand",
                   transform_command):
            with patch("signalflowgrapher.controllers.main_controller."
                       "MoveNodeCommand",
                       move_command):
                self.controller.move_node(node, 51, 22)

        self.model.graph.move_node_relative.assert_called_once_with(
            node, 51, 22)
        self.model.graph.transform_branch.assert_any_call(branch1,
                                                          0,
                                                          0,
                                                          51,
                                                          22)
        self.model.graph.transform_branch.assert_any_call(branch2,
                                                          51,
                                                          22,
                                                          0,
                                                          0)

        move_command.assert_called_once_with(node, 51, 22, self.model.graph)
        transform_command.assert_any_call(self.model.graph,
                                          branch1,
                                          0,
                                          0,
                                          51,
                                          22)

        transform_command.assert_any_call(self.model.graph,
                                          branch2,
                                          51,
                                          22,
                                          0,
                                          0)

        self.assertEqual(3, self.command_handler.add_command.call_count)

    def test_move_label_relative(self):
        labeled_object = MagicMock(LabeledObject)
        command = MagicMock()
        r_command = MagicMock(MoveLabelCommand)
        command.return_value = r_command

        with patch("signalflowgrapher.controllers.main_controller."
                   "MoveLabelCommand",
                   command):
            self.controller.move_label_relative(labeled_object, 99, -22)

        command.assert_called_once_with(labeled_object,
                                        99,
                                        -22,
                                        self.model.graph)
        r_command.redo.assert_called_once()
        self.command_handler.add_command.assert_called_once_with(command())

    def test_set_branch_weight(self):
        branch = MagicMock(CurvedBranch)
        command = MagicMock()
        r_command = MagicMock(ChangeBranchWeightCommand)
        command.return_value = r_command

        with patch("signalflowgrapher.controllers.main_controller."
                   "ChangeBranchWeightCommand",
                   command):
            self.controller.set_branch_weight(branch, "New Branch Weight")

        command.assert_called_once_with(branch,
                                        "New Branch Weight",
                                        self.model.graph)
        r_command.redo.assert_called_once()
        self.command_handler.add_command.assert_called_once_with(command())

    def test_set_node_name(self):
        node = MagicMock(PositionedNode)
        command = MagicMock()
        r_command = MagicMock(ChangeNodeNameCommand)
        command.return_value = r_command

        with patch("signalflowgrapher.controllers.main_controller."
                   "ChangeNodeNameCommand",
                   command):
            self.controller.set_node_name(node, "New Node Name")

        command.assert_called_once_with(node,
                                        "New Node Name",
                                        self.model.graph)
        r_command.redo.assert_called_once()
        self.command_handler.add_command.assert_called_once_with(command())

    def test_transform_branch(self):
        branch = MagicMock(CurvedBranch)
        command = MagicMock(TransformBranchCommand)

        with patch("signalflowgrapher.controllers.main_controller."
                   "TransformBranchCommand",
                   command):
            self.controller.transform_branch(branch,
                                             1,
                                             2,
                                             3,
                                             4)

        command.assert_called_once_with(self.model.graph,
                                        branch,
                                        1,
                                        2,
                                        3,
                                        4)
        self.command_handler.add_command.assert_called_once_with(command())
        self.model.graph.transform_branch.assert_called_once_with(branch,
                                                                  1,
                                                                  2,
                                                                  3,
                                                                  4)

    def test_create_branch(self):
        start_node = MagicMock(PositionedNode)
        end_node = MagicMock(PositionedNode)
        command = MagicMock(CreateBranchCommand)
        branch = MagicMock(CurvedBranch)

        with patch("signalflowgrapher.controllers.main_controller."
                   "CreateBranchCommand",
                   command):
            with patch("signalflowgrapher.controllers.main_controller."
                       "CurvedBranch",
                       branch):
                self.controller.create_branch(start_node,
                                              end_node,
                                              10,
                                              20,
                                              30,
                                              40,
                                              11,
                                              12,
                                              "Weight Test")
        branch.assert_called_once_with(start_node,
                                       end_node,
                                       10,
                                       20,
                                       30,
                                       40,
                                       11,
                                       12,
                                       "Weight Test")
        command.assert_called_once_with(self.model.graph,
                                        branch(), self.model)

    def test_create_branch_auto_pos(self):
        start_node = MagicMock(PositionedNode)
        start_node.x = 10
        start_node.y = 10
        end_node = MagicMock(PositionedNode)
        end_node.x = 100
        end_node.y = 10
        command = MagicMock(CreateBranchCommand)
        branch = MagicMock(CurvedBranch)

        with patch("signalflowgrapher.controllers.main_controller."
                   "CreateBranchCommand",
                   command):
            with patch("signalflowgrapher.controllers.main_controller."
                       "CurvedBranch",
                       branch):
                self.controller.create_branch_auto_pos(start_node,
                                                       end_node,
                                                       "Weight Test")

        branch.assert_called_once_with(start_node,
                                       end_node,
                                       55,
                                       10,
                                       55,
                                       10,
                                       0,
                                       30,
                                       "Weight Test")
        command.assert_called_once_with(self.model.graph,
                                        branch(), self.model)

    def test_create_branch_auto_pos_near_branch(self):
        existing_branch = MagicMock(CurvedBranch)
        existing_branch.spline1_x = 55
        existing_branch.spline1_y = 10
        existing_branch.spline2_x = 55
        existing_branch.spline2_y = 10
        existing_branch.start.x = 10
        existing_branch.start.y = 10
        existing_branch.end.x = 100
        existing_branch.end.y = 10
        self.model.graph.branches = {existing_branch}
        start_node = MagicMock(PositionedNode)
        start_node.x = 10
        start_node.y = 10
        end_node = MagicMock(PositionedNode)
        end_node.x = 100
        end_node.y = 10
        command = MagicMock(CreateBranchCommand)
        branch = MagicMock(CurvedBranch)

        with patch("signalflowgrapher.controllers.main_controller."
                   "CreateBranchCommand",
                   command):
            with patch("signalflowgrapher.controllers.main_controller."
                       "CurvedBranch",
                       branch):
                self.controller.create_branch_auto_pos(start_node,
                                                       end_node,
                                                       "Weight Test")

        branch.assert_called_once_with(start_node,
                                       end_node,
                                       9.999999999999995,
                                       -35,
                                       100,
                                       -35,
                                       0,
                                       30,
                                       "Weight Test")
        command.assert_called_once_with(self.model.graph,
                                        branch(), self.model)

    def test_create_branch_auto_pos_same_line(self):
        existing_branch = MagicMock(CurvedBranch)
        existing_branch.spline1_x = 55
        existing_branch.spline1_y = 10
        existing_branch.spline2_x = 55
        existing_branch.spline2_y = 10
        existing_branch.start.x = 10
        existing_branch.start.y = 10
        existing_branch.end.x = 100
        existing_branch.end.y = 10
        self.model.graph.branches = {existing_branch}
        start_node = MagicMock(PositionedNode)
        start_node.x = 20
        start_node.y = 10
        end_node = MagicMock(PositionedNode)
        end_node.x = 50
        end_node.y = 10
        command = MagicMock(CreateBranchCommand)
        branch = MagicMock(CurvedBranch)

        with patch("signalflowgrapher.controllers.main_controller."
                   "CreateBranchCommand",
                   command):
            with patch("signalflowgrapher.controllers.main_controller."
                       "CurvedBranch",
                       branch):
                self.controller.create_branch_auto_pos(start_node,
                                                       end_node,
                                                       "Weight Test")

        branch.assert_called_once_with(start_node,
                                       end_node,
                                       19.999999999999996,
                                       -5,
                                       50,
                                       -5,
                                       0,
                                       30,
                                       "Weight Test")
        command.assert_called_once_with(self.model.graph,
                                        branch(), self.model)

    def test_create_self_loop(self):
        start_node = MagicMock(PositionedNode)
        start_node.x = 10
        start_node.y = 10

        existing_branch = MagicMock(CurvedBranch)
        existing_branch.spline1_x = 80.71067811865476
        existing_branch.spline1_y = -60.710678118654755
        existing_branch.spline2_x = -60.710678118654755
        existing_branch.spline2_y = -60.710678118654755
        existing_branch.start = start_node
        existing_branch.end = start_node

        self.model.graph.branches = {existing_branch}

        command = MagicMock(CreateBranchCommand)
        branch = MagicMock(CurvedBranch)

        with patch("signalflowgrapher.controllers.main_controller."
                   "CreateBranchCommand",
                   command):
            with patch("signalflowgrapher.controllers.main_controller."
                       "CurvedBranch",
                       branch):
                self.controller.create_self_loop(start_node,
                                                 "Weight Test")

        branch.assert_called_once()
        call = branch.call_args[0]
        self.assertEqual(start_node, call[0])
        self.assertEqual(start_node, call[1])
        self.assertAlmostEqual(110.71067811865476, call[2], delta=0.00001)
        self.assertAlmostEqual(-90.71067811865476, call[3], delta=0.00001)
        self.assertAlmostEqual(-90.71067811865476, call[4], delta=0.00001)
        self.assertAlmostEqual(-90.71067811865476, call[5], delta=0.00001)
        self.assertEqual(0, call[6])
        self.assertEqual(-40, call[7])
        self.assertEqual("Weight Test", call[8])

        command.assert_called_once_with(self.model.graph,
                                        branch(), self.model)

    def test_create_self_loop_existing_loop(self):
        start_node = MagicMock(PositionedNode)
        start_node.x = 10
        start_node.y = 10

        command = MagicMock(CreateBranchCommand)
        branch = MagicMock(CurvedBranch)

        with patch("signalflowgrapher.controllers.main_controller."
                   "CreateBranchCommand",
                   command):
            with patch("signalflowgrapher.controllers.main_controller."
                       "CurvedBranch",
                       branch):
                self.controller.create_self_loop(start_node,
                                                 "Weight Test")
        branch.assert_called_once()
        call = branch.call_args[0]
        self.assertEqual(start_node, call[0])
        self.assertEqual(start_node, call[1])
        self.assertAlmostEqual(80.710678118654, call[2], delta=0.00001)
        self.assertAlmostEqual(-60.71067811865, call[3], delta=0.00001)
        self.assertAlmostEqual(-60.71067811865, call[4], delta=0.00001)
        self.assertAlmostEqual(-60.71067811865, call[5], delta=0.00001)
        self.assertEqual(0, call[6])
        self.assertEqual(-40, call[7])
        self.assertEqual("Weight Test", call[8])

        command.assert_called_once_with(self.model.graph,
                                        branch(), self.model)
