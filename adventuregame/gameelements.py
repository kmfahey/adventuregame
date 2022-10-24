#!/usr/bin/python3

import abc
import math
import random
import re
import operator
import functools
import operator

import iniconfig

from .collections import *
from .utility import *

__name__ = 'adventuregame.gameelements'


class items_state(state):  # has been tested

    def __init__(self, **dict_of_dicts):
        self._contents = dict()
        for item_internal_name, item_dict in dict_of_dicts.items():
            item_obj = item.subclassing_factory(internal_name=item_internal_name, **item_dict)
            self._contents[item_internal_name] = item_obj


class items_multi_state(items_state):

    def __init__(self, **argd):
        items_state.__init__(self, **argd)

        # I preload the dict's items() sequence outside of the loop because
        # the loop alters the dict and I don't want a concurrent update error.
        contents_items = tuple(self._contents.items())
        for item_internal_name, item_obj in contents_items:
            self._contents[item_internal_name] = (1, item_obj)

    def contains(self, item_internal_name):
        return(any(contained_item_obj.internal_name == item_internal_name for _, contained_item_obj in self._contents.values()))

    def set(self, item_internal_name, item_qty, item_obj):
        self._contents[item_internal_name] = item_qty, item_obj

    def add_one(self, item_internal_name, item_obj):
        if self.contains(item_internal_name):
            self._contents[item_internal_name] = self._contents[item_internal_name][0] + 1, self._contents[item_internal_name][1]
        else:
            self._contents[item_internal_name] = 1, item_obj

    def remove_one(self, item_internal_name):
        if item_internal_name not in self._contents:
            raise KeyError(item_internal_name)
        elif self._contents[item_internal_name][0] == 1:
            del self._contents[item_internal_name]
        else:
            self._contents[item_internal_name] = self._contents[item_internal_name][0] - 1, self._contents[item_internal_name][1]


class inventory(items_multi_state):  # has been tested

    Light = 0
    Medium = 1
    Heavy = 2
    Immobilizing = 3

    _carry_weight = {
        3:  {Light: (0, 10),    Medium: (11, 20),   Heavy: (21, 30)},
        4:  {Light: (0, 13),    Medium: (14, 26),   Heavy: (27, 40)},
        5:  {Light: (0, 16),    Medium: (17, 33),   Heavy: (34, 50)},
        6:  {Light: (0, 20),    Medium: (21, 40),   Heavy: (41, 60)},
        7:  {Light: (0, 23),    Medium: (24, 46),   Heavy: (47, 70)},
        8:  {Light: (0, 26),    Medium: (27, 53),   Heavy: (54, 80)},
        9:  {Light: (0, 30),    Medium: (31, 60),   Heavy: (61, 90)},
        10: {Light: (0, 33),    Medium: (34, 66),   Heavy: (67, 100)},
        11: {Light: (0, 38),    Medium: (39, 76),   Heavy: (77, 115)},
        12: {Light: (0, 43),    Medium: (44, 86),   Heavy: (87, 130)},
        13: {Light: (0, 50),    Medium: (51, 100),  Heavy: (101, 150)},
        14: {Light: (0, 58),    Medium: (59, 116),  Heavy: (117, 175)},
        15: {Light: (0, 66),    Medium: (67, 133),  Heavy: (134, 200)},
        16: {Light: (0, 76),    Medium: (77, 153),  Heavy: (154, 230)},
        17: {Light: (0, 86),    Medium: (87, 173),  Heavy: (174, 260)},
        18: {Light: (0, 100),   Medium: (101, 200), Heavy: (201, 300)}
    }

    def __init__(self, **dict_of_dicts):
        super().__init__(**dict_of_dicts)

    @property
    def total_weight(self):
        total_weight_val = 0
        for item_name, (item_count, item_obj) in self._contents.items():
            if item_obj.weight <= 0:
                raise internal_exception('item ' + item_obj.internal_name + ' has invalid weight ' + str(item_obj.weight) + ': is <= 0')
            elif item_count <= 0:
                raise internal_exception('item ' + item_obj.internal_name + ' is stored with invalid count ' + str(item_count) + ': is <= 0')
            total_weight_val += item_obj.weight * item_count
        return total_weight_val

    def burden_for_strength_score(self, strength_score):
        total_weight_val = self.total_weight
        if total_weight_val < 0:
            raise internal_exception('the `total_weight` value for this inventory equals a negative number')
        light_burden_lower_bound = self._carry_weight[strength_score][self.Light][0]
        light_burden_upper_bound = self._carry_weight[strength_score][self.Light][1]
        medium_burden_lower_bound = self._carry_weight[strength_score][self.Medium][0]
        medium_burden_upper_bound = self._carry_weight[strength_score][self.Medium][1]
        heavy_burden_lower_bound = self._carry_weight[strength_score][self.Heavy][0]
        heavy_burden_upper_bound = self._carry_weight[strength_score][self.Heavy][1]
        if light_burden_lower_bound <= total_weight_val <= light_burden_upper_bound:
            return self.Light
        elif medium_burden_lower_bound <= total_weight_val <= medium_burden_upper_bound:
            return self.Medium
        elif heavy_burden_lower_bound <= total_weight_val <= heavy_burden_upper_bound:
            return self.Heavy
        else:
            return self.Immobilizing


