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
from advgame.statemsgs.command import NotAllowedNowGSM, NotRecognizedGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Processor_Process",)


class Test_Processor_Process(TestCase):
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

    def test_command_not_recognized_in_pregame(self):
        result = self.command_processor.process("juggle")
        self.assertIsInstance(result[0], NotRecognizedGSM)
        self.assertEqual(result[0].command, "juggle")
        self.assertEqual(
            result[0].allowed_commands,
            {"begin_game", "set_name", "help", "quit", "set_class", "reroll"},
        )
        self.assertEqual(
            result[0].message,
            "Command 'juggle' not recognized. Commands allowed before game "
            + "start are BEGIN GAME, HELP, QUIT, REROLL, SET CLASS, and SET "
            + "NAME.",
        )

    def test_command_not_recognized_during_game(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.command_processor.game_state.game_has_begun = True
        result = self.command_processor.process("juggle")
        self.assertIsInstance(result[0], NotRecognizedGSM)
        self.assertEqual(result[0].command, "juggle")
        self.assertEqual(
            result[0].allowed_commands,
            {
                "attack",
                "cast_spell",
                "close",
                "drink",
                "drop",
                "equip",
                "leave",
                "inventory",
                "leave",
                "look_at",
                "lock",
                "open",
                "help",
                "pick_lock",
                "pick_up",
                "put",
                "quit",
                "status",
                "take",
                "unequip",
                "unlock",
            },
        )
        self.assertEqual(
            result[0].message,
            "Command 'juggle' not recognized. Commands allowed during the "
            + "game are ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, "
            + "INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, "
            + "PUT, QUIT, STATUS, TAKE, UNEQUIP, and UNLOCK.",
        )

    def test_command_not_allowed_in_pregame(self):
        result = self.command_processor.process("attack kobold")
        self.assertIsInstance(result[0], NotAllowedNowGSM)
        self.assertEqual(result[0].command, "attack")
        self.assertEqual(
            result[0].allowed_commands,
            {"begin_game", "help", "reroll", "set_name", "quit", "set_class"},
        )
        self.assertEqual(
            result[0].message,
            "Command 'attack' not allowed before game start. Commands allowed "
            + "before game start are BEGIN GAME, HELP, QUIT, REROLL, SET "
            + "CLASS, and SET NAME.",
        )

    def test_command_not_allowed_during_game(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.command_processor.game_state.game_has_begun = True
        result = self.command_processor.process("reroll")
        self.assertIsInstance(result[0], NotAllowedNowGSM)
        self.assertEqual(result[0].command, "reroll")
        self.assertEqual(
            result[0].allowed_commands,
            {
                "attack",
                "cast_spell",
                "close",
                "drink",
                "drop",
                "equip",
                "help",
                "leave",
                "inventory",
                "leave",
                "look_at",
                "lock",
                "open",
                "pick_lock",
                "pick_up",
                "quit",
                "put",
                "quit",
                "status",
                "take",
                "unequip",
                "unlock",
            },
        )
        self.assertEqual(
            result[0].message,
            "Command 'reroll' not allowed during the game. Commands allowed "
            + "during the game are ATTACK, CAST SPELL, CLOSE, DRINK, DROP, "
            + "EQUIP, HELP, INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, "
            + "PICK UP, PUT, QUIT, STATUS, TAKE, UNEQUIP, and UNLOCK.",
        )
