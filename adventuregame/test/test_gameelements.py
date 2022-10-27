#!/usr/bin/python3

import math
import operator
import unittest

from adventuregame import *
from adventuregame.test.utility import *

__name__ = 'adventuregame.test_gameelements'


class test_container(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)

    def test_container(self):
        container_obj = self.containers_state_obj.get('Wooden_Chest_1')
        self.assertEqual(container_obj.internal_name, 'Wooden_Chest_1')
        self.assertEqual(container_obj.title, 'wooden chest')
        self.assertEqual(container_obj.description, 'This small, serviceable chest is made of wooden slat bounds within an iron framing, and features a sturdy-looking lock.')
        self.assertEqual(container_obj.is_locked, True)
        self.assertTrue(container_obj.contains('Gold_Coin'))
        self.assertTrue(container_obj.contains('Warhammer'))
        self.assertTrue(container_obj.contains('Mana_Potion'))
        potion_qty, mana_potion_obj = container_obj.get('Mana_Potion')
        self.assertIsInstance(mana_potion_obj, consumable)
        self.assertEqual(potion_qty, 1)
        container_obj.delete('Mana_Potion')
        self.assertFalse(container_obj.contains('Mana_Potion'))
        container_obj.set('Mana_Potion', potion_qty, mana_potion_obj)
        self.assertTrue(container_obj.contains('Mana_Potion'))


