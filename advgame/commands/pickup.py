#!/usr/bin/python3

from math import nan as NaN

from advgame.commands.utils import _pick_up_or_drop_preproc, _door_selector
from advgame.statemsgs import GameStateMessage
from advgame.statemsgs.pickup import (
    CantPickUpChestCorpseCreatureOrDoorGSM,
    ItemNotFoundGSM,
    ItemPickedUpGSM,
    TryingToPickUpMoreThanIsPresentGSM,
)


__all__ = ("pick_up_command",)


def pick_up_command(game_state, tokens):
    """
    Execute the PICK UP command. The return value is always in a tuple even
    when it's of length 1. The PICK UP command has the following usage:

    PICK UP <item name>
    PICK UP <number> <item name>),

    * If that syntax is not followed, returns a BadSyntaxGSM
    object.

    * If the arguments are ungrammatical and are unclear about the quantity
    to pick up, returns a AmountToPickUpUnclearGSM object.

    * If the arguments specify a chest, corpse, creature or door, returns a
    CantPickUpChestCorpseCreatureOrDoorGSM object.

    * If the arguments specify an item to pick up that is not on the floor
    in the room, returns a ItemNotFoundGSM object.

    * If the arguments specify a quantity of the item to pick up that is
    greater than the quantity present on the floor in the room, returns a
    TryingToPickUpMoreThanIsPresentGSM object.

    * Otherwise, the item— or the quantity of the item— is removed
    from the floor, and added to the character's inventory, and a
    ItemPickedUpGSM object is returned.
    """
    # The door var is set to None so later it can be checked for a
    # non-None value.
    door = None
    pick_up_quantity = 0

    # If the contents of tokens is a door specifier,
    # _door_selector() is used.
    if tokens[-1] in ("door", "doorway"):
        result = _door_selector(game_state, tokens)
        # If an error value was returned, it's returned.
        if isinstance(result[0], GameStateMessage):
            return result
        else:
            # Otherwise the Door object is extracted from the result
            # tuple. Doors can't be picked up but we at least want
            # to match exactly.
            (door,) = result
            target_title = door.title
    else:
        # Otherwise, a private workhorse method is used to parse the
        # arguments.
        result = _pick_up_or_drop_preproc("PICK UP", tokens)
        if isinstance(result[0], GameStateMessage):
            return result
        else:
            pick_up_quantity, target_title = result

    # unpickupable_item_type is initialized to None so it can be
    # tested for a non-None value later. If it acquires another
    # value, an error value will be returned.
    unpickupable_element_type = None
    if door is not None:

        # The arguments specified a door, so unpickupable_item_type
        # is set to 'door'.
        unpickupable_element_type = "door"

    # Otherwise, if the current room has a creature_here and its
    # title matches, unpickupable_item_type is set to 'creature'.
    elif (
        game_state.rooms_state.cursor.creature_here is not None
        and game_state.rooms_state.cursor.creature_here.title == target_title
    ):
        unpickupable_element_type = "creature"

    # Otherwise, if the current room has a container_here and
    # its title matches, unpickupable_item_type is set to its
    # container_type.
    elif (
        game_state.rooms_state.cursor.container_here is not None
        and game_state.rooms_state.cursor.container_here.title == target_title
    ):
        unpickupable_element_type = (
            game_state.rooms_state.cursor.container_here.container_type
        )

    # If unpickupable_element_type acquired a value, a
    # cant-pick-up-element error is returned.
    if unpickupable_element_type:
        return (
            CantPickUpChestCorpseCreatureOrDoorGSM(
                unpickupable_element_type, target_title
            ),
        )

    # If this room has no items_here ItemsMultiState object, nothing
    # can be picked up, and a item-not-found error is returned.
    if game_state.rooms_state.cursor.items_here is None:
        return (ItemNotFoundGSM(target_title, pick_up_quantity),)

    # The items_here.values() sequence is cast to tuple and assigned
    # to a local variable, and the character's inventory is also so
    # assigned. I iterate through both of them looking for items
    # with titles matching target_title.
    items_here = tuple(game_state.rooms_state.cursor.items_here.values())
    items_had = tuple(game_state.character.list_items())
    item_here_pair = tuple(
        filter(lambda pair: pair[1].title == target_title, items_here)
    )
    items_had_pair = tuple(
        filter(lambda pair: pair[1].title == target_title, items_had)
    )

    # If no item was found in items_here matching target_title, a
    # tuple of items that *are* here is formed, and a item-not-found
    # error is instanced with it as an argument and returned.
    if not len(item_here_pair):
        items_here_qtys_titles = tuple(
            (item_qty, item.title) for item_qty, item in items_here
        )
        return (
            ItemNotFoundGSM(target_title, pick_up_quantity, *items_here_qtys_titles),
        )

    # Otherwise, the item was found here, so its quantity and the
    # Item subclass object are extracted and saved.
    ((quantity_here, item),) = item_here_pair

    # _pick_up_or_drop_preproc() returns NaN if it couldn't
    # determine a quantity. If it did, I assume the player meant
    # all of the item that's here, and set pick_up_quantity to
    # quantity_here.
    if pick_up_quantity is NaN:
        pick_up_quantity = quantity_here

    # quantity_in_inventory is needed for the item-picked-up
    # return value constructor. If the item title had a match
    # in the inventory, the quantity there is assigned to
    # quantity_in_inventory, otherwise it's set to 0.
    quantity_in_inventory = items_had_pair[0][0] if len(items_had_pair) else 0

    # If the quantity to pick up specified in the command
    # is greater than the quantity in items_here, a
    # trying-to-pick-up-more-than-is-present error is returned.
    if quantity_here < pick_up_quantity:
        return (
            TryingToPickUpMoreThanIsPresentGSM(
                target_title, pick_up_quantity, quantity_here
            ),
        )
    else:
        # Otherwise, that quantity of the item is added to the
        # player character's inventory.
        game_state.character.pick_up_item(item, qty=pick_up_quantity)

        # If the entire quantity of the item in items_here was
        # picked up, it's deleted from items_here.
        if quantity_here == pick_up_quantity:
            game_state.rooms_state.cursor.items_here.delete(item.internal_name)
        else:
            # Otherwise its new quantity is set in items_here.
            game_state.rooms_state.cursor.items_here.set(
                item.internal_name, quantity_here - pick_up_quantity, item
            )
        # The quantity now possessed is computed, and used to
        # construct a item-picked-up return value, which is
        # returned.
        quantity_had_now = quantity_in_inventory + pick_up_quantity
        return (ItemPickedUpGSM(target_title, pick_up_quantity, quantity_had_now),)
