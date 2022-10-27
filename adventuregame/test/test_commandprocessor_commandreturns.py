#!/usr/bin/python3

import math
import operator
import unittest
import sys

from adventuregame import *
from adventuregame.test.utility import *

__name__ = 'adventuregame.test_commandprocessor_commandreturns'




class test_status(unittest.TestCase):

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

    def test_status1(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        result = self.command_processor_obj.process('status status')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'STATUS')
        self.assertEqual(result[0].message, "STATUS command: bad syntax. Should be 'STATUS'.")

    def test_status2(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        self.command_processor_obj.game_state.character.pick_up_item(longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(shield_obj)
        self.command_processor_obj.game_state.character.equip_weapon(longsword_obj)
        self.command_processor_obj.game_state.character.equip_armor(scale_mail_obj)
        self.command_processor_obj.game_state.character.equip_shield(shield_obj)
        result = self.command_processor_obj.process('status')
        self.assertIsInstance(result[0], status_command_output)
        self.assertRegex(result[0].message, "Hit Points: \d+/\d+ | Attack: [+-]\d+ (\d+d[\d+-]+ damage) - Armor Class: \d+ | Weapon: [a-z ]+ - Armor: [a-z ]+ - Shield: [a-z ]+")

    def test_status3(self):
        self.command_processor_obj.game_state.character_name = 'Mialee'
        self.command_processor_obj.game_state.character_class = 'Mage'
        staff_obj = self.command_processor_obj.game_state.items_state.get('Staff')
        magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')
        self.command_processor_obj.game_state.character.pick_up_item(staff_obj)
        self.command_processor_obj.game_state.character.pick_up_item(magic_wand_obj)
        self.command_processor_obj.game_state.character.equip_weapon(staff_obj)
        self.command_processor_obj.game_state.character.equip_wand(magic_wand_obj)
        result = self.command_processor_obj.process('status')
        self.assertIsInstance(result[0], status_command_output)
        self.assertRegex(result[0].message, "Hit Points: \d+/\d+ - Mana Points: \d+/\d+ | Attack: [+-]\d+ (\d+d[\d+-]+ damage) - Armor Class: \d+ | Wand: [a-z ]+ - Weapon: [a-z ]+ - Armor: [a-z ]+ - Shield: [a-z ]+")


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
        longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')
        mana_potion_obj = self.command_processor_obj.game_state.items_state.get('Mana_Potion')
        gold_coin_obj = self.command_processor_obj.game_state.items_state.get('Gold_Coin')
        self.command_processor_obj.game_state.character.pick_up_item(longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(shield_obj)
        self.command_processor_obj.game_state.character.pick_up_item(magic_wand_obj)
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
        self.assertEqual(result[0].inventory_contents, ['30 gold coins', 'a longsword', 'a magic wand',
                                                        '2 mana potions', 'a suit of scale mail armor',
                                                        'a steel shield'])
        self.assertEqual(result[0].message, 'You have 30 gold coins, a longsword, a magic wand, 2 mana potions, a suit '
                                            'of scale mail armor, and a steel shield in your inventory.')


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
        self.assertEqual(result[0].item_description, "A broad panel of leather-bound steel with a metal rim that is "
                                                     "useful for sheltering behind. Its armor bonus is +2. Warriors "
                                                     "and priests can use this.")
        self.assertEqual(result[0].message, "A broad panel of leather-bound steel with a metal rim that is useful for "
                                            "sheltering behind. Its armor bonus is +2. Warriors and priests can use "
                                            "this.")

    def test_inspect_11(self):
        result = self.command_processor_obj.process('inspect steel shield in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, "A broad panel of leather-bound steel with a metal rim that is "
                                                     "useful for sheltering behind. Its armor bonus is +2. Warriors "
                                                     "and priests can use this.")
        self.assertEqual(result[0].message, "A broad panel of leather-bound steel with a metal rim that is useful for "
                                            "sheltering behind. Its armor bonus is +2. Warriors and priests can use "
                                            "this.")

    def test_inspect_12(self):
        result = self.command_processor_obj.process('inspect mana potion in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, "A small, stoppered bottle that contains a pungeant but drinkable "
                                                     "blue liquid with a discernable magic aura. It restores 25 mana "
                                                     "points.")
        self.assertEqual(result[0].message, "A small, stoppered bottle that contains a pungeant but drinkable blue "
                                            "liquid with a discernable magic aura. It restores 25 mana points.")

    def test_inspect_13(self):
        result = self.command_processor_obj.process('inspect health potion in wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_item_or_items_here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, "A small, stoppered bottle that contains a pungeant but drinkable "
                                                     "red liquid with a discernable magic aura. It restores 25 hit "
                                                     "points.")
        self.assertEqual(result[0].message, "A small, stoppered bottle that contains a pungeant but drinkable red "
                                            "liquid with a discernable magic aura. It restores 25 hit points.")

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
                                                     'its damage is 2d12+3. Mages can use this.')
        self.assertEqual(result[0].message, 'A palpably magical tapered length of polished ash wood tipped with a '
                                            'glowing red carnelian gem. Its attack bonus is +3 and its damage is '
                                            '2d12+3. Mages can use this.')


class test_command_equip_unequip(unittest.TestCase):

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

    def test_equip_1(self):
        self.command_processor_obj.game_state.character_name = 'Arliss'
        self.command_processor_obj.game_state.character_class = 'Mage'

        result = self.command_processor_obj.process('equip')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'EQUIP')
        self.assertEqual(result[0].message, "EQUIP command: bad syntax. Should be 'EQUIP <armor name>', "
                                            "'EQUIP <shield name>', 'EQUIP <wand name>', or 'EQUIP <weapon name>'.")

        longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')
        magic_wand_2_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand_2')

        result = self.command_processor_obj.process('equip longsword')
        self.assertIsInstance(result[0], equip_command_no_such_item_in_inventory)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].message, "You don't have a longsword in your inventory.")

        self.command_processor_obj.game_state.character.pick_up_item(longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(shield_obj)
        self.command_processor_obj.game_state.character.pick_up_item(magic_wand_obj)
        self.command_processor_obj.game_state.character.pick_up_item(magic_wand_2_obj)

        result = self.command_processor_obj.process('equip longsword')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "Mages can't wield longswords.")

        result = self.command_processor_obj.process('equip scale mail armor')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertEqual(result[0].message, "Mages can't wear scale mail armor.")

        result = self.command_processor_obj.process('equip steel shield')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertEqual(result[0].message, "Mages can't carry steel shields.")

        result = self.command_processor_obj.process('equip magic wand')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, "^You're now using a magic wand. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")

        result = self.command_processor_obj.process('equip magic wand 2')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertEqual(result[0].message, "You're no longer using a magic wand. You now can't attack.")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'magic wand 2')
        self.assertEqual(result[1].item_type, 'wand')
        self.assertRegex(result[1].message, "^You're now using a magic wand 2. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")

    def test_unequip_1(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'

        mace_obj = self.command_processor_obj.game_state.items_state.get('Mace')
        studded_leather_obj = self.command_processor_obj.game_state.items_state.get('Studded_Leather')
        buckler_obj = self.command_processor_obj.game_state.items_state.get('Buckler')
        longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')

        self.command_processor_obj.game_state.character.pick_up_item(mace_obj)
        self.command_processor_obj.game_state.character.pick_up_item(studded_leather_obj)
        self.command_processor_obj.game_state.character.pick_up_item(buckler_obj)
        self.command_processor_obj.game_state.character.pick_up_item(longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(shield_obj)
        self.command_processor_obj.game_state.character.pick_up_item(magic_wand_obj)

        result = self.command_processor_obj.process('unequip')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'UNEQUIP')
        self.assertEqual(result[0].message, "UNEQUIP command: bad syntax. Should be 'UNEQUIP <armor name>', "
                                            "'UNEQUIP <shield name>', 'UNEQUIP <wand name>', or 'UNEQUIP <weapon name>'.")

        result = self.command_processor_obj.process('unequip mace')
        self.assertIsInstance(result[0], unequip_command_item_not_equipped)
        self.assertEqual(result[0].item_asked_title, 'mace')
        self.assertEqual(result[0].message, "You're not wielding a mace.")

        result = self.command_processor_obj.process('unequip steel shield')
        self.assertIsInstance(result[0], unequip_command_item_not_equipped)
        self.assertEqual(result[0].item_asked_title, 'steel shield')
        self.assertEqual(result[0].message, "You're not carrying a steel shield.")

        result = self.command_processor_obj.process('unequip scale mail armor')
        self.assertIsInstance(result[0], unequip_command_item_not_equipped)
        self.assertEqual(result[0].item_asked_title, 'scale mail armor')
        self.assertEqual(result[0].message, "You're not wearing scale mail armor.")

        result = self.command_processor_obj.process('unequip magic wand')
        self.assertIsInstance(result[0], unequip_command_item_not_equipped)
        self.assertEqual(result[0].item_asked_title, 'magic wand')
        self.assertEqual(result[0].message, "You're not using a magic wand.")

        result = self.command_processor_obj.process('equip mace')
        result = self.command_processor_obj.process('unequip mace')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'mace')
        self.assertEqual(result[0].message, "You're no longer wielding a mace. You now can't attack.")

        result = self.command_processor_obj.process('equip steel shield')
        result = self.command_processor_obj.process('unequip steel shield')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertRegex(result[0].message, r"^You're no longer carrying a steel shield. Your armor class is \d+.$")

        result = self.command_processor_obj.process('equip scale mail armor')
        result = self.command_processor_obj.process('unequip scale mail armor')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertRegex(result[0].message, r"^You're no longer wearing scale mail armor. Your armor class is \d+.$")


    def test_equip_2(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'

        mace_obj = self.command_processor_obj.game_state.items_state.get('Mace')
        studded_leather_obj = self.command_processor_obj.game_state.items_state.get('Studded_Leather')
        buckler_obj = self.command_processor_obj.game_state.items_state.get('Buckler')
        longsword_obj = self.command_processor_obj.game_state.items_state.get('Longsword')
        scale_mail_obj = self.command_processor_obj.game_state.items_state.get('Scale_Mail')
        shield_obj = self.command_processor_obj.game_state.items_state.get('Steel_Shield')
        magic_wand_obj = self.command_processor_obj.game_state.items_state.get('Magic_Wand')

        self.command_processor_obj.game_state.character.pick_up_item(mace_obj)
        self.command_processor_obj.game_state.character.pick_up_item(studded_leather_obj)
        self.command_processor_obj.game_state.character.pick_up_item(buckler_obj)
        self.command_processor_obj.game_state.character.pick_up_item(longsword_obj)
        self.command_processor_obj.game_state.character.pick_up_item(scale_mail_obj)
        self.command_processor_obj.game_state.character.pick_up_item(shield_obj)
        self.command_processor_obj.game_state.character.pick_up_item(magic_wand_obj)

        result = self.command_processor_obj.process('equip longsword')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertRegex(result[0].message, "^You're now wielding a longsword. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")

        result = self.command_processor_obj.process('equip scale mail armor')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertRegex(result[0].message, "^You're now wearing scale mail armor. Your armor class is \d+.$")

        result = self.command_processor_obj.process('equip steel shield')
        self.assertIsInstance(result[0], equip_command_item_equipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertRegex(result[0].message, "^You're now carrying a steel shield. Your armor class is \d+.$")

        result = self.command_processor_obj.process('equip magic wand')
        self.assertIsInstance(result[0], equip_command_class_cant_use_item)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].message, "Warriors can't use magic wands.")

        result = self.command_processor_obj.process('equip mace')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "You're no longer wielding a longsword. You now can't attack.")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'mace')
        self.assertEqual(result[1].item_type, 'weapon')
        self.assertRegex(result[1].message, "^You're now wielding a mace. Your attack bonus is [\d+-]+, and your damage is [\dd+-]+.$")

        result = self.command_processor_obj.process('equip buckler')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertRegex(result[0].message, "^You're no longer carrying a steel shield. Your armor class is \d+.$")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'buckler')
        self.assertEqual(result[1].item_type, 'shield')
        self.assertRegex(result[1].message, "^You're now carrying a buckler. Your armor class is [\d+-]+.$")

        result = self.command_processor_obj.process('equip studded leather armor')
        self.assertIsInstance(result[0], equip_or_unequip_command_item_unequipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertRegex(result[0].message, "^You're no longer wearing scale mail armor. Your armor class is \d+.$")
        self.assertIsInstance(result[1], equip_command_item_equipped)
        self.assertEqual(result[1].item_title, 'studded leather armor')
        self.assertEqual(result[1].item_type, 'armor')
        self.assertRegex(result[1].message, "^You're now wearing studded leather armor. Your armor class is \d+.$")


class test_command_processor_lock_vs_unlock(unittest.TestCase):

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

    def test_unlock(self):
        result = self.command_processor_obj.process('unlock')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'UNLOCK')
        self.assertEqual(result[0].message, "UNLOCK command: bad syntax. Should be 'UNLOCK <door name>' or "
                                            "'UNLOCK <chest name>'."),

        door_obj = self.command_processor_obj.game_state.rooms_state.cursor.north_exit
        door_obj.is_locked = True
        door_title = self.command_processor_obj.game_state.rooms_state.cursor.north_exit.title

        result = self.command_processor_obj.process('unlock west door')
        self.assertIsInstance(result[0], unlock_command_object_to_unlock_not_here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to unlock.'),
        self.command_processor_obj.game_state.rooms_state.cursor.north_exit.is_locked
        door_title = self.command_processor_obj.game_state.rooms_state.cursor.north_exit.title

        result = self.command_processor_obj.process(f'unlock {door_title}')
        self.assertIsInstance(result[0], unlock_command_dont_possess_correct_key)
        self.assertEqual(result[0].object_to_unlock_title, door_title)
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, f'To unlock the {door_title} you need a door key.')
        self.assertTrue(door_obj.is_locked)

        door_obj.is_locked = False
        key_obj = self.command_processor_obj.game_state.items_state.get('Door_Key')
        self.command_processor_obj.game_state.character.pick_up_item(key_obj)
        result = self.command_processor_obj.process(f'unlock {door_title}')
        self.assertIsInstance(result[0], unlock_command_object_is_already_unlocked)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'The {door_title} is already unlocked.')
        self.assertFalse(door_obj.is_locked)

        door_obj.is_locked = True
        result = self.command_processor_obj.process(f'unlock {door_title}')
        self.assertIsInstance(result[0], unlock_command_object_has_been_unlocked)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'You have unlocked the {door_title}.')
        self.assertFalse(door_obj.is_locked)

        chest_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here
        chest_obj.is_locked = True
        chest_title = chest_obj.title

        result = self.command_processor_obj.process(f'unlock {chest_title}')
        self.assertIsInstance(result[0], unlock_command_dont_possess_correct_key)
        self.assertEqual(result[0].object_to_unlock_title, chest_title)
        self.assertEqual(result[0].key_needed, 'chest key')
        self.assertEqual(result[0].message, f'To unlock the {chest_title} you need a chest key.')
        self.assertTrue(chest_obj.is_locked)

        chest_obj.is_locked = False

        key_obj = self.command_processor_obj.game_state.items_state.get('Chest_Key')
        self.command_processor_obj.game_state.character.pick_up_item(key_obj)
        result = self.command_processor_obj.process(f'unlock {chest_title}')
        self.assertIsInstance(result[0], unlock_command_object_is_already_unlocked)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'The {chest_title} is already unlocked.')
        self.assertFalse(chest_obj.is_locked)

        chest_obj.is_locked = True

        result = self.command_processor_obj.process(f'unlock {chest_title}')
        self.assertIsInstance(result[0], unlock_command_object_has_been_unlocked)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'You have unlocked the {chest_title}.')
        self.assertFalse(chest_obj.is_locked)

    def test_lock(self):
        result = self.command_processor_obj.process('lock')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'LOCK')
        self.assertEqual(result[0].message, "LOCK command: bad syntax. Should be 'LOCK <door name>' or "
                                            "'LOCK <chest name>'."),

        door_obj = self.command_processor_obj.game_state.rooms_state.cursor.north_exit
        door_obj.is_locked = True
        door_title = self.command_processor_obj.game_state.rooms_state.cursor.north_exit.title

        result = self.command_processor_obj.process('lock west door')
        self.assertIsInstance(result[0], lock_command_object_to_lock_not_here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to lock.'),
        self.command_processor_obj.game_state.rooms_state.cursor.north_exit.is_locked
        door_title = self.command_processor_obj.game_state.rooms_state.cursor.north_exit.title

        door_obj.is_locked = False
        result = self.command_processor_obj.process(f'lock {door_title}')
        self.assertIsInstance(result[0], lock_command_dont_possess_correct_key)
        self.assertEqual(result[0].object_to_lock_title, door_title)
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, f'To lock the {door_title} you need a door key.')
        self.assertFalse(door_obj.is_locked)

        door_obj.is_locked = True
        key_obj = self.command_processor_obj.game_state.items_state.get('Door_Key')
        self.command_processor_obj.game_state.character.pick_up_item(key_obj)
        result = self.command_processor_obj.process(f'lock {door_title}')
        self.assertIsInstance(result[0], lock_command_object_is_already_locked)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'The {door_title} is already locked.')
        self.assertTrue(door_obj.is_locked)

        door_obj.is_locked = False
        result = self.command_processor_obj.process(f'lock {door_title}')
        self.assertIsInstance(result[0], lock_command_object_has_been_locked)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'You have locked the {door_title}.')
        self.assertTrue(door_obj.is_locked)

        chest_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here
        chest_obj.is_locked = False
        chest_title = chest_obj.title

        result = self.command_processor_obj.process(f'lock {chest_title}')
        self.assertIsInstance(result[0], lock_command_dont_possess_correct_key)
        self.assertEqual(result[0].object_to_lock_title, chest_title)
        self.assertEqual(result[0].key_needed, 'chest key')
        self.assertEqual(result[0].message, f'To lock the {chest_title} you need a chest key.')

        chest_obj.is_locked = True

        key_obj = self.command_processor_obj.game_state.items_state.get('Chest_Key')
        self.command_processor_obj.game_state.character.pick_up_item(key_obj)
        result = self.command_processor_obj.process(f'lock {chest_title}')
        self.assertIsInstance(result[0], lock_command_object_is_already_locked)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'The {chest_title} is already locked.')

        chest_obj.is_locked = False

        result = self.command_processor_obj.process(f'lock {chest_title}')
        self.assertIsInstance(result[0], lock_command_object_has_been_locked)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'You have locked the {chest_title}.')
        self.assertTrue(chest_obj.is_locked)

    def test_open(self):
        result = self.command_processor_obj.process('open')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'OPEN')
        self.assertEqual(result[0].message, "OPEN command: bad syntax. Should be 'OPEN <door name>' or "
                                            "'OPEN <chest name>'."),

        chest_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here
        chest_obj.is_closed = True
        chest_obj.is_locked = True
        chest_title = chest_obj.title

        result = self.command_processor_obj.process(f'open {chest_title}')
        self.assertIsInstance(result[0], open_command_object_is_locked)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'The {chest_title} is locked.')

        chest_obj.is_locked = False
        chest_obj.is_closed = False
        chest_title = chest_obj.title

        result = self.command_processor_obj.process(f'open {chest_title}')
        self.assertIsInstance(result[0], open_command_object_is_already_open)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'The {chest_title} is already open.')
        self.assertFalse(chest_obj.is_closed)

        chest_obj.is_closed = True

        result = self.command_processor_obj.process(f'open {chest_title}')
        self.assertIsInstance(result[0], open_command_object_has_been_opened)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'You have opened the {chest_title}.')
        self.assertFalse(chest_obj.is_closed)

        door_obj = self.command_processor_obj.game_state.rooms_state.cursor.north_exit
        door_obj.is_closed = False
        door_title = door_obj.title

        result = self.command_processor_obj.process('open west door')
        self.assertIsInstance(result[0], open_command_object_to_open_not_here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to open.'),

        result = self.command_processor_obj.process(f'open {door_title}')
        self.assertIsInstance(result[0], open_command_object_is_already_open)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'The {door_title} is already open.')
        self.assertFalse(door_obj.is_closed)

        door_obj.is_closed = True

        result = self.command_processor_obj.process(f'open {door_title}')
        self.assertIsInstance(result[0], open_command_object_has_been_opened)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'You have opened the {door_title}.')
        self.assertFalse(door_obj.is_closed)

        door_obj.is_closed = True
        door_obj.is_locked = True

        result = self.command_processor_obj.process(f'open {door_title}')
        self.assertIsInstance(result[0], open_command_object_is_locked)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'The {door_title} is locked.')
        self.assertTrue(door_obj.is_closed)

    def test_close(self):
        result = self.command_processor_obj.process('close')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'CLOSE')
        self.assertEqual(result[0].message, "CLOSE command: bad syntax. Should be 'CLOSE <door name>' or "
                                            "'CLOSE <chest name>'."),

        chest_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here
        chest_obj.is_closed = True
        chest_obj.is_locked = False
        chest_title = chest_obj.title

        result = self.command_processor_obj.process(f'close {chest_title}')
        self.assertIsInstance(result[0], close_command_object_is_already_closed)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'The {chest_title} is already closed.')
        self.assertTrue(chest_obj.is_closed)

        chest_obj.is_closed = False

        result = self.command_processor_obj.process(f'close {chest_title}')
        self.assertIsInstance(result[0], close_command_object_has_been_closed)
        self.assertEqual(result[0].target_object, chest_title)
        self.assertEqual(result[0].message, f'You have closed the {chest_title}.')
        self.assertTrue(chest_obj.is_closed)

        result = self.command_processor_obj.process('close west door')
        self.assertIsInstance(result[0], close_command_object_to_close_not_here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to close.'),

        door_obj = self.command_processor_obj.game_state.rooms_state.cursor.north_exit
        door_obj.is_closed = True
        door_title = door_obj.title

        result = self.command_processor_obj.process(f'close {door_title}')
        self.assertIsInstance(result[0], close_command_object_is_already_closed)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'The {door_title} is already closed.')
        self.assertTrue(door_obj.is_closed)

        door_obj.is_closed = False

        result = self.command_processor_obj.process(f'close {door_title}')
        self.assertIsInstance(result[0], close_command_object_has_been_closed)
        self.assertEqual(result[0].target_object, door_title)
        self.assertEqual(result[0].message, f'You have closed the {door_title}.')
        self.assertTrue(door_obj.is_closed)


