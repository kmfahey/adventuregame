#!/usr/bin/python3

from advgame.utils import roll_dice
from advgame.stmsg.be_atkd import (
    AttackedAndHitGSM,
    AttackedAndNotHitGSM,
    CharacterDeathGSM,
)


__all__ = ("be_attacked_by_command",)


def be_attacked_by_command(context, creature):
    # Called when a attack_command() execution included a
    # successful attack but didn't end in foe death. This is a
    # pseudo-command-method that can only be called internally. An
    # attack by the foe creature is calculated, if it hits damage is
    # assessed on the player character, and if character.is_dead becomes
    # True, the game ends.
    #
    # :creature: The foe creature that was targeted by attack_command().
    game_state = context.game_state

    # The attack is calculated.
    attack_roll_dice_expr = creature.attack_roll
    damage_roll_dice_expr = creature.damage_roll
    attack_result = roll_dice(attack_roll_dice_expr)

    # If the attack roll didn't meet or exceed the player character's
    # armor class, an attacked-and-not-hit value is returned.
    if attack_result < game_state.character.armor_class:
        return (AttackedAndNotHitGSM(creature.title),)
    else:
        # attack_result >= game_state.character.armor_class

        # The attack hit, so damage is rolled and inflicted.
        damage_done = roll_dice(damage_roll_dice_expr)
        game_state.character.take_damage(damage_done)
        if game_state.character.is_dead:
            # The attack killed the player character, so an
            # attacked-and-hit value and a character-death value are
            # returned. Game over, it's that easy. Combat comes with
            # risk.
            return_tuple = (
                AttackedAndHitGSM(creature.title, damage_done, 0),
                CharacterDeathGSM(),
            )

            # The game_has_ended boolean is set True, and the
            # game-ending return value is saved so that process() can
            # return it if the frontend accidentally tries to submit
            # another command.
            game_state.game_has_ended = True
            context.game_ending_state_msg = return_tuple[-1]
            return return_tuple
        else:
            # game_state.character.is_alive == True

            # The player character survived, so just an attacked-and-hit
            # value is returned.
            return (
                AttackedAndHitGSM(
                    creature.title, damage_done, game_state.character.hit_points
                ),
            )
