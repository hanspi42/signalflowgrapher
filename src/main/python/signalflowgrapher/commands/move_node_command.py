from signalflowgrapher.commands.command_handler import MergeableCommand
from signalflowgrapher.model.model import Model


class MoveNodeCommand(MergeableCommand):
    def __init__(self, node, xMovement: int, yMovement: int, model: Model):
        self.__node = node
        self.__xMovement = xMovement
        self.__yMovement = yMovement
        self.__model = model

    def undo(self):
        self.__model.move_node_relative(
            self.__node, -self.__xMovement, -self.__yMovement)

    def redo(self):
        self.__model.move_node_relative(
            self.__node, self.__xMovement, self.__yMovement)

    def merge(self, cmd):
        if cmd.get_ressource() is not self.get_ressource():
            raise ValueError("Command must have the same ressource for merge.")

        return MoveNodeCommand(cmd.__node,
                               self.__xMovement + cmd.__xMovement,
                               self.__yMovement + cmd.__yMovement,
                               self.__model)

    def get_ressource(self):
        return self.__node