class test_command_processor_pick_up_vs_drop(unittest.TestCase):

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

    def test_pick_up(self):
        result = self.command_processor_obj.process('pick up the')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PICK UP')
        self.assertEqual(result[0].message, "PICK UP command: bad syntax. Should be 'PICK UP <item name>' or 'PICK UP <number> <item name>'."),

        result = self.command_processor_obj.process('pick up a gold coins')  # check
        self.assertIsInstance(result[0], pick_up_command_quantity_unclear)
        self.assertEqual(result[0].message, 'Amount to pick up unclear. How many do you mean?')

        result = self.command_processor_obj.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], pick_up_command_item_not_found)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 15)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no gold coins here. However, there is 2 health potions and a mana potion here.')

        result = self.command_processor_obj.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], pick_up_command_item_not_found)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no short sword here. However, there is 2 health potions and a mana potion here.')

        self.command_processor_obj.game_state.rooms_state.move(north=True)
        result = self.command_processor_obj.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], pick_up_command_item_not_found)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ())
        self.assertEqual(result[0].message, 'You see no short sword here.')
        self.command_processor_obj.game_state.rooms_state.move(south=True)

        result = self.command_processor_obj.process('pick up 2 mana potions')  # check
        self.assertIsInstance(result[0], pick_up_command_trying_to_pick_up_more_than_is_present)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, "You can't pick up 2 mana potions. Only 1 is here.")

        result = self.command_processor_obj.process('pick up a mana potion')  # check
        self.assertIsInstance(result[0], pick_up_command_item_picked_up)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 1)
        self.assertEqual(result[0].message, 'You picked up a mana potion. You have 1 mana potion.')

        result = self.command_processor_obj.process('pick up a health potion')  # check
        result = self.command_processor_obj.process('pick up health potion')  # check
        self.assertIsInstance(result[0], pick_up_command_item_picked_up)
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 2)
        self.assertEqual(result[0].message, 'You picked up a health potion. You have 2 health potions.')

        gold_coin_obj = self.items_state_obj.get('Gold_Coin')
        self.command_processor_obj.game_state.rooms_state.cursor.items_here.set('Gold_Coin', 30, gold_coin_obj)

        result = self.command_processor_obj.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], pick_up_command_item_picked_up)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 15)
        self.assertEqual(result[0].message, 'You picked up 15 gold coins. You have 15 gold coins.')

        result = self.command_processor_obj.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], pick_up_command_item_picked_up)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, 'You picked up 15 gold coins. You have 30 gold coins.')

    def test_drop(self):
        result = self.command_processor_obj.process('drop the')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'DROP')
        self.assertEqual(result[0].message, "DROP command: bad syntax. Should be 'DROP <item name>' or 'DROP <number> <item name>'."),

        result = self.command_processor_obj.process('drop a gold coins')  # check
        self.assertIsInstance(result[0], drop_command_quantity_unclear)
        self.assertEqual(result[0].message, 'Amount to drop unclear. How many do you mean?')

        gold_coin_obj = self.items_state_obj.get('Gold_Coin')
        self.command_processor_obj.game_state.character.pick_up_item(gold_coin_obj, qty=30)

        result = self.command_processor_obj.process('drop a mana potion')  # check
        self.assertIsInstance(result[0], drop_command_trying_to_drop_item_you_dont_have)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].message, "You don't have a mana potion in your inventory.")

        result = self.command_processor_obj.process('drop 45 gold coins')  # check
        self.assertIsInstance(result[0], drop_command_trying_to_drop_more_than_you_have)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 45)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, "You can't drop 45 gold coins. You only have 30 gold coins in your inventory.")

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

        self.command_processor_obj.process('pick up 29 gold coins')  # check
        result = self.command_processor_obj.process('drop 1 gold coin')  # check
        self.assertIsInstance(result[0], drop_command_dropped_item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 29)
        self.assertEqual(result[0].message, 'You dropped a gold coin. You see a gold coin here. You have 29 gold coins left.')


