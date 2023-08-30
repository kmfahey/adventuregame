#!/usr/bin/python3

from unittest import TestCase
from operator import itemgetter

from advgame import (
    AbilityScores,
    ContainersState,
    CreaturesState,
    DoorsState,
    Equipment,
    GameState,
    InternalError,
    ItemsState,
    RoomsState,
    Weapon,
)

from ..context import (
    containers_ini_config,
    creatures_ini_config,
    doors_ini_config,
    items_ini_config,
    rooms_ini_config,
)


__all__ = (
    "Test_Equipment",
    "Test_AbilityScores",
    "Test_GameState",
    "Test_Item_and_ItemsState",
)


class Test_Equipment(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)

    def test_equipment_1(self):
        equipment = Equipment("Warrior")
        self.assertFalse(equipment.weapon_equipped)
        self.assertFalse(equipment.armor_equipped)
        self.assertFalse(equipment.shield_equipped)
        self.assertFalse(equipment.wand_equipped)
        equipment.equip_armor(self.items_state.get("Scale_Mail"))
        equipment.equip_shield(self.items_state.get("Steel_Shield"))
        equipment.equip_weapon(self.items_state.get("Magic_Sword"))
        self.assertTrue(equipment.armor_equipped)
        self.assertTrue(equipment.shield_equipped)
        self.assertTrue(equipment.weapon_equipped)
        with self.assertRaises(InternalError):
            equipment.equip_armor(self.items_state.get("Steel_Shield"))
        self.assertEqual(equipment.armor_class, 16)
        self.assertEqual(equipment.attack_bonus, 3)
        self.assertEqual(equipment.damage, "1d12+3")
        equipment.unequip_armor()
        equipment.unequip_shield()
        equipment.unequip_weapon()
        self.assertFalse(equipment.armor_equipped)
        self.assertFalse(equipment.shield_equipped)
        self.assertFalse(equipment.weapon_equipped)

    def test_equipment_2(self):
        equipment = Equipment("Mage")
        self.assertFalse(equipment.wand_equipped)
        equipment.equip_wand(self.items_state.get("Magic_Wand"))
        self.assertTrue(equipment.wand_equipped)
        equipment.unequip_wand()
        self.assertFalse(equipment.wand_equipped)


