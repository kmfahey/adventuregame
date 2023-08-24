#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("CastDamagingSpell", "CastHealingSpell", "InsufficientMana",
           "NoCreatureToTarget",)


class CastDamagingSpell(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.cast_spell_command() when
the player, while playing a Mage, has cast a damaging spell. Like
.stmsg.attack.AttackHit, it tracks whether the foe was slain, and adds a
'they turn to attack' sentence if not.
    """
    __slots__ = 'creature_title', 'damage_dealt'

    @property
    def message(self):
        # This message property handles two cases:
        #
        # The player character's spell killed their foe.
        if self.creature_slain:
            return (f'A magic missile springs from your gesturing hand and unerringly strikes the {self.creature_title}. '
                    f'You have done {self.damage_dealt} points of damage.')
        # The player character's spell didn't kill their foe, and, as with any
        # use of the ATTACK command, the creature is counterattacking.
        else:
            return (f'A magic missile springs from your gesturing hand and unerringly strikes the {self.creature_title}. '
                    f'You have done {self.damage_dealt} points of damage. The {self.creature_title} turns to attack!')

    def __init__(self, creature_title, damage_dealt, creature_slain):
        self.creature_title = creature_title
        self.damage_dealt = damage_dealt
        self.creature_slain = creature_slain


class CastHealingSpell(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.cast_spell_command() when
used by a Priest. It doesn't need to mention how much damage was healed
because it's followed by a Stmsg_Various_UnderwentHealingEffect instance
that does that.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You cast a healing spell on yourself.'

    def __init__(self):
        pass


class InsufficientMana(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.cast_spell_command() when
the player tries to cast a spell with insufficient mana points.
    """
    __slots__ = 'current_mana_points', 'mana_point_total', 'spell_mana_cost'

    @property
    def message(self):
        return ("You don't have enough mana points to cast a spell. Casting a spell costs "
                f'{self.spell_mana_cost} mana points. Your mana points are '
                f'{self.current_mana_points}/{self.mana_point_total}.')

    def __init__(self, current_mana_points, mana_point_total, spell_mana_cost):
        self.current_mana_points = current_mana_points
        self.mana_point_total = mana_point_total
        self.spell_mana_cost = spell_mana_cost


class NoCreatureToTarget(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.cast_spell_command() when
the player uses the command in a room with no creature to attack.
    """
    __slots__ = ()

    @property
    def message(self):
        return "You can't cast magic missile here; there is no creature here to target."

    def __init__(self):
        pass
