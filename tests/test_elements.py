#!/usr/bin/python3

import math
import operator
import unittest

import iniconfig

from .context import advgame as advg


containers_ini_config = iniconfig.IniConfig('./testing_data/containers.ini')
items_ini_config = iniconfig.IniConfig('./testing_data/items.ini')
doors_ini_config = iniconfig.IniConfig('./testing_data/doors.ini')
creatures_ini_config = iniconfig.IniConfig('./testing_data/creatures.ini')
rooms_ini_config = iniconfig.IniConfig('./testing_data/rooms.ini')


class Test_Container(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)

    def test_container(self):
        container = self.containers_state.get('Wooden_Chest_1')
        self.assertEqual(container.internal_name, 'Wooden_Chest_1')
        self.assertEqual(container.title, 'wooden chest')
        self.assertEqual(container.description,
                         'This small, serviceable chest is made of wooden slats bound within an iron frame, and '
                         + 'features a sturdy-looking lock.')
        self.assertEqual(container.is_locked, True)
        self.assertTrue(container.contains('Gold_Coin'))
        self.assertTrue(container.contains('Warhammer'))
        self.assertTrue(container.contains('Mana_Potion'))
        potion_qty, mana_potion = container.get('Mana_Potion')
        self.assertIsInstance(mana_potion, advg.Potion)
        self.assertEqual(potion_qty, 1)
        container.delete('Mana_Potion')
        self.assertFalse(container.contains('Mana_Potion'))
        container.set('Mana_Potion', potion_qty, mana_potion)
        self.assertTrue(container.contains('Mana_Potion'))


