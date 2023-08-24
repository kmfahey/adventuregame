#!/usr/bin/python3


from adventuregame.statemsgs._common import GameStateMessage
from adventuregame.utility import join_str_seq_w_commas_and_conjunction, usage_verb


__all__ = ("PutAmountOfItem", "ItemNotInInventory", "QuantityUnclear", "TryingToPutMoreThanYouHave",)

class PutAmountOfItem(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player
successfully places one or more items in a chest or on a corpse's person.
    """
    __slots__ = 'item_title', 'container_title', 'container_type', 'amount_put', 'amount_left'

    @property
    def message(self):
        # This message property constructs a pair of sentences that convey how
        # many of what item was put where, and how many the player character has
        # left.
        amount_put_pluralizer = 's' if self.amount_put > 1 else ''
        amount_left_pluralizer = 's' if self.amount_left > 1 or not self.amount_left else ''
        container_placed_location_clause = (f'in the {self.container_title}' if self.container_type == 'chest'
                              else f"on the {self.container_title}'s person")
        amount_left_clause = (f'{self.amount_left} {self.item_title}{amount_left_pluralizer} left' if self.amount_left != 0
                        else f'no more {self.item_title}{amount_left_pluralizer}')
        return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} {container_placed_location_clause}. '
                f'You have {amount_left_clause}.')

    def __init__(self, item_title, container_title, container_type, amount_put, amount_left):
        self.item_title = item_title
        self.container_title = container_title
        self.container_type = container_type
        self.amount_put = amount_put
        self.amount_left = amount_left


class ItemNotInInventory(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player attempts
to put an item in a chest or on a corpse that is not in their inventory.
    """
    __slots__ = 'amount_attempted', 'item_title'

    @property
    def message(self):
        if self.amount_attempted > 1:
            return f"You don't have any {self.item_title}s in your inventory."
        else:
            return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title, amount_attempted):
        self.amount_attempted = amount_attempted
        self.item_title = item_title


class QuantityUnclear(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player writes
an ungrammatical sentence that is ambiguous as to how many of the item they mean
to put in the chest or on the corpse.
    """

    @property
    def message(self):
        return 'Amount to put unclear. How many do you mean?'

    def __init__(self):
        pass


class TryingToPutMoreThanYouHave(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player tries to
put a quantity of an item in a chest or on a corpse that that is more than they
have in their inventory.
    """
    __slots__ = 'item_title', 'amount_present'

    @property
    def message(self):
        pluralizer = 's' if self.amount_present > 1 else ''
        return f'You only have {self.amount_present} {self.item_title}{pluralizer} in your inventory.'

    def __init__(self, item_title, amount_present):
        self.item_title = item_title
        self.amount_present = amount_present
