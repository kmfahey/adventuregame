#!/usr/bin/python3

from advgame import stmsg as stmsg

from advgame.commands.utils import (
    _matching_door,
    _preprocessing_for_lock_unlock_open_or_close,
)

from advgame.elements import Door


__all__ = ("open_command",)


def open_command(game_state, tokens):
    """
    Execute the OPEN command. The return value is always in a tuple even
    when it's of length 1. The OPEN command has the following usage:

    OPEN <door name>
    OPEN <chest name>

    * If that syntax is not followed, returns a .stmsg.command.BadSyntax
    object.

    * If trying to open a door which is not present in the room, returns a
    .stmsg.various.DoorNotPresent object.

    * If trying to open a door, but the command is ambiguous and matches
    more than one door, returns a .stmsg.various.AmbiguousDoorSpecifier
    object.

    * If trying to open an item, creature, corpse or doorway, returns a
    .stmsg.open_.ElementNotOpenable object.

    * If trying to open a chest that is not present in the room, returns a
    .stmsg.open_.ElementtoOpenNotHere object.

    * If trying to open a door or chest that is locked, returns a
    .stmsg.open_.ElementIsLocked object.

    * If trying to open a door or chest that is already open, returns a
    .stmsg.open_.ElementIsAlreadyOpen object.

    * Otherwise, the chest or door has its is_closed attribute set to False,
    and returns returns a .stmsg.open_.ElementHasBeenOpened..
    """
    # The shared private workhorse method is called and it handles
    # the majority of the error-checking. If it returns an error
    # that is passed along.
    result = _preprocessing_for_lock_unlock_open_or_close(game_state, "OPEN", tokens)
    if isinstance(result[0], stmsg.GameStateMessage):
        return result
    else:
        # Otherwise the element to open is extracted from the return
        # tuple.
        (element_to_open,) = result

    # If the element is locked, a element-is-locked error is
    # returned.
    if element_to_open.is_locked:
        return (stmsg.open_.ElementIsLocked(element_to_open.title),)
    elif not element_to_open.is_closed:
        # Otherwise if it's alreadty open, an
        # element-is-already-open error is returned.
        return (stmsg.open_.ElementIsAlreadyOpen(element_to_open.title),)
    elif isinstance(element_to_open, Door):
        # This is a door object, and it only represents _this side_
        # of the door game element; I use _matching_door() to fetch
        # the door object representing the opposite side so that the
        # door game element will be open from the perspective of
        # either room.
        opposite_door = _matching_door(game_state, element_to_open)
        if opposite_door is not None:
            opposite_door.is_closed = False

    # The element has is_closed set to False and an
    # element-has-been-opened value is returned.
    element_to_open.is_closed = False
    return (stmsg.open_.ElementHasBeenOpened(element_to_open.title),)
