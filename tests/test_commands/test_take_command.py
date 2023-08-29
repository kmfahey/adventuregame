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


__all__ = ("Test_Take",)

class Test_Take(unittest.TestCase):
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

    def test_take_1(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        (
            potion_qty,
            health_potion,
        ) = self.command_processor.game_state.rooms_state.cursor.container_here.get(
            "Health_Potion"
        )
        result = self.command_processor.process(
            "take a health potion from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTakenGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].item_title, "health potion")
        self.assertEqual(result[0].amount_taken, 1)
        self.assertEqual(
            result[0].message, "You took a health potion from the kobold corpse."
        )
        self.assertTrue(
            self.command_processor.game_state.character.inventory.contains(
                "Health_Potion"
            )
        )
        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.container_here.contains(
                "Health_Potion"
            )
        )
        self.assertEqual(
            self.command_processor.game_state.character.inventory.get("Health_Potion"),
            (1, health_potion),
        )

    def test_take_2(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process(
            "take 15 gold coins from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTakenGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(
            result[0].message, "You took 15 gold coins from the kobold corpse."
        )
        self.assertTrue(
            self.command_processor.game_state.character.have_item(self.gold_coin)
        )
        self.assertEqual(
            self.command_processor.game_state.character.item_have_qty(self.gold_coin),
            15,
        )
        self.assertTrue(
            self.command_processor.game_state.rooms_state.cursor.container_here.contains(
                "Gold_Coin"
            )
        )
        self.assertEqual(
            self.command_processor.game_state.rooms_state.cursor.container_here.get(
                "Gold_Coin"
            ),
            (15, self.gold_coin),
        )

    def test_take_3(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        (
            _,
            short_sword,
        ) = self.command_processor.game_state.rooms_state.cursor.container_here.get(
            "Short_Sword"
        )
        result = self.command_processor.process(
            "take one short sword from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTakenGSM)

    def test_take_4(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process(
            "take one small leather armor from the kobold corpses"
        )
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        result = self.command_processor.process("take one small leather armor")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        result = self.command_processor.process("take the from the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        result = self.command_processor.process("take the short sword from the")
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
        self.assertEqual(result[0].command, "TAKE")
        self.assertEqual(
            result[0].message,
            "TAKE command: bad syntax. Should be "
            + "'TAKE\u00A0<item\u00A0name>\u00A0FROM\u00A0<container\u00A0name>' or "
            + "'TAKE\u00A0<number>\u00A0<item\u00A0name>\u00A0FROM\u00A0<container\u00A0name>'.",
        ),

    def test_take_5(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process(
            "take the short sword from the sorcerer corpse"
        )  # check
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerNotFoundGSM)
        self.assertEqual(result[0].container_not_found_title, "sorcerer corpse")
        self.assertEqual(result[0].container_present_title, "kobold corpse")
        self.assertEqual(
            result[0].message,
            "There is no sorcerer corpse here. However, there *is* a kobold corpse here.",
        )

    def test_take_6(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        container = (
            self.command_processor.game_state.rooms_state.cursor.container_here
        )  # check
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process(
            "take the short sword from the sorcerer corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerNotFoundGSM)
        self.assertEqual(result[0].container_not_found_title, "sorcerer corpse")
        self.assertIs(result[0].container_present_title, None)
        self.assertEqual(result[0].message, "There is no sorcerer corpse here.")
        self.command_processor.game_state.rooms_state.cursor.container_here = container

    def test_take_7(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process(
            "take 3 small leather armors from the kobold corpse"
        )
        self.assertIsInstance(
            result[0], advg.stmsg.take.TryingToTakeMoreThanIsPresentGSM
        )
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].item_title, "small leather armor")
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(
            result[0].message,
            "You can't take 3 suits of small leather armor from the kobold "
            + "corpse. Only 1 is there.",
        )

    def test_take_8(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.process("take the short sword from the kobold corpse")
        result = self.command_processor.process(
            "take the short sword from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainerGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertIs(result[0].amount_attempted, 1)
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].item_title, "short sword")
        self.assertEqual(
            result[0].message, "The kobold corpse doesn't have a short sword on them."
        )

    def test_take_9(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.process("take the short sword from the kobold corpse")
        result = self.command_processor.process(
            "take three short swords from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainerGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].item_title, "short sword")
        self.assertEqual(
            result[0].message,
            "The kobold corpse doesn't have any short swords on them.",
        )

    def test_take_10(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process(
            "take fifteen gold coins from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTakenGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(
            result[0].message, "You took 15 gold coins from the kobold corpse."
        )

    def test_take_11(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take gold coins from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTakenGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(
            result[0].message, "You took 15 gold coins from the kobold corpse."
        )

    def test_take_12(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process("take gold coin from the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTakenGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(
            result[0].message, "You took 15 gold coins from the kobold corpse."
        )

    def test_take_13(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take a small leather armor from the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTakenGSM)
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].amount_taken, 1)
        self.assertEqual(result[0].item_title, "small leather armor")
        self.assertEqual(
            result[0].message,
            "You took a small leather armor from the kobold corpse.",
        )

    def test_take_14(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 30, self.gold_coin
        )
        result = self.command_processor.process(
            "take 30 gold coins from the kobold corpse"
        )
        result = self.command_processor.process(
            "put 15 gold coins on the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].amount_put, 15)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(
            result[0].message,
            "You put 15 gold coins on the kobold corpse's person. You have 15 "
            + "gold coins left.",
        )

    def test_take_15(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take 15 gold coins from the kobold corpse"
        )
        result = self.command_processor.process("put 1 gold coin on the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 14)
        self.assertEqual(
            result[0].message,
            "You put 1 gold coin on the kobold corpse's person. You have 14 "
            + "gold coins left.",
        )

    def test_take_16(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take 14 gold coins from the kobold corpse"
        )
        result = self.command_processor.process(
            "put 13 gold coins on the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].amount_put, 13)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(
            result[0].message,
            "You put 13 gold coins on the kobold corpse's person. You have 1 "
            + "gold coin left.",
        )

    def test_take_17(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take fourteen gold coins from the kobold corpse"
        )
        result = self.command_processor.process(
            "put thirteen gold coins on the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].amount_put, 13)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(
            result[0].message,
            "You put 13 gold coins on the kobold corpse's person. You have 1 "
            + "gold coin left.",
        )

    def test_take_18(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take 1 gold coin from the kobold corpse"
        )
        result = self.command_processor.process("put 1 gold coin on the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].container_title, "kobold corpse")
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(
            result[0].message,
            "You put 1 gold coin on the kobold corpse's person. You have no "
            + "more gold coins.",
        )

    def test_take_19(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process("put 2 gold coins on the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.put.ItemNotInInventoryGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(
            result[0].message, "You don't have any gold coins in your inventory."
        )

    def test_take_20(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process("put 1 gold coin on the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.put.ItemNotInInventoryGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(
            result[0].message, "You don't have a gold coin in your inventory."
        )

    def test_take_21(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take five gold coins from the kobold corpse"
        )
        result = self.command_processor.process(
            "put ten gold coin on the kobold corpse"
        )
        self.assertIsInstance(result[0], advg.stmsg.put.TryingToPutMoreThanYouHaveGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_present, 5)
        self.assertEqual(
            result[0].message, "You only have 5 gold coins in your inventory."
        )

    def test_take_22(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take 5 gold coins from the kobold corpse"
        )
        result = self.command_processor.process("put 10 gold coin on the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.put.TryingToPutMoreThanYouHaveGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_present, 5)
        self.assertEqual(
            result[0].message, "You only have 5 gold coins in your inventory."
        )

    def test_take_23(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "take 5 gold coins from the kobold corpse"
        )
        result = self.command_processor.process("put 4 gold coins on the kobold corpse")
        result = self.command_processor.process("put 4 gold coins on the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.put.TryingToPutMoreThanYouHaveGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(
            result[0].message, "You only have 1 gold coin in your inventory."
        )

    def test_take_24(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process("put a gold coins on the kobold corpse")
        self.assertIsInstance(result[0], advg.stmsg.put.AmountToPutUnclearGSM)
        self.assertEqual(
            result[0].message, "Amount to put unclear. How many do you mean?"
        )

    def test_take_25(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process("put on the kobold corpse")
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

    def test_take_26(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "put one small leather armor on"
        )  # check
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

    def test_take_27(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process("put on")  # check
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

    def test_take_28(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        self.command_processor.game_state.rooms_state.cursor.container_here.set(
            "Gold_Coin", 15, self.gold_coin
        )
        result = self.command_processor.process(
            "put 1 gold coin in the kobold corpse"
        )  # check
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

    def test_take_29(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process(
            "take three short swords from the wooden chest"
        )
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainerGSM)
        self.assertEqual(result[0].container_title, "wooden chest")
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, "chest")
        self.assertEqual(result[0].item_title, "short sword")
        self.assertEqual(
            result[0].message, "The wooden chest doesn't have any short swords in it."
        )

    def test_take_30(self):
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process("take gold coin from wooden chest")
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerIsClosedGSM)
        self.assertEqual(result[0].target, "wooden chest")
        self.assertEqual(result[0].message, "The wooden chest is closed.")
