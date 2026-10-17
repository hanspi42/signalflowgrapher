import unittest
from unittest.mock import MagicMock, Mock
from signalflowgrapher.commands.remove_node_command import RemoveNodeCommand
from signalflowgrapher.model.model import ObservableGraph


class TestRemoveNodeCommand(unittest.TestCase):
    def test_redo(self):
        graph_mock = MagicMock(ObservableGraph)
        node_mock = Mock()
        command = RemoveNodeCommand(graph_mock, node_mock)
        command.redo()

        # Assert
        node_mock.remove.assert_called_once()

    def test_undo(self):
        graph_mock = MagicMock(ObservableGraph)
        node_mock = Mock()

        command = RemoveNodeCommand(graph_mock, node_mock)
        command.undo()

        # Assert
        graph_mock.add_node.assert_called_once_with(node_mock)
