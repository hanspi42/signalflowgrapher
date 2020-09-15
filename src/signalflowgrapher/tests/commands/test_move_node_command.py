import unittest
from unittest.mock import MagicMock
from signalflowgrapher.commands.move_node_command import MoveNodeCommand
from signalflowgrapher.model.model import PositionedNode, ObservableGraph


class TestMoveNodeCommand(unittest.TestCase):
    def test_redo(self):
        node_mock = MagicMock(PositionedNode)
        model_mock = MagicMock(ObservableGraph)
        command = MoveNodeCommand(node_mock, 7, 12, model_mock)
        command.redo()
        model_mock.move_node_relative \
            .assert_called_once_with(node_mock, 7, 12)

    def test_undo(self):
        node_mock = MagicMock(PositionedNode)
        model_mock = MagicMock(ObservableGraph)
        command = MoveNodeCommand(node_mock, 7, 12, model_mock)
        command.undo()
        model_mock.move_node_relative \
            .assert_called_once_with(node_mock, -7, -12)
