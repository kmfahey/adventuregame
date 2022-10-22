#!/usr/bin/python3

import math
import operator
import os
import tempfile
import unittest
import tokenize

import iniconfig

from adventure_game import *


# Creatures_Ini_Config_Text
# Chests_Ini_Config_Text
# Rooms_Ini_Config_Text
# Items_Ini_Config_Text

Items_Ini_Config_Text = """
[Short_Sword]
attack_bonus=0
damage=1d8
description=A smaller sword with a short blade and a narrower grip.
item_type=weapon
thief_can_use=true
title=short sword
value=10
warrior_can_use=true
weight=2

[Rapier]
attack_bonus=0
damage=1d8
description=A slender, sharply pointed blade with a basket hilt.
item_type=weapon
thief_can_use=true
title=rapier
value=25
warrior_can_use=true
weight=2

[Mace]
attack_bonus=0
damage=1d6
description=A hefty, blunt instrument with a dully-spiked weighted metal head.
item_type=weapon
priest_can_use=true
title=mace
value=5
warrior_can_use=true
weight=4

[Small_Leather_Armor]
armor_bonus=2
description=A suit of leather armor designed for a humanoid of 4 feet in height.
item_type=armor
title=small leather armor
value=10
weight=7.5

[Longsword]
attack_bonus=0
damage=1d8
description=A hefty sword with a long blade, a broad hilt and a leathern grip.
item_type=weapon
title=longsword
value=15
warrior_can_use=true
weight=3

[Staff]
attack_bonus=0
damage=1d6
description=A balanced pole 6 feet in length with metal-shod ends.
item_type=weapon
mage_can_use=true
title=staff
value=0.2
warrior_can_use=true
weight=4

[Dagger]
attack_bonus=0
damage=1d4
description=A simple bladed weapon with a plain iron hilt and a notched edge.
mage_can_use=true
priest_can_use=true
thief_can_use=true
title=dagger
item_type=weapon
value=2
warrior_can_use=true
weight=1

[Warhammer]
attack_bonus=0
damage=1d8
description=A heavy hammer with a heavy iron head with a tapered striking point and a long leather-wrapped hast.
item_type=weapon
priest_can_use==true
title=warhammer
warrior_can_use=true
weight=5

[Studded_Leather]
armor_bonus=2
description=A suit of fire-hardened leather plates and padding that provides some protection from attack.
item_type=armor
thief_can_use=true
title=studded leather armor
value=45
warrior_can_use=true
weight=15

[Shield]
armor_bonus=2
description=A broad panel of leather-bound wood with a metal rim that is useful for sheltering behind.
item_type=shield
priest_can_use=true
title=shield
value=10
warrior_can_use=true
weight=6

[Scale_Mail]
armor_bonus=4
description=A suit of small steel scales linked together in a flexible plating that provides strong protection from attack.
item_type=armor
priest_can_use=true
title=scale mail armor
value=50
warrior_can_use=true
weight=45

[Magic_Sword]
attack_bonus=3
damage=1d12+3
description=A magic sword with a palpable magic aura and an unnaturally sharp blade.
item_type=weapon
title=magic sword
value=15
warrior_can_use=true
weight=3

[Magic_Wand]
attack_bonus=3
damage=2d12+3
description=A palpably magical tapered length of polished ash wood tipped with a glowing red carnelian gem.
item_type=wand
mage_can_use=true
title=magic wand
value=100
weight=0.5

[Mana_Potion]
description=A small, stoppered bottle that contains a pungeant but drinkable blue liquid with a discernable magic aura.
item_type=consumable
mage_can_use=true
priest_can_use=true
title=health potion
value=25
weight=.1

[Health_Potion]
description=A small, stoppered bottle that contains a pungeant but drinkable red liquid with a discernable magic aura.
item_type=consumable
mage_can_use=true
priest_can_use=true
thief_can_use=true
title=health potion
value=25
warrior_can_use=true
weight=.1

[Gold_Piece]
description=A small shiny gold coin imprinted with an indistinct bust on one side and a worn state seal on the other.
item_type=coin
title=gold piece
value=1
weight=0.02
"""

