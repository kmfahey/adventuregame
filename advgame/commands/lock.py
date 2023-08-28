#!/usr/bin/python3

from advgame import stmsg as stmsg

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.commands.utils import (
    _matching_door,
    _preprocessing_for_lock_unlock_open_or_close,
)

from advgame.elements import Door


__all__ = ("lock_command",)


def lock_command(game_state, tokens):
    """
    Execute the LOCK command. The return value is always in a tuple even
    when it's of length 1. The LOCK command has the following usage:

    LOCK <door name>
    LOCK <chest name>

    * If that syntax is not followed, returns a .stmsg.command.BadSyntaxGSM
    object.

    * If no such door is present in the room, returns a
    .stmsg.various.DoorNotPresentGSM object.

    * If the command is ambiguous and matches more than one door in the
    room, returns a .stmsg.various.AmbiguousDoorSpecifierGSM object.

    * If the object to lock is not present, returns a
    .stmsg.lock.ElementToLockNotHereGSM object.

    * If the object to lock is already locked, returns a
    .stmsg.lock.ElementIsAlreadyLockedGSM object.

    * If the object to lock is not present, a .stmsg.lock.ElementNotLockableGSM
    is returned.

    * If the character does not possess the requisite door or
    chest key to lock the specified door or chest, returns a
    .stmsg.lock.DontPossessCorrectKeyGSM object.

    * Otherwise, the object has its is_locked attribute set to True, and a
    .stmsg.lock.ElementHasBeenLockedGSM object is returned.
    """
    # This command requires an argument, so if tokens is zero-length
    # a syntax error is returned.
    if not len(tokens):
        return (stmsg.command.BadSyntaxGSM("LOCK", COMMANDS_SYNTAX["LOCK"]),)

    # A private workhorse method is used for logic shared
    # with unlock_command(), open_command(),
    # close_command().
    result = _preprocessing_for_lock_unlock_open_or_close(game_state, "LOCK", tokens)

    # As always with a workhorse method, the result is checked
    # to see if it's an error value. If so, the result tuple is
    # returned as-is.
    if isinstance(result[0], stmsg.GameStateMessage):
        return result
    else:
        # Otherwise, the element to lock is extracted from the
        # return value.
        (element_to_lock,) = result

    # Locking something requires the matching key in inventory. The
    # key's item title is determined, and the player character's
    # inventory is searched for a matching Key object. The object
    # isn't used for anything (it's not expended), so I don't save
    # it, just check if it's there.
    key_required = "door key" if isinstance(element_to_lock, Door) else "chest key"
    if not any(
        item.title == key_required for _, item in game_state.character.list_items()
    ):
        # Lacking the key, a don't-possess-correct-key error is
        # returned.
        return (stmsg.lock.DontPossessCorrectKeyGSM(element_to_lock.title, key_required),)

    # If the element_to_lock is already locked, a
    # element-is-already-locked error is returned.
    elif element_to_lock.is_locked:
        return (stmsg.lock.ElementIsAlreadyUnlockedGSM(element_to_lock.title),)
    elif isinstance(element_to_lock, Door):
        # This is a door object, and it only represents _this side_
        # of the door game element; I use _matching_door() to fetch
        # the door object representing the opposite side so that the
        # door game element will be locked from the perspective of
        # either room.
        opposite_door = _matching_door(game_state, element_to_lock)
        if opposite_door is not None:
            opposite_door.is_locked = True

    # The element_to_lock's is_locked attribute is set to rue, and a
    # Telement-has-been-locked value is returned.
    element_to_lock.is_locked = True
    return (stmsg.lock.ElementHasBeenUnlockedGSM(element_to_lock.title),)
