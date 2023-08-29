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
from advgame.stmsg.command import BadSyntaxGSM, ClassRestrictedGSM
from advgame.stmsg.pklock import (
    ElementNotLockpickableGSM,
    TargetHasBeenUnlockedGSM,
    TargetNotFoundGSM,
    TargetNotLockedGSM,
)
from advgame.stmsg.various import DoorNotPresentGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Pick_Lock",)


class Test_Pick_Lock(TestCase):
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

    def test_pick_lock_1(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("pick lock on wooden chest")
        self.assertIsInstance(result[0], ClassRestrictedGSM)
        self.assertEqual(result[0].command, "PICK LOCK")
        self.assertEqual(result[0].classes, ("thief",))
        self.assertEqual(
            result[0].message, "Only thieves can use the PICK LOCK command."
        )

    def test_pick_lock_2(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("pick lock")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("pick lock on")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("pick lock on the")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("pick lock wooden chest")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "PICK LOCK")
        self.assertEqual(
            result[0].message,
            "PICK LOCK command: bad syntax. Should be "
            + "'PICK\u00A0LOCK\u00A0ON\u00A0[THE]\u00A0<chest\u00A0name>' or "
            + "'PICK\u00A0LOCK\u00A0ON\u00A0[THE]\u00A0<door\u00A0name>'.",
        )

    def test_pick_lock_3(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("pick lock on west door")
        self.assertIsInstance(result[0], DoorNotPresentGSM)
        self.assertEqual(result[0].compass_dir, "west")
        self.assertEqual(result[0].portal_type, "door")
        self.assertEqual(result[0].message, "This room does not have a west door.")

    def test_pick_lock_4(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("pick lock on north iron door")
        self.assertIsInstance(result[0], TargetNotLockedGSM)
        self.assertEqual(result[0].target_title, "north iron door")
        self.assertEqual(result[0].message, "The north iron door is not locked.")

    def test_pick_lock_5(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("pick lock on north door")
        self.assertIsInstance(result[0], TargetNotLockedGSM)
        self.assertEqual(result[0].target_title, "north door")
        self.assertEqual(result[0].message, "The north door is not locked.")

    def test_pick_lock_6(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process("pick lock on wooden chest")
        self.assertIsInstance(result[0], TargetNotFoundGSM)
        self.assertEqual(result[0].target_title, "wooden chest")
        self.assertEqual(result[0].message, "This room has no wooden chest.")

    def test_pick_lock_7(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here.is_locked = (
            False
        )
        result = self.command_processor.process("pick lock on wooden chest")
        self.assertIsInstance(result[0], TargetNotLockedGSM)
        self.assertEqual(result[0].target_title, "wooden chest")
        self.assertEqual(result[0].message, "The wooden chest is not locked.")
        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.container_here.is_locked
        )

    def test_pick_lock_8(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.assertTrue(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_locked
        )
        result = self.command_processor.process("pick lock on east door")
        self.assertIsInstance(result[0], TargetHasBeenUnlockedGSM)
        self.assertEqual(result[0].target_title, "east door")
        self.assertEqual(result[0].message, "You have unlocked the east door.")
        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_locked
        )

    def test_pick_lock_9(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.assertTrue(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_locked
        )
        result = self.command_processor.process("pick lock on east door")
        self.assertIsInstance(result[0], TargetHasBeenUnlockedGSM)
        self.assertEqual(result[0].target_title, "east door")
        self.assertEqual(result[0].message, "You have unlocked the east door.")
        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_locked
        )
        result = self.command_processor.process("leave via east door")
        result = self.command_processor.process("pick lock on west door")
        self.assertIsInstance(result[0], TargetNotLockedGSM)
        self.assertEqual(result[0].target_title, "west door")
        self.assertEqual(result[0].message, "The west door is not locked.")

    def test_pick_lock_10(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.assertTrue(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_locked
        )
        result = self.command_processor.process("pick lock on east door")
        self.assertIsInstance(result[0], TargetHasBeenUnlockedGSM)
        self.assertEqual(result[0].target_title, "east door")
        self.assertEqual(result[0].message, "You have unlocked the east door.")
        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_locked
        )

    def test_pick_lock_11(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.assertTrue(
            self.command_processor.game_state.rooms_state.cursor.container_here.is_locked
        )
        result = self.command_processor.process("pick lock on wooden chest")
        self.assertIsInstance(result[0], TargetHasBeenUnlockedGSM)
        self.assertEqual(result[0].target_title, "wooden chest")
        self.assertEqual(result[0].message, "You have unlocked the wooden chest.")
        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.container_here.is_locked
        )

    def test_pick_lock_12(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("pick lock on mana potion")
        self.assertIsInstance(result[0], ElementNotLockpickableGSM)
        self.assertEqual(result[0].target_title, "mana potion")
        self.assertEqual(result[0].target_type, "potion")
        self.assertEqual(
            result[0].message,
            "You can't pick a lock on the mana potion; potions are not unlockable.",
        ),

    def test_pick_lock_13(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("pick lock on kobold")
        self.assertIsInstance(result[0], ElementNotLockpickableGSM)
        self.assertEqual(result[0].target_title, "kobold")
        self.assertEqual(result[0].target_type, "creature")
        self.assertEqual(
            result[0].message,
            "You can't pick a lock on the kobold; creatures are not unlockable.",
        ),

    def test_pick_lock_14(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process("pick lock on the kobold corpse")
        self.assertIsInstance(result[0], ElementNotLockpickableGSM)
        self.assertEqual(result[0].target_title, "kobold corpse")
        self.assertEqual(result[0].target_type, "corpse")
        self.assertEqual(
            result[0].message,
            "You can't pick a lock on the kobold corpse; corpses are not "
            + "unlockable.",
        ),

    def test_pick_lock_15(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process("pick lock on east doorway")
        self.assertIsInstance(result[0], ElementNotLockpickableGSM)
        self.assertEqual(result[0].target_title, "east doorway")
        self.assertEqual(result[0].target_type, "doorway")
        self.assertEqual(
            result[0].message,
            "You can't pick a lock on the east doorway; doorways are not "
            + "unlockable.",
        )

    def test_pick_lock_16(self):
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        studded_leather_armor = self.items_state.get("Studded_Leather")
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process("pick lock on studded leather armor")
        self.assertIsInstance(result[0], ElementNotLockpickableGSM)
        self.assertEqual(result[0].target_title, "studded leather armor")
        self.assertEqual(result[0].target_type, "armor")
        self.assertEqual(
            result[0].message,
            "You can't pick a lock on the studded leather armor; suits of "
            + "armor are not unlockable.",
        ),
