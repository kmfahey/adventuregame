#!/usr/bin/python3

from operator import itemgetter

from advgame.stmsg.gsm import GameStateMessage
from advgame.utils import join_strs_w_comma_conj


__all__ = ("CantPickUpChestCorpseCreatureOrDoor", "ItemNotFound", "ItemPickedUp", "QuantityUnclear", "TryingToPickUpMoreThanIsPresent",)


class CantPickUpChestCorpseCreatureOrDoor(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.pick_up_command() when the
player has specifies a game element that is a chest, corpse, creature or
door and can't be picked up.
    """

    __slots__ = 'element_type', 'element_title'

    @property
    def message(self):
        return f"You can't pick up the {self.element_title}: can't pick up {self.element_type}s!"

    def __init__(self, element_type, element_title):
        self.element_type = element_type
        self.element_title = element_title


class ItemNotFound(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.pick_up_command() when the
player targets an item to pick up that is not present in the current
dungeon room. If they meant to acquire an item from a chest or corpse,
they need to say `TAKE <item name> FROM <corpse or chest name>`.
    """

    __slots__ = 'item_title', 'amount_attempted', 'items_here'

    @property
    def message(self):
        # This message property assembles a string that indicates the
        # specified item isn't present. The object is initialized with
        # the items_here attribute of the current room object, and if
        # it's non-null the items are listed as alternatives.
        item_pluralizer = 's' if self.amount_attempted > 1 else ''
        if self.items_here:
            items_here_str_tuple = tuple(f'{item_count} {item_title}s' if item_count > 1
                                         else f'an {item_title}' if item_title[0] in 'aeiou'
                                         else f'a {item_title}'
                                             for item_count, item_title in self.items_here)
            items_here_str = join_strs_w_comma_conj(items_here_str_tuple, 'and')
            return f'You see no {self.item_title}{item_pluralizer} here. However, there is {items_here_str} here.'
        else:
            return f'You see no {self.item_title}{item_pluralizer} here.'

    def __init__(self, item_title, amount_attempted, *items_here):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.items_here = tuple(sorted(items_here, key=itemgetter(1)))


class ItemPickedUp(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.pick_up_command() when
the player successfully acquires an item from the floor of the current
dungeon room.
    """

    __slots__ = 'item_title', 'pick_up_amount', 'amount_had'

    @property
    def message(self):
        # This message property assembles a sentence conveying that one
        # or more items were picked up, and mentioning how many the
        # player character now has. It picks the article or determiner
        # and the use of a pluralizing s suffix.
        picked_up_indir_artcl_or_qty = (str(self.pick_up_amount) if self.pick_up_amount > 1
                                        else 'an' if self.item_title[0] in 'aeiou'
                                        else 'a')
        picked_up_pluralizer = 's' if self.pick_up_amount > 1 else ''
        amt_had_indir_artcl_or_qty = (str(self.amount_had) if self.amount_had > 1
                                      else 'an' if self.item_title[0] in 'aeiou'
                                      else 'a')
        amt_had_pluralizer = 's' if self.amount_had > 1 else ''
        return (f'You picked up {picked_up_indir_artcl_or_qty} {self.item_title}{picked_up_pluralizer}. You have '
                f'{amt_had_indir_artcl_or_qty} {self.item_title}{amt_had_pluralizer}.')

    def __init__(self, item_title, pick_up_amount, amount_had):
        self.item_title = item_title
        self.pick_up_amount = pick_up_amount
        self.amount_had = amount_had


class QuantityUnclear(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.pick_up_command() when the
player has entered an ungrammatical sentence that is ambiguous as to how
many it means to specify.
    """

    @property
    def message(self):
        return 'Amount to pick up unclear. How many do you mean?'

    def __init__(self):
        pass


class TryingToPickUpMoreThanIsPresent(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.pick_up_command() when
the player has targeted an item that is present, but has specified a
quantity to pick up that is greater than the number of that item that is
present in the current dungeon room.
    """

    __slots__ = 'item_title', 'amount_attempted', 'amount_present'

    @property
    def message(self):
        return f"You can't pick up {self.amount_attempted} {self.item_title}s. Only {self.amount_present} is here."

    def __init__(self, item_title, amount_attempted, amount_present):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_present = amount_present
