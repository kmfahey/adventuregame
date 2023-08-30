#!/usr/bin/python3

from math import floor
from random import randint

from .basics import State
from .items import Armor, Shield, Weapon, Wand, Item
from ..errors import InternalError


__all__ = (
    "ItemsState",
    "Equipment",
    "ItemsMultiState",
    "AbilityScores",
    "Character",
    "GameState",
)


class ItemsState(State):
    """
    A container object which stores Item objects (an abstract class).
    """

    # <<< HERE
    def __init__(self, **dict_of_dicts):
        """
        This __init__ method accepts a **dict-of-dicts -- such as offered by an
        IniConfig object's section attribute-- and uses Item.subclassing_factory
        to construct Item subclass objects from the internal dicts. Each one has
        the attribute internal_name set to the corresponding key from the outer
        dict.

        :**dict_of_dicts: A structure of internal name keys corresponding to
        dict values which are key-value pairs to initialize an individual Item
        subclass object with.
        """
        self._contents = dict()
        for item_internal_name, item_dict in dict_of_dicts.items():
            item = Item.subclassing_factory(
                internal_name=item_internal_name, **item_dict
            )
            self._contents[item_internal_name] = item


class Equipment:
    """
    This object represents the equipment held by a Character or Creature. It
    stores what items are equipped as the armor, shield, weapon or wand, and
    computes the derived values armor class, attack bonus and damage.
    """

    __slots__ = "character_class", "armor", "shield", "weapon", "wand"

    @property
    def armor_equipped(self):
        """
        This property returns the armor that is equipped, or None if none is
        equipped.

        :return: An Armor object, or None.
        """
        return getattr(self, "armor", None)

    @property
    def shield_equipped(self):
        """
        This property returns the shield that is equipped, or None if none is
        equipped.

        :return: A Shield object, or None.
        """
        return getattr(self, "shield", None)

    @property
    def weapon_equipped(self):
        """
        This property returns the weapon that is equipped, or None if none is
        equipped.

        :return: A Weapon object, or None.
        """
        return getattr(self, "weapon", None)

    @property
    def wand_equipped(self):
        """
        This property returns the wand that is equipped, or None if none is
        equipped.

        :return: A Wand object, or None.
        """
        return getattr(self, "wand", None)

    def __init__(
        self,
        character_class,
        armor_item=None,
        shield_item=None,
        weapon_item=None,
        wand_item=None,
    ):
        """
        This __init__ method instantiates the object with the given character
        class, and (optionally) armor, shield, weapon or wand items to equip.
        """
        self.character_class = character_class
        self.armor = armor_item
        self.shield = shield_item
        self.wand = wand_item
        self.weapon = weapon_item

    def equip_armor(self, item):
        """
        This method equips the given Armor object.

        :item: An Armor object.
        :returns: None.
        """
        if not isinstance(item, Armor):
            raise InternalError(
                "the method 'equip_armor()' only accepts 'armor' objects for "
                + "its argument"
            )
        self._equip("armor", item)

    def equip_shield(self, item):
        """
        This method equips the given Shield object.

        :item: A Shield object.
        :returns: None.
        """
        if not isinstance(item, Shield):
            raise InternalError(
                "the method 'equip_shield()' only accepts 'shield' objects "
                + "for its argument"
            )
        self._equip("shield", item)

    def equip_weapon(self, item):
        """
        This method equips the given Weapon object.

        :item: A Weapon object.
        :returns: None.
        """
        if not isinstance(item, Weapon):
            raise InternalError(
                "the method 'equip_weapon()' only accepts 'weapon' objects "
                + "for its argument"
            )
        self._equip("weapon", item)

    def equip_wand(self, item):
        """
        This method equips the given Wand object.

        :item: A Wand object.
        :returns: None.
        """
        if not isinstance(item, Wand):
            raise InternalError(
                "the method 'equip_wand()' only accepts 'wand' objects for "
                + "its argument"
            )
        self._equip("wand", item)

    def unequip_armor(self):
        """
        This method unequips the armor that is equipped.

        :return: None.
        """
        self._unequip("armor")

    def unequip_shield(self):
        """
        This method unequips the shield that is equipped.

        :return: None.
        """
        self._unequip("shield")

    def unequip_weapon(self):
        """
        This method unequips the weapon that is equipped.

        :return: None.
        """
        self._unequip("weapon")

    def unequip_wand(self):
        """
        This method unequips the wand that is equipped.

        :return: None.
        """
        self._unequip("wand")

    def _equip(self, equipment_slot, item):
        """
        This private method equips the given EquippableItem subclass object in
        the given slot.

        :equipment_slot: A string, one of 'armor', 'shield', 'weapon', or
        'wand'.
        :return: None.
        """
        if equipment_slot not in ("armor", "shield", "weapon", "wand"):
            raise InternalError(f"equipment slot {equipment_slot} not recognized")
        if equipment_slot == "armor":
            self.armor = item
        elif equipment_slot == "shield":
            self.shield = item
        elif equipment_slot == "weapon":
            self.weapon = item
        elif equipment_slot == "wand":
            self.wand = item

    def _unequip(self, equipment_slot):
        """
        This private method unequips the given EquippableItem subclass object.

        :equipment_slot: A string, one of 'armor', 'shield', 'weapon', or
        'wand'.
        :return: None.
        """
        if equipment_slot not in ("armor", "shield", "weapon", "wand"):
            raise InternalError(f"equipment slot {equipment_slot} not recognized")
        if equipment_slot == "armor":
            self.armor = None
        elif equipment_slot == "shield":
            self.shield = None
        elif equipment_slot == "weapon":
            self.weapon = None
        elif equipment_slot == "wand":
            self.wand = None

    @property
    def armor_class(self):
        """
        This method computes the armor class from the equipped Armor and Shield
        objects' armor bonuses if any.

        :return: An int.
        """
        ac = 10
        if self.armor_equipped:
            ac += self.armor.armor_bonus
        if self.shield_equipped:
            ac += self.shield.armor_bonus
        return ac

    @property
    def attack_bonus(self):
        """
        This method returns the attack bonus associated with any equipped weapon
        or wand.

        :return: An int.
        """
        if self.wand_equipped:
            return self.wand.attack_bonus
        elif self.weapon_equipped:
            return self.weapon.attack_bonus
        else:
            return None

    @property
    def damage(self):
        r"""
        This method returns the damage associated with any equipped weapon or
        wand.

        :return: A string of the form '\d+d\d+([+-]\d+)?'.
        """
        if self.wand_equipped:
            return self.wand.damage
        if self.weapon_equipped:
            return self.weapon.damage
        else:
            return None


