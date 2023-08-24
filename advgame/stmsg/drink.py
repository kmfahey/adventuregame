#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = ("DrankManaPotion", "DrankManaPotionWhenNotASpellcaster", "ItemNotDrinkable", "ItemNotInInventory", "TriedToDrinkMoreThanPossessed", "QuantityUnclear",)


class DrankManaPotion(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drink_coomand() when the
player uses it to drink a mana potion. It is only returned if the
player's character is a Mage or Priest. If they're playing a Warrior
or Thief, a Stmsg_Drink_DrankManaPotionWhenNotASpellcaster object is
returned instead.
    """
    __slots__ = 'amount_regained', 'current_mana_points', 'mana_point_total',

    @property
    def message(self):
        # This message property handles three cases:
        # * The player regained mana points and now has their maximum hit points.
        # * The player regained mana points but are still short of their maximum.
        # * The player didn't regain any mana points because their mana points were
        #   already at maximum.
        return_str = (f'You regained {self.amount_regained} mana points.' if self.amount_regained != 0
                      else "You didn't regain any mana points.")
        if self.current_mana_points == self.mana_point_total:
            return_str += ' You have full mana points!'
        return_str += f' Your mana points are {self.current_mana_points}/{self.mana_point_total}.'
        return return_str

    def __init__(self, amount_regained, current_mana_points, mana_point_total):
        self.amount_regained = amount_regained
        self.current_mana_points = current_mana_points
        self.mana_point_total = mana_point_total


class DrankManaPotionWhenNotASpellcaster(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drink_command() when the
player drinks a mana potion but they're playing a Warrior or Thief and
have no mana points to restore.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You feel a little strange, but otherwise nothing happens.'

    def __init__(self):
        pass


class ItemNotDrinkable(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drink_command() when the
player targets an item that is not a potion.
    """
    __slots__ = 'item_title',

    @property
    def message(self):
        return f'A {self.item_title} is not drinkable.'

    def __init__(self, item_title):
        self.item_title = item_title


class ItemNotInInventory(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drink_command() when the
player tries to drink a potion that isn't in their inventory.
    """
    __slots__ = 'item_title',

    @property
    def message(self):
        return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title):
        self.item_title = item_title


class TriedToDrinkMoreThanPossessed(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drink_command() when the
player specifies drinking a quantity of potions that is greater than the
number they have in their inventory.
    """
    __slots__ = 'item_title', 'attempted_qty', 'possessed_qty'

    @property
    def message(self):
        return f"You can't drink {self.attempted_qty} {self.item_title}s. You only have {self.possessed_qty} of them."

    def __init__(self, item_title, attempted_qty, possessed_qty):
        self.item_title = item_title
        self.attempted_qty = attempted_qty
        self.possessed_qty = possessed_qty


class QuantityUnclear(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.drink_command() when the
player writes an ungrammatical sentence that is ambiguous as to how many
of the item they intend to target.
    """

    @property
    def message(self):
        return 'Amount to drink unclear. How many do you mean?'

    def __init__(self):
        pass
