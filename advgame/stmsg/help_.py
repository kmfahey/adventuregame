#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage
from advgame.utils import join_strs_w_comma_conj


__all__ = ("NotRecognized", "DisplayCommands", "DisplayHelpForCommand",)


class NotRecognized(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.help_command() when the
player tries to get help with a command that is not in the game.
    """

    __slots__ = 'command_attempted', 'commands_available',

    @property
    def message(self):
        return_lines = [f"The command '{self.command_attempted.upper()}' is not recognized. The full list of commands "
                        + "is:", '']
        return_lines.extend((join_strs_w_comma_conj(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return '\n'.join(return_lines)

    def __init__(self, command_attempted, commands_available):
        self.command_attempted = command_attempted
        self.commands_available = commands_available


class DisplayCommands(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.help_command() when the
player calls it with no arguments; it displays all the commands in the
game and prompts the player to ask for help with one of them.
    """

    __slots__ = 'commands_available', 'game_started'

    @property
    def message(self):
        if self.game_started:
            return_lines = ['The list of commands available ' + 'during the game is:', '']
        else:
            return_lines = ['The list of commands available ' + 'before game start is:', '']
        return_lines.extend((join_strs_w_comma_conj(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return '\n'.join(return_lines)

    def __init__(self, commands_available, game_started=True):
        self.commands_available = commands_available
        self.game_started = game_started


class DisplayHelpForCommand(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.help_command() when the
player asks for help with a specific command. It summarizes the syntax
for them and prints an informative blurb about the command.
    """

    __slots__ = 'command', 'syntax_tuple', 'instructions',

    @property
    def message(self):
        # Like BadSyntax, this message property accepts syntax
        # outlines from advgame.process.COMMANDS_SYNTAX and assembles
        # them into a list of valid usages, using unicode nonbreaking
        # spaces so the usage examples aren't broken across lines by
        # advgame.utilsities.textwrapper().
        syntax_str_list = [f"'{self.command}\u00A0{syntax_entry}'" if syntax_entry else f"'{self.command}'"
                           for syntax_entry in self.syntax_tuple]
        return_lines = [f'Help for the {self.command} command:', '']
        return_lines.extend(('Usage: ' + join_strs_w_comma_conj(syntax_str_list, 'or'), ''))
        return_lines.extend((self.instructions, ''))
        return '\n'.join(return_lines)

    def __init__(self, command, syntax_tuple=None, instructions=None):
        self.command = command
        self.syntax_tuple = syntax_tuple
        self.instructions = instructions
