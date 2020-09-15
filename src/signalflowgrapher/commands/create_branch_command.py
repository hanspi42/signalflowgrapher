from signalflowgrapher.commands.command_handler import Command
from signalflowgrapher.model.model import ObservableGraph, CurvedBranch


class CreateBranchCommand(Command):
    def __init__(self, graph: ObservableGraph, branch: CurvedBranch):
        self.__graph = graph
        self.__branch = branch
        self.__start_node = branch.start
        self.__end_node = branch.end

    def undo(self):
        # Remove branch from nodes and graph
        self.__branch.remove()

    def redo(self):
        # Reconnect branch
        self.__branch.reconnect(self.__start_node, self.__end_node)
