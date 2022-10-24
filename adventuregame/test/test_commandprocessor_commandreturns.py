#!/usr/bin/python3

import math
import operator
import os
import tempfile
import unittest
import tokenize
import pprint

import iniconfig

from adventuregame import *
from .utility import *

__name__ = 'adventuregame.test_commandprocessor_commandreturns'


class test_command_processor_attack_vs_be_attacked_by(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.items_state_obj,
                                           **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.game_state_obj.character_name = "Niath"
        self.game_state_obj.character_class = "Warrior"
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get("Longsword"))
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get("Studded_Leather"))
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get("Shield"))
        self.game_state_obj.character.equip_weapon(self.items_state_obj.get("Longsword"))
        self.game_state_obj.character.equip_armor(self.items_state_obj.get("Studded_Leather"))
        self.game_state_obj.character.equip_shield(self.items_state_obj.get("Shield"))

    def test_attack_bad_usages(self):
        result = self.command_processor_obj.process("attack sorcerer")
        self.assertIsInstance(result[0], attack_command_opponent_not_found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertEqual(result[0].opponent_present, 'kobold')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; but there is a kobold.")
        self.game_state_obj.rooms_state.cursor.creature_here = None
        result = self.command_processor_obj.process("attack sorcerer")
        self.assertIsInstance(result[0], attack_command_opponent_not_found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertIs(result[0].opponent_present, '')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; nobody is here.")

    def test_attack_vs_be_attacked_by_and_character_death_and_inspect_and_loot_corpse(self):
        results = tuple()
        while not len(results) or not isinstance(results[-1], attack_command_foe_death):
            self.setUp()
            results = self.command_processor_obj.process("attack kobold")
            while not (isinstance(results[-1], be_attacked_by_command_character_death) or isinstance(results[-1], attack_command_foe_death)):
                results += self.command_processor_obj.process("attack kobold")
            for index in range(0, len(results)):
                command_results_obj = results[index]
                if isinstance(command_results_obj, attack_command_attack_hit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertRegex(results[index].message, 'Your attack on the kobold hit! You did [1-9][0-9]* damage.( The kobold turns to attack!)?')
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
                    self.assertRegex(results[index].message, 'The kobold attacks! Their attack hits. They did [0-9]+ damage! You have [0-9]+ hit points left.')
                elif isinstance(command_results_obj, attack_command_foe_death):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertRegex(results[index].message, 'The kobold is slain.')
                elif isinstance(command_results_obj, be_attacked_by_command_character_death):
                    self.assertRegex(results[index].message, 'You have died!')
            results_str_join = ' '.join(command_results_obj.__class__.__name__ for command_results_obj in results)
            self.assertRegex(results_str_join, '(attack_command_attack_(hit|missed) be_attacked_by_command_attacked_an'
                                               'd_(not_)?hit)+ (attack_command_attack_hit attack_command_foe_death|be_'
                                               'attacked_by_command_character_death)')
        self.assertIsInstance(self.game_state_obj.rooms_state.cursor.container_here, corpse)
        corpse_belonging_list = sorted(self.game_state_obj.rooms_state.cursor.container_here.items(), key=operator.itemgetter(0))
        gold_coin_obj = self.game_state_obj.items_state.get("Gold_Coin")
        health_potion_obj = self.game_state_obj.items_state.get("Health_Potion")
        short_sword_obj = self.game_state_obj.items_state.get("Short_Sword")
        small_leather_armor_obj = self.game_state_obj.items_state.get("Small_Leather_Armor")
        expected_list = [('Gold_Coin', (30, gold_coin_obj)), ('Health_Potion', (1, health_potion_obj)),
                         ('Short_Sword', (1, short_sword_obj)), ('Small_Leather_Armor', (1, small_leather_armor_obj))]
        self.assertEqual(corpse_belonging_list, expected_list)

        result, = self.command_processor_obj.process('inspect kobold corpse')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} They '
                                          'have 30 gold coins, a health potion, a short sword, and a small leather '
                                          'armor on them.')

        (potion_qty, health_potion_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Health_Potion')
        result, = self.command_processor_obj.process('take a health potion from the kobold corpse')
        self.assertIsInstance(result, take_command_item_or_items_taken)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.item_title, 'health potion')
        self.assertEqual(result.amount_taken, 1)
        self.assertEqual(result.message, 'You took a health potion from the kobold corpse.')
        self.assertTrue(self.command_processor_obj.game_state.character.inventory.contains('Health_Potion'))
        self.assertFalse(self.command_processor_obj.game_state.rooms_state.cursor.container_here.contains('Health_Potion'))
        self.assertTrue(self.command_processor_obj.game_state.character.inventory.get('Health_Potion'), (1, health_potion_obj))

        (_, gold_coin_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Gold_Coin')
        result, = self.command_processor_obj.process('take 15 gold coins from the kobold corpse')
        self.assertIsInstance(result, take_command_item_or_items_taken)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.amount_taken, 15)
        self.assertEqual(result.message, 'You took 15 gold coins from the kobold corpse.')
        self.assertTrue(self.command_processor_obj.game_state.character.have_item(gold_coin_obj))
        self.assertEqual(self.command_processor_obj.game_state.character.item_have_qty(gold_coin_obj), 15)
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.container_here.contains('Gold_Coin'))
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Gold_Coin'), (15, gold_coin_obj))

        (_, short_sword_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Short_Sword')
        result, = self.command_processor_obj.process('take one short sword from the kobold corpse')
        self.assertIsInstance(result, take_command_item_or_items_taken)

        result, = self.command_processor_obj.process('take one small leather armors from the kobold corpse') # check
        self.assertIsInstance(result, command_bad_syntax)
        self.assertEqual(result.command, 'TAKE')
        self.assertEqual(result.message, "TAKE command: bad syntax. Should be '<item name> FROM <container name>' or '<number> <item name> FROM <container name>'."),

        result, = self.command_processor_obj.process('take one small leather armor from the kobold corpses') # check
        self.assertIsInstance(result, command_bad_syntax)
        self.assertEqual(result.command, 'TAKE')
        self.assertEqual(result.message, "TAKE command: bad syntax. Should be '<item name> FROM <container name>' or '<number> <item name> FROM <container name>'."),

        result, = self.command_processor_obj.process('take one small leather armor') # check
        self.assertIsInstance(result, command_bad_syntax)
        self.assertEqual(result.command, 'TAKE')
        self.assertEqual(result.message, "TAKE command: bad syntax. Should be '<item name> FROM <container name>' or '<number> <item name> FROM <container name>'."),

        result, = self.command_processor_obj.process('take the from the kobold corpse') # check
        self.assertIsInstance(result, command_bad_syntax)
        self.assertEqual(result.command, 'TAKE')
        self.assertEqual(result.message, "TAKE command: bad syntax. Should be '<item name> FROM <container name>' or '<number> <item name> FROM <container name>'."),

        result, = self.command_processor_obj.process('take the short sword from the') # check
        self.assertIsInstance(result, command_bad_syntax)
        self.assertEqual(result.command, 'TAKE')
        self.assertEqual(result.message, "TAKE command: bad syntax. Should be '<item name> FROM <container name>' or '<number> <item name> FROM <container name>'."),

        result, = self.command_processor_obj.process('take the short sword from the sorcerer corpse') # check
        self.assertIsInstance(result, various_commands_container_not_found)
        self.assertEqual(result.container_not_found_title, 'sorcerer corpse')
        self.assertEqual(result.container_present_title, 'kobold corpse')
        self.assertEqual(result.message, "There is no sorcerer corpse here. However, there *is* a kobold corpse here.")

        container_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here # check
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = None
        result, = self.command_processor_obj.process('take the short sword from the sorcerer corpse')
        self.assertIsInstance(result, various_commands_container_not_found)
        self.assertEqual(result.container_not_found_title, 'sorcerer corpse')
        self.assertIs(result.container_present_title, None)
        self.assertEqual(result.message, "There is no sorcerer corpse here.")
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = container_obj

        result, = self.command_processor_obj.process('take 3 small leather armors from the kobold corpse')
        self.assertIsInstance(result, take_command_trying_to_take_more_than_is_present)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.item_title, 'small leather armor')
        self.assertEqual(result.amount_attempted, 3)
        self.assertEqual(result.amount_present, 1)
        self.assertEqual(result.message, "You can't take 3 small leather armors from the kobold corpse. Only 1 is there.")

        result, = self.command_processor_obj.process('take the short sword from the kobold corpse')
        self.assertIsInstance(result, take_command_item_not_found_in_container)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertIs(result.amount_attempted, math.nan)
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.item_title, 'short sword')
        self.assertEqual(result.message, "The kobold corpse doesn't have a short sword on them.")

        result, = self.command_processor_obj.process('take three short swords from the kobold corpse')
        self.assertIsInstance(result, take_command_item_not_found_in_container)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.amount_attempted, 3)
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.item_title, 'short sword')
        self.assertEqual(result.message, "The kobold corpse doesn't have any short swords on them.")

        result, = self.command_processor_obj.process('take fifteen gold coins from the kobold corpse')
        self.assertIsInstance(result, take_command_item_or_items_taken)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.amount_taken, 15)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.message, 'You took 15 gold coins from the kobold corpse.')

        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, gold_coin_obj)
        result, = self.command_processor_obj.process('take gold coins from the kobold corpse')
        self.assertIsInstance(result, take_command_item_or_items_taken)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.amount_taken, 15)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.message, 'You took 15 gold coins from the kobold corpse.')

        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, gold_coin_obj)
        result, = self.command_processor_obj.process('take gold coin from the kobold corpse')
        self.assertIsInstance(result, take_command_item_or_items_taken)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.amount_taken, 15)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.message, 'You took 15 gold coins from the kobold corpse.')

        result, = self.command_processor_obj.process('take a small leather armor from the kobold corpse')
        self.assertIsInstance(result, take_command_item_or_items_taken)
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.amount_taken, 1)
        self.assertEqual(result.item_title, 'small leather armor')
        self.assertEqual(result.message, 'You took a small leather armor from the kobold corpse.')

        result, = self.command_processor_obj.process('put 15 gold coins on the kobold corpse')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.amount_put, 15)
        self.assertEqual(result.amount_left, 45)
        self.assertEqual(result.message, "You put 15 gold coins on the kobold corpse's person. You have 45 gold coins left.")

        result, = self.command_processor_obj.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.amount_put, 1)
        self.assertEqual(result.amount_left, 44)
        self.assertEqual(result.message, "You put 1 gold coin on the kobold corpse's person. You have 44 gold coins left.")

        result, = self.command_processor_obj.process('put 43 gold coins on the kobold corpse')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.amount_put, 43)
        self.assertEqual(result.amount_left, 1)
        self.assertEqual(result.message, "You put 43 gold coins on the kobold corpse's person. You have 1 gold coin left.")

        result, = self.command_processor_obj.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'kobold corpse')
        self.assertEqual(result.container_type, 'corpse')
        self.assertEqual(result.amount_put, 1)
        self.assertEqual(result.amount_left, 0)
        self.assertEqual(result.message, "You put 1 gold coin on the kobold corpse's person. You have no more gold coins.")

        result, = self.command_processor_obj.process('put 2 gold coins on the kobold corpse')
        self.assertIsInstance(result, put_command_item_not_in_inventory)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.amount_attempted, 2)
        self.assertEqual(result.message, "You don't have any gold coins in your inventory.")

        result, = self.command_processor_obj.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result, put_command_item_not_in_inventory)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.amount_attempted, 1)
        self.assertEqual(result.message, "You don't have a gold coin in your inventory.")

        result, = self.command_processor_obj.process('take 5 gold coins from the kobold corpse')
        result, = self.command_processor_obj.process('put 10 gold coin on the kobold corpse')
        self.assertIsInstance(result, put_command_trying_to_put_more_than_you_have)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.amount_present, 5)
        self.assertEqual(result.message, "You only have 5 gold coins in your inventory.")

        result, = self.command_processor_obj.process('put 4 gold coins on the kobold corpse')
        result, = self.command_processor_obj.process('put 4 gold coins on the kobold corpse')
        self.assertIsInstance(result, put_command_trying_to_put_more_than_you_have)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.amount_present, 1)
        self.assertEqual(result.message, "You only have 1 gold coin in your inventory.")

        result, = self.command_processor_obj.process('put a gold coins on the kobold corpse')
        self.assertIsInstance(result, put_command_quantity_unclear)
        self.assertEqual(result.message, "Amount to put unclear. How many do you mean?")




    def test_inspect_also_two_take_cases(self):
        result, = self.command_processor_obj.process('inspect kobold')
        self.assertIsInstance(result, inspect_command_found_creature_here)
        self.assertEqual(result.creature_description, self.game_state_obj.rooms_state.cursor.creature_here.description)
        self.assertEqual(result.message, self.game_state_obj.rooms_state.cursor.creature_here.description)

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed and locked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed but unlocked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is '
                                          'unlocked and open. It contains 20 gold coins, a health potion, and a warhammer.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        with self.assertRaises(internal_exception):
            result, = self.command_processor_obj.process('inspect wooden chest')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is '
                                          'open. It contains 20 gold coins, a health potion, and a warhammer.')

        result, = self.command_processor_obj.process('take three short swords from the wooden chest')
        self.assertIsInstance(result, take_command_item_not_found_in_container)
        self.assertEqual(result.container_title, 'wooden chest')
        self.assertEqual(result.amount_attempted, 3)
        self.assertEqual(result.container_type, 'chest')
        self.assertEqual(result.item_title, 'short sword')
        self.assertEqual(result.message, "The wooden chest doesn't have any short swords in it.")

        result, = self.command_processor_obj.process('take 20 gold coins from the wooden chest')
        result, = self.command_processor_obj.process('put 5 gold coins in the wooden chest')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'wooden chest')
        self.assertEqual(result.container_type, 'chest')
        self.assertEqual(result.amount_put, 5)
        self.assertEqual(result.amount_left, 15)
        self.assertEqual(result.message, "You put 5 gold coins in the wooden chest. You have 15 gold coins left.")

        result, = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'wooden chest')
        self.assertEqual(result.container_type, 'chest')
        self.assertEqual(result.amount_put, 1)
        self.assertEqual(result.amount_left, 14)
        self.assertEqual(result.message, "You put 1 gold coin in the wooden chest. You have 14 gold coins left.")

        result, = self.command_processor_obj.process('put 12 gold coin in the wooden chest')
        result, = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'wooden chest')
        self.assertEqual(result.container_type, 'chest')
        self.assertEqual(result.amount_put, 1)
        self.assertEqual(result.amount_left, 1)
        self.assertEqual(result.message, "You put 1 gold coin in the wooden chest. You have 1 gold coin left.")

        result, = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result, put_command_amount_put)
        self.assertEqual(result.item_title, 'gold coin')
        self.assertEqual(result.container_title, 'wooden chest')
        self.assertEqual(result.container_type, 'chest')
        self.assertEqual(result.amount_put, 1)
        self.assertEqual(result.amount_left, 0)
        self.assertEqual(result.message, "You put 1 gold coin in the wooden chest. You have no more gold coins.")

        result, = self.command_processor_obj.process('take one short sword from the wooden chest')
        self.assertIsInstance(result, take_command_item_not_found_in_container)
        self.assertEqual(result.container_title, 'wooden chest')
        self.assertEqual(result.amount_attempted, 1)
        self.assertEqual(result.container_type, 'chest')
        self.assertEqual(result.item_title, 'short sword')
        self.assertEqual(result.message, "The wooden chest doesn't have a short sword in it.")

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is locked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is unlocked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result, = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result, inspect_command_found_container_here)
        self.assertEqual(result.container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result.is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result.is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.container_here.description}')

        result, = self.command_processor_obj.process('look at kobold')
        self.assertIsInstance(result, inspect_command_found_creature_here)
        self.assertEqual(result.creature_description, self.game_state_obj.rooms_state.cursor.creature_here.description)
        self.assertEqual(result.message, f'{self.game_state_obj.rooms_state.cursor.creature_here.description}')