class test_command_processor_set_name_vs_set_class_vs_reroll_vs_satisfied(unittest.TestCase):

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

    def test_set_name_and_class_1(self):

        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)

        result = self.command_processor_obj.process('set class to Warrior')
        self.assertIsInstance(result[0], set_class_command_class_set)
        self.assertEqual(result[0].class_str, 'Warrior')
        self.assertEqual(result[0].message, 'Your class, Warrior, has been set.')

        result = self.command_processor_obj.process('set name to Kerne')
        self.assertIsInstance(result[0], set_name_command_name_set)
        self.assertEqual(result[0].name, 'Kerne')
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")
        self.assertIsInstance(result[1], set_name_or_class_command_display_rolled_stats)
        self.assertIsInstance(result[1].strength, int)
        self.assertTrue(3 <= result[1].strength <= 18)
        self.assertIsInstance(result[1].dexterity, int)
        self.assertTrue(3 <= result[1].dexterity <= 18)
        self.assertIsInstance(result[1].constitution, int)
        self.assertTrue(3 <= result[1].constitution <= 18)
        self.assertIsInstance(result[1].intelligence, int)
        self.assertTrue(3 <= result[1].intelligence <= 18)
        self.assertIsInstance(result[1].wisdom, int)
        self.assertTrue(3 <= result[1].wisdom <= 18)
        self.assertIsInstance(result[1].charisma, int)
        self.assertTrue(3 <= result[1].charisma <= 18)
        self.assertEqual(result[1].message, f'Your ability scores are Strength {result[1].strength}, Dexterity '
                                            f'{result[1].dexterity}, Constitution {result[1].constitution}, '
                                            f'Intelligence {result[1].intelligence}, Wisdom {result[1].wisdom}, '
                                            f'Charisma {result[1].charisma}.\nAre you satisfied with these scores or '
                                            'would you like to reroll?')

        first_roll = {'strength': result[1].strength, 'dexterity': result[1].dexterity,
                      'constitution': result[1].constitution, 'intelligence': result[1].intelligence,
                      'wisdom': result[1].wisdom, 'charisma': result[1].charisma}
        result = self.command_processor_obj.process('reroll')
        second_roll = {'strength': result[0].strength, 'dexterity': result[0].dexterity,
                      'constitution': result[0].constitution, 'intelligence': result[0].intelligence,
                      'wisdom': result[0].wisdom, 'charisma': result[0].charisma}
        self.assertIsInstance(result[0], set_name_or_class_command_display_rolled_stats)
        self.assertNotEqual(first_roll, second_roll)

        result = self.command_processor_obj.process('satisfied')
        self.assertIsInstance(result[0], satisfied_command_game_begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_and_class_2(self):
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process("I'm satisfied")
        self.assertIsInstance(result[0], satisfied_command_game_begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_and_class_3(self):
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process("I'm satisfied to play")
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'SATISFIED')
        self.assertEqual(result[0].message, "SATISFIED command: bad syntax. Should be 'SATISFIED'.")
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_and_class_4(self):
        result = self.command_processor_obj.process('set name to Kerne0')
        self.assertIsInstance(result[0], set_name_command_invalid_part)
        self.assertEqual(result[0].name_part, 'Kerne0')
        self.assertEqual(result[0].message, 'The name Kerne0 is invalid; must be a capital letter followed by lowercase letters.')

        result = self.command_processor_obj.process('set name to Kerne MacDonald0 Fahey1')
        self.assertIsInstance(result[0], set_name_command_invalid_part)
        self.assertEqual(result[0].name_part, 'MacDonald0')
        self.assertEqual(result[0].message, 'The name MacDonald0 is invalid; must be a capital letter followed by lowercase letters.')
        self.assertIsInstance(result[1], set_name_command_invalid_part)
        self.assertEqual(result[1].name_part, 'Fahey1')
        self.assertEqual(result[1].message, 'The name Fahey1 is invalid; must be a capital letter followed by lowercase letters.')

        result = self.command_processor_obj.process('set name to Kerne')
        self.assertIsInstance(result[0], set_name_command_name_set)
        self.assertEqual(result[0].name, 'Kerne')
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")

        result = self.command_processor_obj.process('set class to Ranger')
        self.assertIsInstance(result[0], set_class_command_invalid_class)
        self.assertEqual(result[0].bad_class, 'Ranger')
        self.assertEqual(result[0].message, "'Ranger' is not a valid class choice. Please choose Warrior, Thief, Mage, or Priest.")

        result = self.command_processor_obj.process('set class to Warrior')
        self.assertIsInstance(result[0], set_class_command_class_set)
        self.assertEqual(result[0].class_str, 'Warrior')
        self.assertEqual(result[0].message, 'Your class, Warrior, has been set.')
        self.assertIsInstance(result[1], set_name_or_class_command_display_rolled_stats)
        self.assertIsInstance(result[1].strength, int)
        self.assertTrue(3 <= result[1].strength <= 18)
        self.assertIsInstance(result[1].dexterity, int)
        self.assertTrue(3 <= result[1].dexterity <= 18)
        self.assertIsInstance(result[1].constitution, int)
        self.assertTrue(3 <= result[1].constitution <= 18)
        self.assertIsInstance(result[1].intelligence, int)
        self.assertTrue(3 <= result[1].intelligence <= 18)
        self.assertIsInstance(result[1].wisdom, int)
        self.assertTrue(3 <= result[1].wisdom <= 18)
        self.assertIsInstance(result[1].charisma, int)
        self.assertTrue(3 <= result[1].charisma <= 18)

    def test_set_name_and_class_5(self):
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process("I'm satisfied to play")
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'SATISFIED')
        self.assertEqual(result[0].message, "SATISFIED command: bad syntax. Should be 'SATISFIED'.")
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_and_class_6(self):
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('reroll please')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)


