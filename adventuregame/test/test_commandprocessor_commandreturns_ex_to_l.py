#!/usr/bin/python3

import math
import operator
import unittest
import sys

from adventuregame import *
from adventuregame.test.utility import *

__name__ = 'adventuregame.test_commandprocessor_commandreturns_ex_to_l'


class test_exit(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_ini_config_obj.sections['Wooden_Chest_1']['contents'] = '[20xGold_Coin,1xWarhammer,1xMana_Potion,1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]'
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'

    def test_exit1(self):
        result = self.command_processor_obj.process('exit')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'EXIT')
        self.assertEqual(result[0].message, "EXIT command: bad syntax. Should be 'EXIT USING <compass direction> DOOR' "
                                            "or 'EXIT USING <compass direction> DOORWAY'.")

    def test_exit2(self):
        result = self.command_processor_obj.process('exit using')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'EXIT')
        self.assertEqual(result[0].message, "EXIT command: bad syntax. Should be 'EXIT USING <compass direction> DOOR' "
                                            "or 'EXIT USING <compass direction> DOORWAY'.")

    def test_exit3(self):
        result = self.command_processor_obj.process('exit using north')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'EXIT')
        self.assertEqual(result[0].message, "EXIT command: bad syntax. Should be 'EXIT USING <compass direction> DOOR' "
                                            "or 'EXIT USING <compass direction> DOORWAY'.")

    def test_exit4(self):
        result = self.command_processor_obj.process('exit using west door')
        self.assertIsInstance(result[0], various_commands_door_not_present)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].message, 'This room does not have a west door.')

    def test_exit5(self):
        result = self.command_processor_obj.process('exit using north door')
        self.assertIsInstance(result[0], exit_command_exitted_room)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'You leave the room via the north door.')
        self.assertEqual(self.command_processor_obj.game_state.rooms_state.cursor.internal_name, 'Room_1,2')



