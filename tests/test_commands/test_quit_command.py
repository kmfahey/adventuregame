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


__all__ = ("Test_Quit",)

class Test_Quit(unittest.TestCase):
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

    def test_quit_1(self):
        result = self.command_processor.process("quit the game now")  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "QUIT")
        self.assertEqual(
            result[0].message, "QUIT command: bad syntax. Should be 'QUIT'."
        )

    def test_quit_2(self):
        result = self.command_processor.process("quit")  # check
        self.assertIsInstance(result[0], advg.stmsg.quit.HaveQuitTheGameGSM)
        self.assertEqual(result[0].message, "You have quit the game.")
        self.assertTrue(self.command_processor.game_state.game_has_ended)
