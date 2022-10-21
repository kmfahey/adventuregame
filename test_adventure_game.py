#!/usr/bin/python3

import math
import operator
import os
import tempfile
import unittest

import iniconfig

from adventure_game import *



class test_isfloat(unittest.TestCase):

    def test_isfloat(self):
        self.assertTrue(isfloat('+5.6'))
        self.assertTrue(isfloat('-5.6'))
        self.assertTrue(isfloat('5.6'))
        self.assertTrue(isfloat('5.'))
        self.assertTrue(isfloat('.6'))
        self.assertTrue(isfloat('6'))
        self.assertFalse(isfloat('.'))
        self.assertFalse(isfloat('+'))
        self.assertFalse(isfloat('-'))


class test_dice_expr_to_randint_closure(unittest.TestCase):

    def test_dice_expr_to_randint_closure(self):
        closure_obj = dice_expr_to_randint_closure('1d20+6')
        self.assertEqual(closure_obj.dice, '1d20')
        self.assertEqual(closure_obj.modifier, '+6')
        closure_obj = dice_expr_to_randint_closure('1d20+3', 3)
        self.assertEqual(closure_obj.dice, '1d20')
        self.assertEqual(closure_obj.modifier, '+6')
        closure_obj = dice_expr_to_randint_closure('1d20', 6)
        self.assertEqual(closure_obj.dice, '1d20')
        self.assertEqual(closure_obj.modifier, '+6')