class ItemsMultiState(ItemsState):
    """
    This subclass of ItemsState extends its functionality to track the
    quantity of each Item subclass object it contains.
    """

    def __init__(self, **argd):
        """
        The __init__ method of this class uses super() to call
        ItemsState.__init__() with the **dict-of-dicts argd. It then resets
        each key's value to a tuple of the quantity 1 and the Item subclass
        object. Quantities can be altered with subsequent method use but setting
        quantities above 1 in ItemsMultiState.__init__ is not supported.
        """
        super().__init__(**argd)

        # I preload the dict's items() sequence outside of the loop
        # because the loop alters the dict and I don't want a concurrent
        # update error.

        contents_items = tuple(self._contents.items())
        for item_internal_name, item in contents_items:
            self._contents[item_internal_name] = (1, item)

    def contains(self, item_internal_name):
        """
        This method tests whether an item object with the specified internal
        name is present in the private dictionary.

        :item_internal_name: The internal name of the Item subclass object.
        :return: A boolean.
        """
        return any(
            contained_item.internal_name == item_internal_name
            for _, contained_item in self._contents.values()
        )

    def set(self, item_internal_name, item_qty, item):
        """
        If an object with the given internal name is present in the internal
        dict, this accessor method returns a 2-tuple comprising an int of the
        item's quantity and the Item subclass object; otherwise the internal
        dict raises a KeyError.

        :item_internal_name: The internal name of the Item subclass object.
        :item_qty: An int value of the item quantity.
        :item: The Item subclass object.
        :return: None.
        """
        self._contents[item_internal_name] = item_qty, item

    def add_one(self, item_internal_name, item):
        """
        This method increases the quantity stored for the given Item subclass
        object by 1, if it's present. Otherwise, the Item is stored under the
        given internal name with a quantity of 1.

        :item_internal_name: The internal name of the Item subclass object.
        :item: The Item subclass object.
        :return: None.
        """
        if self.contains(item_internal_name):
            self._contents[item_internal_name] = (
                self._contents[item_internal_name][0] + 1,
                self._contents[item_internal_name][1],
            )
        else:
            self._contents[item_internal_name] = 1, item

    def remove_one(self, item_internal_name):
        """
        This method decreases the quantity stored for the given Item subclass
        object by 1, if it's present. If it's not present, a KeyError is raised.
        If the Item subclass object's stored quantity was 1, the object is
        deleted from the internal dictionary.

        :item_internal_name: The internal name of the Item subclass object.
        :return: None.
        """
        if item_internal_name not in self._contents:
            raise KeyError(item_internal_name)
        elif self._contents[item_internal_name][0] == 1:
            del self._contents[item_internal_name]
        else:
            self._contents[item_internal_name] = (
                self._contents[item_internal_name][0] - 1,
                self._contents[item_internal_name][1],
            )


