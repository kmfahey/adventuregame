#!/usr/bin/python3

import unittest

from adventuregame import *
from adventuregame.test.testing_game_data import *

__name__ = 'adventuregame.test_command_processor_command_returns_o_to_se'


class test_open_command(unittest.TestCase):

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
        self.chest_title = self.chest_obj.title
        self.door_obj = self.command_processor_obj.game_state.rooms_state.cursor.north_exit
        self.door_obj.is_closed = False
        self.door_title = self.door_obj.title

    def test_open_1(self):
        result = self.command_processor_obj.process('open')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'OPEN')
        self.assertEqual(result[0].message, "OPEN command: bad syntax. Should be 'OPEN <door name>' or "
                                            "'OPEN <chest name>'."),

    def test_open_2(self):
        self.chest_obj.is_closed = True
        self.chest_obj.is_locked = True
        result = self.command_processor_obj.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], open_command_object_is_locked)
        self.assertEqual(result[0].target_obj, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is locked.')

    def test_open_3(self):
        self.chest_obj.is_locked = False
        self.chest_obj.is_closed = False
        self.chest_title = self.chest_obj.title
        result = self.command_processor_obj.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], open_command_object_is_already_open)
        self.assertEqual(result[0].target_obj, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already open.')
        self.assertFalse(self.chest_obj.is_closed)

        self.chest_obj.is_closed = True
        result = self.command_processor_obj.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], open_command_object_has_been_opened)
        self.assertEqual(result[0].target_obj, self.chest_title)
        self.assertEqual(result[0].message, f'You have opened the {self.chest_title}.')
        self.assertFalse(self.chest_obj.is_closed)

    def test_open_4(self):
        result = self.command_processor_obj.process('open west door')
        self.assertIsInstance(result[0], open_command_object_to_open_not_here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to open.'),

    def test_open_5(self):
        result = self.command_processor_obj.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], open_command_object_is_already_open)
        self.assertEqual(result[0].target_obj, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already open.')
        self.assertFalse(self.door_obj.is_closed)

    def test_open_6(self):
        self.door_obj.is_closed = True
        result = self.command_processor_obj.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], open_command_object_has_been_opened)
        self.assertEqual(result[0].target_obj, self.door_title)
        self.assertEqual(result[0].message, f'You have opened the {self.door_title}.')
        self.assertFalse(self.door_obj.is_closed)

    def test_open_7(self):
        self.door_obj.is_closed = True
        self.door_obj.is_locked = True
        result = self.command_processor_obj.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], open_command_object_is_locked)
        self.assertEqual(result[0].target_obj, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is locked.')
        self.assertTrue(self.door_obj.is_closed)


class test_pick_lock_command(unittest.TestCase):

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

    def test_pick_lock1(self):
        self.command_processor_obj.game_state.character_name = 'Niath'
        self.command_processor_obj.game_state.character_class = 'Warrior'
        self.game_state_obj.game_has_begun = True
        result = self.command_processor_obj.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], command_class_restricted)
        self.assertEqual(result[0].command, 'PICK LOCK')
        self.assertEqual(result[0].classes, ('thief',))
        self.assertEqual(result[0].message, 'Only thieves can use the PICK LOCK command.')

    def test_pick_lock2(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        for bad_argument_str in ('pick lock', 'pick lock on', 'pick lock on the', 'pick lock wooden chest'):
            result = self.command_processor_obj.process(bad_argument_str)
            self.assertIsInstance(result[0], command_bad_syntax)
            self.assertEqual(result[0].command, 'PICK LOCK')
            self.assertEqual(result[0].message, "PICK LOCK command: bad syntax. Should be 'PICK LOCK ON [THE] "
                                                "<chest name>' or 'PICK LOCK ON [THE] <door name>'.")

    def test_pick_lock3(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        result = self.command_processor_obj.process('pick lock on west door')
        self.assertIsInstance(result[0], pick_lock_command_target_not_found)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'This room has no west door.')

    def test_pick_lock4(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        result = self.command_processor_obj.process('pick lock on north door')
        self.assertIsInstance(result[0], pick_lock_command_target_not_locked)
        self.assertEqual(result[0].target_title, 'north door')
        self.assertEqual(result[0].message, 'The north door is not locked.')

    def test_pick_lock5(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        self.command_processor_obj.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor_obj.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], pick_lock_command_target_cant_be_unlocked_or_not_found)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, "The wooden chest is not found or can't be unlocked.")

    def test_pick_lock6(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.is_locked = False
        result = self.command_processor_obj.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], pick_lock_command_target_not_locked)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is not locked.')
        self.assertFalse(self.command_processor_obj.game_state.rooms_state.cursor.container_here.is_locked)

    def test_pick_lock7(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.east_exit.is_locked)
        result = self.command_processor_obj.process('pick lock on east door')
        self.assertIsInstance(result[0], pick_lock_command_target_has_been_unlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor_obj.game_state.rooms_state.cursor.east_exit.is_locked)

    def test_pick_lock8(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.east_exit.is_locked)
        result = self.command_processor_obj.process('pick lock on east door')
        self.assertIsInstance(result[0], pick_lock_command_target_has_been_unlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor_obj.game_state.rooms_state.cursor.east_exit.is_locked)

    def test_pick_lock9(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.east_exit.is_locked)
        result = self.command_processor_obj.process('pick lock on east door')
        self.assertIsInstance(result[0], pick_lock_command_target_has_been_unlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor_obj.game_state.rooms_state.cursor.east_exit.is_locked)

    def test_pick_lock10(self):
        self.command_processor_obj.game_state.character_name = 'Lidda'
        self.command_processor_obj.game_state.character_class = 'Thief'
        self.game_state_obj.game_has_begun = True
        self.assertTrue(self.command_processor_obj.game_state.rooms_state.cursor.container_here.is_locked)
        result = self.command_processor_obj.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], pick_lock_command_target_has_been_unlocked)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, 'You have unlocked the wooden chest.')
        self.assertFalse(self.command_processor_obj.game_state.rooms_state.cursor.container_here.is_locked)


