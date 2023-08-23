#!/usr/bin/python3


from adventuregame.utility import usage_verb
from adventuregame.statemsgs._common import GameStateMessage


__all__ = "ItemNotEquipped",


class ItemNotEquipped(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.unequip_command() when the player
tries to unequip an item that is not equipped.
    """
    __slots__ = 'item_specified_title', 'item_specified_type', 'item_present_title'

    @property
    def message(self):
        # This message property assembles 1-2 sentences that indicate the
        # specified item can't be unequipped because it wasn't equipped to begin
        # with.
        if self.item_specified_type is not None:

            # This convenience function returns the correct verb to use to refer
            # to using an item of the given type.
            item_usage_verb = usage_verb(self.item_specified_type, gerund=True)
            article_or_suit = ('a suit of' if self.item_specified_type == 'armor'
                               else 'an' if self.item_specified_title[0] in 'aeiou'
                               else 'a')
            return_str = f"You're not {item_usage_verb} {article_or_suit} {self.item_specified_title}."

            # If the player character has another item of that type equipped
            # instead, a sentence referring to it is included, so the player can
            # amend their EQUIP command.
            if self.item_present_title:
                return_str += f" You're {item_usage_verb} {article_or_suit} {self.item_present_title}."
        else:
            # The returning method didn't know what type the specified item was,
            # so I use a generic reply.
            return_str = f"You don't have a {self.item_specified_title} equipped."
        return return_str

    def __init__(self, item_specified_title, item_specified_type=None, item_present_title=None):
        self.item_specified_title = item_specified_title
        self.item_specified_type = item_specified_type
        self.item_present_title = item_present_title


