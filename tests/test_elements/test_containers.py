#!/usr/bin/python3

from unittest import TestCase

from advgame import ContainersState, CreaturesState, ItemsState, Potion
from ..context import containers_ini_config, creatures_ini_config, items_ini_config


__all__ = (
    "Test_Container",
    "Test_Creature",
)


class Test_Container(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        self.containers_state = ContainersState(
            self.items_state, **containers_ini_config.sections
        )

    def test_container(self):
        container = self.containers_state.get("Wooden_Chest_1")
        self.assertEqual(container.internal_name, "Wooden_Chest_1")
        self.assertEqual(container.title, "wooden chest")
        self.assertEqual(
            container.description,
            "This small, serviceable chest is made of wooden slats bound within an iron frame, and "
            + "features a sturdy-looking lock.",
        )
        self.assertEqual(container.is_locked, True)
        self.assertTrue(container.contains("Gold_Coin"))
        self.assertTrue(container.contains("Warhammer"))
        self.assertTrue(container.contains("Mana_Potion"))
        potion_qty, mana_potion = container.get("Mana_Potion")
        self.assertIsInstance(mana_potion, Potion)
        self.assertEqual(potion_qty, 1)
        container.delete("Mana_Potion")
        self.assertFalse(container.contains("Mana_Potion"))
        container.set("Mana_Potion", potion_qty, mana_potion)
        self.assertTrue(container.contains("Mana_Potion"))


class Test_Creature(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        self.creatures_state = CreaturesState(
            self.items_state, **creatures_ini_config.sections
        )

    def test_creature_const_1(self):
        kobold = self.creatures_state.get("Kobold_Trysk")
        self.assertEqual(kobold.character_class, "Thief")
        self.assertEqual(kobold.character_name, "Trysk")
        self.assertEqual(kobold.species, "Kobold")
        self.assertEqual(
            kobold.description,
            "This diminuitive draconic humanoid is dressed in leather armor and has a short sword at its "
            + "hip. It eyes you warily.",
        )
        self.assertEqual(kobold.character_class, "Thief")
        self.assertEqual(kobold.strength, 9)
        self.assertEqual(kobold.dexterity, 13)
        self.assertEqual(kobold.constitution, 10)
        self.assertEqual(kobold.intelligence, 10)
        self.assertEqual(kobold.wisdom, 9)
        self.assertEqual(kobold.charisma, 8)
        self.assertEqual(kobold.hit_points, 20)
        short_sword = self.items_state.get("Short_Sword")
        small_leather_armor = self.items_state.get("Small_Leather_Armor")
        self.assertEqual(kobold.weapon_equipped, short_sword)
        self.assertEqual(kobold.armor_equipped, small_leather_armor)

    def test_creature_const_2(self):
        sorcerer = self.creatures_state.get("Sorcerer_Ardren")
        self.assertEqual(sorcerer.magic_key_stat, "charisma")
        self.assertEqual(sorcerer.mana_points, 36)

    def test_convert_to_corpse(self):
        kobold = self.creatures_state.get("Kobold_Trysk")
        kobold_corpse = kobold.convert_to_corpse()
        self.assertEqual(kobold_corpse.description, kobold.description_dead)
        self.assertEqual(kobold_corpse.title, f"{kobold.title} corpse")
        self.assertEqual(kobold_corpse.internal_name, kobold.internal_name)
        for item_internal_name, (item_qty, item) in kobold.inventory.items():
            self.assertEqual(kobold_corpse.get(item_internal_name), (item_qty, item))