class Test_Character(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)

    def test_attack_and_damage_rolls_1(self):
        character = advg.Character('Regdar', 'Warrior')
        self.assertEqual(character.character_name, 'Regdar')
        self.assertEqual(character.character_class, 'Warrior')
        longsword = self.items_state.get('Longsword')
        scale_mail = self.items_state.get('Scale_Mail')
        shield = self.items_state.get('Steel_Shield')
        with self.assertRaises(advg.InternalError):
            character.equip_weapon(longsword)
        character.pick_up_item(longsword)
        character.pick_up_item(scale_mail)
        character.pick_up_item(shield)
        character.equip_weapon(longsword)
        character.equip_armor(scale_mail)
        character.equip_shield(shield)
        self.assertTrue(character.armor_equipped)
        self.assertTrue(character.shield_equipped)
        self.assertTrue(character.weapon_equipped)
        self.assertFalse(character.wand_equipped)
        strength_mod = character.strength_mod
        strength_mod_str = ('+' + str(strength_mod) if strength_mod > 0
                            else str(strength_mod) if strength_mod < 0 else '')
        self.assertEqual(character.attack_roll, '1d20' + strength_mod_str)
        self.assertEqual(character.damage_roll, '1d8' + strength_mod_str)
        self.assertEqual(character.attack_bonus, character.strength_mod)
        self.assertEqual(character.armor_class, 10 + scale_mail.armor_bonus + shield.armor_bonus
                         + character.dexterity_mod)
        self.assertEqual(character.weapon, longsword)
        self.assertEqual(character.armor, scale_mail)
        self.assertEqual(character.shield, shield)
        character.unequip_weapon()
        character.unequip_armor()
        character.unequip_shield()
        self.assertFalse(character.armor_equipped)
        self.assertFalse(character.shield_equipped)
        self.assertFalse(character.weapon_equipped)

    def test_attack_and_damage_rolls_2(self):
        character = advg.Character('Mialee', 'Mage')
        wand = self.items_state.get('Magic_Wand')
        character.pick_up_item(wand)
        character.equip_wand(wand)
        self.assertFalse(character.armor_equipped)
        self.assertFalse(character.shield_equipped)
        self.assertFalse(character.weapon_equipped)
        self.assertTrue(character.wand_equipped)
        total_atk_bonus = wand.attack_bonus + character.intelligence_mod
        total_dmg_bonus = int(wand.damage.split('+')[1]) + character.intelligence_mod
        total_atk_bonus_str = ('+' + str(total_atk_bonus) if total_atk_bonus > 0
                               else str(total_atk_bonus) if total_atk_bonus < 0 else '')
        total_dmg_bonus_str = ('+' + str(total_dmg_bonus) if total_dmg_bonus > 0
                               else str(total_dmg_bonus) if total_dmg_bonus < 0 else '')
        self.assertEqual(character.attack_roll, '1d20' + total_atk_bonus_str)
        self.assertEqual(character.damage_roll, '3d8' + total_dmg_bonus_str)
        self.assertEqual(character.attack_bonus, int(wand.attack_bonus) + character.intelligence_mod)
        self.assertEqual(character.armor_class, 10 + character.dexterity_mod)
        self.assertEqual(character.wand, wand)
        character.unequip_wand()
        self.assertFalse(character.wand_equipped)

    def test_pickup_vs_drop_vs_list(self):
        character = advg.Character('Regdar', 'Warrior')
        longsword = self.items_state.get('Longsword')
        scale_mail = self.items_state.get('Scale_Mail')
        shield = self.items_state.get('Steel_Shield')
        character.pick_up_item(longsword)
        character.pick_up_item(scale_mail)
        character.pick_up_item(shield)
        testing_items_list = list(sorted((longsword, scale_mail, shield),
                                         key=operator.attrgetter('title')))
        given_items_list = list(sorted(map(operator.itemgetter(1), character.list_items()),
                                       key=operator.attrgetter('title')))
        self.assertEqual(testing_items_list, given_items_list)
        character.drop_item(longsword)
        character.drop_item(scale_mail)
        character.drop_item(shield)
        self.assertFalse(character.have_item(longsword))
        character.pick_up_item(longsword, qty=5)
        self.assertTrue(character.have_item(longsword))
        self.assertEqual(character.item_have_qty(longsword), 5)
        character.drop_item(longsword, qty=3)
        self.assertEqual(character.item_have_qty(longsword), 2)
        character.drop_item(longsword, qty=2)
        self.assertEqual(character.item_have_qty(longsword), 0)
        self.assertFalse(character.have_item(longsword))

    def test_character_ability_scores(self):
        character = advg.Character('Regdar', 'Warrior')
        self.assertEqual(math.floor((character.strength - 10) / 2), character.strength_mod)
        self.assertEqual(math.floor((character.dexterity - 10) / 2), character.dexterity_mod)
        self.assertEqual(math.floor((character.constitution - 10) / 2), character.constitution_mod)
        self.assertEqual(math.floor((character.intelligence - 10) / 2), character.intelligence_mod)
        self.assertEqual(math.floor((character.wisdom - 10) / 2), character.wisdom_mod)
        self.assertEqual(math.floor((character.charisma - 10) / 2), character.charisma_mod)

    def test_character_mana_points_and_spending_mana_and_regaining_it(self):
        character = advg.Character('Mialee', 'Mage')
        bonus_mana_points = {-4: 0, -3: 0, -2: 0, -1: 0, 0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
        self.assertEqual(character.mana_points, 19 + bonus_mana_points[character.intelligence_mod])
        self.assertEqual(character.mana_point_total, 19 + bonus_mana_points[character.intelligence_mod])
        character.spend_mana(10)
        self.assertEqual(character.mana_points, 9 + bonus_mana_points[character.intelligence_mod])
        self.assertEqual(character.mana_point_total, 19 + bonus_mana_points[character.intelligence_mod])
        regained_amt = character.regain_mana(20)
        self.assertEqual(regained_amt, 10)
        self.assertEqual(character.mana_points, 19 + bonus_mana_points[character.intelligence_mod])
        self.assertEqual(character.mana_point_total, 19 + bonus_mana_points[character.intelligence_mod])
        character = advg.Character('Kaeva', 'Priest')
        bonus_mana_points = {-4: 0, -3: 0, -2: 0, -1: 0, 0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
        self.assertEqual(character.mana_points, 16 + bonus_mana_points[character.wisdom_mod])
        self.assertEqual(character.mana_point_total, 16 + bonus_mana_points[character.wisdom_mod])
        spent_amt = character.spend_mana(50)
        self.assertEqual(spent_amt, 0)

    def test_character_hitpoints_and_taking_damage_and_healing(self):
        character = advg.Character('Regdar', 'Warrior')
        self.assertEqual(character.hit_points, 40 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 40 + 3 * character.constitution_mod)
        character.take_damage(10)
        self.assertEqual(character.hit_points, 30 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 40 + 3 * character.constitution_mod)
        healed_amt = character.heal_damage(20)
        self.assertEqual(healed_amt, 10)
        self.assertEqual(character.hit_points, 40 + 3 * character.constitution_mod)
        character = advg.Character('Tordek', 'Priest')
        self.assertEqual(character.hit_points, 30 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 30 + 3 * character.constitution_mod)
        character = advg.Character('Lidda', 'Thief')
        self.assertEqual(character.hit_points, 30 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 30 + 3 * character.constitution_mod)
        character = advg.Character('Mialee', 'Mage')
        self.assertEqual(character.hit_points, 20 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 20 + 3 * character.constitution_mod)
        self.assertTrue(character.is_alive)
        self.assertFalse(character.is_dead)
        character.take_damage(20 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_points, 0)
        self.assertFalse(character.is_alive)
        self.assertTrue(character.is_dead)
        character.heal_damage(20 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_points, 20 + 3 * character.constitution_mod)
        self.assertTrue(character.is_alive)
        self.assertFalse(character.is_dead)

    def test_character_init_ability_score_and_hp_overrides(self):
        character = advg.Character('Regdar', 'Warrior', base_hit_points=50, strength=15, constitution=14, dexterity=13,
                                   intelligence=12, wisdom=8, charisma=10)
        self.assertEqual(character.strength, 15)
        self.assertEqual(character.constitution, 14)
        self.assertEqual(character.dexterity, 13)
        self.assertEqual(character.intelligence, 12)
        self.assertEqual(character.wisdom, 8)
        self.assertEqual(character.charisma, 10)
        self.assertEqual(character.hit_points, 56)  # base_hit_points := 50 + 3 * floor((constitution - 10) / 2)

    def test_mana_points(self):
        character = advg.Character('Hennet', 'Mage', base_hit_points=30, strength=12, constitution=13, dexterity=14,
                                   intelligence=15, wisdom=10, charisma=8)
        self.assertEqual(character.mana_points, 23)
        self.assertEqual(character.mana_point_total, 23)
        result = character.spend_mana(10)
        self.assertTrue(result)
        self.assertEqual(character.mana_points, 13)
        self.assertEqual(character.mana_point_total, 23)
        result = character.spend_mana(15)
        self.assertFalse(result)
        self.assertEqual(character.mana_points, 13)


class Test_Creature(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)

    def test_creature_const_1(self):
        kobold = self.creatures_state.get('Kobold_Trysk')
        self.assertEqual(kobold.character_class, 'Thief')
        self.assertEqual(kobold.character_name, 'Trysk')
        self.assertEqual(kobold.species, 'Kobold')
        self.assertEqual(kobold.description,
                         'This diminuitive draconic humanoid is dressed in leather armor and has a short sword at its '
                         + 'hip. It eyes you warily.')
        self.assertEqual(kobold.character_class, 'Thief')
        self.assertEqual(kobold.strength, 9)
        self.assertEqual(kobold.dexterity, 13)
        self.assertEqual(kobold.constitution, 10)
        self.assertEqual(kobold.intelligence, 10)
        self.assertEqual(kobold.wisdom, 9)
        self.assertEqual(kobold.charisma, 8)
        self.assertEqual(kobold.hit_points, 20)
        short_sword = self.items_state.get('Short_Sword')
        small_leather_armor = self.items_state.get('Small_Leather_Armor')
        self.assertEqual(kobold.weapon_equipped, short_sword)
        self.assertEqual(kobold.armor_equipped, small_leather_armor)

    def test_creature_const_2(self):
        sorcerer = self.creatures_state.get('Sorcerer_Ardren')
        self.assertEqual(sorcerer.magic_key_stat, 'charisma')
        self.assertEqual(sorcerer.mana_points, 36)

    def test_convert_to_corpse(self):
        kobold = self.creatures_state.get('Kobold_Trysk')
        kobold_corpse = kobold.convert_to_corpse()
        self.assertEqual(kobold_corpse.description, kobold.description_dead)
        self.assertEqual(kobold_corpse.title, f'{kobold.title} corpse')
        self.assertEqual(kobold_corpse.internal_name, kobold.internal_name)
        for item_internal_name, (item_qty, item) in kobold.inventory.items():
            self.assertEqual(kobold_corpse.get(item_internal_name), (item_qty, item))


class Test_Equipment(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)

    def test_equipment_1(self):
        equipment = advg.Equipment('Warrior')
        self.assertFalse(equipment.weapon_equipped)
        self.assertFalse(equipment.armor_equipped)
        self.assertFalse(equipment.shield_equipped)
        self.assertFalse(equipment.wand_equipped)
        equipment.equip_armor(self.items_state.get('Scale_Mail'))
        equipment.equip_shield(self.items_state.get('Steel_Shield'))
        equipment.equip_weapon(self.items_state.get('Magic_Sword'))
        self.assertTrue(equipment.armor_equipped)
        self.assertTrue(equipment.shield_equipped)
        self.assertTrue(equipment.weapon_equipped)
        with self.assertRaises(advg.InternalError):
            equipment.equip_armor(self.items_state.get('Steel_Shield'))
        self.assertEqual(equipment.armor_class, 16)
        self.assertEqual(equipment.attack_bonus, 3)
        self.assertEqual(equipment.damage, '1d12+3')
        equipment.unequip_armor()
        equipment.unequip_shield()
        equipment.unequip_weapon()
        self.assertFalse(equipment.armor_equipped)
        self.assertFalse(equipment.shield_equipped)
        self.assertFalse(equipment.weapon_equipped)

    def test_equipment_2(self):
        equipment = advg.Equipment('Mage')
        self.assertFalse(equipment.wand_equipped)
        equipment.equip_wand(self.items_state.get('Magic_Wand'))
        self.assertTrue(equipment.wand_equipped)
        equipment.unequip_wand()
        self.assertFalse(equipment.wand_equipped)


class Test_AbilityScores(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_ability_scores_args_exception(self):
        with self.assertRaises(advg.InternalError):
            advg.AbilityScores('Ranger')

    def test_roll_stats(self):
        ability_scores = advg.AbilityScores('Warrior')
        ability_scores.roll_stats()
        self.assertTrue(ability_scores.strength >= ability_scores.constitution >= ability_scores.dexterity
                        >= ability_scores.intelligence >= ability_scores.charisma >= ability_scores.wisdom)
        ability_scores = advg.AbilityScores('Thief')
        ability_scores.roll_stats()
        self.assertTrue(ability_scores.dexterity >= ability_scores.constitution
                        >= ability_scores.charisma >= ability_scores.strength
                        >= ability_scores.wisdom >= ability_scores.intelligence)
        ability_scores = advg.AbilityScores('Priest')
        ability_scores.roll_stats()
        self.assertTrue(ability_scores.wisdom >= ability_scores.strength
                        >= ability_scores.constitution >= ability_scores.charisma
                        >= ability_scores.intelligence >= ability_scores.dexterity)
        ability_scores = advg.AbilityScores('Mage')
        ability_scores.roll_stats()
        self.assertTrue(ability_scores.intelligence >= ability_scores.dexterity
                        >= ability_scores.constitution >= ability_scores.strength
                        >= ability_scores.wisdom >= ability_scores.charisma)

    def test_reroll_stats(self):
        ability_scores = advg.AbilityScores('Warrior')
        ability_scores.roll_stats()
        first_stat_roll = (ability_scores.strength, ability_scores.constitution, ability_scores.dexterity,
                           ability_scores.intelligence, ability_scores.charisma, ability_scores.wisdom)
        ability_scores.roll_stats()
        second_stat_roll = (ability_scores.strength, ability_scores.constitution, ability_scores.dexterity,
                            ability_scores.intelligence, ability_scores.charisma, ability_scores.wisdom)

        # This is a test of a method with a random element, so the results are nondeterministic. I'm looking for the
        # second call to `roll_stats()` to yield different stats, but there's a chance that the results are identical;
        # so I reroll until the results are different.
        while first_stat_roll == second_stat_roll:
            ability_scores.roll_stats()
            second_stat_roll = (ability_scores.strength, ability_scores.constitution,
                                ability_scores.dexterity, ability_scores.intelligence,
                                ability_scores.charisma, ability_scores.wisdom)
        self.assertNotEqual(first_stat_roll, second_stat_roll)


class Test_Inventory(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.inventory = advg.Inventory(**items_ini_config.sections)

    def test_inventory_collection_methods(self):
        sword_qty, longsword = self.inventory.get('Longsword')
        self.assertTrue(self.inventory.contains(longsword.internal_name))
        self.assertEqual(sword_qty, 1)
        self.inventory.add_one(longsword.internal_name, longsword)
        sword_qty, longsword = self.inventory.get('Longsword')
        self.assertEqual(sword_qty, 2)
        self.inventory.remove_one('Longsword')
        sword_qty, longsword = self.inventory.get('Longsword')
        self.assertEqual(sword_qty, 1)
        self.inventory.delete('Longsword')
        with self.assertRaises(KeyError):
            self.inventory.get('Longsword')
        with self.assertRaises(KeyError):
            self.inventory.remove_one('Longsword')
        with self.assertRaises(KeyError):
            self.inventory.delete('Longsword')
        self.inventory.set('Longsword', 1, longsword)
        self.assertTrue(self.inventory.contains(longsword.internal_name))
        self.assertEqual(set(self.inventory.keys()), {'Longsword', 'Rapier', 'Buckler', 'Heavy_Mace', 'Staff',
                                                      'Warhammer', 'Door_Key', 'Chest_Key', 'Studded_Leather',
                                                      'Scale_Mail', 'Magic_Sword', 'Dagger', 'Gold_Coin',
                                                      'Small_Leather_Armor', 'Short_Sword', 'Steel_Shield',
                                                      'Mana_Potion', 'Health_Potion', 'Magic_Wand', 'Magic_Wand_2'})
        _, rapier, = self.inventory.get('Rapier')
        _, heavy_mace, = self.inventory.get('Heavy_Mace')
        _, staff = self.inventory.get('Staff')
        _, warhammer = self.inventory.get('Warhammer')
        _, studded_leather = self.inventory.get('Studded_Leather')
        _, scale_mail = self.inventory.get('Scale_Mail')
        _, magic_sword = self.inventory.get('Magic_Sword')
        _, chest_key = self.inventory.get('Chest_Key')
        _, door_key = self.inventory.get('Door_Key')
        _, dagger = self.inventory.get('Dagger')
        _, gold_coin = self.inventory.get('Gold_Coin')
        _, small_leather_armor = self.inventory.get('Small_Leather_Armor')
        _, short_sword = self.inventory.get('Short_Sword')
        _, shield = self.inventory.get('Steel_Shield')
        _, mana_potion = self.inventory.get('Mana_Potion')
        _, health_potion = self.inventory.get('Health_Potion')
        _, magic_wand = self.inventory.get('Magic_Wand')
        _, magic_wand_2 = self.inventory.get('Magic_Wand_2')
        _, buckler = self.inventory.get('Buckler')
        inventory_values = tuple(self.inventory.values())
        self.assertTrue(all((1, item) in inventory_values
                            for item in (longsword, rapier, heavy_mace, staff)))
        inventory_items = tuple(sorted(self.inventory.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Buckler', (1, buckler)), ('Chest_Key', (1, chest_key)),
                              ('Dagger', (1, dagger)), ('Door_Key', (1, door_key)),
                              ('Gold_Coin', (1, gold_coin)), ('Health_Potion', (1, health_potion)),
                              ('Longsword', (1, longsword)), ('Heavy_Mace', (1, heavy_mace)),
                              ('Magic_Sword', (1, magic_sword)), ('Magic_Wand', (1, magic_wand)),
                              ('Magic_Wand_2', (1, magic_wand_2)), ('Mana_Potion', (1, mana_potion)),
                              ('Rapier', (1, rapier)), ('Scale_Mail', (1, scale_mail)),
                              ('Steel_Shield', (1, shield)), ('Short_Sword', (1, short_sword)),
                              ('Small_Leather_Armor', (1, small_leather_armor)), ('Staff', (1, staff)),
                              ('Studded_Leather', (1, studded_leather)), ('Warhammer', (1, warhammer)))
        self.assertEqual(inventory_items, items_compare_with)
        self.assertEqual(self.inventory.size(), 20)

    def test_total_weight_and_burden_for_strength_score(self):
        for item_internal_name in ('Buckler', 'Dagger', 'Gold_Coin', 'Health_Potion', 'Magic_Sword', 'Magic_Wand',
                                   'Magic_Wand_2', 'Mana_Potion', 'Scale_Mail', 'Door_Key', 'Chest_Key',
                                   'Steel_Shield', 'Short_Sword', 'Small_Leather_Armor', 'Studded_Leather',
                                   'Warhammer'):
            self.inventory.remove_one(item_internal_name)
        self.assertEqual(self.inventory.total_weight, 13)
        self.assertEqual(self.inventory.burden_for_strength_score(4), advg.Inventory.LIGHT)
        self.assertEqual(self.inventory.burden_for_strength_score(3), advg.Inventory.MEDIUM)
        for item_name, (_, item) in self.inventory.items():
            self.inventory.set(item_name, 4, item)
        self.assertEqual(self.inventory.total_weight, 52)
        self.assertEqual(self.inventory.burden_for_strength_score(6), advg.Inventory.HEAVY)
        self.assertEqual(self.inventory.burden_for_strength_score(3), advg.Inventory.IMMOBILIZING)


class Test_Door_and_DoorsState(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)

    def test_doors_state(self):
        doors_state_keys = self.doors_state.keys()
        self.assertEqual(doors_state_keys, [('Room_1,1', 'Room_1,2'), ('Room_1,1', 'Room_2,1'),
                                            ('Room_1,2', 'Room_2,2'), ('Room_2,1', 'Room_2,2'),
                                            ('Room_2,2', 'Exit')])
        doors_state_values = self.doors_state.values()
        self.assertTrue(all(isinstance(door, advg.Door) and isinstance(door, (advg.WoodenDoor, advg.IronDoor,
                                                                              advg.Doorway))
                            for door in doors_state_values))
        doors_state_items = self.doors_state.items()
        self.assertEqual(list(map(operator.itemgetter(0, 1), doors_state_items)), [('Room_1,1', 'Room_1,2'),
                                                                                   ('Room_1,1', 'Room_2,1'),
                                                                                   ('Room_1,2', 'Room_2,2'),
                                                                                   ('Room_2,1', 'Room_2,2'),
                                                                                   ('Room_2,2', 'Exit')])
        self.assertTrue(all(isinstance(door, advg.Door) and isinstance(door, (advg.WoodenDoor, advg.IronDoor,
                                                                              advg.Doorway))
                            for door in doors_state_values))
        self.assertEqual(self.doors_state.size(), 5)
        self.assertTrue(self.doors_state.contains('Room_2,1', 'Room_2,2'))
        door = self.doors_state.get('Room_1,2', 'Room_2,2')
        self.assertEqual(door.title, 'doorway')
        self.assertEqual(door.description, 'This open doorway is outlined by a stone arch set into the wall.')
        self.assertEqual(door.door_type, 'doorway')
        self.assertFalse(door.is_locked, False)
        self.assertFalse(door.is_closed, False)
        self.assertFalse(door.closeable, False)
        self.doors_state.delete('Room_1,2', 'Room_2,2')
        self.assertFalse(self.doors_state.contains('Room_1,2', 'Room_2,2'))
        self.doors_state.set('Room_1,2', 'Room_2,2', door)
        self.assertTrue(self.doors_state.contains('Room_1,2', 'Room_2,2'))

    def test_doors_state_and_door_1(self):
        door = self.doors_state.get('Room_1,1', 'Room_1,2')
        self.assertEqual(door.title, 'iron door')
        self.assertEqual(door.description, 'This door is bound in iron plates with a small barred window set up high.')
        self.assertEqual(door.door_type, 'iron_door')
        self.assertEqual(door.is_locked, False)
        self.assertEqual(door.is_closed, True)
        self.assertEqual(door.closeable, True)

        door = self.doors_state.get('Room_1,1', 'Room_2,1')
        self.assertEqual(door.title, 'iron door')
        self.assertEqual(door.description,
                         'This door is bound in iron plates with a small barred window set up high.')
        self.assertEqual(door.door_type, 'iron_door')
        self.assertEqual(door.is_locked, True)
        self.assertEqual(door.is_closed, True)
        self.assertEqual(door.closeable, True)

        door = self.doors_state.get('Room_1,2', 'Room_2,2')
        self.assertEqual(door.title, 'doorway')
        self.assertEqual(door.description, 'This open doorway is outlined by a stone arch set into the wall.')
        self.assertEqual(door.door_type, 'doorway')
        self.assertEqual(door.is_locked, False)
        self.assertEqual(door.is_closed, False)
        self.assertEqual(door.closeable, False)

    def test_doors_state_and_door_2(self):
        door = self.doors_state.get('Room_1,1', 'Room_1,2')
        self.assertIsInstance(door, advg.IronDoor)
        door_copy = door.copy()
        self.assertIsInstance(door_copy, advg.IronDoor)


class Test_Item_and_ItemsState(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)

    def test_items_values(self):
        self.assertEqual(self.items_state.get('Longsword').title, 'longsword')
        self.assertIsInstance(self.items_state.get('Longsword'), advg.Weapon)
        self.assertEqual(self.items_state.get('Longsword').description,
                         'A hefty sword with a long blade, a broad hilt and a leathern grip.')
        self.assertEqual(self.items_state.get('Longsword').weight, 3)
        self.assertEqual(self.items_state.get('Longsword').value, 15)
        self.assertEqual(self.items_state.get('Longsword').damage, '1d8')
        self.assertEqual(self.items_state.get('Longsword').attack_bonus, 0)
        self.assertEqual(self.items_state.get('Longsword').warrior_can_use, True)

    def test_usable_by(self):
        self.assertTrue(self.items_state.get('Longsword').usable_by('Warrior'))
        self.assertFalse(self.items_state.get('Longsword').usable_by('Thief'))
        self.assertFalse(self.items_state.get('Longsword').usable_by('Priest'))
        self.assertFalse(self.items_state.get('Longsword').usable_by('Mage'))
        self.assertTrue(self.items_state.get('Rapier').usable_by('Warrior'))
        self.assertTrue(self.items_state.get('Rapier').usable_by('Thief'))
        self.assertFalse(self.items_state.get('Rapier').usable_by('Priest'))
        self.assertFalse(self.items_state.get('Rapier').usable_by('Mage'))
        self.assertTrue(self.items_state.get('Heavy_Mace').usable_by('Warrior'))
        self.assertFalse(self.items_state.get('Heavy_Mace').usable_by('Thief'))
        self.assertTrue(self.items_state.get('Heavy_Mace').usable_by('Priest'))
        self.assertFalse(self.items_state.get('Heavy_Mace').usable_by('Mage'))
        self.assertTrue(self.items_state.get('Staff').usable_by('Warrior'))
        self.assertFalse(self.items_state.get('Staff').usable_by('Thief'))
        self.assertFalse(self.items_state.get('Staff').usable_by('Priest'))
        self.assertTrue(self.items_state.get('Staff').usable_by('Mage'))

    def test_state_collection_interface(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        longsword = self.items_state.get('Longsword')
        self.assertTrue(self.items_state.contains(longsword.internal_name))
        self.items_state.delete('Longsword')
        with self.assertRaises(KeyError):
            self.items_state.get('Longsword')
        with self.assertRaises(KeyError):
            self.items_state.delete('Longsword')
        self.items_state.set('Longsword', longsword)
        self.assertTrue(self.items_state.contains(longsword.internal_name))
        self.assertEqual(set(self.items_state.keys()), {'Buckler', 'Longsword', 'Rapier', 'Heavy_Mace', 'Staff',
                                                        'Warhammer', 'Studded_Leather', 'Door_Key', 'Chest_Key',
                                                        'Scale_Mail', 'Magic_Sword', 'Dagger', 'Gold_Coin',
                                                        'Small_Leather_Armor', 'Short_Sword', 'Steel_Shield',
                                                        'Mana_Potion', 'Magic_Wand', 'Magic_Wand_2',
                                                        'Health_Potion'})
        rapier = self.items_state.get('Rapier')
        heavy_mace = self.items_state.get('Heavy_Mace')
        staff = self.items_state.get('Staff')
        warhammer = self.items_state.get('Warhammer')
        studded_leather = self.items_state.get('Studded_Leather')
        scale_mail = self.items_state.get('Scale_Mail')
        door_key = self.items_state.get('Door_Key')
        chest_key = self.items_state.get('Chest_Key')
        magic_sword = self.items_state.get('Magic_Sword')
        dagger = self.items_state.get('Dagger')
        gold_coin = self.items_state.get('Gold_Coin')
        small_leather_armor = self.items_state.get('Small_Leather_Armor')
        short_sword = self.items_state.get('Short_Sword')
        shield = self.items_state.get('Steel_Shield')
        mana_potion = self.items_state.get('Mana_Potion')
        health_potion = self.items_state.get('Health_Potion')
        magic_wand = self.items_state.get('Magic_Wand')
        magic_wand_2 = self.items_state.get('Magic_Wand_2')
        buckler = self.items_state.get('Buckler')
        state_values = tuple(self.items_state.values())
        self.assertTrue(all(item in state_values for item in (longsword, rapier, heavy_mace, staff)))
        state_items = tuple(sorted(self.items_state.items(), key=operator.itemgetter(0)))
        items_compare_with = (('Buckler', buckler), ('Chest_Key', chest_key), ('Dagger', dagger),
                              ('Door_Key', door_key), ('Gold_Coin', gold_coin), ('Health_Potion', health_potion),
                              ('Heavy_Mace', heavy_mace), ('Longsword', longsword), ('Magic_Sword', magic_sword),
                              ('Magic_Wand', magic_wand), ('Magic_Wand_2', magic_wand_2), ('Mana_Potion', mana_potion),
                              ('Rapier', rapier), ('Scale_Mail', scale_mail), ('Short_Sword', short_sword),
                              ('Small_Leather_Armor', small_leather_armor), ('Staff', staff), ('Steel_Shield', shield),
                              ('Studded_Leather', studded_leather), ('Warhammer', warhammer))
        self.assertEqual(state_items, items_compare_with)
        self.assertEqual(self.items_state.size(), 20)


class Test_RoomsState_Obj(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)

    def test_rooms_state_init(self):
        self.assertEqual(self.rooms_state.cursor.internal_name, 'Room_1,1')
        self.assertTrue(self.rooms_state.cursor.is_entrance)
        self.assertFalse(self.rooms_state.cursor.is_exit)
        self.assertEqual(self.rooms_state.cursor.title, 'southwest dungeon room')
        self.assertEqual(self.rooms_state.cursor.description, 'Entrance room.')
        self.assertTrue(self.rooms_state.cursor.has_north_door)
        self.assertEqual(self.rooms_state.cursor.north_door.title, 'north door')
        self.assertEqual(self.rooms_state.cursor.north_door.description, 'This door is bound in iron plates with a '
                                                                         'small barred window set up high.')
        self.assertEqual(self.rooms_state.cursor.north_door.door_type, 'iron_door')
        self.assertEqual(self.rooms_state.cursor.north_door.is_locked, False)
        self.assertEqual(self.rooms_state.cursor.north_door.is_closed, True)
        self.assertEqual(self.rooms_state.cursor.north_door.closeable, True)
        self.assertTrue(self.rooms_state.cursor.has_east_door)
        self.assertTrue(self.rooms_state.cursor.east_door.title, 'east door')
        self.assertTrue(self.rooms_state.cursor.east_door.description,
                        'This door is bound in iron plates with a small barred window set up high.')
        self.assertTrue(self.rooms_state.cursor.east_door.door_type, 'iron_door')
        self.assertTrue(self.rooms_state.cursor.east_door.is_locked, True)
        self.assertTrue(self.rooms_state.cursor.east_door.is_closed, True)
        self.assertTrue(self.rooms_state.cursor.east_door.closeable, True)
        self.assertFalse(self.rooms_state.cursor.has_south_door)
        self.assertFalse(self.rooms_state.cursor.has_west_door)
        self.rooms_state.move(north=True)

    def test_rooms_state_move_east(self):
        self.rooms_state.cursor.east_door.is_locked = False
        self.rooms_state.move(east=True)
        self.assertEqual(self.rooms_state.cursor.internal_name, 'Room_2,1')
        self.assertFalse(self.rooms_state.cursor.is_entrance)
        self.assertFalse(self.rooms_state.cursor.is_exit)
        self.assertEqual(self.rooms_state.cursor.title, 'southeast dungeon room')
        self.assertEqual(self.rooms_state.cursor.description, 'Nondescript room.')
        self.assertTrue(self.rooms_state.cursor.has_north_door)
        self.assertFalse(self.rooms_state.cursor.has_east_door)
        self.assertFalse(self.rooms_state.cursor.has_south_door)
        self.assertTrue(self.rooms_state.cursor.has_west_door)

    def test_rooms_state_move_north(self):
        self.rooms_state.move(north=True)
        self.assertEqual(self.rooms_state.cursor.internal_name, 'Room_1,2')
        self.assertFalse(self.rooms_state.cursor.is_entrance)
        self.assertFalse(self.rooms_state.cursor.is_exit)
        self.assertEqual(self.rooms_state.cursor.title, 'northwest dungeon room')
        self.assertEqual(self.rooms_state.cursor.description, 'Nondescript room.')
        self.assertFalse(self.rooms_state.cursor.has_north_door)
        self.assertTrue(self.rooms_state.cursor.has_east_door)
        self.assertTrue(self.rooms_state.cursor.has_south_door)
        self.assertFalse(self.rooms_state.cursor.has_west_door)

    def test_rooms_state_move_north_and_east(self):
        self.rooms_state.cursor.east_door.is_locked = False
        self.rooms_state.move(north=True)
        self.rooms_state.move(east=True)
        self.assertTrue(self.rooms_state.cursor.west_door.title, 'west doorway')
        self.assertTrue(self.rooms_state.cursor.west_door.description,
                        'This door is bound in iron plates with a small barred window set up high.')
        self.assertTrue(self.rooms_state.cursor.west_door.door_type, 'doorway')
        self.assertFalse(self.rooms_state.cursor.west_door.is_locked)
        self.assertFalse(self.rooms_state.cursor.west_door.is_closed)
        self.assertFalse(self.rooms_state.cursor.west_door.closeable)
        self.assertEqual(self.rooms_state.cursor.internal_name, 'Room_2,2')
        self.assertTrue(self.rooms_state.cursor.is_exit)
        self.assertFalse(self.rooms_state.cursor.is_entrance)
        self.assertEqual(self.rooms_state.cursor.title, 'northeast dungeon room')
        self.assertEqual(self.rooms_state.cursor.description, 'Exit room.')
        self.assertTrue(self.rooms_state.cursor.has_north_door)
        self.assertFalse(self.rooms_state.cursor.has_east_door)
        self.assertTrue(self.rooms_state.cursor.has_south_door)
        self.assertTrue(self.rooms_state.cursor.has_west_door)

    def test_rooms_state_invalid_move(self):
        with self.assertRaises(advg.BadCommandError):
            self.rooms_state.move(south=True)

    def test_rooms_state_room_items_container_creature_here(self):
        kobold = self.creatures_state.get('Kobold_Trysk')
        wooden_chest = self.containers_state.get('Wooden_Chest_1')
        mana_potion = self.items_state.get('Mana_Potion')
        health_potion = self.items_state.get('Health_Potion')
        room = self.rooms_state.cursor
        self.assertEqual(room.creature_here, kobold)
        self.assertEqual(room.container_here, wooden_chest)
        self.assertEqual(room.items_here.get('Mana_Potion'), (1, mana_potion))
        self.assertEqual(room.items_here.get('Health_Potion'), (2, health_potion))

    def test_rooms_state_and_door(self):
        self.assertIsInstance(self.rooms_state.cursor.north_door, advg.Door)
        self.assertEqual(self.rooms_state.cursor.north_door.internal_name, 'Room_1,1_x_Room_1,2')
        self.assertEqual(self.rooms_state.cursor.east_door.internal_name, 'Room_1,1_x_Room_2,1')

    def test_room_doors(self):
        doors_tuple = self.rooms_state.cursor.doors
        self.assertEqual(doors_tuple[0].internal_name, 'Room_1,1_x_Room_1,2')
        self.assertEqual(doors_tuple[1].internal_name, 'Room_1,1_x_Room_2,1')


class Test_GameState(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)

    def test_game_state(self):
        self.assertFalse(self.game_state.game_has_begun)
        self.assertFalse(self.game_state.game_has_ended)
        self.assertIs(self.game_state.character_name, None)
        self.assertIs(self.game_state.character_class, None)
        self.assertIs(getattr(self.game_state, 'character', None), None)
        self.game_state.character_name = 'Kaeva'
        self.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        self.assertEqual(self.game_state.character_name, 'Kaeva')
        self.assertEqual(self.game_state.character_class, 'Priest')
        self.assertIsNot(getattr(self.game_state, 'character', None), None)
