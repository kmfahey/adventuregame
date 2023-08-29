#!/usr/bin/python3

import unittest
import operator

from advgame import (
    CommandProcessor,
    ContainersState,
    Corpse,
    CreaturesState,
    DoorsState,
    GameState,
    ItemsState,
    RoomsState,
)
from advgame.stmsg.attack import (
    AttackHitGSM,
    AttackMissedGSM,
    OpponentNotFoundGSM,
    YouHaveNoWeaponOrWandEquippedGSM,
)
from advgame.stmsg.be_atkd import (
    AttackedAndHitGSM,
    AttackedAndNotHitGSM,
    CharacterDeathGSM,
)
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.various import FoeDeathGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = (
    "Test_Attack_1",
    "Test_Attack_2",
)


class Test_Attack_1(unittest.TestCase):
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
        self.game_state.character_name = "Niath"
        self.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        self.game_state.character.pick_up_item(self.items_state.get("Longsword"))
        self.game_state.character.pick_up_item(self.items_state.get("Studded_Leather"))
        self.game_state.character.pick_up_item(self.items_state.get("Steel_Shield"))
        self.game_state.character.equip_weapon(self.items_state.get("Longsword"))
        self.game_state.character.equip_armor(self.items_state.get("Studded_Leather"))
        self.game_state.character.equip_shield(self.items_state.get("Steel_Shield"))
        # (_, self.gold_coin) = self.command_processor.game_state.rooms_state.cursor.container_here.get('Gold_Coin')

    def test_attack_1(self):
        result = self.command_processor.process("attack")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "ATTACK")
        self.assertEqual(
            result[0].message,
            "ATTACK command: bad syntax. Should be "
            + "'ATTACK\u00A0<creature\u00A0name>'.",
        )

    def test_attack_2(self):
        self.command_processor.process("unequip longsword")
        result = self.command_processor.process("attack sorcerer")
        self.assertIsInstance(result[0], YouHaveNoWeaponOrWandEquippedGSM)
        self.assertEqual(
            result[0].message, "You have no weapon equipped; you can't attack."
        )
        self.command_processor.process("equip longsword")

    def test_attack_3(self):
        result = self.command_processor.process("attack sorcerer")
        self.assertIsInstance(result[0], OpponentNotFoundGSM)
        self.assertEqual(result[0].creature_title_given, "sorcerer")
        self.assertEqual(result[0].opponent_present, "kobold")
        self.assertEqual(
            result[0].message,
            "This room doesn't have a sorcerer; but there is a kobold.",
        )

    def test_attack_4(self):
        self.game_state.rooms_state.cursor.creature_here = None
        result = self.command_processor.process("attack sorcerer")
        self.assertIsInstance(result[0], OpponentNotFoundGSM)
        self.assertEqual(result[0].creature_title_given, "sorcerer")
        self.assertIs(result[0].opponent_present, "")
        self.assertEqual(
            result[0].message, "This room doesn't have a sorcerer; nobody is here."
        )

    def test_attack_5(self):
        self.game_state.rooms_state.cursor.creature_here = None
        result = self.command_processor.process("attack sorcerer")
        self.assertIsInstance(result[0], OpponentNotFoundGSM)
        self.assertEqual(result[0].creature_title_given, "sorcerer")
        self.assertIs(result[0].opponent_present, "")
        self.assertEqual(
            result[0].message, "This room doesn't have a sorcerer; nobody is here."
        )

    def test_attack_vs_be_attacked_by_vs_character_death_2(self):
        results = tuple()
        while not len(results) or not isinstance(results[-1], FoeDeathGSM):
            self.setUp()
            results = self.command_processor.process("attack kobold")
            while not (
                isinstance(results[-1], CharacterDeathGSM)
                or isinstance(results[-1], FoeDeathGSM)
            ):
                results += self.command_processor.process("attack kobold")
            for index in range(0, len(results)):
                command_results = results[index]
                if isinstance(command_results, AttackHitGSM):
                    self.assertEqual(results[index].creature_title, "kobold")
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertRegex(
                        results[index].message,
                        r"Your attack on the kobold hit! You did [1-9][0-9]* "
                        + r"damage.( The kobold turns to attack!)?",
                    )
                elif isinstance(command_results, AttackMissedGSM):
                    self.assertEqual(results[index].creature_title, "kobold")
                    self.assertEqual(
                        results[index].message,
                        "Your attack on the kobold missed. It turns to attack!",
                    )
                elif isinstance(command_results, AttackedAndNotHitGSM):
                    self.assertEqual(results[index].creature_title, "kobold")
                    self.assertEqual(
                        results[index].message,
                        "The kobold attacks! Their attack misses.",
                    )
                elif isinstance(command_results, AttackedAndHitGSM):
                    self.assertEqual(results[index].creature_title, "kobold")
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertTrue(isinstance(results[index].hit_points_left, int))
                    self.assertRegex(
                        results[index].message,
                        r"The kobold attacks! Their attack hits. They did "
                        + r"[0-9]+ damage! You have [0-9]+ hit points left.",
                    )
                elif isinstance(command_results, FoeDeathGSM):
                    self.assertEqual(results[index].creature_title, "kobold")
                    self.assertRegex(results[index].message, r"The kobold is slain.")
                elif isinstance(command_results, CharacterDeathGSM):
                    self.assertRegex(results[index].message, r"You have died!")
            results_str_join = " ".join(
                command_results.__class__.__name__ for command_results in results
            )

            # Got a little clever here. The sequence of `GameStateMessage` subclass objects that are returned during
            # a combat follows a particular pattern, and any deviation from that pattern is an error. I conjoin the
            # classnames into a string and use regular expressions to parse the sequence to verify that the required
            # pattern is conformed to.

            self.assertRegex(
                results_str_join,
                r"(Attack(Hit|Missed)GSM AttackedAnd(Not)?HitGSM)+ (AttackHitGSM "
                + r"FoeDeathGSM|CharacterDeathGSM)",
            )
        self.assertIsInstance(self.game_state.rooms_state.cursor.container_here, Corpse)
        corpse_belonging_list = sorted(
            self.game_state.rooms_state.cursor.container_here.items(),
            key=operator.itemgetter(0),
        )
        self.gold_coin = self.game_state.items_state.get("Gold_Coin")
        health_potion = self.game_state.items_state.get("Health_Potion")
        short_sword = self.game_state.items_state.get("Short_Sword")
        small_leather_armor = self.game_state.items_state.get("Small_Leather_Armor")
        expected_list = [
            ("Gold_Coin", (30, self.gold_coin)),
            ("Health_Potion", (1, health_potion)),
            ("Short_Sword", (1, short_sword)),
            ("Small_Leather_Armor", (1, small_leather_armor)),
        ]
        self.assertEqual(corpse_belonging_list, expected_list)


