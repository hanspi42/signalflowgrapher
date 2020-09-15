import unittest
from unittest.mock import Mock
from signalflowgrapher.commands.command_handler import ScriptCommand


class TestScriptCommand(unittest.TestCase):
    def test_undo(self):
        # Prepare
        cmds = list()

        for i in range(5):
            cmd = Mock()
            cmds.append(cmd)

        command = ScriptCommand(cmds)

        # Execute
        command.undo()

        # Assert
        for cmd in cmds:
            cmd.undo.assert_called_once()

    def test_redo(self):
        # Prepare
        cmds = list()

        for i in range(5):
            cmd = Mock()
            cmds.append(cmd)

        command = ScriptCommand(cmds)

        # Execute
        command.redo()

        # Assert
        for cmd in cmds:
            cmd.redo.assert_called_once()
