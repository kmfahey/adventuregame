#!/usr/bin/python3


from advgame.statemsgs.gsm import GameStateMessage
from advgame.utils import usage_verb


__all__ = (
    "ClassCantUseItem",
    "NoSuchItemInInventory",
)


class ClassCantUseItemGSM(GameStateMessage):
    """
    Returned by equip_command() when the player tries to equip an item that
    is not allowed for their class. As an example, a Mage would get this
    result if they tried to equip a suit of armor or a shield, and anyone
    besides a Mage would get this result if they tried to equip a wand.
    """

    __slots__ = "character_class", "item_title", "item_type"

    @property
    def message(self):
        # This message property assembles a string to inform the player
        # that they can't equip an item due to class restrictions. Like
        # Stmsg_Drop_DroppedItem.message, it omits the indirect article
        # if the item is a suit of armor.
        item_usage_verb = usage_verb(self.item_type, gerund=False)
        pluralizer = "s" if self.item_type != "armor" else ""
        return (
            f"{self.character_class}s can't {item_usage_verb} "
            + f"{self.item_title}{pluralizer}."
        )

    def __init__(self, character_class, item_title, item_type):
        self.character_class = character_class
        self.item_title = item_title
        self.item_type = item_type


class NoSuchItemInInventoryGSM(GameStateMessage):
    """
    Returned by equip_command() when the player tries to equip an item that
    they don't have in their inventory.
    """

    __slots__ = ("item_title",)

    @property
    def message(self):
        return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title):
        self.item_title = item_title
