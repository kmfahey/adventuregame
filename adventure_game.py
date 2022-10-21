#!/usr/bin/python

import math
import random
import re

import iniconfig


__export__ = ('ability_scores', 'armor', 'bad_command_exception', 'character', 'consumable',
              'dice_expr_to_randint_closure', 'dungeon_room', 'equipment', 'ini_file_entry', 'internal_exception',
              'inventory', 'isfloat', 'item', 'items_index', 'room_navigator', 'shield', 'wand', 'weapon')


# Python3's str class doesn't offer a method to test if the string constitutes
# a float value so I rolled my own.
_float_re = re.compile(r'^[+-]?([0-9]+\.|\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+)$')

isfloat = lambda strval: bool(_float_re.match(strval))


# In D&D, the standard notation for dice rolling is of the form
# [1-9][0-9]*d[1-9]+[0-9]*([+-][1-9][0-9]*)?, where the first number indicates
# how many dice to roll, the second number is the number of sides of the die
# to roll, and the optional third number is a positive or negative value to
# add to the result of the roll to reach the final outcome. As an example,
# 1d20+3 indicates a roll of one 20-sided die to which 3 should be added.
#
# I have used this notation in the items.ini file since it's the simplest
# way to compactly express weapon damage, and in the attack roll methods
# to call for a d20 roll (the standard D&D conflict resolution roll). This
# function parses those expressions and returns a closure that executes
# random.randint appropriately to simulate dice rolls of the dice indicated by
# the expression.
dice_expression_re = re.compile(r'([1-9]+)d([1-9][0-9]*)([-+][1-9][0-9]*)?')


def dice_expr_to_randint_closure(dice_expression, additional_mod=0):
    dice_match = dice_expression_re.match(dice_expression)
    if not dice_match:
        raise internal_exception(f"unable to parse dice expresson '{dice_expression}' using regular expressions")
    match_groups = dice_match.groups()
    number_of_dice = int(match_groups[0])
    die_number_of_sides = int(match_groups[1])
    modifier_to_roll = (int(match_groups[2]) if match_groups[2] is not None else 0) + additional_mod
    returnFunc = lambda: sum(random.randint(1, die_number_of_sides) for _ in range(0, number_of_dice)) + modifier_to_roll

    # Conveniently, a function object allows arbitrary attributes to be set.
    # It's impossible to read the code inside a closure so I set identifying
    # attributes on the function object that allow the results to be tested in
    # test_adventure_game.py
    setattr(returnFunc, 'dice', f'{number_of_dice}d{die_number_of_sides}')
    setattr(returnFunc, 'modifier', ('+' if modifier_to_roll >= 0 else '') + str(modifier_to_roll))
    return returnFunc


class internal_exception(Exception):
    pass


class bad_command_exception(Exception):
    __slots__ = 'command', 'message'

    def __init__(self, command_str, message_str):
        self.command = command_str
        self.message = message_str



class command_processor(object):
    pass


class command(object):
    pass


class move_command(command):
    pass


class pick_up_command(command):
    pass


class drop_command(command):
    pass


class inspect_command(command):
    pass


class unlock_command(command):
    pass


class open_command(command):
    pass


class close_command(command):
    pass


class attack_command(command):
    pass


class steal_command(command):
    pass


class sell_command(command):
    pass


class talk_command(command):
    pass


class buy_command(command):
    pass


