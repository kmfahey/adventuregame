#!/usr/bin/python3

import abc
import collections
import math
import random
import re

from adventuregame.utility import isfloat, Bad_Command_Exception, Internal_Exception

__name__ = 'adventuregame.elements'


class Ini_Entry(object):

    inventory_list_value_re = re.compile(r"""^\[(
                                                    (
                                                        [1-9][0-9]*
                                                        x
                                                        [A-Z][A-Za-z_]+
                                                    )(,
                                                        [1-9][0-9]*
                                                        x
                                                        [A-Z][A-Za-z_]+
                                                    )*
                                                )\]$""", re.X)

    def __init__(self, **argd):
        for Key, value in argd.items():
            if isinstance(value, str):
                if value.lower() == 'false':
                    value = False
                elif value.lower() == 'true':
                    value = True
                elif value.isdigit():
                    value = int(value)
                elif isfloat(value):
                    value = float(value)
            setattr(self, Key, value)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in self.__slots__)

    def _post_init_slots_set_none(self, slots):
        for Key in slots:
            if not hasattr(self, Key):
                setattr(self, Key, None)

    def _process_list_value(self, inventory_value):
        value_match = self.inventory_list_value_re.match(inventory_value)
        inner_capture = value_match.groups(1)[0]
        capture_split = inner_capture.split(',')
        qty_strval_pairs = tuple((int(item_qty), item_name) for item_qty, item_name in (
                                    name_x_qty_str.split('x', maxsplit=1) for name_x_qty_str in capture_split))
        return qty_strval_pairs


class State(abc.ABC):
    __slots__ = '_contents',

    __abstractmethods__ = frozenset(('__init__',))

    def contains(self, item_internal_name):  # check
        return any(item_internal_name == contained_item.internal_name
                   for contained_item in self._contents.values())

    def get(self, item_internal_name):  # check
        return self._contents[item_internal_name]

    def set(self, item_internal_name, item):  # check
        self._contents[item_internal_name] = item

    def delete(self, item_internal_name):  # check
        del self._contents[item_internal_name]

    def keys(self):  # check
        return self._contents.keys()

    def values(self):  # check
        return self._contents.values()

    def items(self):  # check
        return self._contents.items()

    def size(self):  # check
        return len(self._contents)


class Items_State(State):  # has been tested

    def __init__(self, **dict_of_dicts):
        self._contents = dict()
        for item_internal_name, item_dict in dict_of_dicts.items():
            item = Item.subclassing_factory(internal_name=item_internal_name, **item_dict)
            self._contents[item_internal_name] = item


class Items_Multi_State(Items_State):

    def __init__(self, **argd):
        Items_State.__init__(self, **argd)

        # I preload the dict's items() sequence outside of the loop because the loop alters the dict and I don't want a
        # concurrent update error.
        contents_items = tuple(self._contents.items())
        for item_internal_name, item in contents_items:
            self._contents[item_internal_name] = (1, item)

    def contains(self, item_internal_name):
        return(any(contained_item.internal_name == item_internal_name
                   for _, contained_item in self._contents.values()))

    def set(self, item_internal_name, item_qty, item):
        self._contents[item_internal_name] = item_qty, item

    def add_one(self, item_internal_name, item):
        if self.contains(item_internal_name):
            self._contents[item_internal_name] = (self._contents[item_internal_name][0] + 1,
                                                  self._contents[item_internal_name][1])
        else:
            self._contents[item_internal_name] = 1, item

    def remove_one(self, item_internal_name):
        if item_internal_name not in self._contents:
            raise KeyError(item_internal_name)
        elif self._contents[item_internal_name][0] == 1:
            del self._contents[item_internal_name]
        else:
            self._contents[item_internal_name] = (self._contents[item_internal_name][0] - 1,
                                                  self._contents[item_internal_name][1])


# This class doesn't subclass `State` because it re-implements every method.

class Doors_State(object):

    def __init__(self, **dict_of_dicts):
        self._contents = collections.defaultdict(dict)
        for door_internal_name, door_argd in dict_of_dicts.items():
            first_room_internal_name, second_room_internal_name = door_internal_name.split('_x_')
            self._contents[first_room_internal_name][second_room_internal_name] = \
                Door.subclassing_factory(internal_name=door_internal_name, **door_argd)
            pass

    def contains(self, first_room_internal_name, second_room_internal_name):  # tested
        return (first_room_internal_name in self._contents
                and second_room_internal_name in self._contents[first_room_internal_name])

    def get(self, first_room_internal_name, second_room_internal_name):  # tested
        return self._contents[first_room_internal_name][second_room_internal_name]

    def set(self, first_room_internal_name, second_room_internal_name, door):
        self._contents[first_room_internal_name][second_room_internal_name] = door

    def delete(self, first_room_internal_name, second_room_internal_name):  # tested
        del self._contents[first_room_internal_name][second_room_internal_name]

    def keys(self):  # tested
        keys_list = list()
        for first_room_name in self._contents.keys():
            for second_room_name in self._contents[first_room_name].keys():
                keys_list.append((first_room_name, second_room_name))
        return keys_list

    def values(self):  # tested
        values_list = list()
        for first_room_name in self._contents.keys():
            values_list.extend(self._contents[first_room_name].values())
        return values_list

    def items(self):  # tested
        items_list = list()
        for first_room_name in self._contents.keys():
            for second_room_name, door in self._contents[first_room_name].items():
                items_list.append((first_room_name, second_room_name, door))
        return items_list

    def size(self):  # tested
        return len(self.keys())


