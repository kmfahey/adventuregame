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
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.leave import DoorIsLockedGSM, LeftRoomGSM, WonTheGameGSM
from advgame.stmsg.various import DoorNotPresentGSM, EnteredRoomGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Leave",)


class Test_Leave(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        self.doors_state = DoorsState(**doors_ini_config.sections)
        containers_ini_config.sections["Wooden_Chest_1"]["contents"] = (
            "[20xGold_Coin,1xWarhammer,1xMana_Potion,"
            "1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]"
        )
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

    def test_leave_1(self):
        result = self.command_processor.process("leave")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("leave using")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("leave using north")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "LEAVE")
        self.assertEqual(
            result[0].message,
            "LEAVE command: bad syntax. Should be "
            + "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOOR', "
            + "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOORWAY', "
            + "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<door\u00A0name>', or "
            + "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0<door\u00A0name>'.",
        )

    def test_leave_2(self):
        result = self.command_processor.process("leave using west door")
        self.assertIsInstance(result[0], DoorNotPresentGSM)
        self.assertEqual(result[0].compass_dir, "west")
        self.assertEqual(result[0].message, "This room does not have a west door.")

    def test_leave_3(self):
        result = self.command_processor.process("leave using north door")
        self.assertIsInstance(result[0], LeftRoomGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertEqual(result[0].message, "You leave the room via the north door.")
        self.assertIsInstance(result[1], EnteredRoomGSM)
        self.assertIsInstance(result[1].room, Room)
        self.assertEqual(
            result[1].message,
            "Nondescript room.\nThere is a doorway to the east and an iron "
            + "door to the south.",
        )
        result = self.command_processor.process("leave using south door")
        self.assertIsInstance(result[0], LeftRoomGSM)
        self.assertEqual(result[0].compass_dir, "south")
        self.assertEqual(result[0].message, "You leave the room via the south door.")
        self.assertIsInstance(result[1], EnteredRoomGSM)
        self.assertIsInstance(result[1].room, Room)
        self.assertEqual(
            result[1].message,
            "Entrance room.\nYou see a wooden chest here.\nThere is a kobold "
            + "in the room.\nYou see a mana potion and 2 health potions on "
            + "the floor.\nThere is an iron door to the north and an iron "
            + "door to the east.",
        )

    def test_leave_4(self):
        result = self.command_processor.process("leave using north iron door")
        self.assertIsInstance(result[0], LeftRoomGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertEqual(result[0].message, "You leave the room via the north door.")
        self.assertIsInstance(result[1], EnteredRoomGSM)
        self.assertIsInstance(result[1].room, Room)
        self.assertEqual(
            result[1].message,
            "Nondescript room.\nThere is a doorway to the east and an iron "
            + "door to the south.",
        )

    def test_leave_5(self):
        self.command_processor = CommandProcessor(self.game_state)
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True
        self.assertEqual(
            self.command_processor.game_state.rooms_state.cursor.title,
            "southwest dungeon room",
        )
        self.command_processor.process("leave using north door")
        self.assertEqual(
            self.command_processor.game_state.rooms_state.cursor.title,
            "northwest dungeon room",
        )
        self.command_processor.process("leave using east doorway")
        self.assertEqual(
            self.command_processor.game_state.rooms_state.cursor.title,
            "northeast dungeon room",
        )
        result = self.command_processor.process("leave using north door")
        self.assertIsInstance(result[0], DoorIsLockedGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertEqual(result[0].portal_type, "door")
        self.assertEqual(
            result[0].message,
            "You can't leave the room via the north door. The door is locked.",
        )
        result = self.command_processor.process("pick lock on north door")
        result = self.command_processor.process("leave using north door")
        self.assertIsInstance(result[0], LeftRoomGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertEqual(result[0].message, "You leave the room via the north door.")
        self.assertIsInstance(result[1], WonTheGameGSM)
        self.assertEqual(
            result[1].message,
            "You found the exit to the dungeon. You have won the game!",
        )
