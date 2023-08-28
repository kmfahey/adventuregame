#!/usr/bin/python3

from advgame.utils import roll_dice

from advgame.commands.be_atkd import be_attacked_by_command
from advgame.commands.constants import COMMANDS_SYNTAX, SPELL_DAMAGE, SPELL_MANA_COST
from advgame.stmsg.castspl import (
    CastDamagingSpellGSM,
    CastHealingSpellGSM,
    InsufficientManaGSM,
    NoCreatureToTargetGSM,
)
from advgame.stmsg.command import BadSyntaxGSM, ClassRestrictedGSM
from advgame.stmsg.various import FoeDeathGSM, UnderwentHealingEffectGSM


__all__ = ("cast_spell_command",)


def cast_spell_command(context, tokens):
    """
    Execute the CAST SPELL command. The return value is always in a tuple
    even when it's of length 1. Takes no arguments.

    * If any arguments are given, returns a BadSyntaxGSM object.

    * If the character is a Warrior or a Thief, returns a
    ClassRestrictedGSM object.

    * This command costs mana points. If the character doesn't have enough,
    returns a InsufficientManaGSM object.

    * If the character is a Mage and there's no creature in the room,
    returns a NoCreatureToTargetGSM object.

    * If they're a Mage and there is a creature present, a damaging spell
    is cast and the creature is wounded. If they don't die, returns a
    CastDamagingSpellGSM object followed by the object(s)
    generated by the creature's followup attack.

    * If the creature is killed, returns a CastDamagingSpellGSM
    object and a FoeDeathGSM object.

    * If the character is a Priest, returns a
    CastHealingSpellGSM object and a
    UnderwentHealingEffectGSM object."""
    game_state = context.game_state

    # The first error check detects if the player has used this
    # command while playing a Warrior or Thief. Those classes can't
    # cast spells, so a command-class-restricted error is returned.
    if game_state.character_class not in ("Mage", "Priest"):
        return (ClassRestrictedGSM("CAST SPELL", "mage", "priest"),)

    # This command takes no arguments, so if any were used a syntax
    # error is returned.
    elif len(tokens):
        return (BadSyntaxGSM("CAST SPELL", COMMANDS_SYNTAX["CAST SPELL"]),)

    # If the player character's mana is less than SPELL_MANA_COST,
    # an insufficient-mana error is returned.
    elif game_state.character.mana_points < SPELL_MANA_COST:
        return (
            InsufficientManaGSM(
                game_state.character.mana_points,
                game_state.character.mana_point_total,
                SPELL_MANA_COST,
            ),
        )

    # The initial error handling is concluded, so now the execution
    # handles the Mage and Priest cases separately.
    elif game_state.character_class == "Mage":

        # If the current room has no creature in it, a
        # no-creature-to-target error is returned.
        if game_state.rooms_state.cursor.creature_here is None:
            return (NoCreatureToTargetGSM(),)
        else:
            # Otherwise, spell damage is rolled and inflicted on
            # creature_here. The spell always hits (it's styled
            # after _magic missile_, a classic D&D spell that always
            # hits its target.
            damage_dealt = roll_dice(SPELL_DAMAGE)
            creature = game_state.rooms_state.cursor.creature_here
            damage_dealt = creature.take_damage(damage_dealt)
            game_state.character.spend_mana(SPELL_MANA_COST)

            # If the creature died, a cast-damaging-spell value and
            # a foe-death value are returned.
            if creature.is_dead:
                corpse = creature.convert_to_corpse()
                game_state.rooms_state.cursor.container_here = corpse
                game_state.rooms_state.cursor.creature_here = None
                return (
                    CastDamagingSpellGSM(
                        creature.title, damage_dealt, creature_slain=True
                    ),
                    FoeDeathGSM(creature.title),
                )
            else:
                # Otherwise, like ATTACK, using this command and
                # not killing your foe means they counterattack.
                # cast-damaging-spell is conjoined with the outcome
                # of _be_attacked_by_command() and the total
                # tuple is returned.
                be_attacked_by_result = be_attacked_by_command(context, creature)
                return (
                    CastDamagingSpellGSM(
                        creature.title, damage_dealt, creature_slain=False
                    ),
                ) + be_attacked_by_result
    else:
        # The Mage's spell is a damaging spell, but the Priest's
        # spell is a self-heal. The same SPELL_DAMAGE dice are used.
        # The healing is rolled and applied to the Character object.
        # A cast-healing-spell value and a underwent-healing-effect
        # value are returned.
        damage_rolled = roll_dice(SPELL_DAMAGE)
        healed_amt = game_state.character.heal_damage(damage_rolled)
        game_state.character.spend_mana(SPELL_MANA_COST)
        return (
            CastHealingSpellGSM(),
            UnderwentHealingEffectGSM(
                healed_amt,
                game_state.character.hit_points,
                game_state.character.hit_point_total,
            ),
        )
