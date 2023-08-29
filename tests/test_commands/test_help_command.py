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
from advgame.stmsg.help_ import (
    DisplayCommandsGSM,
    DisplayHelpForCommandGSM,
    NotRecognizedGSM,
)

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = (
    "Test_Help_1",
    "Test_Help_2",
)


class Test_Help_1(TestCase):
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
        self.command_processor.process("set name to Niath")
        self.command_processor.process("set class to Warrior")
        self.command_processor.process("begin game")

    def test_help_1(self):
        result = self.command_processor.process("help")
        self.assertIsInstance(result[0], DisplayCommandsGSM)
        self.assertEqual(
            result[0].commands_available,
            (
                "ATTACK",
                "CAST SPELL",
                "CLOSE",
                "DRINK",
                "DROP",
                "EQUIP",
                "HELP",
                "INVENTORY",
                "LEAVE",
                "LOCK",
                "LOOK AT",
                "OPEN",
                "PICK LOCK",
                "PICK UP",
                "PUT",
                "QUIT",
                "STATUS",
                "TAKE",
                "UNEQUIP",
                "UNLOCK",
            ),
        )
        self.assertEqual(
            result[0].message,
            """The list of commands available during the game is:

ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, \
PICK UP, PUT, QUIT, STATUS, TAKE, UNEQUIP, and UNLOCK

Which one do you want help with?
""",
        )

    def test_help_2(self):
        result = self.command_processor.process("help juggle")
        self.assertIsInstance(result[0], NotRecognizedGSM)
        self.assertEqual(
            result[0].commands_available,
            (
                "ATTACK",
                "BEGIN GAME",
                "CAST SPELL",
                "CLOSE",
                "DRINK",
                "DROP",
                "EQUIP",
                "HELP",
                "INVENTORY",
                "LEAVE",
                "LOCK",
                "LOOK AT",
                "OPEN",
                "PICK LOCK",
                "PICK UP",
                "PUT",
                "QUIT",
                "REROLL",
                "SET CLASS",
                "SET NAME",
                "STATUS",
                "TAKE",
                "UNEQUIP",
                "UNLOCK",
            ),
        )
        self.assertEqual(
            result[0].message,
            """The command 'JUGGLE' is not recognized. The full list of commands is:

ATTACK, BEGIN GAME, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, INVENTORY, \
LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, QUIT, REROLL, SET CLASS, \
SET NAME, STATUS, TAKE, UNEQUIP, and UNLOCK

Which one do you want help with?
""",
        )

    def test_help_3(self):
        result = self.command_processor.process("help attack")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "ATTACK")
        self.assertEqual(result[0].syntax_tuple, ("<creature\u00A0name>",))
        self.assertEqual(
            result[0].message,
            """Help for the ATTACK command:

Usage: 'ATTACK\u00A0<creature\u00A0name>'

The ATTACK command is used to attack creatures. Beware: if you attack a \
creature and don't kill it, it will attack you in return! After you kill a \
creature, you can check its corpse for loot using the LOOK AT command and \
take loot with the TAKE command.
""",
        )

    def test_help_4(self):
        result = self.command_processor.process("help close")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "CLOSE")
        self.assertEqual(
            result[0].syntax_tuple, ("<door\u00A0name>", "<chest\u00A0name>")
        )
        self.assertEqual(
            result[0].message,
            """Help for the CLOSE command:

Usage: 'CLOSE\u00A0<door\u00A0name>' or 'CLOSE\u00A0<chest\u00A0name>'

The CLOSE command can be used to close doors and chests.
""",
        )

    def test_help_5(self):
        result = self.command_processor.process("help put")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "PUT")
        self.assertEqual(
            result[0].syntax_tuple,
            (
                "<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>",
                "<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>",
                "<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>",
                "<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>",
            ),
        )
        self.assertEqual(
            result[0].message,
            """Help for the PUT command:

Usage: 'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'

The PUT command can be used to remove items from your inventory and place \
them in a chest or on a corpse's person. To leave items on the floor, use \
DROP.
""",
        )

    def test_help_6(self):
        result = self.command_processor.process("help begin game")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "BEGIN GAME")
        self.assertEqual(result[0].syntax_tuple, ("",)),
        self.assertEqual(
            result[0].message,
            """Help for the BEGIN GAME command:

Usage: 'BEGIN GAME'

The BEGIN GAME command is used to start the game after you have set your name \
and class and approved your ability scores. When you enter this command, you \
will automatically be equiped with your starting gear and started in the \
antechamber of the dungeon.
""",
        )