Rooms_Ini_Config_Text = """
[Room_1,1]
description=Entrance room
east_exit=Room_1,2
is_entrance=true
north_exit=Room_2,1
title=Southwest dungeon room

[Room_1,2]
description=Nondescript room
north_exit=Room_2,2
title=Southeast dungeon room
west_exit=Room_1,1

[Room_2,1]
description=Nondescript room
east_exit=Room_2,2
south_exit=Room_1,1
title=Northwest dungeon room

[Room_2,2]
description=Exit room
is_exit=true
south_exit=Room_1,2
title=Northeast dungeon room
west_exit=Room_2,1
occupant=Kobold_Trysk
"""

Chests_Ini_Config_Text = """
[Wooden_Chest_1]
contents=[20xGold_Piece,1xWarhammer,1xMana_Potion]
description=This small, serviceable chest is made of wooden slat bounds within an iron framing, and features a sturdy-looking lock.
is_locked=true
title=wooden chest
"""

Creatures_Ini_Config_Text = """
[Kobold_Trysk]
# This creature was adapted from the Dungeons & Dragons 3rd edition _Monster Manual_, p.123.
armor_equipped=Small_Leather_Armor
base_hit_points=20
character_class=Thief
character_name=Trysk
charisma=8
constitution=10
description=This diminuitive draconic humanoid is dressed in leather armor and has a short sword at its hip. It eyes you warily.
dexterity=13
intelligence=10
inventory_items=[1xShort_Sword,1xSmall_Leather_Armor,30xGold_Piece,1xHealth_Potion]
species=Kobold
strength=9
weapon_equipped=Short_Sword
wisdom=9

[Sorcerer_Ardren]
# This creature was adapted from the Dungeons & Dragons 3rd edition _Enemies & Allies_, p.55
base_hit_points=30
base_mana_points=20
character_class=Thief
character_name=Ardren
charisma=18
constitution=15
description=Stripped to the waist and inscribed with dragon chest tattoos, this half-elf is clearly a sorcerer.
dexterity=16
intelligence=10
inventory_items=[2xMana_Potion,1xDagger,10xGold_Piece]
magic_key_stat=charisma
species=human
strength=8
weapon_equipped=Dagger
wisdom=12
"""


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


class test_game_state_manager(unittest.TestCase):
    pass


