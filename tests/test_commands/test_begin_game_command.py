#!/usr/bin/python3

from unittest import TestCase

from advgame import (
    CommandProcessor,
    ContainersState,
    CreaturesState,
    DoorsState,
    GameState,
    ItemsState,
    Room,
    RoomsState,
)
from advgame.statemsgs.begin import GameBeginsGSM, NameOrClassNotSetGSM
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.various import EnteredRoomGSM, ItemEquippedGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Begin_Game",)


class Test_Begin_Game(TestCase):
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

    def test_begin_game_1(self):
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], NameOrClassNotSetGSM)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(
            result[0].message,
            "You need to set your character name and class before you begin "
            + "the game. Use SET NAME <name> to set your name and SET CLASS "
            + "<Warrior, Thief, Mage or Priest> to select your class.",
        )

    def test_begin_game_2(self):
        self.command_processor.process("set class to Warrior")
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], NameOrClassNotSetGSM)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, "Warrior")
        self.assertEqual(
            result[0].message,
            "You need to set your character name before you begin the game. "
            + "Use SET NAME <name> to set your name.",
        )

    def test_begin_game_3(self):
        self.command_processor.process("set name to Niath")
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], NameOrClassNotSetGSM)
        self.assertEqual(result[0].character_name, "Niath")
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(
            result[0].message,
            "You need to set your character class before you begin the game. "
            + "Use SET CLASS <Warrior, Thief, Mage or Priest> to select your "
            + "class.",
        )

    def test_begin_game_4(self):
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Niath")
        result = self.command_processor.process("begin game now")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "BEGIN GAME")
        self.assertEqual(
            result[0].message,
            "BEGIN GAME command: bad syntax. Should be 'BEGIN\u00A0GAME'.",
        )

    def test_begin_game_5(self):
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Niath")
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], GameBeginsGSM)
        self.assertEqual(result[0].message, "The game has begun!")
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[-1], EnteredRoomGSM)
        self.assertIsInstance(result[-1].room, Room)
        self.assertEqual(
            result[-1].message,
            "Entrance room.\nYou see a wooden chest here.\nThere is a kobold "
            + "in the room.\nYou see a mana potion and 2 health potions on "
            + "the floor.\nThere is an iron door to the north and an iron "
            + "door to the east.",
        )

    def test_begin_game_6(self):
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Niath")
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], GameBeginsGSM)
        self.assertEqual(result[0].message, "The game has begun!")
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "studded leather armor")
        self.assertEqual(result[1].item_type, "armor")
        self.assertRegex(
            result[1].message,
            r"^You're now wearing a suit of studded leather armor. Your armor "
            + r"class is now \d+.",
        )
        self.assertIsInstance(result[2], ItemEquippedGSM)
        self.assertEqual(result[2].item_title, "buckler")
        self.assertEqual(result[2].item_type, "shield")
        self.assertRegex(
            result[2].message,
            r"^You're now carrying a buckler. Your armor class is now \d+.",
        )
        self.assertIsInstance(result[3], ItemEquippedGSM)
        self.assertEqual(result[3].item_title, "longsword")
        self.assertEqual(result[3].item_type, "weapon")
        self.assertRegex(
            result[3].message,
            r"^You're now wielding a longsword. Your attack bonus is now "
            + r"[\d+-]+ and your weapon damage is now [\dd+-]+.$",
        )
        self.assertIsInstance(result[4], EnteredRoomGSM)
        self.assertIsInstance(result[4].room, Room)
        self.assertEqual(
            result[4].message,
            "Entrance room.\nYou see a wooden chest here.\nThere is a kobold "
            + "in the room.\nYou see a mana potion and 2 health potions on "
            + "the floor.\nThere is an iron door to the north and an iron "
            + "door to the east.",
        )

    def test_begin_game_7(self):
        self.command_processor.process("set class to Thief")
        self.command_processor.process("set name to Lidda")
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], GameBeginsGSM)
        self.assertEqual(result[0].message, "The game has begun!")
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "studded leather armor")
        self.assertEqual(result[1].item_type, "armor")
        self.assertRegex(
            result[1].message,
            r"^You're now wearing a suit of studded leather armor. Your armor "
            + r"class is now \d+",
        )
        self.assertIsInstance(result[2], ItemEquippedGSM)
        self.assertEqual(result[2].item_title, "rapier")
        self.assertEqual(result[2].item_type, "weapon")
        self.assertRegex(
            result[2].message,
            r"^You're now wielding a rapier. Your attack bonus is now [\d+-]+ "
            + r"and your weapon damage is now [\dd+-]+.$",
        )
        self.assertIsInstance(result[3], EnteredRoomGSM)
        self.assertIsInstance(result[3].room, Room)
        self.assertEqual(
            result[3].message,
            "Entrance room.\nYou see a wooden chest here.\nThere is a kobold "
            + "in the room.\nYou see a mana potion and 2 health potions on "
            + "the floor.\nThere is an iron door to the north and an iron "
            + "door to the east.",
        )

    def test_begin_game_8(self):
        self.command_processor.process("set class to Priest")
        self.command_processor.process("set name to Tordek")
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], GameBeginsGSM)
        self.assertEqual(result[0].message, "The game has begun!")
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "studded leather armor")
        self.assertEqual(result[1].item_type, "armor")
        self.assertRegex(
            result[1].message,
            r"^You're now wearing a suit of studded leather armor. Your armor "
            + r"class is now \d+",
        )
        self.assertIsInstance(result[2], ItemEquippedGSM)
        self.assertEqual(result[2].item_title, "buckler")
        self.assertEqual(result[2].item_type, "shield")
        self.assertRegex(
            result[2].message,
            r"^You're now carrying a buckler. Your armor class is now \d+.",
        )
        self.assertIsInstance(result[3], ItemEquippedGSM)
        self.assertEqual(result[3].item_title, "mace")
        self.assertEqual(result[3].item_type, "weapon")
        self.assertRegex(
            result[3].message,
            r"^You're now wielding a mace. Your attack bonus is now [\d+-]+ "
            + r"and your weapon damage is now [\dd+-]+.$",
        )
        self.assertIsInstance(result[4], EnteredRoomGSM)
        self.assertIsInstance(result[4].room, Room)
        self.assertEqual(
            result[4].message,
            "Entrance room.\nYou see a wooden chest here.\nThere is a kobold "
            + "in the room.\nYou see a mana potion and 2 health potions on "
            + "the floor.\nThere is an iron door to the north and an iron "
            + "door to the east.",
        )

    def test_begin_game_9(self):
        self.command_processor.process("set class to Mage")
        self.command_processor.process("set name to Mialee")
        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], GameBeginsGSM)
        self.assertEqual(result[0].message, "The game has begun!")
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], ItemEquippedGSM)
        self.assertEqual(result[1].item_title, "staff")
        self.assertEqual(result[1].item_type, "weapon")
        self.assertRegex(
            result[1].message,
            r"^You're now wielding a staff. Your attack bonus is now [\d+-]+ "
            + r"and your weapon damage is now [\dd+-]+.$",
        )
        self.assertIsInstance(result[2], EnteredRoomGSM)
        self.assertIsInstance(result[2].room, Room)
        self.assertEqual(
            result[2].message,
            "Entrance room.\nYou see a wooden chest here.\nThere is a kobold "
            + "in the room.\nYou see a mana potion and 2 health potions on "
            + "the floor.\nThere is an iron door to the north and an iron "
            + "door to the east.",
        )
