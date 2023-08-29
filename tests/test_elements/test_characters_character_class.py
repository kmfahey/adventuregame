#!/usr/bin/python3

from unittest import TestCase
from operator import attrgetter, itemgetter
from math import floor
from advgame import Character, InternalError, ItemsState
from ..context import items_ini_config


__all__ = ("Test_Character",)


class Test_Character(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)

    def test_attack_and_damage_rolls_1(self):
        character = Character("Regdar", "Warrior")
        self.assertEqual(character.character_name, "Regdar")
        self.assertEqual(character.character_class, "Warrior")
        longsword = self.items_state.get("Longsword")
        scale_mail = self.items_state.get("Scale_Mail")
        shield = self.items_state.get("Steel_Shield")
        with self.assertRaises(InternalError):
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
        strength_mod_str = (
            "+" + str(strength_mod)
            if strength_mod > 0
            else str(strength_mod)
            if strength_mod < 0
            else ""
        )
        self.assertEqual(character.attack_roll, "1d20" + strength_mod_str)
        self.assertEqual(character.damage_roll, "1d8" + strength_mod_str)
        self.assertEqual(character.attack_bonus, character.strength_mod)
        self.assertEqual(
            character.armor_class,
            10 + scale_mail.armor_bonus + shield.armor_bonus + character.dexterity_mod,
        )
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
        character = Character("Mialee", "Mage")
        wand = self.items_state.get("Magic_Wand")
        character.pick_up_item(wand)
        character.equip_wand(wand)
        self.assertFalse(character.armor_equipped)
        self.assertFalse(character.shield_equipped)
        self.assertFalse(character.weapon_equipped)
        self.assertTrue(character.wand_equipped)
        total_atk_bonus = wand.attack_bonus + character.intelligence_mod
        total_dmg_bonus = int(wand.damage.split("+")[1]) + character.intelligence_mod
        total_atk_bonus_str = (
            "+" + str(total_atk_bonus)
            if total_atk_bonus > 0
            else str(total_atk_bonus)
            if total_atk_bonus < 0
            else ""
        )
        total_dmg_bonus_str = (
            "+" + str(total_dmg_bonus)
            if total_dmg_bonus > 0
            else str(total_dmg_bonus)
            if total_dmg_bonus < 0
            else ""
        )
        self.assertEqual(character.attack_roll, "1d20" + total_atk_bonus_str)
        self.assertEqual(character.damage_roll, "3d8" + total_dmg_bonus_str)
        self.assertEqual(
            character.attack_bonus, int(wand.attack_bonus) + character.intelligence_mod
        )
        self.assertEqual(character.armor_class, 10 + character.dexterity_mod)
        self.assertEqual(character.wand, wand)
        character.unequip_wand()
        self.assertFalse(character.wand_equipped)

    def test_pickup_vs_drop_vs_list(self):
        character = Character("Regdar", "Warrior")
        longsword = self.items_state.get("Longsword")
        scale_mail = self.items_state.get("Scale_Mail")
        shield = self.items_state.get("Steel_Shield")
        character.pick_up_item(longsword)
        character.pick_up_item(scale_mail)
        character.pick_up_item(shield)
        testing_items_list = list(
            sorted((longsword, scale_mail, shield), key=attrgetter("title"))
        )
        given_items_list = list(
            sorted(
                map(itemgetter(1), character.list_items()),
                key=attrgetter("title"),
            )
        )
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
        character = Character("Regdar", "Warrior")
        self.assertEqual(floor((character.strength - 10) / 2), character.strength_mod)
        self.assertEqual(floor((character.dexterity - 10) / 2), character.dexterity_mod)
        self.assertEqual(
            floor((character.constitution - 10) / 2), character.constitution_mod
        )
        self.assertEqual(
            floor((character.intelligence - 10) / 2), character.intelligence_mod
        )
        self.assertEqual(floor((character.wisdom - 10) / 2), character.wisdom_mod)
        self.assertEqual(floor((character.charisma - 10) / 2), character.charisma_mod)

    def test_character_mana_points_and_spending_mana_and_regaining_it(self):
        character = Character("Mialee", "Mage")
        bonus_mana_points = {-4: 0, -3: 0, -2: 0, -1: 0, 0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
        self.assertEqual(
            character.mana_points, 19 + bonus_mana_points[character.intelligence_mod]
        )
        self.assertEqual(
            character.mana_point_total,
            19 + bonus_mana_points[character.intelligence_mod],
        )
        character.spend_mana(10)
        self.assertEqual(
            character.mana_points, 9 + bonus_mana_points[character.intelligence_mod]
        )
        self.assertEqual(
            character.mana_point_total,
            19 + bonus_mana_points[character.intelligence_mod],
        )
        regained_amt = character.regain_mana(20)
        self.assertEqual(regained_amt, 10)
        self.assertEqual(
            character.mana_points, 19 + bonus_mana_points[character.intelligence_mod]
        )
        self.assertEqual(
            character.mana_point_total,
            19 + bonus_mana_points[character.intelligence_mod],
        )
        character = Character("Kaeva", "Priest")
        bonus_mana_points = {-4: 0, -3: 0, -2: 0, -1: 0, 0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
        self.assertEqual(
            character.mana_points, 16 + bonus_mana_points[character.wisdom_mod]
        )
        self.assertEqual(
            character.mana_point_total, 16 + bonus_mana_points[character.wisdom_mod]
        )
        spent_amt = character.spend_mana(50)
        self.assertEqual(spent_amt, 0)

    def test_character_hitpoints_and_taking_damage_and_healing(self):
        character = Character("Regdar", "Warrior")
        self.assertEqual(character.hit_points, 40 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 40 + 3 * character.constitution_mod)
        character.take_damage(10)
        self.assertEqual(character.hit_points, 30 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 40 + 3 * character.constitution_mod)
        healed_amt = character.heal_damage(20)
        self.assertEqual(healed_amt, 10)
        self.assertEqual(character.hit_points, 40 + 3 * character.constitution_mod)
        character = Character("Tordek", "Priest")
        self.assertEqual(character.hit_points, 30 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 30 + 3 * character.constitution_mod)
        character = Character("Lidda", "Thief")
        self.assertEqual(character.hit_points, 30 + 3 * character.constitution_mod)
        self.assertEqual(character.hit_point_total, 30 + 3 * character.constitution_mod)
        character = Character("Mialee", "Mage")
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
        character = Character(
            "Regdar",
            "Warrior",
            base_hit_points=50,
            strength=15,
            constitution=14,
            dexterity=13,
            intelligence=12,
            wisdom=8,
            charisma=10,
        )
        self.assertEqual(character.strength, 15)
        self.assertEqual(character.constitution, 14)
        self.assertEqual(character.dexterity, 13)
        self.assertEqual(character.intelligence, 12)
        self.assertEqual(character.wisdom, 8)
        self.assertEqual(character.charisma, 10)
        self.assertEqual(
            character.hit_points, 56
        )  # base_hit_points := 50 + 3 * floor((constitution - 10) / 2)

    def test_mana_points(self):
        character = Character(
            "Hennet",
            "Mage",
            base_hit_points=30,
            strength=12,
            constitution=13,
            dexterity=14,
            intelligence=15,
            wisdom=10,
            charisma=8,
        )
        self.assertEqual(character.mana_points, 23)
        self.assertEqual(character.mana_point_total, 23)
        result = character.spend_mana(10)
        self.assertTrue(result)
        self.assertEqual(character.mana_points, 13)
        self.assertEqual(character.mana_point_total, 23)
        result = character.spend_mana(15)
        self.assertFalse(result)
        self.assertEqual(character.mana_points, 13)
