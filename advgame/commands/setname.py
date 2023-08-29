#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX, VALID_NAME_RE
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.setname import InvalidPartGSM, NameSetGSM
from advgame.stmsg.various import DisplayRolledStatsGSM


__all__ = ("set_name_command",)


def set_name_command(game_state, tokens):
    """
    Execute the SET NAME command. The return value is always in a tuple even
    when it's of length 1. The SET NAME command has the following usage:

    SET NAME [TO] <character name>

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If a name is specified that doesn't match the pattern [A-Z][a-z]+(
    [A-Z][a-z]+)*, returns a InvalidPartGSM object.

    * If the class has not yet been set, then the name is set, and a
    NameSetGSM object is returned.

    * If the class has been set, then the name is set, ability scores for
    the character are rolled, and a NameSetGSM object and a
    DisplayRolledStatsGSM object are returned.
    """
    # This command requires one or more arguments, so if len(tokens)
    # == 0 I return a syntax error.
    if len(tokens) == 0:
        return (BadSyntaxGSM("SET NAME", COMMANDS_SYNTAX["SET NAME"]),)

    # valid_name_re.pattern == '^[A-Z][a-z]+$'. I test each
    # token for a match, and non-matching name parts are saved.
    # If invalid_name_parts is nonempty afterwards, a separate
    # invalid-name-part error is returned for each failing name
    # part.
    invalid_name_parts = list()
    for name_part in tokens:
        if VALID_NAME_RE.match(name_part):
            continue
        invalid_name_parts.append(name_part)
    if len(invalid_name_parts):
        return tuple(map(InvalidPartGSM, invalid_name_parts))

    # If the name wasn't set before this call, I save that fact,
    # then set the character name.
    name_was_none = game_state.character_name is None
    name_str = " ".join(tokens)
    game_state.character_name = " ".join(tokens)

    # If the character class is set and this command is the
    # first time the name has been set, that means that
    # game_state has instantiated a Character object as a
    # side effect, so I return a 2-tuple of a name-set value and a
    # display-rolled-stats value.
    if game_state.character_class is not None and name_was_none:
        return (
            NameSetGSM(name_str),
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
        # Otherwise I just return a name-set value.
        return (NameSetGSM(game_state.character_name),)
