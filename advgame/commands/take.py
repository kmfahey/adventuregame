#!/usr/bin/python3

from math import nan as NaN

from advgame.commands.utils import _put_or_take_preproc
from advgame.statemsgs import GameStateMessage
from advgame.statemsgs.take import (
    ItemNotFoundInContainerGSM,
    ItemOrItemsTakenGSM,
    TryingToTakeMoreThanIsPresentGSM,
)


__all__ = ("take_command",)


def take_command(game_state, tokens):
    """
    Execute the TAKE command. The return value is always in a tuple even
    when it's of length 1. The TAKE command has the following usage:

    TAKE <item name> FROM <container name>
    TAKE <number> <item name> FROM <container name>

    * If that syntax is not followed, returns a BadSyntaxGSM object.

    * If the specified container isn't present in the current room, returns
    a ContainerNotFoundGSM object.

    * If the specified container is a chest and the chest is closed, returns
    a ContainerIsClosedGSM object.

    * If the arguments are an ungrammatical sentence and are ambiguous as to
    what quantity the player means to take, returns a AmountToTakeUnclearGSM
    object.

    * If the specified item is not present in the specified chest or on the
    specified corpse, returns a ItemNotFoundInContainerGSM object.

    * If the specified quantity of the item is greater than the
    quantity of that item in the chest or on the corpse, returns a
    TryingToTakeMoreThanIsPresentGSM object.

    * Otherwise, the item— or the quantity of the item— is removed from
    the chest or the corpse and added to the character's inventory, and a
    ItemOrItemsTakenGSM object is returned.
    """
    # take_command() shares logic with put_command() in a private
    # workhorse method _put_or_take_preproc().
    results = _put_or_take_preproc(game_state, "TAKE", tokens)

    # As always with private workhorse methods, it may have returned
    # an error value; if so, I return it.
    if len(results) == 1 and isinstance(results[0], GameStateMessage):
        return results
    else:
        # Otherwise, I extract the values parsed out of tokens from
        # the results tuple.
        quantity_to_take, item_title, container_title, container = results

    # The following loop iterates over all the items in the
    # Container. I use a while loop so it's possible for the search
    # to fall off the end of the loop. If that code is reached, the
    # specified Item isn't in this Container.
    matching_item = tuple(
        filter(lambda argl: argl[1][1].title == item_title, container.items())
    )
    if len(matching_item) == 0:
        return (
            ItemNotFoundInContainerGSM(
                container_title,
                quantity_to_take,
                container.container_type,
                item_title,
            ),
        )

    ((item_internal_name, (item_quantity, item)),) = matching_item

    # The private workhorse method couldn't determine a quantity and
    # returned the signal value NaN, so I assume the entire
    # amount present is intended, and set quantity_to_take to
    # item_quantity.
    if quantity_to_take is NaN:
        quantity_to_take = item_quantity
    if quantity_to_take > item_quantity:
        # The amount specified is more than how
        # much is in the Container, so I return a
        # trying-to-take-more-than-is-present error.
        return (
            TryingToTakeMoreThanIsPresentGSM(
                container_title,
                container.container_type,
                item_title,
                item.item_type,
                quantity_to_take,
                item_quantity,
            ),
        )

    if quantity_to_take == item_quantity:
        # The amount to remove is the total amount present, so I
        # delete it from the container.
        container.delete(item_internal_name)
    else:
        # The quantity to take is less thant the amount present, so
        # I set the item in the container to the new lower quantity.
        container.set(item_internal_name, item_quantity - quantity_to_take, item)

    # I add the item in the given quantity to the player character's
    # inventory and return an item-or-items-taken value.
    game_state.character.pick_up_item(item, qty=quantity_to_take)
    return (ItemOrItemsTakenGSM(container_title, item_title, quantity_to_take),)
