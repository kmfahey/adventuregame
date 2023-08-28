#!/usr/bin/python3

from advgame.errors import InternalError
from advgame.stmsg.gsm import GameStateMessage
from advgame.utils import join_strs_w_comma_conj


__all__ = (
    "FoundContainerHere",
    "FoundCreatureHere",
    "FoundDoorOrDoorway",
    "FoundItemOrItemsHere",
    "FoundNothing",
)


class FoundContainerHereGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.look_at_command() when the
    player targets a chest or a corpse. If it's a chest and it's unlocked,
    the contents of the chest are conveyed. If it's a corpse, the corpse's
    possessions are conveyed.
    """

    __slots__ = (
        "container_description",
        "container_type",
        "container",
        "is_locked",
        "is_closed",
    )

    @property
    def message(self):
        # This message property handles looking at a chest or corpse. If
        # it's a chest, the property handles all possible combinations
        # of is_locked in (True, False, None) and is_closed in (True,
        # False, None). If the chest isn't locked or closed, it lists
        # the chest's contents. If it's a corpse, contents are listed.
        # Since contents listing appears at several points in the
        # conditional, it's handled by a private property, _contents
        # (see below).
        if self.container_type == "chest":
            if self.is_locked is True and self.is_closed is True:
                return f"{self.container_description} It is closed and locked."
            elif self.is_locked is False and self.is_closed is True:
                return f"{self.container_description} It is closed but unlocked."
            elif self.is_locked is False and self.is_closed is False:
                return (
                    f"{self.container_description} It is unlocked and open. "
                    + f"{self._contents}"
                )
            elif self.is_locked is True and self.is_closed is False:
                raise InternalError(
                    "FoundContainerHere.message accessed to describe a chest "
                    + "with the impossible combination of is_locked = True "
                    + "and is_closed = False."
                )
            elif self.is_locked is None and self.is_closed is True:
                return f"{self.container_description} It is closed."
            elif self.is_locked is None and self.is_closed is False:
                return f"{self.container_description} It is open. {self._contents}"
            elif self.is_locked is True and self.is_closed is None:
                return f"{self.container_description} It is locked."
            elif self.is_locked is False and self.is_closed is None:
                return f"{self.container_description} It is unlocked."
            else:  # None and None
                return self.container_description
        elif self.container_type == "corpse":
            return f"{self.container_description} {self._contents}"

    # This property assembles a sentence listing off the items the
    # container has. It's implemented separately because several
    # different outcomes of the logic in the message property above can
    # lead to conveying the container's contents.

    @property
    def _contents(self):
        # A list of strings comprising the item title and qty for each
        # item in sorted order by title is formed.
        contents_strs_tuple = [
            f"{qty} {item.title}s"
            if qty > 1
            else f"an {item.title}"
            if item.title[0] in "aeiou"
            else f"a {item.title}"
            for qty, item in sorted(
                self.container.values(), key=lambda arg: arg[1].title
            )
        ]
        # The list is condensed to a comma-separated string using a
        # utility function.
        contents_str = join_strs_w_comma_conj(contents_strs_tuple, "and")
        # If the list is zero-length, the message conveys that the
        # container is empty.
        if len(contents_strs_tuple) == 0:
            return (
                "It is empty."
                if self.container_type == "chest"
                else "They have nothing on them."
            )
        # Otherwise a container-specific framing str is used to convey
        # the contents.
        elif self.container_type == "chest":
            return f"It contains {contents_str}."
        else:
            return f"They have {contents_str} on them."

    def __init__(self, container):
        self.container = container
        self.container_description = container.description
        self.is_locked = container.is_locked
        self.is_closed = container.is_closed
        self.container_type = container.container_type
        if self.is_locked is True and self.is_closed is False:
            raise InternalError(
                f"Container {container.internal_name} has is_locked = True "
                + "and is_open = False, invalid combination of parameters."
            )


class FoundCreatureHereGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.look_command() when the
    player targets a creature in the dungeon's current room.
    """

    __slots__ = ("creature_description",)

    @property
    def message(self):
        return self.creature_description

    def __init__(self, creature_description):
        self.creature_description = creature_description


class FoundDoorOrDoorwayGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.look_at_command() when the
    player targets a door or doorway in the current dungeon room.
    """

    __slots__ = "compass_dir", "door"

    @property
    def message(self):
        # This message property combines the Door object's description,
        # a statement of which wall the door is on, and a statement of
        # its closed/locked status.
        closed_locked_str = (
            "It is closed and locked."
            if self.door.is_closed and self.door.is_locked
            else "It is closed but unlocked."
            if self.door.is_closed and not self.door.is_locked
            else "It is open."
        )
        return (
            f"{self.door.description} It is set in the "
            + f"{self.compass_dir} wall. {closed_locked_str}"
        )

    def __init__(self, compass_dir, door):
        self.compass_dir = compass_dir
        self.door = door


class FoundItemOrItemsHereGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.look_at_command() when the
    player targets an item that is present on the floor of current room or
    in their inventory or in a chest or on a corpse's person as specified by
    the player. It conveys the item's description attribute and specifies
    how many are present.
    """

    __slots__ = "item_description", "item_qty"

    @property
    def message(self):
        # This message property combines the given item description with
        # a sentence indicating how many there are and where they are:
        # on the floor, in the character's inventory, in a chest or on a
        # corpse's person.
        to_be_conjug = "is" if self.item_qty == 1 else "are"
        item_location = (
            "on the floor"
            if self.container_title == "floor"
            else "in your inventory"
            if self.container_title == "inventory"
            else f"in the {self.container_title}"
            if self.container_type == "chest"
            else f"on the {self.container_title}'s person"
        )
        return (
            f"{self.item_description} There {to_be_conjug} "
            + f"{self.item_qty} {item_location}."
        )

    def __init__(
        self, item_description, item_qty, container_title, container_type=None
    ):
        self.item_description = item_description
        self.item_qty = item_qty
        self.container_title = container_title
        self.container_type = container_type


class FoundNothingGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.look_at_command() when the
    player targets an item that can't be found where they said it was.
    """

    __slots__ = "item_title", "item_location", "location_type"

    @property
    def message(self):
        # This message property conveys that an item doesn't exist where
        # the player looked for it: in a chest, on a corpse, on the
        # floor or in their inventory. If the call wasn't specific, a
        # generic 'You see no X here' is returned.
        if self.item_location is not None:
            if self.location_type == "chest":
                return f"The {self.item_location} has no {self.item_title} in it."
            elif self.location_type == "corpse":
                return (
                    f"The {self.item_location} has no {self.item_title} on "
                    + "its person."
                )
            elif self.item_location == "floor":
                return f"There is no {self.item_title} on the floor."
            elif self.item_location == "inventory":
                return f"You have no {self.item_title} in your inventory."
            else:
                raise InternalError(
                    f"Location type {self.location_type} not recognized."
                )
        else:
            return f"You see no {self.item_title} here."

    def __init__(self, item_title, item_location=None, location_type=None):
        self.item_title = item_title
        self.item_location = item_location
        self.location_type = location_type
