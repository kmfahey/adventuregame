#!/usr/bin/python3

from advgame.utils import roll_dice

from advgame.commands.be_atkd import be_attacked_by_command
from advgame.commands.constants import COMMANDS_SYNTAX

from advgame.stmsg.attack import (
    AttackHitGSM,
    AttackMissedGSM,
    OpponentNotFoundGSM,
    YouHaveNoWeaponOrWandEquippedGSM,
)
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.various import FoeDeathGSM


__all__ = ("attack_command",)


def attack_command(context, tokens):
    """
    Execute the ATTACK command. The return value is always in a tuple even
    when it's of length 1. The ATTACK command has the following usage:

    ATTACK <creature name>

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If .character has no weapon (or, for Mages, wand) equipped,
    returns a YouHaveNoWeaponOrWandEquippedGSM object.

    * If there's no creature by the given name in the room, returns a
    OpponentNotFoundGSM object.

    * If the attack misses, returns a AttackMissedGSM object
    followed by the object(s) generated by the creature's followup attack.

    * If the attack hits but doesn't kill the foe, returns an
    AttackHitGSM object followed by the object(s) generated by
    the creature's followup attack.

    * If the attack hits and kills the foe, a AttackHitGSM
    object and a FoeDeathGSM object are returned.
    """
    game_state = context.game_state
    # If the player character has no weapon or wand equipped, an error
    # is returned right away.
    if not game_state.character.weapon_equipped and (
        game_state.character_class != "Mage" or not game_state.character.wand_equipped
    ):
        return (YouHaveNoWeaponOrWandEquippedGSM(game_state.character_class),)

    # Using this command with no argument is a syntax error.
    elif not tokens:
        return (BadSyntaxGSM("ATTACK", COMMANDS_SYNTAX["ATTACK"]),)

    # This var is used by some return values.
    weapon_type = "wand" if game_state.character.wand_equipped else "weapon"
    creature_title = " ".join(tokens)

    # If there's no creature in the current room, an error is returned.
    if not game_state.rooms_state.cursor.creature_here:
        return (OpponentNotFoundGSM(creature_title),)
    # If the arguments don't match the title of the creature in the
    # current room, an error is returned.
    elif game_state.rooms_state.cursor.creature_here.title.lower() != creature_title:
        return (
            OpponentNotFoundGSM(
                creature_title, game_state.rooms_state.cursor.creature_here.title
            ),
        )

    # All possible errors have been handles, so the actual attack is
    # figured on the creature here.
    creature = game_state.rooms_state.cursor.creature_here
    attack_roll_dice_expr = game_state.character.attack_roll
    damage_roll_dice_expr = game_state.character.damage_roll
    attack_result = roll_dice(attack_roll_dice_expr)

    # The attack doesn't meet or exceed the creature's armor class.
    if attack_result < creature.armor_class:

        # So a attack-missed return value is prepared.
        attack_missed_result = AttackMissedGSM(creature.title, weapon_type)

        # The be_attacked_by_command() pseudo-command is triggered by
        # any attack command that doesn't kill the creature. Its tuple
        # of return values is appended to the attack-missed return value
        # and the combined tuple is returned.
        #
        # Please note that it's possible for be_attacked_by_command()
        # to end in Stmsg_Batkby_CharacterDeath; the game might end
        # right here.
        be_attacked_by_result = be_attacked_by_command(context, creature)
        return (attack_missed_result,) + be_attacked_by_result
    else:
        # attack_result >= creature.armor_class

        # The attack roll met or exceeded the creature's armor class, so
        # damage is assessed and inflicted on the creature.
        damage_result = roll_dice(damage_roll_dice_expr)
        damage_result = creature.take_damage(damage_result)

        # If the creature was killed by that damage, the
        # Creature.convert_to_corpse() method is used to instantiate
        # a Corpse object from its data, that object is stored to
        # the room's container_here attribute, and its creature_here
        # attribute is set to None. Corpse is a Container, so the player
        # can use TAKE to loot the corpse.
        if creature.is_dead:
            corpse = creature.convert_to_corpse()
            game_state.rooms_state.cursor.container_here = corpse
            game_state.rooms_state.cursor.creature_here = None

            # The return tuple is comprised of an attack-hit value and a
            # foe-death value.
            return (
                AttackHitGSM(creature.title, damage_result, True, weapon_type),
                FoeDeathGSM(creature.title),
            )
        else:
            # creature.is_alive == True

            # The attack hit but didn't kill, so the return tuple
            # begins with an attack-hit value. The creature lived, so
            # be_attacked_by_command() is called and its return tuple
            # is appended and the entire sequence is returned. Again,
            # the counterattack might kill the player character, so the
            # game might end right here.
            attack_hit_result = AttackHitGSM(
                creature.title, damage_result, False, weapon_type
            )
            be_attacked_by_result = be_attacked_by_command(context, creature)
            return (attack_hit_result,) + be_attacked_by_result
