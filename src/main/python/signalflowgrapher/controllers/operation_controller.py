from signalflow_algorithms.algorithms.graph_operations import (
    ChainingOperation, EliminateNodeOperation, CombineParallelOperation,
    EliminateSelfLoopOperation, InvertPathOperation, ScalePathOperation)
from signalflowgrapher.model.model import CurvedBranch, Model, PositionedNode
from signalflowgrapher.commands.change_branch_weight_command import (
    ChangeBranchWeightCommand)
from signalflowgrapher.commands.remove_branch_command import (
    RemoveBranchCommand)
from signalflowgrapher.commands.command_handler import (
    ScriptCommand, CommandHandler)
from signalflowgrapher.commands.create_branch_command import (
    CreateBranchCommand)
from signalflowgrapher.controllers.main_controller import MainController
from typing import List
import logging
logger = logging.getLogger(__name__)


class OperationController(object):
    def __init__(self, model: Model,
                 command_handler: CommandHandler,
                 main_controller: MainController):
        self.__model = model
        self.__command_handler = command_handler
        self.__main_controller = main_controller

    def chain_branches(self, branch_1: CurvedBranch, branch_2: CurvedBranch):
        """Apply the chaining rule to the two given branches"""

        logger.debug("Apply chaining rule")
        self.__command_handler.start_script()
        operation = ChainingOperation()

        (start_node,
         middle_node,
         end_node) = operation.get_nodes_in_order(branch_1, branch_2)

        new_weight = operation.get_new_weight(branch_1, branch_2)
        self.__main_controller.remove_nodes_and_branches([middle_node])

        if start_node == end_node:
            self.__main_controller.create_self_loop(start_node, new_weight)
        else:
            self.__main_controller.create_branch_auto_pos(start_node,
                                                          end_node,
                                                          new_weight)

        self.__command_handler.end_script()

    def combine_parallel(self, branch_1: CurvedBranch, branch_2: CurvedBranch):
        """Apply the combine parallel rule to the two given branches"""

        logger.debug("Apply combine parallel rule")
        self.__command_handler.start_script()
        operation = CombineParallelOperation()
        new_weight = operation.get_new_weight(branch_1, branch_2)
        start_node = branch_1.start
        end_node = branch_1.end
        self.__main_controller.remove_nodes_and_branches([branch_1, branch_2])

        if start_node == end_node:
            self.__main_controller.create_self_loop(start_node, new_weight)
        else:
            self.__main_controller.create_branch_auto_pos(start_node,
                                                          end_node,
                                                          new_weight)
        self.__command_handler.end_script()

    def transpose(self):
        """Transpose the graph"""

        logger.debug("Transpose graph")
        self.__command_handler.start_script()
        branches = self.__model.graph.branches.copy()
        for branch in branches:
            self.__main_controller.create_branch(branch.end,
                                                 branch.start,
                                                 branch.spline2_x,
                                                 branch.spline2_y,
                                                 branch.spline1_x,
                                                 branch.spline1_y,
                                                 branch.label_dx,
                                                 branch.label_dy,
                                                 branch.weight)
            self.__main_controller.remove_nodes_and_branches([branch])
        self.__command_handler.end_script()

    def eliminate_node(self, node: PositionedNode):
        """Apply the eliminate node rule to the given node"""
        logger.debug("Eliminate node")

        operation = EliminateNodeOperation()

        # Get self loops and new paths to create
        self_loops = operation.get_self_loops(node)
        new_paths = operation.get_new_paths(node)

        # Remove node
        self.__command_handler.start_script()
        self.__main_controller.remove_nodes_and_branches([node])

        # Create self loops and new paths
        for loop in self_loops:
            self.__main_controller.create_self_loop(loop[0], loop[1])

        for path in new_paths:
            self.__main_controller.create_branch_auto_pos(
                path[0], path[1], path[2])

        self.__command_handler.end_script()

    def eliminate_self_loop(self, self_loop: CurvedBranch):
        """Eliminate the given self loop"""
        logger.debug("Eliminate self loop")

        # Get ingoing branch if any (check if part of loop)
        operation = EliminateSelfLoopOperation()
        if not operation.is_self_loop(self_loop):
            raise ValueError("Branch is not a selfloop")

        # Get all affected branches
        affected_branches = operation.get_affected_branches(self_loop)

        # Set new weights on affected branches
        cmds = []
        for branch in affected_branches:
            new_weight = operation.get_new_affected_branch_weight(
                self_loop, branch)
            cmds.append(ChangeBranchWeightCommand(
                branch, new_weight, self.__model.graph))
            branch.weight = new_weight

        cmds.append(RemoveBranchCommand(self.__model.graph, self_loop, self.__model))

        # Remove self loop
        self_loop.remove()

        self.__command_handler.add_command(ScriptCommand(cmds))

    def invert_path(self, path_to_invert: List[CurvedBranch]):
        """Invert the given path"""
        logger.debug("Invert path")

        operation = InvertPathOperation()
        if not operation.start_is_independent_var(path_to_invert):
            raise ValueError("The given path is not valid for an inversion.")

        cmds = []
        for branch_to_invert in path_to_invert:
            # Get affected branches, reconnect and adjust weights
            for affected_branch in operation.get_affected_branches(
                    branch_to_invert):
                new_weight = operation.get_new_affected_branch_weight(
                    branch_to_invert, affected_branch)

                # Calculate distance between nodes for spline translation
                distance_x = branch_to_invert.start.x - affected_branch.end.x
                distance_y = branch_to_invert.start.y - affected_branch.end.y

                # Create new branch for replacement of affected branch
                new_branch = CurvedBranch(
                    affected_branch.start,
                    # Reconnect to start of branch to invert
                    branch_to_invert.start,
                    affected_branch.spline1_x,
                    affected_branch.spline1_y,
                    affected_branch.spline2_x + distance_x,
                    affected_branch.spline2_y + distance_y,
                    affected_branch.label_dx,
                    affected_branch.label_dy,
                    new_weight)

                # Append commands
                cmds.append(RemoveBranchCommand(
                    self.__model.graph, affected_branch, self.__model))
                cmds.append(CreateBranchCommand(
                    self.__model.graph, new_branch, self.__model))

                # Remove affected branch
                affected_branch.remove()

            # Invert branch
            inverted_branch = CurvedBranch(
                branch_to_invert.end,  # Use end as start
                branch_to_invert.start,  # Use start as end
                branch_to_invert.spline2_x,  # Swap splines
                branch_to_invert.spline2_y,
                branch_to_invert.spline1_x,
                branch_to_invert.spline1_y,
                branch_to_invert.label_dx,
                branch_to_invert.label_dy,
                operation.get_new_branch_weight(branch_to_invert))
            cmds.append(RemoveBranchCommand(
                self.__model.graph, branch_to_invert, self.__model))
            branch_to_invert.remove()
            cmds.append(CreateBranchCommand(
                self.__model.graph, inverted_branch, self.__model))

        self.__command_handler.add_command(ScriptCommand(cmds))

    def scale_path(self, nodes: List[PositionedNode], scale_expr: str):
        logger.debug("Scale path")
        operation = ScalePathOperation()
        cmds = []
        for node in nodes:
            # Scale outgoing branches
            for branch in node.outgoing:
                new_weight = operation.get_outgoing_branch_weight(
                    branch, scale_expr)
                cmds.append(ChangeBranchWeightCommand(
                    branch, new_weight, self.__model.graph))
                branch.weight = new_weight

            # Scale ingoing branches
            for branch in node.ingoing:
                new_weight = operation.get_ingoing_branch_weight(
                    branch, scale_expr)
                cmds.append(ChangeBranchWeightCommand(
                    branch, new_weight, self.__model.graph))
                branch.weight = new_weight

        self.__command_handler.add_command(ScriptCommand(cmds))
