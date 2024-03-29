#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage


__all__ = ("ClassSetGSM", "InvalidClassGSM")


class ClassSetGSM(GameStateMessage):
    """
    Returned by set_class_command() when the player selects a class from the
    choices Warrior, Thief, Mage and Priest.
    """

    __slots__ = ("class_str",)

    @property
    def message(self):
        return f"Your class, {self.class_str}, has been set."

    def __init__(self, class_str):
        self.class_str = class_str


class InvalidClassGSM(GameStateMessage):
    """
    Returned by set_class_command() when the player specifies a class that
    is not one of Warrior, Thief, Mage or Priest.
    """

    __slots__ = ("bad_class",)

    @property
    def message(self):
        return (
            f"'{self.bad_class}' is not a valid class choice. Please choose "
            + "Warrior, Thief, Mage, or Priest."
        )

    def __init__(self, bad_class):
        self.bad_class = bad_class
