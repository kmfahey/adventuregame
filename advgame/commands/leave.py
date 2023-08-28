#!/usr/bin/python3

from advgame import stmsg as stmsg

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.commands.utils import _door_selector


__all__ = ("leave_command",)


def leave_command(context, tokens):
    """
    Execute the LEAVE command. The return value is always in a tuple even
    when it's of length 1. The LEAVE command has the following usage:

    LEAVE [USING or VIA] <compass direction> DOOR
    LEAVE [USING or VIA] <compass direction> DOORWAY
    LEAVE [USING or VIA] <door name>
    LEAVE [USING or VIA] <compass direction> <door name>

    * If that syntax is not followed, returns a .stmsg.command.BadSyntaxGSM
    object.

    * If the door by that name is not present in the room, returns a
    .stmsg.various.DoorNotPresentGSM object.

    * If the door specifier is ambiguous and matches more than one door in
    the room, returns a .stmsg.various.AmbiguousDoorSpecifierGSM object.

    * If the door is the exit to the dungeon, returns a
    .stmsg.leave.LeftRoomGSM object and a .stmsg.leave.WonTheGameGSM object.

    * Otherwise, a .stmsg.leave.LeftRoomGSM object and a
    .stmsg.various.EnteredRoomGSM object are returned.
    """
    game_state = context.game_state

    # This method takes arguments of a specific form; if the
    # arguments don't match it, a syntax error is returned.
    if (
        not len(tokens)
        or not 2 <= len(tokens) <= 4
        or tokens[-1] not in ("door", "doorway")
    ):
        return (stmsg.command.BadSyntaxGSM("LEAVE", COMMANDS_SYNTAX["LEAVE"]),)

    # The format for specifying doors is flexible, and is
    # implemented by a private workhorse method.
    result = _door_selector(game_state, tokens)

    # Like all workhorse methods, it may return an error. result[0]
    # is type-tested if it inherits from GameStateMessage. If it
    # matches, the result tuple is returned.
    if isinstance(result[0], stmsg.GameStateMessage):
        return result
    else:
        # Otherwise, the matching Door object is extracted from
        # result.
        (door,) = result

    # The compass direction door type are extracted from the Door
    # object.
    compass_dir = door.title.split(" ")[0]
    portal_type = door.door_type.split("_")[-1]

    # If the door is locked, a door-is-locked error is returned.
    if door.is_locked:
        return (stmsg.leave.DoorIsLockedGSM(compass_dir, portal_type),)

    # The exit to the dungeon is a special Door object marked with
    # is_exit=True. I test the Door object to see if this is the
    # one.
    if door.is_exit:

        # If so, a left-room value will be returned along with a
        # won-the-game value.
        return_tuple = (
            stmsg.leave.LeftRoomGSM(compass_dir, portal_type),
            stmsg.leave.WonTheGameGSM(),
        )

        # The game_has_ended boolean is set True, and the
        # game-ending return value is saved so that process()
        # can return it if the frontend accidentally tries to submit
        # another command.
        game_state.game_has_ended = True
        context.game_ending_state_msg = return_tuple[-1]
        return return_tuple

    # Otherwise, RoomsState.move is called with the compass
    # direction, and a left-room value is returned along with a
    # entered-room value.
    game_state.rooms_state.move(**{compass_dir: True})
    return (
        stmsg.leave.LeftRoomGSM(compass_dir, portal_type),
        stmsg.various.EnteredRoomGSM(game_state.rooms_state.cursor),
    )
