import unittest
from signalflowgrapher.commands.command_handler import CommandHandler
from unittest.mock import MagicMock
from signalflowgrapher.commands.create_node_command import CreateNodeCommand


class TestCommandHandler(unittest.TestCase):
    def test_can_undo(self):
        command_handler = CommandHandler()
        self.assertFalse(command_handler.can_undo.get())

        mock = MagicMock()
        command_handler.add_command(mock)
        self.assertTrue(command_handler.can_undo.get())

        command_handler.undo()
        self.assertFalse(command_handler.can_undo.get())

    def test_can_redo(self):
        command_handler = CommandHandler()
        self.assertFalse(command_handler.can_redo.get())

        mock = MagicMock()
        command_handler.add_command(mock)
        self.assertFalse(command_handler.can_redo.get())

        command_handler.undo()
        self.assertTrue(command_handler.can_redo.get())

        command_handler.redo()
        self.assertFalse(command_handler.can_redo.get())

    def test_undo_redo(self):
        command_handler = CommandHandler()
        self.assertFalse(command_handler.can_redo.get())
        self.assertFalse(command_handler.can_undo.get())

        mock = MagicMock(CreateNodeCommand)
        command_handler.add_command(mock)
        self.assertTrue(command_handler.can_undo.get())
        self.assertFalse(command_handler.can_redo.get())

        command_handler.undo()
        mock.undo.assert_called()

        self.assertFalse(command_handler.can_undo.get())
        self.assertTrue(command_handler.can_redo.get())

        command_handler.redo()
        mock.undo.assert_called()

        self.assertTrue(command_handler.can_undo.get())
        self.assertFalse(command_handler.can_redo.get())

    def test_duplicate_start(self):
        command_handler = CommandHandler()
        command_handler.start_script()
        self.assertRaises(ValueError, command_handler.start_script)

    def test_no_script_running(self):
        command_handler = CommandHandler()
        self.assertRaises(ValueError, command_handler.end_script)
        command_handler.start_script()
        command_handler.end_script()
        self.assertRaises(ValueError, command_handler.end_script)

    def test_with_script(self):
        command_handler = CommandHandler()

        call_order = []

        command_1 = MagicMock()
        command_2 = MagicMock()
        command_3 = MagicMock()
        command_1.undo = lambda: call_order.append(1)
        command_2.undo = lambda: call_order.append(2)
        command_3.undo = lambda: call_order.append(3)

        command_handler.start_script()
        command_handler.add_command(command_1)
        command_handler.add_command(command_2)
        command_handler.add_command(command_3)
        command_handler.end_script()

        command_handler.undo()
        self.assertEqual([3, 2, 1], call_order)

        call_order = []
        command_1.redo = lambda: call_order.append(1)
        command_2.redo = lambda: call_order.append(2)
        command_3.redo = lambda: call_order.append(3)

        command_handler.redo()
        self.assertEqual([1, 2, 3], call_order)

    def test_undo_redo_when_script_running(self):
        command_handler = CommandHandler()

        command_1 = MagicMock()
        command_2 = MagicMock()
        command_handler.add_command(command_1)
        command_handler.add_command(command_2)

        command_handler.undo()

        command_handler.start_script()
        self.assertRaises(ValueError, command_handler.undo)
        self.assertRaises(ValueError, command_handler.redo)
