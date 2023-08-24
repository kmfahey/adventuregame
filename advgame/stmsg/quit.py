#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("HaveQuitTheGame",)


class HaveQuitTheGame(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.quit_command() when the player
executes the command. When advgame.py receives this object, it prints the
message and then exits the program.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You have quit the game.'

    def __init__(self):
        pass