class test_chest(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Chests_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.chests_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Items_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.chests_state_obj = chests_state(self.items_state_obj, **self.chests_ini_config_obj.sections)

    def test_chest(self):
        chest_obj = self.chests_state_obj.get("Wooden_Chest_1")
        self.assertEqual(chest_obj.internal_name, "Wooden_Chest_1")
        self.assertEqual(chest_obj.title, "wooden chest")
        self.assertEqual(chest_obj.description, "This small, serviceable chest is made of wooden slat bounds within an iron framing, and features a sturdy-looking lock.")
        self.assertEqual(chest_obj.is_locked, True)
        self.assertTrue(chest_obj.contains("Gold_Piece"))
        self.assertTrue(chest_obj.contains("Warhammer"))
        self.assertTrue(chest_obj.contains("Mana_Potion"))
        potion_qty, mana_potion_obj = chest_obj.get("Mana_Potion")
        self.assertIsInstance(mana_potion_obj, consumable)
        self.assertEqual(potion_qty, 1)
        chest_obj.delete("Mana_Potion")
        self.assertFalse(chest_obj.contains("Mana_Potion"))
        chest_obj.set("Mana_Potion", potion_qty, mana_potion_obj)
        self.assertTrue(chest_obj.contains("Mana_Potion"))


class test_character(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Items_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)

    def test_attack_and_damage_rolls_1(self):
        character_obj = character('Regdar', 'Warrior')
        self.assertEqual(character_obj.character_name, 'Regdar')
        self.assertEqual(character_obj.character_class, 'Warrior')
        longsword_obj = self.items_state_obj.get('Longsword')
        scale_mail_obj = self.items_state_obj.get('Scale_Mail')
        shield_obj = self.items_state_obj.get('Shield')
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
        strength_mod_str = "+" + str(strength_mod) if strength_mod > 0 else str(strength_mod) if strength_mod < 0 else ""
        self.assertEqual(character_obj.attack_roll, '1d20' + strength_mod_str)
        self.assertEqual(character_obj.damage_roll, '1d8' + strength_mod_str)
        self.assertEqual(character_obj.attack_bonus, character_obj.strength_mod)
        self.assertEqual(character_obj.armor_class, 10 + scale_mail_obj.armor_bonus + shield_obj.armor_bonus
                                                    + character_obj.dexterity_mod)
        self.assertEqual(character_obj.weapon, longsword_obj)
        self.assertEqual(character_obj.armor, scale_mail_obj)
        self.assertEqual(character_obj.shield, shield_obj)

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
        total_bonus_str = "+" + str(total_bonus) if total_bonus > 0 else str(total_bonus) if total_bonus < 0 else ""
        self.assertEqual(character_obj.attack_roll, '1d20' + total_bonus_str)
        self.assertEqual(character_obj.damage_roll, '2d12' + total_bonus_str)
        self.assertEqual(character_obj.attack_bonus, int(wand_obj.attack_bonus)
                                                     + character_obj.intelligence_mod)
        self.assertEqual(character_obj.armor_class, 10 + character_obj.dexterity_mod)
        self.assertEqual(character_obj.wand, wand_obj)

    def test_pickup_vs_drop_vs_list(self):
        character_obj = character('Regdar', 'Warrior')
        longsword_obj = self.items_state_obj.get('Longsword')
        scale_mail_obj = self.items_state_obj.get('Scale_Mail')
        shield_obj = self.items_state_obj.get('Shield')
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
        testing_items_list = list(sorted((longsword_obj, scale_mail_obj, shield_obj),
                                          key=operator.attrgetter('title')))
        given_items_list = list(sorted(map(operator.itemgetter(1), character_obj.list_items()),
                                       key=operator.attrgetter('title')))
        self.assertEqual(testing_items_list, given_items_list)
        character_obj.drop_item(longsword_obj)
        character_obj.drop_item(scale_mail_obj)
        character_obj.drop_item(shield_obj)
        self.assertEqual(character_obj.total_weight, 0)

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
        character_obj = character('Tordek', 'Priest')
        self.assertEqual(character_obj.hit_points, 30 + 3 * character_obj.constitution_mod)
        character_obj = character('Lidda', 'Thief')
        self.assertEqual(character_obj.hit_points, 30 + 3 * character_obj.constitution_mod)
        character_obj = character('Mialee', 'Mage')
        self.assertEqual(character_obj.hit_points, 20 + 3 * character_obj.constitution_mod)
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
        result = character_obj.attempt_to_spend_mana(10)
        self.assertTrue(result)
        self.assertEqual(character_obj.mana_points, 13)
        result = character_obj.attempt_to_spend_mana(15)
        self.assertFalse(result)
        self.assertEqual(character_obj.mana_points, 13)


class test_creature(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Items_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Creatures_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.creatures_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
    
    def test_creature_const(self):
        kobold_obj = self.creatures_state_obj.get("Kobold_Trysk")
        self.assertEqual(kobold_obj.character_class, "Thief")
        self.assertEqual(kobold_obj.character_name, "Trysk")
        self.assertEqual(kobold_obj.species, "Kobold")
        self.assertEqual(kobold_obj.description, "This diminuitive draconic humanoid is dressed in leather armor and has a short sword at its hip. It eyes you warily.")
        self.assertEqual(kobold_obj.character_class, "Thief")
        self.assertEqual(kobold_obj.strength, 9)
        self.assertEqual(kobold_obj.dexterity, 13)
        self.assertEqual(kobold_obj.constitution, 10)
        self.assertEqual(kobold_obj.intelligence, 10)
        self.assertEqual(kobold_obj.wisdom, 9)
        self.assertEqual(kobold_obj.charisma, 8)
        self.assertEqual(kobold_obj.hit_points, 20)
        short_sword_obj = self.items_state_obj.get("Short_Sword")
        small_leather_armor_obj = self.items_state_obj.get("Small_Leather_Armor")
        gold_piece_obj = self.items_state_obj.get("Gold_Piece")
        health_potion_obj = self.items_state_obj.get("Health_Potion")
        testing_items_list = list(sorted((short_sword_obj, small_leather_armor_obj, gold_piece_obj, health_potion_obj),
                                         key=operator.attrgetter('title')))
        given_items_list = list(sorted(map(operator.itemgetter(1), kobold_obj.list_items()),
                                       key=operator.attrgetter('title')))
        self.assertEqual(kobold_obj.weapon_equipped, short_sword_obj)
        self.assertEqual(kobold_obj.armor_equipped, small_leather_armor_obj)

    def test_creature_const(self):
        sorcerer_obj = self.creatures_state_obj.get("Sorcerer_Ardren")
        self.assertEqual(sorcerer_obj.magic_key_stat, "charisma")
        self.assertEqual(sorcerer_obj.mana_points, 36)




class test_equipment(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Items_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)

    def test_equipment(self):
        equipment_obj = equipment('Warrior')
        self.assertFalse(equipment_obj.weapon_equipped)
        self.assertFalse(equipment_obj.armor_equipped)
        self.assertFalse(equipment_obj.shield_equipped)
        self.assertFalse(equipment_obj.wand_equipped)
        equipment_obj.equip_weapon(self.items_state_obj.get('Magic_Sword'))
        self.assertTrue(equipment_obj.weapon_equipped)
        equipment_obj.equip_armor(self.items_state_obj.get('Scale_Mail'))
        self.assertTrue(equipment_obj.armor_equipped)
        equipment_obj.equip_shield(self.items_state_obj.get('Shield'))
        self.assertTrue(equipment_obj.shield_equipped)
        with self.assertRaises(internal_exception):
            equipment_obj.equip_armor(self.items_state_obj.get('Shield'))
        self.assertEqual(equipment_obj.armor_class, 16)
        self.assertEqual(equipment_obj.attack_bonus, 3)
        self.assertEqual(equipment_obj.damage, '1d12+3')


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

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Items_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

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
        self.assertEqual(set(self.inventory_obj.keys()), {'Longsword', 'Rapier', 'Mace', 'Staff', 'Warhammer',
                                                          'Studded_Leather', 'Scale_Mail', 'Magic_Sword', 'Dagger',
                                                          'Gold_Piece', 'Small_Leather_Armor', 'Short_Sword', 'Shield',
                                                          'Mana_Potion', 'Health_Potion', 'Magic_Wand'})
        _, rapier_obj, = self.inventory_obj.get('Rapier')
        _, mace_obj, = self.inventory_obj.get('Mace')
        _, staff_obj = self.inventory_obj.get('Staff')
        _, warhammer_obj = self.inventory_obj.get('Warhammer')
        _, studded_leather_obj = self.inventory_obj.get('Studded_Leather')
        _, scale_mail_obj = self.inventory_obj.get('Scale_Mail')
        _, magic_sword_obj = self.inventory_obj.get('Magic_Sword')
        _, dagger_obj = self.inventory_obj.get('Dagger')
        _, gold_piece_obj = self.inventory_obj.get('Gold_Piece')
        _, small_leather_armor_obj = self.inventory_obj.get('Small_Leather_Armor')
        _, short_sword_obj = self.inventory_obj.get('Short_Sword')
        _, shield_obj = self.inventory_obj.get('Shield')
        _, mana_potion_obj = self.inventory_obj.get('Mana_Potion')
        _, health_potion_obj = self.inventory_obj.get('Health_Potion')
        _, magic_wand_obj = self.inventory_obj.get('Magic_Wand')
        inventory_values = tuple(self.inventory_obj.values())
        self.assertTrue(all((1, item_obj) in inventory_values
                            for item_obj in (longsword_obj, rapier_obj, mace_obj, staff_obj)))
        inventory_items = tuple(sorted(self.inventory_obj.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Dagger', (1, dagger_obj)), ('Gold_Piece', (1, gold_piece_obj)),
                              ('Health_Potion', (1, health_potion_obj)), ('Longsword', (1, longsword_obj)),
                              ('Mace', (1, mace_obj)), ('Magic_Sword', (1, magic_sword_obj)),
                              ('Magic_Wand', (1, magic_wand_obj)), ('Mana_Potion', (1, mana_potion_obj)),
                              ('Rapier', (1, rapier_obj)), ('Scale_Mail', (1, scale_mail_obj)),
                              ('Shield', (1, shield_obj)), ('Short_Sword', (1, short_sword_obj)),
                              ('Small_Leather_Armor', (1, small_leather_armor_obj)), ('Staff', (1, staff_obj)),
                              ('Studded_Leather', (1, studded_leather_obj)), ('Warhammer', (1, warhammer_obj)))
        self.assertEqual(inventory_items, items_compare_with)
        self.assertEqual(self.inventory_obj.size(), 16)

    def test_total_weight_and_burden_for_strength_score(self):
        for item_internal_name in ('Dagger', 'Gold_Piece', 'Health_Potion', 'Magic_Sword', 'Magic_Wand', 'Mana_Potion',
                                   'Scale_Mail', 'Shield', 'Short_Sword', 'Small_Leather_Armor', 'Studded_Leather',
                                   'Warhammer'):
            self.inventory_obj.remove_one(item_internal_name)
        self.assertEqual(self.inventory_obj.total_weight, 13)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(4), inventory.Light)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(3), inventory.Medium)
        for item_name, (_, item_obj) in self.inventory_obj.items():
            self.inventory_obj.set(item_name, 4, item_obj)
        self.assertEqual(self.inventory_obj.total_weight, 52)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(6), inventory.Heavy)
        self.assertEqual(self.inventory_obj.burden_for_strength_score(3), inventory.Immobilizing)