class character(object):  # has been tested
    __slots__ = ('character_name', 'character_class', 'magic_key_stat', '_hit_point_maximum', '_current_hit_points',
                 '_mana_point_maximum', '_current_mana_points', '_ability_scores_obj', 'inventory',
                 '_equipment_obj')

    _base_mana_points = {'Priest': 16, 'Mage': 19}

    _bonus_mana_points = {1: 1, 2: 4, 3: 9, 4: 16}

    _hitpoint_base = {'Warrior': 40, 'Priest': 30, 'Thief': 30, 'Mage': 20}

    def __init__(self, character_name_str, character_class_str, base_hit_points=0, base_mana_points=0,
                 magic_key_stat=None, strength=0, dexterity=0, constitution=0, intelligence=0, wisdom=0, charisma=0):
        if character_class_str not in {'Warrior', 'Thief', 'Priest', 'Mage'}:
            raise internal_exception(f'character class argument {character_class_str} not one of '
                                     'Warrior, Thief, Priest or Mage')
        self.character_name = character_name_str
        self.character_class = character_class_str
        self._ability_scores_obj = ability_scores(character_class_str)
        self._set_up_ability_scores(strength, dexterity, constitution, intelligence, wisdom, charisma)
        self.inventory = inventory()
        self._equipment_obj = equipment(character_class_str)
        self._set_up_hit_points_and_mana_points(base_hit_points, base_mana_points, magic_key_stat)

    def _set_up_ability_scores(self, strength=0, dexterity=0, constitution=0, intelligence=0, wisdom=0, charisma=0):
        if all((strength, dexterity, constitution, intelligence, wisdom, charisma)):
            self._ability_scores_obj.strength = strength
            self._ability_scores_obj.dexterity = dexterity
            self._ability_scores_obj.constitution = constitution
            self._ability_scores_obj.intelligence = intelligence
            self._ability_scores_obj.wisdom = wisdom
            self._ability_scores_obj.charisma = charisma
        elif any((strength, dexterity, constitution, intelligence, wisdom, charisma)):
            raise internal_exception('The constructor for `character` must be supplied with either all of the arguments'
                                     ' `strength`, `dexterity`, `constitution`, `intelligence`, `wisdom`, and '
                                     '`charisma` or none of them.')
        else:
            self._ability_scores_obj.roll_stats()

    def _set_up_hit_points_and_mana_points(self, base_hit_points, base_mana_points, magic_key_stat):
        if base_hit_points:
            self._hit_point_maximum = self._current_hit_points = base_hit_points + self._ability_scores_obj.constitution_mod * 3
        else:
            self._hit_point_maximum = self._current_hit_points = self._hitpoint_base[self.character_class] + self._ability_scores_obj.constitution_mod * 3
        if magic_key_stat:
            if magic_key_stat not in ('intelligence', 'wisdom', 'charisma'):
                raise internal_exception("`magic_key_stat` argument '" + magic_key_stat + "' not recognized")
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
            mana_points_init_val = base_mana_points
        elif self.character_class in self._base_mana_points:
            mana_points_init_val = self._base_mana_points[self.character_class]
        else:
            mana_points_init_val = 0
        if mana_points_init_val:
            if magic_key_stat_mod > 0:
                self._mana_point_maximum = self._current_mana_points = (mana_points_init_val
                                                                        + self._bonus_mana_points[magic_key_stat_mod])
            else:
                self._mana_point_maximum = self._current_mana_points = mana_points_init_val
        else:
            self._mana_point_maximum = self._current_mana_points = 0

    def _attack_or_damage_stat_dependency(self):
        if self.character_class in ('Warrior', 'Priest') or (self.character_class == 'Mage' and self._equipment_obj.weapon_equipped):
            return 'strength'
        elif self.character_class == 'Thief':
            return 'dexterity'
        else:  # By exclusion, (`character_class` == 'Mage' and self._equipment_obj.wand_equipped)
            return 'intelligence'

    _item_attacking_with = property(fget=(lambda self: self._equipment_obj.weapon
                                                       if not self._equipment_obj.wand_equipped
                                                       else self._equipment_obj.wand))

    hit_points = property(fget=(lambda self: self._current_hit_points))

    mana_points = property(fget=(lambda self: self._current_mana_points))

    def take_damage(self, damage_value):
        if self._current_hit_points - damage_value < 0:
            self._current_hit_points = 0
        else:
            self._current_hit_points -= damage_value

    def heal_damage(self, healing_value):
        if self._current_hit_points + healing_value > self._hit_point_maximum:
            self._current_hit_points = self._hit_point_maximum
        else:
            self._current_hit_points += healing_value

    def attempt_to_spend_mana(self, spent_amount):
        if self._current_mana_points < spent_amount:
            return False
        else:
            self._current_mana_points -= spent_amount
            return True

    def regain_mana(self, regained_amount):
        if self._current_mana_points + regained_amount > self._mana_point_maximum:
            self._current_mana_points = self._mana_point_maximum
        else:
            self._current_mana_points += regained_amount

    is_alive = property(fget=(lambda self: self._current_hit_points > 0))

    is_dead = property(fget=(lambda self: self._current_hit_points == 0))

    # These two properties are sneaky. When called, they return closures.
    # The result is that the code `character_obj.attack_roll(12)` or
    # `character_obj.damage_roll()` *appears* to be a method call but is
    # actually a property access that returns a closure which is then
    # immediately called and returns a result from the closure, not from
    # method code in the `character` object.
    #
    # The upside of doing it this way is, if the call is omitted, the return
    # value can be introspected by the testing code to confirm the calculation
    # being done is correct.
    @property
    def attack_roll(self):
        if not (self._equipment_obj.weapon_equipped or self._equipment_obj.wand_equipped):
            if self.character_class != 'Mage':
                raise bad_command_exception('ATTACK', 'You have no weapon equipped.')
            else:
                raise bad_command_exception('ATTACK', 'You have no weapon or wand equipped.')
        stat_dependency = self._attack_or_damage_stat_dependency()
        item_attacking_with = self._item_attacking_with
        stat_mod = getattr(self._ability_scores_obj, stat_dependency+'_mod')
        total_mod = item_attacking_with.attack_bonus + stat_mod
        mod_str = '+' + str(total_mod) if total_mod > 0 else str(total_mod) if total_mod < 0 else ''
        return '1d20' + mod_str

    @property
    def damage_roll(self):
        stat_dependency = self._attack_or_damage_stat_dependency()
        item_attacking_with = self._item_attacking_with
        item_damage = item_attacking_with.damage
        damage_base_dice, damage_mod = item_damage.split('+') if '+' in item_damage else item_damage.split('-') if '-' in item_damage else (item_damage, '0')
        damage_mod = int(damage_mod)
        total_damage_mod = damage_mod + getattr(self._ability_scores_obj, stat_dependency+'_mod')
        damage_str = damage_base_dice + ('+' + str(total_damage_mod) if total_damage_mod > 0 else str(total_damage_mod) if total_damage_mod < 0 else '')
        return damage_str

    # This class keeps its `ability_scores`, `equipment` and `inventory` objects
    # in private attributes, just as a matter of good OOP design. In the cases
    # of the `ability_scores` and `equipment` objects, these passthrough methods
    # are necessary so the concealed objects' functionality can be accessed
    # from code that only has the `character` object.
    #
    # The `inventory` object presents a customized mapping interface that
    # character action management code doesn't need to access, so only a few
    # methods are offered.

    total_weight = property(fget=(lambda self: self.inventory.total_weight))

    burden = property(fget=(lambda self: self.inventory.burden_for_strength_score(
                                             self._ability_scores_obj.strength
                                         )))

    def pick_up_item(self, item_obj, qty=1):
        have_qty = self.item_have_qty(item_obj)
        if qty == 1:
            self.inventory.add_one(item_obj.internal_name, item_obj)
        else:
            self.inventory.set(item_obj.internal_name, qty + have_qty, item_obj)

    def drop_item(self, item_obj, qty=1):
        have_qty = self.item_have_qty(item_obj)
        if have_qty == 0:
            raise KeyError(item_obj.internal_name)
        if have_qty == qty:
            self.inventory.delete(item_obj.internal_name)
        else:
            self.inventory.set(item_obj.internal_name, have_qty - qty, item_obj)

    def item_have_qty(self, item_obj):
        if not self.inventory.contains(item_obj.internal_name):
            return 0
        else:
            have_qty, _ = self.inventory.get(item_obj.internal_name)
            return have_qty

    def have_item(self, item_obj):
        return self.inventory.contains(item_obj.internal_name)

    def list_items(self):
        return list(sorted(self.inventory.values(), key=lambda *argl: argl[0][1].title))

    # BEGIN passthrough methods for private _ability_scores_obj
    strength = property(fget=(lambda self: getattr(self._ability_scores_obj, 'strength')))

    dexterity = property(fget=(lambda self: getattr(self._ability_scores_obj, 'dexterity')))

    constitution = property(fget=(lambda self: getattr(self._ability_scores_obj, 'constitution')))

    intelligence = property(fget=(lambda self: getattr(self._ability_scores_obj, 'intelligence')))

    wisdom = property(fget=(lambda self: getattr(self._ability_scores_obj, 'wisdom')))

    charisma = property(fget=(lambda self: getattr(self._ability_scores_obj, 'charisma')))

    strength_mod = property(fget=(lambda self: self._ability_scores_obj._stat_mod('strength')))

    dexterity_mod = property(fget=(lambda self: self._ability_scores_obj._stat_mod('dexterity')))

    constitution_mod = property(fget=(lambda self: self._ability_scores_obj._stat_mod('constitution')))

    intelligence_mod = property(fget=(lambda self: self._ability_scores_obj._stat_mod('intelligence')))

    wisdom_mod = property(fget=(lambda self: self._ability_scores_obj._stat_mod('wisdom')))

    charisma_mod = property(fget=(lambda self: self._ability_scores_obj._stat_mod('charisma')))
    # END passthrough methods for private _ability_scores_obj

    # BEGIN passthrough methods for private _equipment_obj
    armor_equipped = property(fget=(lambda self: self._equipment_obj.armor_equipped))

    shield_equipped = property(fget=(lambda self: self._equipment_obj.shield_equipped))

    weapon_equipped = property(fget=(lambda self: self._equipment_obj.weapon_equipped))

    wand_equipped = property(fget=(lambda self: self._equipment_obj.wand_equipped))

    armor = property(fget=(lambda self: self._equipment_obj.armor))

    shield = property(fget=(lambda self: self._equipment_obj.shield))

    weapon = property(fget=(lambda self: self._equipment_obj.weapon))

    wand = property(fget=(lambda self: self._equipment_obj.wand))

    def equip_armor(self, item_obj):
        if not self.inventory.contains(item_obj.internal_name):
            raise internal_exception("equipping an `item` object that is not in the character's `inventory` object is not allowed")
        return self._equipment_obj.equip_armor(item_obj)

    def equip_shield(self, item_obj):
        if not self.inventory.contains(item_obj.internal_name):
            raise internal_exception("equipping an `item` object that is not in the character's `inventory` object is not allowed")
        return self._equipment_obj.equip_shield(item_obj)

    def equip_weapon(self, item_obj):
        if not self.inventory.contains(item_obj.internal_name):
            raise internal_exception("equipping an `item` object that is not in the character's `inventory` object is not allowed")
        return self._equipment_obj.equip_weapon(item_obj)

    def equip_wand(self, item_obj):
        if not self.inventory.contains(item_obj.internal_name):
            raise internal_exception("equipping an `item` object that is not in the character's `inventory` object is not allowed")
        return self._equipment_obj.equip_wand(item_obj)
    # END passthrough methods for private _equipment_obj

    # These aren't passthrough methods because the `_equipment_obj` returns
    # values for these character parameters that are informed only by the
    # equipment it stores. At the level of the `character` object, these
    # values should also be informed by the character's ability scores stores
    # in the `_ability_scores_obj`. A character's armor class is modified by
    # their dexterity modifier; and their attack & damage values are modified
    # by either their strength score (for Warriors, Priests, and Mages using a
    # weapon), or Dexterity (for Thieves), or Intelligence (for Mages using a
    # wand).
    @property
    def armor_class(self):
        armor_class = self._equipment_obj.armor_class
        dexterity_mod = self._ability_scores_obj.dexterity_mod
        return armor_class + dexterity_mod

    @property
    def attack_bonus(self):
        if not (self._equipment_obj.weapon_equipped or self.character_class == 'Mage' and self._equipment_obj.wand_equipped):
            raise internal_exception('The character does not have a weapon equipped; no valid value for `attack_bonus` can be computed.')
        stat_dependency = self._attack_or_damage_stat_dependency()
        base_attack_bonus = self._equipment_obj.weapon.attack_bonus if self._equipment_obj.weapon_equipped else self._equipment_obj.wand.attack_bonus
        return base_attack_bonus + getattr(self._ability_scores_obj, stat_dependency + '_mod')


