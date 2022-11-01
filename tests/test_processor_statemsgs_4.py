#!/usr/bin/python3

import math
import unittest

from .context import *
from .testing_data import *

__name__ = 'tests.test_processor_statemsgs_4'


class Test_Status_Command(unittest.TestCase):

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

    def test_status1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status status')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'STATUS')
        self.assertEqual(result[0].message, "STATUS command: bad syntax. Should be 'STATUS'.")

    def test_status2(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        longsword = self.command_processor.game_state.items_state.get('Longsword')
        self.scale_mail = self.command_processor.game_state.items_state.get('Scale_Mail')
        self.shield = self.command_processor.game_state.items_state.get('Steel_Shield')
        self.command_processor.game_state.character.pick_up_item(longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.equip_weapon(longsword)
        self.command_processor.game_state.character.equip_armor(self.scale_mail)
        self.command_processor.game_state.character.equip_shield(self.shield)
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], Status_Command_Output)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ \| Attack: [+-]\d+ \(\d+d[\d+-]+ damage\) - Armor '
                                            r'Class: \d+ \| Weapon: [a-z ]+ - Armor: [a-z ]+ - Shield: [a-z ]+')

    def test_status3(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        staff = self.command_processor.game_state.items_state.get('Staff')
        self.magic_wand = self.command_processor.game_state.items_state.get('Magic_Wand')
        self.command_processor.game_state.character.pick_up_item(staff)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)
        self.command_processor.game_state.character.equip_weapon(staff)
        self.command_processor.game_state.character.equip_wand(self.magic_wand)
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], Status_Command_Output)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: [+-]\d+ '
                                            r'\(\d+d[\d+-]+ damage\) - Armor Class: \d+ \| Wand: [a-z ]+ - Weapon: '
                                             '[a-z ]+ - Armor: [a-z ]+ - Shield: [a-z ]+')

    def test_status4(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], Status_Command_Output)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: no wand or weapon '
                                            r'equipped - Armor Class: \d+ \| Wand: none - Weapon: none - Armor: none - '
                                             'Shield: none')

    def test_status5(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], Status_Command_Output)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ \| Attack: no weapon equipped - Armor Class: \d+ \| '
                                             'Weapon: none - Armor: none - Shield: none')

    def test_status6(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], Status_Command_Output)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: no weapon equipped '
                                            r'- Armor Class: \d+ \| Weapon: none - Armor: none - Shield: none')

    def test_status7(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.take_damage(10)
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], Status_Command_Output)
        self.assertRegex(result[0].message, r'Hit Points: (?!(\d+)/\1)\d+/\d+ - Mana Points: \d+/\d+ \| Attack: no '
                                            r'weapon equipped - Armor Class: \d+ \| Weapon: none - Armor: none - '
                                             'Shield: none')

    def test_status8(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.spend_mana(10)
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], Status_Command_Output)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: (?!(\d+)/\1)\d+/\d+ \| Attack: no '
                                            r'weapon equipped - Armor Class: \d+ \| Weapon: none - Armor: none - '
                                             'Shield: none')


