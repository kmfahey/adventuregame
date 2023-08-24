#!/usr/bin/python3


from adventuregame.statemsgs._common import GameStateMessage
from adventuregame.utility import join_str_seq_w_commas_and_conjunction, usage_verb


__all__ = ("ClassSet", "InvalidClass")


class ClassSet(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.set_class_command() when the player
selects a class from the choices Warrior, Thief, Mage and Priest.
    """
    __slots__ = 'class_str',

    @property
    def message(self):
        return f'Your class, {self.class_str}, has been set.'

    def __init__(self, class_str):
        self.class_str = class_str


class InvalidClass(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.set_class_command() when the player
specifies a class that is not one of Warrior, Thief, Mage or Priest.
    """
    __slots__ = 'bad_class',

    @property
    def message(self):
        return f"'{self.bad_class}' is not a valid class choice. Please choose Warrior, Thief, Mage, or Priest."

    def __init__(self, bad_class):
        self.bad_class = bad_class