class test_pick_up_command(unittest.TestCase):

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

    def test_pick_up_1(self):
        result = self.command_processor_obj.process('pick up the')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PICK UP')
        self.assertEqual(result[0].message, "PICK UP command: bad syntax. Should be 'PICK UP <item name>' or 'PICK UP <number> <item name>'."),

    def test_pick_up_2(self):
        result = self.command_processor_obj.process('pick up a gold coins')  # check
        self.assertIsInstance(result[0], pick_up_command_quantity_unclear)
        self.assertEqual(result[0].message, 'Amount to pick up unclear. How many do you mean?')

    def test_pick_up_3(self):
        result = self.command_processor_obj.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], pick_up_command_item_not_found)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 15)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no gold coins here. However, there is 2 health potions and a mana potion here.')

    def test_pick_up_4(self):
        result = self.command_processor_obj.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], pick_up_command_item_not_found)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no short sword here. However, there is 2 health potions and a mana potion here.')

    def test_pick_up_5(self):
        self.command_processor_obj.game_state.rooms_state.move(north=True)
        result = self.command_processor_obj.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], pick_up_command_item_not_found)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ())
        self.assertEqual(result[0].message, 'You see no short sword here.')
        self.command_processor_obj.game_state.rooms_state.move(south=True)

    def test_pick_up_6(self):
        result = self.command_processor_obj.process('pick up 2 mana potions')  # check
        self.assertIsInstance(result[0], pick_up_command_trying_to_pick_up_more_than_is_present)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, "You can't pick up 2 mana potions. Only 1 is here.")

    def test_pick_up_7(self):
        result = self.command_processor_obj.process('pick up a mana potion')  # check
        self.assertIsInstance(result[0], pick_up_command_item_picked_up)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 1)
        self.assertEqual(result[0].message, 'You picked up a mana potion. You have 1 mana potion.')

    def test_pick_up_8(self):
        result = self.command_processor_obj.process('pick up a health potion')  # check
        result = self.command_processor_obj.process('pick up health potion')  # check
        self.assertIsInstance(result[0], pick_up_command_item_picked_up)
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 2)
        self.assertEqual(result[0].message, 'You picked up a health potion. You have 2 health potions.')

    def test_pick_up_9(self):
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


