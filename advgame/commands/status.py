#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.status import StatusOutputGSM


__all__ = ("status_command",)


def status_command(game_state, tokens):
    """
    Execute the STATUS command. The return value is always in a tuple even
    when it's of length 1. The STATUS command takes no arguments.

    * If the command is used with any arguments, returns a
    BadSyntaxGSM object.

    * Otherwise, returns a StatusOutputGSM object.
    """
    # This command takes no arguments so if any were supplied I
    # return a syntax error.
    if len(tokens):
        return (BadSyntaxGSM("STATUS", COMMANDS_SYNTAX["STATUS"]),)

    # A lot of data goes into a status command so I build the argd
    # to Stmsg_Status_StatusOutput key by key.
    character = game_state.character
    status_gsm_argd = dict()
    status_gsm_argd["hit_points"] = character.hit_points
    status_gsm_argd["hit_point_total"] = character.hit_point_total

    # Mana points are only part of a status line if the player
    # character is a Mage or Priest.
    if character.character_class in ("Mage", "Priest"):
        status_gsm_argd["mana_points"] = character.mana_points
        status_gsm_argd["mana_point_total"] = character.mana_point_total
    else:
        status_gsm_argd["mana_points"] = None
        status_gsm_argd["mana_point_total"] = None

    status_gsm_argd["armor_class"] = character.armor_class

    # attack_bonus and damage are only set if a weapon is
    # equipped... or if the player character is a Mage and a wand is
    # equipped.
    if character.weapon_equipped or (
        character.character_class == "Mage" and character.wand_equipped
    ):
        status_gsm_argd["attack_bonus"] = character.attack_bonus
        status_gsm_argd["damage"] = character.damage_roll
    else:
        status_gsm_argd["attack_bonus"] = 0
        status_gsm_argd["damage"] = ""

    # The status line can display the currently equipped armor,
    # shield, weapon and wand, and if an item isn't equipped
    # in a given slot it can display 'none'; but it only shows
    # '<Equipment>: none' if that equipment type is one the player
    # character's class can use. So I use class-tests to determine
    # whether to add each equipment-type argument.
    if character.character_class != "Mage":
        status_gsm_argd["armor"] = (
            character.armor.title if character.armor_equipped else None
        )
    if character.character_class not in ("Thief", "Mage"):
        status_gsm_argd["shield"] = (
            character.shield.title if character.shield_equipped else None
        )
    if character.character_class == "Mage":
        status_gsm_argd["wand"] = (
            character.wand.title if character.wand_equipped else None
        )

    status_gsm_argd["weapon"] = (
        character.weapon.title if character.weapon_equipped else None
    )
    status_gsm_argd["character_class"] = character.character_class

    # The entire argd has been assembled so I return a status-ouput
    # value.
    return (StatusOutputGSM(**status_gsm_argd),)
