#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage


__all__ = ("HaveQuitTheGameGSM",)


class HaveQuitTheGameGSM(GameStateMessage):
    """
    Returned by quit_command() when the player executes the command. When
    advgame.py receives this object, it prints the message and then exits
    the program.
    """

    __slots__ = ()

    @property
    def message(self):
        return "You have quit the game."

    def __init__(self):
        pass
