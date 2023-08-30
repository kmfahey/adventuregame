#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage


__all__ = (
    "ElementNotLockpickable",
    "TargetHasBeenUnlocked",
    "TargetNotFound",
    "TargetNotLocked",
)


class ElementNotLockpickableGSM(GameStateMessage):
    """
    Returned by pick_lock_command() when the player attempts to pick a lock
    on a corpse, creature, doorway or item.
    """

    __slots__ = "target_title", "target_type"

    @property
    def message(self):
        # This message conveys that a corpse, creature, door or item
        # isn't unlockable, handling armor separately so 'suits of
        # [armor title]' can be used.
        if self.target_type == "armor":
            return (
                f"You can't pick a lock on the {self.target_title}; suits of "
                + f"{self.target_type} are not unlockable."
            )
        else:
            return (
                f"You can't pick a lock on the {self.target_title}; "
                + f"{self.target_type}s are not unlockable."
            )

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class TargetHasBeenUnlockedGSM(GameStateMessage):
    """
    Returned by pick_lock_command() when the player successfully unlocks the
    chest or door.
    """

    __slots__ = ("target_title",)

    @property
    def message(self):
        return f"You have unlocked the {self.target_title}."

    def __init__(self, target_title):
        self.target_title = target_title


class TargetNotFoundGSM(GameStateMessage):
    """
    Returned by pick_lock_command() when the player targets a door or chest
    that is not present in the current dungeon room.
    """

    __slots__ = ("target_title",)

    @property
    def message(self):
        return f"This room has no {self.target_title}."

    def __init__(self, target_title):
        self.target_title = target_title


class TargetNotLockedGSM(GameStateMessage):
    """
    Returned by pick_lock_command() when the player targets a door or chest
    that is not locked.
    """

    __slots__ = ("target_title",)

    @property
    def message(self):
        return f"The {self.target_title} is not locked."

    def __init__(self, target_title):
        self.target_title = target_title