class equipment(object):  # has been tested
    __slots__ = 'character_class', 'armor', 'shield', 'weapon', 'wand'

    armor_equipped = property(fget=(lambda self: getattr(self, 'armor', None)))

    shield_equipped = property(fget=(lambda self: getattr(self, 'shield', None)))

    weapon_equipped = property(fget=(lambda self: getattr(self, 'weapon', None)))

    wand_equipped = property(fget=(lambda self: getattr(self, 'wand', None)))

    def __init__(self, character_class, armor_item=None, shield_item=None, weapon_item=None):
        self.character_class = character_class
        self.armor = armor_item
        self.shield = shield_item
        self.weapon = weapon_item

    def equip_armor(self, item_obj):
        if not isinstance(item_obj, armor):
            raise internal_exception('the method `equip_armor()` only accepts `armor` objects for its argument')
        self._equip('armor', item_obj)

    def equip_shield(self, item_obj):
        if not isinstance(item_obj, shield):
            raise internal_exception('the method `equip_shield()` only accepts `shield` objects for its argument')
        self._equip('shield', item_obj)

    def equip_weapon(self, item_obj):
        if not isinstance(item_obj, weapon):
            raise internal_exception('the method `equip_weapon()` only accepts `weapon` objects for its argument')
        self._equip('weapon', item_obj)

    def equip_wand(self, item_obj):
        if not isinstance(item_obj, wand):
            raise internal_exception('the method `equip_wand()` only accepts `wand` objects for its argument')
        self._equip('wand', item_obj)

    def _equip(self, equipment_slot, item_obj):
        if equipment_slot not in ('armor', 'shield', 'weapon', 'wand'):
            raise internal_exception(f'equipment slot {equipment_slot} not recognized')
        if equipment_slot == 'armor':
            self.armor = item_obj
        elif equipment_slot == 'shield':
            self.shield = item_obj
        elif equipment_slot == 'weapon':
            self.weapon = item_obj
        elif equipment_slot == 'wand':
            self.wand = item_obj

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


