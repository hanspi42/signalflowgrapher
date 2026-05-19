import unittest
from unittest.mock import MagicMock, Mock
from signalflowgrapher.commands.create_branch_command \
    import CreateBranchCommand
from signalflowgrapher.model.model import ObservableGraph, Model


class TestCreateBranchCommand(unittest.TestCase):
    def test_undo(self):
        # Prepare
        graph_mock = MagicMock(ObservableGraph)
        branch_mock = Mock()
        model_mock = MagicMock(Model)

        command = CreateBranchCommand(graph_mock, branch_mock, model_mock)

        # Execute
        command.undo()

        # Assert
        branch_mock.remove.assert_called_once()

    def test_redo(self):
        # Prepare
        graph_mock = MagicMock(ObservableGraph)
        branch_mock = Mock()
        start_node_mock = Mock()
        end_node_mock = Mock()
        model_mock = MagicMock(Model)
        branch_mock.start = start_node_mock
        branch_mock.end = end_node_mock

        command = CreateBranchCommand(graph_mock, branch_mock, model_mock)

        # Execute
        command.redo()

        # Assert
        branch_mock.reconnect \
            .assert_called_once_with(start_node_mock, end_node_mock)
