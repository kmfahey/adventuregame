#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("ElementNotCloseable", "ElementHasBeenClosed",
           "ElementIsAlreadyClosed", "ElementToCloseNotHere",)


class ElementNotCloseable(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.close_command() when the player
attempts to close a corpse, creature, doorway or item.
    """
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        if self.target_type == 'armor':
            return f"You can't close the {self.target_title}; suits of {self.target_type} are not closable."
        else:
            return f"You can't close the {self.target_title}; {self.target_type}s are not closable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class ElementHasBeenClosed(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.close_command() when the player
succeeds in closing a door or chest.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'You have closed the {self.target}.'

    def __init__(self, target):
        self.target = target


class ElementIsAlreadyClosed(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.close_command() when the closable
object the player targeted is already closed.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already closed.'

    def __init__(self, target):
        self.target = target


class ElementToCloseNotHere(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.close_command() when the player
specifies a target to the command that is not present in the current room of the
game.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to close.'

    def __init__(self, target_title):
        self.target_title = target_title

