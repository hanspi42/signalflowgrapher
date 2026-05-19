from signalflowgrapher.commands.command_handler import Command
from signalflowgrapher.model.model import ObservableGraph, CurvedBranch, Model


class RemoveBranchCommand(Command):
    def __init__(self, graph: ObservableGraph, branch: CurvedBranch, model: Model):
        self.__graph = graph
        self.__branch = branch
        self.__start_node = branch.start
        self.__end_node = branch.end
        self.__model = model
        self.__gridpos_atCreation = self.__model.get_grid_position()

    def undo(self):
        # Restore node position
        gridpos_new = self.__model.get_grid_position()
        dx = gridpos_new[0] - self.__gridpos_atCreation[0]
        dy = gridpos_new[1] - self.__gridpos_atCreation[1]
        self.__branch.transform(dx, dy, dx, dy)
        self.__gridpos_atCreation = gridpos_new

        # Reconnect branch
        self.__branch.reconnect(self.__start_node, self.__end_node)

    def redo(self):
        # Remove branch from nodes and graph
        self.__branch.remove()
        # Grid position reset (No position correction is necessary as long as the node is not removed.)
        self.__gridpos_atCreation = self.__model.get_grid_position()