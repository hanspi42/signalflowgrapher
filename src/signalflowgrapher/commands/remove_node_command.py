from signalflowgrapher.commands.command_handler import Command
from signalflowgrapher.model.model import ObservableGraph, PositionedNode, Model


class RemoveNodeCommand(Command):
    def __init__(self, graph: ObservableGraph, node: PositionedNode, model: Model):
        self.__graph = graph
        self.__node = node
        self.__model = model
        self.__gridpos_atCreation = self.__model.get_grid_position()

    def undo(self):
        # Restore node position
        gridpos_new = self.__model.get_grid_position()
        dx = gridpos_new[0] - self.__gridpos_atCreation[0]
        dy = gridpos_new[1] - self.__gridpos_atCreation[1]
        self.__node.move(dx, dy)
        self.__gridpos_atCreation = gridpos_new

        # Readd node to graph
        self.__graph.add_node(self.__node)

    def redo(self):
        # Remove node
        self.__node.remove()
        # Grid position reset (No position correction is necessary as long as the node is not removed.)
        self.__gridpos_atCreation = self.__model.get_grid_position()
