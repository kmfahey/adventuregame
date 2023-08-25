#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("DontPossessCorrectKey", "ElementNotLockable",
           "ElementHasBeenLocked", "ElementIsAlreadyLocked",
           "ElementToLockNotHere")


class DontPossessCorrectKey(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.unlock_command() when the
player tries to unlock a door while not possessing the door key, or
unlock a chest while not possessing the chest key.
    """

    __slots__ = 'object_to_unlock_title', 'key_needed',

    @property
    def message(self):
        return f'To unlock the {self.object_to_unlock_title} you need a {self.key_needed}.'

    def __init__(self, object_to_unlock_title, key_needed):
        self.object_to_unlock_title = object_to_unlock_title
        self.key_needed = key_needed


class ElementNotLockable(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.unlock_command() when the
player attempts to unlock a corpse, creature, doorway or item.
    """

    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        singular_item = (f'the suit of {self.target_title}' if self.target_type == 'armor'
                         else f'the {self.target_title}')
        item_pluralized = f'suits of {self.target_type}' if self.target_type == 'armor' else f'{self.target_type}s'
        return f"You can't unlock {singular_item}; {item_pluralized} are not unlockable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class ElementHasBeenLocked(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.unlock_command() when the
player successfully unlocks a chest or door.
    """

    __slots__ = 'target',

    @property
    def message(self):
        return f'You have unlocked the {self.target}.'

    def __init__(self, target):
        self.target = target


class ElementIsAlreadyLocked(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.unlock_command() when the
player tries to unlock a door or chest that is already unlocked.
    """

    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already unlocked.'

    def __init__(self, target):
        self.target = target


class ElementToLockNotHere(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.unlock_command() when
the player tries to unlock a door or chest that is not present in the
current dungeon room.
    """

    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to unlock.'

    def __init__(self, target_title):
        self.target_title = target_title