class test_inspect_command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)


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
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get('Longsword'))
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get('Studded_Leather'))
        self.game_state_obj.character.pick_up_item(self.items_state_obj.get('Steel_Shield'))
        self.game_state_obj.character.equip_weapon(self.items_state_obj.get('Longsword'))
        self.game_state_obj.character.equip_armor(self.items_state_obj.get('Studded_Leather'))
        self.game_state_obj.character.equip_shield(self.items_state_obj.get('Steel_Shield'))
        (_, self.gold_coin_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Gold_Coin')


    def test_inspect_1(self):
        result = self.command_processor_obj.process('inspect kobold')
        self.assertIsInstance(result[0], inspect_command_found_creature_here)
        self.assertEqual(result[0].creature_description, self.game_state_obj.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, self.game_state_obj.rooms_state.cursor.creature_here.description)


    def test_inspect_1(self):
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = \
            self.command_processor_obj.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor_obj.process('inspect kobold corpse')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} They '
                                          'have 30 gold coins, a health potion, a short sword, and a small leather '
                                          'armor on them.')


    def test_inspect_2(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed and locked.')


    def test_inspect_3(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed but unlocked.')


    def test_inspect_4(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is '
                                          'unlocked and open. It contains 20 gold coins, a mana potion, and a warhammer.')


    def test_inspect_5(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        with self.assertRaises(internal_exception):
            result = self.command_processor_obj.process('inspect wooden chest')


    def test_inspect_6(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed.')


    def test_inspect_7(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is '
                                             'open. It contains 20 gold coins, a mana potion, and a warhammer.')


    def test_inspect_8(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is locked.')


    def test_inspect_9(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is unlocked.')


    def test_inspect_10(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description}')


    def test_inspect_11(self):
        result = self.command_processor_obj.process('look at kobold')
        self.assertIsInstance(result[0], inspect_command_found_creature_here)
        self.assertEqual(result[0].creature_description, self.game_state_obj.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.creature_here.description}')




class test_inspect(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_ini_config_obj.sections['Wooden_Chest_1']['contents'] = '[20xGold_Coin,1xWarhammer,1xMana_Potion,1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]'
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'

    def test_inspect_1(self):
        result = self.command_processor_obj.process('inspect')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_2(self):
        result = self.command_processor_obj.process('inspect on')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_3(self):
        result = self.command_processor_obj.process('inspect in')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_4(self):
        result = self.command_processor_obj.process('inspect mana potion in')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_5(self):
        result = self.command_processor_obj.process('inspect health potion on')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_6(self):
        result = self.command_processor_obj.process('inspect health potion on wooden chest')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_7(self):
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = \
            self.command_processor_obj.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor_obj.process('inspect mana potion in kobold corpse')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_7(self):
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor_obj.process('inspect mana potion in wooden chest')
        self.assertIsInstance(result[0], various_commands_container_not_found)
        self.assertEqual(result[0].container_not_found_title, 'wooden chest')
        self.assertEqual(result[0].message, 'There is no wooden chest here.')

    def test_inspect_8(self):
        result = self.command_processor_obj.process('inspect gold coin in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 20)
        self.assertEqual(result[0].item_description, 'A small shiny gold coin imprinted with an indistinct bust on one '
                                                     'side and a worn state seal on the other.')
        self.assertEqual(result[0].message, 'A small shiny gold coin imprinted with an indistinct bust on one side and '
                                            'a worn state seal on the other. You see 20 here.')

    def test_inspect_9(self):
        result = self.command_processor_obj.process('inspect warhammer in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A heavy hammer with a heavy iron head with a tapered striking '
                                                     'point and a long leather-wrapped haft. Its attack bonus is +0 '
                                                     'and its damage is 1d8. Warriors and priests can use this.')
        self.assertEqual(result[0].message, 'A heavy hammer with a heavy iron head with a tapered striking point and '
                                            'a long leather-wrapped haft. Its attack bonus is +0 and its damage is 1d8.'
                                            ' Warriors and priests can use this.')

    def test_inspect_10(self):
        result = self.command_processor_obj.process('inspect steel shield in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A broad panel of leather-bound steel with a metal rim that is '
                                                     'useful for sheltering behind. Its armor bonus is +2. Warriors '
                                                     'and priests can use this.')
        self.assertEqual(result[0].message, 'A broad panel of leather-bound steel with a metal rim that is useful for '
                                            'sheltering behind. Its armor bonus is +2. Warriors and priests can use '
                                            'this.')

    def test_inspect_11(self):
        result = self.command_processor_obj.process('inspect steel shield in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A broad panel of leather-bound steel with a metal rim that is '
                                                     'useful for sheltering behind. Its armor bonus is +2. Warriors '
                                                     'and priests can use this.')
        self.assertEqual(result[0].message, 'A broad panel of leather-bound steel with a metal rim that is useful for '
                                            'sheltering behind. Its armor bonus is +2. Warriors and priests can use '
                                            'this.')

    def test_inspect_12(self):
        result = self.command_processor_obj.process('inspect mana potion in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A small, stoppered bottle that contains a pungeant but drinkable '
                                                     'blue liquid with a discernable magic aura. It restores 20 mana '
                                                     'points.')
        self.assertEqual(result[0].message, 'A small, stoppered bottle that contains a pungeant but drinkable blue '
                                            'liquid with a discernable magic aura. It restores 20 mana points.')

    def test_inspect_13(self):
        result = self.command_processor_obj.process('inspect health potion in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A small, stoppered bottle that contains a pungeant but drinkable '
                                                     'red liquid with a discernable magic aura. It restores 20 hit '
                                                     'points.')
        self.assertEqual(result[0].message, 'A small, stoppered bottle that contains a pungeant but drinkable red '
                                            'liquid with a discernable magic aura. It restores 20 hit points.')

    def test_inspect_14(self):
        result = self.command_processor_obj.process('inspect north door')
        self.assertIsInstance(result[0], inspect_command_found_door_or_doorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is set into the north wall of the room. This door is made of '
                                            'wooden planks secured together with iron divots. It is closed but '
                                            'unlocked.')

    def test_inspect_15(self):
        self.command_processor_obj.game_state.rooms_state.cursor.north_exit.is_locked = True
        result = self.command_processor_obj.process('inspect north door')
        self.assertIsInstance(result[0], inspect_command_found_door_or_doorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is set into the north wall of the room. This door is made of '
                                            'wooden planks secured together with iron divots. It is closed and '
                                            'locked.')

    def test_inspect_16(self):
        self.command_processor_obj.game_state.rooms_state.cursor.north_exit.is_closed = False
        result = self.command_processor_obj.process('inspect north door')
        self.assertIsInstance(result[0], inspect_command_found_door_or_doorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is set into the north wall of the room. This door is made of '
                                            'wooden planks secured together with iron divots. It is open.')

    def test_inspect_17(self):
        self.command_processor_obj.game_state.rooms_state.cursor.north_exit.is_closed = False
        result = self.command_processor_obj.process('inspect west door')
        self.assertIsInstance(result[0], various_commands_door_not_present)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].message, 'This room does not have a west exit.')

    def test_inspect_18(self):
        self.command_processor_obj.game_state.rooms_state.move(north=True)
        result = self.command_processor_obj.process('inspect east doorway')
        self.assertIsInstance(result[0], inspect_command_found_door_or_doorway)
        self.assertEqual(result[0].compass_dir, 'east')
        self.assertEqual(result[0].message, 'This doorway is set into the east wall of the room. This open doorway is '
                                            'outlined by a stone arch set into the wall.')

    def test_inspect_19(self):
        self.command_processor_obj.game_state.character.pick_up_item(
            self.command_processor_obj.game_state.items_state.get('Longsword'))
        result = self.command_processor_obj.process('inspect longsword in inventory')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A hefty sword with a long blade, a broad hilt and a leathern '
                                                     'grip. Its attack bonus is +0 and its damage is 1d8. Warriors can '
                                                     'use this.')
        self.assertEqual(result[0].message, 'A hefty sword with a long blade, a broad hilt and a leathern grip. Its '
                                            'attack bonus is +0 and its damage is 1d8. Warriors can use this.')

    def test_inspect_19(self):
        self.command_processor_obj.game_state.character.pick_up_item(
            self.command_processor_obj.game_state.items_state.get('Magic_Wand'))
        result = self.command_processor_obj.process('inspect magic wand in inventory')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A palpably magical tapered length of polished ash wood tipped '
                                                     'with a glowing red carnelian gem. Its attack bonus is +3 and '
                                                     'its damage is 3d8+5. Mages can use this.')
        self.assertEqual(result[0].message, 'A palpably magical tapered length of polished ash wood tipped with a '
                                            'glowing red carnelian gem. Its attack bonus is +3 and its damage is '
                                            '3d8+5. Mages can use this.')



class test_inventory(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state_obj = items_state(**self.items_ini_config_obj.sections)
        self.doors_state_obj = doors_state(**self.doors_ini_config_obj.sections)
        self.containers_ini_config_obj.sections['Wooden_Chest_1']['contents'] = ('[20xGold_Coin,1xWarhammer,'
                                                                                 '1xMana_Potion,1xHealth_Potion,'
                                                                                 '1xSteel_Shield,1xScale_Mail,'
                                                                                 '1xMagic_Wand]')
        self.containers_state_obj = containers_state(self.items_state_obj, **self.containers_ini_config_obj.sections)
        self.creatures_state_obj = creatures_state(self.items_state_obj, **self.creatures_ini_config_obj.sections)
        self.rooms_state_obj = rooms_state(self.creatures_state_obj, self.containers_state_obj, self.doors_state_obj,
                                           self.items_state_obj, **self.rooms_ini_config_obj.sections)
        self.game_state_obj = game_state(self.rooms_state_obj, self.creatures_state_obj,
                                                          self.containers_state_obj, self.doors_state_obj, self.items_state_obj)
        self.command_processor_obj = command_processor(self.game_state_obj)
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        self.scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        self.shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        self.magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')
        mana_potion_obj = self.command_processor_obj.game_state.items_state.get('Mana_Potion')
        gold_coin_obj = self.command_processor_obj.game_state.items_state.get('Gold_Coin')
        self.command_processor_obj.game_state.character.pick_up_item(longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.shield_obj)
        self.command_processor_obj.game_state.character.pick_up_item(self.magic_wand_obj)
        self.command_processor_obj.game_state.character.pick_up_item(mana_potion_obj, qty=2)
        self.command_processor_obj.game_state.character.pick_up_item(gold_coin_obj, qty=30)

    def test_inventory1(self):
        result = self.command_processor_obj.process('inventory show')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'INVENTORY')
        self.assertEqual(result[0].message, "INVENTORY command: bad syntax. Should be 'INVENTORY'.")

    def test_inventory2(self):
        result = self.command_processor_obj.process('inventory')
        self.assertIsInstance(result[0], inventory_command_display_inventory)
        self.assertEqual(tuple(map(operator.itemgetter(0), result[0].inventory_contents)), (30, 1, 1, 2, 1, 1))
        self.assertIsInstance(result[0].inventory_contents[0][1], coin)
        self.assertIsInstance(result[0].inventory_contents[1][1], weapon)
        self.assertIsInstance(result[0].inventory_contents[2][1], wand)
        self.assertIsInstance(result[0].inventory_contents[3][1], consumable)
        self.assertIsInstance(result[0].inventory_contents[4][1], armor)
        self.assertIsInstance(result[0].inventory_contents[5][1], shield)
        self.assertEqual(result[0].message, 'You have 30 gold coins, a longsword, a magic wand, 2 mana potions, a suit '
                                            'of scale mail armor, and a steel shield in your inventory.')



class test_lock_command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Chests_Ini_Config_Text)
        self.items_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Items_Ini_Config_Text)
        self.doors_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Doors_Ini_Config_Text)
        self.creatures_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Creatures_Ini_Config_Text)
        self.rooms_ini_config_obj = create_temp_ini_file_and_instance_IniConfig(Rooms_Ini_Config_Text)

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
        self.door_obj = self.command_processor_obj.game_state.rooms_state.cursor.north_exit
        self.door_obj.is_locked = True
        self.door_title = self.command_processor_obj.game_state.rooms_state.cursor.north_exit.title
        self.chest_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here
        self.chest_obj.is_locked = False
        self.chest_title = self.chest_obj.title

    def test_lock_1(self):
        result = self.command_processor_obj.process('lock')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'LOCK')
        self.assertEqual(result[0].message, "LOCK command: bad syntax. Should be 'LOCK <door name>' or "
                                            "'LOCK <chest name>'."),

    def test_lock_2(self):
        result = self.command_processor_obj.process('lock west door')
        self.assertIsInstance(result[0], lock_command_object_to_lock_not_here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to lock.'),
        self.command_processor_obj.game_state.rooms_state.cursor.north_exit.is_locked
        self.door_title = self.command_processor_obj.game_state.rooms_state.cursor.north_exit.title

    def test_lock_3(self):
        self.door_obj.is_locked = False
        result = self.command_processor_obj.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], lock_command_dont_possess_correct_key)
        self.assertEqual(result[0].object_to_lock_title, self.door_title)
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, f'To lock the {self.door_title} you need a door key.')
        self.assertFalse(self.door_obj.is_locked)

    def test_lock_4(self):
        self.door_obj.is_locked = True
        key_obj = self.command_processor_obj.game_state.items_state.get('Door_Key')
        self.command_processor_obj.game_state.character.pick_up_item(key_obj)
        result = self.command_processor_obj.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], lock_command_object_is_already_locked)
        self.assertEqual(result[0].target_obj, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already locked.')
        self.assertTrue(self.door_obj.is_locked)

        self.door_obj.is_locked = False
        result = self.command_processor_obj.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], lock_command_object_has_been_locked)
        self.assertEqual(result[0].target_obj, self.door_title)
        self.assertEqual(result[0].message, f'You have locked the {self.door_title}.')
        self.assertTrue(self.door_obj.is_locked)

    def test_lock_5(self):
        result = self.command_processor_obj.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], lock_command_dont_possess_correct_key)
        self.assertEqual(result[0].object_to_lock_title, self.chest_title)
        self.assertEqual(result[0].key_needed, 'chest key')
        self.assertEqual(result[0].message, f'To lock the {self.chest_title} you need a chest key.')

    def test_lock_6(self):
        self.chest_obj.is_locked = True
        key_obj = self.command_processor_obj.game_state.items_state.get('Chest_Key')
        self.command_processor_obj.game_state.character.pick_up_item(key_obj)
        result = self.command_processor_obj.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], lock_command_object_is_already_locked)
        self.assertEqual(result[0].target_obj, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already locked.')

        self.chest_obj.is_locked = False
        result = self.command_processor_obj.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], lock_command_object_has_been_locked)
        self.assertEqual(result[0].target_obj, self.chest_title)
        self.assertEqual(result[0].message, f'You have locked the {self.chest_title}.')
        self.assertTrue(self.chest_obj.is_locked)
