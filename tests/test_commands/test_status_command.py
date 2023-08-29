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
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.status import StatusOutputGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Status",)


class Test_Status(TestCase):
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

    def test_status1(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("status status")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "STATUS")
        self.assertEqual(
            result[0].message, "STATUS command: bad syntax. Should be 'STATUS'."
        )

    def test_status2(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        longsword = self.command_processor.game_state.items_state.get("Longsword")
        self.scale_mail = self.command_processor.game_state.items_state.get(
            "Scale_Mail"
        )
        self.shield = self.command_processor.game_state.items_state.get("Steel_Shield")
        self.command_processor.game_state.character.pick_up_item(longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.equip_weapon(longsword)
        self.command_processor.game_state.character.equip_armor(self.scale_mail)
        self.command_processor.game_state.character.equip_shield(self.shield)
        result = self.command_processor.process("status")
        self.assertIsInstance(result[0], StatusOutputGSM)
        self.assertRegex(
            result[0].message,
            r"Hit Points: \d+/\d+ \| Attack: [+-]\d+ \(\d+d[\d+-]+ damage\) - "
            + r"Armor Class: \d+ \| Weapon: [a-z ]+ - Armor: [a-z ]+ - Shield: "
            + r"[a-z ]+",
        )

    def test_status3(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        staff = self.command_processor.game_state.items_state.get("Staff")
        self.magic_wand = self.command_processor.game_state.items_state.get(
            "Magic_Wand"
        )
        self.command_processor.game_state.character.pick_up_item(staff)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)
        self.command_processor.game_state.character.equip_weapon(staff)
        self.command_processor.game_state.character.equip_wand(self.magic_wand)
        result = self.command_processor.process("status")
        self.assertIsInstance(result[0], StatusOutputGSM)
        self.assertRegex(
            result[0].message,
            r"Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: [+-]\d+ "
            + r"\(\d+d[\d+-]+ damage\) - Armor Class: \d+ \| Weapon: [a-z ]+ - "
            + r"Wand: [a-z ]+",
        )

    def test_status4(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("status")
        self.assertIsInstance(result[0], StatusOutputGSM)
        self.assertRegex(
            result[0].message,
            r"Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: no wand "
            + r"or weapon equipped - Armor Class: \d+ \| Weapon: none - Wand: "
            + r"none",
        )

    def test_status5(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("status")
        self.assertIsInstance(result[0], StatusOutputGSM)
        self.assertRegex(
            result[0].message,
            r"Hit Points: \d+/\d+ \| Attack: no weapon equipped - Armor "
            + r"Class: \d+ \| Weapon: none - Armor: none - Shield: none",
        )

    def test_status6(self):
        self.command_processor.game_state.character_name = "Kaeva"
        self.command_processor.game_state.character_class = "Priest"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("status")
        self.assertIsInstance(result[0], StatusOutputGSM)
        self.assertRegex(
            result[0].message,
            r"Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: no weapon "
            + r"equipped - Armor Class: \d+ \| Weapon: none - Armor: none - "
            + r"Shield: none",
        )

    def test_status7(self):
        self.command_processor.game_state.character_name = "Kaeva"
        self.command_processor.game_state.character_class = "Priest"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.take_damage(10)
        result = self.command_processor.process("status")
        self.assertIsInstance(result[0], StatusOutputGSM)
        self.assertRegex(
            result[0].message,
            r"Hit Points: (?!(\d+)/\1)\d+/\d+ - Mana Points: \d+/\d+ \| "
            + r"Attack: no weapon equipped - Armor Class: \d+ \| Weapon: none "
            + r"- Armor: none - Shield: none",
        )

    def test_status8(self):
        self.command_processor.game_state.character_name = "Kaeva"
        self.command_processor.game_state.character_class = "Priest"
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.spend_mana(10)
        result = self.command_processor.process("status")
        self.assertIsInstance(result[0], StatusOutputGSM)
        self.assertRegex(
            result[0].message,
            r"Hit Points: \d+/\d+ - Mana Points: (?!(\d+)/\1)\d+/\d+ \| "
            + r"Attack: no weapon equipped - Armor Class: \d+ \| Weapon: none "
            + r"- Armor: none - Shield: none",
        )
