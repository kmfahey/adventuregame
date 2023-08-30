#!/usr/bin/python3

from advgame.statemsgs.gsm import GameStateMessage
from advgame.utils import join_strs_w_comma_conj


__all__ = ("DisplayInventoryGSM",)


class DisplayInventoryGSM(GameStateMessage):
    """
    Returned by inventory_command(). It lists all the items in the
    character's inventory by title and quantity. If they want more
    information they need to say 'LOOK AT <item title> IN INVENTORY'.
    """

    __slots__ = ("inventory_contents",)

    @property
    def message(self):
        display_strs_list = list()
        for item_qty, item in self.inventory_contents:
            indir_artcl_or_qty = (
                str(item_qty)
                if item_qty > 1
                else "a suit of"
                if item.item_type == "armor"
                else "an"
                if item.title[0] in "aeiou"
                else "a"
            )
            pluralizer = "s" if item_qty > 1 else ""
            display_strs_list.append(f"{indir_artcl_or_qty} {item.title}{pluralizer}")
        return (
            "You have "
            + join_strs_w_comma_conj(display_strs_list, "and")
            + " in your inventory."
        )

    def __init__(self, inventory_contents_list):
        self.inventory_contents = inventory_contents_list
