from signalflowgrapher.commands.command_handler import MergeableCommand
from signalflowgrapher.model.model import ObservableGraph, CurvedBranch


class TransformBranchCommand(MergeableCommand):
    def __init__(self,
                 graph: ObservableGraph,
                 branch: CurvedBranch,
                 spline1_dx: int,
                 spline1_dy: int,
                 spline2_dx: int,
                 spline2_dy: int):
        self.__graph = graph
        self.__branch = branch
        self.__spline1_dx = spline1_dx
        self.__spline1_dy = spline1_dy
        self.__spline2_dx = spline2_dx
        self.__spline2_dy = spline2_dy

    def undo(self):
        self.__graph.transform_branch(self.__branch,
                                      -self.__spline1_dx,
                                      -self.__spline1_dy,
                                      -self.__spline2_dx,
                                      -self.__spline2_dy)

    def redo(self):
        self.__graph.transform_branch(self.__branch,
                                      self.__spline1_dx,
                                      self.__spline1_dy,
                                      self.__spline2_dx,
                                      self.__spline2_dy)

    def merge(self, cmd):
        if cmd.get_ressource() is not self.get_ressource():
            raise ValueError("Command must have the same ressource for merge.")

        return TransformBranchCommand(
            self.__graph,
            cmd.__branch,
            self.__spline1_dx + cmd.__spline1_dx,
            self.__spline1_dy + cmd.__spline1_dy,
            self.__spline2_dx + cmd.__spline2_dx,
            self.__spline2_dy + cmd.__spline2_dy)

    def get_ressource(self):
        return self.__branch