class Test_Take_Command(unittest.TestCase):

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

    def test_take_1(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        (potion_qty, health_potion) = \
            self.command_processor.game_state.rooms_state.cursor.container_here.get('Health_Potion')
        result = self.command_processor.process('take a health potion from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_or_Items_Taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].amount_taken, 1)
        self.assertEqual(result[0].message, 'You took a health potion from the kobold corpse.')
        self.assertTrue(self.command_processor.game_state.character.inventory.contains('Health_Potion'))
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.container_here
                         .contains('Health_Potion'))
        self.assertEqual(self.command_processor.game_state.character.inventory.get('Health_Potion'),
                         (1, health_potion))

    def test_take_2(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take 15 gold coins from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_or_Items_Taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')
        self.assertTrue(self.command_processor.game_state.character.have_item(self.gold_coin))
        self.assertEqual(self.command_processor.game_state.character.item_have_qty(self.gold_coin), 15)
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.container_here.contains('Gold_Coin'))
        self.assertEqual(self.command_processor.game_state.rooms_state.cursor.container_here.get('Gold_Coin'),
                         (15, self.gold_coin))

    def test_take_3(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        (_, short_sword) = \
            self.command_processor.game_state.rooms_state.cursor.container_here.get('Short_Sword')
        result = self.command_processor.process('take one short sword from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_or_Items_Taken)

    def test_take_4(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take one small leather armors from the kobold corpse')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container "
                                            "name>' or 'TAKE <number> <item name> FROM <container name>'."),

    def test_take_5(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take one small leather armor from the kobold corpses')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container "
                                            "name>' or 'TAKE <number> <item name> FROM <container name>'."),

    def test_take_6(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take one small leather armor')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container "
                                            "name>' or 'TAKE <number> <item name> FROM <container name>'."),

    def test_take_7(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take the from the kobold corpse')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container "
                                            "name>' or 'TAKE <number> <item name> FROM <container name>'."),

    def test_take_8(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take the short sword from the')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, "TAKE command: bad syntax. Should be 'TAKE <item name> FROM <container "
                                            "name>' or 'TAKE <number> <item name> FROM <container name>'."),

    def test_take_9(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take the short sword from the sorcerer corpse')  # check
        self.assertIsInstance(result[0], Various_Commands_Container_Not_Found)
        self.assertEqual(result[0].container_not_found_title, 'sorcerer corpse')
        self.assertEqual(result[0].container_present_title, 'kobold corpse')
        self.assertEqual(result[0].message, 'There is no sorcerer corpse here. However, there *is* a kobold corpse '
                                            'here.')

    def test_take_10(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        container = self.command_processor.game_state.rooms_state.cursor.container_here  # check
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process('take the short sword from the sorcerer corpse')
        self.assertIsInstance(result[0], Various_Commands_Container_Not_Found)
        self.assertEqual(result[0].container_not_found_title, 'sorcerer corpse')
        self.assertIs(result[0].container_present_title, None)
        self.assertEqual(result[0].message, 'There is no sorcerer corpse here.')
        self.command_processor.game_state.rooms_state.cursor.container_here = container

    def test_take_11(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take 3 small leather armors from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Trying_to_Take_More_than_Is_Present)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'small leather armor')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, "You can't take 3 small leather armors from the kobold corpse. Only 1 is "
                                            'there.')

    def test_take_12(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.process('take the short sword from the kobold corpse')
        result = self.command_processor.process('take the short sword from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_Not_Found_in_Container)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertIs(result[0].amount_attempted, math.nan)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The kobold corpse doesn't have a short sword on them.")

    def test_take_13(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.process('take the short sword from the kobold corpse')
        result = self.command_processor.process('take three short swords from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_Not_Found_in_Container)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The kobold corpse doesn't have any short swords on them.")

    def test_take_14(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take fifteen gold coins from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_or_Items_Taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

    def test_take_15(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take gold coins from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_or_Items_Taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

    def test_take_16(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take gold coin from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_or_Items_Taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

    def test_take_17(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take a small leather armor from the kobold corpse')
        self.assertIsInstance(result[0], Take_Command_Item_or_Items_Taken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 1)
        self.assertEqual(result[0].item_title, 'small leather armor')
        self.assertEqual(result[0].message, 'You took a small leather armor from the kobold corpse.')

    def test_take_18(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 30, self.gold_coin)
        result = self.command_processor.process('take 30 gold coins from the kobold corpse')
        result = self.command_processor.process('put 15 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 15)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, "You put 15 gold coins on the kobold corpse's person. You have 15 gold "
                                            'coins left.')

    def test_take_19(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 15 gold coins from the kobold corpse')
        result = self.command_processor.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 14)
        self.assertEqual(result[0].message, "You put 1 gold coin on the kobold corpse's person. You have 14 gold "
                                            'coins left.')

    def test_take_20(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 14 gold coins from the kobold corpse')
        result = self.command_processor.process('put 13 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 13)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, "You put 13 gold coins on the kobold corpse's person. You have 1 gold "
                                            'coin left.')

    def test_take_21(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 1 gold coin from the kobold corpse')
        result = self.command_processor.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, "You put 1 gold coin on the kobold corpse's person. You have no more gold "
                                            'coins.')

    def test_take_22(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 2 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Item_Not_in_Inventory)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].message, "You don't have any gold coins in your inventory.")

    def test_take_23(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Item_Not_in_Inventory)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].message, "You don't have a gold coin in your inventory.")

    def test_take_24(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 5 gold coins from the kobold corpse')
        result = self.command_processor.process('put 10 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Trying_to_Put_More_than_You_Have)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_present, 5)
        self.assertEqual(result[0].message, 'You only have 5 gold coins in your inventory.')

    def test_take_25(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 5 gold coins from the kobold corpse')
        result = self.command_processor.process('put 4 gold coins on the kobold corpse')
        result = self.command_processor.process('put 4 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Trying_to_Put_More_than_You_Have)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, 'You only have 1 gold coin in your inventory.')

    def test_take_26(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put a gold coins on the kobold corpse')
        self.assertIsInstance(result[0], Put_Command_Quantity_Unclear)
        self.assertEqual(result[0].message, 'Amount to put unclear. How many do you mean?')

    def test_take_27(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put on the kobold corpse')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_take_28(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put one small leather armor on')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_take_29(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put on')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_take_30(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 1 gold coin in the kobold corpse')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_take_31(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('take three short swords from the wooden chest')
        self.assertIsInstance(result[0], Take_Command_Item_Not_Found_in_Container)
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The wooden chest doesn't have any short swords in it.")

    def test_take_32(self):
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('take gold coin from wooden chest')
        self.assertIsInstance(result[0], Various_Commands_Container_Is_Closed)
        self.assertEqual(result[0].target, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is closed.')


class Test_Unequip_Command(unittest.TestCase):

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
        self.buckler = self.command_processor.game_state.items_state.get('Buckler')
        self.longsword = self.command_processor.game_state.items_state.get('Longsword')
        self.mace = self.command_processor.game_state.items_state.get('Mace')
        self.magic_wand_2 = self.command_processor.game_state.items_state.get('Magic_Wand_2')
        self.magic_wand = self.command_processor.game_state.items_state.get('Magic_Wand')
        self.scale_mail = self.command_processor.game_state.items_state.get('Scale_Mail')
        self.shield = self.command_processor.game_state.items_state.get('Steel_Shield')
        self.studded_leather = self.command_processor.game_state.items_state.get('Studded_Leather')
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.pick_up_item(self.mace)
        self.command_processor.game_state.character.pick_up_item(self.studded_leather)
        self.command_processor.game_state.character.pick_up_item(self.buckler)
        self.command_processor.game_state.character.pick_up_item(self.longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)

    def test_unequip_1(self):
        result = self.command_processor.process('unequip')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'UNEQUIP')
        self.assertEqual(result[0].message, "UNEQUIP command: bad syntax. Should be 'UNEQUIP <armor name>', "
                                            "'UNEQUIP <shield name>', 'UNEQUIP <wand name>', or 'UNEQUIP <weapon "
                                            "name>'.")

    def test_unequip_2(self):
        result = self.command_processor.process('unequip mace')
        self.assertIsInstance(result[0], Unequip_Command_Item_Not_Equipped)
        self.assertEqual(result[0].item_asked_title, 'mace')
        self.assertEqual(result[0].message, "You're not wielding a mace.")

    def test_unequip_3(self):
        result = self.command_processor.process('unequip steel shield')
        self.assertIsInstance(result[0], Unequip_Command_Item_Not_Equipped)
        self.assertEqual(result[0].item_asked_title, 'steel shield')
        self.assertEqual(result[0].message, "You're not carrying a steel shield.")

    def test_unequip_4(self):
        result = self.command_processor.process('unequip scale mail armor')
        self.assertIsInstance(result[0], Unequip_Command_Item_Not_Equipped)
        self.assertEqual(result[0].item_asked_title, 'scale mail armor')
        self.assertEqual(result[0].message, "You're not wearing scale mail armor.")

    def test_unequip_5(self):
        result = self.command_processor.process('unequip magic wand')
        self.assertIsInstance(result[0], Unequip_Command_Item_Not_Equipped)
        self.assertEqual(result[0].item_asked_title, 'magic wand')
        self.assertEqual(result[0].message, "You're not using a magic wand.")

    def test_unequip_6(self):
        result = self.command_processor.process('equip mace')
        result = self.command_processor.process('unequip mace')
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'mace')
        self.assertEqual(result[0].message, "You're no longer wielding a mace. You now can't attack.")

    def test_unequip_7(self):
        result = self.command_processor.process('equip steel shield')
        result = self.command_processor.process('unequip steel shield')
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertRegex(result[0].message, r"^You're no longer carrying a steel shield. Your armor class is \d+.$")

    def test_unequip_8(self):
        result = self.command_processor.process('equip scale mail armor')
        result = self.command_processor.process('unequip scale mail armor')
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertRegex(result[0].message, r"^You're no longer wearing scale mail armor. Your armor class is \d+.$")


class Test_Unlock_Command(unittest.TestCase):

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
        self.chest.is_locked = True
        self.chest_title = self.chest.title

    def test_unlock_1(self):
        result = self.command_processor.process('unlock')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'UNLOCK')
        self.assertEqual(result[0].message, "UNLOCK command: bad syntax. Should be 'UNLOCK <door name>' or "
                                            "'UNLOCK <chest name>'."),

    def test_unlock_2(self):
        result = self.command_processor.process('unlock west door')
        self.assertIsInstance(result[0], Unlock_Command_Object_to_Unlock_Not_Here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to unlock.'),
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked
        self.door_title = self.command_processor.game_state.rooms_state.cursor.north_door.title

    def test_unlock_3(self):
        result = self.command_processor.process(f'unlock {self.door_title}')
        self.assertIsInstance(result[0], Unlock_Command_Dont_Possess_Correct_Key)
        self.assertEqual(result[0].object_to_unlock_title, self.door_title)
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, f'To unlock the {self.door_title} you need a door key.')
        self.assertTrue(self.door.is_locked)

    def test_unlock_4(self):
        self.door.is_locked = False
        key = self.command_processor.game_state.items_state.get('Door_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'unlock {self.door_title}')
        self.assertIsInstance(result[0], Unlock_Command_Object_Is_Already_Unlocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already unlocked.')
        self.assertFalse(self.door.is_locked)

        self.door.is_locked = True
        result = self.command_processor.process(f'unlock {self.door_title}')
        self.assertIsInstance(result[0], Unlock_Command_Object_Has_Been_Unlocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have unlocked the {self.door_title}.')
        self.assertFalse(self.door.is_locked)

    def test_unlock_5(self):
        result = self.command_processor.process(f'unlock {self.chest_title}')
        self.assertIsInstance(result[0], Unlock_Command_Dont_Possess_Correct_Key)
        self.assertEqual(result[0].object_to_unlock_title, self.chest_title)
        self.assertEqual(result[0].key_needed, 'chest key')
        self.assertEqual(result[0].message, f'To unlock the {self.chest_title} you need a chest key.')
        self.assertTrue(self.chest.is_locked)

    def test_unlock_6(self):
        self.chest.is_locked = False
        key = self.command_processor.game_state.items_state.get('Chest_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'unlock {self.chest_title}')
        self.assertIsInstance(result[0], Unlock_Command_Object_Is_Already_Unlocked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already unlocked.')
        self.assertFalse(self.chest.is_locked)

        self.chest.is_locked = True
        result = self.command_processor.process(f'unlock {self.chest_title}')
        self.assertIsInstance(result[0], Unlock_Command_Object_Has_Been_Unlocked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have unlocked the {self.chest_title}.')
        self.assertFalse(self.chest.is_locked)
