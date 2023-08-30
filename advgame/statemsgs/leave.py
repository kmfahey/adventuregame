#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage


__all__ = ("DoorIsLockedGSM", "LeftRoomGSM", "WonTheGameGSM")


class DoorIsLockedGSM(GameStateMessage):
    """
    Returned by leave_command() if the player tries to leave through a door
    that is locked.
    """

    __slots__ = "compass_dir", "portal_type"

    @property
    def message(self):
        return (
            f"You can't leave the room via the {self.compass_dir} "
            + f"{self.portal_type}. The {self.portal_type} is locked."
        )

    def __init__(self, compass_dir, portal_type):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class LeftRoomGSM(GameStateMessage):
    """
    Returned by leave_command() when the player uses it to leave the current
    dungeon room.
    """

    __slots__ = "compass_dir", "portal_type"

    @property
    def message(self):
        return f"You leave the room via the {self.compass_dir} {self.portal_type}."

    def __init__(self, compass_dir, portal_type):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class WonTheGameGSM(GameStateMessage):
    """
    Returned by leave_command() when the player chances upon the door that
    is the exit to the dungeon. They have won the game; when advgame.py
    receives this game state message it prints its message and then exits
    the program.
    """

    __slots__ = ()

    @property
    def message(self):
        return "You found the exit to the dungeon. You have won the game!"

    def __init__(self):
        pass
