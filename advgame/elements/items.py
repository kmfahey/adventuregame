#!/usr/bin/python3

from advgame.elements.basics import IniEntry
from advgame.errors import InternalError


__all__ = (
    "Item",
    "EquippableItem",
    "Oddment",
    "Key",
    "Potion",
    "Coin",
    "Wand",
    "Weapon",
    "Shield",
    "Armor",
)


class Item(IniEntry):
    """A single item, taken from .ini format."""

    __slots__ = (
        "internal_name",
        "title",
        "description",
        "weight",
        "value",
        "damage",
        "attack_bonus",
        "armor_bonus",
        "item_type",
        "warrior_can_use",
        "thief_can_use",
        "priest_can_use",
        "mage_can_use",
        "hit_points_recovered",
        "mana_points_recovered",
    )

    def __init__(self, **argd):
        """Instance the item for arbitrary key-value pairs."""
        super().__init__(**argd)
        self._post_init_slots_set_none(self.__slots__)

    @classmethod
    def subclassing_factory(cls, **item_dict):
        """
        Instance an arbitrary subclass from arguments based on the value of the
        item_type key.

        :**item_dict: A dictionary of key-value pairs to instantiate the Item
        subclass object with.
        :return: An Item subclass object.
        """
        if item_dict["item_type"] == "armor":
            item = Armor(**item_dict)
        elif item_dict["item_type"] == "coin":
            item = Coin(**item_dict)
        elif item_dict["item_type"] == "potion":
            item = Potion(**item_dict)
        elif item_dict["item_type"] == "key":
            item = Key(**item_dict)
        elif item_dict["item_type"] == "shield":
            item = Shield(**item_dict)
        elif item_dict["item_type"] == "wand":
            item = Wand(**item_dict)
        elif item_dict["item_type"] == "weapon":
            item = Weapon(**item_dict)
        elif item_dict["item_type"] == "oddment":
            item = Oddment(**item_dict)
        else:
            raise InternalError(
                "couldn't instance Item subclass, unrecognized item type "
                + f"'{item_dict['item_type']}'."
            )
        return item


class EquippableItem(Item):
    def usable_by(self, character_class):
        """
        An item equippable by some classes and not by others, based on the
        'warrior_can_use', 'thief_can_use', 'mage_can_use', or 'priest_can_use'
        attributes.

        :character_class: Either 'Warrior', 'Thief', 'Mage', or 'Priest'.
        :return: A boolean.
        """
        if character_class not in ("Warrior", "Thief", "Mage", "Priest"):
            raise InternalError(f"character class {character_class} not recognized")
        return bool(getattr(self, character_class.lower() + "_can_use", None))


# The subclasses don't have much differing functionality but accurately
# typing each Item allows classes that handle items of specific types,
# like Equipment(), to use type testing to determine if a valid Item has
# been supplied as an argument.


class Oddment(Item):
    """A miscellaneous good with no in-game purpose."""

    pass


class Key(Item):
    """A key, which can be used to unlock doors."""

    pass


class Potion(Item):
    """A potion, which is drinkable."""

    pass


class Coin(Item):
    """A coin, i.e. a unit of value."""

    pass


class Wand(EquippableItem):
    """A wand, which can be equipped and used by mages to do damage"""

    pass


class Weapon(EquippableItem):
    """A weapon, which can be equipped, and wielded to do damage."""

    pass


class Shield(EquippableItem):
    """A shield, which can be equipped, to raise armor class."""

    pass


class Armor(EquippableItem):
    """A suit of armor, which can be equipped, to raise armor class."""

    pass
