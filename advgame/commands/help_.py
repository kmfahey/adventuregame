#!/usr/bin/python3

from advgame import stmsg as stmsg

from advgame.commands.constants import (
    COMMANDS_SYNTAX,
    PREGAME_COMMANDS,
    INGAME_COMMANDS,
    COMMANDS_HELP,
)


__all__ = ("help_command",)


def help_command(game_state, tokens):
    """
    Execute the HELP command. The return value is always in a tuple even
    when it's of length 1. The HELP command has the following usage:

    HELP
    HELP <command name>

    * If that syntax is not followed, returns a .stmsg.command.BadSyntax
    object.

    * If the command is used with no arguments, returns a
    .stmsg.help_.DisplayCommands object.

    * If the argument is not a recognized command, returns a
    .stmsg.help_.NotRecognized object.

    * Otherwise, returns a .stmsg.help_.DisplayHelpForCommand object.
    """
    # An ordered tuple of all commands in uppercase is displayed in
    # some return values so it is computed.

    # If called with no arguments, the help command displays a
    # generic help message listing all available commands.
    if len(tokens) == 0:
        commands_set = (
            INGAME_COMMANDS if game_state.game_has_begun else PREGAME_COMMANDS
        )
        commands_tuple = tuple(
            sorted(strval.replace("_", " ").upper() for strval in commands_set)
        )
        return (stmsg.help_.DisplayCommands(commands_tuple, game_state.game_has_begun),)

    # A specific command was included as an argument.
    else:
        command_uc = " ".join(tokens).upper()
        command_lc = "_".join(tokens).lower()

        # If the command doesn't occur in commands_tuple, a
        # command-not-recognized error is returned.
        if command_lc not in (INGAME_COMMANDS | PREGAME_COMMANDS):
            commands_tuple = tuple(
                sorted(
                    strval.replace("_", " ").upper()
                    for strval in INGAME_COMMANDS | PREGAME_COMMANDS
                )
            )
            return (stmsg.help_.NotRecognized(command_uc, commands_tuple),)
        else:
            # Otherwise, a help message for the command specified is
            # returned.
            return (
                stmsg.help_.DisplayHelpForCommand(
                    command_uc,
                    COMMANDS_SYNTAX[command_uc],
                    COMMANDS_HELP[command_uc],
                ),
            )
