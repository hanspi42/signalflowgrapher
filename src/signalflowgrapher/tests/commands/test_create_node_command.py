import unittest
from unittest.mock import MagicMock, Mock
from signalflowgrapher.commands.create_node_command import CreateNodeCommand
from signalflowgrapher.model.model import ObservableGraph


class TestCreateNodeCommand(unittest.TestCase):
    def test_undo(self):
        graph_mock = MagicMock(ObservableGraph)
        node_mock = Mock()
        command = CreateNodeCommand(graph_mock, node_mock)
        command.undo()

        # Assert
        node_mock.remove.assert_called_once()

    def test_redo(self):
        graph_mock = MagicMock(ObservableGraph)
        node_mock = Mock()

        command = CreateNodeCommand(graph_mock, node_mock)
        command.redo()

        # Assert
        graph_mock.add_node.assert_called_once_with(node_mock)