class test_item_and_items_state(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Items_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)

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
        self.assertEqual(set(self.items_state_obj.keys()), {'Longsword', 'Rapier', 'Mace', 'Staff', 'Warhammer',
                                                            'Studded_Leather', 'Scale_Mail', 'Magic_Sword', 'Dagger',
                                                            'Gold_Piece', 'Small_Leather_Armor', 'Short_Sword',
                                                            'Shield', 'Mana_Potion', 'Magic_Wand', 'Health_Potion'})
        rapier_obj = self.items_state_obj.get('Rapier')
        mace_obj = self.items_state_obj.get('Mace')
        staff_obj = self.items_state_obj.get('Staff')
        warhammer_obj = self.items_state_obj.get('Warhammer')
        studded_leather_obj = self.items_state_obj.get('Studded_Leather')
        scale_mail_obj = self.items_state_obj.get('Scale_Mail')
        magic_sword_obj = self.items_state_obj.get('Magic_Sword')
        dagger_obj = self.items_state_obj.get('Dagger')
        gold_piece_obj = self.items_state_obj.get('Gold_Piece')
        small_leather_armor_obj = self.items_state_obj.get('Small_Leather_Armor')
        short_sword_obj = self.items_state_obj.get('Short_Sword')
        shield_obj = self.items_state_obj.get('Shield')
        mana_potion_obj = self.items_state_obj.get('Mana_Potion')
        health_potion_obj = self.items_state_obj.get('Health_Potion')
        magic_wand_obj = self.items_state_obj.get('Magic_Wand')
        state_values = tuple(self.items_state_obj.values())
        self.assertTrue(all(item_obj in state_values for item_obj in (longsword_obj, rapier_obj, mace_obj, staff_obj)))
        state_items = tuple(sorted(self.items_state_obj.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Dagger', dagger_obj), ('Gold_Piece', gold_piece_obj),
                              ('Health_Potion', health_potion_obj), ('Longsword', longsword_obj),
                              ('Mace', mace_obj), ('Magic_Sword', magic_sword_obj),
                              ('Magic_Wand', magic_wand_obj), ('Mana_Potion', mana_potion_obj),
                              ('Rapier', rapier_obj), ('Scale_Mail', scale_mail_obj),
                              ('Shield', shield_obj), ('Short_Sword', short_sword_obj),
                              ('Small_Leather_Armor', small_leather_armor_obj), ('Staff', staff_obj),
                              ('Studded_Leather', studded_leather_obj), ('Warhammer', warhammer_obj))
        self.assertEqual(state_items, items_compare_with)
        self.assertEqual(self.items_state_obj.size(), 16)


class test_rooms_state_obj(unittest.TestCase):
    def __init__(self, *argl, **argd):
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Creatures_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.creatures_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Rooms_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.rooms_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)
        _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
        temp_ini_config_fh = open(temp_ini_config_file, 'w')
        temp_ini_config_fh.write(Items_Ini_Config_Text)
        temp_ini_config_fh.close()
        self.items_ini_config_obj = iniconfig.IniConfig(temp_ini_config_file)
        os.remove(temp_ini_config_file)
        super().__init__(*argl, **argd)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.items_state_obj, self.creatures_state_obj, **self.rooms_ini_config_obj.sections)

    def test_rooms_state_obj_init(self):
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_1,1')
        self.assertTrue(self.rooms_state_obj.cursor.is_entrance)
        self.assertFalse(self.rooms_state_obj.cursor.is_exit)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Southwest dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Entrance room')
        self.assertTrue(self.rooms_state_obj.cursor.has_north_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_east_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_south_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_west_exit)
        self.rooms_state_obj.move(north=True)

    def test_rooms_state_obj_move_east(self):
        self.rooms_state_obj.move(east=True)
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_1,2')
        self.assertFalse(self.rooms_state_obj.cursor.is_entrance)
        self.assertFalse(self.rooms_state_obj.cursor.is_exit)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Southeast dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Nondescript room')
        self.assertTrue(self.rooms_state_obj.cursor.has_north_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_east_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_south_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_west_exit)

    def test_rooms_state_obj_move_north(self):
        self.rooms_state_obj.move(north=True)
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_2,1')
        self.assertFalse(self.rooms_state_obj.cursor.is_entrance)
        self.assertFalse(self.rooms_state_obj.cursor.is_exit)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Northwest dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Nondescript room')
        self.assertFalse(self.rooms_state_obj.cursor.has_north_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_east_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_south_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_west_exit)

    def test_rooms_state_obj_move_north_and_east(self):
        self.rooms_state_obj.move(north=True)
        self.rooms_state_obj.move(east=True)
        self.assertEqual(self.rooms_state_obj.cursor.internal_name, 'Room_2,2')
        self.assertTrue(self.rooms_state_obj.cursor.is_exit)
        self.assertFalse(self.rooms_state_obj.cursor.is_entrance)
        self.assertEqual(self.rooms_state_obj.cursor.title, 'Northeast dungeon room')
        self.assertEqual(self.rooms_state_obj.cursor.description, 'Exit room')
        self.assertFalse(self.rooms_state_obj.cursor.has_north_exit)
        self.assertFalse(self.rooms_state_obj.cursor.has_east_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_south_exit)
        self.assertTrue(self.rooms_state_obj.cursor.has_west_exit)

    def test_rooms_state_obj_invalid_move(self):
        with self.assertRaises(bad_command_exception):
            self.rooms_state_obj.move(south=True)


if __name__ == '__main__':
    unittest.main()
