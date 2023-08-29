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
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.drop import (
    AmountToDropUnclearGSM,
    DroppedItemGSM,
    TryingToDropItemYouDontHaveGSM,
    TryingToDropMoreThanYouHaveGSM,
)
from advgame.stmsg.various import ItemUnequippedGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Drop",)


class Test_Drop(TestCase):
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

    def test_drop_1(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process("drop the")  # check
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "DROP")
        self.assertEqual(
            result[0].message,
            "DROP command: bad syntax. Should be 'DROP\u00A0<item\u00A0name>' "
            + "or 'DROP\u00A0<number>\u00A0<item\u00A0name>'.",
        ),

    def test_drop_2(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process("drop a gold coins")  # check
        self.assertIsInstance(result[0], AmountToDropUnclearGSM)
        self.assertEqual(
            result[0].message, "Amount to drop unclear. How many do you mean?"
        )

    def test_drop_3(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process("drop a mana potion")  # check
        self.assertIsInstance(result[0], TryingToDropItemYouDontHaveGSM)
        self.assertEqual(result[0].item_title, "mana potion")
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(
            result[0].message, "You don't have a mana potion in your inventory."
        )

    def test_drop_4(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process("drop 45 gold coins")  # check
        self.assertIsInstance(result[0], TryingToDropMoreThanYouHaveGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_attempted, 45)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(
            result[0].message,
            "You can't drop 45 gold coins. You only have 30 gold coins in "
            + "your inventory.",
        )

    def test_drop_5(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process("drop forty-five gold coins")  # check
        self.assertIsInstance(result[0], TryingToDropMoreThanYouHaveGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_attempted, 45)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(
            result[0].message,
            "You can't drop 45 gold coins. You only have 30 gold coins in your inventory.",
        )

    def test_drop_6(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process("drop 15 gold coins")  # check
        self.assertIsInstance(result[0], DroppedItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_dropped, 15)
        self.assertEqual(result[0].amount_on_floor, 15)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(
            result[0].message,
            "You dropped 15 gold coins. You see 15 gold coins here. You have "
            + "15 gold coins left.",
        )

        result = self.command_processor.process("drop 14 gold coins")  # check
        self.assertIsInstance(result[0], DroppedItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_dropped, 14)
        self.assertEqual(result[0].amount_on_floor, 29)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(
            result[0].message,
            "You dropped 14 gold coins. You see 29 gold coins here. You have "
            + "1 gold coin left.",
        )

    def test_drop_7(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        self.command_processor.process("pick up 29 gold coins")  # check
        result = self.command_processor.process("drop 1 gold coin")  # check
        self.assertIsInstance(result[0], DroppedItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 29)
        self.assertEqual(
            result[0].message,
            "You dropped a gold coin. You see a gold coin here. You have 29 "
            + "gold coins left.",
        )

    def test_drop_8(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process("drop 30 gold coins")  # check
        self.assertIsInstance(result[0], DroppedItemGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_dropped, 30)
        self.assertEqual(result[0].amount_on_floor, 30)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(
            result[0].message,
            "You dropped 30 gold coins. You see 30 gold coins here. You have "
            + "no gold coins left.",
        )

    def test_drop_9(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        longsword = self.items_state.get("Longsword")
        self.command_processor.game_state.character.pick_up_item(longsword)
        self.command_processor.game_state.character.equip_weapon(longsword)
        result = self.command_processor.process("drop longsword")  # check
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertEqual(result[0].item_type, "weapon")
        self.assertEqual(
            result[0].message,
            "You're no longer wielding a longsword. You now can't attack.",
        )
        self.assertIsInstance(result[1], DroppedItemGSM)
        self.assertEqual(result[1].item_title, "longsword")
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(
            result[1].message,
            "You dropped a longsword. You see a longsword here. You have no "
            + "longswords left.",
        )

    def test_drop_10(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        steel_shield = self.items_state.get("Steel_Shield")
        self.command_processor.game_state.character.pick_up_item(steel_shield)
        self.command_processor.game_state.character.equip_shield(steel_shield)
        result = self.command_processor.process("drop steel shield")  # check
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "steel shield")
        self.assertEqual(result[0].item_type, "shield")
        self.assertRegex(
            result[0].message,
            r"You're no longer carrying a steel shield. Your armor class is now \d+.",
        )
        self.assertIsInstance(result[1], DroppedItemGSM)
        self.assertEqual(result[1].item_title, "steel shield")
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(
            result[1].message,
            "You dropped a steel shield. You see a steel shield here. You "
            + "have no steel shields left.",
        )

    def test_drop_11(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        magic_wand = self.items_state.get("Magic_Wand")
        self.command_processor.game_state.character.pick_up_item(magic_wand)
        self.command_processor.game_state.character.equip_wand(magic_wand)
        result = self.command_processor.process("drop magic wand")  # check
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "magic wand")
        self.assertEqual(result[0].item_type, "wand")
        self.assertRegex(
            result[0].message,
            r"You're no longer using a magic wand. You now can't attack.",
        )
        self.assertIsInstance(result[1], DroppedItemGSM)
        self.assertEqual(result[1].item_title, "magic wand")
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(
            result[1].message,
            "You dropped a magic wand. You see a magic wand here. You have no "
            + "magic wands left.",
        )

    def test_drop_12(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        staff = self.items_state.get("Staff")
        self.command_processor.game_state.character.pick_up_item(staff)
        self.command_processor.game_state.character.equip_weapon(staff)
        magic_wand = self.items_state.get("Magic_Wand")
        self.command_processor.game_state.character.pick_up_item(magic_wand)
        self.command_processor.game_state.character.equip_wand(magic_wand)
        result = self.command_processor.process("drop magic wand")  # check
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "magic wand")
        self.assertEqual(result[0].item_type, "wand")
        self.assertRegex(
            result[0].message,
            r"You're no longer using a magic wand. You're now attacking with "
            + r"your staff.",
        )
        self.assertIsInstance(result[1], DroppedItemGSM)
        self.assertEqual(result[1].item_title, "magic wand")
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(
            result[1].message,
            "You dropped a magic wand. You see a magic wand here. You have no "
            + "magic wands left.",
        )

    def test_drop_13(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        staff = self.items_state.get("Staff")
        self.command_processor.game_state.character.pick_up_item(staff)
        self.command_processor.game_state.character.equip_weapon(staff)
        magic_wand = self.items_state.get("Magic_Wand")
        self.command_processor.game_state.character.pick_up_item(magic_wand)
        self.command_processor.game_state.character.equip_wand(magic_wand)
        result = self.command_processor.process("drop staff")  # check
        self.assertIsInstance(result[0], ItemUnequippedGSM)
        self.assertEqual(result[0].item_title, "staff")
        self.assertEqual(result[0].item_type, "weapon")
        self.assertRegex(
            result[0].message,
            r"You're no longer wielding a staff. You're attacking with your "
            + r"magic wand. Your attack bonus is [\d+-]+ and your magic wand "
            + r"damage is \d+d\d+([+-]\d+)?.",
        )
        self.assertIsInstance(result[1], DroppedItemGSM)
        self.assertEqual(result[1].item_title, "staff")
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(
            result[1].message,
            "You dropped a staff. You see a staff here. You have no staffs left.",
        )

    def test_drop_14(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        longsword = self.items_state.get("Longsword")
        self.command_processor.game_state.character.pick_up_item(longsword, qty=3)
        self.command_processor.game_state.character.equip_weapon(longsword)
        result = self.command_processor.process("drop longsword")  # check
        self.assertIsInstance(result[0], DroppedItemGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 2)
        self.assertEqual(
            result[0].message,
            "You dropped a longsword. You see a longsword here. You have 2 "
            + "longswords left.",
        )

    def test_drop_15(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        longsword = self.items_state.get("Longsword")
        self.command_processor.game_state.character.pick_up_item(longsword, qty=3)
        self.command_processor.game_state.character.equip_weapon(longsword)
        result = self.command_processor.process("drop longsword")  # check
        self.assertIsInstance(result[0], DroppedItemGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 2)
        self.assertEqual(
            result[0].message,
            "You dropped a longsword. You see a longsword here. You have 2 "
            + "longswords left.",
        )