class Test_Help_2(TestCase):
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

    def test_help_1(self):
        result = self.command_processor.process("help")
        self.assertIsInstance(result[0], DisplayCommandsGSM)
        self.assertEqual(
            result[0].commands_available,
            ("BEGIN GAME", "HELP", "QUIT", "REROLL", "SET CLASS", "SET NAME"),
        )
        self.assertEqual(
            result[0].message,
            """The list of commands available before game start is:

BEGIN GAME, HELP, QUIT, REROLL, SET CLASS, and SET NAME

Which one do you want help with?
""",
        )

    def test_help_2(self):
        result = self.command_processor.process("help juggle")
        self.assertIsInstance(result[0], NotRecognizedGSM)
        self.assertEqual(
            result[0].commands_available,
            (
                "ATTACK",
                "BEGIN GAME",
                "CAST SPELL",
                "CLOSE",
                "DRINK",
                "DROP",
                "EQUIP",
                "HELP",
                "INVENTORY",
                "LEAVE",
                "LOCK",
                "LOOK AT",
                "OPEN",
                "PICK LOCK",
                "PICK UP",
                "PUT",
                "QUIT",
                "REROLL",
                "SET CLASS",
                "SET NAME",
                "STATUS",
                "TAKE",
                "UNEQUIP",
                "UNLOCK",
            ),
        )
        self.assertEqual(
            result[0].message,
            """The command 'JUGGLE' is not recognized. The full list of commands is:

ATTACK, BEGIN GAME, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, INVENTORY, \
LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, QUIT, REROLL, SET CLASS, \
SET NAME, STATUS, TAKE, UNEQUIP, and UNLOCK

Which one do you want help with?
""",
        )

    def test_help_3(self):
        result = self.command_processor.process("help attack")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "ATTACK")
        self.assertEqual(result[0].syntax_tuple, ("<creature\u00A0name>",))
        self.assertEqual(
            result[0].message,
            """Help for the ATTACK command:

Usage: 'ATTACK\u00A0<creature\u00A0name>'

The ATTACK command is used to attack creatures. Beware: if you attack a \
creature and don't kill it, it will attack you in return! After you kill a \
creature, you can check its corpse for loot using the LOOK AT command and \
take loot with the TAKE command.
""",
        )

    def test_help_4(self):
        result = self.command_processor.process("help close")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "CLOSE")
        self.assertEqual(
            result[0].syntax_tuple, ("<door\u00A0name>", "<chest\u00A0name>")
        )
        self.assertEqual(
            result[0].message,
            """Help for the CLOSE command:

Usage: 'CLOSE\u00A0<door\u00A0name>' or 'CLOSE\u00A0<chest\u00A0name>'

The CLOSE command can be used to close doors and chests.
""",
        )

    def test_help_5(self):
        result = self.command_processor.process("help put")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "PUT")
        self.assertEqual(
            result[0].syntax_tuple,
            (
                "<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>",
                "<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>",
                "<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>",
                "<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>",
            ),
        )
        self.assertEqual(
            result[0].message,
            """Help for the PUT command:

Usage: 'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'

The PUT command can be used to remove items from your inventory and place \
them in a chest or on a corpse's person. To leave items on the floor, use \
DROP.
""",
        )

    def test_help_6(self):
        result = self.command_processor.process("help begin game")
        self.assertIsInstance(result[0], DisplayHelpForCommandGSM)
        self.assertEqual(result[0].command, "BEGIN GAME")
        self.assertEqual(result[0].syntax_tuple, ("",)),
        self.assertEqual(
            result[0].message,
            """Help for the BEGIN GAME command:

Usage: 'BEGIN GAME'

The BEGIN GAME command is used to start the game after you have set your name \
and class and approved your ability scores. When you enter this command, you \
will automatically be equiped with your starting gear and started in the \
antechamber of the dungeon.
""",
        )