class AbilityScores:
    """
    This class is one of the dependencies of the Character and Creature
    classes and is only used as a subordinate object to them. It abstracts
    the six ability scores of a Character or Creature and provides methods
    for using them.
    """

    __slots__ = (
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
        "character_class",
    )

    weightings = {
        "Warrior": (
            "strength",
            "constitution",
            "dexterity",
            "intelligence",
            "charisma",
            "wisdom",
        ),
        "Thief": (
            "dexterity",
            "constitution",
            "charisma",
            "strength",
            "wisdom",
            "intelligence",
        ),
        "Priest": (
            "wisdom",
            "strength",
            "constitution",
            "charisma",
            "intelligence",
            "dexterity",
        ),
        "Mage": (
            "intelligence",
            "dexterity",
            "constitution",
            "strength",
            "wisdom",
            "charisma",
        ),
    }

    @property
    def strength_mod(self):
        """
        This property computes the Strength modifier from the stored Strength
        score.

        :return: An int.
        """
        return self._stat_mod("strength")

    @property
    def dexterity_mod(self):
        """
        This property computes the Dexterity modifier from the stored Dexterity
        score.

        :return: An int.
        """
        return self._stat_mod("dexterity")

    @property
    def constitution_mod(self):
        """
        This property computes the Constitution modifier from the stored
        Constitution score.

        :return: An int.
        """
        return self._stat_mod("constitution")

    @property
    def intelligence_mod(self):
        """
        This property computes the Intelligence modifier from the stored
        Intelligence score.

        :return: An int.
        """
        return self._stat_mod("intelligence")

    @property
    def wisdom_mod(self):
        """
        This property computes the Wisdom modifier from the stored Wisdom score.

        :return: An int.
        """
        return self._stat_mod("wisdom")

    @property
    def charisma_mod(self):
        """
        This property computes the Charisma modifier from the stored Charisma
        score.

        :return: An int.
        """
        return self._stat_mod("charisma")

    # In modern D&D, the derived value from an ability score that
    # is relevant to determining outcomes is the 'stat mod' (or
    # 'stat modifier'), which is computed from the ability score
    # by subtracting 10, dividing by 2 and rounding down. That is
    # implemented here.

    def _stat_mod(self, ability_score):
        """
        This private method implements the ability score modifier equation for
        an arbitrary ability score.

        :ability_score: A string, one of 'Strength', 'Dexterity',
        'Constitution', 'Intelligence', 'Wisdom' or 'Charisma'.
        :return: An int.
        """
        if not hasattr(self, ability_score):
            raise InternalError(f"unrecognized ability {ability_score}")
        return floor((getattr(self, ability_score) - 10) / 2)

    def __init__(self, character_class_str):
        """
        This __init__ method instantiates the Character object from the given
        character class. When the ability scores are randomly generated, they
        will be assigned by order of priority as determined by the character
        class; each class has a different ability priority ordering.

        :character_class_str: One of 'Warrior', 'Thief', 'Priest' or 'Mage'.
        """
        if character_class_str not in self.weightings:
            raise InternalError(
                f"character class {character_class_str} not recognized, "
                + "should be one of 'Warrior', 'Thief', 'Priest' or 'Mage'"
            )
        self.character_class = character_class_str

    # Rolling a six-sided die 4 times and then dropping the lowest roll
    # before summing the remaining 3 results to reach a value for an
    # ability score (or 'stat') is the traditional method for generating
    # D&D ability scores. It is reproduced here.

    def roll_stats(self):
        """
        This method randomly generates the six ability scores and assigns them
        in priority order as dictated by the weightings. For each ability score,
        the roll of four 6-sided dice is simulated. The lowest roll is dropped
        and the remaining three are summed to yield an ability score value.

        :return: None.
        """
        results_list = list()
        for _ in range(0, 6):
            four_rolls = sorted([randint(1, 6) for _ in range(0, 4)])
            three_rolls = four_rolls[1:4]
            results_list.append(sum(three_rolls))
        results_list.sort()
        results_list.reverse()
        for index in range(0, 6):
            setattr(
                self, self.weightings[self.character_class][index], results_list[index]
            )