class test_character(unittest.TestCase):
    __slots__ = 'equipment_ini_config_obj',

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(test_equipment.equipment_ini_config_text)
        temp_ini_config_fh.close()
        self.equipment_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.items_index_obj = items_index(self.equipment_ini_config_obj)

    def test_attack_and_damage_rolls_1(self):
        character_obj = character('Warrior')
        longsword_obj = self.items_index_obj.get('Longsword')
        scale_mail_obj = self.items_index_obj.get('Scale_Mail')
        shield_obj = self.items_index_obj.get('Shield')
        with self.assertRaises(internal_exception):
            character_obj.equip_weapon(longsword_obj)
        character_obj.pick_up_item(longsword_obj)
        character_obj.pick_up_item(scale_mail_obj)
        character_obj.pick_up_item(shield_obj)
        character_obj.equip_weapon(longsword_obj)
        character_obj.equip_armor(scale_mail_obj)
        character_obj.equip_shield(shield_obj)
        self.assertTrue(character_obj.armor_equipped)
        self.assertTrue(character_obj.shield_equipped)
        self.assertTrue(character_obj.weapon_equipped)
        self.assertFalse(character_obj.wand_equipped)
        self.assertEqual(character_obj.attack_roll.dice, '1d20')
        self.assertEqual(int(character_obj.attack_roll.modifier), character_obj.strength_mod)
        self.assertEqual(character_obj.damage_roll.dice, '1d8')
        self.assertEqual(int(character_obj.damage_roll.modifier), character_obj.strength_mod)
        self.assertEqual(int(character_obj.attack_bonus), character_obj.strength_mod)
        self.assertEqual(character_obj.armor_class, 10 + scale_mail_obj.armor_bonus + shield_obj.armor_bonus
                                                    + character_obj.dexterity_mod)
        self.assertEqual(character_obj.damage_bonus, character_obj.strength_mod)
        self.assertEqual(character_obj.weapon, longsword_obj)
        self.assertEqual(character_obj.armor, scale_mail_obj)
        self.assertEqual(character_obj.shield, shield_obj)

    def test_attack_and_damage_rolls_2(self):
        character_obj = character('Mage')
        wand_obj = self.items_index_obj.get('Magic_Wand')
        character_obj.pick_up_item(wand_obj)
        character_obj.equip_wand(wand_obj)
        self.assertFalse(character_obj.armor_equipped)
        self.assertFalse(character_obj.shield_equipped)
        self.assertFalse(character_obj.weapon_equipped)
        self.assertTrue(character_obj.wand_equipped)
        self.assertEqual(character_obj.attack_roll.dice, '1d20')
        self.assertEqual(int(character_obj.attack_roll.modifier), wand_obj.attack_bonus
                                                                  + character_obj.intelligence_mod)
        self.assertEqual(character_obj.damage_roll.dice, '2d12')
        self.assertEqual(int(character_obj.damage_roll.modifier), int(wand_obj.damage.modifier)
                                                                  + character_obj.intelligence_mod)
        self.assertEqual(character_obj.attack_bonus, int(wand_obj.attack_bonus)
                                                     + character_obj.intelligence_mod)
        self.assertEqual(character_obj.damage_bonus, int(wand_obj.damage.modifier)
                                                     + character_obj.intelligence_mod)
        self.assertEqual(character_obj.armor_class, 10 + character_obj.dexterity_mod)
        self.assertEqual(character_obj.wand, wand_obj)

    def test_pickup_vs_drop_vs_list(self):
        character_obj = character('Warrior')
        longsword_obj = self.items_index_obj.get('Longsword')
        scale_mail_obj = self.items_index_obj.get('Scale_Mail')
        shield_obj = self.items_index_obj.get('Shield')
        character_obj.pick_up_item(longsword_obj)
        character_obj.pick_up_item(scale_mail_obj)
        character_obj.pick_up_item(shield_obj)
        self.assertEqual(character_obj.total_weight, longsword_obj.weight + scale_mail_obj.weight + shield_obj.weight)
                                                     # The items total weight is 54.
        if character_obj.strength <= 5:
            self.assertEqual(character_obj.burden, inventory.Immobilized)
        elif character_obj.strength <= 8:
            self.assertEqual(character_obj.burden, inventory.Heavy)
        elif character_obj.strength <= 13:
            self.assertEqual(character_obj.burden, inventory.Medium)
        else:
            self.assertEqual(character_obj.burden, inventory.Light)
        testing_items_list = tuple(sorted((longsword_obj, scale_mail_obj, shield_obj),
                                          key=operator.attrgetter('title')))
        given_items_list = tuple(sorted(map(operator.itemgetter(1), character_obj.list_items()),
                                        key=operator.attrgetter('title')))
        self.assertEqual(testing_items_list, given_items_list)
        character_obj.drop_item(longsword_obj)
        character_obj.drop_item(scale_mail_obj)
        character_obj.drop_item(shield_obj)
        self.assertEqual(character_obj.total_weight, 0)

    def test_character_ability_scores(self):
        character_obj = character('Warrior')
        self.assertEqual(math.floor((character_obj.strength - 10) / 2), character_obj.strength_mod)
        self.assertEqual(math.floor((character_obj.dexterity - 10) / 2), character_obj.dexterity_mod)
        self.assertEqual(math.floor((character_obj.constitution - 10) / 2), character_obj.constitution_mod)
        self.assertEqual(math.floor((character_obj.intelligence - 10) / 2), character_obj.intelligence_mod)
        self.assertEqual(math.floor((character_obj.wisdom - 10) / 2), character_obj.wisdom_mod)
        self.assertEqual(math.floor((character_obj.charisma - 10) / 2), character_obj.charisma_mod)

    def test_character_hitpoints_and_taking_damage_and_healing(self):
        character_obj = character('Warrior')
        self.assertEqual(character_obj.hit_points, 40 + 3 * character_obj.constitution_mod)
        character_obj = character('Priest')
        self.assertEqual(character_obj.hit_points, 30 + 3 * character_obj.constitution_mod)
        character_obj = character('Thief')
        self.assertEqual(character_obj.hit_points, 30 + 3 * character_obj.constitution_mod)
        character_obj = character('Mage')
        self.assertEqual(character_obj.hit_points, 20 + 3 * character_obj.constitution_mod)
        self.assertTrue(character_obj.is_alive)
        self.assertFalse(character_obj.is_dead)
        character_obj.take_damage(20 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_points, 0)
        self.assertFalse(character_obj.is_alive)
        self.assertTrue(character_obj.is_dead)
        character_obj.heal_damage(20 + 3 * character_obj.constitution_mod)
        self.assertTrue(character_obj.is_alive)
        self.assertFalse(character_obj.is_dead)
        self.assertEqual(character_obj.hit_points, 20 + 3 * character_obj.constitution_mod)
        character_obj.hit_points -= 10
        self.assertEqual(character_obj.hit_points, 10 + 3 * character_obj.constitution_mod)
        character_obj.hit_points += 10
        self.assertEqual(character_obj.hit_points, 20 + 3 * character_obj.constitution_mod)


