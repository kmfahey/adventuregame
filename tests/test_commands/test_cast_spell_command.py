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
from advgame.commands.constants import SPELL_MANA_COST
from advgame.statemsgs.be_atkd import AttackedAndHitGSM, AttackedAndNotHitGSM
from advgame.statemsgs.castspl import (
    CastDamagingSpellGSM,
    CastHealingSpellGSM,
    InsufficientManaGSM,
)
from advgame.statemsgs.command import BadSyntaxGSM, ClassRestrictedGSM
from advgame.statemsgs.various import FoeDeathGSM, UnderwentHealingEffectGSM

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = ("Test_Cast_Spell",)


class Test_Cast_Spell(TestCase):
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

    def test_cast_spell1(self):
        self.command_processor.game_state.character_name = "Niath"
        self.command_processor.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("cast spell")
        self.assertIsInstance(result[0], ClassRestrictedGSM)
        self.assertEqual(result[0].command, "CAST SPELL")
        self.assertEqual(
            result[0].classes,
            (
                "mage",
                "priest",
            ),
        )
        self.assertEqual(
            result[0].message, "Only mages and priests can use the CAST SPELL command."
        )

    def test_cast_spell2(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        for bad_argument_str in (
            "cast spell at kobold",
            "cast spell at",
        ):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], BadSyntaxGSM)
            self.assertEqual(result[0].command, "CAST SPELL")
            self.assertEqual(
                result[0].message,
                "CAST SPELL command: bad syntax. Should be 'CAST\u00A0SPELL'.",
            )

    def test_cast_spell3(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        mana_point_total = self.command_processor.game_state.character.mana_point_total
        mana_spending_outcome = self.command_processor.game_state.character.spend_mana(
            mana_point_total - 4
        )
        current_mana_points = 4
        self.assertTrue(mana_spending_outcome)
        result = self.command_processor.process("cast spell")
        self.assertIsInstance(result[0], InsufficientManaGSM)
        self.assertEqual(
            result[0].current_mana_points,
            self.command_processor.game_state.character.mana_points,
        )
        self.assertEqual(
            result[0].mana_point_total,
            self.command_processor.game_state.character.mana_point_total,
        )
        self.assertEqual(result[0].spell_mana_cost, SPELL_MANA_COST)
        self.assertEqual(
            result[0].message,
            "You don't have enough mana points to cast a spell. Casting a spell costs "
            + f"{SPELL_MANA_COST} mana points. Your mana points are "
            + f"{current_mana_points}/{mana_point_total}.",
        )

    def test_cast_spell4(self):
        self.command_processor.game_state.character_name = "Mialee"
        self.command_processor.game_state.character_class = "Mage"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("cast spell")
        self.assertIsInstance(result[0], CastDamagingSpellGSM)
        self.assertEqual(result[0].creature_title, "kobold")
        self.assertIsInstance(result[0].damage_dealt, int)
        self.assertRegex(
            result[0].message,
            r"A magic missile springs from your gesturing hand and unerringly "
            + r"strikes the kobold. You have done \d+ points of damage.",
        )
        self.assertIsInstance(
            result[1],
            (
                FoeDeathGSM,
                AttackedAndNotHitGSM,
                AttackedAndHitGSM,
            ),
        )
        if not isinstance(result[1], FoeDeathGSM):
            spell_cast_count = 1
            while result[0].damage_dealt >= 20:
                self.command_processor.game_state.rooms_state.cursor.creature_here.heal_damage(
                    20
                )
                result = self.command_processor.process("cast spell")
                spell_cast_count += 1
            self.assertRegex(
                result[0].message,
                "A magic missile springs from your gesturing hand and "
                + r"unerringly strikes the kobold. You have done \d+ points of "
                + "damage. The kobold turns to attack!",
            )
            self.assertEqual(
                self.command_processor.game_state.character.mana_points
                + spell_cast_count * SPELL_MANA_COST,
                self.command_processor.game_state.character.mana_point_total,
            )

    def test_cast_spell5(self):
        self.command_processor.game_state.character_name = "Kaeva"
        self.command_processor.game_state.character_class = "Priest"
        self.game_state.game_has_begun = True
        result = self.command_processor.process("cast spell")
        self.assertIsInstance(result[0], CastHealingSpellGSM)
        self.assertRegex(result[0].message, r"You cast a healing spell on yourself.")
        self.assertIsInstance(result[1], UnderwentHealingEffectGSM)
        self.assertEqual(
            self.command_processor.game_state.character.mana_points + SPELL_MANA_COST,
            self.command_processor.game_state.character.mana_point_total,
        )
