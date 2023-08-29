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
from advgame.stmsg.pickup import (
    AmountToPickUpUnclearGSM,
    CantPickUpChestCorpseCreatureOrDoorGSM,
    ItemNotFoundGSM,
    ItemPickedUpGSM,
    TryingToPickUpMoreThanIsPresentGSM,
)

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Pick_Up",)


class Test_Pick_Up(TestCase):
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
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True

    def test_pick_up_1(self):
        result = self.command_processor.process("pick up the")  # check
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "PICK UP")
        self.assertEqual(
            result[0].message,
            "PICK UP command: bad syntax. Should be "
            + "'PICK\u00A0UP\u00A0<item\u00A0name>' or "
            + "'PICK\u00A0UP\u00A0<number>\u00A0<item\u00A0name>'.",
        ),

    def test_pick_up_2(self):
        result = self.command_processor.process("pick up a gold coins")  # check
        self.assertIsInstance(result[0], AmountToPickUpUnclearGSM)
        self.assertEqual(
            result[0].message, "Amount to pick up unclear. How many do you mean?"
        )

    def test_pick_up_3(self):
        result = self.command_processor.process("pick up 15 gold coins")  # check
        self.assertIsInstance(result[0], ItemNotFoundGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_attempted, 15)
        self.assertEqual(
            result[0].items_here, ((2, "health potion"), (1, "mana potion"))
        )
        self.assertEqual(
            result[0].message,
            "You see no gold coins here. However, there is 2 health potions "
            + "and a mana potion here.",
        )

    def test_pick_up_4(self):
        result = self.command_processor.process("pick up fifteen gold coins")  # check
        self.assertIsInstance(result[0], ItemNotFoundGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].amount_attempted, 15)
        self.assertEqual(
            result[0].items_here, ((2, "health potion"), (1, "mana potion"))
        )
        self.assertEqual(
            result[0].message,
            "You see no gold coins here. However, there is 2 health potions "
            + "and a mana potion here.",
        )

    def test_pick_up_5(self):
        result = self.command_processor.process("pick up a short sword")  # check
        self.assertIsInstance(result[0], ItemNotFoundGSM)
        self.assertEqual(result[0].item_title, "short sword")
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(
            result[0].items_here, ((2, "health potion"), (1, "mana potion"))
        )
        self.assertEqual(
            result[0].message,
            "You see no short sword here. However, there is 2 health potions "
            + "and a mana potion here.",
        )

    def test_pick_up_6(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process("pick up a short sword")  # check
        self.assertIsInstance(result[0], ItemNotFoundGSM)
        self.assertEqual(result[0].item_title, "short sword")
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ())
        self.assertEqual(result[0].message, "You see no short sword here.")
        self.command_processor.game_state.rooms_state.move(south=True)

    def test_pick_up_7(self):
        result = self.command_processor.process("pick up 2 mana potions")  # check
        self.assertIsInstance(result[0], TryingToPickUpMoreThanIsPresentGSM)
        self.assertEqual(result[0].item_title, "mana potion")
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(
            result[0].message, "You can't pick up 2 mana potions. Only 1 is here."
        )

    def test_pick_up_8(self):
        result = self.command_processor.process("pick up a mana potion")  # check
        self.assertIsInstance(result[0], ItemPickedUpGSM)
        self.assertEqual(result[0].item_title, "mana potion")
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 1)
        self.assertEqual(
            result[0].message, "You picked up a mana potion. You have a mana potion."
        )

    def test_pick_up_9(self):
        result = self.command_processor.process("pick up a health potion")  # check
        result = self.command_processor.process("pick up health potion")  # check
        self.assertIsInstance(result[0], ItemPickedUpGSM)
        self.assertEqual(result[0].item_title, "health potion")
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 2)
        self.assertEqual(
            result[0].message,
            "You picked up a health potion. You have 2 health potions.",
        )

    def test_pick_up_10(self):
        gold_coin = self.items_state.get("Gold_Coin")
        self.command_processor.game_state.rooms_state.cursor.items_here.set(
            "Gold_Coin", 30, gold_coin
        )
        result = self.command_processor.process("pick up 15 gold coins")  # check
        self.assertIsInstance(result[0], ItemPickedUpGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 15)
        self.assertEqual(
            result[0].message, "You picked up 15 gold coins. You have 15 gold coins."
        )
        result = self.command_processor.process("pick up 15 gold coins")  # check
        self.assertIsInstance(result[0], ItemPickedUpGSM)
        self.assertEqual(result[0].item_title, "gold coin")
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(
            result[0].message, "You picked up 15 gold coins. You have 30 gold coins."
        )

    def test_pick_up_11(self):
        result = self.command_processor.process("pick up wooden chest")  # check
        self.assertIsInstance(result[0], CantPickUpChestCorpseCreatureOrDoorGSM)
        self.assertEqual(result[0].element_type, "chest")
        self.assertEqual(result[0].element_title, "wooden chest")
        self.assertEqual(
            result[0].message,
            "You can't pick up the wooden chest: can't pick up chests!",
        )

    def test_pick_up_12(self):
        result = self.command_processor.process("pick up kobold")  # check
        self.assertIsInstance(result[0], CantPickUpChestCorpseCreatureOrDoorGSM)
        self.assertEqual(result[0].element_type, "creature")
        self.assertEqual(result[0].element_title, "kobold")
        self.assertEqual(
            result[0].message, "You can't pick up the kobold: can't pick up creatures!"
        )

    def test_pick_up_13(self):
        result = self.command_processor.process("pick up north iron door")  # check
        self.assertIsInstance(result[0], CantPickUpChestCorpseCreatureOrDoorGSM)
        self.assertEqual(result[0].element_type, "door")
        self.assertEqual(result[0].element_title, "north door")
        self.assertEqual(
            result[0].message, "You can't pick up the north door: can't pick up doors!"
        )

    def test_pick_up_14(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process("pick up kobold corpse")  # check
        self.assertIsInstance(result[0], CantPickUpChestCorpseCreatureOrDoorGSM)
        self.assertEqual(result[0].element_type, "corpse")
        self.assertEqual(result[0].element_title, "kobold corpse")
        self.assertEqual(
            result[0].message,
            "You can't pick up the kobold corpse: can't pick up corpses!",
        )