class test_equipment(unittest.TestCase):
    __slots__ = 'item_index_obj', 'equipment_ini_config_obj',

    equipment_ini_config_text = """
[Longsword]
title=longsword
description=A hefty sword with a long blade, a broad hilt and a leathern grip.
item_type=weapon
weight=3
value=15
damage=1d8
attack_bonus=0
warrior_can_use=true

[Staff]
title=staff
description=A balanced pole 6 feet in length with metal-shod ends.
item_type=weapon
weight=4
value=0.2
damage=1d6
attack_bonus=0
mage_can_use=true
warrior_can_use=true

[Studded_Leather]
title=studded leather armor
description=A suit of fire-hardened leather plates and padding that provides some protection from attack.
item_type=armor
weight=15
value=45
armor_bonus=2
thief_can_use=true
warrior_can_use=true

[Shield]
title=shield
description=A broad panel of leather-bound wood with a metal rim that is useful for sheltering behind.
item_type=shield
weight=6
value=10
armor_bonus=2
warrior_can_use=true
priest_can_use=true

[Scale_Mail]
title=scale mail armor
description=A suit of small steel scales linked together in a flexible plating that provides strong protection from attack.
item_type=armor
weight=45
value=50
armor_bonus=4
priest_can_use=true
warrior_can_use=true

[Magic_Sword]
title=magic sword
description=A magic sword with a palpable magic aura and an unnaturally sharp blade.
item_type=weapon
weight=3
value=15
damage=1d12+3
attack_bonus=3
warrior_can_use=true

[Magic_Wand]
title=magic wand
description=A palpably magical tapered length of polished ash wood tipped with a glowing red carnelian gem.
item_type=wand
weight=0.5
value=100
damage=2d12+3
attack_bonus=3
mage_can_use=true
"""

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(self.equipment_ini_config_text)
        temp_ini_config_fh.close()
        self.equipment_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.items_index_obj = items_index(self.equipment_ini_config_obj)

    def test_equipment(self):
        equipment_obj = equipment('Warrior')
        self.assertFalse(equipment_obj.weapon_equipped)
        self.assertFalse(equipment_obj.armor_equipped)
        self.assertFalse(equipment_obj.shield_equipped)
        self.assertFalse(equipment_obj.wand_equipped)
        equipment_obj.equip_weapon(self.items_index_obj.get('Magic_Sword'))
        self.assertTrue(equipment_obj.weapon_equipped)
        equipment_obj.equip_armor(self.items_index_obj.get('Scale_Mail'))
        self.assertTrue(equipment_obj.armor_equipped)
        equipment_obj.equip_shield(self.items_index_obj.get('Shield'))
        self.assertTrue(equipment_obj.shield_equipped)
        with self.assertRaises(internal_exception):
            equipment_obj.equip_armor(self.items_index_obj.get('Shield'))
        with self.assertRaises(bad_command_exception):
            equipment_obj.equip_wand(self.items_index_obj.get('Magic_Wand'))
        self.assertEqual(equipment_obj.armor_class, 16)
        self.assertEqual(equipment_obj.attack_bonus, 3)
        self.assertEqual(equipment_obj.damage.dice, '1d12')
        self.assertEqual(equipment_obj.damage.modifier, '+3')