class Test_AbilityScores(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_ability_scores_args_exception(self):
        with self.assertRaises(InternalError):
            AbilityScores("Ranger")

    def test_roll_stats(self):
        ability_scores = AbilityScores("Warrior")
        ability_scores.roll_stats()
        self.assertTrue(
            ability_scores.strength
            >= ability_scores.constitution
            >= ability_scores.dexterity
            >= ability_scores.intelligence
            >= ability_scores.charisma
            >= ability_scores.wisdom
        )
        ability_scores = AbilityScores("Thief")
        ability_scores.roll_stats()
        self.assertTrue(
            ability_scores.dexterity
            >= ability_scores.constitution
            >= ability_scores.charisma
            >= ability_scores.strength
            >= ability_scores.wisdom
            >= ability_scores.intelligence
        )
        ability_scores = AbilityScores("Priest")
        ability_scores.roll_stats()
        self.assertTrue(
            ability_scores.wisdom
            >= ability_scores.strength
            >= ability_scores.constitution
            >= ability_scores.charisma
            >= ability_scores.intelligence
            >= ability_scores.dexterity
        )
        ability_scores = AbilityScores("Mage")
        ability_scores.roll_stats()
        self.assertTrue(
            ability_scores.intelligence
            >= ability_scores.dexterity
            >= ability_scores.constitution
            >= ability_scores.strength
            >= ability_scores.wisdom
            >= ability_scores.charisma
        )

    def test_reroll_stats(self):
        ability_scores = AbilityScores("Warrior")
        ability_scores.roll_stats()
        first_stat_roll = (
            ability_scores.strength,
            ability_scores.constitution,
            ability_scores.dexterity,
            ability_scores.intelligence,
            ability_scores.charisma,
            ability_scores.wisdom,
        )
        ability_scores.roll_stats()
        second_stat_roll = (
            ability_scores.strength,
            ability_scores.constitution,
            ability_scores.dexterity,
            ability_scores.intelligence,
            ability_scores.charisma,
            ability_scores.wisdom,
        )

        # This is a test of a method with a random element, so the
        # results are nondeterministic. I'm looking for the second call
        # to `roll_stats()` to yield different stats, but there's a
        # chance that the results are identical; so I reroll until the
        # results are different.
        while first_stat_roll == second_stat_roll:
            ability_scores.roll_stats()
            second_stat_roll = (
                ability_scores.strength,
                ability_scores.constitution,
                ability_scores.dexterity,
                ability_scores.intelligence,
                ability_scores.charisma,
                ability_scores.wisdom,
            )
        self.assertNotEqual(first_stat_roll, second_stat_roll)


class Test_GameState(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        self.doors_state = DoorsState(**doors_ini_config.sections)
        self.containers_state = ContainersState(
            self.items_state, **containers_ini_config.sections
        )
        self.creatures_state = CreaturesState(
            self.items_state, **creatures_ini_config.sections
        )
        self.rooms_state = RoomsState(
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
            **rooms_ini_config.sections,
        )
        self.game_state = GameState(
            self.rooms_state,
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
        )

    def test_game_state(self):
        self.assertFalse(self.game_state.game_has_begun)
        self.assertFalse(self.game_state.game_has_ended)
        self.assertIs(self.game_state.character_name, None)
        self.assertIs(self.game_state.character_class, None)
        self.assertIs(getattr(self.game_state, "character", None), None)
        self.game_state.character_name = "Kaeva"
        self.game_state.character_class = "Priest"
        self.game_state.game_has_begun = True
        self.assertEqual(self.game_state.character_name, "Kaeva")
        self.assertEqual(self.game_state.character_class, "Priest")
        self.assertIsNot(getattr(self.game_state, "character", None), None)


class Test_Item_and_ItemsState(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)

    def test_items_values(self):
        self.assertEqual(self.items_state.get("Longsword").title, "longsword")
        self.assertIsInstance(self.items_state.get("Longsword"), Weapon)
        self.assertEqual(
            self.items_state.get("Longsword").description,
            "A hefty sword with a long blade, a broad hilt and a leathern grip.",
        )
        self.assertEqual(self.items_state.get("Longsword").weight, 3)
        self.assertEqual(self.items_state.get("Longsword").value, 15)
        self.assertEqual(self.items_state.get("Longsword").damage, "1d8")
        self.assertEqual(self.items_state.get("Longsword").attack_bonus, 0)
        self.assertEqual(self.items_state.get("Longsword").warrior_can_use, True)

    def test_usable_by(self):
        self.assertTrue(self.items_state.get("Longsword").usable_by("Warrior"))
        self.assertFalse(self.items_state.get("Longsword").usable_by("Thief"))
        self.assertFalse(self.items_state.get("Longsword").usable_by("Priest"))
        self.assertFalse(self.items_state.get("Longsword").usable_by("Mage"))
        self.assertTrue(self.items_state.get("Rapier").usable_by("Warrior"))
        self.assertTrue(self.items_state.get("Rapier").usable_by("Thief"))
        self.assertFalse(self.items_state.get("Rapier").usable_by("Priest"))
        self.assertFalse(self.items_state.get("Rapier").usable_by("Mage"))
        self.assertTrue(self.items_state.get("Heavy_Mace").usable_by("Warrior"))
        self.assertFalse(self.items_state.get("Heavy_Mace").usable_by("Thief"))
        self.assertTrue(self.items_state.get("Heavy_Mace").usable_by("Priest"))
        self.assertFalse(self.items_state.get("Heavy_Mace").usable_by("Mage"))
        self.assertTrue(self.items_state.get("Staff").usable_by("Warrior"))
        self.assertFalse(self.items_state.get("Staff").usable_by("Thief"))
        self.assertFalse(self.items_state.get("Staff").usable_by("Priest"))
        self.assertTrue(self.items_state.get("Staff").usable_by("Mage"))

    def test_state_collection_interface(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        longsword = self.items_state.get("Longsword")
        self.assertTrue(self.items_state.contains(longsword.internal_name))
        self.items_state.delete("Longsword")
        with self.assertRaises(KeyError):
            self.items_state.get("Longsword")
        with self.assertRaises(KeyError):
            self.items_state.delete("Longsword")
        self.items_state.set("Longsword", longsword)
        self.assertTrue(self.items_state.contains(longsword.internal_name))
        self.assertEqual(
            set(self.items_state.keys()),
            {
                "Buckler",
                "Longsword",
                "Rapier",
                "Heavy_Mace",
                "Staff",
                "Warhammer",
                "Studded_Leather",
                "Door_Key",
                "Chest_Key",
                "Scale_Mail",
                "Magic_Sword",
                "Dagger",
                "Gold_Coin",
                "Small_Leather_Armor",
                "Short_Sword",
                "Steel_Shield",
                "Mana_Potion",
                "Magic_Wand",
                "Magic_Wand_2",
                "Health_Potion",
            },
        )
        rapier = self.items_state.get("Rapier")
        heavy_mace = self.items_state.get("Heavy_Mace")
        staff = self.items_state.get("Staff")
        warhammer = self.items_state.get("Warhammer")
        studded_leather = self.items_state.get("Studded_Leather")
        scale_mail = self.items_state.get("Scale_Mail")
        door_key = self.items_state.get("Door_Key")
        chest_key = self.items_state.get("Chest_Key")
        magic_sword = self.items_state.get("Magic_Sword")
        dagger = self.items_state.get("Dagger")
        gold_coin = self.items_state.get("Gold_Coin")
        small_leather_armor = self.items_state.get("Small_Leather_Armor")
        short_sword = self.items_state.get("Short_Sword")
        shield = self.items_state.get("Steel_Shield")
        mana_potion = self.items_state.get("Mana_Potion")
        health_potion = self.items_state.get("Health_Potion")
        magic_wand = self.items_state.get("Magic_Wand")
        magic_wand_2 = self.items_state.get("Magic_Wand_2")
        buckler = self.items_state.get("Buckler")
        state_values = tuple(self.items_state.values())
        self.assertTrue(
            all(item in state_values for item in (longsword, rapier, heavy_mace, staff))
        )
        state_items = tuple(sorted(self.items_state.items(), key=itemgetter(0)))
        items_compare_with = (
            ("Buckler", buckler),
            ("Chest_Key", chest_key),
            ("Dagger", dagger),
            ("Door_Key", door_key),
            ("Gold_Coin", gold_coin),
            ("Health_Potion", health_potion),
            ("Heavy_Mace", heavy_mace),
            ("Longsword", longsword),
            ("Magic_Sword", magic_sword),
            ("Magic_Wand", magic_wand),
            ("Magic_Wand_2", magic_wand_2),
            ("Mana_Potion", mana_potion),
            ("Rapier", rapier),
            ("Scale_Mail", scale_mail),
            ("Short_Sword", short_sword),
            ("Small_Leather_Armor", small_leather_armor),
            ("Staff", staff),
            ("Steel_Shield", shield),
            ("Studded_Leather", studded_leather),
            ("Warhammer", warhammer),
        )
        self.assertEqual(state_items, items_compare_with)
        self.assertEqual(self.items_state.size(), 20)
