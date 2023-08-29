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


__all__ = ("Test_Put",)

class Test_Put(unittest.TestCase):
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
        self.game_state.character_name = "Niath"
        self.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        self.game_state.character.pick_up_item(self.items_state.get("Longsword"))
        self.game_state.character.pick_up_item(self.items_state.get("Studded_Leather"))
        self.game_state.character.pick_up_item(self.items_state.get("Steel_Shield"))
        self.game_state.character.equip_weapon(self.items_state.get("Longsword"))
        self.game_state.character.equip_armor(self.items_state.get("Studded_Leather"))
        self.game_state.character.equip_shield(self.items_state.get("Steel_Shield"))
        (
            _,
            self.gold_coin,
        ) = self.command_processor.game_state.rooms_state.cursor.container_here.get(
            "Gold_Coin"
        )

    def test_put_1(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process(
            "take 20 gold coins from the wooden chest"
        )
        result = self.command_processor.process("put 5 gold coins in the wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "wooden chest")
        self.assertEqual(result[0].container_type, "chest")
        self.assertEqual(result[0].amount_put, 5)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(
            result[0].message,
            "You put 5 gold coins in the wooden chest. You have 15 gold coins "
            + "left.",
        )

    def test_put_2(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        self.command_processor.process("take 15 gold coins from the wooden chest")
        result = self.command_processor.process("put 1 gold coin in the wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "wooden chest")
        self.assertEqual(result[0].container_type, "chest")
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 14)
        self.assertEqual(
            result[0].message,
            "You put 1 gold coin in the wooden chest. You have 14 gold coins "
            + "left.",
        )

    def test_put_3(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        self.command_processor.process("take 14 gold coins from the wooden chest")
        self.command_processor.process("put 12 gold coins in the wooden chest")
        result = self.command_processor.process("put 1 gold coin in the wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "wooden chest")
        self.assertEqual(result[0].container_type, "chest")
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(
            result[0].message,
            "You put 1 gold coin in the wooden chest. You have 1 gold coin left.",
        )

    def test_put_4(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        self.command_processor.process("take 1 gold coin from the wooden chest")
        result = self.command_processor.process("put 1 gold coin in the wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "wooden chest")
        self.assertEqual(result[0].container_type, "chest")
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(
            result[0].message,
            "You put 1 gold coin in the wooden chest. You have no more gold "
            + "coins.",
        )

    def test_put_5(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take one short sword from the wooden chest"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainerGSM)
        self.assertEqual(result[0].container_title, "wooden chest")
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].container_type, "chest")
        self.assertEqual(result[0].item_title, "short sword")
        self.assertEqual(
            result[0].message, "The wooden chest doesn't have a short sword in it."
        )

    def test_put_6(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process("put gold coin in wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerIsClosedGSM)
        self.assertEqual(result[0].target, "wooden chest")
        self.assertEqual(result[0].message, "The wooden chest is closed.")

    def test_put_7(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process("put in")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        result = self.command_processor.process("put 1 gold coin in")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        result = self.command_processor.process("put in the wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        result = self.command_processor.process("put 1 gold coin on the wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "PUT")
        self.assertEqual(
            result[0].message,
            "PUT command: bad syntax. Should be "
            + "'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
            + "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
            + "'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or "
            + "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'.",
        ),

    def test_put_8(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process("take gold coins from wooden chest")
        result = self.command_processor.process("put gold coins in wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "wooden chest")
        self.assertEqual(result[0].container_type, "chest")
        self.assertEqual(result[0].amount_put, 15)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(
            result[0].message,
            "You put 15 gold coins in the wooden chest. You have no more gold "
            + "coins.",
        )