class test_ability_scores(unittest.TestCase):

    def test_ability_scores_args_exception(self):
        with self.assertRaises(internal_exception):
            ability_scores('Ranger')

    def test_roll_stats(self):
        ability_scores_obj = ability_scores('Warrior')
        ability_scores_obj.roll_stats()
        self.assertTrue(ability_scores_obj.strength >= ability_scores_obj.constitution >= ability_scores_obj.dexterity
                        >= ability_scores_obj.intelligence >= ability_scores_obj.charisma >= ability_scores_obj.wisdom)
        ability_scores_obj = ability_scores('Thief')
        ability_scores_obj.roll_stats()
        self.assertTrue(ability_scores_obj.dexterity >= ability_scores_obj.constitution
                        >= ability_scores_obj.charisma >= ability_scores_obj.strength
                        >= ability_scores_obj.wisdom >= ability_scores_obj.intelligence)
        ability_scores_obj = ability_scores('Priest')
        ability_scores_obj.roll_stats()
        self.assertTrue(ability_scores_obj.wisdom >= ability_scores_obj.strength
                        >= ability_scores_obj.constitution >= ability_scores_obj.charisma
                        >= ability_scores_obj.intelligence >= ability_scores_obj.dexterity)
        ability_scores_obj = ability_scores('Mage')
        ability_scores_obj.roll_stats()
        self.assertTrue(ability_scores_obj.intelligence >= ability_scores_obj.dexterity
                        >= ability_scores_obj.constitution >= ability_scores_obj.strength
                        >= ability_scores_obj.wisdom >= ability_scores_obj.charisma)

    def test_reroll_stats(self):
        ability_scores_obj = ability_scores('Warrior')
        ability_scores_obj.roll_stats()
        first_stat_roll = (ability_scores_obj.strength, ability_scores_obj.constitution, ability_scores_obj.dexterity,
                           ability_scores_obj.intelligence, ability_scores_obj.charisma, ability_scores_obj.wisdom)
        ability_scores_obj.roll_stats()
        second_stat_roll = (ability_scores_obj.strength, ability_scores_obj.constitution, ability_scores_obj.dexterity,
                            ability_scores_obj.intelligence, ability_scores_obj.charisma, ability_scores_obj.wisdom)
        # This is a test of a method with a random element, so the results are
        # nondeterministic. I'm looking for the second call to `roll_stats()`
        # to yield different stats, but there's a chance that the results are
        # identical; so I reroll until the results are different.
        while first_stat_roll == second_stat_roll:
            ability_scores_obj.roll_stats()
            second_stat_roll = (ability_scores_obj.strength, ability_scores_obj.constitution,
                                ability_scores_obj.dexterity, ability_scores_obj.intelligence,
                                ability_scores_obj.charisma, ability_scores_obj.wisdom)
        self.assertNotEqual(first_stat_roll, second_stat_roll)


