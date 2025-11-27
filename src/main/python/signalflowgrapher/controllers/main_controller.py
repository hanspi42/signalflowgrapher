from typing import List
from signalflowgrapher.model.model import (
    CurvedBranch, LabeledObject, Model, PositionedNode)
from signalflowgrapher.commands.create_node_command import CreateNodeCommand
from signalflowgrapher.commands.remove_node_command import RemoveNodeCommand
from signalflowgrapher.commands.move_node_command import MoveNodeCommand
from signalflowgrapher.commands.command_handler import (
    ScriptCommand, CommandHandler)
from signalflowgrapher.commands.remove_branch_command import (
    RemoveBranchCommand)
from signalflowgrapher.commands.create_branch_command import (
    CreateBranchCommand)
from signalflowgrapher.commands.transform_branch_command import (
    TransformBranchCommand)
import math
from signalflowgrapher.common.geometry import rotate, move, distance, collinear
from signalflowgrapher.commands.change_node_name_command import (
    ChangeNodeNameCommand)
from signalflowgrapher.commands.change_branch_weight_command import (
    ChangeBranchWeightCommand)
from signalflowgrapher.commands.move_label_command import MoveLabelCommand
import logging
logger = logging.getLogger(__name__)


class MainController:
    def __init__(self, model: Model, command_handler: CommandHandler):
        self.__model = model
        self.__command_handler = command_handler

    def create_node(self, x_pos: int, y_pos: int):
        """Create a new node at the given coordinates."""
        logger.debug("Create new node at position (%s,%s)", x_pos, y_pos)
        node = PositionedNode(self.__model.graph, x_pos, y_pos, 0, 30)

        command = CreateNodeCommand(self.__model.graph, node, self.__model)
        self.__command_handler.add_command(command)

    def remove_nodes_and_branches(self, nodes_and_branches: List):
        """Remove all nodes and branches in the given list."""

        logger.debug("Remove nodes and branches")
        # First remove ALL branches or adjacent branches would be
        # missing after node remove
        cmds = []
        # Remove selected branches
        for node_or_branch in nodes_and_branches:
            if isinstance(node_or_branch, CurvedBranch):
                cmds.append(RemoveBranchCommand(
                    self.__model.graph, node_or_branch, self.__model))
                node_or_branch.remove()

        # Remove nodes with connected branches
        for node_or_branch in nodes_and_branches:
            if isinstance(node_or_branch, PositionedNode):
                # Get connected branches and remove them
                connected_branches = node_or_branch.outgoing.union(
                    node_or_branch.ingoing)
                for branch in connected_branches:
                    cmds.append(RemoveBranchCommand(
                        self.__model.graph, branch))
                    branch.remove()
                cmds.append(RemoveNodeCommand(
                    self.__model.graph, node_or_branch, self.__model))
                node_or_branch.remove()

        self.__command_handler.add_command(ScriptCommand(cmds))

    def move_node(self, node: PositionedNode, dx: int, dy: int):
        """Move node dx, dy pixels."""
        logger.debug("Move node, dx: %s, dy: %s", dx, dy)
        self.__model.graph.move_node_relative(node, dx, dy)
        for branch in node.ingoing:
            self.__command_handler.add_command(TransformBranchCommand(
                self.__model.graph,
                branch,
                0, 0,
                dx, dy))
            self.__model.graph.transform_branch(branch, 0, 0, dx, dy)

        for branch in node.outgoing:
            self.__command_handler.add_command(TransformBranchCommand(
                self.__model.graph,
                branch,
                dx, dy,
                0, 0))
            self.__model.graph.transform_branch(branch, dx, dy, 0, 0)

        command = MoveNodeCommand(node, dx, dy, self.__model.graph)
        self.__command_handler.add_command(command)

    def move_label_relative(self,
                            labeled_object: LabeledObject,
                            dx: int,
                            dy: int):
        """Move label relative to its parent object."""
        logger.debug("Move label realtive, dx: %s, dy: %s", dx, dy)
        command = MoveLabelCommand(labeled_object, dx, dy, self.__model.graph)
        self.__command_handler.add_command(command)
        command.redo()

    def set_branch_weight(self, branch: CurvedBranch, weight: str):
        """Set the given weight to the given branch."""
        logger.debug("Set new weight: %s", weight)
        command = ChangeBranchWeightCommand(branch, weight, self.__model.graph)
        command.redo()
        self.__command_handler.add_command(command)

    def set_node_name(self, node: PositionedNode, name: str):
        """Set the given name for the given node."""
        logger.debug("Set node name: %s", name)
        command = ChangeNodeNameCommand(node, name, self.__model.graph)
        command.redo()
        self.__command_handler.add_command(command)

    def transform_branch(self,
                         branch: CurvedBranch,
                         spline1_dx: int,
                         spline1_dy: int,
                         spline2_dx: int,
                         spline2_dy: int):
        """Transform the given branch with the given deltas."""
        logger.debug("Transform branch, spline1_dx: %s, spline1_dy: %s, "
                     "spline2_dx: %s, spline2_dy: %s",
                     spline1_dx,
                     spline1_dy,
                     spline2_dx,
                     spline2_dy)
        self.__command_handler.add_command(
            TransformBranchCommand(self.__model.graph,
                                   branch,
                                   spline1_dx,
                                   spline1_dy,
                                   spline2_dx,
                                   spline2_dy))
        self.__model.graph.transform_branch(branch,
                                            spline1_dx,
                                            spline1_dy,
                                            spline2_dx,
                                            spline2_dy)

    def create_branch(self,
                      start_node: PositionedNode,
                      end_node: PositionedNode,
                      spline1_x: int, spline1_y: int,
                      spline2_x: int, spline2_y: int,
                      label_dx: int, label_dy: int,
                      weight: str = ""):
        """Create branch between the given
           nodes with the given spline positions
        """
        logger.debug("Create branch, spline1_x: %s, spline1_y: %s, "
                     "spline2_x: %s, spline2_y: %s",
                     spline1_x,
                     spline1_y,
                     spline2_x,
                     spline2_y)
        branch = CurvedBranch(start_node, end_node, spline1_x,
                              spline1_y, spline2_x, spline2_y,
                              label_dx, label_dy, weight)
        self.__command_handler.add_command(
            CreateBranchCommand(self.__model.graph, branch, self.__model))

    def create_branch_auto_pos(self,
                               start_node: PositionedNode,
                               end_node: PositionedNode,
                               weight: str = ""):
        """Create branch between nodes, calculate initial spline positions"""
        logger.debug("Create branch auto pos")
        # Calculate initial spline position
        # Branch should not overlap with other branches

        if start_node is end_node:
            raise ValueError("Cannot create self loop, use dedicated method.")

        # Find Branches with similar start / end positions
        # or which are straight lines and are on the same line
        # (collinear points)
        overlap = list()
        for branch in self.__model.graph.branches:
            (exist_start,
             exist_end,
             exist_spline1,
             exist_spline2) = self.__get_points_of_branch(branch)

            new_start = [start_node.x, start_node.y]
            new_end = [end_node.x, end_node.y]

            # Add branch to overlap if it has similar start
            # and end points (check both ways if one branch is flipped)
            if ((distance(exist_start, new_start)
                 + distance(exist_end, new_end) < 40)
                or (distance(exist_start, new_end)
                    + distance(exist_end, new_start) < 40)):
                overlap.append(branch)

            # Check if the existing branch is straight and
            # is on the same line as the new branch
            if (collinear([exist_spline1,
                           exist_spline2,
                           exist_start,
                           exist_end,
                           new_start,
                           new_end])):
                overlap.append(branch)

        # Calculate inital spline positions (forming a straight line)
        max_x = max(start_node.x, end_node.x)
        max_y = max(start_node.y, end_node.y)
        min_x = min(start_node.x, end_node.x)
        min_y = min(start_node.y, end_node.y)

        spline1_x = min_x + (max_x - min_x) / 2
        spline1_y = min_y + (max_y - min_y) / 2
        spline2_x, spline2_y = spline1_x, spline1_y

        if len(overlap) > 0:
            distance_step_size = math.hypot(max_x - min_x, max_y - min_y) / 2

            # Adjust the splines until all other branches are far away
            all_far_away = False
            i = 0
            j = 1

            # Start on the upper side
            use_left_side = (start_node.x < end_node.x)
            while (not all_far_away):
                all_far_away = True

                # Check all near branches for overlapping
                for o in overlap:
                    (exist_start,
                     exist_end,
                     exist_spline1,
                     exist_spline2) = self.__get_points_of_branch(o)

                    new_spline1 = [spline1_x, spline1_y]
                    new_spline2 = [spline2_x, spline2_y]
                    new_start = [start_node.x, start_node.y]
                    new_end = [end_node.x, end_node.y]

                    # Check if the splines have similar position which means
                    # that the branch have also a similar position
                    if ((distance(exist_spline1, new_spline1)
                         + distance(exist_spline2, new_spline2) < 40)
                        or (distance(exist_spline1, new_spline2)
                            + distance(exist_spline2, new_spline1) < 40)):
                        all_far_away = False

                    # Check if all points are on the same line
                    if (collinear([exist_spline1,
                                   exist_spline2,
                                   exist_start,
                                   exist_end,
                                   new_spline1,
                                   new_start,
                                   new_spline2,
                                   new_end])):
                        if(self.__check_if_crossing([exist_start, exist_end],
                                                    [new_start, new_end])):
                            all_far_away = False

                # Increase spline position if any spline was to near
                if (not all_far_away):
                    if use_left_side:
                        (spline1_x,
                         spline1_y,
                         spline2_x,
                         spline2_y) = self.__get_spline_positions(
                            start_node,
                            end_node,
                            j * distance_step_size)
                    else:
                        (spline2_x,
                         spline2_y,
                         spline1_x,
                         spline1_y) = self.__get_spline_positions(
                            end_node,
                            start_node,
                            j * distance_step_size)

                    # Try other side on next iteration
                    use_left_side = not use_left_side
                    j += i % 2
                    i += 1

        # Calulate initial label position
        middle_x = (start_node.x + end_node.x) / 2
        middle_y = (start_node.y + end_node.y) / 2
        [label_x, label_y] = rotate([middle_x, middle_y],
                                    move([middle_x, middle_y],
                                         [end_node.x, end_node.y],
                                         30),
                                    math.pi / 2)

        # Create branch
        self.create_branch(start_node, end_node,
                           spline1_x, spline1_y,
                           spline2_x, spline2_y,
                           label_x - middle_x, label_y - middle_y,
                           weight)

    def create_self_loop(self, node: PositionedNode, weight=""):
        """
        Create a self loop.
        """
        logger.debug("Create self loop")
        y_offset = -100
        y_offset_label = -40
        angle_deg = 45
        x, y = node.x, node.y
        spline_1x, spline_1y = rotate(
            (x, y),
            (x, y + y_offset),
            math.radians(angle_deg))
        spline_2x, spline_2y = rotate(
            (x, y),
            (x, y + y_offset),
            math.radians(-angle_deg))

        # Check if there are other self loops
        other_loops = list(filter(lambda branch: branch.start == node
                                  and branch.end == node,
                                  self.__model.graph.branches))
        if (len(other_loops) > 0):
            all_far_away = False
            while(not all_far_away):
                all_far_away = True
                for branch in other_loops:
                    (exist_start,
                     exist_end,
                     exist_spline1,
                     exist_spline2) = self.__get_points_of_branch(branch)
                    new_spline1 = [spline_1x, spline_1y]
                    new_spline2 = [spline_2x, spline_2y]
                    if ((distance(exist_spline1, new_spline1)
                         + distance(exist_spline2, new_spline2) < 40)
                        or (distance(exist_spline1, new_spline2)
                            + distance(exist_spline2, new_spline1) < 40)):
                        all_far_away = False

                if (not all_far_away):
                    spline_1x += 30
                    spline_1y -= 30
                    spline_2x -= 30
                    spline_2y -= 30
        self.create_branch(node, node,
                           spline_1x, spline_1y,
                           spline_2x, spline_2y,
                           0, y_offset_label, weight)

    def __get_points_of_branch(self, branch: CurvedBranch) -> (List[int],
                                                               List[int],
                                                               List[int],
                                                               List[int]):
        """
        Returns start point, end point, spline1 point, splin2 point as points
        """
        spline1 = [branch.spline1_x, branch.spline1_y]
        spline2 = [branch.spline2_x, branch.spline2_y]
        start = [branch.start.x, branch.start.y]
        end = [branch.end.x, branch.end.y]
        return start, end, spline1, spline2

    def __check_if_crossing(self, line1: List, line2: List) -> bool:
        """
        Check if two given lines are crossing
        The two lines are expected to lay on the same groundline
        """
        line1_x1 = line1[0][0]
        line1_x2 = line1[1][0]
        line1_y1 = line1[0][1]
        line1_y2 = line1[1][1]
        line2_x1 = line2[0][0]
        line2_x2 = line2[1][0]
        line2_y1 = line2[0][1]
        line2_y2 = line2[1][1]

        max_x_1 = max(line1_x1, line1_x2)
        max_y_1 = max(line1_y1, line1_y2)
        max_x_2 = max(line2_x1, line2_x2)
        max_y_2 = max(line2_y1, line2_y2)
        min_x_1 = min(line1_x1, line1_x2)
        min_y_1 = min(line1_y1, line1_y2)
        min_x_2 = min(line2_x1, line2_x2)
        min_y_2 = min(line2_y1, line2_y2)

        # Check if line2 is above line 1 or exactly touching at the end
        if (min_y_2 >= max_y_1 and min_x_2 >= max_x_1):
            return False

        # Check if line1 is below line 1 or exactly touching at the end
        if (max_y_2 <= min_y_1 and max_x_2 <= min_x_1):
            return False

        return True

    def __get_spline_positions(self,
                               node1: PositionedNode,
                               node2: PositionedNode,
                               distance: float,
                               x_offset=0) -> (int, int, int, int):
        """
        Get initial spline positions relative to nodes.
        """
        tan = math.atan2(node1.y - node2.y,
                         node1.x - node2.x)
        spline1_x, spline1_y = rotate(
            [node1.x, node1.y],
            [node1.x - x_offset,
                node1.y + distance],
            tan)

        spline2_x, spline2_y = rotate(
            [node2.x, node2.y],
            [node2.x + x_offset,
                node2.y + distance],
            tan)

        return spline1_x, spline1_y, spline2_x, spline2_y
