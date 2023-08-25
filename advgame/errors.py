#!/usr/bin/python3

"""
This module stores the exceptions used by other advgame modules.
"""

__all__ = "BadCommandError", "InternalError",


class InternalError(Exception):
    """
This Exception subclass represents an internal error.
    """
    pass


class BadCommandError(Exception):
    """
This Exception subclass represents an error caused by a misuse of a command.
    """
    __slots__ = 'command', 'message'

    def __init__(self, command, message):
        """
This __init__ method initializes a BadCommandError.

:command_str: The command that was being executed when this error was encountered.
:message:     The exception message.
        """
        self.command = command
        self.message = message
