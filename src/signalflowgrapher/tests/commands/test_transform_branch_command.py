import unittest
from unittest.mock import MagicMock
from signalflowgrapher.commands.transform_branch_command import \
    TransformBranchCommand
from signalflowgrapher.model.model import CurvedBranch, ObservableGraph


class TestTransformBranchCommand(unittest.TestCase):
    def test_redo(self):
        branch_mock = MagicMock(CurvedBranch)
        model_mock = MagicMock(ObservableGraph)
        command = TransformBranchCommand(model_mock, branch_mock, 7, 12, 20, 9)
        command.redo()
        model_mock.transform_branch.assert_called_once_with(
            branch_mock, 7, 12, 20, 9)

    def test_undo(self):
        branch_mock = MagicMock(CurvedBranch)
        model_mock = MagicMock(ObservableGraph)
        command = TransformBranchCommand(model_mock, branch_mock, 7, 12, 20, 9)
        command.undo()
        model_mock.transform_branch.assert_called_once_with(
            branch_mock, -7, -12, -20, -9)
