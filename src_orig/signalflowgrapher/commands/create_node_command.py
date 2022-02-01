from signalflowgrapher.commands.command_handler import Command
from signalflowgrapher.model.model import ObservableGraph, PositionedNode


class CreateNodeCommand(Command):
    def __init__(self, graph: ObservableGraph, node: PositionedNode):
        self.__graph = graph
        self.__node = node

    def undo(self):
        # Remove node
        self.__node.remove()

    def redo(self):
        # Readd node to graph
        self.__graph.add_node(self.__node)
