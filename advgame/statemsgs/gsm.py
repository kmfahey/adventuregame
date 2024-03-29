#!/usr/bin/python32

"""
Contains GameStateMessage, the abstract base calss for all game state
message classes in CommandProcessor.process() processes a natural
language command from the player and tail calls a command method of the
CommandProcessor object. It always returns a tuple of GameStateMessage
subclass objects; each one represents a single possible outcome of a
command. A GameStateMessage subclass has an __init__ method that assigns
keyword arguments to object attributes and a message property which
contains the logic for rendering the semantic value of the message
object in natural language.
"""

from abc import ABC, abstractmethod


class GameStateMessage(ABC):
    """
    This class is the abstract base class for all the game state message
    classes in this module. It defines an abstract property message and an
    abstract method __init__.
    """

    @property
    @abstractmethod
    def message(self):
        """
        The message property of a GameStateMessage subclass renders the data
        stored in the object attributes to a natural language string which
        communicates the semantic content of the object to the player. The
        message property is accessed and printed by advgame.py.
        """
        pass

    @abstractmethod
    def __init__(self, *argl, **argd):
        """
        The __init__ method of a GameStateMessage subclass stores its keyword
        arguments to object attributes, and performs no other task.
        """
        pass
