#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage


__all__ = (
    "GameBeginsGSM",
    "NameOrClassNotSetGSM",
)


class GameBeginsGSM(GameStateMessage):
    """
    Returned by begin_game_command() when the command executes successfully.
    The game has begun.
    """

    @property
    def message(self):
        return "The game has begun!"

    def __init__(self):
        pass


class NameOrClassNotSetGSM(GameStateMessage):
    """
    Returned by begin_game_command() when the player has used the BEGIN GAME
    command prematurely. The player must set a name and a class before the
    game can begin; this object is returned if they fail to.
    """

    __slots__ = "character_name", "character_class"

    @property
    def message(self):
        # This message property covers three cases:
        #
        # The player needs to use both the SET NAME and the SET CLASS
        # commands before proceeding.
        if not self.character_name and not self.character_class:
            return (
                "You need to set your character name and class before you "
                + "begin the game. Use SET NAME <name> to set your name and "
                + "SET CLASS <Warrior, Thief, Mage or Priest> to select your "
                + "class."
            )
        # The player needs to use the SET NAME command before
        # proceeding.
        elif not self.character_name:
            return (
                "You need to set your character name before you begin the "
                + "game. Use SET NAME <name> to set your name."
            )
        # The player needs to use the SET CLASS command before
        # proceeding.
        else:
            return (
                "You need to set your character class before you begin the "
                + "game. Use SET CLASS <Warrior, Thief, Mage or Priest> to "
                + "select your class."
            )

    def __init__(self, character_name, character_class):
        self.character_name = character_name
        self.character_class = character_class
