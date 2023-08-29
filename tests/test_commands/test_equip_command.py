#!/usr/bin/python3

from unittest import TestCase

from advgame import (
    CommandProcessor,
    ContainersState,
    CreaturesState,
    DoorsState,
    GameState,
    ItemsState,
    RoomsState,
)
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.equip import ClassCantUseItemGSM, NoSuchItemInInventoryGSM
from advgame.stmsg.various import ItemEquippedGSM, ItemUnequippedGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = (
    "Test_Equip_1",
    "Test_Equip_2",
)


class Test_Equip_1(TestCase):
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
        self.command_processor = CommandProcessor(self.game_state)
        self.longsword = self.command_processor.game_state.items_state.get("Longsword")
        self.scale_mail = self.command_processor.game_state.items_state.get(
            "Scale_Mail"
        )
        self.shield = self.command_processor.game_state.items_state.get("Steel_Shield")
        self.magic_wand = self.command_processor.game_state.items_state.get(
            "Magic_Wand"
        )
        self.magic_wand_2 = self.command_processor.game_state.items_state.get(
            "Magic_Wand_2"
        )
        self.staff = self.command_processor.game_state.items_state.get("Staff")
        self.command_processor.game_state.character_name = "Arliss"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.pick_up_item(self.longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.staff)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand_2)

    def test_equip_1(self):
        self.command_processor.game_state.character_name = "Arliss"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True

        result = self.command_processor.process("equip")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "EQUIP")
        self.assertEqual(
            result[0].message,
            "EQUIP command: bad syntax. Should be "
            + "'EQUIP\u00A0<armor\u00A0name>', "
            + "'EQUIP\u00A0<shield\u00A0name>', "
            + "'EQUIP\u00A0<wand\u00A0name>', or "
            + "'EQUIP\u00A0<weapon\u00A0name>'.",
        )

        result = self.command_processor.process("drop longsword")
        result = self.command_processor.process("equip longsword")
        self.assertIsInstance(result[0], NoSuchItemInInventoryGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertEqual(
            result[0].message, "You don't have a longsword in your inventory."
        )

    def test_equip_2(self):
        result = self.command_processor.process("equip longsword")
        self.assertIsInstance(result[0], ClassCantUseItemGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertEqual(result[0].item_type, "weapon")
        self.assertEqual(result[0].message, "Mages can't wield longswords.")

    def test_equip_3(self):
        result = self.command_processor.process("equip scale mail armor")
        self.assertIsInstance(result[0], ClassCantUseItemGSM)
        self.assertEqual(result[0].item_title, "scale mail armor")
        self.assertEqual(result[0].item_type, "armor")
        self.assertEqual(result[0].message, "Mages can't wear scale mail armor.")

    def test_equip_4(self):
        result = self.command_processor.process("equip steel shield")
        self.assertIsInstance(result[0], ClassCantUseItemGSM)
        self.assertEqual(result[0].item_title, "steel shield")
        self.assertEqual(result[0].item_type, "shield")
        self.assertEqual(result[0].message, "Mages can't carry steel shields.")

    def test_equip_5(self):
        result = self.command_processor.process("equip magic wand")
        self.assertIsInstance(result[0], ItemEquippedGSM)
        self.assertEqual(result[0].item_title, "magic wand")
        self.assertEqual(result[0].item_type, "wand")
        self.assertRegex(
            result[0].message,
            r"^You're now using a magic wand. Your attack bonus is now "
            + r"[\d+-]+ and your wand damage is now [\dd+-]+.$",
        )

    def test_equip_6(self):
        self.command_processor.process("equip magic wand")
        result = self.command_processor.process("equip magic wand 2")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "magic wand")
        self.assertEqual(result[0].item_type, "wand")
        self.assertEqual(
            result[0].message,
            "You're no longer using a magic wand. You now can't attack.",
        )
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "magic wand 2")
        self.assertEqual(result[1].item_type, "wand")
        self.assertRegex(
            result[1].message,
            r"^You're now using a magic wand 2. Your attack bonus is now "
            + r"[\d+-]+ and your wand damage is now [\dd+-]+.$",
        )

    def test_equip_7(self):
        self.command_processor.process("equip staff")
        result = self.command_processor.process("equip magic wand")
        result = self.command_processor.process("equip magic wand 2")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "magic wand")
        self.assertEqual(result[0].item_type, "wand")
        self.assertRegex(
            result[0].message,
            r"You're no longer using a magic wand. You're attacking with your "
            + r"staff. Your attack bonus is [+-]\d+ and your staff damage is "
            + r"\d+d\d+([+-]\d+)?.",
        )
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "magic wand 2")
        self.assertEqual(result[1].item_type, "wand")
        self.assertRegex(
            result[1].message,
            r"^You're now using a magic wand 2. Your attack bonus is now "
            + r"[\d+-]+ and your wand damage is now [\dd+-]+.$",
        )


