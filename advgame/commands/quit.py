#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.quit import HaveQuitTheGameGSM


__all__ = ("quit_command",)


def quit_command(context, tokens):
    """
    Execute the QUIT command. The return value is always in a tuple even
    when it's of length 1. The QUIT command takes no arguments.

    * If the command is used with any arguments, returns a
    BadSyntaxGSM object.

    * Otherwise, the game is ended, and a HaveQuitTheGameGSM object
    is returned.
    """
    # This command takes no arguments, so if any were supplied, I
    # return a syntax error.
    if len(tokens):
        return (BadSyntaxGSM("QUIT", COMMANDS_SYNTAX["QUIT"]),)

    # I devise the quit-the-game return value, set game_has_ended
    # to True, store the return value in game_ending_state_msg so
    # process() can reuse it if needs be, and return the value.
    return_tuple = (HaveQuitTheGameGSM(),)
    context.game_state.game_has_ended = True
    context.game_ending_state_msg = return_tuple[-1]
    return return_tuple