class test_character(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)

    def test_attack_and_damage_rolls_1(self):
        character_obj = character('Regdar', 'Warrior')
        self.assertEqual(character_obj.character_name, 'Regdar')
        self.assertEqual(character_obj.character_class, 'Warrior')
        longsword_obj = self.items_state_obj.get('Longsword')
        scale_mail_obj = self.items_state_obj.get('Scale_Mail')
        shield_obj = self.items_state_obj.get('Steel_Shield')
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
        strength_mod = character_obj.strength_mod
        strength_mod_str = '+' + str(strength_mod) if strength_mod > 0 else str(strength_mod) if strength_mod < 0 else ''
        self.assertEqual(character_obj.attack_roll, '1d20' + strength_mod_str)
        self.assertEqual(character_obj.damage_roll, '1d8' + strength_mod_str)
        self.assertEqual(character_obj.attack_bonus, character_obj.strength_mod)
        self.assertEqual(character_obj.armor_class, 10 + scale_mail_obj.armor_bonus + shield_obj.armor_bonus
                                                    + character_obj.dexterity_mod)
        self.assertEqual(character_obj.weapon, longsword_obj)
        self.assertEqual(character_obj.armor, scale_mail_obj)
        self.assertEqual(character_obj.shield, shield_obj)
        character_obj.unequip_weapon()
        character_obj.unequip_armor()
        character_obj.unequip_shield()
        self.assertFalse(character_obj.armor_equipped)
        self.assertFalse(character_obj.shield_equipped)
        self.assertFalse(character_obj.weapon_equipped)

    def test_attack_and_damage_rolls_2(self):
        character_obj = character('Mialee', 'Mage')
        wand_obj = self.items_state_obj.get('Magic_Wand')
        character_obj.pick_up_item(wand_obj)
        character_obj.equip_wand(wand_obj)
        self.assertFalse(character_obj.armor_equipped)
        self.assertFalse(character_obj.shield_equipped)
        self.assertFalse(character_obj.weapon_equipped)
        self.assertTrue(character_obj.wand_equipped)
        total_bonus = wand_obj.attack_bonus + character_obj.intelligence_mod
        total_bonus_str = '+' + str(total_bonus) if total_bonus > 0 else str(total_bonus) if total_bonus < 0 else ''
        self.assertEqual(character_obj.attack_roll, '1d20' + total_bonus_str)
        self.assertEqual(character_obj.damage_roll, '2d12' + total_bonus_str)
        self.assertEqual(character_obj.attack_bonus, int(wand_obj.attack_bonus)
                                                     + character_obj.intelligence_mod)
        self.assertEqual(character_obj.armor_class, 10 + character_obj.dexterity_mod)
        self.assertEqual(character_obj.wand, wand_obj)
        character_obj.unequip_wand()
        self.assertFalse(character_obj.wand_equipped)

    def test_pickup_vs_drop_vs_list(self):
        character_obj = character('Regdar', 'Warrior')
        longsword_obj = self.items_state_obj.get('Longsword')
        scale_mail_obj = self.items_state_obj.get('Scale_Mail')
        shield_obj = self.items_state_obj.get('Steel_Shield')
        character_obj.pick_up_item(longsword_obj)
        character_obj.pick_up_item(scale_mail_obj)
        character_obj.pick_up_item(shield_obj)
        self.assertEqual(character_obj.total_weight, longsword_obj.weight + scale_mail_obj.weight + shield_obj.weight)
                                                     # The items' total weight is 54.
        if character_obj.strength <= 5:
            self.assertEqual(character_obj.burden, inventory.Immobilized)
        elif character_obj.strength <= 8:
            self.assertEqual(character_obj.burden, inventory.Heavy)
        elif character_obj.strength <= 13:
            self.assertEqual(character_obj.burden, inventory.Medium)
        else:
            self.assertEqual(character_obj.burden, inventory.Light)
        testing_items_list = list(sorted((longsword_obj, scale_mail_obj, shield_obj),
                                          key=operator.attrgetter('title')))
        given_items_list = list(sorted(map(operator.itemgetter(1), character_obj.list_items()),
                                       key=operator.attrgetter('title')))
        self.assertEqual(testing_items_list, given_items_list)
        character_obj.drop_item(longsword_obj)
        character_obj.drop_item(scale_mail_obj)
        character_obj.drop_item(shield_obj)
        self.assertEqual(character_obj.total_weight, 0)
        self.assertFalse(character_obj.have_item(longsword_obj))
        character_obj.pick_up_item(longsword_obj, qty=5)
        self.assertTrue(character_obj.have_item(longsword_obj))
        self.assertEqual(character_obj.item_have_qty(longsword_obj), 5)
        character_obj.drop_item(longsword_obj, qty=3)
        self.assertEqual(character_obj.item_have_qty(longsword_obj), 2)
        character_obj.drop_item(longsword_obj, qty=2)
        self.assertEqual(character_obj.item_have_qty(longsword_obj), 0)
        self.assertFalse(character_obj.have_item(longsword_obj))

    def test_character_ability_scores(self):
        character_obj = character('Regdar', 'Warrior')
        self.assertEqual(math.floor((character_obj.strength - 10) / 2), character_obj.strength_mod)
        self.assertEqual(math.floor((character_obj.dexterity - 10) / 2), character_obj.dexterity_mod)
        self.assertEqual(math.floor((character_obj.constitution - 10) / 2), character_obj.constitution_mod)
        self.assertEqual(math.floor((character_obj.intelligence - 10) / 2), character_obj.intelligence_mod)
        self.assertEqual(math.floor((character_obj.wisdom - 10) / 2), character_obj.wisdom_mod)
        self.assertEqual(math.floor((character_obj.charisma - 10) / 2), character_obj.charisma_mod)

    def test_character_hitpoints_and_taking_damage_and_healing(self):
        character_obj = character('Regdar', 'Warrior')
        self.assertEqual(character_obj.hit_points, 40 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_point_total, 40 + 3 * character_obj.constitution_mod)
        character_obj.take_damage(10)
        self.assertEqual(character_obj.hit_points, 30 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_point_total, 40 + 3 * character_obj.constitution_mod)
        character_obj = character('Tordek', 'Priest')
        self.assertEqual(character_obj.hit_points, 30 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_point_total, 30 + 3 * character_obj.constitution_mod)
        character_obj = character('Lidda', 'Thief')
        self.assertEqual(character_obj.hit_points, 30 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_point_total, 30 + 3 * character_obj.constitution_mod)
        character_obj = character('Mialee', 'Mage')
        self.assertEqual(character_obj.hit_points, 20 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_point_total, 20 + 3 * character_obj.constitution_mod)
        self.assertTrue(character_obj.is_alive)
        self.assertFalse(character_obj.is_dead)
        character_obj.take_damage(20 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_points, 0)
        self.assertFalse(character_obj.is_alive)
        self.assertTrue(character_obj.is_dead)
        character_obj.heal_damage(20 + 3 * character_obj.constitution_mod)
        self.assertEqual(character_obj.hit_points, 20 + 3 * character_obj.constitution_mod)
        self.assertTrue(character_obj.is_alive)
        self.assertFalse(character_obj.is_dead)

    def test_character_init_ability_score_and_hp_overrides(self):
        character_obj = character('Regdar', 'Warrior', base_hit_points=50, strength=15, constitution=14, dexterity=13, intelligence=12, wisdom=8, charisma=10)
        self.assertEqual(character_obj.strength, 15)
        self.assertEqual(character_obj.constitution, 14)
        self.assertEqual(character_obj.dexterity, 13)
        self.assertEqual(character_obj.intelligence, 12)
        self.assertEqual(character_obj.wisdom, 8)
        self.assertEqual(character_obj.charisma, 10)
        self.assertEqual(character_obj.hit_points, 56)  # base_hit_points := 50 + 3 * floor((constitution - 10) / 2)

    def test_mana_points(self):
        character_obj = character('Hennet', 'Mage', base_hit_points=30, strength=12, constitution=13, dexterity=14, intelligence=15, wisdom=10, charisma=8)
        self.assertEqual(character_obj.mana_points, 23)
        self.assertEqual(character_obj.mana_point_total, 23)
        result = character_obj.attempt_to_spend_mana(10)
        self.assertTrue(result)
        self.assertEqual(character_obj.mana_points, 13)
        self.assertEqual(character_obj.mana_point_total, 23)
        result = character_obj.attempt_to_spend_mana(15)
        self.assertFalse(result)
        self.assertEqual(character_obj.mana_points, 13)


