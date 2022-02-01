from signalflowgrapher.commands.command_handler import Command
from signalflowgrapher.model.model import ObservableGraph, CurvedBranch


class ChangeBranchWeightCommand(Command):
    def __init__(self,
                 branch: CurvedBranch,
                 weight: str,
                 graph: ObservableGraph):
        self.__branch = branch
        self.__old_weight = branch.weight
        self.__new_weight = weight
        self.__graph = graph

    def undo(self):
        self.__graph.set_branch_weight(self.__branch, self.__old_weight)

    def redo(self):
        self.__graph.set_branch_weight(self.__branch, self.__new_weight)
