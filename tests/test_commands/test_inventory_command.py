#!/usr/bin/python3

from unittest import TestCase
from operator import itemgetter

from advgame import (
    Armor,
    Coin,
    CommandProcessor,
    ContainersState,
    CreaturesState,
    DoorsState,
    GameState,
    ItemsState,
    Potion,
    RoomsState,
    Shield,
    Wand,
    Weapon,
)
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.inven import DisplayInventoryGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Inventory",)


class Test_Inventory(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        self.doors_state = DoorsState(**doors_ini_config.sections)
        containers_ini_config.sections["Wooden_Chest_1"]["contents"] = (
            "[20xGold_Coin,1xWarhammer,1xMana_Potion,"
            + "1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]"
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
        longsword = self.command_processor.game_state.items_state.get("Longsword")
        self.scale_mail = self.command_processor.game_state.items_state.get(
            "Scale_Mail"
        )
        self.shield = self.command_processor.game_state.items_state.get("Steel_Shield")
        self.magic_wand = self.command_processor.game_state.items_state.get(
            "Magic_Wand"
        )
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        gold_coin = self.command_processor.game_state.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)
        self.command_processor.game_state.character.pick_up_item(mana_potion, qty=2)
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)

    def test_inventory_1(self):
        result = self.command_processor.process("inventory show")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "INVENTORY")
        self.assertEqual(
            result[0].message, "INVENTORY command: bad syntax. Should be 'INVENTORY'."
        )

    def test_inventory_2(self):
        result = self.command_processor.process("inventory")
        self.assertIsInstance(result[0], DisplayInventoryGSM)
        self.assertEqual(
            tuple(map(itemgetter(0), result[0].inventory_contents)),
            (30, 1, 1, 2, 1, 1),
        )
        self.assertIsInstance(result[0].inventory_contents[0][1], Coin)
        self.assertIsInstance(result[0].inventory_contents[1][1], Weapon)
        self.assertIsInstance(result[0].inventory_contents[2][1], Wand)
        self.assertIsInstance(result[0].inventory_contents[3][1], Potion)
        self.assertIsInstance(result[0].inventory_contents[4][1], Armor)
        self.assertIsInstance(result[0].inventory_contents[5][1], Shield)
        self.assertEqual(
            result[0].message,
            "You have 30 gold coins, a longsword, a magic wand, 2 mana "
            + "potions, a suit of scale mail armor, and a steel shield in "
            + "your inventory.",
        )
