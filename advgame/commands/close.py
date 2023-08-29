#!/usr/bin/python3

from advgame.commands.utils import (
    _preprocessing_for_lock_unlock_open_or_close,
    _matching_door,
)
from advgame.elements import Door
from advgame.statemsgs import GameStateMessage
from advgame.statemsgs.close import ElementHasBeenClosedGSM, ElementIsAlreadyClosedGSM


__all__ = ("close_command",)


def close_command(game_state, tokens):
    """
    Execute the CLOSE command. The return value is always in a tuple even
    when it's of length 1. The CLOSE command has the following usage:

    CLOSE <door name>
    CLOSE <chest name>

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If there is no matching chest or door in the room, returns a
    ElementToCloseNotHereGSM object.

    * If there is no matching door, returns a DoorNotPresentGSM
    object.

    * If more than one door in the room matches, returns a
    AmbiguousDoorSpecifierGSM object.

    * If the door or chest specified is already closed, returns a
    ElementIsAlreadyClosedGSM object.

    * Otherwise, returns a ElementHasBeenClosedGSM object.
    """
    # The open_command(), close_command(),
    # lock_command(), and unlock_command() share the
    # majority of their logic in a private workhorse method,
    # _preprocessing_for_lock_unlock_open_or_close().
    result = _preprocessing_for_lock_unlock_open_or_close(game_state, "CLOSE", tokens)

    # As with any workhorse method, it either returns an error value
    # or the object to operate on. So I type test if the result
    # tuple's 1st element is a GameStateMessage subclass object. If
    # so, it's returned.
    if isinstance(result[0], GameStateMessage):
        return result
    else:
        # Otherwise I extract the element to close.
        (element_to_close,) = result

    # If the element to close is already closed, a
    if element_to_close.is_closed:
        return (ElementIsAlreadyClosedGSM(element_to_close.title),)
    elif isinstance(element_to_close, Door):
        # This is a door object, and it only represents _this side_
        # of the door game element; I use _matching_door() to fetch
        # the door object representing the opposite side so that the
        # door game element will be closed from the perspective of
        # either room.
        opposite_door = _matching_door(game_state, element_to_close)
        if opposite_door is not None:
            opposite_door.is_closed = True

    # I set the element's is_closed attribute to True, and return an
    # element-has-been-closed value.
    element_to_close.is_closed = True
    return (ElementHasBeenClosedGSM(element_to_close.title),)
