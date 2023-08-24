#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("DontPossessCorrectKey", "ElementNotUnlockable",
           "ElementHasBeenUnlocked", "ElementIsAlreadyUnlocked",
           "ElementToUnlockNotHere")


class DontPossessCorrectKey(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.lock_command() when the player tries
to lock a chest while they don't possess the chest key, or a door while they
don't possess the door key.
    """
    __slots__ = 'object_to_lock_title', 'key_needed',

    @property
    def message(self):
        return f'To lock the {self.object_to_lock_title} you need a {self.key_needed}.'

    def __init__(self, object_to_lock_title, key_needed):
        self.object_to_lock_title = object_to_lock_title
        self.key_needed = key_needed


class ElementNotUnlockable(GameStateMessage):
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        # This message property returns a string that informs the player that
        # they tried to lock something that can't be locked (a corpse, creature,
        # doorway or item). It omits the direct article is the item is armor.
        if self.target_type == 'armor':
            return f"You can't lock the {self.target_title}; suits of {self.target_type} are not lockable."
        else:
            return f"You can't lock the {self.target_title}; {self.target_type}s are not lockable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class ElementHasBeenUnlocked(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.lock_command() when the player
successfully locks a chest or door.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'You have locked the {self.target}.'

    def __init__(self, target):
        self.target = target


class ElementIsAlreadyUnlocked(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.lock_command() when the player tries
to lock a chest or door that is already locked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already locked.'

    def __init__(self, target):
        self.target = target


class ElementToUnlockNotHere(GameStateMessage):
    """
This class implements an object that is returned by
advgame.process.Command_Processor.lock_command() when the player
specifies an object to lock that is not present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to lock.'

    def __init__(self, target_title):
        self.target_title = target_title