class test_put_command(unittest.TestCase):

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

    def test_put_1(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor_obj.process('take 20 gold coins from the wooden chest')
        result = self.command_processor_obj.process('put 5 gold coins in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 5)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, 'You put 5 gold coins in the wooden chest. You have 15 gold coins left.')

    def test_put_2(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        self.command_processor_obj.process('take 15 gold coins from the wooden chest')
        result = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 14)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have 14 gold coins left.')

    def test_put_3(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        self.command_processor_obj.process('take 14 gold coins from the wooden chest')
        self.command_processor_obj.process('put 12 gold coins in the wooden chest')
        result = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have 1 gold coin left.')

    def test_put_4(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        self.command_processor_obj.process('take 1 gold coin from the wooden chest')
        result = self.command_processor_obj.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], put_command_amount_put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have no more gold coins.')

    def test_put_5(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        result = self.command_processor_obj.process('take one short sword from the wooden chest')
        self.assertIsInstance(result[0], take_command_item_not_found_in_container)
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The wooden chest doesn't have a short sword in it.")

    def test_put_6(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor_obj.process('put gold coin in wooden chest')
        self.assertIsInstance(result[0], various_commands_container_is_closed)
        self.assertEqual(result[0].target_obj, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is closed.')

    def test_put_7(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor_obj.process('put in the wooden chest')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_put_8(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        result = self.command_processor_obj.process('put 1 gold coin in')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_put_9(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        result = self.command_processor_obj.process('put in')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_put_10(self):
        self.game_state_obj.rooms_state.cursor.container_here.is_locked = None
        self.game_state_obj.rooms_state.cursor.container_here.is_closed = False
        self.command_processor_obj.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin_obj)
        result = self.command_processor_obj.process('put 1 gold coin on the wooden chest')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),


class test_quit_command(unittest.TestCase):

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

    def test_quit_1(self):
        result = self.command_processor_obj.process('quit the game now')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'QUIT')
        self.assertEqual(result[0].message, "QUIT command: bad syntax. Should be 'QUIT'.")

    def test_quit_2(self):
        result = self.command_processor_obj.process('quit')  # check
        self.assertIsInstance(result[0], quit_command_have_quit_the_game)
        self.assertEqual(result[0].message, "You have quit the game.")
        self.assertTrue(self.command_processor_obj.game_state.game_has_ended)


class test_set_name_vs_set_class_vs_reroll_vs_begin_game_commands(unittest.TestCase):

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

    def test_reroll_1(self):
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('reroll stats')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")

    def test_begin_game_1(self):
        result = self.command_processor_obj.process('reroll')
        self.assertIsInstance(result[0], reroll_command_name_or_class_not_set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            "reroll. Use SET NAME <name> to set your name and SET CLASS <Warrior, "
                                            "Thief, Mage or Priest> to select your class.")

    def test_begin_game_2(self):
        self.command_processor_obj.process('set class to Warrior')
        result = self.command_processor_obj.process('reroll')
        self.assertIsInstance(result[0], reroll_command_name_or_class_not_set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, 'Warrior')
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            "reroll. Use SET NAME <name> to set your name.")

    def test_begin_game_3(self):
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('reroll')
        self.assertIsInstance(result[0], reroll_command_name_or_class_not_set)
        self.assertEqual(result[0].character_name, 'Kerne')
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            "reroll. Use SET CLASS <Warrior, Thief, Mage or Priest> to select your "
                                            "class.")

    def test_begin_game_4(self):
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('reroll my stats')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")

    def test_begin_game_5(self):
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('reroll')
        self.assertIsInstance(result[0], set_name_or_class_command_display_rolled_stats)

    def test_set_name_vs_set_class_1(self):
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
        for bad_argument_str in ('set class', 'set class dread necromancer'):
            result = self.command_processor_obj.process(bad_argument_str)
            self.assertIsInstance(result[0], command_bad_syntax)
            self.assertEqual(result[0].command, 'SET CLASS')
            self.assertEqual(result[0].message, "SET CLASS command: bad syntax. Should be 'SET CLASS <Warrior, Thief, Mage or Priest>'.")

        result = self.command_processor_obj.process('set class to Warrior')
        self.assertIsInstance(result[0], set_class_command_class_set)
        self.assertEqual(result[0].class_str, 'Warrior')
        self.assertEqual(result[0].message, 'Your class, Warrior, has been set.')

        result = self.command_processor_obj.process('set name')  # check
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'SET NAME')
        self.assertEqual(result[0].message, "SET NAME command: bad syntax. Should be 'SET NAME <character name>'.")

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
                                            f'Charisma {result[1].charisma}.\nWould you like to reroll or begin game?')
        first_roll = {'strength': result[1].strength, 'dexterity': result[1].dexterity,
                      'constitution': result[1].constitution, 'intelligence': result[1].intelligence,
                      'wisdom': result[1].wisdom, 'charisma': result[1].charisma}
        result = self.command_processor_obj.process('reroll')
        second_roll = {'strength': result[0].strength, 'dexterity': result[0].dexterity,
                      'constitution': result[0].constitution, 'intelligence': result[0].intelligence,
                      'wisdom': result[0].wisdom, 'charisma': result[0].charisma}
        self.assertIsInstance(result[0], set_name_or_class_command_display_rolled_stats)
        self.assertNotEqual(first_roll, second_roll)

        result = self.command_processor_obj.process('begin game')
        self.assertIsInstance(result[0], begin_game_command_game_begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_vs_set_class_2(self):
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process("begin")
        self.assertIsInstance(result[0], begin_game_command_game_begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_vs_set_class_3(self):
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process("begin the game now")
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN GAME'.")
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_vs_set_class_4(self):
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

    def test_set_name_vs_set_class_vs_begin_game(self):
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process("begin the game now")
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN GAME'.")
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)

    def test_set_name_vs_set_class_vs_reroll(self):
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
        self.command_processor_obj.process('set class to Warrior')
        self.command_processor_obj.process('set name to Kerne')
        result = self.command_processor_obj.process('reroll please')
        self.assertIsInstance(result[0], command_bad_syntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")
        self.assertFalse(self.command_processor_obj.game_state.game_has_begun)
