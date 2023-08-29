#!/usr/bin/python3

from operator import itemgetter
from unittest import TestCase

from advgame import Door, DoorsState, Doorway, IronDoor, WoodenDoor

from ..context import doors_ini_config


__all__ = ("Test_Door_and_DoorsState",)


class Test_Door_and_DoorsState(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.doors_state = DoorsState(**doors_ini_config.sections)

    def test_doors_state(self):
        doors_state_keys = self.doors_state.keys()
        self.assertEqual(
            doors_state_keys,
            [
                ("Room_1,1", "Room_1,2"),
                ("Room_1,1", "Room_2,1"),
                ("Room_1,2", "Room_2,2"),
                ("Room_2,1", "Room_2,2"),
                ("Room_2,2", "Exit"),
            ],
        )
        doors_state_values = self.doors_state.values()
        self.assertTrue(
            all(
                isinstance(door, Door)
                and isinstance(door, (WoodenDoor, IronDoor, Doorway))
                for door in doors_state_values
            )
        )
        doors_state_items = self.doors_state.items()
        self.assertEqual(
            list(map(itemgetter(0, 1), doors_state_items)),
            [
                ("Room_1,1", "Room_1,2"),
                ("Room_1,1", "Room_2,1"),
                ("Room_1,2", "Room_2,2"),
                ("Room_2,1", "Room_2,2"),
                ("Room_2,2", "Exit"),
            ],
        )
        self.assertTrue(
            all(
                isinstance(door, Door)
                and isinstance(door, (WoodenDoor, IronDoor, Doorway))
                for door in doors_state_values
            )
        )
        self.assertEqual(self.doors_state.size(), 5)
        self.assertTrue(self.doors_state.contains("Room_2,1", "Room_2,2"))
        door = self.doors_state.get("Room_1,2", "Room_2,2")
        self.assertEqual(door.title, "doorway")
        self.assertEqual(
            door.description,
            "This open doorway is outlined by a stone arch set into the wall.",
        )
        self.assertEqual(door.door_type, "doorway")
        self.assertFalse(door.is_locked, False)
        self.assertFalse(door.is_closed, False)
        self.assertFalse(door.closeable, False)
        self.doors_state.delete("Room_1,2", "Room_2,2")
        self.assertFalse(self.doors_state.contains("Room_1,2", "Room_2,2"))
        self.doors_state.set("Room_1,2", "Room_2,2", door)
        self.assertTrue(self.doors_state.contains("Room_1,2", "Room_2,2"))

    def test_doors_state_and_door_1(self):
        door = self.doors_state.get("Room_1,1", "Room_1,2")
        self.assertEqual(door.title, "iron door")
        self.assertEqual(
            door.description,
            "This door is bound in iron plates with a small barred window set up high.",
        )
        self.assertEqual(door.door_type, "iron_door")
        self.assertEqual(door.is_locked, False)
        self.assertEqual(door.is_closed, True)
        self.assertEqual(door.closeable, True)

        door = self.doors_state.get("Room_1,1", "Room_2,1")
        self.assertEqual(door.title, "iron door")
        self.assertEqual(
            door.description,
            "This door is bound in iron plates with a small barred window set up high.",
        )
        self.assertEqual(door.door_type, "iron_door")
        self.assertEqual(door.is_locked, True)
        self.assertEqual(door.is_closed, True)
        self.assertEqual(door.closeable, True)

        door = self.doors_state.get("Room_1,2", "Room_2,2")
        self.assertEqual(door.title, "doorway")
        self.assertEqual(
            door.description,
            "This open doorway is outlined by a stone arch set into the wall.",
        )
        self.assertEqual(door.door_type, "doorway")
        self.assertEqual(door.is_locked, False)
        self.assertEqual(door.is_closed, False)
        self.assertEqual(door.closeable, False)

    def test_doors_state_and_door_2(self):
        door = self.doors_state.get("Room_1,1", "Room_1,2")
        self.assertIsInstance(door, IronDoor)
        door_copy = door.copy()
        self.assertIsInstance(door_copy, IronDoor)
