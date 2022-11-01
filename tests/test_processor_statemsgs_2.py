#!/usr/bin/python3

import operator
import unittest

from .context import *
from .testing_data import *

__name__ = 'tests.test_processor_statemsgs_2'


class Test_Inspect_Command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state = Items_State(**self.items_ini_config.sections)
        self.doors_state = Doors_State(**self.doors_ini_config.sections)
        self.containers_state = Containers_State(self.items_state, **self.containers_ini_config.sections)
        self.creatures_state = Creatures_State(self.items_state, **self.creatures_ini_config.sections)
        self.rooms_state = Rooms_State(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **self.rooms_ini_config.sections)
        self.game_state = Game_State(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = Command_Processor(self.game_state)
        self.game_state.character_name = 'Niath'
        self.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        self.game_state.character.pick_up_item(self.items_state.get('Longsword'))
        self.game_state.character.pick_up_item(self.items_state.get('Studded_Leather'))
        self.game_state.character.pick_up_item(self.items_state.get('Steel_Shield'))
        self.game_state.character.equip_weapon(self.items_state.get('Longsword'))
        self.game_state.character.equip_armor(self.items_state.get('Studded_Leather'))
        self.game_state.character.equip_shield(self.items_state.get('Steel_Shield'))
        (_, self.gold_coin) = \
            self.command_processor.game_state.rooms_state.cursor.container_here.get('Gold_Coin')

    def test_inspect_1(self):
        result = self.command_processor.process('inspect kobold')
        self.assertIsInstance(result[0], Inspect_Command_Found_Creature_Here)
        self.assertEqual(result[0].creature_description,
                         self.game_state.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, self.game_state.rooms_state.cursor.creature_here.description)

    def test_inspect_2(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('inspect kobold corpse')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} They '
                                          'have 30 gold coins, a health potion, a short sword, and a small leather '
                                          'armor on them.')

    def test_inspect_3(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is closed and locked.')

    def test_inspect_4(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is closed but unlocked.')

    def test_inspect_5(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is unlocked and open. It contains 20 gold coins, a health potion, a '
                                             'magic wand, a mana potion, a scale mail armor, a steel shield, and a '
                                             'warhammer.')

    def test_inspect_6(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        with self.assertRaises(Internal_Exception):
            self.command_processor.process('inspect wooden chest')

    def test_inspect_7(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is closed.')

    def test_inspect_8(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is open. It contains 20 gold coins, a health potion, a magic wand, a '
                                             'mana potion, a scale mail armor, a steel shield, and a warhammer.')

    def test_inspect_9(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is locked.')

    def test_inspect_10(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is unlocked.')

    def test_inspect_11(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process('inspect wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Container_Here)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description}')

    def test_inspect_12(self):
        result = self.command_processor.process('look at kobold')
        self.assertIsInstance(result[0], Inspect_Command_Found_Creature_Here)
        self.assertEqual(result[0].creature_description,
                         self.game_state.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.creature_here.description}')


class Test_Inspect(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state = Items_State(**self.items_ini_config.sections)
        self.doors_state = Doors_State(**self.doors_ini_config.sections)
        self.containers_ini_config.sections['Wooden_Chest_1']['contents'] = \
            '[20xGold_Coin,1xWarhammer,1xMana_Potion,1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]'
        self.containers_state = Containers_State(self.items_state, **self.containers_ini_config.sections)
        self.creatures_state = Creatures_State(self.items_state, **self.creatures_ini_config.sections)
        self.rooms_state = Rooms_State(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **self.rooms_ini_config.sections)
        self.game_state = Game_State(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True

    def test_inspect_1(self):
        result = self.command_processor.process('inspect')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_2(self):
        result = self.command_processor.process('inspect on')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_3(self):
        result = self.command_processor.process('inspect in')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_4(self):
        result = self.command_processor.process('inspect mana potion in')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_5(self):
        result = self.command_processor.process('inspect health potion on')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_6(self):
        result = self.command_processor.process('inspect health potion on wooden chest')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_7(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('inspect mana potion in kobold corpse')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INSPECT')
        self.assertEqual(result[0].message, "INSPECT command: bad syntax. Should be 'INSPECT <item name>', "
                                            "'INSPECT <item name> IN <chest name>', "
                                            "'INSPECT <item name> IN INVENTORY', "
                                            "'INSPECT <item name> ON <corpse name>', "
                                            "'INSPECT <compass direction> DOOR', or "
                                            "'INSPECT <compass direction> DOORWAY'.")

    def test_inspect_8(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process('inspect mana potion in wooden chest')
        self.assertIsInstance(result[0], Various_Commands_Container_Not_Found)
        self.assertEqual(result[0].container_not_found_title, 'wooden chest')
        self.assertEqual(result[0].message, 'There is no wooden chest here.')

    def test_inspect_9(self):
        result = self.command_processor.process('inspect gold coin in wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 20)
        self.assertEqual(result[0].item_description, 'A small shiny gold coin imprinted with an indistinct bust on one '
                                                     'side and a worn state seal on the other.')
        self.assertEqual(result[0].message, 'A small shiny gold coin imprinted with an indistinct bust on one side and '
                                            'a worn state seal on the other. You see 20 here.')

    def test_inspect_10(self):
        result = self.command_processor.process('inspect warhammer in wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A heavy hammer with a heavy iron head with a tapered striking '
                                                     'point and a long leather-wrapped haft. Its attack bonus is +0 '
                                                     'and its damage is 1d8. Warriors and priests can use this.')
        self.assertEqual(result[0].message, 'A heavy hammer with a heavy iron head with a tapered striking point and '
                                            'a long leather-wrapped haft. Its attack bonus is +0 and its damage is 1d8.'
                                            ' Warriors and priests can use this.')

    def test_inspect_11(self):
        result = self.command_processor.process('inspect steel shield in wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A broad panel of leather-bound steel with a metal rim that is '
                                                     'useful for sheltering behind. Its armor bonus is +2. Warriors '
                                                     'and priests can use this.')
        self.assertEqual(result[0].message, 'A broad panel of leather-bound steel with a metal rim that is useful for '
                                            'sheltering behind. Its armor bonus is +2. Warriors and priests can use '
                                            'this.')

    def test_inspect_12(self):
        result = self.command_processor.process('inspect steel shield in wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A broad panel of leather-bound steel with a metal rim that is '
                                                     'useful for sheltering behind. Its armor bonus is +2. Warriors '
                                                     'and priests can use this.')
        self.assertEqual(result[0].message, 'A broad panel of leather-bound steel with a metal rim that is useful for '
                                            'sheltering behind. Its armor bonus is +2. Warriors and priests can use '
                                            'this.')

    def test_inspect_13(self):
        result = self.command_processor.process('inspect mana potion in wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A small, stoppered bottle that contains a pungeant but drinkable '
                                                     'blue liquid with a discernable magic aura. It restores 20 mana '
                                                     'points.')
        self.assertEqual(result[0].message, 'A small, stoppered bottle that contains a pungeant but drinkable blue '
                                            'liquid with a discernable magic aura. It restores 20 mana points.')

    def test_inspect_14(self):
        result = self.command_processor.process('inspect health potion in wooden chest')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A small, stoppered bottle that contains a pungeant but drinkable '
                                                     'red liquid with a discernable magic aura. It restores 20 hit '
                                                     'points.')
        self.assertEqual(result[0].message, 'A small, stoppered bottle that contains a pungeant but drinkable red '
                                            'liquid with a discernable magic aura. It restores 20 hit points.')

    def test_inspect_15(self):
        result = self.command_processor.process('inspect north door')
        self.assertIsInstance(result[0], Inspect_Command_Found_Door_or_Doorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is set into the north wall of the room. This door is made of '
                                            'wooden planks secured together with iron divots. It is closed but '
                                            'unlocked.')

    def test_inspect_16(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked = True
        result = self.command_processor.process('inspect north door')
        self.assertIsInstance(result[0], Inspect_Command_Found_Door_or_Doorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is set into the north wall of the room. This door is made of '
                                            'wooden planks secured together with iron divots. It is closed and '
                                            'locked.')

    def test_inspect_17(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_closed = False
        result = self.command_processor.process('inspect north door')
        self.assertIsInstance(result[0], Inspect_Command_Found_Door_or_Doorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is set into the north wall of the room. This door is made of '
                                            'wooden planks secured together with iron divots. It is open.')

    def test_inspect_18(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_closed = False
        result = self.command_processor.process('inspect west door')
        self.assertIsInstance(result[0], Various_Commands_Door_Not_Present)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].message, 'This room does not have a west door.')

    def test_inspect_19(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('inspect east doorway')
        self.assertIsInstance(result[0], Inspect_Command_Found_Door_or_Doorway)
        self.assertEqual(result[0].compass_dir, 'east')
        self.assertEqual(result[0].message, 'This doorway is set into the east wall of the room. This open doorway is '
                                            'outlined by a stone arch set into the wall.')

    def test_inspect_20(self):
        self.command_processor.game_state.character.pick_up_item(
            self.command_processor.game_state.items_state.get('Longsword'))
        result = self.command_processor.process('inspect longsword in inventory')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A hefty sword with a long blade, a broad hilt and a leathern '
                                                     'grip. Its attack bonus is +0 and its damage is 1d8. Warriors can '
                                                     'use this.')
        self.assertEqual(result[0].message, 'A hefty sword with a long blade, a broad hilt and a leathern grip. Its '
                                            'attack bonus is +0 and its damage is 1d8. Warriors can use this.')

    def test_inspect_21(self):
        self.command_processor.game_state.character.pick_up_item(
            self.command_processor.game_state.items_state.get('Magic_Wand'))
        result = self.command_processor.process('inspect magic wand in inventory')
        self.assertIsInstance(result[0], Inspect_Command_Found_Item_or_Items_Here)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A palpably magical tapered length of polished ash wood tipped '
                                                     'with a glowing red carnelian gem. Its attack bonus is +3 and '
                                                     'its damage is 3d8+5. Mages can use this.')
        self.assertEqual(result[0].message, 'A palpably magical tapered length of polished ash wood tipped with a '
                                            'glowing red carnelian gem. Its attack bonus is +3 and its damage is '
                                            '3d8+5. Mages can use this.')


class Test_Inventory(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state = Items_State(**self.items_ini_config.sections)
        self.doors_state = Doors_State(**self.doors_ini_config.sections)
        self.containers_ini_config.sections['Wooden_Chest_1']['contents'] = ('[20xGold_Coin,1xWarhammer,'
                                                                                 '1xMana_Potion,1xHealth_Potion,'
                                                                                 '1xSteel_Shield,1xScale_Mail,'
                                                                                 '1xMagic_Wand]')
        self.containers_state = Containers_State(self.items_state, **self.containers_ini_config.sections)
        self.creatures_state = Creatures_State(self.items_state, **self.creatures_ini_config.sections)
        self.rooms_state = Rooms_State(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **self.rooms_ini_config.sections)
        self.game_state = Game_State(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        longsword = self.command_processor.game_state.items_state.get('Longsword')
        self.scale_mail = self.command_processor.game_state.items_state.get('Scale_Mail')
        self.shield = self.command_processor.game_state.items_state.get('Steel_Shield')
        self.magic_wand = self.command_processor.game_state.items_state.get('Magic_Wand')
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        gold_coin = self.command_processor.game_state.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)
        self.command_processor.game_state.character.pick_up_item(mana_potion, qty=2)
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)

    def test_inventory_1(self):
        result = self.command_processor.process('inventory show')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'INVENTORY')
        self.assertEqual(result[0].message, "INVENTORY command: bad syntax. Should be 'INVENTORY'.")

    def test_inventory_2(self):
        result = self.command_processor.process('inventory')
        self.assertIsInstance(result[0], Inventory_Command_Display_Inventory)
        self.assertEqual(tuple(map(operator.itemgetter(0), result[0].inventory_contents)), (30, 1, 1, 2, 1, 1))
        self.assertIsInstance(result[0].inventory_contents[0][1], Coin)
        self.assertIsInstance(result[0].inventory_contents[1][1], Weapon)
        self.assertIsInstance(result[0].inventory_contents[2][1], Wand)
        self.assertIsInstance(result[0].inventory_contents[3][1], Potion)
        self.assertIsInstance(result[0].inventory_contents[4][1], Armor)
        self.assertIsInstance(result[0].inventory_contents[5][1], Shield)
        self.assertEqual(result[0].message, 'You have 30 gold coins, a longsword, a magic wand, 2 mana potions, a suit '
                                            'of scale mail armor, and a steel shield in your inventory.')


class Test_Leave(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state = Items_State(**self.items_ini_config.sections)
        self.doors_state = Doors_State(**self.doors_ini_config.sections)
        self.containers_ini_config.sections['Wooden_Chest_1']['contents'] = \
            '[20xGold_Coin,1xWarhammer,1xMana_Potion,1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]'
        self.containers_state = Containers_State(self.items_state, **self.containers_ini_config.sections)
        self.creatures_state = Creatures_State(self.items_state, **self.creatures_ini_config.sections)
        self.rooms_state = Rooms_State(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **self.rooms_ini_config.sections)
        self.game_state = Game_State(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True

    def test_leave_1(self):
        result = self.command_processor.process('leave')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'LEAVE')
        self.assertEqual(result[0].message, "LEAVE command: bad syntax. Should be 'LEAVE USING <compass direction> "
                                            "DOOR' or 'LEAVE USING <compass direction> DOORWAY'.")

    def test_leave_2(self):
        result = self.command_processor.process('leave using')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'LEAVE')
        self.assertEqual(result[0].message, "LEAVE command: bad syntax. Should be 'LEAVE USING <compass direction> "
                                            "DOOR' or 'LEAVE USING <compass direction> DOORWAY'.")

    def test_leave_3(self):
        result = self.command_processor.process('leave using north')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'LEAVE')
        self.assertEqual(result[0].message, "LEAVE command: bad syntax. Should be 'LEAVE USING <compass direction> "
                                            "DOOR' or 'LEAVE USING <compass direction> DOORWAY'.")

    def test_leave_4(self):
        result = self.command_processor.process('leave using west door')
        self.assertIsInstance(result[0], Various_Commands_Door_Not_Present)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].message, 'This room does not have a west door.')

    def test_leave_5(self):
        result = self.command_processor.process('leave using north door')
        self.assertIsInstance(result[0], Leave_Command_Left_Room)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'You leave the room via the north door.')
        self.assertIsInstance(result[1], Various_Commands_Entered_Room)
        self.assertIsInstance(result[1].room, Room)
        self.assertEqual(result[1].message, 'Nondescript room. There is a doorway to the east and a wooden door to the '
                                            'south.')
        result = self.command_processor.process('leave using south door')
        self.assertIsInstance(result[0], Leave_Command_Left_Room)
        self.assertEqual(result[0].compass_dir, 'south')
        self.assertEqual(result[0].message, 'You leave the room via the south door.')
        self.assertIsInstance(result[1], Various_Commands_Entered_Room)
        self.assertIsInstance(result[1].room, Room)
        self.assertEqual(result[1].message, 'Entrance room. You see a wooden chest here. There is a kobold in the '
                                            'room. You see a mana potion and 2 health potions on the floor. There '
                                            'is a wooden door to the north and a iron door to the east.')

    def test_leave_6(self):
        self.command_processor = Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.command_processor.process('leave using north door')
        self.command_processor.process('pick lock on east door')
        self.command_processor.process('leave using east door')
        result = self.command_processor.process('leave using north door')
        self.assertIsInstance(result[0], Leave_Command_Left_Room)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'You leave the room via the north door.')
        self.assertIsInstance(result[1], Leave_Command_Won_The_Game)
        self.assertEqual(result[1].message, 'You found the exit to the dungeon. You have won the game!')


class Test_Lock_Command(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None
        self.containers_ini_config = iniconfig_obj_from_ini_text(Chests_Ini_Config_Text)
        self.items_ini_config = iniconfig_obj_from_ini_text(Items_Ini_Config_Text)
        self.doors_ini_config = iniconfig_obj_from_ini_text(Doors_Ini_Config_Text)
        self.creatures_ini_config = iniconfig_obj_from_ini_text(Creatures_Ini_Config_Text)
        self.rooms_ini_config = iniconfig_obj_from_ini_text(Rooms_Ini_Config_Text)

    def setUp(self):
        self.items_state = Items_State(**self.items_ini_config.sections)
        self.doors_state = Doors_State(**self.doors_ini_config.sections)
        self.containers_state = Containers_State(self.items_state, **self.containers_ini_config.sections)
        self.creatures_state = Creatures_State(self.items_state, **self.creatures_ini_config.sections)
        self.rooms_state = Rooms_State(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **self.rooms_ini_config.sections)
        self.game_state = Game_State(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_locked = True
        self.door_title = self.command_processor.game_state.rooms_state.cursor.north_door.title
        self.chest = self.command_processor.game_state.rooms_state.cursor.container_here
        self.chest.is_locked = False
        self.chest_title = self.chest.title

    def test_lock_1(self):
        result = self.command_processor.process('lock')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'LOCK')
        self.assertEqual(result[0].message, "LOCK command: bad syntax. Should be 'LOCK <door name>' or "
                                            "'LOCK <chest name>'."),

    def test_lock_2(self):
        result = self.command_processor.process('lock west door')
        self.assertIsInstance(result[0], Lock_Command_Object_to_Lock_Not_Here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to lock.'),
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked
        self.door_title = self.command_processor.game_state.rooms_state.cursor.north_door.title

    def test_lock_3(self):
        self.door.is_locked = False
        result = self.command_processor.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], Lock_Command_Dont_Possess_Correct_Key)
        self.assertEqual(result[0].object_to_lock_title, self.door_title)
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, f'To lock the {self.door_title} you need a door key.')
        self.assertFalse(self.door.is_locked)

    def test_lock_4(self):
        self.door.is_locked = True
        key = self.command_processor.game_state.items_state.get('Door_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], Lock_Command_Object_Is_Already_Locked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already locked.')
        self.assertTrue(self.door.is_locked)

        self.door.is_locked = False
        result = self.command_processor.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], Lock_Command_Object_Has_Been_Locked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have locked the {self.door_title}.')
        self.assertTrue(self.door.is_locked)

    def test_lock_5(self):
        result = self.command_processor.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], Lock_Command_Dont_Possess_Correct_Key)
        self.assertEqual(result[0].object_to_lock_title, self.chest_title)
        self.assertEqual(result[0].key_needed, 'chest key')
        self.assertEqual(result[0].message, f'To lock the {self.chest_title} you need a chest key.')

    def test_lock_6(self):
        self.chest.is_locked = True
        key = self.command_processor.game_state.items_state.get('Chest_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], Lock_Command_Object_Is_Already_Locked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already locked.')

        self.chest.is_locked = False
        result = self.command_processor.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], Lock_Command_Object_Has_Been_Locked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have locked the {self.chest_title}.')
        self.assertTrue(self.chest.is_locked)