class test_inventory(unittest.TestCase):
    __slots__ = 'items_ini_config_obj', 'inventory_obj',

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(test_item_and_items_index.items_ini_config_text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.inventory_obj = inventory(self.items_ini_config_obj)

    def test_inventory_collection_methods(self):
        sword_qty, longsword_obj = self.inventory_obj.get('Longsword')
        self.assertTrue(self.inventory_obj.contains(longsword_obj.internal_name))
        self.assertEqual(sword_qty, 1)
        self.inventory_obj.add_one(longsword_obj.internal_name, longsword_obj)
        sword_qty, longsword_obj = self.inventory_obj.get('Longsword')
        self.assertEqual(sword_qty, 2)
        self.inventory_obj.remove_one('Longsword')
        sword_qty, longsword_obj = self.inventory_obj.get('Longsword')
        self.assertEqual(sword_qty, 1)
        self.inventory_obj.delete('Longsword')
        with self.assertRaises(KeyError):
            self.inventory_obj.get('Longsword')
        with self.assertRaises(KeyError):
            self.inventory_obj.remove_one('Longsword')
        with self.assertRaises(KeyError):
            self.inventory_obj.delete('Longsword')
        self.inventory_obj.set('Longsword', 1, longsword_obj)
        self.assertTrue(self.inventory_obj.contains(longsword_obj.internal_name))
        self.assertEqual(set(self.inventory_obj.keys()), {'Longsword', 'Rapier', 'Mace', 'Staff'})
        _, rapier_obj, = self.inventory_obj.get('Rapier')
        _, mace_obj, = self.inventory_obj.get('Mace')
        _, staff_obj = self.inventory_obj.get('Staff')
        inventory_values = tuple(self.inventory_obj.values())
        self.assertTrue(all((1, item_obj) in inventory_values
                            for item_obj in (longsword_obj, rapier_obj, mace_obj, staff_obj)))
        inventory_items = tuple(sorted(self.inventory_obj.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Longsword', (1, longsword_obj)), ('Mace', (1, mace_obj)),
                              ('Rapier', (1, rapier_obj)), ('Staff', (1, staff_obj)))
        self.assertEqual(inventory_items, items_compare_with)
        self.assertEqual(self.inventory_obj.size(), 4)

    def test_total_weight_and_burden_for_strength_score(self):
        self.assertEqual(self.inventory_obj.total_weight, 13)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(4), inventory.Light)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(3), inventory.Medium)
        for item_name, (_, item_obj) in self.inventory_obj.items():
            self.inventory_obj.set(item_name, 4, item_obj)
        self.assertEqual(self.inventory_obj.total_weight, 52)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(6), inventory.Heavy)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(3), inventory.Immobilizing)


