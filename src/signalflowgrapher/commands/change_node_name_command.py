from signalflowgrapher.commands.command_handler import Command
from signalflowgrapher.model.model import ObservableGraph, PositionedNode


class ChangeNodeNameCommand(Command):
    def __init__(self,
                 node: PositionedNode,
                 name: str,
                 model: ObservableGraph):
        self.__node = node
        self.__old_name = node.name
        self.__new_name = name
        self.__model = model

    def undo(self):
        self.__model.set_node_name(self.__node, self.__old_name)

    def redo(self):
        self.__model.set_node_name(self.__node, self.__new_name)
