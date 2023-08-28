#!/usr/bin/python3

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.equip import ClassCantUseItemGSM, NoSuchItemInInventoryGSM
from advgame.stmsg.various import ItemEquippedGSM, ItemUnequippedGSM


__all__ = ("equip_command",)


def equip_command(game_state, tokens):
    """
    Execute the EQUIP command. The return value is always in a tuple even
    when it's of length 1. The EQUIP command has the following usage:

    EQUIP <armor name>
    EQUIP <shield name>
    EQUIP <wand name>
    EQUIP <weapon name>

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If the item isn't in inventory, returns a
    NoSuchItemInInventoryGSM object.

    * If the item can't be used by the character due to their class, returns
    a ClassCantUseItemGSM object.

    * If an item of the same kind is already equipped (for example trying
    to equip a suit of armor when the character is already wearing armor),
    that item is unequipped, the specified item is equipped, and a
    ItemUnequippedGSM object and a ItemEquippedGSM
    object are returned.

    * Otherwise, the item is equipped, and a ItemEquippedGSM
    object is returned.
    """
    # The equip command requires an argument; if none was given, a
    # syntax error is returned.
    if not tokens or len(tokens) == 1 and tokens[0] == "the":
        return (BadSyntaxGSM("EQUIP", COMMANDS_SYNTAX["EQUIP"]),)
    if tokens[0] == "the":
        tokens = tokens[1:]

    # The title of the item to equip is formed from the arguments.
    item_title = " ".join(tokens)

    # The inventory is filtered looking for an item with a matching
    # title.
    matching_item_tuple = tuple(
        item
        for _, item in game_state.character.list_items()
        if item.title == item_title
    )

    # If no such item is found in the inventory, a
    # no-such-item-in-inventory error is returned.
    if not len(matching_item_tuple):
        return (NoSuchItemInInventoryGSM(item_title),)

    # The Item subclass object was found and is saved.
    (item,) = matching_item_tuple[0:1]

    # I check that the item has a {class}_can_use = True attribute.
    # If not, a class-can't-use-item error is returned.
    can_use_attr = game_state.character_class.lower() + "_can_use"
    if not getattr(item, can_use_attr):
        return (
            ClassCantUseItemGSM(game_state.character_class, item_title, item.item_type),
        )

    # This conditional handles checking, for each type of equippable
    # item, whether the player character already has an item of that
    # type equipped; if so, it's unequipped, and a item-unequipped
    # return value is appended to the return values tuple.
    return_values = tuple()
    if item.item_type == "armor" and game_state.character.armor_equipped:
        # The player is trying to equip armor but is already wearing
        # armor, so their existing armor is unequipped.
        old_equipped = game_state.character.armor_equipped
        game_state.character.unequip_armor()
        return_values += (
            ItemUnequippedGSM(
                old_equipped.title,
                old_equipped.item_type,
                armor_class=game_state.character.armor_class,
            ),
        )
    elif item.item_type == "shield" and game_state.character.shield_equipped:
        # The player is trying to equip shield but is already
        # carrying a shield, so their existing shield is unequipped.
        old_equipped = game_state.character.shield_equipped
        game_state.character.unequip_shield()
        return_values += (
            ItemUnequippedGSM(
                old_equipped.title,
                old_equipped.item_type,
                armor_class=game_state.character.armor_class,
            ),
        )
    elif item.item_type == "wand" and game_state.character.wand_equipped:
        # The player is trying to equip wand but is already using a
        # wand, so their existing wand is unequipped.
        old_equipped = game_state.character.wand_equipped
        game_state.character.unequip_wand()
        if game_state.character.weapon_equipped:
            return_values += (
                ItemUnequippedGSM(
                    old_equipped.title,
                    old_equipped.item_type,
                    attacking_with=game_state.character.weapon_equipped,
                    attack_bonus=game_state.character.attack_bonus,
                    damage=game_state.character.damage_roll,
                ),
            )
        else:
            return_values += (
                ItemUnequippedGSM(
                    old_equipped.title, old_equipped.item_type, now_cant_attack=True
                ),
            )
    elif item.item_type == "weapon" and game_state.character.weapon_equipped:
        # The player is trying to equip weapon but is already
        # wielding a weapon, so their existing weapon is unequipped.
        old_equipped = game_state.character.weapon_equipped
        game_state.character.unequip_weapon()
        if game_state.character.wand_equipped:
            return_values += (
                ItemUnequippedGSM(
                    old_equipped.title,
                    old_equipped.item_type,
                    attacking_with=game_state.character.wand_equipped,
                    attack_bonus=game_state.character.attack_bonus,
                    damage=game_state.character.damage_roll,
                ),
            )
        else:
            return_values += (
                ItemUnequippedGSM(
                    old_equipped.title, old_equipped.item_type, now_cant_attack=True
                ),
            )

    # Now it's time to equip the new item; a item-equipped return
    # value is appended to return_values.
    if item.item_type == "armor":
        # The player is equipping a suit of armor, so the
        # Character.equip_armor() method is called with the item
        # object.
        game_state.character.equip_armor(item)
        return_values += (
            ItemEquippedGSM(
                item.title,
                "armor",
                armor_class=game_state.character.armor_class,
            ),
        )
    elif item.item_type == "shield":
        # The player is equipping a shield, so the
        # Character.equip_shield() method is called with the item
        # object.
        game_state.character.equip_shield(item)
        return_values += (
            ItemEquippedGSM(
                item.title,
                "shield",
                armor_class=game_state.character.armor_class,
            ),
        )
    elif item.item_type == "wand":
        # The player is equipping a wand, so the
        # Character.equip_wand() method is called with the item
        # object.
        game_state.character.equip_wand(item)
        return_values += (
            ItemEquippedGSM(
                item.title,
                "wand",
                attack_bonus=game_state.character.attack_bonus,
                damage=game_state.character.damage_roll,
            ),
        )
    else:
        # The player is equipping a weapon, so the
        # Character.equip_weapon() method is called with the item
        # object.
        game_state.character.equip_weapon(item)

        # Because a wand equipped always supercedes any weapon
        # equipped for a Mage, the item-equipped return value is
        # different if a wand is equipped, so this extra conditional
        # is necessary.
        if game_state.character.wand_equipped:
            return_values += (
                ItemEquippedGSM(
                    item.title,
                    "weapon",
                    attack_bonus=game_state.character.attack_bonus,
                    damage=game_state.character.damage_roll,
                    attacking_with=game_state.character.wand_equipped,
                ),
            )
        else:
            return_values += (
                ItemEquippedGSM(
                    item.title,
                    "weapon",
                    attack_bonus=game_state.character.attack_bonus,
                    damage=game_state.character.damage_roll,
                ),
            )

    # The optional item-unequipped value and the item-equipped value
    # are returned.
    return return_values
