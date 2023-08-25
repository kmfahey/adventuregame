#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("DroppedItem", "QuantityUnclear", "TryingToDropItemYouDontHave", "TryingToDropMoreThanYouHave",)


class DroppedItem(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drop_command() when the
player successfully drops an item on the floor.
    """

    __slots__ = ('item_title', 'item_type', 'amount_dropped',
                 'amount_on_floor', 'amount_left')

    @property
    def message(self):
        # This message property handles assembling a string that informs
        # the player how many of the item they dropped (always nonzero),
        # how many are on the floor now (always nonzero), and how many
        # of the item they have left (may be zero).
        #
        # Armor is handled specially because the proper way to refer to
        # a singular armor piece isn't "a studded leather armor" but "a
        # suit of studded leather armor'.
        drop_qty_or_ind_artcl = (f'{self.amount_dropped} ' if self.amount_on_floor > 1
                                 else 'a suit of ' if self.item_type == 'armor'
                                 else 'an ' if self.item_title[0] in 'aeiou'
                                 else 'a ')
        floor_qty_or_ind_artcl = (f'{self.amount_on_floor} ' if self.amount_on_floor > 1
                                  else 'a suit of ' if self.item_type == 'armor'
                                  else 'an ' if self.item_title[0] in 'aeiou' else 'a ')
        # The *_pluralizer strings are appended to the item titles, and
        # are 's' if the item qty is more than 1, or '' if the item qty
        # is 1.
        drop_qty_pluralizer = '' if self.amount_dropped == 1 else 's'
        floor_qty_pluralizer = '' if self.amount_on_floor == 1 else 's'

        # The amount dropped and the amount on the floor both must be
        # nonzero, but the amount left may be zero. If the player has
        # none of the item left, this isn't used.
        left_qty_plr_or_sing_term = (
                f'suits of {self.item_title}' if self.item_type == 'armor'
                else f'{self.item_title}s' if self.amount_left != 1
                else self.item_title)
        if self.amount_left >= 1:
            return (f'You dropped {drop_qty_or_ind_artcl}{self.item_title}{drop_qty_pluralizer}. You see '
                    + f'{floor_qty_or_ind_artcl}{self.item_title}{floor_qty_pluralizer} here. You have '
                    + f'{self.amount_left} {left_qty_plr_or_sing_term} left.')
        else:
            return (f'You dropped {drop_qty_or_ind_artcl}{self.item_title}{drop_qty_pluralizer}. You see '
                    + f'{floor_qty_or_ind_artcl}{self.item_title}{floor_qty_pluralizer} here. You have no '
                    + f'{left_qty_plr_or_sing_term} left.')

    def __init__(self, item_title, item_type, amount_dropped, amount_on_floor,
                 amount_left):
        self.item_title = item_title
        self.item_type = item_type
        self.amount_dropped = amount_dropped
        self.amount_on_floor = amount_on_floor
        self.amount_left = amount_left


class QuantityUnclear(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drop_command() when the
player writes an ungrammatical sentence that is ambiguous as to how many
of the item they intend to target.
    """

    @property
    def message(self):
        return 'Amount to drop unclear. How many do you mean?'

    def __init__(self):
        pass


class TryingToDropItemYouDontHave(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drop_command() when the
player specifies an item to drop that is not in their inventory.
    """

    __slots__ = 'item_title', 'amount_attempted'

    @property
    def message(self):
        # This message property assembles a string informing the player
        # they don't have the item in their inventory, hanlding both the
        # singular and the plural cases.
        article_or_pronoun = ('any' if self.amount_attempted > 1
                              else 'an' if self.item_title[0] in 'aeiou'
                              else 'a')
        pluralizer = '' if self.amount_attempted == 1 else 's'
        return (f"You don't have {article_or_pronoun} "
                + f"{self.item_title}{pluralizer} in your inventory.")

    def __init__(self, item_title, amount_attempted):
        self.item_title = item_title
        self.amount_attempted = amount_attempted


class TryingToDropMoreThanYouHave(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drop_command() when the
player specifies a quantity of a certain item to drop that is more than
the quantity of that item that they actually possess.
    """

    __slots__ = 'item_title', 'amount_attempted', 'amount_had'

    @property
    def message(self):
        # This message assumes the quantity the player attempted to drop
        # is greater than 1. They're getting this message because they
        # tried to drop a quantity of the item greater than the quantity
        # they possess; but they must possess at least 1 to get this
        # message, so the quantity they tried to drop must be more than
        # that.
        pluralizer = '' if self.amount_had == 1 else 's'
        return (f"You can't drop {self.amount_attempted} {self.item_title}s. "
                + f"You only have {self.amount_had} "
                + f'{self.item_title}{pluralizer} in your inventory.')

    def __init__(self, item_title, amount_attempted, amount_had):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_had = amount_had