class ability_scores(object):  # has been tested
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

    # In modern D&D, the derived value from an ability score that is relevant
    # to determining outcomes is the 'stat mod' (or 'stat modifier'), which
    # is computed from the ability score by subtracting 10, dividing by 2 and
    # rounding down. That is implemented here.
    def _stat_mod(self, ability_score):
        if not hasattr(self, ability_score):
            raise internal_exception(f'unrecognized ability {ability_score}')
        return math.floor((getattr(self, ability_score) - 10) / 2)

    def __init__(self, character_class_str):
        if character_class_str not in self.weightings:
            raise internal_exception(f'character class {character_class_str} not recognized, should be one of '
                                      "'Warrior', 'Thief', 'Priest' or 'Mage'")
        self.character_class = character_class_str

    def roll_stats(self):
        # Rolling a six-sided die 4 times and then dropping the lowest roll
        # before summing the remaining 3 results to reach a value for an
        # ability score (or 'stat') is the traditional method for generating
        # D&D ability scores. It is reproduced here.
        results_list = list()
        for _ in range(0, 6):
            four_rolls = sorted([random.randint(1, 6) for _ in range(0, 4)])
            three_rolls = four_rolls[1:4]
            results_list.append(sum(three_rolls))
        results_list.sort()
        results_list.reverse()
        for index in range(0, 6):
            setattr(self, self.weightings[self.character_class][index], results_list[index])