class Character:
    """
    This class represents a character. The player's interaction with the
    game rules environment during play is mediated by an instance of this
    class, which tracks their ability scores, equipment, hit points, mana
    points if a spellcaster, and inventory.
    """

    __slots__ = (
        "character_name",
        "character_class",
        "magic_key_stat",
        "_hit_point_maximum",
        "_current_hit_points",
        "_mana_point_maximum",
        "_current_mana_points",
        "ability_scores",
        "inventory",
        "_equipment",
    )

    # The rules for "mana" points I use in this class are drawn
    # from Dungeons & Dragons 3rd edition rules. In those rules
    # they"re called "spell points". These two dicts are drawn from
    # the variant Spell Points rules, which are available online at
    # <http://dndsrd.net/unearthedSpellPoints.html>

    _base_mana_points = {"Priest": 16, "Mage": 19}

    _bonus_mana_points = {-4: 0, -3: 0, -2: 0, -1: 0, 0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
    # End data from that page.

    # These defaults are adapted from D&D 3rd edition rules. This info
    # is generic and doesn't have a citation.

    _magic_key_stats = {"Priest": "wisdom", "Mage": "intelligence"}

    # End rules drawn from D&D.

    # These are arbitrary.

    _hitpoint_base = {"Warrior": 40, "Priest": 30, "Thief": 30, "Mage": 20}

    def __init__(
        self,
        character_name_str,
        character_class_str,
        base_hit_points=0,
        base_mana_points=0,
        magic_key_stat=None,
        strength=0,
        dexterity=0,
        constitution=0,
        intelligence=0,
        wisdom=0,
        charisma=0,
    ):
        """
        This __init__ method sets the character's name and class. It
        instantiates a subordinate AbilityScores object, and initialized it with
        the ability scores arguments (which does nothing if they are the default
        of zero). It instantiates the subordinate inventory ItemsMultiState()
        object and the subordinate Equipment object, and sets up the hit point
        and (optionally) mana point values. It also sets the magic key stat if
        any. | :character_name_str: A string, the name for the character.

        :character_class_str: A string one of 'Warrior', 'Thief', 'Priest', or
        'Mage'.
        :base_hit_points: An int, the character's base hit points (optional).
        :base_mana_points: An int, the character's base mana points (optional).
        :magic_key_stat: A string, the character's magic key stat (one of
        'Intelligence', 'Wisdom', or 'Charisma').
        :strength: An int, the set value for the character's Strength score
        (optional).
        :dexterity: An int, the set value for the character's Dexterity score
        (optional).
        :constitution: An int, the set value for the character's Constitution
        score (optional).
        :intelligence: An int, the set value for the character's Intelligence
        score (optional).
        :wisdom: An int, the set value for the character's Wisdom score
        (optional).
        :charisma: An int, the set value for the character's Charisma score
        (optional).
        """
        if character_class_str not in {"Warrior", "Thief", "Priest", "Mage"}:
            raise InternalError(
                f"character class argument {character_class_str} not one of "
                + "Warrior, Thief, Priest or Mage"
            )
        self.character_name = character_name_str
        self.character_class = character_class_str
        self.ability_scores = AbilityScores(character_class_str)

        # This step is refactored into a private method for readability.
        # All it does is set the ability scores if they're all nonzero.

        self._set_up_ability_scores(
            strength, dexterity, constitution, intelligence, wisdom, charisma
        )
        self.inventory = ItemsMultiState()
        self._equipment = Equipment(character_class_str)

        # This step is refactored into a private method for readability.
        # Its logic is fairly complex, q.v.

        self._set_up_hit_points_and_mana_points(
            base_hit_points, base_mana_points, magic_key_stat
        )

    def _set_up_ability_scores(
        self,
        strength=0,
        dexterity=0,
        constitution=0,
        intelligence=0,
        wisdom=0,
        charisma=0,
    ):
        """
        This private method sets the ability scores from its arguments if they
        are nonzero. It is used by __init__ to set ability scores from its
        arguments if furnished.

        :strength: An int, the set value for the character's Strength score
        (optional).
        :dexterity: An int, the set value for the character's Dexterity score
        (optional).
        :constitution: An int, the set value for the character's Constitution
        score (optional).
        :intelligence: An int, the set value for the character's Intelligence
        score (optional).
        :wisdom: An int, the set value for the character's Wisdom score
        (optional).
        :charisma: An int, the set value for the character's Charisma score
        (optional).
        """
        if all((strength, dexterity, constitution, intelligence, wisdom, charisma)):
            self.ability_scores.strength = strength
            self.ability_scores.dexterity = dexterity
            self.ability_scores.constitution = constitution
            self.ability_scores.intelligence = intelligence
            self.ability_scores.wisdom = wisdom
            self.ability_scores.charisma = charisma
        elif any((strength, dexterity, constitution, intelligence, wisdom, charisma)):
            raise InternalError(
                "The constructor for 'character' must be supplied with either "
                + "all of the arguments 'strength', 'dexterity', "
                + "'constitution', 'intelligence', 'wisdom', and 'charisma' "
                + "or none of them."
            )
        else:
            self.ability_scores.roll_stats()

    def _set_up_hit_points_and_mana_points(
        self, base_hit_points, base_mana_points, magic_key_stat
    ):
        """
        This private method sets up the Character object's hit points, and
        mana points if they're playing a spellcaster. Bonus hit points are
        calculated from the character's Constitution modifier. Bonus mana points
        are calculated from the specified magic key ability score (Intelligence
        for Mages, and Wisdom for Priests).

        :base_hit_points: An int, the character's base hit points.
        :base_mana_points: An int, the character's base mana points.
        :magic_key_stat: A string, the character's magic key stat (one of
        'Intelligence', 'Wisdom', or 'Charisma').
        :return: None.
        """

        # When the Character is instanced by a GameState object, none
        # of these values are supplied to __init__. But the Creature
        # object that subclasses Character draws its values from an .ini
        # entry, and it does have all these values supplied to __init__.
        #
        # Base hit points are taken either from an argument to __init__
        # or from the class's default in the _hitpoint_base dict.

        if base_hit_points:
            self._hit_point_maximum = self._current_hit_points = (
                base_hit_points + self.ability_scores.constitution_mod * 3
            )
        else:
            self._hit_point_maximum = self._current_hit_points = (
                self._hitpoint_base[self.character_class]
                + self.ability_scores.constitution_mod * 3
            )

        # Magic key stat can be set from the arguments to __init__ or
        # drawn from class defaults.

        if magic_key_stat:
            if magic_key_stat not in ("intelligence", "wisdom", "charisma"):
                raise InternalError(
                    f"`magic_key_stat` argument '{magic_key_stat}' not recognized"
                )
            self.magic_key_stat = magic_key_stat
        else:
            if self.character_class == "Priest":
                self.magic_key_stat = "wisdom"
            elif self.character_class == "Mage":
                self.magic_key_stat = "intelligence"
            else:
                self.magic_key_stat = ""
                self._mana_point_maximum = self._current_mana_points = 0
                return
        magic_key_stat_mod = getattr(self, self.magic_key_stat + "_mod", None)

        # These assignments add bonus mana points from the
        # _bonus_mana_points dict. A spellcaster with a high
        # spellcasting stat (16-18) can gain a lot of extra mana points.

        if base_mana_points:
            self._mana_point_maximum = self._current_mana_points = (
                base_mana_points + self._bonus_mana_points[magic_key_stat_mod]
            )
        elif self.character_class in self._base_mana_points:
            self._mana_point_maximum = self._current_mana_points = (
                self._base_mana_points[self.character_class]
                + self._bonus_mana_points[magic_key_stat_mod]
            )
        else:
            self._mana_point_maximum = self._current_mana_points = 0

    def _attack_or_damage_stat_dependency(self):
        """
        This private method is used by attack_roll(), attack_bonus() and
        damage() to determine which ability score modifier to add to attack
        and damage. It's Strength for Warriors, Priests, and Mages wielding a
        weapon; it's Dexterity for Thieves, and it's Intelligence for Mages
        wielding a wand.

        :return: A string, one of 'strength', 'dexterity', or 'intelligence'.
        """

        # The convention that a Mage using a spell add Intelligence
        # to their attack & damage is drawn from Dungeons & Dragons
        # 5th edition rules as laid out in the 5th edition _Player's
        # Handbook_.

        if self.character_class in ("Warrior", "Priest") or (
            self.character_class == "Mage" and self._equipment.weapon_equipped
        ):
            return "strength"
        elif self.character_class == "Thief":
            return "dexterity"
        else:
            # By exclusion, (`character_class` == "Mage" and
            # self._equipment.wand_equipped)
            return "intelligence"

    @property
    def _item_attacking_with(self):
        """
        This private property returns the wand object equipped if there is one,
        otherwise the weapon object equipped if there is one, otherwise None.

        :return: A Wand object, a Weapon object, or None.
        """
        if self._equipment.wand_equipped:
            return self._equipment.wand
        elif self._equipment.weapon_equipped:
            return self._equipment.weapon
        else:
            return None

    @property
    def hit_point_total(self):
        """
        This property returns the character's maximum hit points.

        :return: An int.
        """
        return self._hit_point_maximum

    @property
    def hit_points(self):
        """
        This property returns the character's current hit points.

        :return: An int.
        """
        return self._current_hit_points

    @property
    def mana_points(self):
        """
        This property returns the character's current mana points if any.

        :return: An int.
        """
        return self._current_mana_points

    @property
    def mana_point_total(self):
        """
        This property returns the character's maximum mana points if any.

        :return: An int.
        """
        return self._mana_point_maximum

    def take_damage(self, damage_value):
        """
        This method applies the given damage to the character's hit points.
        If the hit points would be reduced to less than 0, they are set to 0
        instead. The method returns the amount of damage assessed.

        :damage_value: An int, the number of hit points to lose.
        :return: An int.
        """
        if self._current_hit_points - damage_value < 0:
            taken_amount = self._current_hit_points
            self._current_hit_points = 0
            return taken_amount
        else:
            self._current_hit_points -= damage_value
            return damage_value

    def heal_damage(self, healing_value):
        """
        This method applies an amount of healing to the character's hit
        points. If the healing would increase the hit points to more than the
        character's maximum hit points, their hit point value is set to their
        hit point maximum instead. The method returns the amount of healing
        done.

        :healing_value: An int, the number of hit points to recover.
        :return: An int.
        """
        if self._current_hit_points + healing_value > self._hit_point_maximum:
            amount_healed = self._hit_point_maximum - self._current_hit_points
            self._current_hit_points = self._hit_point_maximum
            return amount_healed
        else:
            self._current_hit_points += healing_value
            return healing_value

    def spend_mana(self, spent_amount):
        """
        This method attempts to spend an amount of mana points from the
        character's mana points, returning the amount spent if successful. If
        the amount spent would reduce the character's mana points to less than
        zero, no spending takes place, and 0 is returned to indicate failure.

        :spent_amount: An int, the number of mana points to spend.
        :return: An int.
        """
        if self._current_mana_points < spent_amount:
            return 0
        else:
            self._current_mana_points -= spent_amount
            return spent_amount

    def regain_mana(self, regaining_value):
        """
        This method regains mana points by the given value. If the amount
        regained would increase the character's mana points to greater than
        their maximum mana point total, their current mana point value is set
        equal to their maximum mana point value instead. The method returns the
        amount of mana points regained.

        :regaining_value: An int, the number of mana points to regain.
        :return: An int.
        """
        if self._current_mana_points + regaining_value > self._mana_point_maximum:
            amount_regained = self._mana_point_maximum - self._current_mana_points
            self._current_mana_points = self._mana_point_maximum
            return amount_regained
        else:
            self._current_mana_points += regaining_value
            return regaining_value

    @property
    def is_alive(self):
        """
        This property returns True if the character's hit point total is greater
        than 0.

        :return: A boolean.
        """
        return self._current_hit_points > 0

    @property
    def is_dead(self):
        """
        This property returns True if the character's hit point total equals 0.

        :return: A boolean.
        """
        return self._current_hit_points == 0

    @property
    def attack_roll(self):
        r"""
        This property returns a dice expression usable by
        advgame.utilsities.roll_dice() to execute an attack roll during an
        ATTACK command. It calculates the attack bonus from the equipped item
        and the relevant ability score modifier.

        :return: A string of the form '\d+d\d+([+-]\d+)?'.
        """

        # This standard for formulating attack rolls is drawn from
        # Dungeons & Dragon 3rd edition. Those rules can be found at
        # <https://dndsrd.net/>.
        #
        # If no weapon or wand is equipped, None is returned.

        if not (self._equipment.weapon_equipped or self._equipment.wand_equipped):
            return None

        # The ability score can be strength, dexterity or intelligence,
        # depending on class. Its modifier is added to the attack roll.

        stat_dependency = self._attack_or_damage_stat_dependency()

        # The item attacking with can have a bonus to attack. That is
        # added to the attack roll.

        item_attacking_with = self._item_attacking_with
        stat_mod = getattr(self.ability_scores, stat_dependency + "_mod")
        total_mod = item_attacking_with.attack_bonus + stat_mod
        mod_str = (
            "+" + str(total_mod)
            if total_mod > 0
            else str(total_mod)
            if total_mod < 0
            else ""
        )

        # Attack rolls are resolved with a roll of a twenty-sided die.
        # .utils.roll_dice can interpret this return value into a
        # random number generation and execute it.

        return "1d20" + mod_str

    @property
    def damage_roll(self):
        r"""
        This property returns a dice expression usable by
        advgame.utilsities.roll_dice() to execute a damage roll during an ATTACK
        command. It calculates the damage dice value from the equipped wand or
        weapon, and the relevant ability score modifier.

        :return: A string of the form '\d+d\d+([+-]\d+)?'.
        """

        # This standard for formulating damage rolls is drawn from
        # Dungeons & Dragon 3rd edition. Those rules can be found at
        # <https://dndsrd.net/>.

        if not (self._equipment.weapon_equipped or self._equipment.wand_equipped):
            return None
        stat_dependency = self._attack_or_damage_stat_dependency()
        item_attacking_with = self._item_attacking_with
        item_dmg = item_attacking_with.damage

        # The item's damage is a die roll and an optional modifier. This
        # step splits that into the dice and the modifier.

        dmg_base_dice, dmg_mod = (
            item_dmg.split("+")
            if "+" in item_dmg
            else item_dmg.split("-")
            if "-" in item_dmg
            else (item_dmg, "0")
        )
        dmg_mod = int(dmg_mod)

        # The damage modifier needs to be adjusted by the stat mod from
        # above.

        total_dmg_mod = dmg_mod + getattr(self.ability_scores, stat_dependency + "_mod")
        dmg_str = dmg_base_dice + (
            "+" + str(total_dmg_mod)
            if total_dmg_mod > 0
            else str(total_dmg_mod)
            if total_dmg_mod < 0
            else ""
        )

        # The dice expression is reassembled with the changed modifier,
        # and returned.

        return dmg_str

    # This class keeps its `AbilityScores`, `Equipment` and
    # `ItemsMultiState` (Inventory) objects in private attributes,
    # just as a matter of good OOP design. In the cases of the
    # `AbilityScores` and `Equipment` objects, these passthrough
    # methods are necessary so the concealed objects' functionality can
    # be accessed from code that only has the `Character` object.
    #
    # The `ItemsMultiState` inventory object presents a customized
    # mapping interface that Character action management code doesn't
    # need to access, so only a few methods are offered.

    def pick_up_item(self, item, qty=1):
        """
        This method adds the given Item subclass object to the character's
        inventory in the quantity specified, default 1.

        :item: An Item subclass object.
        :qty: An int, the quantity to add to the container, default 1.
        :return: None.
        """
        have_qty = self.item_have_qty(item)
        if qty == 1:
            self.inventory.add_one(item.internal_name, item)
        else:
            self.inventory.set(item.internal_name, qty + have_qty, item)

    def drop_item(self, item, qty=1):
        """
        This method removes the specified quantity (default 1) of the given Item
        subclass object from the character's inventory.

        :item: An Item subclass object.
        :qty: An int, the quantity to remove from the container, default 1.
        :return: None.
        """
        have_qty = self.item_have_qty(item)
        if have_qty == 0:
            raise KeyError(item.internal_name)
        if have_qty == qty:
            self.inventory.delete(item.internal_name)
        else:
            self.inventory.set(item.internal_name, have_qty - qty, item)

    def item_have_qty(self, item):
        """
        This method checks whether the given Item subclass object is present in
        the character's inventory. If so, it returns the quantity possessed. If
        not, it returns 0.

        :item: An Item subclass object.
        :return: An int.
        """
        if not self.inventory.contains(item.internal_name):
            return 0
        else:
            have_qty, _ = self.inventory.get(item.internal_name)
            return have_qty

    def have_item(self, item):
        """
        This method checks whether the given Item subclass object is present in
        the character's inventory. It returns True or False.

        :item: An Item subclass object.
        :return: A boolean.
        """
        return self.inventory.contains(item.internal_name)

    def list_items(self):
        """
        This method returns a sorted list of 2-tuples comprising an integer item
        quantity and an Item subclass object. The list is ordered alphabetically
        by the Item subclass object's title attributes.

        :return: A list of 2-tuples.
        """
        return list(sorted(self.inventory.values(), key=lambda *argl: argl[0][1].title))

    # BEGIN passthrough methods for private AbilityScores
    @property
    def strength(self):
        """
        This property returns the value for the Strength score stored in the
        subordinate AbilityScores object.

        :return: An int.
        """
        return getattr(self.ability_scores, "strength")

    @property
    def dexterity(self):
        """
        This property returns the value for the Dexterity score stored in the
        subordinate AbilityScores object.

        :return: An int.
        """
        return getattr(self.ability_scores, "dexterity")

    @property
    def constitution(self):
        """
        This property returns the value for the Constitution score stored in the
        subordinate AbilityScores object.

        :return: An int.
        """
        return getattr(self.ability_scores, "constitution")

    @property
    def intelligence(self):
        """
        This property returns the value for the Intelligence score stored in the
        subordinate AbilityScores object.

        :return: An int.
        """
        return getattr(self.ability_scores, "intelligence")

    @property
    def wisdom(self):
        """
        This property returns the value for the Wisdom score stored in the
        subordinate AbilityScores object.

        :return: An int.
        """
        return getattr(self.ability_scores, "wisdom")

    @property
    def charisma(self):
        """
        This property returns the value for the Charisma score stored in the
        subordinate AbilityScores object.

        :return: An int.
        """
        return getattr(self.ability_scores, "charisma")

    @property
    def strength_mod(self):
        """
        This property returns the Strength ability score modifier from the
        subordinate AbilityScores object.

        :return: An int.
        """
        return self.ability_scores._stat_mod("strength")

    @property
    def dexterity_mod(self):
        """
        This property returns the Dexterity ability score modifier from the
        subordinate AbilityScores object.

        :return: An int.
        """
        return self.ability_scores._stat_mod("dexterity")

    @property
    def constitution_mod(self):
        """
        This property returns the Constitution ability score modifier from the
        subordinate AbilityScores object.

        :return: An int.
        """
        return self.ability_scores._stat_mod("constitution")

    @property
    def intelligence_mod(self):
        """
        This property returns the Intelligence ability score modifier from the
        subordinate AbilityScores object.

        :return: An int.
        """
        return self.ability_scores._stat_mod("intelligence")

    @property
    def wisdom_mod(self):
        """
        This property returns the Wisdom ability score modifier from the
        subordinate AbilityScores object.

        :return: An int.
        """
        return self.ability_scores._stat_mod("wisdom")

    @property
    def charisma_mod(self):
        """
        This property returns the Charisma ability score modifier from the
        subordinate AbilityScores object.

        :return: An int.
        """
        return self.ability_scores._stat_mod("charisma")

    # END passthrough methods for private AbilityScores

    # BEGIN passthrough methods for private _equipment
    @property
    def armor_equipped(self):
        """
        This property returns the armor_equipped property from the subordinate
        Equipment object.

        :return: An Armor object, or None.
        """
        return self._equipment.armor_equipped

    @property
    def shield_equipped(self):
        """
        This property returns the shield_equipped property from the subordinate
        Equipment object.

        :return: A Shield object, or None.
        """
        return self._equipment.shield_equipped

    @property
    def weapon_equipped(self):
        """
        This property returns the weapon_equipped property from the subordinate
        Equipment object.

        :return: A Weapon object, or None.
        """
        return self._equipment.weapon_equipped

    @property
    def wand_equipped(self):
        """
        This property returns the wand_equipped property from the subordinate
        Equipment object.

        :return: A Wand object, or None.
        """
        return self._equipment.wand_equipped

    @property
    def armor(self):
        """
        This property returns the armor property from the subordinate Equipment
        object.

        :return: An Armor object, or None.
        """
        return self._equipment.armor

    @property
    def shield(self):
        """
        This property returns the shield property from the subordinate Equipment
        object.

        :return: A Shield object, or None.
        """
        return self._equipment.shield

    @property
    def weapon(self):
        """
        This property returns the weapon property from the subordinate Equipment
        object.

        :return: A Weapon object, or None.
        """
        return self._equipment.weapon

    @property
    def wand(self):
        """
        This property returns the wand property from the subordinate Equipment
        object.

        :return: A Wand object, or None.
        """
        return self._equipment.wand

    def equip_armor(self, item):
        """
        This method calls the equip_armor method on the subordinate Equipment
        object with the given argument.

        :item: An Armor object.
        :return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise InternalError(
                "equipping an `item` object that is not in the character's "
                + "`inventory` object is not allowed"
            )
        return self._equipment.equip_armor(item)

    def equip_shield(self, item):
        """
        This method calls the equip_shield method on the subordinate Equipment
        object with the given argument.

        :item: A Shield object.
        :return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise InternalError(
                "equipping an `item` object that is not in the character's "
                + "`inventory` object is not allowed"
            )
        return self._equipment.equip_shield(item)

    def equip_weapon(self, item):
        """
        This method calls the equip_weapon method on the subordinate Equipment
        object with the given argument.

        :item: A Weapon object.
        :return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise InternalError(
                "equipping an `item` object that is not in the character's "
                + "`inventory` object is not allowed"
            )
        return self._equipment.equip_weapon(item)

    def equip_wand(self, item):
        """
        This method calls the equip_wand method on the subordinate Equipment
        object with the given argument.

        :item: A Wand object.
        :return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise InternalError(
                "equipping an `item` object that is not in the character's "
                + "`inventory` object is not allowed"
            )
        return self._equipment.equip_wand(item)

    def unequip_armor(self):
        """
        This method calls the unequip_armor method on the subordinate Equipment
        object.

        :return: None.
        """
        return self._equipment.unequip_armor()

    def unequip_shield(self):
        """
        This method calls the unequip_shield method on the subordinate Equipment
        object.

        :return: None.
        """
        return self._equipment.unequip_shield()

    def unequip_weapon(self):
        """
        This method calls the unequip_weapon method on the subordinate Equipment
        object.

        :return: None.
        """
        return self._equipment.unequip_weapon()

    def unequip_wand(self):
        """
        This method calls the unequip_wand method on the subordinate Equipment
        object.

        :return: None.
        """
        return self._equipment.unequip_wand()

    # END passthrough methods for private _equipment

    # These aren't passthrough methods because the `_equipment` returns
    # values for these Character parameters that are informed only by
    # the Equipment it stores. At the level of the `Character` object,
    # these values should also be informed by the character's ability
    # scores stores in the `AbilityScores`. A character's armor class
    # is modified by their dexterity modifier; and their attack & damage
    # values are modified by either their strength score (for Warriors,
    # Priests, and Mages using a Weapon), or Dexterity (for Thieves), or
    # Intelligence (for Mages using a Wand).

    @property
    def armor_class(self):
        """
        This property returns the character's ability score as computed from
        their equipments' armor bonuses and their Dexterity modifier.

        :return: An int.
        """
        armor_class = self._equipment.armor_class
        dexterity_mod = self.ability_scores.dexterity_mod
        return armor_class + dexterity_mod

    @property
    def attack_bonus(self):
        """
        This property returns the character's attack bonus as computed from
        their weapon or wand's attack bonus and their relevant ability score
        modifier (Strength for Warriors, Priests and Mages wielding a weapon;
        Dexterity for Thieves; and Intelligence for Mages wielding a wand).

        :return: An int.
        """

        # A character with no weapon or wand has no attack bonus.

        if not (
            self._equipment.weapon_equipped
            or self.character_class == "Mage"
            and self._equipment.wand_equipped
        ):
            raise InternalError(
                "The character does not have a weapon equipped; no valid "
                + "value for `attack_bonus` can be computed."
            )
        stat_dependency = self._attack_or_damage_stat_dependency()

        # By the shield statement above, I know that the control flow
        # getting here means that if no weapon is equipped a wand must
        # be.

        if self.character_class == "Mage":
            base_attack_bonus = (
                self._equipment.wand.attack_bonus
                if self._equipment.wand_equipped
                else self._equipment.weapon.attack_bonus
            )
        else:
            base_attack_bonus = self._equipment.weapon.attack_bonus

        # The attack bonus is drawn from the weapon or wand's attack
        # bonus plus the relevant stat mod.

        return base_attack_bonus + getattr(
            self.ability_scores, stat_dependency + "_mod"
        )


class GameState:
    """
    This class represents the entire GameState needed to run a session
    of AdventureGame. It is the top-level object, and stores an
    items_state object, a doors_state object, a containers_state object,
    a creatures_state object, a rooms_state object, and (once it can be
    instantiated) a character object.
    """

    __slots__ = (
        "_character_name",
        "_character_class",
        "character",
        "rooms_state",
        "containers_state",
        "doors_state",
        "items_state",
        "creatures_state",
        "game_has_begun",
        "game_has_ended",
    )

    @property
    def character_name(self):
        """
        This property returns the character name.

        :return: A string.
        """
        return self._character_name

    @character_name.setter
    def character_name(self, name_str):
        """
        This property sets the character name, and contains a hook to attempt to
        instantiate the character object if both the name and class have been
        set.

        :name_str: A string, the character name.
        :return: None.
        """
        setattr(self, "_character_name", name_str)
        self._incept_character_obj_if_possible()

    @property
    def character_class(self):
        """
        This property returns the character class.

        :return: A string, one of 'Warrior', 'Thief', 'Mage', or 'Priest'.
        """
        return self._character_class

    @character_class.setter
    def character_class(self, class_str):
        """
        This property sets the character class, and contains a hook to attempt
        to instantiate the character object if both the name and class have been
        set.

        :name_str: A string, the character class.
        :return: None.
        """
        setattr(self, "_character_class", class_str)
        self._incept_character_obj_if_possible()

    def __init__(
        self, rooms_state, creatures_state, containers_state, doors_state, items_state
    ):
        """
        This __init__ method stores an items_state object, a doors_state object,
        a containers_state object, a creatures_state object, and a rooms_state
        object from its arguments.

        :rooms_state: A RoomsState object.
        :creatures_state: A CreaturesState object.
        :containers_state: A ContainersState object.
        :doors_state: A DoorsState object.
        :items_state: An ItemsState object.
        """
        self.items_state = items_state
        self.doors_state = doors_state
        self.containers_state = containers_state
        self.creatures_state = creatures_state
        self.rooms_state = rooms_state
        self._character_name = None
        self._character_class = None
        self.game_has_begun = False
        self.game_has_ended = False
        self.character = None

    # The Character object can't be instantiated until the
    # `character_name` and `character_class` attributes are set, but
    # that happens after initialization; so the `character_name` and
    # `character_class` setters call this method prospectively each time
    # either is called to check if both have been set and `Character`
    # object instantiation can proceed.

    def _incept_character_obj_if_possible(self):
        """
        This private method is called by the character_name and character_class
        property setters, and it instantiates the Character object if both the
        character name and the character class have been set.

        :return: None.
        """
        if (
            self.character is None
            and getattr(self, "character_name", None)
            and getattr(self, "character_class", None)
        ):
            self.character = Character(self.character_name, self.character_class)
