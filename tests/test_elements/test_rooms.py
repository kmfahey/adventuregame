#!/usr/bin/python3

from unittest import TestCase

from advgame import (
    BadCommandError,
    ContainersState,
    CreaturesState,
    Door,
    DoorsState,
    ItemsState,
    RoomsState,
)

from ..context import (
    containers_ini_config,
    creatures_ini_config,
    doors_ini_config,
    items_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_RoomsState_Obj",)


class Test_RoomsState_Obj(TestCase):
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

    def test_rooms_state_init(self):
        self.assertEqual(self.rooms_state.cursor.internal_name, "Room_1,1")
        self.assertTrue(self.rooms_state.cursor.is_entrance)
        self.assertFalse(self.rooms_state.cursor.is_exit)
        self.assertEqual(self.rooms_state.cursor.title, "southwest dungeon room")
        self.assertEqual(self.rooms_state.cursor.description, "Entrance room.")
        self.assertTrue(self.rooms_state.cursor.has_north_door)
        self.assertEqual(self.rooms_state.cursor.north_door.title, "north door")
        self.assertEqual(
            self.rooms_state.cursor.north_door.description,
            "This door is bound in iron plates with a "
            "small barred window set up high.",
        )
        self.assertEqual(self.rooms_state.cursor.north_door.door_type, "iron_door")
        self.assertEqual(self.rooms_state.cursor.north_door.is_locked, False)
        self.assertEqual(self.rooms_state.cursor.north_door.is_closed, True)
        self.assertEqual(self.rooms_state.cursor.north_door.closeable, True)
        self.assertTrue(self.rooms_state.cursor.has_east_door)
        self.assertTrue(self.rooms_state.cursor.east_door.title, "east door")
        self.assertTrue(
            self.rooms_state.cursor.east_door.description,
            "This door is bound in iron plates with a small barred window set up high.",
        )
        self.assertTrue(self.rooms_state.cursor.east_door.door_type, "iron_door")
        self.assertTrue(self.rooms_state.cursor.east_door.is_locked, True)
        self.assertTrue(self.rooms_state.cursor.east_door.is_closed, True)
        self.assertTrue(self.rooms_state.cursor.east_door.closeable, True)
        self.assertFalse(self.rooms_state.cursor.has_south_door)
        self.assertFalse(self.rooms_state.cursor.has_west_door)
        self.rooms_state.move(north=True)

    def test_rooms_state_move_east(self):
        self.rooms_state.cursor.east_door.is_locked = False
        self.rooms_state.move(east=True)
        self.assertEqual(self.rooms_state.cursor.internal_name, "Room_2,1")
        self.assertFalse(self.rooms_state.cursor.is_entrance)
        self.assertFalse(self.rooms_state.cursor.is_exit)
        self.assertEqual(self.rooms_state.cursor.title, "southeast dungeon room")
        self.assertEqual(self.rooms_state.cursor.description, "Nondescript room.")
        self.assertTrue(self.rooms_state.cursor.has_north_door)
        self.assertFalse(self.rooms_state.cursor.has_east_door)
        self.assertFalse(self.rooms_state.cursor.has_south_door)
        self.assertTrue(self.rooms_state.cursor.has_west_door)

    def test_rooms_state_move_north(self):
        self.rooms_state.move(north=True)
        self.assertEqual(self.rooms_state.cursor.internal_name, "Room_1,2")
        self.assertFalse(self.rooms_state.cursor.is_entrance)
        self.assertFalse(self.rooms_state.cursor.is_exit)
        self.assertEqual(self.rooms_state.cursor.title, "northwest dungeon room")
        self.assertEqual(self.rooms_state.cursor.description, "Nondescript room.")
        self.assertFalse(self.rooms_state.cursor.has_north_door)
        self.assertTrue(self.rooms_state.cursor.has_east_door)
        self.assertTrue(self.rooms_state.cursor.has_south_door)
        self.assertFalse(self.rooms_state.cursor.has_west_door)

    def test_rooms_state_move_north_and_east(self):
        self.rooms_state.cursor.east_door.is_locked = False
        self.rooms_state.move(north=True)
        self.rooms_state.move(east=True)
        self.assertTrue(self.rooms_state.cursor.west_door.title, "west doorway")
        self.assertTrue(
            self.rooms_state.cursor.west_door.description,
            "This door is bound in iron plates with a small barred window set up high.",
        )
        self.assertTrue(self.rooms_state.cursor.west_door.door_type, "doorway")
        self.assertFalse(self.rooms_state.cursor.west_door.is_locked)
        self.assertFalse(self.rooms_state.cursor.west_door.is_closed)
        self.assertFalse(self.rooms_state.cursor.west_door.closeable)
        self.assertEqual(self.rooms_state.cursor.internal_name, "Room_2,2")
        self.assertTrue(self.rooms_state.cursor.is_exit)
        self.assertFalse(self.rooms_state.cursor.is_entrance)
        self.assertEqual(self.rooms_state.cursor.title, "northeast dungeon room")
        self.assertEqual(self.rooms_state.cursor.description, "Exit room.")
        self.assertTrue(self.rooms_state.cursor.has_north_door)
        self.assertFalse(self.rooms_state.cursor.has_east_door)
        self.assertTrue(self.rooms_state.cursor.has_south_door)
        self.assertTrue(self.rooms_state.cursor.has_west_door)

    def test_rooms_state_invalid_move(self):
        with self.assertRaises(BadCommandError):
            self.rooms_state.move(south=True)

    def test_rooms_state_room_items_container_creature_here(self):
        kobold = self.creatures_state.get("Kobold_Trysk")
        wooden_chest = self.containers_state.get("Wooden_Chest_1")
        mana_potion = self.items_state.get("Mana_Potion")
        health_potion = self.items_state.get("Health_Potion")
        room = self.rooms_state.cursor
        self.assertEqual(room.creature_here, kobold)
        self.assertEqual(room.container_here, wooden_chest)
        self.assertEqual(room.items_here.get("Mana_Potion"), (1, mana_potion))
        self.assertEqual(room.items_here.get("Health_Potion"), (2, health_potion))

    def test_rooms_state_and_door(self):
        self.assertIsInstance(self.rooms_state.cursor.north_door, Door)
        self.assertEqual(
            self.rooms_state.cursor.north_door.internal_name, "Room_1,1_x_Room_1,2"
        )
        self.assertEqual(
            self.rooms_state.cursor.east_door.internal_name, "Room_1,1_x_Room_2,1"
        )

    def test_room_doors(self):
        doors_tuple = self.rooms_state.cursor.doors
        self.assertEqual(doors_tuple[0].internal_name, "Room_1,1_x_Room_1,2")
        self.assertEqual(doors_tuple[1].internal_name, "Room_1,1_x_Room_2,1")
