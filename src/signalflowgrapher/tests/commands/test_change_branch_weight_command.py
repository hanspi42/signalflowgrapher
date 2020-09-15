import unittest
from unittest.mock import MagicMock
from signalflowgrapher.commands.change_branch_weight_command import \
    ChangeBranchWeightCommand
from signalflowgrapher.model.model import CurvedBranch, ObservableGraph


class TestChangeBranchWeightCommand(unittest.TestCase):
    def test_redo(self):
        branch_mock = MagicMock(CurvedBranch)
        branch_mock.weight = "Old Branch Weight"
        model_mock = MagicMock(ObservableGraph)
        command = ChangeBranchWeightCommand(branch_mock,
                                            "New Branch Weight",
                                            model_mock)
        command.redo()
        model_mock.set_branch_weight.assert_called_once_with(
            branch_mock, "New Branch Weight")

    def test_undo(self):
        branch_mock = MagicMock(CurvedBranch)
        branch_mock.weight = "Old Branch Weight"
        model_mock = MagicMock(ObservableGraph)
        command = ChangeBranchWeightCommand(branch_mock,
                                            "New Branch Weight",
                                            model_mock)
        command.undo()
        model_mock.set_branch_weight.assert_called_once_with(
            branch_mock, "Old Branch Weight")