class test_item_and_items_index(unittest.TestCase):
    __slots__ = 'items_index_obj', 'items_ini_config_obj'

    items_ini_config_text = """
[Longsword]
title=longsword
description=A hefty sword with a long blade, a broad hilt and a leathern grip.
item_type=weapon
weight=3
value=15
damage=1d8
attack_bonus=0
warrior_can_use=true

[Rapier]
title=rapier
description=A slender, sharply pointed blade with a basket hilt.
item_type=weapon
weight=2
value=25
damage=1d8
attack_bonus=0
thief_can_use=true
warrior_can_use=true

[Mace]
title=mace
description=A hefty, blunt instrument with a dully-spiked weighted metal head.
item_type=weapon
weight=4
value=5
damage=1d6
attack_bonus=0
priest_can_use=true
warrior_can_use=true

[Staff]
title=staff
description=A balanced pole 6 feet in length with metal-shod ends.
item_type=weapon
weight=4
value=0.2
damage=1d6
attack_bonus=0
mage_can_use=true
warrior_can_use=true
"""

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(self.items_ini_config_text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.items_index_obj = items_index(self.items_ini_config_obj)

    def test_items_values(self):
        self.assertEqual(self.items_index_obj.get('Longsword').title, 'longsword')
        self.assertIsInstance(self.items_index_obj.get('Longsword'), weapon)
        self.assertEqual(self.items_index_obj.get('Longsword').description,
                         'A hefty sword with a long blade, a broad hilt and a leathern grip.')
        self.assertEqual(self.items_index_obj.get('Longsword').weight, 3)
        self.assertEqual(self.items_index_obj.get('Longsword').value, 15)
        self.assertEqual(self.items_index_obj.get('Longsword').damage.dice, '1d8')
        self.assertEqual(self.items_index_obj.get('Longsword').damage.modifier, '+0')
        self.assertEqual(self.items_index_obj.get('Longsword').attack_bonus, 0)
        self.assertEqual(self.items_index_obj.get('Longsword').warrior_can_use, True)

    def test_usable_by(self):
        self.assertTrue(self.items_index_obj.get('Longsword').usable_by('Warrior'))
        self.assertFalse(self.items_index_obj.get('Longsword').usable_by('Thief'))
        self.assertFalse(self.items_index_obj.get('Longsword').usable_by('Priest'))
        self.assertFalse(self.items_index_obj.get('Longsword').usable_by('Mage'))
        self.assertTrue(self.items_index_obj.get('Rapier').usable_by('Warrior'))
        self.assertTrue(self.items_index_obj.get('Rapier').usable_by('Thief'))
        self.assertFalse(self.items_index_obj.get('Rapier').usable_by('Priest'))
        self.assertFalse(self.items_index_obj.get('Rapier').usable_by('Mage'))
        self.assertTrue(self.items_index_obj.get('Mace').usable_by('Warrior'))
        self.assertFalse(self.items_index_obj.get('Mace').usable_by('Thief'))
        self.assertTrue(self.items_index_obj.get('Mace').usable_by('Priest'))
        self.assertFalse(self.items_index_obj.get('Mace').usable_by('Mage'))
        self.assertTrue(self.items_index_obj.get('Staff').usable_by('Warrior'))
        self.assertFalse(self.items_index_obj.get('Staff').usable_by('Thief'))
        self.assertFalse(self.items_index_obj.get('Staff').usable_by('Priest'))
        self.assertTrue(self.items_index_obj.get('Staff').usable_by('Mage'))

    def test_index_collection_interface(self):
        self.items_index_obj = items_index(self.items_ini_config_obj)
        longsword_obj = self.items_index_obj.get('Longsword')
        self.assertTrue(self.items_index_obj.contains(longsword_obj.internal_name))
        self.items_index_obj.delete('Longsword')
        with self.assertRaises(KeyError):
            self.items_index_obj.get('Longsword')
        with self.assertRaises(KeyError):
            self.items_index_obj.delete('Longsword')
        self.items_index_obj.set('Longsword', longsword_obj)
        self.assertTrue(self.items_index_obj.contains(longsword_obj.internal_name))
        self.assertEqual(set(self.items_index_obj.keys()), {'Longsword', 'Rapier', 'Mace', 'Staff'})
        rapier_obj = self.items_index_obj.get('Rapier')
        mace_obj = self.items_index_obj.get('Mace')
        staff_obj = self.items_index_obj.get('Staff')
        index_values = tuple(self.items_index_obj.values())
        self.assertTrue(all(item_obj in index_values for item_obj in (longsword_obj, rapier_obj, mace_obj, staff_obj)))
        index_items = tuple(sorted(self.items_index_obj.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Longsword', longsword_obj), ('Mace', mace_obj),
                              ('Rapier', rapier_obj), ('Staff', staff_obj))
        self.assertEqual(index_items, items_compare_with)
        self.assertEqual(self.items_index_obj.size(), 4)


class test_room_navigator(unittest.TestCase):
    __slots__ = 'rooms_ini_config_obj',

    rooms_ini_config_text = """
[Room_1,1]
title=Southwest dungeon room
description=Entrance room
north_exit=Room_2,1
east_exit=Room_1,2
is_entrance=true

[Room_1,2]
title=Southeast dungeon room
description=Nondescript room
north_exit=Room_2,2
west_exit=Room_1,1

[Room_2,1]
title=Northwest dungeon room
description=Nondescript room
south_exit=Room_1,1
east_exit=Room_2,2

[Room_2,2]
title=Northeast dungeon room
description=Exit room
west_exit=Room_2,1
south_exit=Room_1,2
is_exit=true
"""

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(self.rooms_ini_config_text)
        temp_ini_config_fh.close()
        self.rooms_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.room_navigator_obj = room_navigator(self.rooms_ini_config_obj)

    def test_room_navigator_init(self):
        self.room_navigator_obj = room_navigator(self.rooms_ini_config_obj)
        self.assertEqual(self.room_navigator_obj.cursor.internal_name, 'Room_1,1')
        self.assertTrue(self.room_navigator_obj.cursor.is_entrance)
        self.assertFalse(self.room_navigator_obj.cursor.is_exit)
        self.assertEqual(self.room_navigator_obj.cursor.title, 'Southwest dungeon room')
        self.assertEqual(self.room_navigator_obj.cursor.description, 'Entrance room')
        self.assertTrue(self.room_navigator_obj.cursor.has_north_exit)
        self.assertTrue(self.room_navigator_obj.cursor.has_east_exit)
        self.assertFalse(self.room_navigator_obj.cursor.has_south_exit)
        self.assertFalse(self.room_navigator_obj.cursor.has_west_exit)
        self.room_navigator_obj.move(north=True)

    def test_room_navigator_move_east(self):
        self.room_navigator_obj.move(east=True)
        self.assertEqual(self.room_navigator_obj.cursor.internal_name, 'Room_1,2')
        self.assertFalse(self.room_navigator_obj.cursor.is_entrance)
        self.assertFalse(self.room_navigator_obj.cursor.is_exit)
        self.assertEqual(self.room_navigator_obj.cursor.title, 'Southeast dungeon room')
        self.assertEqual(self.room_navigator_obj.cursor.description, 'Nondescript room')
        self.assertTrue(self.room_navigator_obj.cursor.has_north_exit)
        self.assertFalse(self.room_navigator_obj.cursor.has_east_exit)
        self.assertFalse(self.room_navigator_obj.cursor.has_south_exit)
        self.assertTrue(self.room_navigator_obj.cursor.has_west_exit)

    def test_room_navigator_move_north(self):
        self.room_navigator_obj.move(north=True)
        self.assertEqual(self.room_navigator_obj.cursor.internal_name, 'Room_2,1')
        self.assertFalse(self.room_navigator_obj.cursor.is_entrance)
        self.assertFalse(self.room_navigator_obj.cursor.is_exit)
        self.assertEqual(self.room_navigator_obj.cursor.title, 'Northwest dungeon room')
        self.assertEqual(self.room_navigator_obj.cursor.description, 'Nondescript room')
        self.assertFalse(self.room_navigator_obj.cursor.has_north_exit)
        self.assertTrue(self.room_navigator_obj.cursor.has_east_exit)
        self.assertTrue(self.room_navigator_obj.cursor.has_south_exit)
        self.assertFalse(self.room_navigator_obj.cursor.has_west_exit)

    def test_room_navigator_move_north_and_east(self):
        self.room_navigator_obj.move(north=True)
        self.room_navigator_obj.move(east=True)
        self.assertEqual(self.room_navigator_obj.cursor.internal_name, 'Room_2,2')
        self.assertTrue(self.room_navigator_obj.cursor.is_exit)
        self.assertFalse(self.room_navigator_obj.cursor.is_entrance)
        self.assertEqual(self.room_navigator_obj.cursor.title, 'Northeast dungeon room')
        self.assertEqual(self.room_navigator_obj.cursor.description, 'Exit room')
        self.assertFalse(self.room_navigator_obj.cursor.has_north_exit)
        self.assertFalse(self.room_navigator_obj.cursor.has_east_exit)
        self.assertTrue(self.room_navigator_obj.cursor.has_south_exit)
        self.assertTrue(self.room_navigator_obj.cursor.has_west_exit)

    def test_room_navigator_invalid_move(self):
        room_navigator_obj = room_navigator(self.rooms_ini_config_obj)
        with self.assertRaises(bad_command_exception):
            room_navigator_obj.move(south=True)

    def test_room_navigator_args_exception(self):
        with self.assertRaises(internal_exception):
            dungeon_room(foo='bar')


if __name__ == '__main__':
    unittest.main()
