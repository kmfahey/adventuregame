#!/usr/bin/python3

from math import nan as NaN

from advgame.commands.utils import _pick_up_or_drop_preproc
from advgame.elements import ItemsMultiState
from advgame.stmsg import GameStateMessage
from advgame.stmsg.drop import DroppedItemGSM, TryingToDropItemYouDontHaveGSM, TryingToDropMoreThanYouHaveGSM
from advgame.stmsg.various import ItemUnequippedGSM


__all__ = ("drop_command",)


def drop_command(game_state, tokens):
    """
    Execute the DROP command. The return value is always in a tuple even
    when it's of length 1. The DROP command has the following usage:

    DROP <item name>
    DROP <number> <item name>

    * If the item specified isn't in inventory, returns a
    TryingToDropItemYouDontHaveGSM object.

    * If a number is specified, and that's more than how many of the item
    are in inventory, returns a
    TryingToDropMorethanYouHaveGSM object.

    * If no number is used and the item is equipped, returns a
    ItemUnequippedGSM object and a DroppedItemGSM
    object.

    * Otherwise, the item is removed— or the specified number of the item
    are removed— from inventory and a DroppedItemGSM object is
    returned.
    """
    # pick_up_command() and drop_command()
    # share a lot of logic in a private workhorse method
    # _pick_up_or_drop_preproc(). As with all private workhorse
    # methods, the return value is a tuple and might consist of an
    # error value; so the 1st element is type tested to see if its a
    # GameStateMessage subclass object.
    result = _pick_up_or_drop_preproc("DROP", tokens)
    if len(result) == 1 and isinstance(result[0], GameStateMessage):

        # The workhorse method returned an error, so I pass that
        # along.
        return result
    else:

        # The workhorse method succeeded, I extract the item to drop
        # and the quantity from its return tuple.
        drop_quantity, item_title = result

    # The quantity of the item on the floor is reported by some
    # drop_command() return values, so I check the contents of
    # items_here.
    if game_state.rooms_state.cursor.items_here is not None:
        items_here = tuple(game_state.rooms_state.cursor.items_here.values())
    else:
        items_here = ()

    # items_here's contents are filtered looking for an item by a
    # matching title. If one is found, the quantity already in the
    # room is saved to quantity_already_here.
    item_here_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_here))
    quantity_already_here = item_here_pair[0][0] if len(item_here_pair) else 0

    # In the same way, the Character's inventory is listed and
    # filtered looking for an item by a matching title.
    items_had_pair = tuple(
        filter(
            lambda pair: pair[1].title == item_title,
            game_state.character.list_items(),
        )
    )

    # The player character's inventory doesn't contain an item by
    # that title, so a trying-to-drop-an-item-you-don't-have error
    # is returned.
    if not len(items_had_pair):
        return (TryingToDropItemYouDontHaveGSM(item_title, drop_quantity),)

    # The item was found, so its object and quantity are saved.
    ((item_had_qty, item),) = items_had_pair

    if drop_quantity > item_had_qty:

        # If the quantity specified to drop is greater than the
        # quantity in inventory, a trying-to-drop-more-than-you-have
        # error is returned.
        return (
            TryingToDropMoreThanYouHaveGSM(
                item_title, drop_quantity, item_had_qty
            ),
        )
    elif drop_quantity is NaN:

        # The workhorse method returns NaN as the drop_quantity
        # if the arguments didn't specify a quantity. I now know how
        # many the player character has, so I assume they mean to
        # drop all of them. I set drop_quantity to item_had_qty.
        drop_quantity = item_had_qty

    # If the player drops an item they had equipped, and they have
    # none left, it is unequipped. The return tuple is started
    # with unequip_return, which may be empty at the end of this
    # conditional.
    unequip_return = ()
    if drop_quantity - item_had_qty == 0:

        # This only runs if the player character will have none left
        # after this drop. All four equipment types are separately
        # checked to see if they're the item being dropped. The
        # unequip return value needs to specify which game stats
        # have been changed by the unequipping, so this conditional
        # is involved.
        armor_equipped = game_state.character.armor_equipped
        weapon_equipped = game_state.character.weapon_equipped
        shield_equipped = game_state.character.shield_equipped
        wand_equipped = game_state.character.wand_equipped

        # If the character's armor is being dropped, it's unequipped
        # and a item-unequipped error value is generated, noting the
        # decreased armor class.
        if (
            item.item_type == "armor"
            and armor_equipped is not None
            and armor_equipped.internal_name == item.internal_name
        ):
            game_state.character.unequip_armor()
            unequip_return = (
                ItemUnequippedGSM(
                    item.title,
                    item.item_type,
                    armor_class=game_state.character.armor_class,
                ),
            )
        # If the character's shield is being dropped, it's
        # unequipped and a item-unequipped error value is generated,
        # noting the decreased armor class.
        elif (
            item.item_type == "shield"
            and shield_equipped is not None
            and shield_equipped.internal_name == item.internal_name
        ):
            game_state.character.unequip_shield()
            unequip_return = (
                ItemUnequippedGSM(
                    item_title,
                    "shield",
                    armor_class=game_state.character.armor_class,
                ),
            )

        # If the character's weapon is being dropped, it's
        # unequipped, and an item-unequipped error value is
        # generated.
        elif (
            item.item_type == "weapon"
            and weapon_equipped is not None
            and weapon_equipped.internal_name == item.internal_name
        ):
            game_state.character.unequip_weapon()
            if wand_equipped:
                # If the player character is a mage and has a wand
                # equipped, the wand's attack values are included
                # since they will use the wand to attack. (An
                # equipped wand always takes precedence over a
                # weapon for a Mage.)
                unequip_return = (
                    ItemUnequippedGSM(
                        item_title,
                        "weapon",
                        attack_bonus=game_state.character.attack_bonus,
                        damage=game_state.character.damage_roll,
                        attacking_with=wand_equipped,
                    ),
                )
            else:
                # Otherwise, the player will be informed that they
                # now can't attack.
                unequip_return = (
                    ItemUnequippedGSM(
                        item_title, "weapon", now_cant_attack=True
                    ),
                )

        # If the character's wand is being dropped, it's unequipped,
        # and an item-unequipped error value is generated.
        elif (
            item.item_type == "wand"
            and wand_equipped is not None
            and wand_equipped.internal_name == item.internal_name
        ):
            game_state.character.unequip_wand()
            if weapon_equipped:
                # If the player has a weapon equipped, the weapon's
                # attack values are included since they will fall
                # back on it.
                unequip_return = (
                    ItemUnequippedGSM(
                        item_title,
                        "wand",
                        attack_bonus=game_state.character.attack_bonus,
                        damage=game_state.character.damage_roll,
                        now_attacking_with=weapon_equipped,
                    ),
                )
            else:
                # Otherwise, the player will be informed that they
                # now can't attack.
                unequip_return = (
                    ItemUnequippedGSM(
                        item_title, "wand", now_cant_attack=True
                    ),
                )

    # Finally, with all other preconditions handled, I actually drop
    # the item.
    game_state.character.drop_item(item, qty=drop_quantity)

    # If there wasn't a ItemsMultiState set to items_here, I
    # instantiate one.
    if game_state.rooms_state.cursor.items_here is None:
        game_state.rooms_state.cursor.items_here = ItemsMultiState()

    # The item is saved to items_here with the combined quantity of
    # what was already there (can be 0) and the quantity dropped.
    game_state.rooms_state.cursor.items_here.set(
        item.internal_name, quantity_already_here + drop_quantity, item
    )

    # I calculate the quantity left in the character's inventory,
    # and return a dropped-item value with the quantity dropped,
    # the quantity on the floor, and the quantity remaining in
    # inventory.
    quantity_had_now = item_had_qty - drop_quantity
    return unequip_return + (
        DroppedItemGSM(
            item_title,
            item.item_type,
            drop_quantity,
            quantity_already_here + drop_quantity,
            quantity_had_now,
        ),
    )
