#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("NameOrClassNotSet",)


class NameOrClassNotSet(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.reroll_command() when the
player tries to use it before they have set their name and class. The
player's ability scores aren't rolled until they've chosen a name and
class, and therefore can't be rerolled yet.
    """
    __slots__ = 'character_name', 'character_class'

    @property
    def message(self):
        # This mesage property constructs a string that indicates which of the
        # two commands, SET NAME and SET CLASS, the player needs to use before
        # REROLL can be used.
        reroll_str = "Your character's stats haven't been rolled yet, so there's nothing to reroll."
        set_name_str = 'SET NAME <name> to set your name'
        set_class_str = 'SET CLASS <Warrior, Thief, Mage or Priest> to select your class'
        if self.character_name is None and self.character_class is None:
            return reroll_str + f' Use {set_name_str} and {set_class_str}.'
        elif self.character_class is None:
            return reroll_str + f' Use {set_class_str}.'
        else:
            return reroll_str + f' Use {set_name_str}.'

    def __init__(self, character_name, character_class):
        self.character_name = character_name
        self.character_class = character_class