class character(object):  # has been tested
    __slots__ = 'character_class', '_hit_point_maximum', '_current_hit_points', '_ability_scores_obj', '_inventory_obj', '_equipment_obj'

    _hitpoint_base = {'Warrior': 40, 'Priest': 30, 'Thief': 30, 'Mage': 20}

    def __init__(self, character_class_str):
        if character_class_str not in {'Warrior', 'Thief', 'Priest', 'Mage'}:
            raise internal_exception('character class argument {character_class_str} not one of Warrior, Thief, Priest or Mage')
        self.character_class = character_class_str
        self._ability_scores_obj = ability_scores(character_class_str)
        self._inventory_obj = inventory()
        self._ability_scores_obj.roll_stats()
        self._equipment_obj = equipment(character_class_str)
        self._hit_point_maximum = self._current_hit_points = self._hitpoint_base[character_class_str] + self._ability_scores_obj.constitution_mod * 3

    def _attack_or_damage_stat_dependency(self):
        if self.character_class in ('Warrior', 'Priest') or (self.character_class == 'Mage' and self._equipment_obj.weapon_equipped):
            return 'strength'
        elif self.character_class == 'Thief':
            return 'dexterity'
        else:  # By exclusion, (`character_class` == 'Mage' and self._equipment_obj.wand_equipped)
            return 'intelligence'

    _item_attacking_with = property(lambda self: self._equipment_obj.weapon if not self._equipment_obj.wand_equipped else self._equipment_obj.wand)

    hit_points = property(lambda self: self._current_hit_points, lambda self, value: setattr(self, '_current_hit_points', value))

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

    is_alive = property(lambda self: self._current_hit_points > 0)

    is_dead = property(lambda self: self._current_hit_points == 0)

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
        return dice_expr_to_randint_closure('1d20', item_attacking_with.attack_bonus + stat_mod)

    @property
    def damage_roll(self):
        stat_dependency = self._attack_or_damage_stat_dependency()
        item_attacking_with = self._item_attacking_with
        return dice_expr_to_randint_closure(item_attacking_with.damage.dice, int(item_attacking_with.damage.modifier) + getattr(self._ability_scores_obj, stat_dependency+'_mod'))

    # This class keeps its `ability_scores`, `equipment` and `inventory` objects
    # in private attributes, just as a matter of good OOP design. In the cases
    # of the `ability_scores` and `equipment` objects, these passthrough methods
    # are necessary so the concealed objects' functionality can be accessed
    # from code that only has the `character` object.
    #
    # The `inventory` object presents a customized mapping interface that
    # character action management code doesn't need to access, so only a few
    # methods are offered.

    total_weight = property(lambda self: self._inventory_obj.total_weight)

    burden = property(lambda self: self._inventory_obj.burden_for_strength_score(self._ability_scores_obj.strength))

    def pick_up_item(self, item_obj):
        self._inventory_obj.add_one(item_obj.internal_name, item_obj)

    def drop_item(self, item_obj):
        if not self._inventory_obj.contains(item_obj.internal_name):
            raise bad_command_exception('DROP', f"You can't drop the item {item_obj.title} because you aren't carrying one.")
        self._inventory_obj.remove_one(item_obj.internal_name)

    def list_items(self):
        return list(sorted(self._inventory_obj.values(), key=lambda *argl: argl[0][1].title))

    # BEGIN passthrough methods for private _ability_scores_obj
    strength = property(lambda self: getattr(self._ability_scores_obj, 'strength'))

    dexterity = property(lambda self: getattr(self._ability_scores_obj, 'dexterity'))

    constitution = property(lambda self: getattr(self._ability_scores_obj, 'constitution'))

    intelligence = property(lambda self: getattr(self._ability_scores_obj, 'intelligence'))

    wisdom = property(lambda self: getattr(self._ability_scores_obj, 'wisdom'))

    charisma = property(lambda self: getattr(self._ability_scores_obj, 'charisma'))

    strength_mod = property(lambda self: self._ability_scores_obj._stat_mod('strength'))

    dexterity_mod = property(lambda self: self._ability_scores_obj._stat_mod('dexterity'))

    constitution_mod = property(lambda self: self._ability_scores_obj._stat_mod('constitution'))

    intelligence_mod = property(lambda self: self._ability_scores_obj._stat_mod('intelligence'))

    wisdom_mod = property(lambda self: self._ability_scores_obj._stat_mod('wisdom'))

    charisma_mod = property(lambda self: self._ability_scores_obj._stat_mod('charisma'))
    # END passthrough methods for private _ability_scores_obj

    # BEGIN passthrough methods for private _equipment_obj
    armor_equipped = property(lambda self: self._equipment_obj.armor_equipped)

    shield_equipped = property(lambda self: self._equipment_obj.shield_equipped)

    weapon_equipped = property(lambda self: self._equipment_obj.weapon_equipped)

    wand_equipped = property(lambda self: self._equipment_obj.wand_equipped)

    armor = property(lambda self: self._equipment_obj.armor)

    shield = property(lambda self: self._equipment_obj.shield)

    weapon = property(lambda self: self._equipment_obj.weapon)

    wand = property(lambda self: self._equipment_obj.wand)

    def equip_armor(self, item_obj):
        if not self._inventory_obj.contains(item_obj.internal_name):
            raise internal_exception("equipping an `item` object that is not in the character's `inventory` object is not allowed")
        return self._equipment_obj.equip_armor(item_obj)

    def equip_shield(self, item_obj):
        if not self._inventory_obj.contains(item_obj.internal_name):
            raise internal_exception("equipping an `item` object that is not in the character's `inventory` object is not allowed")
        return self._equipment_obj.equip_shield(item_obj)

    def equip_weapon(self, item_obj):
        if not self._inventory_obj.contains(item_obj.internal_name):
            raise internal_exception("equipping an `item` object that is not in the character's `inventory` object is not allowed")
        return self._equipment_obj.equip_weapon(item_obj)

    def equip_wand(self, item_obj):
        if not self._inventory_obj.contains(item_obj.internal_name):
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

    @property
    def damage_bonus(self):
        if not (self._equipment_obj.weapon_equipped or self.character_class == 'Mage' and self._equipment_obj.wand_equipped):
            raise internal_exception('The character does not have a weapon equipped; no valid value for `damage` can be computed.')
        stat_dependency = self._attack_or_damage_stat_dependency()

        # I don't use this closure; this is just a quick way of accessing
        # its parsing logic to combine any terminating '+[1-9][0-9]*'
        # value that may be on the damage string with the modifier we have
        # in hand, without having to use the regex here and duplicate
        # `dice_expr_to_randint_closure()`'s code.
        if self._equipment_obj.weapon_equipped:
            return int(self._equipment_obj.weapon.damage.modifier) + getattr(self._ability_scores_obj, stat_dependency + '_mod')
        else:  # relying on the shield statement at the top of this method, by exclusion, self._equipment_obj.weapon_equipped is True
            return int(self._equipment_obj.wand.damage.modifier) + getattr(self._ability_scores_obj, stat_dependency + '_mod')