class creature(ini_entry, character):
    __slots__ = ('internal_name', 'character_name', 'description', 'character_class', 'species', '_strength',
                 '_dexterity', '_constitution', '_intelligence', '_wisdom', '_charisma', '_items_state_obj',
                 '_base_hit_points', '_weapon_equipped', '_armor_equipped', '_shield_equipped')

    def __init__(self, items_state_obj, internal_name, **argd):
        character_init_argd, ini_entry_init_argd, equipment_argd, inventory_qty_name_pairs = \
            self._separate_argd_into_different_arg_sets(items_state_obj, internal_name, **argd)
        ini_entry.__init__(self, internal_name=internal_name, **ini_entry_init_argd)
        self._post_init_slots_set_none(self.__slots__)
        character.__init__(self, **character_init_argd)
        self._init_inventory_and_equipment(items_state_obj, inventory_qty_name_pairs, equipment_argd)
        self._items_state_obj = items_state_obj

    # Divides the argd passed to __init__ into arguments for
    # character.__init__, arguments for ini_entry.__init__, arguments to
    # character.equip_*, and arguments to character.pick_up_item.
    #
    # argd is accepted as a ** argument so it's passed by copy rather than by reference.
    def _separate_argd_into_different_arg_sets(self, items_state_obj, internal_name, **argd):
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
        if any(not items_state_obj.contains(inventory_internal_name)
               for _, inventory_internal_name in inventory_qty_name_pairs):
            missing_names = tuple(item_internal_name for _, item_internal_name in inventory_qty_name_pairs
                                  if not items_state_obj.contains(item_internal_name))
            pluralizer = 's' if len(missing_names) > 1 else ''
            raise internal_exception(f'bad creatures.ini specification for creature {internal_name}: creature '
                                     f'ini config dict `inventory_items` value indicated item{pluralizer}'
                                     " not present in `items_state` argument: " + (', '.join(missing_names)))
        ini_entry_init_argd = argd
        return character_init_argd, ini_entry_init_argd, equipment_argd, inventory_qty_name_pairs

    def _init_inventory_and_equipment(self, items_state_obj, inventory_qty_name_pairs, equipment_argd):
        for item_qty, item_internal_name in inventory_qty_name_pairs:
            item_obj = items_state_obj.get(item_internal_name)
            for index in range(0, item_qty):
                self.pick_up_item(item_obj)
        for equipment_key, item_internal_name in equipment_argd.items():
            if not items_state_obj.contains(item_internal_name):
                raise internal_exception(f'bad creatures.ini specification for creature {self.internal_name}: items '
                                         f'index object does not contain an item named {item_internal_name}')
            item_obj = items_state_obj.get(item_internal_name)
            if equipment_key == 'weapon_equipped':
                self.equip_weapon(item_obj)
            elif equipment_key == 'armor_equipped':
                self.equip_armor(item_obj)
            elif equipment_key == 'shield_equipped':
                self.equip_shield(item_obj)
            else:  # by exclusion, the value must be 'wand_equipped'
                self.equip_wand(item_obj)

    def convert_to_corpse(self):
        internal_name = self.internal_name
        description = self.description_dead
        title = f'{self.title} corpse'
        corpse_obj = corpse(self._items_state_obj, internal_name, container_type='corpse', description=description, title=title)
        for item_internal_name, (item_qty, item_obj) in self.inventory.items():
            corpse_obj.set(item_internal_name, item_qty, item_obj)
        return corpse_obj