class Inventory(Items_Multi_State):  # has been tested

    LIGHT = 0
    MEDIUM = 1
    HEAVY = 2
    IMMOBILIZING = 3

    _carry_weight = {
        3:  {LIGHT: (0, 10),    MEDIUM: (11, 20),   HEAVY: (21, 30)},
        4:  {LIGHT: (0, 13),    MEDIUM: (14, 26),   HEAVY: (27, 40)},
        5:  {LIGHT: (0, 16),    MEDIUM: (17, 33),   HEAVY: (34, 50)},
        6:  {LIGHT: (0, 20),    MEDIUM: (21, 40),   HEAVY: (41, 60)},
        7:  {LIGHT: (0, 23),    MEDIUM: (24, 46),   HEAVY: (47, 70)},
        8:  {LIGHT: (0, 26),    MEDIUM: (27, 53),   HEAVY: (54, 80)},
        9:  {LIGHT: (0, 30),    MEDIUM: (31, 60),   HEAVY: (61, 90)},
        10: {LIGHT: (0, 33),    MEDIUM: (34, 66),   HEAVY: (67, 100)},
        11: {LIGHT: (0, 38),    MEDIUM: (39, 76),   HEAVY: (77, 115)},
        12: {LIGHT: (0, 43),    MEDIUM: (44, 86),   HEAVY: (87, 130)},
        13: {LIGHT: (0, 50),    MEDIUM: (51, 100),  HEAVY: (101, 150)},
        14: {LIGHT: (0, 58),    MEDIUM: (59, 116),  HEAVY: (117, 175)},
        15: {LIGHT: (0, 66),    MEDIUM: (67, 133),  HEAVY: (134, 200)},
        16: {LIGHT: (0, 76),    MEDIUM: (77, 153),  HEAVY: (154, 230)},
        17: {LIGHT: (0, 86),    MEDIUM: (87, 173),  HEAVY: (174, 260)},
        18: {LIGHT: (0, 100),   MEDIUM: (101, 200), HEAVY: (201, 300)}
    }

    def __init__(self, **dict_of_dicts):
        super().__init__(**dict_of_dicts)

    @property
    def total_weight(self):
        total_weight_val = 0
        for item_name, (item_count, item) in self._contents.items():
            if item.weight <= 0:
                raise Internal_Exception('item ' + item.internal_name
                                         + ' has invalid weight ' + str(item.weight) + ': is <= 0')
            elif item_count <= 0:
                raise Internal_Exception('item ' + item.internal_name + ' is stored with invalid count '
                                         + str(item_count) + ': is <= 0')
            total_weight_val += item.weight * item_count
        return total_weight_val

    def burden_for_strength_score(self, strength_score):
        total_weight_val = self.total_weight
        if total_weight_val < 0:
            raise Internal_Exception('the `total_weight` value for this inventory equals a negative number')
        light_burden_lower_bound = self._carry_weight[strength_score][self.LIGHT][0]
        light_burden_upper_bound = self._carry_weight[strength_score][self.LIGHT][1]
        medium_burden_lower_bound = self._carry_weight[strength_score][self.MEDIUM][0]
        medium_burden_upper_bound = self._carry_weight[strength_score][self.MEDIUM][1]
        heavy_burden_lower_bound = self._carry_weight[strength_score][self.HEAVY][0]
        heavy_burden_upper_bound = self._carry_weight[strength_score][self.HEAVY][1]
        if light_burden_lower_bound <= total_weight_val <= light_burden_upper_bound:
            return self.LIGHT
        elif medium_burden_lower_bound <= total_weight_val <= medium_burden_upper_bound:
            return self.MEDIUM
        elif heavy_burden_lower_bound <= total_weight_val <= heavy_burden_upper_bound:
            return self.HEAVY
        else:
            return self.IMMOBILIZING