class test_creature(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)

    def test_creature_const_1(self):
        kobold_obj = self.creatures_state_obj.get('Kobold_Trysk')
        self.assertEqual(kobold_obj.character_class, 'Thief')
        self.assertEqual(kobold_obj.character_name, 'Trysk')
        self.assertEqual(kobold_obj.species, 'Kobold')
        self.assertEqual(kobold_obj.description, 'This diminuitive draconic humanoid is dressed in leather armor and has a short sword at its hip. It eyes you warily.')
        self.assertEqual(kobold_obj.character_class, 'Thief')
        self.assertEqual(kobold_obj.strength, 9)
        self.assertEqual(kobold_obj.dexterity, 13)
        self.assertEqual(kobold_obj.constitution, 10)
        self.assertEqual(kobold_obj.intelligence, 10)
        self.assertEqual(kobold_obj.wisdom, 9)
        self.assertEqual(kobold_obj.charisma, 8)
        self.assertEqual(kobold_obj.hit_points, 20)
        short_sword_obj = self.items_state_obj.get('Short_Sword')
        small_leather_armor_obj = self.items_state_obj.get('Small_Leather_Armor')
        self.assertEqual(kobold_obj.weapon_equipped, short_sword_obj)
        self.assertEqual(kobold_obj.armor_equipped, small_leather_armor_obj)

    def test_creature_const_2(self):
        sorcerer_obj = self.creatures_state_obj.get('Sorcerer_Ardren')
        self.assertEqual(sorcerer_obj.magic_key_stat, 'charisma')
        self.assertEqual(sorcerer_obj.mana_points, 36)

    def test_convert_to_corpse(self):
        kobold_obj = self.creatures_state_obj.get('Kobold_Trysk')
        kobold_corpse_obj = kobold_obj.convert_to_corpse()
        self.assertEqual(kobold_corpse_obj.description, kobold_obj.description_dead)
        self.assertEqual(kobold_corpse_obj.title, f'{kobold_obj.title} corpse')
        self.assertEqual(kobold_corpse_obj.internal_name, kobold_obj.internal_name)
        for item_internal_name, (item_qty, item_obj) in kobold_obj.inventory.items():
            self.assertEqual(kobold_corpse_obj.get(item_internal_name), (item_qty, item_obj))