class Test_Attack_2(unittest.TestCase):
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
        self.game_state.character_name = "Mialee"
        self.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        self.game_state.character.pick_up_item(self.items_state.get("Magic_Wand"))
        self.game_state.character.equip_wand(self.items_state.get("Magic_Wand"))

    # I'm trying to test how the specific `GameStateMessage` subclasses
    # behave but the only way to get them is to run an entire combat and
    # gamble that both a hit and a miss occur in the fight. The inner
    # loop continues til both occur or the combat ends in a death, and
    # the outer loop repeats indefinitely, but is continue'd if combat
    # ended before both show up to retry, or break'd if both objects I'm
    # testing have occurred.

    def test_attack_1(self):
        results = tuple()
        kobold = self.game_state.rooms_state.cursor.creature_here
        while True:
            self.setUp()
            if kobold.hit_points < kobold.hit_point_total:
                kobold.heal_damage(kobold.hit_point_total - kobold.hit_points)
            results = self.command_processor.process("attack kobold")
            while (
                not any(isinstance(result, AttackMissedGSM) for result in results)
                and not any(isinstance(result, AttackHitGSM) for result in results)
            ) or (
                isinstance(
                    results[-1],
                    (
                        AttackHitGSM,
                        CharacterDeathGSM,
                    ),
                )
            ):
                results += self.command_processor.process("attack kobold")
            if isinstance(
                results[-1],
                (AttackHitGSM, CharacterDeathGSM),
            ):
                continue
            else:
                break
        for index in range(0, len(results)):
            result = results[index]
            if isinstance(result, AttackMissedGSM):
                self.assertEqual(result.creature_title, "kobold")
                self.assertEqual(result.weapon_type, "wand")
                self.assertEqual(
                    result.message,
                    "A bolt of energy from your wand misses the kobold. It "
                    + "turns to attack!",
                )
            elif isinstance(result, AttackHitGSM):
                self.assertEqual(result.creature_title, "kobold")
                self.assertEqual(result.weapon_type, "wand")
                self.assertRegex(
                    result.message,
                    r"A bolt of energy from your wand hits the kobold! You "
                    + r"did \d+ damage.( The kobold turns to attack!)?",
                )
