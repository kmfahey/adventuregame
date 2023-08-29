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


__all__ = ("Test_Close",)

class Test_Close(unittest.TestCase):
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
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.chest = self.command_processor.game_state.rooms_state.cursor.container_here
        self.chest.is_closed = True
        self.chest.is_locked = False
        self.chest_title = self.chest.title
        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_closed = True
        self.door_title = self.door.title

    def test_close_1(self):
        result = self.command_processor.process("close")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "CLOSE")
        self.assertEqual(
            result[0].message,
            "CLOSE command: bad syntax. Should be "
            + "'CLOSE\u00A0<door\u00A0name>' or 'CLOSE\u00A0<chest\u00A0name>'.",
        ),

    def test_close_2(self):
        result = self.command_processor.process(f"close {self.chest_title}")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosedGSM)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(
            result[0].message, f"The {self.chest_title} is already closed."
        )
        self.assertTrue(self.chest.is_closed)

    def test_close_3(self):
        self.chest.is_closed = False
        result = self.command_processor.process(f"close {self.chest_title}")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementHasBeenClosedGSM)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f"You have closed the {self.chest_title}.")
        self.assertTrue(self.chest.is_closed)

    def test_close_5(self):
        result = self.command_processor.process("close west door")
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresentGSM)
        self.assertEqual(result[0].compass_dir, "west")
        self.assertEqual(result[0].portal_type, "door")
        self.assertEqual(result[0].message, "This room does not have a west door."),

    def test_close_6(self):
        result = self.command_processor.process(f"close {self.door_title}")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosedGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"The {self.door_title} is already closed.")
        self.assertTrue(self.door.is_closed)

    def test_close_7(self):
        self.door.is_closed = False
        result = self.command_processor.process(f"close {self.door_title}")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementHasBeenClosedGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"You have closed the {self.door_title}.")
        self.assertTrue(self.door.is_closed)
        result = self.command_processor.process("pick lock on east door")
        result = self.command_processor.process("leave via east door")
        result = self.command_processor.process("pick lock on north door")
        result = self.command_processor.process("leave via north door")
        result = self.command_processor.process("pick lock on west door")
        result = self.command_processor.process("leave via west door")
        result = self.command_processor.process("close south door")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosedGSM)
        self.assertEqual(result[0].target, "south door")
        self.assertEqual(result[0].message, "The south door is already closed.")
        self.assertTrue(self.door.is_closed)

    def test_close_8(self):
        result = self.command_processor.process("close north iron door")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosedGSM)
        self.assertEqual(result[0].target, "north door")
        self.assertEqual(result[0].message, "The north door is already closed."),

    def test_close_9(self):
        result = self.command_processor.process("close mana potion")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseableGSM)
        self.assertEqual(result[0].target_title, "mana potion")
        self.assertEqual(result[0].target_type, "potion")
        self.assertEqual(
            result[0].message,
            "You can't close the mana potion; potions are not closeable.",
        ),

    def test_close_10(self):
        result = self.command_processor.process("close kobold")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseableGSM)
        self.assertEqual(result[0].target_title, "kobold")
        self.assertEqual(result[0].target_type, "creature")
        self.assertEqual(
            result[0].message,
            "You can't close the kobold; creatures are not closeable.",
        ),

    def test_close_11(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process("close kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseableGSM)
        self.assertEqual(result[0].target_title, "kobold corpse")
        self.assertEqual(result[0].target_type, "corpse")
        self.assertEqual(
            result[0].message,
            "You can't close the kobold corpse; corpses are not closeable.",
        ),

    def test_close_12(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process("close east doorway")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseableGSM)
        self.assertEqual(result[0].target_title, "east doorway")
        self.assertEqual(result[0].target_type, "doorway")
        self.assertEqual(
            result[0].message,
            "You can't close the east doorway; doorways are not closeable.",
        )

    def test_open_13(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        studded_leather_armor = self.items_state.get("Studded_Leather")
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process("close studded leather armor")
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseableGSM)
        self.assertEqual(result[0].target_title, "studded leather armor")
        self.assertEqual(result[0].target_type, "armor")
        self.assertEqual(
            result[0].message,
            "You can't close the studded leather armor; suits of armor are "
            + "not closeable.",
        ),
