#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("ElementNotOpenable", "ElementHasBeenOpened",
           "ElementIsAlreadyOpen", "ElementIsLocked", "ElementToOpenNotHere")


class ElementNotOpenable(GameStateMessage):
    """
This class implements an object that is returned by
advgame.processor.Command_Processor.open_command() when the player
attempts to open a corpse, creature, doorway or item.
    """
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        # This message conveys that a corpse, creature, door or item isn't
        # openable, handling armor separately so 'suits of [armor title]' can
        # be used.
        if self.target_type == 'armor':
            return f"You can't open the {self.target_title}; suits of {self.target_type} are not openable."
        else:
            return f"You can't open the {self.target_title}; {self.target_type}s are not openable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class ElementHasBeenOpened(GameStateMessage):
    """
This class implements an object that is returned by
advgame.processor.Command_Processor.open_command() when the player
successfully opens a chest or door.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'You have opened the {self.target}.'

    def __init__(self, target):
        self.target = target


class ElementIsAlreadyOpen(GameStateMessage):
    """
This class implements an object that is returned by
advgame.processor.Command_Processor.open_command() when the player targets
a door or chest that is already open.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already open.'

    def __init__(self, target):
        self.target = target


class ElementIsLocked(GameStateMessage):
    """
This class implements an object that is returned by
advgame.processor.Command_Processor.open_command() when the player targets
a door or chest that is locked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is locked.'

    def __init__(self, target):
        self.target = target


class ElementToOpenNotHere(GameStateMessage):
    """
This class implements an object that is returned by
advgame.processor.Command_Processor.open_command() when the player targets
a door or chest that is not present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to open.'

    def __init__(self, target_title):
        self.target_title = target_title