class test_equipment(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)

    def test_equipment_1(self):
        equipment_obj = equipment('Warrior')
        self.assertFalse(equipment_obj.weapon_equipped)
        self.assertFalse(equipment_obj.armor_equipped)
        self.assertFalse(equipment_obj.shield_equipped)
        self.assertFalse(equipment_obj.wand_equipped)
        equipment_obj.equip_armor(self.items_state_obj.get('Scale_Mail'))
        equipment_obj.equip_shield(self.items_state_obj.get('Steel_Shield'))
        equipment_obj.equip_weapon(self.items_state_obj.get('Magic_Sword'))
        self.assertTrue(equipment_obj.armor_equipped)
        self.assertTrue(equipment_obj.shield_equipped)
        self.assertTrue(equipment_obj.weapon_equipped)
        with self.assertRaises(internal_exception):
            equipment_obj.equip_armor(self.items_state_obj.get('Steel_Shield'))
        self.assertEqual(equipment_obj.armor_class, 16)
        self.assertEqual(equipment_obj.attack_bonus, 3)
        self.assertEqual(equipment_obj.damage, '1d12+3')
        equipment_obj.unequip_armor()
        equipment_obj.unequip_shield()
        equipment_obj.unequip_weapon()
        self.assertFalse(equipment_obj.armor_equipped)
        self.assertFalse(equipment_obj.shield_equipped)
        self.assertFalse(equipment_obj.weapon_equipped)

    def test_equipment_2(self):
        equipment_obj = equipment('Mage')
        self.assertFalse(equipment_obj.wand_equipped)
        equipment_obj.equip_wand(self.items_state_obj.get('Magic_Wand'))
        self.assertTrue(equipment_obj.wand_equipped)
        equipment_obj.unequip_wand()
        self.assertFalse(equipment_obj.wand_equipped)

class test_ability_scores(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

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

        # This is a test of a method with a random element, so the results are nondeterministic. I'm looking for the
        # second call to `roll_stats()` to yield different stats, but there's a chance that the results are identical;
        # so I reroll until the results are different.
        while first_stat_roll == second_stat_roll:
            ability_scores_obj.roll_stats()
            second_stat_roll = (ability_scores_obj.strength, ability_scores_obj.constitution,
                                ability_scores_obj.dexterity, ability_scores_obj.intelligence,
                                ability_scores_obj.charisma, ability_scores_obj.wisdom)
        self.assertNotEqual(first_stat_roll, second_stat_roll)


class test_inventory(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)

    def setUp(self):
        self.inventory_obj = inventory(**self.items_ini_config_obj.sections)

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
        self.assertEqual(set(self.inventory_obj.keys()), {'Longsword', 'Rapier', 'Buckler', 'Mace', 'Staff',
                                                          'Warhammer', 'Door_Key', 'Chest_Key', 'Studded_Leather',
                                                          'Scale_Mail', 'Magic_Sword', 'Dagger', 'Gold_Coin',
                                                          'Small_Leather_Armor', 'Short_Sword', 'Steel_Shield', 'Mana_Potion',
                                                          'Health_Potion', 'Magic_Wand', 'Magic_Wand_2'})
        _, rapier_obj, = self.inventory_obj.get('Rapier')
        _, mace_obj, = self.inventory_obj.get('Mace')
        _, staff_obj = self.inventory_obj.get('Staff')
        _, warhammer_obj = self.inventory_obj.get('Warhammer')
        _, studded_leather_obj = self.inventory_obj.get('Studded_Leather')
        _, scale_mail_obj = self.inventory_obj.get('Scale_Mail')
        _, magic_sword_obj = self.inventory_obj.get('Magic_Sword')
        _, chest_key_obj = self.inventory_obj.get('Chest_Key')
        _, door_key_obj = self.inventory_obj.get('Door_Key')
        _, dagger_obj = self.inventory_obj.get('Dagger')
        _, gold_coin_obj = self.inventory_obj.get('Gold_Coin')
        _, small_leather_armor_obj = self.inventory_obj.get('Small_Leather_Armor')
        _, short_sword_obj = self.inventory_obj.get('Short_Sword')
        _, shield_obj = self.inventory_obj.get('Steel_Shield')
        _, mana_potion_obj = self.inventory_obj.get('Mana_Potion')
        _, health_potion_obj = self.inventory_obj.get('Health_Potion')
        _, magic_wand_obj = self.inventory_obj.get('Magic_Wand')
        _, magic_wand_2_obj = self.inventory_obj.get('Magic_Wand_2')
        _, buckler_obj = self.inventory_obj.get('Buckler')
        inventory_values = tuple(self.inventory_obj.values())
        self.assertTrue(all((1, item_obj) in inventory_values
                            for item_obj in (longsword_obj, rapier_obj, mace_obj, staff_obj)))
        inventory_items = tuple(sorted(self.inventory_obj.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Buckler', (1, buckler_obj)), ('Chest_Key', (1, chest_key_obj)),
                              ('Dagger', (1, dagger_obj)), ('Door_Key', (1, door_key_obj)),
                              ('Gold_Coin', (1, gold_coin_obj)), ('Health_Potion', (1, health_potion_obj)),
                              ('Longsword', (1, longsword_obj)), ('Mace', (1, mace_obj)),
                              ('Magic_Sword', (1, magic_sword_obj)), ('Magic_Wand', (1, magic_wand_obj)),
                              ('Magic_Wand_2', (1, magic_wand_2_obj)), ('Mana_Potion', (1, mana_potion_obj)),
                              ('Rapier', (1, rapier_obj)), ('Scale_Mail', (1, scale_mail_obj)),
                              ('Steel_Shield', (1, shield_obj)), ('Short_Sword', (1, short_sword_obj)),
                              ('Small_Leather_Armor', (1, small_leather_armor_obj)), ('Staff', (1, staff_obj)),
                              ('Studded_Leather', (1, studded_leather_obj)), ('Warhammer', (1, warhammer_obj)))
        self.assertEqual(inventory_items, items_compare_with)
        self.assertEqual(self.inventory_obj.size(), 20)

    def test_total_weight_and_burden_for_strength_score(self):
        for item_internal_name in ('Buckler', 'Dagger', 'Gold_Coin', 'Health_Potion', 'Magic_Sword', 'Magic_Wand',
                                   'Magic_Wand_2', 'Mana_Potion', 'Scale_Mail', 'Door_Key', 'Chest_Key', 'Steel_Shield',
                                   'Short_Sword', 'Small_Leather_Armor', 'Studded_Leather', 'Warhammer'):
            self.inventory_obj.remove_one(item_internal_name)
        self.assertEqual(self.inventory_obj.total_weight, 13)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(4), inventory.Light)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(3), inventory.Medium)
        for item_name, (_, item_obj) in self.inventory_obj.items():
            self.inventory_obj.set(item_name, 4, item_obj)
        self.assertEqual(self.inventory_obj.total_weight, 52)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(6), inventory.Heavy)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(3), inventory.Immobilizing)


