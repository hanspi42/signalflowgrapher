from signalflowgrapher.commands.command_handler import MergeableCommand
from signalflowgrapher.model.model import Model, LabeledObject


class MoveLabelCommand(MergeableCommand):
    def __init__(self,
                 labeled_object: LabeledObject,
                 dx: int,
                 dy: int,
                 model: Model):
        self.__labeled_object = labeled_object
        self.__dx = dx
        self.__dy = dy
        self.__model = model

    def undo(self):
        self.__model.move_label_relative(self.__labeled_object,
                                         -self.__dx, -self.__dy)

    def redo(self):
        self.__model.move_label_relative(self.__labeled_object,
                                         self.__dx,
                                         self.__dy)

    def merge(self, cmd):
        if cmd.get_ressource() is not self.get_ressource():
            raise ValueError("Command must have the same ressource for merge.")

        return MoveLabelCommand(self.__labeled_object,
                                self.__dx + cmd.__dx,
                                self.__dy + cmd.__dy,
                                self.__model)

    def get_ressource(self):
        return self.__labeled_object