class Character(object):  # has been tested
    __slots__ = ('character_name', 'character_class', 'magic_key_stat', '_hit_point_maximum', '_current_hit_points',
                 '_mana_point_maximum', '_current_mana_points', 'ability_scores', 'inventory',
                 '_equipment')

    _base_mana_points = {'Priest': 16, 'Mage': 19}

    _bonus_mana_points = {-4: 0, -3: 0, -2: 0, -1: 0, 0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

    _hitpoint_base = {'Warrior': 40, 'Priest': 30, 'Thief': 30, 'Mage': 20}

    def __init__(self, character_name_str, character_class_str, base_hit_points=0, base_mana_points=0,
                 magic_key_stat=None, strength=0, dexterity=0, constitution=0, intelligence=0, wisdom=0, charisma=0):
        if character_class_str not in {'Warrior', 'Thief', 'Priest', 'Mage'}:
            raise Internal_Exception(f'character class argument {character_class_str} not one of '
                                     'Warrior, Thief, Priest or Mage')
        self.character_name = character_name_str
        self.character_class = character_class_str
        self.ability_scores = Ability_Scores(character_class_str)
        self._set_up_ability_scores(strength, dexterity, constitution, intelligence, wisdom, charisma)
        self.inventory = Inventory()
        self._equipment = Equipment(character_class_str)
        self._set_up_hit_points_and_mana_points(base_hit_points, base_mana_points, magic_key_stat)

    def _set_up_ability_scores(self, strength=0, dexterity=0, constitution=0, intelligence=0, wisdom=0, charisma=0):
        if all((strength, dexterity, constitution, intelligence, wisdom, charisma)):
            self.ability_scores.strength = strength
            self.ability_scores.dexterity = dexterity
            self.ability_scores.constitution = constitution
            self.ability_scores.intelligence = intelligence
            self.ability_scores.wisdom = wisdom
            self.ability_scores.charisma = charisma
        elif any((strength, dexterity, constitution, intelligence, wisdom, charisma)):
            raise Internal_Exception('The constructor for `character` must be supplied with either all of the arguments'
                                     ' `strength`, `dexterity`, `constitution`, `intelligence`, `wisdom`, and '
                                     '`charisma` or none of them.')
        else:
            self.ability_scores.roll_stats()

    def _set_up_hit_points_and_mana_points(self, base_hit_points, base_mana_points, magic_key_stat):
        if base_hit_points:
            self._hit_point_maximum = self._current_hit_points = (base_hit_points +
                                                                  self.ability_scores.constitution_mod * 3)
        else:
            self._hit_point_maximum = self._current_hit_points = (self._hitpoint_base[self.character_class]
                                                                  + self.ability_scores.constitution_mod * 3)
        if magic_key_stat:
            if magic_key_stat not in ('intelligence', 'wisdom', 'charisma'):
                raise Internal_Exception("`magic_key_stat` argument '" + magic_key_stat + "' not recognized")
            self.magic_key_stat = magic_key_stat
        else:
            if self.character_class == 'Priest':
                self.magic_key_stat = 'wisdom'
            elif self.character_class == 'Mage':
                self.magic_key_stat = 'intelligence'
            else:
                self.magic_key_stat = None
                self._mana_point_maximum = self._current_mana_points = 0
                return
        magic_key_stat_mod = getattr(self, self.magic_key_stat + '_mod')
        if base_mana_points:
            self._mana_point_maximum = self._current_mana_points = (base_mana_points
                                                                    + self._bonus_mana_points[magic_key_stat_mod])
        elif self.character_class in self._base_mana_points:
            self._mana_point_maximum = self._current_mana_points = (self._base_mana_points[self.character_class]
                                                                    + self._bonus_mana_points[magic_key_stat_mod])
        else:
            self._mana_point_maximum = self._current_mana_points = 0

    def _attack_or_damage_stat_dependency(self):
        if self.character_class in ('Warrior', 'Priest') or (self.character_class == 'Mage'
                                                             and self._equipment.weapon_equipped):
            return 'strength'
        elif self.character_class == 'Thief':
            return 'dexterity'
        else:  # By exclusion, (`character_class` == 'Mage' and self._equipment.wand_equipped)
            return 'intelligence'

    @property
    def _item_attacking_with(self):
        if self._equipment.wand_equipped:
            return self._equipment.wand
        elif self._equipment.weapon_equipped:
            return self._equipment.weapon
        else:
            return None

    hit_point_total = property(fget=(lambda self: self._hit_point_maximum))

    hit_points = property(fget=(lambda self: self._current_hit_points))

    mana_points = property(fget=(lambda self: self._current_mana_points))

    mana_point_total = property(fget=(lambda self: self._mana_point_maximum))

    def take_damage(self, damage_value):
        if self._current_hit_points - damage_value < 0:
            taken_amount = self._current_hit_points
            self._current_hit_points = 0
            return taken_amount
        else:
            self._current_hit_points -= damage_value
            return damage_value

    def heal_damage(self, healing_value):
        if self._current_hit_points + healing_value > self._hit_point_maximum:
            amount_healed = self._hit_point_maximum - self._current_hit_points
            self._current_hit_points = self._hit_point_maximum
            return amount_healed
        else:
            self._current_hit_points += healing_value
            return healing_value

    def spend_mana(self, spent_amount):
        if self._current_mana_points < spent_amount:
            return 0
        else:
            self._current_mana_points -= spent_amount
            return spent_amount

    def regain_mana(self, regaining_value):
        if self._current_mana_points + regaining_value > self._mana_point_maximum:
            amount_regained = self._mana_point_maximum - self._current_mana_points
            self._current_mana_points = self._mana_point_maximum
            return amount_regained
        else:
            self._current_mana_points += regaining_value
            return regaining_value

    is_alive = property(fget=(lambda self: self._current_hit_points > 0))

    is_dead = property(fget=(lambda self: self._current_hit_points == 0))

    # These two properties are sneaky. When called, they return closures. The result is that the code
    # `character.attack_roll(12)` or `character.damage_roll()` *appears* to be a method call but is actually a
    # property access that returns a closure which is then immediately called and returns a result from the closure, not
    # from method code in the `Character` object.
    #
    # The upside of doing it this way is, if the call is omitted, the return value can be introspected by the testing
    # code to confirm the calculation being done is correct.

    @property
    def attack_roll(self):
        if not (self._equipment.weapon_equipped or self._equipment.wand_equipped):
            return None
        stat_dependency = self._attack_or_damage_stat_dependency()
        item_attacking_with = self._item_attacking_with
        stat_mod = getattr(self.ability_scores, stat_dependency+'_mod')
        total_mod = item_attacking_with.attack_bonus + stat_mod
        mod_str = '+' + str(total_mod) if total_mod > 0 else str(total_mod) if total_mod < 0 else ''
        return '1d20' + mod_str

    @property
    def damage_roll(self):
        if not (self._equipment.weapon_equipped or self._equipment.wand_equipped):
            return None
        stat_dependency = self._attack_or_damage_stat_dependency()
        item_attacking_with = self._item_attacking_with
        item_damage = item_attacking_with.damage
        damage_base_dice, damage_mod = (item_damage.split('+') if '+' in item_damage
                                        else item_damage.split('-') if '-' in item_damage
                                        else (item_damage, '0'))
        damage_mod = int(damage_mod)
        total_damage_mod = damage_mod + getattr(self.ability_scores, stat_dependency+'_mod')
        damage_str = damage_base_dice + ('+' + str(total_damage_mod) if total_damage_mod > 0
                                         else str(total_damage_mod) if total_damage_mod < 0
                                         else '')
        return damage_str

    # This class keeps its `Ability_Scores`, `Equipment` and `Inventory` objects in private attributes, just as a matter
    # of good OOP design. In the cases of the `Ability_Scores` and `Equipment` objects, these passthrough methods are
    # necessary so the concealed objects' functionality can be accessed from code that only has the `Character` object.
    #
    # The `Inventory` object presents a customized mapping interface that Character action management code doesn't need
    # to access, so only a few methods are offered.

    total_weight = property(fget=(lambda self: self.inventory.total_weight))

    burden = property(fget=(lambda self: self.inventory.burden_for_strength_score(
                                             self.ability_scores.strength
                                         )))

    def pick_up_item(self, item, qty=1):
        have_qty = self.item_have_qty(item)
        if qty == 1:
            self.inventory.add_one(item.internal_name, item)
        else:
            self.inventory.set(item.internal_name, qty + have_qty, item)

    def drop_item(self, item, qty=1):
        have_qty = self.item_have_qty(item)
        if have_qty == 0:
            raise KeyError(item.internal_name)
        if have_qty == qty:
            self.inventory.delete(item.internal_name)
        else:
            self.inventory.set(item.internal_name, have_qty - qty, item)

    def item_have_qty(self, item):
        if not self.inventory.contains(item.internal_name):
            return 0
        else:
            have_qty, _ = self.inventory.get(item.internal_name)
            return have_qty

    def have_item(self, item):
        return self.inventory.contains(item.internal_name)

    def list_items(self):
        return list(sorted(self.inventory.values(), key=lambda *argl: argl[0][1].title))

    # BEGIN passthrough methods for private Ability_Scores
    strength = property(fget=(lambda self: getattr(self.ability_scores, 'strength')))

    dexterity = property(fget=(lambda self: getattr(self.ability_scores, 'dexterity')))

    constitution = property(fget=(lambda self: getattr(self.ability_scores, 'constitution')))

    intelligence = property(fget=(lambda self: getattr(self.ability_scores, 'intelligence')))

    wisdom = property(fget=(lambda self: getattr(self.ability_scores, 'wisdom')))

    charisma = property(fget=(lambda self: getattr(self.ability_scores, 'charisma')))

    strength_mod = property(fget=(lambda self: self.ability_scores._stat_mod('strength')))

    dexterity_mod = property(fget=(lambda self: self.ability_scores._stat_mod('dexterity')))

    constitution_mod = property(fget=(lambda self: self.ability_scores._stat_mod('constitution')))

    intelligence_mod = property(fget=(lambda self: self.ability_scores._stat_mod('intelligence')))

    wisdom_mod = property(fget=(lambda self: self.ability_scores._stat_mod('wisdom')))

    charisma_mod = property(fget=(lambda self: self.ability_scores._stat_mod('charisma')))
    # END passthrough methods for private Ability_Scores

    # BEGIN passthrough methods for private _equipment
    armor_equipped = property(fget=(lambda self: self._equipment.armor_equipped))

    shield_equipped = property(fget=(lambda self: self._equipment.shield_equipped))

    weapon_equipped = property(fget=(lambda self: self._equipment.weapon_equipped))

    wand_equipped = property(fget=(lambda self: self._equipment.wand_equipped))

    armor = property(fget=(lambda self: self._equipment.armor))

    shield = property(fget=(lambda self: self._equipment.shield))

    weapon = property(fget=(lambda self: self._equipment.weapon))

    wand = property(fget=(lambda self: self._equipment.wand))

    def equip_armor(self, item):
        if not self.inventory.contains(item.internal_name):
            raise Internal_Exception("equipping an `item` object that is not in the character's `inventory` object is "
                                     'not allowed')
        return self._equipment.equip_armor(item)

    def equip_shield(self, item):
        if not self.inventory.contains(item.internal_name):
            raise Internal_Exception("equipping an `item` object that is not in the character's `inventory` object is "
                                     'not allowed')
        return self._equipment.equip_shield(item)

    def equip_weapon(self, item):
        if not self.inventory.contains(item.internal_name):
            raise Internal_Exception("equipping an `item` object that is not in the character's `inventory` object is "
                                     'not allowed')
        return self._equipment.equip_weapon(item)

    def equip_wand(self, item):
        if not self.inventory.contains(item.internal_name):
            raise Internal_Exception("equipping an `item` object that is not in the character's `inventory` object is "
                                     'not allowed')
        return self._equipment.equip_wand(item)

    def unequip_armor(self):
        return self._equipment.unequip_armor()

    def unequip_shield(self):
        return self._equipment.unequip_shield()

    def unequip_weapon(self):
        return self._equipment.unequip_weapon()

    def unequip_wand(self):
        return self._equipment.unequip_wand()
    # END passthrough methods for private _equipment

    # These aren't passthrough methods because the `_equipment` returns values for these Character parameters that
    # are informed only by the Equipment it stores. At the level of the `Character` object, these values should also be
    # informed by the character's ability scores stores in the `Ability_Scores`. A character's armor class is modified
    # by their dexterity modifier; and their attack & damage values are modified by either their strength score (for
    # Warriors, Priests, and Mages using a Weapon), or Dexterity (for Thieves), or Intelligence (for Mages using a
    # Wand).
    @property
    def armor_class(self):
        armor_class = self._equipment.armor_class
        dexterity_mod = self.ability_scores.dexterity_mod
        return armor_class + dexterity_mod

    @property
    def attack_bonus(self):
        if (not (self._equipment.weapon_equipped
            or self.character_class == 'Mage' and self._equipment.wand_equipped)):
            raise Internal_Exception('The character does not have a weapon equipped; no valid value for '
                                     '`attack_bonus` can be computed.')
        stat_dependency = self._attack_or_damage_stat_dependency()
        base_attack_bonus = (self._equipment.weapon.attack_bonus if self._equipment.weapon_equipped
                             else self._equipment.wand.attack_bonus)
        return base_attack_bonus + getattr(self.ability_scores, stat_dependency + '_mod')


class Equipment(object):  # has been tested
    __slots__ = 'character_class', 'armor', 'shield', 'weapon', 'wand'

    armor_equipped = property(fget=(lambda self: getattr(self, 'armor', None)))

    shield_equipped = property(fget=(lambda self: getattr(self, 'shield', None)))

    weapon_equipped = property(fget=(lambda self: getattr(self, 'weapon', None)))

    wand_equipped = property(fget=(lambda self: getattr(self, 'wand', None)))

    def __init__(self, character_class, armor_item=None, shield_item=None, weapon_item=None, wand_item=None):
        self.character_class = character_class
        self.armor = armor_item
        self.shield = shield_item
        self.wand = wand_item
        self.weapon = weapon_item

    def equip_armor(self, item):
        if not isinstance(item, Armor):
            raise Internal_Exception('the method `equip_armor()` only accepts `armor` objects for its argument')
        self._equip('armor', item)

    def equip_shield(self, item):
        if not isinstance(item, Shield):
            raise Internal_Exception('the method `equip_shield()` only accepts `shield` objects for its argument')
        self._equip('shield', item)

    def equip_weapon(self, item):
        if not isinstance(item, Weapon):
            raise Internal_Exception('the method `equip_weapon()` only accepts `weapon` objects for its argument')
        self._equip('weapon', item)

    def equip_wand(self, item):
        if not isinstance(item, Wand):
            raise Internal_Exception('the method `equip_wand()` only accepts `wand` objects for its argument')
        self._equip('wand', item)

    def unequip_armor(self):
        self._unequip('armor')

    def unequip_shield(self):
        self._unequip('shield')

    def unequip_weapon(self):
        self._unequip('weapon')

    def unequip_wand(self):
        self._unequip('wand')

    def _equip(self, equipment_slot, item):
        if equipment_slot not in ('armor', 'shield', 'weapon', 'wand'):
            raise Internal_Exception(f'equipment slot {equipment_slot} not recognized')
        if equipment_slot == 'armor':
            self.armor = item
        elif equipment_slot == 'shield':
            self.shield = item
        elif equipment_slot == 'weapon':
            self.weapon = item
        elif equipment_slot == 'wand':
            self.wand = item

    def _unequip(self, equipment_slot):
        if equipment_slot not in ('armor', 'shield', 'weapon', 'wand'):
            raise Internal_Exception(f'equipment slot {equipment_slot} not recognized')
        if equipment_slot == 'armor':
            self.armor = None
        elif equipment_slot == 'shield':
            self.shield = None
        elif equipment_slot == 'weapon':
            self.weapon = None
        elif equipment_slot == 'wand':
            self.wand = None

    @property
    def armor_class(self):
        ac = 10
        if self.armor_equipped:
            ac += self.armor.armor_bonus
        if self.shield_equipped:
            ac += self.shield.armor_bonus
        return ac

    @property
    def attack_bonus(self):
        attack = 0
        if self.weapon_equipped:
            attack += self.weapon.attack_bonus
            return attack
        else:
            return None

    @property
    def damage(self):
        if self.weapon_equipped:
            return self.weapon.damage
        else:
            return None


class Ability_Scores(object):  # has been tested
    __slots__ = 'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma', 'character_class'

    weightings = {
        'Warrior': ('strength', 'constitution', 'dexterity', 'intelligence', 'charisma', 'wisdom'),
        'Thief': ('dexterity', 'constitution', 'charisma', 'strength', 'wisdom', 'intelligence'),
        'Priest': ('wisdom', 'strength', 'constitution', 'charisma', 'intelligence', 'dexterity'),
        'Mage': ('intelligence', 'dexterity', 'constitution', 'strength', 'wisdom', 'charisma')
    }

    strength_mod = property(fget=(lambda self: self._stat_mod('strength')))

    dexterity_mod = property(fget=(lambda self: self._stat_mod('dexterity')))

    constitution_mod = property(fget=(lambda self: self._stat_mod('constitution')))

    intelligence_mod = property(fget=(lambda self: self._stat_mod('intelligence')))

    wisdom_mod = property(fget=(lambda self: self._stat_mod('wisdom')))

    charisma_mod = property(fget=(lambda self: self._stat_mod('charisma')))

    # In modern D&D, the derived value from an ability score that is relevant to determining outcomes is the 'stat mod'
    # (or 'stat modifier'), which is computed from the ability score by subtracting 10, dividing by 2 and rounding down.
    # That is implemented here.
    def _stat_mod(self, ability_score):
        if not hasattr(self, ability_score):
            raise Internal_Exception(f'unrecognized ability {ability_score}')
        return math.floor((getattr(self, ability_score) - 10) / 2)

    def __init__(self, character_class_str):
        if character_class_str not in self.weightings:
            raise Internal_Exception(f'character class {character_class_str} not recognized, should be one of '
                                      "'Warrior', 'Thief', 'Priest' or 'Mage'")
        self.character_class = character_class_str

    def roll_stats(self):
        # Rolling a six-sided die 4 times and then dropping the lowest roll before summing the remaining 3 results to
        # reach a value for an ability score (or 'stat') is the traditional method for generating D&D ability scores. It
        # is reproduced here.
        results_list = list()
        for _ in range(0, 6):
            four_rolls = sorted([random.randint(1, 6) for _ in range(0, 4)])
            three_rolls = four_rolls[1:4]
            results_list.append(sum(three_rolls))
        results_list.sort()
        results_list.reverse()
        for index in range(0, 6):
            setattr(self, self.weightings[self.character_class][index], results_list[index])


class Creature(Ini_Entry, Character):
    __slots__ = ('internal_name', 'character_name', 'description', 'character_class', 'species', '_strength',
                 '_dexterity', '_constitution', '_intelligence', '_wisdom', '_charisma', '_items_state',
                 '_base_hit_points', '_weapon_equipped', '_armor_equipped', '_shield_equipped')

    def __init__(self, items_state, internal_name, **argd):
        character_init_argd, ini_entry_init_argd, equipment_argd, inventory_qty_name_pairs = \
            self._separate_argd_into_different_arg_sets(items_state, internal_name, **argd)
        Ini_Entry.__init__(self, internal_name=internal_name, **ini_entry_init_argd)
        self._post_init_slots_set_none(self.__slots__)
        Character.__init__(self, **character_init_argd)
        self._init_inventory_and_equipment(items_state, inventory_qty_name_pairs, equipment_argd)
        self._items_state = items_state

    # Divides the argd passed to __init__ into arguments for Character.__init__, arguments for Ini_Entry.__init__,
    # arguments to Character.equip_*, and arguments to Character.pick_up_item.
    #
    # argd is accepted as a ** argument so it's passed by copy rather than by reference.
    def _separate_argd_into_different_arg_sets(self, items_state, internal_name, **argd):
        character_init_argd = dict(strength=int(argd.pop('strength')),
                                   dexterity=int(argd.pop('dexterity')),
                                   constitution=int(argd.pop('constitution')),
                                   intelligence=int(argd.pop('intelligence')),
                                   wisdom=int(argd.pop('wisdom')),
                                   charisma=int(argd.pop('charisma')),
                                   base_hit_points=int(argd.pop('base_hit_points')),
                                   character_name_str=argd.pop('character_name'),
                                   character_class_str=argd.pop('character_class'),
                                   base_mana_points=int(argd.pop('base_mana_points', 0)),
                                   magic_key_stat=argd.pop('magic_key_stat', None))
        equipment_argd = dict()
        for ini_key in ('weapon_equipped', 'armor_equipped', 'shield_equipped', 'wand_equipped'):
            if ini_key not in argd:
                continue
            equipment_argd[ini_key] = argd.pop(ini_key)
        inventory_qty_name_pairs = self._process_list_value(argd.pop('inventory_items'))
        if any(not items_state.contains(inventory_internal_name)
               for _, inventory_internal_name in inventory_qty_name_pairs):
            missing_names = tuple(item_internal_name for _, item_internal_name in inventory_qty_name_pairs
                                  if not items_state.contains(item_internal_name))
            pluralizer = 's' if len(missing_names) > 1 else ''
            raise Internal_Exception(f'bad creatures.ini specification for creature {internal_name}: creature '
                                     f'ini config dict `inventory_items` value indicated item{pluralizer}'
                                     ' not present in `Items_State` argument: ' + (', '.join(missing_names)))
        ini_entry_init_argd = argd
        return character_init_argd, ini_entry_init_argd, equipment_argd, inventory_qty_name_pairs

    def _init_inventory_and_equipment(self, items_state, inventory_qty_name_pairs, equipment_argd):
        for item_qty, item_internal_name in inventory_qty_name_pairs:
            item = items_state.get(item_internal_name)
            for index in range(0, item_qty):
                self.pick_up_item(item)
        for equipment_key, item_internal_name in equipment_argd.items():
            if not items_state.contains(item_internal_name):
                raise Internal_Exception(f'bad creatures.ini specification for creature {self.internal_name}: items '
                                         f'index object does not contain an item named {item_internal_name}')
            item = items_state.get(item_internal_name)
            if equipment_key == 'weapon_equipped':
                self.equip_weapon(item)
            elif equipment_key == 'armor_equipped':
                self.equip_armor(item)
            elif equipment_key == 'shield_equipped':
                self.equip_shield(item)
            else:  # by exclusion, the value must be 'wand_equipped'
                self.equip_wand(item)

    def convert_to_corpse(self):
        internal_name = self.internal_name
        description = self.description_dead
        title = f'{self.title} corpse'
        corpse = Corpse(self._items_state, internal_name, container_type='corpse',
                            description=description, title=title)
        for item_internal_name, (item_qty, item) in self.inventory.items():
            corpse.set(item_internal_name, item_qty, item)
        return corpse


class Container(Ini_Entry, Items_Multi_State):
    __slots__ = 'internal_name', 'title', 'description', 'is_locked', 'is_closed', 'container_type'

    def __init__(self, item_state, internal_name, *item_objs, **ini_constr_argd):
        contents_str = ini_constr_argd.pop('contents', None)
        Ini_Entry.__init__(self, internal_name=internal_name, **ini_constr_argd)
        if contents_str:
            contents_qtys_names = self._process_list_value(contents_str)
            contents_qtys_item_objs = tuple((item_qty, item_state.get(item_internal_name))
                                             for item_qty, item_internal_name in contents_qtys_names)
        Items_Multi_State.__init__(self)
        if contents_str:
            for item_qty, item in contents_qtys_item_objs:
                self.set(item.internal_name, item_qty, item)
        self._post_init_slots_set_none(self.__slots__)

    @classmethod
    def subclassing_factory(self, items_state, **container_dict):
        if container_dict['container_type'] == 'chest':
            container = Chest(items_state, **container_dict)
        elif container_dict['container_type'] == 'corpse':
            container = Corpse(items_state, **container_dict)
        return container


class Chest(Container):
    pass


class Corpse(Container):
    pass


class Door(Ini_Entry):
    __slots__ = ('internal_name', 'title', 'description', 'door_type', 'is_locked', 'is_closed', 'closeable',
                 '_linked_rooms_internal_names', 'is_exit')

    def __init__(self, **argd):
        super().__init__(**argd)
        self._post_init_slots_set_none(self.__slots__)
        self._linked_rooms_internal_names = set(self.internal_name.split('_x_'))

    @classmethod
    def subclassing_factory(self, **door_dict):
        if door_dict['door_type'] == 'doorway':
            door = Doorway(**door_dict)
        elif door_dict['door_type'] == 'wooden_door':
            door = Wooden_Door(**door_dict)
        elif door_dict['door_type'] == 'iron_door':
            door = Iron_Door(**door_dict)
        else:
            raise Internal_Error(f'unrecognized door type: {door_dict["door_type"]}')
        return door

    def other_room_internal_name(self, room_internal_name):

        if room_internal_name not in self._linked_rooms_internal_names:
            raise Internal_Exception(f'room internal name {room_internal_name} not one of the two rooms linked by this'
                                      ' door object')

        # The set _linked_rooms_internal_names is only 2 elements long and by the above one of those elements is the
        # name supplied so this loop returns the other name.
        for found_internal_name in self._linked_rooms_internal_names:
            if found_internal_name == room_internal_name:
                continue
            return found_internal_name

    def copy(self):
        return Door(**{attr: getattr(self, attr, None) for attr in self.__slots__})


class Doorway(Door):
    pass


class Wooden_Door(Door):
    pass


class Iron_Door(Door):
    pass


class Item(Ini_Entry):  # has been tested
    __slots__ = ('internal_name', 'title', 'description', 'weight', 'value', 'damage', 'attack_bonus', 'armor_bonus',
                 'item_type', 'warrior_can_use', 'thief_can_use', 'priest_can_use', 'mage_can_use',
                 'hit_points_recovered', 'mana_points_recovered')

    def __init__(self, **argd):
        super().__init__(**argd)
        self._post_init_slots_set_none(self.__slots__)

    @classmethod
    def subclassing_factory(self, **item_dict):
        if item_dict['item_type'] == 'armor':
            item = Armor(**item_dict)
        elif item_dict['item_type'] == 'coin':
            item = Coin(**item_dict)
        elif item_dict['item_type'] == 'potion':
            item = Potion(**item_dict)
        elif item_dict['item_type'] == 'key':
            item = Key(**item_dict)
        elif item_dict['item_type'] == 'shield':
            item = Shield(**item_dict)
        elif item_dict['item_type'] == 'wand':
            item = Wand(**item_dict)
        elif item_dict['item_type'] == 'weapon':
            item = Weapon(**item_dict)
        return item

    def usable_by(self, character_class):
        if character_class not in ('Warrior', 'Thief', 'Mage', 'Priest'):
            raise Internal_Exception(f'character class {character_class} not recognized')
        return bool(getattr(self, character_class.lower() + '_can_use', None))


# The subclasses don't have much differing functionality but accurately typing each Item allows classes that handle
# items of specific types, like Equipment(), to use type testing to determine if a valid Item has been supplied as an
# argument.
class Armor(Item):
    pass


class Coin(Item):
    pass


class Potion(Item):
    pass


class Key(Item):
    pass


class Shield(Item):
    pass


class Wand(Item):
    pass


class Weapon(Item):
    pass


class Room(Ini_Entry):  # has been tested
    __slots__ = ('internal_name', 'title', 'description', 'north_door', 'west_door', 'south_door', 'east_door',
                 'occupant', 'item', 'is_entrance', 'is_exit', '_containers_state', '_creatures_state',
                 '_doors_state', '_items_state', 'creature_here', 'container_here', 'items_here')

    @property
    def has_north_door(self):
        return bool(getattr(self, 'north_door', False))

    @property
    def has_south_door(self):
        return bool(getattr(self, 'south_door', False))

    @property
    def has_west_door(self):
        return bool(getattr(self, 'west_door', False))

    @property
    def has_east_door(self):
        return bool(getattr(self, 'east_door', False))

    def __init__(self, creatures_state, containers_state, doors_state, items_state, **argd):
        super().__init__(**argd)
        self._containers_state = containers_state
        self._creatures_state = creatures_state
        self._items_state = items_state
        self._doors_state = doors_state
        self._post_init_slots_set_none(self.__slots__)
        if self.creature_here:
            if not self._creatures_state.contains(self.creature_here):
                raise internal_exception(f"room obj `{self.internal_name}` creature_here value '{self.creature_here}' "
                                         "doesn't correspond to any creatures in creatures_state store")
            self.creature_here = self._creatures_state.get(self.creature_here)
        if self.container_here:
            if not self._containers_state.contains(self.container_here):
                raise internal_exception(f"room obj `{self.internal_name}` container_here value '{self.container_here}'"
                                         " doesn't correspond to any creatures in creatures_state store")
            self.container_here = self._containers_state.get(self.container_here)
        if self.items_here:
            items_here_names_list = self._process_list_value(self.items_here)
            items_state = Items_Multi_State()
            for item_qty, item_internal_name in items_here_names_list:
                item = self._items_state.get(item_internal_name)
                items_state.set(item_internal_name, item_qty, item)
            self.items_here = items_state
        for compass_dir in ('north', 'east', 'south', 'west'):
            door_attr = f'{compass_dir}_door'
            if not getattr(self, door_attr, False):
                continue
            sorted_pair = tuple(sorted((self.internal_name, getattr(self, door_attr))))
            if sorted_pair[0].lower() == 'exit':
                sorted_pair = tuple(reversed(sorted_pair))

            # The Door objects stored in each Room object are not identical with the Door objects in
            # self._doors_state because each Door gets a new title based on its compass direction; the same Door can
            # be titled 'north door' in the southern of the two rooms it connects and 'south door' in the northern one.
            door = self._doors_state.get(*sorted_pair).copy()
            door.title = f'{compass_dir} doorway' if door.title == 'doorway' else f'{compass_dir} door'
            setattr(self, door_attr, door)

    @property
    def doors(self):
        doors_tuple = ()
        for compass_dir in ('north', 'east', 'south', 'west'):
            has_door_property = f'has_{compass_dir}_door'
            if not getattr(self, has_door_property):
                continue
            doors_tuple += getattr(self, f'{compass_dir}_door'),
        return doors_tuple

class Items_Multi_State(Items_State):

    def __init__(self, **argd):
        Items_State.__init__(self, **argd)

        # I preload the dict's items() sequence outside of the loop because the loop alters the dict and I don't want a
        # concurrent update error.
        contents_items = tuple(self._contents.items())
        for item_internal_name, item in contents_items:
            self._contents[item_internal_name] = (1, item)

    def contains(self, item_internal_name):
        return(any(contained_item.internal_name == item_internal_name
                   for _, contained_item in self._contents.values()))

    def set(self, item_internal_name, item_qty, item):
        self._contents[item_internal_name] = item_qty, item

    def add_one(self, item_internal_name, item):
        if self.contains(item_internal_name):
            self._contents[item_internal_name] = (self._contents[item_internal_name][0] + 1,
                                                  self._contents[item_internal_name][1])
        else:
            self._contents[item_internal_name] = 1, item

    def remove_one(self, item_internal_name):
        if item_internal_name not in self._contents:
            raise KeyError(item_internal_name)
        elif self._contents[item_internal_name][0] == 1:
            del self._contents[item_internal_name]
        else:
            self._contents[item_internal_name] = (self._contents[item_internal_name][0] - 1,
                                                  self._contents[item_internal_name][1])


class Game_State(object):
    __slots__ = ('_character_name', '_character_class', 'character', 'rooms_state', 'containers_state',
                 'doors_state', 'items_state', 'creatures_state', 'game_has_begun', 'game_has_ended')

    @property
    def character_name(self):
        return self._character_name

    @character_name.setter
    def character_name(self, name_str):
        setattr(self, '_character_name', name_str)
        self._incept_character_obj_if_possible()

    @property
    def character_class(self):
        return self._character_class

    @character_class.setter
    def character_class(self, class_str):
        setattr(self, '_character_class', class_str)
        self._incept_character_obj_if_possible()

    def __init__(self, rooms_state, creatures_state, containers_state, doors_state, items_state):
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

    # The Character object can't be instantiated until the `character_name` and `character_class` attributes are set,
    # but that happens after initialization; so the `character_name` and `character_class` setters call this method
    # prospectively each time either is called to check if both have been set and `Character` object instantiation can
    # proceed.
    def _incept_character_obj_if_possible(self):
        if self.character is None and getattr(self, 'character_name', None) and getattr(self, 'character_class', None):
            self.character = Character(self.character_name, self.character_class)


class Containers_State(Items_State):
    __slots__ = '_contents',

    def __init__(self, items_state, **dict_of_dicts):
        self._contents = dict()
        for container_internal_name, container_dict in dict_of_dicts.items():
            container = Container.subclassing_factory(items_state, internal_name=container_internal_name,
                                                          **container_dict)
            self._contents[container_internal_name] = container


class Creatures_State(State):

    def __init__(self, items_state, **dict_of_dicts):
        self._contents = dict()
        for creature_internal_name, creature_dict in dict_of_dicts.items():
            creature = Creature(items_state, internal_name=creature_internal_name, **creature_dict)
            self.set(creature.internal_name, creature)


class Rooms_State(object):  # has been tested
    __slots__ = ('_creatures_state', '_containers_state', '_items_state', '_doors_state',
                 '_rooms_objs', '_room_cursor')

    @property
    def cursor(self):
        return self._rooms_objs[self._room_cursor]

    def __init__(self, creatures_state, containers_state, doors_state, items_state, **dict_of_dicts):
        self._rooms_objs = dict()
        self._creatures_state = creatures_state
        self._containers_state = containers_state
        self._doors_state = doors_state
        self._items_state = items_state
        for room_internal_name, room_dict in dict_of_dicts.items():
            room = Room(creatures_state, containers_state, doors_state, items_state,
                            internal_name=room_internal_name, **room_dict)
            if room.is_entrance:
                self._room_cursor = room.internal_name
            self._store_room(room.internal_name, room)

    def _store_room(self, room_internal_name, room):
        self._rooms_objs[room_internal_name] = room

    def move(self, north=False, west=False, south=False, east=False):
        if ((north and west) or (north and south) or (north and east) or (west and south)
            or (west and east) or (south and east)):
            raise Internal_Exception('move() must receive only *one* True argument of the four keys `north`, `south`, '
                                     '`east` and `west`')
        if north:
            exit_name = 'north_door'
            exit_key = 'NORTH'
        elif west:
            exit_name = 'west_door'
            exit_key = 'WEST'
        elif south:
            exit_name = 'south_door'
            exit_key = 'SOUTH'
        elif east:
            exit_name = 'east_door'
            exit_key = 'EAST'
        if not getattr(self.cursor, exit_name):
            raise Bad_Command_Exception('MOVE', f'This room has no <{exit_key}> exit.')
        door = getattr(self.cursor, exit_name)
        if door.is_locked:
            raise Internal_Exception(f'exiting {self.cursor.internal_name} via the {exit_name.replace("_"," ")}: door '
                                      'is locked')
        other_room_internal_name = door.other_room_internal_name(self.cursor.internal_name)
        new_room_dest = self._rooms_objs[other_room_internal_name]
        self._room_cursor = new_room_dest.internal_name
