#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage


__all__ = (
    "AttackedAndHitGSM",
    "AttackedAndNotHitGSM",
    "CharacterDeathGSM",
)


class AttackedAndHitGSM(GameStateMessage):
    """
    Returned by _be_attacked_by_command() when the foe's counterattack
    connects. It conveys the damage done and how many hit points the
    player's character has left.
    """

    __slots__ = "creature_title", "damage_done", "hit_points_left"

    @property
    def message(self):
        # This message property informs the player of the effect of a
        # creature's attack on their hit points.
        return (
            f"The {self.creature_title} attacks! Their attack hits. They did "
            + f"{self.damage_done} damage! You have {self.hit_points_left} hit "
            + "points left."
        )

    def __init__(self, creature_title, damage_done, hit_points_left):
        self.creature_title = creature_title
        self.damage_done = damage_done
        self.hit_points_left = hit_points_left


class AttackedAndNotHitGSM(GameStateMessage):
    """
    Returned by _be_attacked_by_command() when the foe's counterattack did
    not connect.
    """

    __slots__ = ("creature_title",)

    @property
    def message(self):
        return f"The {self.creature_title} attacks! Their attack misses."

    def __init__(self, creature_title):
        self.creature_title = creature_title


class CharacterDeathGSM(GameStateMessage):
    """
    Returned by _be_attacked_by_command() when the foe's counter attack
    killed the player's character. The game is now over, and advgame.py
    responds to receiving this object by printing its message and then
    exiting the program.
    """

    @property
    def message(self):
        return "You have died!"

    def __init__(self):
        pass
