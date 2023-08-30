#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.inven import DisplayInventoryGSM


__all__ = ("inventory_command",)


def inventory_command(game_state, tokens):
    """
    Execute the INVENTORY command. The return value is always in a tuple
    even when it's of length 1. The INVENTORY command takes no arguments.

    * If the command is used with any arguments, returns a BadSyntaxGSM
    object.

    * Otherwise, returns a DisplayInventoryGSM object.
    """
    # This command takes no arguments; if any are specified, a
    # syntax error is returned.
    if len(tokens):
        return (BadSyntaxGSM("INVENTORY", COMMANDS_SYNTAX["INVENTORY"]),)

    # There's not really any other error case, for once.
    # The inventory contents are stored in a tuple, and a
    # display-inventory value is returned with the tuple to display.
    inventory_contents = sorted(
        game_state.character.list_items(), key=lambda argl: argl[1].title
    )
    return (DisplayInventoryGSM(inventory_contents),)
