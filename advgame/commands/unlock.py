#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.commands.utils import (
    _preprocessing_for_lock_unlock_open_or_close,
    _matching_door,
)
from advgame.elements import Door
from advgame.statemsgs import GameStateMessage
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.unlock import (
    DontPossessCorrectKeyGSM,
    ElementHasBeenUnlockedGSM,
    ElementIsAlreadyUnlockedGSM,
)


__all__ = ("unlock_command",)


def unlock_command(game_state, tokens):
    """
    Execute the UNLOCK command. The return value is always in a tuple even
    when it's of length 1. The UNLOCK command has the following usage:

    UNLOCK <door\u00A0name>
    UNLOCK <chest\u00A0name>

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If the arguments specify a door that is not present in the room,
    returns a DoorNotPresentGSM object.

    * If the arguments given match more than one door in the room, returns a
    AmbiguousDoorSpecifierGSM object.

    * If the specified door or chest is not present in the current room,
    returns a ElementToUnlockNotHereGSM object.

    * If the specified element is a doorway, item, creature or corpse,
    returns a ElementNotUnlockableGSM object.

    * If the character does not possess the requisite door or
    chest key to lock the specified door or chest, returns an
    DontPossessCorrectKeyGSM object.

    * If the specified door or chest is already unlocked, returns a
    ElementIsAlreadyUnlockedGSM object.

    * Otherwise, the specified door or chest is unlocked, and a
    ElementHasBeenUnlockedGSM object is returned.
    """
    # This command requires an argument; so if it was called with no
    # arguments, I return a syntax error.
    if len(tokens) == 0:
        return (BadSyntaxGSM("UNLOCK", COMMANDS_SYNTAX["UNLOCK"]),)

    # unlock_command() shares preprocessing logic with
    # lock_command(), open_command() and close_command(), so a
    # private workhorse method is called.
    result = _preprocessing_for_lock_unlock_open_or_close(game_state, "UNLOCK", tokens)
    if isinstance(result[0], GameStateMessage):
        # If an error value is returned, I return it in turn.
        return result
    else:
        # Otherwise I extract the element_to_unlock from the result
        # tuple.
        (element_to_unlock,) = result

    # A key is required to unlock something; the chest key for
    # chests and the door key for doors. So I search the player
    # character's inventory for it. The key is not consumed by use,
    # so I only need to know it's there, not retrieve the Key object
    # and operate on it.
    key_required = "door key" if isinstance(element_to_unlock, Door) else "chest key"
    if not any(
        item.title == key_required for _, item in game_state.character.list_items()
    ):
        # If the required key is not present, I return a
        # don't-possess-correct-key error.
        return (DontPossessCorrectKeyGSM(element_to_unlock.title, key_required),)
    elif element_to_unlock.is_locked is False:
        # Otherwise, if the item is already unlocked, I return an
        # element-is-already-unlocked error.
        return (ElementIsAlreadyUnlockedGSM(element_to_unlock.title),)
    elif isinstance(element_to_unlock, Door):
        # This is a door object, and it only represents _this side_
        # of the door game element; I use _matching_door() to fetch
        # the door object representing the opposite side so that the
        # door game element will be unlocked from the perspective of
        # either room.
        opposite_door = _matching_door(game_state, element_to_unlock)
        if opposite_door is not None:
            opposite_door.is_locked = False

    # I unlock the element, and return an element-has-been-unlocked
    # value.
    element_to_unlock.is_locked = False
    return (ElementHasBeenUnlockedGSM(element_to_unlock.title),)
