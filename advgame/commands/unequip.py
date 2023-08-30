#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.unequip import ItemNotEquippedGSM
from advgame.statemsgs.various import ItemUnequippedGSM


__all__ = ("unequip_command",)


def unequip_command(game_state, tokens):
    """
    Execute the UNEQUIP command. The return value is always in a tuple even
    when it's of length 1. The UNEQUIP command has the following usage:

    UNEQUIP <armor name>
    UNEQUIP <shield name>
    UNEQUIP <wand name>
    UNEQUIP <weapon name>

    * If that syntax is not followed, returns a BadSyntaxGSM object.

    * If the character does not have the item equipped, returns a
    ItemNotEquippedGSM object.

    * Otherwise, the specified item is unequipped, and a ItemUnequippedGSM
    is returned.
    """
    # This command requires an argument so if none was supplied I
    # return a syntax error.
    if not tokens:
        return (BadSyntaxGSM("UNEQUIP", COMMANDS_SYNTAX["UNEQUIP"]),)

    # I construct the item title and search for it in the player
    # character's inventory.
    item_title = " ".join(tokens)
    matching_item_tuple = tuple(
        item
        for _, item in game_state.character.list_items()
        if item.title == item_title
    )

    # If the item isn't found in the player character's inventory,
    # I search for it in the items_state just to get the item_type;
    # I return an item-not-equipped error informed by the found
    # item_type if possible.
    if not len(matching_item_tuple):
        matching_item_tuple = tuple(
            item for item in game_state.items_state.values() if item.title == item_title
        )
        if matching_item_tuple:
            (item,) = matching_item_tuple[0:1]
            return (ItemNotEquippedGSM(item.title, item.item_type),)
        else:
            return (ItemNotEquippedGSM(item_title),)

    # I extract the matched item.
    (item,) = matching_item_tuple[0:1]

    # This code is very repetitive but it can't easily be condensed
    # into a loop due to the special case handling in the weapon
    # section vis a vis wands, so I just deal with repetitive code.
    if item.item_type == "armor":
        if game_state.character.armor_equipped is None:
            # If I'm unequipping armor but the player character has
            # no armor equipped I return a item-not-equipped error.
            return (ItemNotEquippedGSM(item_title, "armor"),)
        else:
            if game_state.character.armor_equipped.title != item_title:
                # If armor_equipped's title doesn't match the
                # argument item_title, I return an item-not-equipped
                # error.
                return (
                    ItemNotEquippedGSM(
                        item_title,
                        "armor",
                        game_state.character.armor_equipped.title,
                    ),
                )
            else:
                # Otherwise, the title matches, so I unequip the
                # armor and return a item-unequipped value.
                game_state.character.unequip_armor()
                return (
                    ItemUnequippedGSM(
                        item_title,
                        "armor",
                        armor_class=game_state.character.armor_class,
                    ),
                )
    elif item.item_type == "shield":
        if game_state.character.shield_equipped is None:
            # If I'm unequipping a shield but the player character
            # has no shield equipped I return a item-not-equipped
            # error.
            return (ItemNotEquippedGSM(item_title, "shield"),)
        else:
            if game_state.character.shield_equipped.title != item_title:
                # If shield_equipped's title doesn't match the
                # argument item_title, I return an item-not-equipped
                # error.
                return (
                    ItemNotEquippedGSM(
                        item_title,
                        "shield",
                        game_state.character.shield_equipped.title,
                    ),
                )
            else:
                # Otherwise, the title matches, so I unequip the
                # shield and return a item-unequipped value.
                game_state.character.unequip_shield()
                return (
                    ItemUnequippedGSM(
                        item_title,
                        "shield",
                        armor_class=game_state.character.armor_class,
                    ),
                )
    elif item.item_type == "wand":
        if game_state.character.wand_equipped is None:
            # If I'm unequipping a wand but the player character has
            # no wand equipped I return a item-not-equipped error.
            return (ItemNotEquippedGSM(item_title, "wand"),)
        else:
            if game_state.character.wand_equipped.title != item_title:
                # If wand_equipped's title doesn't match the
                # argument item_title, I return an item-not-equipped
                # error.
                return (ItemNotEquippedGSM(item_title, "wand"),)
            else:
                # Otherwise, the title matches, so I unequip the
                # wand.
                game_state.character.unequip_wand()
                weapon_equipped = game_state.character.weapon_equipped
                # If a weapon is equipped, the player character will
                # still be able to attack with *that*, so I return
                # an item-unequipped value initialized with the
                # weapon's info.
                if weapon_equipped is not None:
                    return (
                        ItemUnequippedGSM(
                            item_title,
                            "wand",
                            attack_bonus=game_state.character.attack_bonus,
                            damage=game_state.character.damage_roll,
                            now_attacking_with=weapon_equipped,
                        ),
                    )
                else:
                    # Otherwise, I return an item-unequipped value
                    # with cant_attack set to True.
                    return (ItemUnequippedGSM(item_title, "wand", cant_attack=True),)
    elif item.item_type == "weapon":
        # If I'm unequipping a weapon but the player character has
        # no weapon equipped I return a item-not-equipped error.
        if game_state.character.weapon_equipped is None:
            return (ItemNotEquippedGSM(item.title, "weapon"),)
        else:
            if game_state.character.weapon_equipped.title != item_title:
                # If weapon_equipped's title doesn't match the
                # argument item_title, I return an item-not-equipped
                # error.
                return (ItemNotEquippedGSM(item.title, "weapon"),)
            else:
                # Otherwise, the title matches, so I unequip the
                # weapon.
                game_state.character.unequip_weapon()
                wand_equipped = game_state.character.wand_equipped
                # If the player character has a wand equipped,
                # they'll be attacking with that regardless of their
                # weapon, so I return an item-unequipped value
                # initialized with the wand's info.
                if wand_equipped is not None:
                    return (
                        ItemUnequippedGSM(
                            item_title,
                            "weapon",
                            attack_bonus=game_state.character.attack_bonus,
                            damage=game_state.character.damage_roll,
                            attacking_with=wand_equipped,
                        ),
                    )
                else:
                    # Otherwise I return an item-unequipped value
                    # with now_cant_attack set to True.
                    return (
                        ItemUnequippedGSM(item_title, "weapon", now_cant_attack=True),
                    )
