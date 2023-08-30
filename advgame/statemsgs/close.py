#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage


__all__ = (
    "ElementNotCloseableGSM",
    "ElementHasBeenClosedGSM",
    "ElementIsAlreadyClosedGSM",
    "ElementToCloseNotHereGSM",
)


class ElementNotCloseableGSM(GameStateMessage):
    """
    Returned by close_command() when the player attempts to close a corpse,
    creature, doorway or item.
    """

    __slots__ = "target_title", "target_type"

    @property
    def message(self):
        if self.target_type == "armor":
            return (
                f"You can't close the {self.target_title}; suits of "
                + f"{self.target_type} are not closeable."
            )
        else:
            return (
                f"You can't close the {self.target_title}; "
                + f"{self.target_type}s are not closeable."
            )

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class ElementHasBeenClosedGSM(GameStateMessage):
    """
    Returned by close_command() when the player succeeds in closing a door
    or chest.
    """

    __slots__ = ("target",)

    @property
    def message(self):
        return f"You have closed the {self.target}."

    def __init__(self, target):
        self.target = target


class ElementIsAlreadyClosedGSM(GameStateMessage):
    """
    Returned by close_command() when the closeable object the player
    targeted is already closed.
    """

    __slots__ = ("target",)

    @property
    def message(self):
        return f"The {self.target} is already closed."

    def __init__(self, target):
        self.target = target


class ElementToCloseNotHereGSM(GameStateMessage):
    """
    Returned by close_command() when the player specifies a target to the
    command that is not present in the current room of the game.
    """

    __slots__ = ("target_title",)

    @property
    def message(self):
        return f"You found no {self.target_title} here to close."

    def __init__(self, target_title):
        self.target_title = target_title