class test_door_and_doors_state(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)

    def setUp(self):
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)

    def test_doors_state(self):
        doors_state_keys = self.doors_state_obj.keys()
        self.assertEqual(doors_state_keys, [('Room_1,1', 'Room_1,2'), ('Room_1,1', 'Room_2,1'), ('Room_1,2', 'Room_2,2'), ('Room_2,1', 'Room_2,2')])
        doors_state_values = self.doors_state_obj.values()
        self.assertTrue(all(isinstance(door_obj, door) and isinstance(door_obj, (wooden_door, iron_door, doorway)) for door_obj in doors_state_values))
        doors_state_items = self.doors_state_obj.items()
        self.assertEqual(list(map(operator.itemgetter(0, 1), doors_state_items)), [('Room_1,1', 'Room_1,2'), ('Room_1,1', 'Room_2,1'), ('Room_1,2', 'Room_2,2'), ('Room_2,1', 'Room_2,2')])
        self.assertTrue(all(isinstance(door_obj, door) and isinstance(door_obj, (wooden_door, iron_door, doorway)) for door_obj in doors_state_values))
        self.assertEqual(self.doors_state_obj.size(), 4)
        self.assertTrue(self.doors_state_obj.contains('Room_2,1', 'Room_2,2'))
        door_obj = self.doors_state_obj.get('Room_1,2', 'Room_2,2')
        self.assertEqual(door_obj.title, 'doorway')
        self.assertEqual(door_obj.description, 'This open doorway is outlined by a stone arch set into the wall.')
        self.assertEqual(door_obj.door_type, 'doorway')
        self.assertFalse(door_obj.is_locked, False)
        self.assertFalse(door_obj.is_closed, False)
        self.assertFalse(door_obj.closeable, False)
        self.doors_state_obj.delete('Room_1,2', 'Room_2,2')
        self.assertFalse(self.doors_state_obj.contains('Room_1,2', 'Room_2,2'))
        self.doors_state_obj.set('Room_1,2', 'Room_2,2', door_obj)
        self.assertTrue(self.doors_state_obj.contains('Room_1,2', 'Room_2,2'))

    def test_doors_state_and_door(self):
        door_obj = self.doors_state_obj.get('Room_1,1', 'Room_1,2')
        self.assertEqual(door_obj.title, 'wooden door')
        self.assertEqual(door_obj.description, 'This door is made of wooden planks secured together with iron divots.')
        self.assertEqual(door_obj.door_type, 'wooden_door')
        self.assertEqual(door_obj.is_locked, False)
        self.assertEqual(door_obj.is_closed, True)
        self.assertEqual(door_obj.closeable, True)

        door_obj = self.doors_state_obj.get('Room_1,1', 'Room_2,1')
        self.assertEqual(door_obj.title, 'iron door')
        self.assertEqual(door_obj.description, 'This door is bound in iron plates with a small barred window set up high.')
        self.assertEqual(door_obj.door_type, 'iron_door')
        self.assertEqual(door_obj.is_locked, True)
        self.assertEqual(door_obj.is_closed, True)
        self.assertEqual(door_obj.closeable, True)

        door_obj = self.doors_state_obj.get('Room_1,2', 'Room_2,2')
        self.assertEqual(door_obj.title, 'doorway')
        self.assertEqual(door_obj.description, 'This open doorway is outlined by a stone arch set into the wall.')
        self.assertEqual(door_obj.door_type, 'doorway')
        self.assertEqual(door_obj.is_locked, False)
        self.assertEqual(door_obj.is_closed, False)
        self.assertEqual(door_obj.closeable, False)