class equipment(object):  # has been tested
    __slots__ = 'character_class', 'armor', 'shield', 'weapon', 'wand'

    armor_equipped = property(lambda self: bool(getattr(self, 'armor', None)))

    shield_equipped = property(lambda self: bool(getattr(self, 'shield', None)))

    weapon_equipped = property(lambda self: bool(getattr(self, 'weapon', None)))

    wand_equipped = property(lambda self: bool(getattr(self, 'wand', None)))

    def __init__(self, character_class, armor_item=None, shield_item=None, weapon_item=None):
        self.character_class = character_class
        self.armor = armor_item
        self.shield = shield_item
        self.weapon = weapon_item

    def equip_armor(self, item_obj):
        if not isinstance(item_obj, armor):
            raise internal_exception('the method `equip_armor()` only accepts `armor` objects for its argument')
        if not item_obj.usable_by(self.character_class):
            raise bad_command_exception('EQUIP', "A {self.character_class} can't wear {item_obj.title} armor.")
        self._equip('armor', item_obj)

    def equip_shield(self, item_obj):
        if not isinstance(item_obj, shield):
            raise internal_exception('the method `equip_shield()` only accepts `shield` objects for its argument')
        if not item_obj.usable_by(self.character_class):
            raise bad_command_exception('EQUIP', "A {self.character_class} can't use shields.")
        self._equip('shield', item_obj)

    def equip_weapon(self, item_obj):
        if not isinstance(item_obj, weapon):
            raise internal_exception('the method `equip_weapon()` only accepts `weapon` objects for its argument')
        if not item_obj.usable_by(self.character_class):
            raise bad_command_exception('EQUIP', "A {self.character_class} can't wield a {item_obj.title}.")
        self._equip('weapon', item_obj)

    def equip_wand(self, item_obj):
        if not isinstance(item_obj, wand):
            raise internal_exception('the method `equip_wand()` only accepts `wand` objects for its argument')
        if not item_obj.usable_by(self.character_class):
            raise bad_command_exception('EQUIP', "A {self.character_class} can't use a wand.")
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

    strength_mod = property(lambda self: self._stat_mod('strength'))

    dexterity_mod = property(lambda self: self._stat_mod('dexterity'))

    constitution_mod = property(lambda self: self._stat_mod('constitution'))

    intelligence_mod = property(lambda self: self._stat_mod('intelligence'))

    wisdom_mod = property(lambda self: self._stat_mod('wisdom'))

    charisma_mod = property(lambda self: self._stat_mod('charisma'))

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
            raise internal_exception(f"character class {character_class_str} not recognized, should be one of 'Warrior', 'Thief', 'Priest' or 'Mage'")
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


class ini_file_entry(object):

    def __init__(self, **argd):
        for key in self.__slots__:
            value = argd.pop(key, None)
            if isinstance(value, str):
                if value.lower() == 'false':
                    value = False
                elif value.lower() == 'true':
                    value = True
                elif value.isdigit():
                    value = int(value)
                elif isfloat(value):
                    value = float(value)
                elif dice_expression_re.match(value):
                    value = dice_expr_to_randint_closure(value)
            setattr(self, key, value)
        if len(argd.keys()):
            raise internal_exception('unexpected argument keys received: ' + ', '.join(argd.keys()))


