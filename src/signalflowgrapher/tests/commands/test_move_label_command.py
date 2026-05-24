import unittest
from unittest.mock import MagicMock
from signalflowgrapher.commands.move_label_command import MoveLabelCommand
from signalflowgrapher.model.model import PositionedNode, ObservableGraph


class TestMoveLabelCommand(unittest.TestCase):
    def test_redo(self):
        node_mock = MagicMock(PositionedNode)
        model_mock = MagicMock(ObservableGraph)
        command = MoveLabelCommand(node_mock, 7, 12, model_mock)
        command.redo()
        model_mock.move_label_relative.assert_called_once_with(node_mock,
                                                               7,
                                                               12)

    def test_undo(self):
        node_mock = MagicMock(PositionedNode)
        model_mock = MagicMock(ObservableGraph)
        command = MoveLabelCommand(node_mock, 7, 12, model_mock)
        command.undo()
        model_mock.move_label_relative.assert_called_once_with(node_mock,
                                                               -7,
                                                               -12)