class container(ini_entry, items_multi_state):
    __slots__ = 'internal_name', 'title', 'description', 'is_locked', 'is_closed', 'container_type'

    def __init__(self, item_state_obj, internal_name, *item_objs, **ini_constr_argd):
        contents_str = ini_constr_argd.pop('contents', None)
        ini_entry.__init__(self, internal_name=internal_name, **ini_constr_argd)
        if contents_str:
            contents_qtys_names = self._process_list_value(contents_str)
            contents_qtys_item_objs = tuple((item_qty, item_state_obj.get(item_internal_name)) for item_qty, item_internal_name in contents_qtys_names)
        items_multi_state.__init__(self)
        if contents_str:
            for item_qty, item_obj in contents_qtys_item_objs:
                self.set(item_obj.internal_name, item_qty, item_obj)
        self._post_init_slots_set_none(self.__slots__)

class chest(container):
    pass


class corpse(container):
    pass


class item(ini_entry):  # has been tested
    __slots__ = ('internal_name', 'title', 'description', 'weight', 'value', 'damage', 'attack_bonus', 'armor_bonus', 'item_type', 'warrior_can_use',
                 'thief_can_use', 'priest_can_use', 'mage_can_use', 'hit_points_recovered', 'mana_points_recovered')

    def __init__(self, **argd):
        super().__init__(**argd)
        self._post_init_slots_set_none(self.__slots__)

    @classmethod
    def subclassing_factory(self, **item_dict):
        if item_dict['item_type'] == 'weapon':
            item_obj = weapon(**item_dict)
        elif item_dict['item_type'] == 'shield':
            item_obj = shield(**item_dict)
        elif item_dict['item_type'] == 'armor':
            item_obj = armor(**item_dict)
        elif item_dict['item_type'] == 'consumable':
            item_obj = consumable(**item_dict)
        elif item_dict['item_type'] == 'wand':
            item_obj = wand(**item_dict)
        elif item_dict['item_type'] == 'coin':
            item_obj = coin(**item_dict)
        return item_obj

    def usable_by(self, character_class):
        if character_class not in ('Warrior', 'Thief', 'Mage', 'Priest'):
            raise internal_exception(f'character class {character_class} not recognized')
        return bool(getattr(self, character_class.lower() + '_can_use', None))