class items_index(object):  # has been tested
    __slots__ = '_items_objs',

    def __init__(self, ini_config_obj):
        self._items_objs = dict()
        for item_internal_name, item_dict in ini_config_obj.sections.items():
            item_obj = item.subclassing_factory(internal_name=item_internal_name, **item_dict)
            self._items_objs[item_internal_name] = item_obj

    def contains(self, item_internal_name):  # check
        return any(item_internal_name == contained_item_obj.internal_name for contained_item_obj in self._items_objs.values())

    def get(self, item_internal_name):  # check
        return self._items_objs[item_internal_name]

    def set(self, item_internal_name, item_obj):  # check
        self._items_objs[item_internal_name] = item_obj

    def delete(self, item_internal_name):  # check
        del self._items_objs[item_internal_name]

    def keys(self):  # check
        return self._items_objs.keys()

    def values(self):  # check
        return self._items_objs.values()

    def items(self):  # check
        return self._items_objs.items()

    def size(self):  # check
        return len(self._items_objs)


class item(ini_file_entry):  # has been tested
    __slots__ = ('internal_name', 'title', 'description', 'weight', 'value', 'damage', 'attack_bonus', 'armor_bonus', 'item_type', 'warrior_can_use',
                 'thief_can_use', 'priest_can_use', 'mage_can_use')

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
        return item_obj

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in self.__slots__)

    def usable_by(self, character_class):
        if character_class not in ('Warrior', 'Thief', 'Mage', 'Priest'):
            raise internal_exception(f'character class {character_class} not recognized')
        return bool(getattr(self, character_class.lower() + '_can_use', None))


# The subclasses don't have much differing functionality but accurately
# typing each item allows classes that handle items of specific types, like
# equipment(), to use isinstance to determine if a valid item has been
# supplied as an argument.
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


class inventory(object):  # has been tested
    __slots__ = '_items_counted_objs',

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

    def __init__(self, *argl):
        self._items_counted_objs = dict()
        if len(argl) == 1 and isinstance(argl[0], iniconfig.IniConfig):
            for section_name, item_dict in argl[0].sections.items():
                item_obj = item.subclassing_factory(internal_name=section_name, **item_dict)
                self.add_one(section_name, item_obj)
        elif all(isinstance(argval, item) for argval in argl):
            for argval in argl:
                self.add_one(argval.internal_name, argval)
        else:
            raise internal_exception('inventory constructor got unexpected arguments ' + repr(argl))

    def contains(self, item_internal_name):
        return(any(contained_item_obj.internal_name == item_internal_name for _, contained_item_obj in self._items_counted_objs.values()))

    def get(self, item_internal_name):
        return self._items_counted_objs[item_internal_name]

    def set(self, item_internal_name, item_qty, item_obj):
        self._items_counted_objs[item_internal_name] = item_qty, item_obj

    def add_one(self, item_internal_name, item_obj):
        if self.contains(item_internal_name):
            self._items_counted_objs[item_internal_name] = self._items_counted_objs[item_internal_name][0] + 1, self._items_counted_objs[item_internal_name][1]
        else:
            self._items_counted_objs[item_internal_name] = 1, item_obj

    def remove_one(self, item_internal_name):
        if item_internal_name not in self._items_counted_objs:
            raise KeyError(item_internal_name)
        elif self._items_counted_objs[item_internal_name][0] == 1:
            del self._items_counted_objs[item_internal_name]
        else:
            self._items_counted_objs[item_internal_name] = self._items_counted_objs[item_internal_name][0] - 1, self._items_counted_objs[item_internal_name][1]

    def delete(self, item_internal_name):
        del self._items_counted_objs[item_internal_name]

    def keys(self):
        return self._items_counted_objs.keys()

    def values(self):
        return self._items_counted_objs.values()

    def items(self):
        return self._items_counted_objs.items()

    def size(self):
        return len(self._items_counted_objs)

    @property
    def total_weight(self):
        total_weight_val = 0
        for item_name, (item_count, item_obj) in self._items_counted_objs.items():
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


class dungeon_room(ini_file_entry):  # has been tested
    __slots__ = 'internal_name', 'title', 'description', 'north_exit', 'west_exit', 'south_exit', 'east_exit', 'occupant', 'item', 'is_entrance', 'is_exit'

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


class room_navigator(object):  # has been tested
    __slots__ = '_rooms_objs', '_room_cursor'

    @property
    def cursor(self):
        return self._rooms_objs[self._room_cursor]

    def __init__(self, ini_config_obj):
        self._rooms_objs = dict()
        for room_internal_name, room_dict in ini_config_obj.sections.items():
            dungeon_room_obj = dungeon_room(internal_name=room_internal_name, **room_dict)
            if dungeon_room_obj.is_entrance:
                self._room_cursor = dungeon_room_obj.internal_name
            self._store_room(dungeon_room_obj.internal_name, dungeon_room_obj)

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
