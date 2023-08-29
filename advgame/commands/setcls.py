#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.setcls import ClassSetGSM, InvalidClassGSM
from advgame.statemsgs.various import DisplayRolledStatsGSM


__all__ = ("set_class_command",)


def set_class_command(game_state, tokens):
    """
    Execute the SET CLASS command. The return value is always in a tuple
    even when it's of length 1. The SET CLASS command has the following
    usage:

    SET CLASS [TO] <Warrior, Thief, Mage or Priest>

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If a class other than Warrior, Thief, Mage or Priest is specified,
    returns a InvalidClassGSM object.

    * If the name has not yet been set, then the class is set, and a
    ClassSetGSM object is returned.

    * If the name has been set, then the class is set, ability scores for
    the character are rolled, and a ClassSetGSM object and a
    Stmsg_Various_DisplayRolledStats object is returned.
    """
    # This command takes exactly one argument, so I return a syntax
    # error if I got 0 or more than 1.
    if len(tokens) == 0 or len(tokens) > 1:
        return (BadSyntaxGSM("SET CLASS", COMMANDS_SYNTAX["SET CLASS"]),)

    # If the user specified something other than one of the four
    # classes, I return an invalid-class error.
    elif tokens[0] not in ("Warrior", "Thief", "Mage", "Priest"):
        return (InvalidClassGSM(tokens[0]),)

    # I assign the chosen classname, record whether this is the
    # first time this command is used, and set the class.
    class_str = tokens[0]
    class_was_none = game_state.character_class is None
    game_state.character_class = class_str

    # If character name was already set and this is the first
    # setting of character class, the Character object will have
    # been initialized as a side effect, so I return a class-set
    # value and a display-rolled-stats value.
    if game_state.character_name is not None and class_was_none:
        return (
            ClassSetGSM(class_str),
            DisplayRolledStatsGSM(
                strength=game_state.character.strength,
                dexterity=game_state.character.dexterity,
                constitution=game_state.character.constitution,
                intelligence=game_state.character.intelligence,
                wisdom=game_state.character.wisdom,
                charisma=game_state.character.charisma,
            ),
        )
    else:
        # Otherwise I return only the class-set value.
        return (ClassSetGSM(class_str),)
