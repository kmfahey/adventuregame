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


__all__ = ("Test_Drink",)

class Test_Drink(unittest.TestCase):
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

    def test_drink1(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        for bad_argument_str in (
            "drink",
            "drink the",
            "drink 2 mana potion",
            "drink 1 mana potions",
        ):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], advg.stmsg.command.BadSyntaxGSM)
            self.assertEqual(result[0].command, "DRINK")
            self.assertEqual(
                result[0].message,
                "DRINK command: bad syntax. Should be "
                + "'DRINK\u00A0[THE]\u00A0<potion\u00A0name>' or "
                + "'DRINK\u00A0<number>\u00A0<potion\u00A0name>(s)'.",
            )

    def test_drink2(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("drink health potion")
        self.assertIsInstance(result[0], advg.stmsg.drink.ItemNotInInventoryGSM)
        self.assertEqual(result[0].item_title, "health potion")
        self.assertEqual(
            result[0].message, "You don't have a health potion in your inventory."
        )

    def test_drink3(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get(
            "Health_Potion"
        )
        self.command_processor.game_state.character.pick_up_item(health_potion)
        self.command_processor.game_state.character.take_damage(10)
        result = self.command_processor.process("drink health potion")
        self.assertIsInstance(result[0], advg.stmsg.various.UnderwentHealingEffectGSM)
        self.assertEqual(result[0].amount_healed, 10)
        self.assertRegex(
            result[0].message,
            r"You regained 10 hit points. You're fully healed! Your hit "
            + r"points are (\d+)/\1.",
        )

    def test_drink4(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get(
            "Health_Potion"
        )
        self.command_processor.game_state.character.pick_up_item(health_potion)
        self.command_processor.game_state.character.take_damage(30)
        result = self.command_processor.process("drink health potion")
        self.assertEqual(health_potion.hit_points_recovered, 20)
        self.assertIsInstance(result[0], advg.stmsg.various.UnderwentHealingEffectGSM)
        self.assertEqual(result[0].amount_healed, 20)
        self.assertRegex(
            result[0].message,
            r"You regained 20 hit points. Your hit points are (?!(\d+)/\1)\d+/\d+.",
        )

    def test_drink5(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get(
            "Health_Potion"
        )
        self.command_processor.game_state.character.pick_up_item(health_potion)
        result = self.command_processor.process("drink health potion")
        self.assertIsInstance(result[0], advg.stmsg.various.UnderwentHealingEffectGSM)
        self.assertEqual(result[0].amount_healed, 0)
        self.assertRegex(
            result[0].message,
            r"You didn't regain any hit points. You're fully healed! Your hit "
            + r"points are \d+/\d+.",
        )

    def test_drink6(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        self.command_processor.game_state.character.spend_mana(10)
        result = self.command_processor.process("drink mana potion")
        self.assertEqual(mana_potion.mana_points_recovered, 20)
        self.assertIsInstance(result[0], advg.stmsg.drink.DrankManaPotionGSM)
        self.assertEqual(result[0].amount_regained, 10)
        self.assertRegex(
            result[0].message,
            r"You regained 10 mana points. You have full mana points! Your "
            + r"mana points are (\d+)/\1.",
        )

    def test_drink7(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        mana_potion.mana_points_recovered = 11
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        self.command_processor.game_state.character.spend_mana(15)
        result = self.command_processor.process("drink mana potion")
        self.assertEqual(mana_potion.mana_points_recovered, 11)
        self.assertIsInstance(result[0], advg.stmsg.drink.DrankManaPotionGSM)
        self.assertEqual(result[0].amount_regained, 11)
        self.assertRegex(
            result[0].message,
            r"You regained 11 mana points. Your mana points are (?!(\d+)/\1)\d+/\d+.",
        )

    def test_drink8(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process("drink mana potion")
        self.assertEqual(mana_potion.mana_points_recovered, 20)
        self.assertIsInstance(result[0], advg.stmsg.drink.DrankManaPotionGSM)
        self.assertEqual(result[0].amount_regained, 0)
        self.assertRegex(
            result[0].message,
            r"You didn't regain any mana points. You have full mana points! "
            + r"Your mana points are (\d+)/\1.",
        )

    def test_drink9(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process("drink mana potion")
        self.assertIsInstance(
            result[0], advg.stmsg.drink.DrankManaPotionWhenNotASpellcasterGSM
        )
        self.assertEqual(
            result[0].message,
            "You feel a little strange, but otherwise nothing happens.",
        )

    def test_drink10(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        gold_coin = self.command_processor.game_state.items_state.get("Gold_Coin")
        self.command_processor.game_state.character.pick_up_item(gold_coin)
        result = self.command_processor.process("drink gold coin")
        self.assertIsInstance(result[0], advg.stmsg.drink.ItemNotDrinkableGSM)
        self.assertEqual(result[0].message, "A gold coin is not drinkable.")

    def test_drink11(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process("drink 3 mana potions")
        self.assertIsInstance(
            result[0], advg.stmsg.drink.TriedToDrinkMoreThanPossessedGSM
        )
        self.assertEqual(
            result[0].message,
            "You can't drink 3 mana potions. You only have 1 of them.",
        )

    def test_drink12(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process("drink three mana potions")
        self.assertIsInstance(
            result[0], advg.stmsg.drink.TriedToDrinkMoreThanPossessedGSM
        )
        self.assertEqual(
            result[0].message,
            "You can't drink 3 mana potions. You only have 1 of them.",
        )

    def test_drink13(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get("Mana_Potion")
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process("drink mana potions")
        self.assertIsInstance(result[0], advg.stmsg.drink.AmountToDrinkUnclearGSM)
        self.assertEqual(
            result[0].message, "Amount to drink unclear. How many do you mean?"
        )
