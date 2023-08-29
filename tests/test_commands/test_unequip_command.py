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
from advgame.stmsg.unequip import ItemNotEquippedGSM
from advgame.stmsg.various import ItemUnequippedGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = (
    "Test_Unequip_1",
    "Test_Unequip_2",
)


class Test_Unequip_1(TestCase):
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

    def test_unequip_1(self):
        result = self.command_processor.process("unequip")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "UNEQUIP")
        self.assertEqual(
            result[0].message,
            "UNEQUIP command: bad syntax. Should be "
            + "'UNEQUIP\u00A0<armor\u00A0name>', "
            + "'UNEQUIP\u00A0<shield\u00A0name>', "
            + "'UNEQUIP\u00A0<wand\u00A0name>', or "
            + "'UNEQUIP\u00A0<weapon\u00A0name>'.",
        )

    def test_unequip_2(self):
        result = self.command_processor.process("unequip mace")
        self.assertIsInstance(result[0], ItemNotEquippedGSM)
        self.assertEqual(result[0].item_specified_title, "mace")
        self.assertEqual(result[0].message, "You're not wielding a mace.")

    def test_unequip_3(self):
        result = self.command_processor.process("unequip steel shield")
        self.assertIsInstance(result[0], ItemNotEquippedGSM)
        self.assertEqual(result[0].item_specified_title, "steel shield")
        self.assertEqual(result[0].message, "You're not carrying a steel shield.")

    def test_unequip_4(self):
        result = self.command_processor.process("unequip scale mail armor")
        self.assertIsInstance(result[0], ItemNotEquippedGSM)
        self.assertEqual(result[0].item_specified_title, "scale mail armor")
        self.assertEqual(
            result[0].message, "You're not wearing a suit of scale mail armor."
        )

    def test_unequip_5(self):
        result = self.command_processor.process("unequip magic wand")
        self.assertIsInstance(result[0], ItemNotEquippedGSM)
        self.assertEqual(result[0].item_specified_title, "magic wand")
        self.assertEqual(result[0].message, "You're not using a magic wand.")

    def test_unequip_6(self):
        result = self.command_processor.process("equip mace")
        result = self.command_processor.process("unequip mace")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "mace")
        self.assertEqual(
            result[0].message, "You're no longer wielding a mace. You now can't attack."
        )

    def test_unequip_7(self):
        result = self.command_processor.process("equip steel shield")
        result = self.command_processor.process("unequip steel shield")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "steel shield")
        self.assertRegex(
            result[0].message,
            r"^You're no longer carrying a steel shield. Your armor class is "
            + r"now \d+.$",
        )

    def test_unequip_8(self):
        result = self.command_processor.process("equip scale mail armor")
        result = self.command_processor.process("unequip scale mail armor")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "scale mail armor")
        self.assertRegex(
            result[0].message,
            r"^You're no longer wearing a suit of scale mail armor. Your "
            + r"armor class is now \d+.$",
        )


class Test_Unequip_2(TestCase):
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
        self.staff = self.command_processor.game_state.items_state.get("Staff")
        self.magic_wand = self.command_processor.game_state.items_state.get(
            "Magic_Wand"
        )
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.pick_up_item(self.staff)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)

    def test_unequip_8(self):
        result = self.command_processor.process("equip staff")
        result = self.command_processor.process("equip magic wand")
        result = self.command_processor.process("unequip magic wand")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "magic wand")
        self.assertRegex(
            result[0].message,
            r"^You're no longer using a magic wand. You're now attacking with "
            + r"your staff. Your attack bonus is now [+-]\d+ and your staff "
            + r"damage is now \d+d\d+([+-]\d+)?.$",
        )

    def test_unequip_9(self):
        result = self.command_processor.process("equip staff")
        result = self.command_processor.process("equip magic wand")
        result = self.command_processor.process("unequip staff")
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "staff")
        self.assertRegex(
            result[0].message,
            r"^You're no longer wielding a staff. You're attacking with your "
            + r"magic wand. Your attack bonus is [+-]\d+ and your magic wand "
            + r"damage is \d+d\d+([+-]\d+)?.$",
        )
