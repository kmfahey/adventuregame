#!/usr/bin/python3

import unittest

import advgame as advg

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Set_Name_Vs_Set_Class_Vs_Reroll_Vs_Begin_Game",)

class Test_Set_Name_Vs_Set_Class_Vs_Reroll_Vs_Begin_Game(unittest.TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(
            self.items_state, **containers_ini_config.sections
        )
        self.creatures_state = advg.CreaturesState(
            self.items_state, **creatures_ini_config.sections
        )
        self.rooms_state = advg.RoomsState(
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
            **rooms_ini_config.sections,
        )
        self.game_state = advg.GameState(
            self.rooms_state,
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
        )
        self.command_processor = advg.CommandProcessor(self.game_state)

    def test_reroll_1(self):
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("reroll stats")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "REROLL")
        self.assertEqual(
            result[0].message, "REROLL command: bad syntax. Should be 'REROLL'."
        )

    def test_begin_game_1(self):
        result = self.command_processor.process("reroll")
        self.assertIsInstance(result[0], advg.stmsg.reroll.NameOrClassNotSetGSM)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(
            result[0].message,
            "Your character's stats haven't been rolled yet, so there's "
            + "nothing to reroll. Use SET NAME <name> to set your name and "
            + "SET CLASS <Warrior, Thief, Mage or Priest> to select your "
            + "class.",
        )

    def test_begin_game_2(self):
        self.command_processor.process("set class to Warrior")
        result = self.command_processor.process("reroll")
        self.assertIsInstance(result[0], advg.stmsg.reroll.NameOrClassNotSetGSM)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, "Warrior")
        self.assertEqual(
            result[0].message,
            "Your character's stats haven't been rolled yet, so there's "
            + "nothing to reroll. Use SET NAME <name> to set your name.",
        )

    def test_begin_game_3(self):
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("reroll")
        self.assertIsInstance(result[0], advg.stmsg.reroll.NameOrClassNotSetGSM)
        self.assertEqual(result[0].character_name, "Kerne")
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(
            result[0].message,
            "Your character's stats haven't been rolled yet, so there's "
            + "nothing to reroll. Use SET CLASS <Warrior, Thief, Mage or "
            + "Priest> to select your class.",
        )

    def test_begin_game_4(self):
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("reroll my stats")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "REROLL")
        self.assertEqual(
            result[0].message, "REROLL command: bad syntax. Should be 'REROLL'."
        )

    def test_begin_game_5(self):
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("reroll")
        self.assertIsInstance(result[0], advg.stmsg.various.DisplayRolledStatsGSM)

    def test_set_name_vs_set_class_1(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        result = self.command_processor.process("set class")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        result = self.command_processor.process("set class dread necromancer")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "SET CLASS")
        self.assertEqual(
            result[0].message,
            "SET CLASS command: bad syntax. Should be "
            + "'SET\u00A0CLASS\u00A0[TO]\u00A0<Warrior,\u00A0Thief,\u00A0Mage\u00A0or\u00A0Priest>'.",
        )

        result = self.command_processor.process("set class to Warrior")
        self.assertIsInstance(result[0], advg.stmsg.setcls.ClassSetGSM)
        self.assertEqual(result[0].class_str, "Warrior")
        self.assertEqual(result[0].message, "Your class, Warrior, has been set.")

        result = self.command_processor.process("set name")  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "SET NAME")
        self.assertEqual(
            result[0].message,
            "SET NAME command: bad syntax. Should be "
            + "'SET\u00A0NAME\u00A0[TO]\u00A0<character\u00A0name>'.",
        )

        result = self.command_processor.process("set name to Kerne")
        self.assertIsInstance(result[0], advg.stmsg.setname.NameSetGSM)
        self.assertEqual(result[0].name, "Kerne")
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")
        self.assertIsInstance(result[1], advg.stmsg.various.DisplayRolledStatsGSM)
        self.assertIsInstance(result[1].strength, int)
        self.assertTrue(3 <= result[1].strength <= 18)
        self.assertIsInstance(result[1].dexterity, int)
        self.assertTrue(3 <= result[1].dexterity <= 18)
        self.assertIsInstance(result[1].constitution, int)
        self.assertTrue(3 <= result[1].constitution <= 18)
        self.assertIsInstance(result[1].intelligence, int)
        self.assertTrue(3 <= result[1].intelligence <= 18)
        self.assertIsInstance(result[1].wisdom, int)
        self.assertTrue(3 <= result[1].wisdom <= 18)
        self.assertIsInstance(result[1].charisma, int)
        self.assertTrue(3 <= result[1].charisma <= 18)
        self.assertEqual(
            result[1].message,
            f"Your ability scores are Strength\u00A0{result[1].strength}, "
            + f"Dexterity\u00A0{result[1].dexterity}, "
            + f"Constitution\u00A0{result[1].constitution}, "
            + f"Intelligence\u00A0{result[1].intelligence}, "
            + f"Wisdom\u00A0{result[1].wisdom}, "
            + f"Charisma\u00A0{result[1].charisma}.\n\nWould you like to "
            + "reroll or begin the game?",
        )
        first_roll = second_roll = {
            "strength": result[1].strength,
            "dexterity": result[1].dexterity,
            "constitution": result[1].constitution,
            "intelligence": result[1].intelligence,
            "wisdom": result[1].wisdom,
            "charisma": result[1].charisma,
        }
        while first_roll == second_roll:
            result = self.command_processor.process("reroll")
            second_roll = {
                "strength": result[0].strength,
                "dexterity": result[0].dexterity,
                "constitution": result[0].constitution,
                "intelligence": result[0].intelligence,
                "wisdom": result[0].wisdom,
                "charisma": result[0].charisma,
            }
        self.assertIsInstance(result[0], advg.stmsg.various.DisplayRolledStatsGSM)
        self.assertNotEqual(first_roll, second_roll)

        result = self.command_processor.process("begin game")
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBeginsGSM)
        self.assertEqual(result[0].message, "The game has begun!")
        self.assertTrue(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_2(self):
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("begin")
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBeginsGSM)
        self.assertEqual(result[0].message, "The game has begun!")
        self.assertTrue(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_3(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("begin the game now")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "BEGIN GAME")
        self.assertEqual(
            result[0].message,
            "BEGIN GAME command: bad syntax. Should be 'BEGIN\u00A0GAME'.",
        )
        self.assertFalse(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_4(self):
        result = self.command_processor.process("set name to Kerne0")
        self.assertIsInstance(result[0], advg.stmsg.setname.InvalidPartGSM)
        self.assertEqual(result[0].name_part, "Kerne0")
        self.assertEqual(
            result[0].message,
            "The name Kerne0 is invalid; must be a capital letter followed by "
            + "lowercase letters.",
        )

        result = self.command_processor.process("set name to Kerne MacDonald0 Fahey1")
        self.assertIsInstance(result[0], advg.stmsg.setname.InvalidPartGSM)
        self.assertEqual(result[0].name_part, "MacDonald0")
        self.assertEqual(
            result[0].message,
            "The name MacDonald0 is invalid; must be a capital letter "
            + "followed by lowercase letters.",
        )
        self.assertIsInstance(result[1], advg.stmsg.setname.InvalidPartGSM)
        self.assertEqual(result[1].name_part, "Fahey1")
        self.assertEqual(
            result[1].message,
            "The name Fahey1 is invalid; must be a capital letter followed by "
            + "lowercase letters.",
        )

        result = self.command_processor.process("set name to Kerne")
        self.assertIsInstance(result[0], advg.stmsg.setname.NameSetGSM)
        self.assertEqual(result[0].name, "Kerne")
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")

        result = self.command_processor.process("set class to Ranger")
        self.assertIsInstance(result[0], advg.stmsg.setcls.InvalidClassGSM)
        self.assertEqual(result[0].bad_class, "Ranger")
        self.assertEqual(
            result[0].message,
            "'Ranger' is not a valid class choice. Please choose Warrior, "
            + "Thief, Mage, or Priest.",
        )

        result = self.command_processor.process("set class to Warrior")
        self.assertIsInstance(result[0], advg.stmsg.setcls.ClassSetGSM)
        self.assertEqual(result[0].class_str, "Warrior")
        self.assertEqual(result[0].message, "Your class, Warrior, has been set.")
        self.assertIsInstance(result[1], advg.stmsg.various.DisplayRolledStatsGSM)
        self.assertIsInstance(result[1].strength, int)
        self.assertTrue(3 <= result[1].strength <= 18)
        self.assertIsInstance(result[1].dexterity, int)
        self.assertTrue(3 <= result[1].dexterity <= 18)
        self.assertIsInstance(result[1].constitution, int)
        self.assertTrue(3 <= result[1].constitution <= 18)
        self.assertIsInstance(result[1].intelligence, int)
        self.assertTrue(3 <= result[1].intelligence <= 18)
        self.assertIsInstance(result[1].wisdom, int)
        self.assertTrue(3 <= result[1].wisdom <= 18)
        self.assertIsInstance(result[1].charisma, int)
        self.assertTrue(3 <= result[1].charisma <= 18)

    def test_set_name_vs_set_class_vs_begin_game(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("begin the game now")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "BEGIN GAME")
        self.assertEqual(
            result[0].message,
            "BEGIN GAME command: bad syntax. Should be 'BEGIN\u00A0GAME'.",
        )
        self.assertFalse(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_vs_reroll(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("set name to Kerne")
        result = self.command_processor.process("reroll please")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "REROLL")
        self.assertEqual(
            result[0].message, "REROLL command: bad syntax. Should be 'REROLL'."
        )
        self.assertFalse(self.command_processor.game_state.game_has_begun)
