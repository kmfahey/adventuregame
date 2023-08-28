#!/usr/bin/python3

import re

from advgame import stmsg as stmsg

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.commands.utils import _look_at_item_detail, _door_selector

from advgame.elements import Chest, Corpse


__all__ = ("look_at_command",)


def look_at_command(game_state, tokens):
    """
    Execute the LOOK AT command. The return value is always in a tuple even
    when it's of length 1. The LOOK AT command has the following usage:

    LOOK AT <item name>
    LOOK AT <item name> IN <chest name>
    LOOK AT <item name> IN INVENTORY
    LOOK AT <item name> ON <corpse name>
    LOOK AT <compass direction> DOOR
    LOOK AT <compass direction> DOORWAY

    * If that syntax is not followed, returns a .stmsg.command.BadSyntaxGSM
    object.

    * If looking at a door which is not present in the room, returns a
    .stmsg.various.DoorNotPresentGSM object.

    * If looking at a door, but the arguments are ambiguous
    and match more than one door in the room, returns a
    .stmsg.various.AmbiguousDoorSpecifierGSM object.

    * If looking at a chest or corpse which is not present in the room,
    returns a .stmsg.various.ContainerNotFoundGSM object.

    * If looking at an item which isn't present (per the arguments)
    on the floor, in a chest, on a corpse, or in inventory, returns a
    .stmsg.lookat.FoundNothingGSM object.

    * If looking at a chest or corpse which is present, returns a
    .stmsg.lookat.FoundCreatureHereGSM object.

    * If looking at a creature which is present, returns a
    .stmsg.lookat.FoundCreatureHereGSM object.

    * If looking at a door or doorway which is present, returns a
    .stmsg.lookat.FoundDoorOrDoorwayGSM object.

    * If looking at an item which is present, returns a
    .stmsg.lookat.FoundItemOrItemsHereGSM object.
    """
    look_at_door_re = re.compile(
        r"""(
                # For example, this regex
                # matches 'north iron door',
                # 'north door', 'iron door',
                # and 'door'. But it won't
                # match 'iron doorway'.
                (north|east|south|west) \s
            |
                (iron|wooden) \s
            |
                (
                    (north|east|south|west)
                    \s (iron|wooden) \s
                )
            )?
            (door|doorway)
            # Lookbehinds must be fixed-width
            # so I use 2.
            (?<! iron \s doorway)
            (?<! wooden \s doorway)
    """,
        re.X,
    )

    # The LOOK AT command can target an item in a chest or on a
    # corpse, so the presence of either 'in' or 'on' in the tokens
    # tuple indicates that case. The tokens tuple is checked for a
    # consistent container specifier; if it's poorly-constructed, an
    # error value is returned.
    if (
        not tokens
        or tokens[0] in ("in", "on")
        or tokens[-1] in ("in", "on")
        or ("in" in tokens and tokens[-1] == "corpse")
        or ("on" in tokens and tokens[-1] == "chest")
    ):
        return (stmsg.command.BadSyntaxGSM("LOOK AT", COMMANDS_SYNTAX["LOOK AT"]),)

    # This conditional is more easily accomplished with a regex
    # than a multi-line boolean chain. `look_at_door_re` is defined
    # above.
    elif tokens[-1] in ("door", "doorway") and not look_at_door_re.match(
        " ".join(tokens)
    ):
        return (stmsg.command.BadSyntaxGSM("LOOK AT", COMMANDS_SYNTAX["LOOK AT"]),)

    # These four booleans are initialized to False so they can be
    # tested for rue values later.
    item_contained = False
    item_in_inventory = False
    item_in_chest = False
    item_on_corpse = False

    # If 'in' or 'on' is used, the tokens can be divided at the
    # point it occurs into a left-hand value which is the title
    # of an item, and a right-hand value which is the title of a
    # container or is 'inventory'.
    if "in" in tokens or "on" in tokens:
        if "in" in tokens:
            # This signal value will control an upcoming conditional
            # tree.
            item_contained = True
            joinword_index = tokens.index("in")
            # As will one of these two.
            if tokens[joinword_index + 1 :] == ("inventory",):
                item_in_inventory = True
            else:
                item_in_chest = True
        else:
            joinword_index = tokens.index("on")
            if tokens[-1] != "floor":
                # These signal values will control an upcoming
                # conditional.
                item_contained = True
                item_on_corpse = True

        # joinword_index has been set, so target_title and
        # location_title are derived from the tokens before that
        # index, and the tokens after, respectively.
        target_title = " ".join(tokens[:joinword_index])
        location_title = " ".join(tokens[joinword_index + 1 :])

    # If the tokens contain neither 'in' or 'on, and the last token
    # is 'door' or 'dooray', _door_selector is used.
    elif tokens[-1] == "door" or tokens[-1] == "doorway":
        result = _door_selector(game_state, tokens)
        if isinstance(result, tuple) and isinstance(result[0], stmsg.GameStateMessage):
            # If it returns an error, that's passed along.
            return result
        else:
            # Otherwise the door it returns is the target, and a
            # found-door-or-doorway value is returned with that door
            # object informing the message.
            (door,) = result
            return (stmsg.lookat.FoundDoorOrDoorwayGSM(door.title.split(" ")[0], door),)
    else:
        # The tokens don't indicate a door and don't have a
        # location_title to break off the end. The target_title is
        # formed from the tokens.
        target_title = " ".join(tokens)

    # creature_here and container_here are assigned to local
    # variables.
    creature_here = game_state.rooms_state.cursor.creature_here
    container_here = game_state.rooms_state.cursor.container_here

    # If earlier reasoning concluded the item is meant to be found
    # in a chest, but the container here is None or a corpse, a
    # syntax error is returned.
    if (
        item_in_chest
        and isinstance(container_here, Corpse)
        or item_on_corpse
        and isinstance(container_here, Chest)
    ):
        return (stmsg.command.BadSyntaxGSM("look at", COMMANDS_SYNTAX["LOOK AT"]),)

    # If the target_title matches the creature in this room, a
    # found-creature-here value is returned.
    if creature_here is not None and creature_here.title == target_title.lower():
        return (stmsg.lookat.FoundCreatureHereGSM(creature_here.description),)

    # If the container here is not None and matches, a
    # found-container-here value is returned.
    elif container_here is not None and container_here.title == target_title.lower():
        return (stmsg.lookat.FoundContainerHereGSM(container_here),)

    # Otherwise, if the command specified an item that is contained
    # in something (including the inventory), so I test all the
    # valid states.
    elif item_contained:

        # If the item is supposed to be in the character's
        # inventory, I iterate through the inventory looking for a
        # matching title.
        if item_in_inventory:
            for item_qty, item in game_state.character.list_items():
                if item.title != target_title:
                    continue
                # If found, a found-item-here value is returned.
                # _look_at_item_detail() is used to supply a
                # detailed accounting of the item.
                return (
                    stmsg.lookat.FoundItemOrItemsHereGSM(
                        _look_at_item_detail(item), item_qty, "inventory"
                    ),
                )
            # Otherwise, a found-nothing value is returned.
            return (stmsg.lookat.FoundNothingGSM(target_title, "inventory"),)
        else:
            # Otherwise, the item is in a chest or on a corpse.
            # Either one would need to be the value for
            # container_here, so I test its title against the
            # location_title.
            if container_here is None or container_here.title != location_title:

                # If it doesn't match, a container-not-found error
                # is returned.
                return (stmsg.various.ContainerNotFoundGSM(location_title),)

            # Otherwise, if the container is non-None and its title
            # matches, I iterate through the container's contents
            # looking for a matching item title.
            elif container_here is not None and container_here.title == location_title:
                for item_qty, item in container_here.values():
                    if item.title != target_title:
                        continue
                    # If I find a match, I return a found-item-here
                    # value. _look_at_item_detail() is used to
                    # supply a detailed accounting of the item.
                    return (
                        stmsg.lookat.FoundItemOrItemsHereGSM(
                            _look_at_item_detail(item),
                            item_qty,
                            container_here.title,
                            container_here.container_type,
                        ),
                    )
                # Otherwise, I return a found-nothing value.
                return (
                    stmsg.lookat.FoundNothingGSM(
                        target_title,
                        location_title,
                        "chest" if item_in_chest else "corpse",
                    ),
                )
            else:
                # The container wasn't found, so I return a
                # container-not-found error.
                return (stmsg.various.ContainerNotFoundGSM(location_title),)
    else:

        # The target isn't a creature, or a container, or in a
        # container, or in the character's inventory, so I check the
        # floor. Again I iterate through items looking for a match.
        for item_name, (
            item_qty,
            item,
        ) in game_state.rooms_state.cursor.items_here.items():
            if item.title != target_title:
                continue
            # If I find a match, I return a found-item-here value.
            # _look_at_item_detail() is used to supply a detailed
            # accounting of the item.
            return (
                stmsg.lookat.FoundItemOrItemsHereGSM(
                    _look_at_item_detail(item), item_qty, "floor"
                ),
            )
        # Otherwise, a found-nothing value is returned.
        return (stmsg.lookat.FoundNothingGSM(target_title, "floor"),)
