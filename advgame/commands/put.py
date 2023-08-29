#!/usr/bin/python3

from math import nan as NaN

from advgame.commands.utils import _put_or_take_preproc
from advgame.stmsg import GameStateMessage
from advgame.stmsg.put import (
    ItemNotInInventoryGSM,
    PutAmountOfItemGSM,
    TryingToPutMoreThanYouHaveGSM,
)


__all__ = ("put_command",)


def put_command(game_state, tokens):
    """
    Execute the PUT command. The return value is always in a tuple even when
    it's of length 1. The PUT command has the following usage:

    PUT <item name> IN <chest name>
    PUT <number> <item name> IN <chest name>
    PUT <item name> ON <corpse name>
    PUT <number> <item name> ON <corpse name>

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If the arguments specify a chest or corpse that is not present in the
    current room, returns a ContainerNotFoundGSM object.

    * If the arguments specify a chest that is closed, returns a
    ContainerIsClosedGSM object.

    * If the arguments are an ungrammatical sentence and are ambiguous about
    the quantity to put, returns a AmountToPutUnclearGSM object.

    * If the arguments specify an item to put that is not present in the
    character's inventory, returns a ItemNotInInventoryGSM object.

    * If the arguments specify a quantity of an item to put that is more
    than the character has, returns a TryingToPutMorethanYouHaveGSM
    object.

    * Otherwise, the item— or the quantity of the item— is removed from
    the character's inventory, placed in the chest or on the corpse, and
    put in the chest or on the corpse, and a AmountPutGSM object is
    returned.
    """
    # The shared private workhorse method is called and it handles
    # the majority of the error-checking. If it returns an error
    # that is passed along.
    results = _put_or_take_preproc(game_state, "PUT", tokens)

    if len(results) == 1 and isinstance(results[0], GameStateMessage):
        # If it returned an error, I return the tuple.
        return results
    else:
        # Otherwise, I recover put_amount (nt), item_title (str),
        # container_title (str) and container (Chest or Corpse) from
        # the results.
        put_amount, item_title, container_title, container = results

    # I read off the player's Inventory and filter it for a
    # (qty,obj) pair whose title matches the supplied Item name.
    inventory_list = tuple(
        filter(
            lambda pair: pair[1].title == item_title,
            game_state.character.list_items(),
        )
    )

    if len(inventory_list) == 1:

        # The player has the Item in their Inventory, so I save the
        # qty they possess and the Item object.
        amount_possessed, item = inventory_list[0]
    else:

        # Otherwise I return an item-not-in-inventory error.
        return (ItemNotInInventoryGSM(item_title, put_amount),)

    # I use the Item subclass object to get the internal_name, and
    # look it up in the container to see if any amount is already
    # there. If so I record the amount, otherwise the amount is
    # saved as 0.
    if container.contains(item.internal_name):
        amount_in_container, _ = container.get(item.internal_name)
    else:
        amount_in_container = 0

    if put_amount > amount_possessed:
        # If the amount to put is more than the amount in inventory,
        # I return a trying-to-put-more-than-you-have error.
        return (TryingToPutMoreThanYouHaveGSM(item_title, amount_possessed),)
    elif put_amount is NaN:
        # Otherwise if _put_or_take_preproc returned nan for
        # the put_amount, that means it couldn't be determined from
        # the arguments but is implied, so I set it equal to the
        # total amount possessed, and set the amount_possessed to 0.
        put_amount = amount_possessed
        amount_possessed = 0
    else:

        # Otherwise I decrement the amount_possessed by the put
        # amount.
        amount_possessed -= put_amount

    # I remove the item in the given quantity from the player
    # character's inventory, and add the item in that quantity to
    # the container. Then I return a amount-put value.
    game_state.character.drop_item(item, qty=put_amount)
    container.set(item.internal_name, amount_in_container + put_amount, item)
    return (
        PutAmountOfItemGSM(
            item_title,
            container_title,
            container.container_type,
            put_amount,
            amount_possessed,
        ),
    )
