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
from advgame.statemsgs.lock import (
    DontPossessCorrectKeyGSM,
    ElementHasBeenLockedGSM,
    ElementIsAlreadyLockedGSM,
    ElementNotLockableGSM,
)
from advgame.statemsgs.various import DoorNotPresentGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Lock",)


class Test_Lock(TestCase):
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
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_locked = True
        self.door_title = (
            self.command_processor.game_state.rooms_state.cursor.north_door.title
        )
        self.chest = self.command_processor.game_state.rooms_state.cursor.container_here
        self.chest.is_locked = False
        self.chest_title = self.chest.title

    def test_lock_1(self):
        result = self.command_processor.process("lock")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "LOCK")
        self.assertEqual(
            result[0].message,
            "LOCK command: bad syntax. Should be 'LOCK\u00A0<door\u00A0name>' "
            + "or 'LOCK\u00A0<chest\u00A0name>'.",
        ),

    def test_lock_2(self):
        result = self.command_processor.process("lock west door")
        self.assertIsInstance(result[0], DoorNotPresentGSM)
        self.assertEqual(result[0].compass_dir, "west")
        self.assertEqual(result[0].portal_type, "door")
        self.assertEqual(result[0].message, "This room does not have a west door."),
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked
        self.door_title = (
            self.command_processor.game_state.rooms_state.cursor.north_door.title
        )

    def test_lock_3(self):
        self.door.is_locked = False
        result = self.command_processor.process(f"lock {self.door_title}")
        self.assertIsInstance(result[0], DontPossessCorrectKeyGSM)
        self.assertEqual(result[0].object_to_lock_title, self.door_title)
        self.assertEqual(result[0].key_needed, "door key")
        self.assertEqual(
            result[0].message, f"To lock the {self.door_title} you need a door key."
        )
        self.assertFalse(self.door.is_locked)

    def test_lock_4(self):
        self.door.is_locked = True
        key = self.command_processor.game_state.items_state.get("Door_Key")
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f"lock {self.door_title}")
        self.assertIsInstance(result[0], ElementIsAlreadyLockedGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"The {self.door_title} is already locked.")
        self.assertTrue(self.door.is_locked)

        self.door.is_locked = False
        result = self.command_processor.process(f"lock {self.door_title}")
        self.assertIsInstance(result[0], ElementHasBeenLockedGSM)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f"You have locked the {self.door_title}.")
        self.assertTrue(self.door.is_locked)
        result = self.command_processor.process("unlock east door")
        result = self.command_processor.process("leave via east door")
        result = self.command_processor.process("unlock north door")
        result = self.command_processor.process("leave via north door")
        result = self.command_processor.process("unlock west door")
        result = self.command_processor.process("leave via west door")
        result = self.command_processor.process("lock south door")
        self.assertIsInstance(result[0], ElementIsAlreadyLockedGSM)
        self.assertEqual(result[0].target, "south door")
        self.assertEqual(result[0].message, "The south door is already locked.")

    def test_lock_5(self):
        result = self.command_processor.process(f"lock {self.chest_title}")
        self.assertIsInstance(result[0], DontPossessCorrectKeyGSM)
        self.assertEqual(result[0].object_to_lock_title, self.chest_title)
        self.assertEqual(result[0].key_needed, "chest key")
        self.assertEqual(
            result[0].message, f"To lock the {self.chest_title} you need a chest key."
        )

    def test_lock_6(self):
        self.chest.is_locked = True
        key = self.command_processor.game_state.items_state.get("Chest_Key")
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f"lock {self.chest_title}")
        self.assertIsInstance(result[0], ElementIsAlreadyLockedGSM)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(
            result[0].message, f"The {self.chest_title} is already locked."
        )

        self.chest.is_locked = False
        result = self.command_processor.process(f"lock {self.chest_title}")
        self.assertIsInstance(result[0], ElementHasBeenLockedGSM)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f"You have locked the {self.chest_title}.")
        self.assertTrue(self.chest.is_locked)

    def test_lock_7(self):
        result = self.command_processor.process("lock north iron door")
        self.assertIsInstance(result[0], DontPossessCorrectKeyGSM)
        self.assertEqual(result[0].object_to_lock_title, "north door")
        self.assertEqual(result[0].key_needed, "door key")
        self.assertEqual(
            result[0].message, "To lock the north door you need a door key."
        )

    def test_lock_8(self):
        result = self.command_processor.process("lock mana potion")
        self.assertIsInstance(result[0], ElementNotLockableGSM)
        self.assertEqual(result[0].target_title, "mana potion")
        self.assertEqual(result[0].target_type, "potion")
        self.assertEqual(
            result[0].message,
            "You can't lock the mana potion; potions are not lockable.",
        ),

    def test_lock_9(self):
        studded_leather_armor = self.items_state.get("Studded_Leather")
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process("lock studded leather armor")
        self.assertIsInstance(result[0], ElementNotLockableGSM)
        self.assertEqual(result[0].target_title, "studded leather armor")
        self.assertEqual(result[0].target_type, "armor")
        self.assertEqual(
            result[0].message,
            "You can't lock the studded leather armor; suits of armor are not "
            + "lockable.",
        ),

    def test_lock_10(self):
        result = self.command_processor.process("lock mana potion")
        self.assertIsInstance(result[0], ElementNotLockableGSM)
        self.assertEqual(result[0].target_title, "mana potion")
        self.assertEqual(result[0].target_type, "potion")
        self.assertEqual(
            result[0].message,
            "You can't lock the mana potion; potions are not lockable.",
        ),

    def test_lock_11(self):
        result = self.command_processor.process("lock kobold")
        self.assertIsInstance(result[0], ElementNotLockableGSM)
        self.assertEqual(result[0].target_title, "kobold")
        self.assertEqual(result[0].target_type, "creature")
        self.assertEqual(
            result[0].message, "You can't lock the kobold; creatures are not lockable."
        ),

    def test_lock_12(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process("lock kobold corpse")
        self.assertIsInstance(result[0], ElementNotLockableGSM)
        self.assertEqual(result[0].target_title, "kobold corpse")
        self.assertEqual(result[0].target_type, "corpse")
        self.assertEqual(
            result[0].message,
            "You can't lock the kobold corpse; corpses are not lockable.",
        ),

    def test_lock_13(self):
        result = self.command_processor.process("pick lock on north door")
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process("lock east doorway")
        self.assertIsInstance(result[0], ElementNotLockableGSM)
        self.assertEqual(result[0].target_title, "east doorway")
        self.assertEqual(result[0].target_type, "doorway")
        self.assertEqual(
            result[0].message,
            "You can't lock the east doorway; doorways are not lockable.",
        )

    def test_lock_14(self):
        studded_leather_armor = self.items_state.get("Studded_Leather")
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process("lock studded leather armor")
        self.assertIsInstance(result[0], ElementNotLockableGSM)
        self.assertEqual(result[0].target_title, "studded leather armor")
        self.assertEqual(result[0].target_type, "armor")
        self.assertEqual(
            result[0].message,
            "You can't lock the studded leather armor; suits of armor are not "
            + "lockable.",
        ),