# The subclasses don't have much differing functionality but accurately
# typing each item allows classes that handle items of specific types, like
# equipment(), to use isinstance to determine if a valid item has been
# supplied as an argument.
class coin(item):
    pass


class weapon(item):
    pass


class shield(item):
    pass


class armor(item):
    pass


class consumable(item):
    pass


class wand(item):
    pass


class room(ini_entry):  # has been tested
    __slots__ = ('internal_name', 'title', 'description', 'north_exit', 'west_exit', 'south_exit', 'east_exit',
                 'occupant', 'item', 'is_entrance', 'is_exit', '_containers_state_obj', '_creatures_state_obj',
                 '_items_state_obj', 'creature_here', 'container_here', 'items_here')

    @property
    def has_north_exit(self):
        return bool(getattr(self, 'north_exit', False))

    @property
    def has_south_exit(self):
        return bool(getattr(self, 'south_exit', False))

    @property
    def has_west_exit(self):
        return bool(getattr(self, 'west_exit', False))

    @property
    def has_east_exit(self):
        return bool(getattr(self, 'east_exit', False))

    def __init__(self, creatures_state_obj, containers_state_obj, items_state_obj, **argd):
        super().__init__(**argd)
        self._containers_state_obj = containers_state_obj
        self._creatures_state_obj = creatures_state_obj
        self._items_state_obj = items_state_obj
        self._post_init_slots_set_none(self.__slots__)
        if self.creature_here:
            if not self._creatures_state_obj.contains(self.creature_here):
                raise internal_exception(f"room obj `{self.internal_name}` creature_here value '{self.creature_here}' "
                                         "doesn't correspond to any creatures in creatures_state store")
            self.creature_here = self._creatures_state_obj.get(self.creature_here)
        if self.container_here:
            if not self._containers_state_obj.contains(self.container_here):
                raise internal_exception(f"room obj `{self.internal_name}` container_here value '{self.container_here}'"
                                         " doesn't correspond to any creatures in creatures_state store")
            self.container_here = self._containers_state_obj.get(self.container_here)
        if self.items_here:
            items_here_names_list = self._process_list_value(self.items_here)
            items_state_obj = items_multi_state()
            for item_qty, item_internal_name in items_here_names_list:
                item_obj = self._items_state_obj.get(item_internal_name)
                items_state_obj.set(item_internal_name, item_qty, item_obj)
            self.items_here = items_state_obj


class items_multi_state(items_state):

    def __init__(self, **argd):
        items_state.__init__(self, **argd)

        # I preload the dict's items() sequence outside of the loop because
        # the loop alters the dict and I don't want a concurrent update error.
        contents_items = tuple(self._contents.items())
        for item_internal_name, item_obj in contents_items:
            self._contents[item_internal_name] = (1, item_obj)

    def contains(self, item_internal_name):
        return(any(contained_item_obj.internal_name == item_internal_name for _, contained_item_obj in self._contents.values()))

    def set(self, item_internal_name, item_qty, item_obj):
        self._contents[item_internal_name] = item_qty, item_obj

    def add_one(self, item_internal_name, item_obj):
        if self.contains(item_internal_name):
            self._contents[item_internal_name] = self._contents[item_internal_name][0] + 1, self._contents[item_internal_name][1]
        else:
            self._contents[item_internal_name] = 1, item_obj

    def remove_one(self, item_internal_name):
        if item_internal_name not in self._contents:
            raise KeyError(item_internal_name)
        elif self._contents[item_internal_name][0] == 1:
            del self._contents[item_internal_name]
        else:
            self._contents[item_internal_name] = self._contents[item_internal_name][0] - 1, self._contents[item_internal_name][1]


class game_state(object):
    __slots__ = ('_character_name', '_character_class', 'character', 'rooms_state', 'containers_state',
                 'items_state', 'creatures_state', 'game_has_begun', 'game_has_ended')

    character_name = property(fget=(lambda self: self._character_name),
                              fset=(lambda self, val: setattr(self, '_character_name', val)
                                        or self._incept_character_obj_if_possible()))

    character_class = property(fget=(lambda self: self._character_class),
                               fset=(lambda self, val: setattr(self, '_character_class', val)
                                         or self._incept_character_obj_if_possible()))

    def __init__(self, rooms_state_obj, creatures_state_obj, containers_state_obj, items_state_obj):
        self.items_state = items_state_obj
        self.containers_state = containers_state_obj
        self.creatures_state = creatures_state_obj
        self.rooms_state = rooms_state_obj
        self._character_name = ''
        self._character_class = ''
        self.game_has_begun = False
        self.game_has_ended = False

    # The character object can't be instantiated until the `character_name`
    # and `character_class` attributes are set, but that happens after
    # initialization; so the `character_name` and `character_class` setters
    # call this method prospectively each time either is called to check if both
    # have been set and `character` object instantiation can proceed.
    def _incept_character_obj_if_possible(self):
        if getattr(self, 'character_name', None) and getattr(self, 'character_class', None):
            self.character = character(self.character_name, self.character_class)