class test_item_and_items_state(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)

    def test_items_values(self):
        self.assertEqual(self.items_state_obj.get('Longsword').title, 'longsword')
        self.assertIsInstance(self.items_state_obj.get('Longsword'), weapon)
        self.assertEqual(self.items_state_obj.get('Longsword').description,
                         'A hefty sword with a long blade, a broad hilt and a leathern grip.')
        self.assertEqual(self.items_state_obj.get('Longsword').weight, 3)
        self.assertEqual(self.items_state_obj.get('Longsword').value, 15)
        self.assertEqual(self.items_state_obj.get('Longsword').damage, '1d8')
        self.assertEqual(self.items_state_obj.get('Longsword').attack_bonus, 0)
        self.assertEqual(self.items_state_obj.get('Longsword').warrior_can_use, True)

    def test_usable_by(self):
        self.assertTrue(self.items_state_obj.get('Longsword').usable_by('Warrior'))
        self.assertFalse(self.items_state_obj.get('Longsword').usable_by('Thief'))
        self.assertFalse(self.items_state_obj.get('Longsword').usable_by('Priest'))
        self.assertFalse(self.items_state_obj.get('Longsword').usable_by('Mage'))
        self.assertTrue(self.items_state_obj.get('Rapier').usable_by('Warrior'))
        self.assertTrue(self.items_state_obj.get('Rapier').usable_by('Thief'))
        self.assertFalse(self.items_state_obj.get('Rapier').usable_by('Priest'))
        self.assertFalse(self.items_state_obj.get('Rapier').usable_by('Mage'))
        self.assertTrue(self.items_state_obj.get('Mace').usable_by('Warrior'))
        self.assertFalse(self.items_state_obj.get('Mace').usable_by('Thief'))
        self.assertTrue(self.items_state_obj.get('Mace').usable_by('Priest'))
        self.assertFalse(self.items_state_obj.get('Mace').usable_by('Mage'))
        self.assertTrue(self.items_state_obj.get('Staff').usable_by('Warrior'))
        self.assertFalse(self.items_state_obj.get('Staff').usable_by('Thief'))
        self.assertFalse(self.items_state_obj.get('Staff').usable_by('Priest'))
        self.assertTrue(self.items_state_obj.get('Staff').usable_by('Mage'))

    def test_state_collection_interface(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        longsword_obj = self.items_state_obj.get('Longsword')
        self.assertTrue(self.items_state_obj.contains(longsword_obj.internal_name))
        self.items_state_obj.delete('Longsword')
        with self.assertRaises(KeyError):
            self.items_state_obj.get('Longsword')
        with self.assertRaises(KeyError):
            self.items_state_obj.delete('Longsword')
        self.items_state_obj.set('Longsword', longsword_obj)
        self.assertTrue(self.items_state_obj.contains(longsword_obj.internal_name))
        self.assertEqual(set(self.items_state_obj.keys()), {'Buckler', 'Longsword', 'Rapier', 'Mace', 'Staff',
                                                            'Warhammer', 'Studded_Leather', 'Door_Key', 'Chest_Key',
                                                            'Scale_Mail', 'Magic_Sword', 'Dagger', 'Gold_Coin',
                                                            'Small_Leather_Armor', 'Short_Sword', 'Steel_Shield',
                                                            'Mana_Potion', 'Magic_Wand', 'Magic_Wand_2',
                                                            'Health_Potion'})
        rapier_obj = self.items_state_obj.get('Rapier')
        mace_obj = self.items_state_obj.get('Mace')
        staff_obj = self.items_state_obj.get('Staff')
        warhammer_obj = self.items_state_obj.get('Warhammer')
        studded_leather_obj = self.items_state_obj.get('Studded_Leather')
        scale_mail_obj = self.items_state_obj.get('Scale_Mail')
        door_key_obj = self.items_state_obj.get('Door_Key')
        chest_key_obj = self.items_state_obj.get('Chest_Key')
        magic_sword_obj = self.items_state_obj.get('Magic_Sword')
        dagger_obj = self.items_state_obj.get('Dagger')
        gold_coin_obj = self.items_state_obj.get('Gold_Coin')
        small_leather_armor_obj = self.items_state_obj.get('Small_Leather_Armor')
        short_sword_obj = self.items_state_obj.get('Short_Sword')
        shield_obj = self.items_state_obj.get('Steel_Shield')
        mana_potion_obj = self.items_state_obj.get('Mana_Potion')
        health_potion_obj = self.items_state_obj.get('Health_Potion')
        magic_wand_obj = self.items_state_obj.get('Magic_Wand')
        magic_wand_2_obj = self.items_state_obj.get('Magic_Wand_2')
        buckler_obj = self.items_state_obj.get('Buckler')
        state_values = tuple(self.items_state_obj.values())
        self.assertTrue(all(item_obj in state_values for item_obj in (longsword_obj, rapier_obj, mace_obj, staff_obj)))
        state_items = tuple(sorted(self.items_state_obj.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Buckler', buckler_obj), ('Chest_Key', chest_key_obj), ('Dagger', dagger_obj),
                              ('Door_Key', door_key_obj), ('Gold_Coin', gold_coin_obj),
                              ('Health_Potion', health_potion_obj), ('Longsword', longsword_obj), ('Mace', mace_obj),
                              ('Magic_Sword', magic_sword_obj), ('Magic_Wand', magic_wand_obj),
                              ('Magic_Wand_2', magic_wand_2_obj), ('Mana_Potion', mana_potion_obj), ('Rapier', rapier_obj),
                              ('Scale_Mail', scale_mail_obj), ('Short_Sword', short_sword_obj),
                              ('Small_Leather_Armor', small_leather_armor_obj), ('Staff', staff_obj),
                              ('Steel_Shield', shield_obj), ('Studded_Leather', studded_leather_obj),
                              ('Warhammer', warhammer_obj))
        self.assertEqual(state_items, items_compare_with)
        self.assertEqual(self.items_state_obj.size(), 20)


class test_rooms_state_obj(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj, self.items_state_obj, **self.rooms_ini_config_obj.sections)

    def test_rooms_state_init(self):
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_1,1')
        self.assertTrue(self.rooms_state_obj.cursor.is_entrance)
        self.assertFalse(self.rooms_state_obj.cursor.is_exit)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Southwest dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Entrance room')
        self.assertTrue(self.rooms_state_obj.cursor.has_north_exit)
        self.assertEqual(self.rooms_state_obj.cursor.north_exit.title, 'north door')
        self.assertEqual(self.rooms_state_obj.cursor.north_exit.description, 'This door is made of wooden planks secured together with iron divots.')
        self.assertEqual(self.rooms_state_obj.cursor.north_exit.door_type, 'wooden_door')
        self.assertEqual(self.rooms_state_obj.cursor.north_exit.is_locked, False)
        self.assertEqual(self.rooms_state_obj.cursor.north_exit.is_closed, True)
        self.assertEqual(self.rooms_state_obj.cursor.north_exit.closeable, True)
        self.assertTrue(self.rooms_state_obj.cursor.has_east_exit)
        self.assertTrue(self.rooms_state_obj.cursor.east_exit.title, 'east door')
        self.assertTrue(self.rooms_state_obj.cursor.east_exit.description, 'This door is bound in iron plates with a small barred window set up high.')
        self.assertTrue(self.rooms_state_obj.cursor.east_exit.door_type, 'iron_door')
        self.assertTrue(self.rooms_state_obj.cursor.east_exit.is_locked, True)
        self.assertTrue(self.rooms_state_obj.cursor.east_exit.is_closed, True)
        self.assertTrue(self.rooms_state_obj.cursor.east_exit.closeable, True)
        self.assertFalse(self.rooms_state_obj.cursor.has_south_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_west_exit)
        self.rooms_state_obj.move(north=True)

    def test_rooms_state_move_east(self):
        self.rooms_state_obj.cursor.east_exit.is_locked = False
        self.rooms_state_obj.move(east=True)
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_2,1')
        self.assertFalse(self.rooms_state_obj.cursor.is_entrance)
        self.assertFalse(self.rooms_state_obj.cursor.is_exit)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Southeast dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Nondescript room')
        self.assertTrue(self.rooms_state_obj.cursor.has_north_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_east_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_south_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_west_exit)

    def test_rooms_state_move_north(self):
        self.rooms_state_obj.move(north=True)
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_1,2')
        self.assertFalse(self.rooms_state_obj.cursor.is_entrance)
        self.assertFalse(self.rooms_state_obj.cursor.is_exit)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Northwest dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Nondescript room')
        self.assertFalse(self.rooms_state_obj.cursor.has_north_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_east_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_south_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_west_exit)

    def test_rooms_state_move_north_and_east(self):
        self.rooms_state_obj.cursor.east_exit.is_locked = False
        self.rooms_state_obj.move(north=True)
        self.rooms_state_obj.move(east=True)
        self.assertTrue(self.rooms_state_obj.cursor.west_exit.title, 'west doorway')
        self.assertTrue(self.rooms_state_obj.cursor.west_exit.description, 'This door is bound in iron plates with a small barred window set up high.')
        self.assertTrue(self.rooms_state_obj.cursor.west_exit.door_type, 'doorway')
        self.assertTrue(self.rooms_state_obj.cursor.west_exit.is_locked, False)
        self.assertTrue(self.rooms_state_obj.cursor.west_exit.is_closed, False)
        self.assertTrue(self.rooms_state_obj.cursor.west_exit.closeable, False)
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_2,2')
        self.assertTrue(self.rooms_state_obj.cursor.is_exit)
        self.assertFalse(self.rooms_state_obj.cursor.is_entrance)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Northeast dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Exit room')
        self.assertFalse(self.rooms_state_obj.cursor.has_north_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_east_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_south_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_west_exit)

    def test_rooms_state_invalid_move(self):
        with self.assertRaises(bad_command_exception):
            self.rooms_state_obj.move(south=True)

    def test_rooms_state_room_items_container_creature_here(self):
        kobold_obj = self.creatures_state_obj.get('Kobold_Trysk')
        wooden_chest_obj = self.containers_state_obj.get('Wooden_Chest_1')
        mana_potion_obj = self.items_state_obj.get('Mana_Potion')
        health_potion_obj = self.items_state_obj.get('Health_Potion')
        room_obj = self.rooms_state_obj.cursor
        self.assertEqual(room_obj.creature_here, kobold_obj)
        self.assertEqual(room_obj.container_here, wooden_chest_obj)
        self.assertEqual(room_obj.items_here.get('Mana_Potion'), (1, mana_potion_obj))
        self.assertEqual(room_obj.items_here.get('Health_Potion'), (2, health_potion_obj))

    def test_rooms_state_and_door_obj(self):
        self.assertIsInstance(self.rooms_state_obj.cursor.north_exit, door)
        self.assertEqual(self.rooms_state_obj.cursor.north_exit.internal_name, 'Room_1,1_x_Room_1,2')
        self.assertEqual(self.rooms_state_obj.cursor.east_exit.internal_name, 'Room_1,1_x_Room_2,1')


class test_game_state(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj, self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj, self.items_state_obj)

    def test_game_state(self):
        self.assertFalse(self.game_state_obj.game_has_begun)
        self.assertFalse(self.game_state_obj.game_has_ended)
        self.assertIs(self.game_state_obj.character_name, None)
        self.assertIs(self.game_state_obj.character_class, None)
        self.assertIs(getattr(self.game_state_obj, 'character_obj', None), None)
        self.game_state_obj.character_name = 'Kaeva'
        self.game_state_obj.character_class = 'Priest'
        self.assertEqual(self.game_state_obj.character_name, 'Kaeva')
        self.assertEqual(self.game_state_obj.character_class, 'Priest')
        self.assertIsNot(getattr(self.game_state_obj, 'character', None), None)
