import abc
from typing import List
from signalflowgrapher.common.observable import ValueObservable
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)


class Command(abc.ABC):
    """Command for undo and redo operation."""
    @abc.abstractmethod
    def redo(self):
        pass

    @abc.abstractmethod
    def undo(self):
        pass


class MergeableCommand(Command):
    """Command that can be merged with another unrelated to its order."""
    @abc.abstractmethod
    def merge(self, cmd):
        """Return new command that merges the given command with this."""
        pass

    @abc.abstractmethod
    def get_ressource(self):
        """Get the ressource this command is applied to."""
        pass


class ScriptCommand(Command):
    """Script command for undo and redo of several commands."""

    def __init__(self, commands: List[Command]):
        abort_merge = False

        # Group type of command
        type_cmd_map = defaultdict(list)
        i = 0
        while i < len(commands) and not abort_merge:
            cmd = commands[i]
            # Abort if at least one cmd can't be merged
            if not isinstance(cmd, MergeableCommand):
                abort_merge = True
            key = type(cmd).__name__
            type_cmd_map[key].append(cmd)
            i += 1

        if not abort_merge:
            type_ressource_cmd_map = defaultdict(lambda: defaultdict(list))
            for k1, cmds in type_cmd_map.items():
                for cmd in cmds:
                    k2 = cmd.get_ressource()
                    type_ressource_cmd_map[k1][k2].append(cmd)

            self.commands = list()
            # Merge commands with same type and ressource
            for k1 in type_ressource_cmd_map:
                cmds_by_type = type_ressource_cmd_map[k1]
                for k2 in cmds_by_type:
                    cmds_by_ressource = cmds_by_type[k2]
                    cmds = iter(cmds_by_ressource)
                    merged = next(cmds, None)
                    if merged is not None:
                        current = next(cmds, None)
                        while current is not None:
                            merged = merged.merge(current)
                            current = next(cmds, None)
                        self.commands.append(merged)
            logger.debug(
                "Script command merge successful - reduced from " +
                str(len(commands)) + " to " + str(len(self.commands)))
        else:
            logger.debug(
                "Script command merge unsuccessful - using raw commands")
            self.commands = commands

    def undo(self):
        for cmd in reversed(self.commands):
            cmd.undo()

    def redo(self):
        for cmd in self.commands:
            cmd.redo()


class CommandHandler(object):
    def __init__(self):
        self.__undo_stack: List[Command] = []
        self.__redo_stack: List[Command] = []
        self.__script_commands = None
        self.can_undo = ValueObservable(False)
        self.can_redo = ValueObservable(False)

    def add_command(self, command: Command):
        """ Add a new command to the stack"""
        if self.__script_commands is not None:
            self.__script_commands.append(command)
        else:
            self.__undo_stack.append(command)

        self.__redo_stack.clear()
        self.__update_can_undo_redo()

    def reset(self):
        """ Clears undo / redo stack"""
        self.__undo_stack.clear()
        self.__redo_stack.clear()
        self.__update_can_undo_redo()

    def undo(self):
        """ Undo the last command"""
        if (len(self.__undo_stack)):

            if (self.__script_commands is not None):
                raise ValueError("Undo not allowed when script is running")

            command = self.__undo_stack.pop()
            command.undo()
            self.__redo_stack.append(command)
            self.__update_can_undo_redo()

    def redo(self):
        """ Redo the last undoed command"""
        if (len(self.__redo_stack)):

            if (self.__script_commands is not None):
                raise ValueError("Redo not allowed when script is running")

            command = self.__redo_stack.pop()
            command.redo()
            self.__undo_stack.append(command)
            self.__update_can_undo_redo()

    def __update_can_undo_redo(self):
        self.can_undo.set(len(self.__undo_stack))
        self.can_redo.set(len(self.__redo_stack))

    def start_script(self):
        """ Starts recording of a command script
            raises ValueError if a script is already running"""
        logger.debug("Start script")
        if (self.__script_commands is not None):
            raise ValueError("Script already running")

        self.__script_commands = []

    def end_script(self):
        """ Ends recording of a command script
            raises ValueError if no script is running"""
        logger.debug("End script")
        if (self.__script_commands is None):
            raise ValueError("No script running")

        # Assign command to temp variable because
        # the variable must be None when calling add_command
        commands = self.__script_commands
        self.__script_commands = None

        if len(commands) > 0:
            self.add_command(ScriptCommand(commands))