class Test_Equip_2(TestCase):
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
        self.command_processor = CommandProcessor(self.game_state)
        self.buckler = self.command_processor.game_state.items_state.get("Buckler")
        self.longsword = self.command_processor.game_state.items_state.get("Longsword")
        self.mace = self.command_processor.game_state.items_state.get("Heavy_Mace")
        self.magic_wand_2 = self.command_processor.game_state.items_state.get(
            "Magic_Wand_2"
        )
        self.magic_wand = self.command_processor.game_state.items_state.get(
            "Magic_Wand"
        )
        self.scale_mail = self.command_processor.game_state.items_state.get(
            "Scale_Mail"
        )
        self.shield = self.command_processor.game_state.items_state.get("Steel_Shield")
        self.studded_leather = self.command_processor.game_state.items_state.get(
            "Studded_Leather"
        )
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.pick_up_item(self.mace)
        self.command_processor.game_state.character.pick_up_item(self.studded_leather)
        self.command_processor.game_state.character.pick_up_item(self.buckler)
        self.command_processor.game_state.character.pick_up_item(self.longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)

    def test_equip_2(self):
        result = self.command_processor.process("equip longsword")
        self.assertIsInstance(result[0], ItemEquippedGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertRegex(
            result[0].message,
            r"^You're now wielding a longsword. Your attack bonus is now "
            + r"[\d+-]+ and your weapon damage is now [\dd+-]+.$",
        )
        result = self.command_processor.process("equip mace")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertEqual(result[0].item_type, "weapon")
        self.assertEqual(
            result[0].message,
            "You're no longer wielding a longsword. You now can't attack.",
        )
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "mace")
        self.assertEqual(result[1].item_type, "weapon")
        self.assertRegex(
            result[1].message,
            r"^You're now wielding a mace. Your attack bonus is now [\d+-]+ "
            + r"and your weapon damage is now [\dd+-]+.$",
        )

    def test_equip_3(self):
        result = self.command_processor.process("equip scale mail armor")
        self.assertIsInstance(result[0], ItemEquippedGSM)
        self.assertEqual(result[0].item_title, "scale mail armor")
        self.assertRegex(
            result[0].message,
            r"^You're now wearing a suit of scale mail armor. Your armor "
            + r"class is now \d+.$",
        )
        result = self.command_processor.process("equip studded leather armor")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "scale mail armor")
        self.assertEqual(result[0].item_type, "armor")
        self.assertRegex(
            result[0].message,
            r"^You're no longer wearing a suit of scale mail armor. Your "
            + r"armor class is now \d+.$",
        )
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "studded leather armor")
        self.assertEqual(result[1].item_type, "armor")
        self.assertRegex(
            result[1].message,
            r"^You're now wearing a suit of studded leather armor. Your armor "
            + r"class is now \d+.$",
        )

    def test_equip_4(self):
        result = self.command_processor.process("equip steel shield")
        self.assertIsInstance(result[0], ItemEquippedGSM)
        self.assertEqual(result[0].item_title, "steel shield")
        self.assertRegex(
            result[0].message,
            r"^You're now carrying a steel shield. Your armor class is now \d+.$",
        )
        result = self.command_processor.process("equip buckler")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "steel shield")
        self.assertEqual(result[0].item_type, "shield")
        self.assertRegex(
            result[0].message,
            r"^You're no longer carrying a steel shield. Your armor class is "
            + r"now \d+.$",
        )
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "buckler")
        self.assertEqual(result[1].item_type, "shield")
        self.assertRegex(
            result[1].message,
            r"^You're now carrying a buckler. Your armor class is now [\d+-]+.$",
        )

    def test_equip_5(self):
        result = self.command_processor.process("equip magic wand")
        self.assertIsInstance(result[0], ClassCantUseItemGSM)
        self.assertEqual(result[0].item_title, "magic wand")
        self.assertEqual(result[0].message, "Warriors can't use magic wands.")
