#!/usr/bin/python3

import operator
import unittest

from adventuregame import *
from adventuregame.test.testing_game_data import *

__name__ = 'adventuregame.test_command_processor_game_state_messages_a_to_eq'


class test_attack(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.game_state_obj.character_name = 'Niath'
        self.game_state_obj.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get('Longsword'))
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get('Studded_Leather'))
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get('Steel_Shield'))
        self.game_state_obj.character.equip_weapon(self.items_state_obj.get('Longsword'))
        self.game_state_obj.character.equip_armor(self.items_state_obj.get('Studded_Leather'))
        self.game_state_obj.character.equip_shield(self.items_state_obj.get('Steel_Shield'))
        (_, self.gold_coin_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Gold_Coin')

    def test_attack_1(self):
        self.command_processor_obj.process('unequip longsword')
        result = self.command_processor_obj.process('attack sorcerer')
        self.assertIsInstance(result[0], attack_command_you_have_no_weapon_or_wand_equipped)
        self.assertEqual(result[0].message, "You have no weapon equipped; you can't attack.")
        self.command_processor_obj.process('equip longsword')

    def test_attack_2(self):
        result = self.command_processor_obj.process('attack sorcerer')
        self.assertIsInstance(result[0], attack_command_opponent_not_found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertEqual(result[0].opponent_present, 'kobold')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; but there is a kobold.")

    def test_attack_3(self):
        self.game_state_obj.rooms_state.cursor.creature_here = None
        result = self.command_processor_obj.process('attack sorcerer')
        self.assertIsInstance(result[0], attack_command_opponent_not_found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertIs(result[0].opponent_present, '')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; nobody is here.")

    def test_attack_vs_be_attacked_by_vs_character_death_1(self):
        results = tuple()
        while not len(results) or not isinstance(results[-1], various_commands_foe_death):
            self.setUp()
            results = self.command_processor_obj.process('attack kobold')
            while not (isinstance(results[-1], be_attacked_by_command_character_death) or isinstance(results[-1], various_commands_foe_death)):
                results += self.command_processor_obj.process('attack kobold')
            for index in range(0, len(results)):
                command_results_obj = results[index]
                if isinstance(command_results_obj, attack_command_attack_hit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertRegex(results[index].message, r'Your attack on the kobold hit! You did [1-9][0-9]* damage.( The kobold turns to attack!)?')
                elif isinstance(command_results_obj, attack_command_attack_missed):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertEqual(results[index].message, 'Your attack on the kobold missed. It turns to attack!')
                elif isinstance(command_results_obj, be_attacked_by_command_attacked_and_not_hit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertEqual(results[index].message, 'The kobold attacks! Their attack misses.')
                elif isinstance(command_results_obj, be_attacked_by_command_attacked_and_hit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertTrue(isinstance(results[index].hit_points_left, int))
                    self.assertRegex(results[index].message, r'The kobold attacks! Their attack hits. They did [0-9]+ damage! You have [0-9]+ hit points left.')
                elif isinstance(command_results_obj, various_commands_foe_death):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertRegex(results[index].message, r'The kobold is slain.')
                elif isinstance(command_results_obj, be_attacked_by_command_character_death):
                    self.assertRegex(results[index].message, r'You have died!')
            results_str_join = ' '.join(command_results_obj.__class__.__name__ for command_results_obj in results)
            self.assertRegex(results_str_join, r'(attack_command_attack_(hit|missed) '
                                               r'be_attacked_by_command_attacked_and_(not_)?hit)+ '
                                               r'(attack_command_attack_hit various_commands_foe_death'
                                               r'|be_attacked_by_command_character_death)')
        self.assertIsInstance(self.game_state_obj.rooms_state.cursor.container_here, corpse)
        corpse_belonging_list = sorted(self.game_state_obj.rooms_state.cursor.container_here.items(), key=operator.itemgetter(0))
        self.gold_coin_obj = self.game_state_obj.items_state.get('Gold_Coin')
        health_potion_obj = self.game_state_obj.items_state.get('Health_Potion')
        short_sword_obj = self.game_state_obj.items_state.get('Short_Sword')
        small_leather_armor_obj = self.game_state_obj.items_state.get('Small_Leather_Armor')
        expected_list = [('Gold_Coin', (30, self.gold_coin_obj)), ('Health_Potion', (1, health_potion_obj)),
                         ('Short_Sword', (1, short_sword_obj)), ('Small_Leather_Armor', (1, small_leather_armor_obj))]
        self.assertEqual(corpse_belonging_list, expected_list)


class test_begin_game_command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)

    def test_begin_game_1(self):
        result = self.command_processor_obj.process('begin game')
        self.assertIsInstance(result[0], begin_game_command_name_or_class_not_set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "You need to set your character name and class before you begin the game. Use SET NAME <name> to set your name and SET CLASS <Warrior, Thief, Mage or Priest> to select your class.")

    def test_begin_game_2(self):
        self.command_processor_obj.process('set class to Warrior')
        result = self.command_processor_obj.process('begin game')
        self.assertIsInstance(result[0], begin_game_command_name_or_class_not_set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, 'Warrior')
        self.assertEqual(result[0].message, "You need to set your character name before you begin the game. Use SET NAME <name> to set your name.")

    def test_begin_game_3(self):
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('begin game')
        self.assertIsInstance(result[0], begin_game_command_name_or_class_not_set)
        self.assertEqual(result[0].character_name, 'Kerne')
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "You need to set your character class before you begin the game. Use SET CLASS <Warrior, Thief, Mage or Priest> to select your class.")

    def test_begin_game_4(self):
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('begin game now')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN GAME'.")

    def test_begin_game_5(self):
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('begin game')
        self.assertIsInstance(result[0], begin_game_command_game_begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor_obj.game_state.game_has_begun)


class test_cast_spell_command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)

    def test_cast_spell1(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        result = self.command_processor_obj.process('cast spell')
        self.assertIsInstance(result[0], command_class_restricted)
        self.assertEqual(result[0].command, 'CAST SPELL')
        self.assertEqual(result[0].classes, ('mage', 'priest',))
        self.assertEqual(result[0].message, 'Only mages and priests can use the CAST SPELL command.')

    def test_cast_spell2(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        for bad_argument_str in ('cast spell at kobold', 'cast spell at',):
            result = self.command_processor_obj.process(bad_argument_str)
            self.assertIsInstance(result[0], command_bad_syntax)
            self.assertEqual(result[0].command, 'CAST SPELL')
            self.assertEqual(result[0].message, "CAST SPELL command: bad syntax. Should be 'CAST SPELL'.")

    def test_cast_spell3(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        mana_point_total = self.command_processor_obj.game_state.character.mana_point_total
        mana_spending_outcome = self.command_processor_obj.game_state.character.spend_mana(mana_point_total - 4)
        current_mana_points = 4
        self.assertTrue(mana_spending_outcome)
        result = self.command_processor_obj.process('cast spell')
        self.assertIsInstance(result[0], cast_spell_command_insuffient_mana)
        self.assertEqual(result[0].current_mana_points, self.command_processor_obj.game_state.character.mana_points)
        self.assertEqual(result[0].mana_point_total, self.command_processor_obj.game_state.character.mana_point_total)
        self.assertEqual(result[0].spell_mana_cost, Spell_Mana_Cost)
        self.assertEqual(result[0].message,  "You don't have enough mana points to cast a spell. Casting a spell costs "
                                            f'{Spell_Mana_Cost} mana points. Your mana points are {current_mana_points}/'
                                            f'{mana_point_total}.')

    def test_cast_spell4(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        result = self.command_processor_obj.process('cast spell')
        self.assertIsInstance(result[0], cast_spell_command_cast_damaging_spell)
        self.assertEqual(result[0].creature_title, 'kobold')
        self.assertIsInstance(result[0].damage_dealt, int)
        self.assertRegex(result[0].message, r'A magic missile springs from your gesturing hand and unerringly strikes '
                                            r'the kobold. You have done \d+ points of damage.')
        self.assertIsInstance(result[1], (various_commands_foe_death, be_attacked_by_command_attacked_and_not_hit,
                                          be_attacked_by_command_attacked_and_hit))
        if isinstance(result[1], be_attacked_by_command_attacked_and_hit) and len(result) == 3:
            self.assertIsInstance(result[2], be_attacked_by_command_character_death)

    def test_cast_spell5(self):
        self.command_processor_obj.game_state.character_name = 'Kaeva'
        self.command_processor_obj.game_state.character_class = 'Priest'
        self.game_state_obj.game_has_begun = True
        result = self.command_processor_obj.process('cast spell')
        self.assertIsInstance(result[0], cast_spell_command_cast_healing_spell)
        self.assertRegex(result[0].message, r'You cast a healing spell on yourself.')
        self.assertIsInstance(result[1], various_commands_underwent_healing_effect)


class test_close_command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        self.chest_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here
        self.chest_obj.is_closed = True
        self.chest_obj.is_locked = False
        self.chest_title = self.chest_obj.title
        self.door_obj = self.command_processor_obj.game_state.rooms_state.cursor.north_exit
        self.door_obj.is_closed = True
        self.door_title = self.door_obj.title

    def test_close_1(self):
        result = self.command_processor_obj.process('close')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'CLOSE')
        self.assertEqual(result[0].message, "CLOSE command: bad syntax. Should be 'CLOSE <door name>' or "
                                            "'CLOSE <chest name>'."),

    def test_close_2(self):
        result = self.command_processor_obj.process(f'close {self.chest_title}')
        self.assertIsInstance(result[0], close_command_object_is_already_closed)
        self.assertEqual(result[0].target_obj, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already closed.')
        self.assertTrue(self.chest_obj.is_closed)

    def test_close_3(self):
        self.chest_obj.is_closed = False
        result = self.command_processor_obj.process(f'close {self.chest_title}')
        self.assertIsInstance(result[0], close_command_object_has_been_closed)
        self.assertEqual(result[0].target_obj, self.chest_title)
        self.assertEqual(result[0].message, f'You have closed the {self.chest_title}.')
        self.assertTrue(self.chest_obj.is_closed)

    def test_close_5(self):
        result = self.command_processor_obj.process('close west door')
        self.assertIsInstance(result[0], close_command_object_to_close_not_here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to close.'),

    def test_close_6(self):
        result = self.command_processor_obj.process(f'close {self.door_title}')
        self.assertIsInstance(result[0], close_command_object_is_already_closed)
        self.assertEqual(result[0].target_obj, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already closed.')
        self.assertTrue(self.door_obj.is_closed)

    def test_close_7(self):
        self.door_obj.is_closed = False
        result = self.command_processor_obj.process(f'close {self.door_title}')
        self.assertIsInstance(result[0], close_command_object_has_been_closed)
        self.assertEqual(result[0].target_obj, self.door_title)
        self.assertEqual(result[0].message, f'You have closed the {self.door_title}.')
        self.assertTrue(self.door_obj.is_closed)


class test_command_processor_process(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)

    def test_command_not_recognized_in_pregame(self):
        result = self.command_processor_obj.process('juggle')
        self.assertIsInstance(result[0], command_not_recognized)
        self.assertEqual(result[0].command, 'juggle')
        self.assertEqual(result[0].allowed_commands, {'begin_game', 'set_name', 'quit', 'set_class', 'reroll'})
        self.assertEqual(result[0].message, "Command 'juggle' not recognized. Commands allowed before game start are "
                                            "BEGIN GAME, QUIT, REROLL, SET CLASS, and SET NAME.")

    def test_command_not_recognized_during_game(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.command_processor_obj.game_state.game_has_begun = True
        result = self.command_processor_obj.process('juggle')
        self.assertIsInstance(result[0], command_not_recognized)
        self.assertEqual(result[0].command, 'juggle')
        self.assertEqual(result[0].allowed_commands, {'attack', 'cast_spell', 'close', 'drink', 'drop', 'equip', 'exit',
                                                      'inventory', 'leave', 'look_at', 'lock', 'inspect', 'open', 
                                                      'pick_lock', 'pick_up', 'put', 'quit', 'status', 'take', 
                                                      'unequip', 'unlock'})
        self.assertEqual(result[0].message, "Command 'juggle' not recognized. Commands allowed during the game are "
                                            "ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, EXIT, INSPECT, INVENTORY, "
                                            "LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, QUIT, STATUS, TAKE, "
                                            "UNEQUIP, and UNLOCK.")

    def test_command_not_allowed_in_pregame(self):
        result = self.command_processor_obj.process('attack kobold')
        self.assertIsInstance(result[0], command_not_allowed_now)
        self.assertEqual(result[0].command, 'attack')
        self.assertEqual(result[0].allowed_commands, {'begin_game', 'reroll', 'set_name', 'quit', 'set_class'})
        self.assertEqual(result[0].message, "Command 'attack' not allowed before game start. Commands allowed before "
                                            "game start are BEGIN GAME, QUIT, REROLL, SET CLASS, and SET NAME.")

    def test_command_not_allowed_during_game(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.command_processor_obj.game_state.game_has_begun = True
        result = self.command_processor_obj.process('reroll')
        self.assertIsInstance(result[0], command_not_allowed_now)
        self.assertEqual(result[0].command, 'reroll')
        self.assertEqual(result[0].allowed_commands, {'attack', 'cast_spell', 'close', 'drink', 'drop', 'equip', 'exit',
                                                      'inventory', 'leave', 'look_at', 'lock', 'inspect', 'open', 
                                                      'pick_lock', 'pick_up', 'quit', 'put', 'quit', 'status', 'take', 
                                                      'unequip', 'unlock'})
        self.assertEqual(result[0].message, "Command 'reroll' not allowed during the game. Commands allowed during "
                                            "the game are ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, EXIT, "
                                            "INSPECT, INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, "
                                            "QUIT, STATUS, TAKE, UNEQUIP, and UNLOCK.")


class test_drink_command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj, self.containers_state_obj,
                                         self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)

    def test_drink1(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        for bad_argument_str in ('drink', 'drink the', 'drink 2 mana potion', 'drink 1 mana potions'):
            result = self.command_processor_obj.process(bad_argument_str)
            self.assertIsInstance(result[0], command_bad_syntax)
            self.assertEqual(result[0].command, 'DRINK')
            self.assertEqual(result[0].message, "DRINK command: bad syntax. Should be 'DRINK [THE] <potion name>'.")

    def test_drink2(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        result = self.command_processor_obj.process('drink health potion')
        self.assertIsInstance(result[0], drink_command_item_not_in_inventory)
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].message, "You don't have a health potion in your inventory.")

    def test_drink3(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        health_potion_obj = self.command_processor_obj.game_state.items_state.get('Health_Potion')
        self.command_processor_obj.game_state.character.pick_up_item(health_potion_obj)
        self.command_processor_obj.game_state.character.take_damage(10)
        result = self.command_processor_obj.process('drink health potion')
        self.assertIsInstance(result[0], various_commands_underwent_healing_effect)
        self.assertEqual(result[0].amount_healed, 10)
        self.assertRegex(result[0].message, r"You regained 10 hit points. You're fully healed! Your hit points are (\d+)/\1.")

    def test_drink4(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        health_potion_obj = self.command_processor_obj.game_state.items_state.get('Health_Potion')
        self.command_processor_obj.game_state.character.pick_up_item(health_potion_obj)
        self.command_processor_obj.game_state.character.take_damage(30)
        result = self.command_processor_obj.process('drink health potion')
        self.assertEqual(health_potion_obj.hit_points_recovered, 20)
        self.assertIsInstance(result[0], various_commands_underwent_healing_effect)
        self.assertEqual(result[0].amount_healed, 20)
        self.assertRegex(result[0].message, r'You regained 20 hit points. Your hit points are (?!(\d+)/\1)\d+/\d+.')

    def test_drink5(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        health_potion_obj = self.command_processor_obj.game_state.items_state.get('Health_Potion')
        self.command_processor_obj.game_state.character.pick_up_item(health_potion_obj)
        result = self.command_processor_obj.process('drink health potion')
        self.assertIsInstance(result[0], various_commands_underwent_healing_effect)
        self.assertEqual(result[0].amount_healed, 0)
        self.assertRegex(result[0].message, r"You didn't regain any hit points. Your hit points are \d+/\d+.")

    def test_drink6(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        mana_potion_obj = self.command_processor_obj.game_state.items_state.get('Mana_Potion')
        self.command_processor_obj.game_state.character.pick_up_item(mana_potion_obj)
        self.command_processor_obj.game_state.character.spend_mana(10)
        result = self.command_processor_obj.process('drink mana potion')
        self.assertEqual(mana_potion_obj.mana_points_recovered, 20)
        self.assertIsInstance(result[0], drink_command_drank_mana_potion)
        self.assertEqual(result[0].amount_regained, 10)
        self.assertRegex(result[0].message, r'You regained 10 mana points. You have full mana points! Your mana points are (\d+)/\1.')

    def test_drink7(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        mana_potion_obj = self.command_processor_obj.game_state.items_state.get('Mana_Potion')
        mana_potion_obj.mana_points_recovered = 11
        self.command_processor_obj.game_state.character.pick_up_item(mana_potion_obj)
        self.command_processor_obj.game_state.character.spend_mana(15)
        result = self.command_processor_obj.process('drink mana potion')
        self.assertEqual(mana_potion_obj.mana_points_recovered, 11)
        self.assertIsInstance(result[0], drink_command_drank_mana_potion)
        self.assertEqual(result[0].amount_regained, 11)
        self.assertRegex(result[0].message, r'You regained 11 mana points. Your mana points are (?!(\d+)/\1)\d+/\d+.')

    def test_drink8(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        mana_potion_obj = self.command_processor_obj.game_state.items_state.get('Mana_Potion')
        self.command_processor_obj.game_state.character.pick_up_item(mana_potion_obj)
        result = self.command_processor_obj.process('drink mana potion')
        self.assertEqual(mana_potion_obj.mana_points_recovered, 20)
        self.assertIsInstance(result[0], drink_command_drank_mana_potion)
        self.assertEqual(result[0].amount_regained, 0)
        self.assertRegex(result[0].message, r"You didn't regain any mana points. Your mana points are (\d+)/\1.")

    def test_drink9(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        mana_potion_obj = self.command_processor_obj.game_state.items_state.get('Mana_Potion')
        self.command_processor_obj.game_state.character.pick_up_item(mana_potion_obj)
        result = self.command_processor_obj.process('drink mana potion')
        self.assertIsInstance(result[0], drink_command_drank_mana_potion_when_not_a_spellcaster)
        self.assertEqual(result[0].message, 'You feel a little strange, but otherwise nothing happens.')

    def test_drink10(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        gold_coin_obj = self.command_processor_obj.game_state.items_state.get('Gold_Coin')
        self.command_processor_obj.game_state.character.pick_up_item(gold_coin_obj)
        result = self.command_processor_obj.process('drink gold coin')
        self.assertIsInstance(result[0], drink_command_item_not_drinkable)
        self.assertEqual(result[0].message, 'A gold coin is not drinkable.')

    def test_drink11(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        mana_potion_obj = self.command_processor_obj.game_state.items_state.get('Mana_Potion')
        self.command_processor_obj.game_state.character.pick_up_item(mana_potion_obj)
        result = self.command_processor_obj.process('drink 3 mana potions')
        self.assertIsInstance(result[0], drink_command_tried_to_drink_more_than_possessed)
        self.assertEqual(result[0].message, "You can't drink 3 mana potions. You only have 1 of them.")


class test_drop_command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        gold_coin_obj = self.items_state_obj.get('Gold_Coin')
        self.command_processor_obj.game_state.character.pick_up_item(gold_coin_obj, qty=30)

    def test_drop_1(self):
        result = self.command_processor_obj.process('drop the')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'DROP')
        self.assertEqual(result[0].message, "DROP command: bad syntax. Should be 'DROP <item name>' or 'DROP <number> <item name>'."),

    def test_drop_2(self):
        result = self.command_processor_obj.process('drop a gold coins')  # check
        self.assertIsInstance(result[0], drop_command_quantity_unclear)
        self.assertEqual(result[0].message, 'Amount to drop unclear. How many do you mean?')

    def test_drop_3(self):
        result = self.command_processor_obj.process('drop a mana potion')  # check
        self.assertIsInstance(result[0], drop_command_trying_to_drop_item_you_dont_have)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].message, "You don't have a mana potion in your inventory.")

    def test_drop_4(self):
        result = self.command_processor_obj.process('drop 45 gold coins')  # check
        self.assertIsInstance(result[0], drop_command_trying_to_drop_more_than_you_have)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 45)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, "You can't drop 45 gold coins. You only have 30 gold coins in your inventory.")

    def test_drop_5(self):
        result = self.command_processor_obj.process('drop 15 gold coins')  # check
        self.assertIsInstance(result[0], drop_command_dropped_item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 15)
        self.assertEqual(result[0].amount_on_floor, 15)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, 'You dropped 15 gold coins. You see 15 gold coins here. You have 15 gold coins left.')

        result = self.command_processor_obj.process('drop 14 gold coins')  # check
        self.assertIsInstance(result[0], drop_command_dropped_item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 14)
        self.assertEqual(result[0].amount_on_floor, 29)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, 'You dropped 14 gold coins. You see 29 gold coins here. You have 1 gold coin left.')

    def test_drop_6(self):
        self.command_processor_obj.process('pick up 29 gold coins')  # check
        result = self.command_processor_obj.process('drop 1 gold coin')  # check
        self.assertIsInstance(result[0], drop_command_dropped_item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 29)
        self.assertEqual(result[0].message, 'You dropped a gold coin. You see a gold coin here. You have 29 gold coins left.')


class test_equip_command_1(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        self.scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        self.shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        self.magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')
        self.magic_wand_2_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand_2')
        self.command_processor_obj.game_state.character_name = 'Arliss'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True
        self.command_processor_obj.game_state.character.pick_up_item(self.longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.shield_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.magic_wand_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.magic_wand_2_obj)

    def test_equip_1(self):
        self.command_processor_obj.game_state.character_name = 'Arliss'
        self.command_processor_obj.game_state.character_class = 'Mage'
        self.game_state_obj.game_has_begun = True

        result = self.command_processor_obj.process('equip')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'EQUIP')
        self.assertEqual(result[0].message, "EQUIP command: bad syntax. Should be 'EQUIP <armor name>', "
                                            "'EQUIP <shield name>', 'EQUIP <wand name>', or 'EQUIP <weapon name>'.")

        result = self.command_processor_obj.process('drop longsword')
        result = self.command_processor_obj.process('equip longsword')
        self.assertIsInstance(result[0], equip_command_no_such_item_in_inventory)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].message, "You don't have a longsword in your inventory.")

    def test_equip_2(self):
        result = self.command_processor_obj.process('equip longsword')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "Mages can't wield longswords.")

    def test_equip_3(self):
        result = self.command_processor_obj.process('equip scale mail armor')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertEqual(result[0].message, "Mages can't wear scale mail armor.")

    def test_equip_4(self):
        result = self.command_processor_obj.process('equip steel shield')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertEqual(result[0].message, "Mages can't carry steel shields.")

    def test_equip_5(self):
        result = self.command_processor_obj.process('equip magic wand')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"^You're now using a magic wand. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")

    def test_equip_6(self):
        self.command_processor_obj.process('equip magic wand')
        result = self.command_processor_obj.process('equip magic wand 2')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertEqual(result[0].message, "You're no longer using a magic wand. You now can't attack.")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'magic wand 2')
        self.assertEqual(result[1].item_type, 'wand')
        self.assertRegex(result[1].message, r"^You're now using a magic wand 2. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")


class test_equip_command_2(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config_obj = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config_obj = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.buckler_obj = self.command_processor_obj.game_state.items_state.get('Buckler')
        self.longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        self.mace_obj = self.command_processor_obj.game_state.items_state.get('Mace')
        self.magic_wand_2_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand_2')
        self.magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')
        self.scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        self.shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        self.studded_leather_obj = self.command_processor_obj.game_state.items_state.get('Studded_Leather')
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        self.command_processor_obj.game_state.character.pick_up_item(self.mace_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.studded_leather_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.buckler_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.shield_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.magic_wand_obj)

    def test_equip_2(self):
        result = self.command_processor_obj.process('equip longsword')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertRegex(result[0].message, r"^You're now wielding a longsword. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")
        result = self.command_processor_obj.process('equip mace')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "You're no longer wielding a longsword. You now can't attack.")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'mace')
        self.assertEqual(result[1].item_type, 'weapon')
        self.assertRegex(result[1].message, r"^You're now wielding a mace. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")

    def test_equip_3(self):
        result = self.command_processor_obj.process('equip scale mail armor')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertRegex(result[0].message, r"^You're now wearing scale mail armor. Your armor class is \d+.$")
        result = self.command_processor_obj.process('equip studded leather armor')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertRegex(result[0].message, r"^You're no longer wearing scale mail armor. Your armor class is \d+.$")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'studded leather armor')
        self.assertEqual(result[1].item_type, 'armor')
        self.assertRegex(result[1].message, r"^You're now wearing studded leather armor. Your armor class is \d+.$")

    def test_equip_4(self):
        result = self.command_processor_obj.process('equip steel shield')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertRegex(result[0].message, r"^You're now carrying a steel shield. Your armor class is \d+.$")
        result = self.command_processor_obj.process('equip buckler')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertRegex(result[0].message, r"^You're no longer carrying a steel shield. Your armor class is \d+.$")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'buckler')
        self.assertEqual(result[1].item_type, 'shield')
        self.assertRegex(result[1].message, r"^You're now carrying a buckler. Your armor class is [\d+-]+.$")

    def test_equip_5(self):
        result = self.command_processor_obj.process('equip magic wand')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].message, "Warriors can't use magic wands.")