class test_command_processor_attack_vs_be_attacked_by(unittest.TestCase):

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

    def test_attack_bad_usages(self):
        self.command_processor_obj.process('unequip longsword')
        result = self.command_processor_obj.process('attack sorcerer')
        self.assertIsInstance(result[0], attack_command_you_have_no_weapon_or_wand_equipped)
        self.assertEqual(result[0].message, "You have no weapon equipped; you can't attack.")
        self.command_processor_obj.process('equip longsword')
        result = self.command_processor_obj.process('attack sorcerer')
        self.assertIsInstance(result[0], attack_command_opponent_not_found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertEqual(result[0].opponent_present, 'kobold')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; but there is a kobold.")
        self.game_state_obj.rooms_state.cursor.creature_here = None
        result = self.command_processor_obj.process('attack sorcerer')
        self.assertIsInstance(result[0], attack_command_opponent_not_found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertIs(result[0].opponent_present, '')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; nobody is here.")

    def test_attack_vs_be_attacked_by_and_character_death_and_inspect_and_loot_corpse(self):
        results = tuple()
        while not len(results) or not isinstance(results[-1], attack_command_foe_death):
            self.setUp()
            results = self.command_processor_obj.process('attack kobold')
            while not (isinstance(results[-1], be_attacked_by_command_character_death) or isinstance(results[-1], attack_command_foe_death)):
                results += self.command_processor_obj.process('attack kobold')
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
        gold_coin_obj = self.game_state_obj.items_state.get('Gold_Coin')
        health_potion_obj = self.game_state_obj.items_state.get('Health_Potion')
        short_sword_obj = self.game_state_obj.items_state.get('Short_Sword')
        small_leather_armor_obj = self.game_state_obj.items_state.get('Small_Leather_Armor')
        expected_list = [('Gold_Coin', (30, gold_coin_obj)), ('Health_Potion', (1, health_potion_obj)),
                         ('Short_Sword', (1, short_sword_obj)), ('Small_Leather_Armor', (1, small_leather_armor_obj))]
        self.assertEqual(corpse_belonging_list, expected_list)

        result = self.command_processor_obj.process('inspect kobold corpse')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} They '
                                          'have 30 gold coins, a health potion, a short sword, and a small leather '
                                          'armor on them.')

        (potion_qty, health_potion_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Health_Potion')
        result = self.command_processor_obj.process('take a health potion from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_or_items_taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].amount_taken, 1)
        self.assertEqual(result[0].message, 'You took a health potion from the kobold corpse.')
        self.assertTrue(self.command_processor_obj.game_state.character.inventory.contains('Health_Potion'))
        self.assertFalse(self.command_processor_obj.game_state.rooms_state.cursor.container_here.contains('Health_Potion'))
        self.assertTrue(self.command_processor_obj.game_state.character.inventory.get('Health_Potion'), (1, health_potion_obj))

        (_, gold_coin_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Gold_Coin')
        result = self.command_processor_obj.process('take 15 gold coins from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_or_items_taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')
        self.assertTrue(self.command_processor_obj.game_state.character.have_item(gold_coin_obj))
        self.assertEqual(self.command_processor_obj.game_state.character.item_have_qty(gold_coin_obj), 15)
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.container_here.contains('Gold_Coin'))
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Gold_Coin'), (15, gold_coin_obj))

        (_, short_sword_obj) = self.command_processor_obj.game_state.rooms_state.cursor.container_here.get('Short_Sword')
        result = self.command_processor_obj.process('take one short sword from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_or_items_taken)

        result = self.command_processor_obj.process('take one small leather armors from the kobold corpse')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container name>' or 'TAKE <number> <item name> FROM <container name>'."),

        result = self.command_processor_obj.process('take one small leather armor from the kobold corpses')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container name>' or 'TAKE <number> <item name> FROM <container name>'."),

        result = self.command_processor_obj.process('take one small leather armor')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container name>' or 'TAKE <number> <item name> FROM <container name>'."),

        result = self.command_processor_obj.process('take the from the kobold corpse')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container name>' or 'TAKE <number> <item name> FROM <container name>'."),

        result = self.command_processor_obj.process('take the short sword from the')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container name>' or 'TAKE <number> <item name> FROM <container name>'."),

        result = self.command_processor_obj.process('take the short sword from the sorcerer corpse')  # check
        self.assertIsInstance(result[0], various_commands_container_not_found)
        self.assertEqual(result[0].container_not_found_title, 'sorcerer corpse')
        self.assertEqual(result[0].container_present_title, 'kobold corpse')
        self.assertEqual(result[0].message, 'There is no sorcerer corpse here. However, there *is* a kobold corpse here.')

        container_obj = self.command_processor_obj.game_state.rooms_state.cursor.container_here  # check
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor_obj.process('take the short sword from the sorcerer corpse')
        self.assertIsInstance(result[0], various_commands_container_not_found)
        self.assertEqual(result[0].container_not_found_title, 'sorcerer corpse')
        self.assertIs(result[0].container_present_title, None)
        self.assertEqual(result[0].message, 'There is no sorcerer corpse here.')
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = container_obj

        result = self.command_processor_obj.process('take 3 small leather armors from the kobold corpse')
        self.assertIsInstance(result[0], take_command_trying_to_take_more_than_is_present)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'small leather armor')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, "You can't take 3 small leather armors from the kobold corpse. Only 1 is there.")

        result = self.command_processor_obj.process('take the short sword from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_not_found_in_container)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertIs(result[0].amount_attempted, math.nan)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The kobold corpse doesn't have a short sword on them.")

        result = self.command_processor_obj.process('take three short swords from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_not_found_in_container)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The kobold corpse doesn't have any short swords on them.")

        result = self.command_processor_obj.process('take fifteen gold coins from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_or_items_taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, gold_coin_obj)
        result = self.command_processor_obj.process('take gold coins from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_or_items_taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, gold_coin_obj)
        result = self.command_processor_obj.process('take gold coin from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_or_items_taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

        result = self.command_processor_obj.process('take a small leather armor from the kobold corpse')
        self.assertIsInstance(result[0], take_command_item_or_items_taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 1)
        self.assertEqual(result[0].item_title, 'small leather armor')
        self.assertEqual(result[0].message, 'You took a small leather armor from the kobold corpse.')

        result = self.command_processor_obj.process('put 15 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 15)
        self.assertEqual(result[0].amount_left, 45)
        self.assertEqual(result[0].message, "You put 15 gold coins on the kobold corpse's person. You have 45 gold coins left.")

        result = self.command_processor_obj.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 44)
        self.assertEqual(result[0].message, "You put 1 gold coin on the kobold corpse's person. You have 44 gold coins left.")

        result = self.command_processor_obj.process('put 43 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 43)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, "You put 43 gold coins on the kobold corpse's person. You have 1 gold coin left.")

        result = self.command_processor_obj.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, "You put 1 gold coin on the kobold corpse's person. You have no more gold coins.")

        result = self.command_processor_obj.process('put 2 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], put_command_item_not_in_inventory)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].message, "You don't have any gold coins in your inventory.")

        result = self.command_processor_obj.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], put_command_item_not_in_inventory)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].message, "You don't have a gold coin in your inventory.")

        result = self.command_processor_obj.process('take 5 gold coins from the kobold corpse')
        result = self.command_processor_obj.process('put 10 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], put_command_trying_to_put_more_than_you_have)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_present, 5)
        self.assertEqual(result[0].message, 'You only have 5 gold coins in your inventory.')

        result = self.command_processor_obj.process('put 4 gold coins on the kobold corpse')
        result = self.command_processor_obj.process('put 4 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], put_command_trying_to_put_more_than_you_have)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, 'You only have 1 gold coin in your inventory.')

        result = self.command_processor_obj.process('put a gold coins on the kobold corpse')
        self.assertIsInstance(result[0], put_command_quantity_unclear)
        self.assertEqual(result[0].message, 'Amount to put unclear. How many do you mean?')

        result = self.command_processor_obj.process('put on the kobold corpse')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

        result = self.command_processor_obj.process('put one small leather armor on')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

        result = self.command_processor_obj.process('put on')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

        result = self.command_processor_obj.process('put 1 gold coin in the kobold corpse')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_inspect_also_two_take_cases(self):
        result = self.command_processor_obj.process('inspect kobold')
        self.assertIsInstance(result[0], inspect_command_found_creature_here)
        self.assertEqual(result[0].creature_description, self.game_state_obj.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, self.game_state_obj.rooms_state.cursor.creature_here.description)

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed and locked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed but unlocked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is '
                                          'unlocked and open. It contains 20 gold coins, a mana potion, and a warhammer.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        with self.assertRaises(internal_exception):
            result = self.command_processor_obj.process('inspect wooden chest')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is closed.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is '
                                             'open. It contains 20 gold coins, a mana potion, and a warhammer.')

        result = self.command_processor_obj.process('take three short swords from the wooden chest')
        self.assertIsInstance(result[0], take_command_item_not_found_in_container)
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The wooden chest doesn't have any short swords in it.")

        result = self.command_processor_obj.process('take 20 gold coins from the wooden chest')
        result = self.command_processor_obj.process('put 5 gold coins in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 5)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, 'You put 5 gold coins in the wooden chest. You have 15 gold coins left.')

        result = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 14)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have 14 gold coins left.')

        result = self.command_processor_obj.process('put 12 gold coin in the wooden chest')
        result = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have 1 gold coin left.')

        result = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have no more gold coins.')

        result = self.command_processor_obj.process('take one short sword from the wooden chest')
        self.assertIsInstance(result[0], take_command_item_not_found_in_container)
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The wooden chest doesn't have a short sword in it.")

        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('put gold coin in wooden chest')
        self.assertIsInstance(result[0], various_commands_container_is_closed)
        self.assertEqual(result[0].target_object, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is closed.')

        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor_obj.process('put in the wooden chest')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

        result = self.command_processor_obj.process('put 1 gold coin in')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

        result = self.command_processor_obj.process('put in')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

        result = self.command_processor_obj.process('put 1 gold coin on the wooden chest')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = True
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is locked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = False
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description} It is unlocked.')

        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor_obj.process('inspect wooden chest')
        self.assertIsInstance(result[0], inspect_command_found_container_here)
        self.assertEqual(result[0].container_description, self.game_state_obj.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state_obj.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state_obj.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.container_here.description}')

        result = self.command_processor_obj.process('look at kobold')
        self.assertIsInstance(result[0], inspect_command_found_creature_here)
        self.assertEqual(result[0].creature_description, self.game_state_obj.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, f'{self.game_state_obj.rooms_state.cursor.creature_here.description}')

        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('take gold coin from wooden chest')
        self.assertIsInstance(result[0], various_commands_container_is_closed)
        self.assertEqual(result[0].target_object, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is closed.')
