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
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.open_ import (
    ElementHasBeenOpenedGSM,
    ElementIsAlreadyOpenGSM,
    ElementIsLockedGSM,
    ElementNotOpenableGSM,
)
from advgame.statemsgs.various import DoorNotPresentGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Open",)


class Test_Open(TestCase):
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
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        self.chest = self.command_processor.game_state.rooms_state.cursor.container_here
        self.chest_title = self.chest.title
        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_closed = False
        self.door_title = self.door.title

    def test_open_1(self):
        result = self.command_processor.process("open")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "OPEN")
        self.assertEqual(
            result[0].message,
            "OPEN command: bad syntax. Should be 'OPEN\u00A0<door\u00A0name>' "
            + "or 'OPEN\u00A0<chest\u00A0name>'.",
        ),

    def test_open_2(self):
        self.chest.is_closed = True
        self.chest.is_locked = True
        result = self.command_processor.process(f"open {self.chest_title}")
        self.assertIsInstance(result[0], ElementIsLockedGSM)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f"The {self.chest_title} is locked.")

    def test_open_3(self):
        self.chest.is_locked = False
        self.chest.is_closed = False
        self.chest_title = self.chest.title
        result = self.command_processor.process(f"open {self.chest_title}")
        self.assertIsInstance(result[0], ElementIsAlreadyOpenGSM)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f"The {self.chest_title} is already open.")
        self.assertFalse(self.chest.is_closed)

        self.chest.is_closed = True
        result = self.command_processor.process(f"open {self.chest_title}")
        self.assertIsInstance(result[0], ElementHasBeenOpenedGSM)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f"You have opened the {self.chest_title}.")
        self.assertFalse(self.chest.is_closed)

    def test_open_4(self):
        result = self.command_processor.process("open west door")
        self.assertIsInstance(result[0], DoorNotPresentGSM)
        self.assertEqual(result[0].compass_dir, "west")
        self.assertEqual(result[0].portal_type, "door")
        self.assertEqual(result[0].message, "This room does not have a west door."),

    def test_open_5(self):
        result = self.command_processor.process(f"open {self.door_title}")
        self.assertIsInstance(result[0], ElementIsAlreadyOpenGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"The {self.door_title} is already open.")
        self.assertFalse(self.door.is_closed)

    def test_open_6(self):
        self.door.is_closed = True
        result = self.command_processor.process(f"open {self.door_title}")
        self.assertIsInstance(result[0], ElementHasBeenOpenedGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"You have opened the {self.door_title}.")
        self.assertFalse(self.door.is_closed)

        result = self.command_processor.process(f"leave using {self.door_title}")
        result = self.command_processor.process("open south door")
        self.assertIsInstance(result[0], ElementIsAlreadyOpenGSM)
        self.assertEqual(result[0].target, "south door")
        self.assertEqual(result[0].message, "The south door is already open.")
        self.assertFalse(self.door.is_closed)

    def test_open_7(self):
        self.door.is_closed = True
        self.door.is_locked = True
        result = self.command_processor.process(f"open {self.door_title}")
        self.assertIsInstance(result[0], ElementIsLockedGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"The {self.door_title} is locked.")
        self.assertTrue(self.door.is_closed)

    def test_open_8(self):
        self.door.is_closed = True
        self.door.is_locked = True
        alternate_title = self.door.door_type.replace("_", " ")
        result = self.command_processor.process(f"open north {alternate_title}")
        self.assertIsInstance(result[0], ElementIsLockedGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"The {self.door_title} is locked.")
        self.assertTrue(self.door.is_closed)

    def test_open_9(self):
        result = self.command_processor.process("open north iron door")
        self.assertIsInstance(result[0], ElementIsAlreadyOpenGSM)
        self.assertEqual(result[0].target, "north door")
        self.assertEqual(result[0].message, "The north door is already open."),

    def test_open_10(self):
        result = self.command_processor.process("open mana potion")
        self.assertIsInstance(result[0], ElementNotOpenableGSM)
        self.assertEqual(result[0].target_title, "mana potion")
        self.assertEqual(result[0].target_type, "potion")
        self.assertEqual(
            result[0].message,
            "You can't open the mana potion; potions are not openable.",
        ),

    def test_open_11(self):
        result = self.command_processor.process("open kobold")
        self.assertIsInstance(result[0], ElementNotOpenableGSM)
        self.assertEqual(result[0].target_title, "kobold")
        self.assertEqual(result[0].target_type, "creature")
        self.assertEqual(
            result[0].message, "You can't open the kobold; creatures are not openable."
        ),

    def test_open_12(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process("open kobold corpse")
        self.assertIsInstance(result[0], ElementNotOpenableGSM)
        self.assertEqual(result[0].target_title, "kobold corpse")
        self.assertEqual(result[0].target_type, "corpse")
        self.assertEqual(
            result[0].message,
            "You can't open the kobold corpse; corpses are not openable.",
        ),

    def test_open_13(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process("open east doorway")
        self.assertIsInstance(result[0], ElementNotOpenableGSM)
        self.assertEqual(result[0].target_title, "east doorway")
        self.assertEqual(result[0].target_type, "doorway")
        self.assertEqual(
            result[0].message,
            "You can't open the east doorway; doorways are not openable.",
        )

    def test_open_14(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        studded_leather_armor = self.items_state.get("Studded_Leather")
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process("open studded leather armor")
        self.assertIsInstance(result[0], ElementNotOpenableGSM)
        self.assertEqual(result[0].target_title, "studded leather armor")
        self.assertEqual(result[0].target_type, "armor")
        self.assertEqual(
            result[0].message,
            "You can't open the studded leather armor; suits of armor are not "
            + "openable.",
        ),
