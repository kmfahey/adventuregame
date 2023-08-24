#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("AttackHit", "AttackMissed", "OpponentNotFound",
           "YouHaveNoWeaponOrWandEquipped",)


class AttackHit(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.attack_command() when
the player's attack connected with their foe. attack_command() always
triggers the hidden _be_attacked_by_command() pseudo-command, an
.stmsg.attack.AttackHit object tracks if the foe was slain. If so,
nothing relating to foe death is conveyed; describing foe death is
handled by the .stmsg.various.FoeDeath class. If not, its message
includes a clause about the foe turning to attack.
    """
    __slots__ = 'creature_title', 'damage_done', 'creature_slain'

    @property
    def message(self):
        # This message property returns a message announcing the result of a
        # successful attack on a creature in one of four cases:
        #
        # The attack was with a weapon and the creature died.
        if self.creature_slain and self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage.'
        # The attack was with a wand and the creature died.
        elif self.creature_slain and self.weapon_type == 'wand':
            return (f'A bolt of energy from your wand hits the {self.creature_title}! You did {self.damage_done} '
                    f'damage. The {self.creature_title} turns to attack!')
        # The attack was with a weapon, the creature didn't die, and they're
        # counterattacking.
        elif not self.creature_slain and self.weapon_type == 'weapon':
            return (f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage. The '
                    f'{self.creature_title} turns to attack!')
        # The attack was with a wand, the creature didn't die, and they're
        # counterattacking.
        else:
            return (f'A bolt of energy from your wand hits the {self.creature_title}! You did {self.damage_done} '
                    f'damage. The {self.creature_title} turns to attack!')

    def __init__(self, creature_title, damage_done, creature_slain, weapon_type):
        self.creature_title = creature_title
        self.damage_done = damage_done
        self.creature_slain = creature_slain
        self.weapon_type = weapon_type


class AttackMissed(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.attack_command() when the
player's attack missed. Like .stmsg.attack.AttackHit, it mentions the
foe turning to attack, because an attack on a foe always leads to a
counterattack if they live.
    """
    __slots__ = 'creature_title', 'weapon_type'

    @property
    def message(self):
        # This message property returns a message announcing the result of a
        # failed attack on a creature in one of two cases:
        #
        # The attack was with a weapon, and the creature is counterattacking.
        if self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} missed. It turns to attack!'
        # The attack was with a wand, and the creature is counterattacking.
        else:
            return f'A bolt of energy from your wand misses the {self.creature_title}. It turns to attack!'

    def __init__(self, creature_title, weapon_type):
        self.creature_title = creature_title
        self.weapon_type = weapon_type


class OpponentNotFound(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.attack_command() when
the player has used an attack command that refers to a foe that is not
present in the game's current room.
    """
    __slots__ = 'creature_title_given', 'opponent_present'

    @property
    def message(self):
        # This message property handles two cases:
        #
        # There is a creature in the room by a different title and they can be
        # suggested as a better target.
        if self.opponent_present:
            return f"This room doesn't have a {self.creature_title_given}; but there is a {self.opponent_present}."
        # There is no creature in this room.
        else:
            return f"This room doesn't have a {self.creature_title_given}; nobody is here."

    def __init__(self, creature_title_given, opponent_present=''):
        self.creature_title_given = creature_title_given
        self.opponent_present = opponent_present


class YouHaveNoWeaponOrWandEquipped(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.attack_method() when the
player has used the attack command while having no weapon (or, for
Mages, no wand) equipped. It tracks player class so it knows to display
the wand option for Mages.
    """
    __slots__ = 'character_class',

    @property
    def message(self):
        # This message property handles two cases:
        #
        # The player's character is a Mage and has neither a wand or a weapon
        # equipped.
        if self.character_class == 'Mage':
            return "You have no wand or weapon equipped; you can't attack."
        # The player's character is a Warrior, Thief or Priest and has no
        # weapon equipped.
        else:
            return "You have no weapon equipped; you can't attack."

    def __init__(self, character_class):
        self.character_class = character_class
