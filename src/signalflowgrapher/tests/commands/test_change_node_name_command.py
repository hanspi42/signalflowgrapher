import unittest
from unittest.mock import MagicMock
from signalflowgrapher.commands.change_node_name_command import \
    ChangeNodeNameCommand
from signalflowgrapher.model.model import PositionedNode, ObservableGraph


class TestChangeNodeNameCommand(unittest.TestCase):
    def test_redo(self):
        node_mock = MagicMock(PositionedNode)
        node_mock.name = "Old Node Name"
        model_mock = MagicMock(ObservableGraph)
        command = ChangeNodeNameCommand(node_mock,
                                        "New Node Name",
                                        model_mock)
        command.redo()
        model_mock.set_node_name.assert_called_once_with(
            node_mock, "New Node Name")

    def test_undo(self):
        node_mock = MagicMock(PositionedNode)
        node_mock.name = "Old Node Name"
        model_mock = MagicMock(ObservableGraph)
        command = ChangeNodeNameCommand(node_mock,
                                        "New Node Name",
                                        model_mock)
        command.undo()
        model_mock.set_node_name.assert_called_once_with(
            node_mock, "Old Node Name")