class ini_entry(object):

    inventory_list_value_re = re.compile(r'^\[(([1-9][0-9]*x[A-Z][A-Za-z_]+)(,[1-9][0-9]*x[A-Z][A-Za-z_]+)*)\]$')

    def __init__(self, **argd):
        for key, value in argd.items():
            if isinstance(value, str):
                if value.lower() == 'false':
                    value = False
                elif value.lower() == 'true':
                    value = True
                elif value.isdigit():
                    value = int(value)
                elif isfloat(value):
                    value = float(value)
            setattr(self, key, value)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in self.__slots__)

    def _post_init_slots_set_none(self, slots):
        for key in slots:
            if not hasattr(self, key):
                setattr(self, key, None)

    def _process_list_value(self, inventory_value):
        value_match = self.inventory_list_value_re.match(inventory_value)
        inner_capture = value_match.groups(1)[0]
        capture_split = inner_capture.split(',')
        qty_strval_pairs = tuple((int(item_qty), item_name) for item_qty, item_name in (
                                    name_x_qty_str.split('x', maxsplit=1) for name_x_qty_str in capture_split)
                                )
        return qty_strval_pairs


class state(abc.ABC):
    __slots__ = '_contents',

    __abstractmethods__ = frozenset(('__init__',))

    def contains(self, item_internal_name):  # check
        return any(item_internal_name == contained_item_obj.internal_name for contained_item_obj in self._contents.values())

    def get(self, item_internal_name):  # check
        return self._contents[item_internal_name]

    def set(self, item_internal_name, item_obj):  # check
        self._contents[item_internal_name] = item_obj

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


class containers_state(items_state):
    __slots__ = '_contents',

    def __init__(self, items_state_obj, **dict_of_dicts):
        self._contents = dict()
        for container_internal_name, container_dict in dict_of_dicts.items():
            container_obj = container(items_state_obj, container_internal_name, **container_dict)
            self._contents[container_internal_name] = container_obj


class creatures_state(state):

    def __init__(self, items_state_obj, **dict_of_dicts):
        self._contents = dict()
        for creature_internal_name, creature_dict in dict_of_dicts.items():
            creature_obj = creature(items_state_obj, internal_name=creature_internal_name, **creature_dict)
            self.set(creature_obj.internal_name, creature_obj)


class rooms_state(object):  # has been tested
    __slots__ = '_creatures_state_obj', '_containers_state_obj', '_items_state_obj', '_rooms_objs', '_room_cursor'

    @property
    def cursor(self):
        return self._rooms_objs[self._room_cursor]

    def __init__(self, creatures_state_obj, containers_state_obj, items_state_obj, **dict_of_dicts):
        self._rooms_objs = dict()
        self._creatures_state_obj = creatures_state_obj
        self._containers_state_obj = containers_state_obj
        self._items_state_obj = items_state_obj
        for room_internal_name, room_dict in dict_of_dicts.items():
            room_obj = room(creatures_state_obj, containers_state_obj, items_state_obj,
                            internal_name=room_internal_name, **room_dict)
            if room_obj.is_entrance:
                self._room_cursor = room_obj.internal_name
            self._store_room(room_obj.internal_name, room_obj)

    def _store_room(self, room_internal_name, room_obj):
        self._rooms_objs[room_internal_name] = room_obj

    def move(self, north=False, west=False, south=False, east=False):
        if (north and west) or (north and south) or (north and east) or (west and south) or (west and east) or (south and east):
            raise internal_exception('move() must receive only *one* True argument of the four keys `north`, `south`, `east` and `west`')
        if north:
            exit_name = 'north_exit'
            exit_key = '<NORTH>'
        elif west:
            exit_name = 'west_exit'
            exit_key = 'WEST'
        elif south:
            exit_name = 'south_exit'
            exit_key = 'SOUTH'
        elif east:
            exit_name = 'east_exit'
            exit_key = 'EAST'
        if not getattr(self.cursor, exit_name):
            raise bad_command_exception('MOVE', f'This room has no <{exit_key}> exit.')
        new_room_dest = self._rooms_objs[getattr(self.cursor, exit_name)]
        self._room_cursor = new_room_dest.internal_name
