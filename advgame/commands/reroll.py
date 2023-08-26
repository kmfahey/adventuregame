#!/usr/bin/python3

from advgame import stmsg as stmsg

from advgame.commands.constants import COMMANDS_SYNTAX


__all__ = ("reroll_command",)


def reroll_command(game_state, tokens):
    """
    Execute the REROLL command. The return value is always in a tuple even
    when it's of length 1. The REROLL command takes no arguments.

    * If the command is used with any arguments, this method returns a
    .stmsg.command.BadSyntax object.

    * If the character's name or class has not been set yet, returns a
    .stmsg.reroll.NameOrClassNotSet object.

    * Otherwise, ability scores for the character are rolled, and a
    .stmsg.various.DisplayRolledStats is returned.
    """
    # This command takes no arguments, so if any were supplied, I
    # return a syntax error.
    if len(tokens):
        return (stmsg.command.BadSyntax("REROLL", COMMANDS_SYNTAX["REROLL"]),)

    # This command is only valid during the pregame after the
    # character's name and class have been set (and, therefore,
    # their stats have been rolled). If either one is None, I return
    # a name-or-class-not-set error.
    character_name = getattr(game_state, "character_name", None)
    character_class = getattr(game_state, "character_class", None)
    if not character_name or not character_class:
        return (stmsg.reroll.NameOrClassNotSet(character_name, character_class),)

    # I reroll the player character's stats, and return a
    # display-rolled-stats value.
    game_state.character.ability_scores.roll_stats()
    return (
        stmsg.various.DisplayRolledStats(
            strength=game_state.character.strength,
            dexterity=game_state.character.dexterity,
            constitution=game_state.character.constitution,
            intelligence=game_state.character.intelligence,
            wisdom=game_state.character.wisdom,
            charisma=game_state.character.charisma,
        ),
    )
