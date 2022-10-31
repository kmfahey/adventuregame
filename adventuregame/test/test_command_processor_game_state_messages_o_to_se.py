#!/usr/bin/python3

import unittest

from .context import *
from .testing_game_data import *

__name__ = 'adventuregame.test_command_processor_command_returns_o_to_se'


class Test_Open_Command(unittest.TestCase):

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
        self.chest = self.command_processor.game_state.rooms_state.cursor.container_here
        self.chest_title = self.chest.title
        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_closed = False
        self.door_title = self.door.title

    def test_open_1(self):
        result = self.command_processor.process('open')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'OPEN')
        self.assertEqual(result[0].message, "OPEN command: bad syntax. Should be 'OPEN <door name>' or "
                                            "'OPEN <chest name>'."),

    def test_open_2(self):
        self.chest.is_closed = True
        self.chest.is_locked = True
        result = self.command_processor.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], Open_Command_Object_Is_Locked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is locked.')

    def test_open_3(self):
        self.chest.is_locked = False
        self.chest.is_closed = False
        self.chest_title = self.chest.title
        result = self.command_processor.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], Open_Command_Object_Is_Already_Open)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already open.')
        self.assertFalse(self.chest.is_closed)

        self.chest.is_closed = True
        result = self.command_processor.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], Open_Command_Object_Has_Been_Opened)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have opened the {self.chest_title}.')
        self.assertFalse(self.chest.is_closed)

    def test_open_4(self):
        result = self.command_processor.process('open west door')
        self.assertIsInstance(result[0], Open_Command_Object_to_Open_Not_Here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to open.'),

    def test_open_5(self):
        result = self.command_processor.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], Open_Command_Object_Is_Already_Open)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already open.')
        self.assertFalse(self.door.is_closed)

    def test_open_6(self):
        self.door.is_closed = True
        result = self.command_processor.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], Open_Command_Object_Has_Been_Opened)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have opened the {self.door_title}.')
        self.assertFalse(self.door.is_closed)

    def test_open_7(self):
        self.door.is_closed = True
        self.door.is_locked = True
        result = self.command_processor.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], Open_Command_Object_Is_Locked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is locked.')
        self.assertTrue(self.door.is_closed)


class Test_Pick_Lock_Command(unittest.TestCase):

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

    def test_pick_lock1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], Command_Class_Restricted)
        self.assertEqual(result[0].command, 'PICK LOCK')
        self.assertEqual(result[0].classes, ('thief',))
        self.assertEqual(result[0].message, 'Only thieves can use the PICK LOCK command.')

    def test_pick_lock2(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        for bad_argument_str in ('pick lock', 'pick lock on', 'pick lock on the', 'pick lock wooden chest'):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], Command_Bad_Syntax)
            self.assertEqual(result[0].command, 'PICK LOCK')
            self.assertEqual(result[0].message, "PICK LOCK command: bad syntax. Should be 'PICK LOCK ON [THE] "
                                                "<chest name>' or 'PICK LOCK ON [THE] <door name>'.")

    def test_pick_lock3(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on west door')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Not_Found)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'This room has no west door.')

    def test_pick_lock4(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on north door')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Not_Locked)
        self.assertEqual(result[0].target_title, 'north door')
        self.assertEqual(result[0].message, 'The north door is not locked.')

    def test_pick_lock5(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Cant_Be_Unlocked_or_Not_Found)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, "The wooden chest is not found or can't be unlocked.")

    def test_pick_lock6(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here.is_locked = False
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Not_Locked)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is not locked.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.container_here.is_locked)

    def test_pick_lock7(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)
        result = self.command_processor.process('pick lock on east door')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Has_Been_Unlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)

    def test_pick_lock8(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)
        result = self.command_processor.process('pick lock on east door')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Has_Been_Unlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)

    def test_pick_lock9(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)
        result = self.command_processor.process('pick lock on east door')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Has_Been_Unlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)

    def test_pick_lock10(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.container_here.is_locked)
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], Pick_Lock_Command_Target_Has_Been_Unlocked)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, 'You have unlocked the wooden chest.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.container_here.is_locked)


class Test_Pick_up_Command(unittest.TestCase):

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

    def test_pick_up_1(self):
        result = self.command_processor.process('pick up the')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PICK UP')
        self.assertEqual(result[0].message, "PICK UP command: bad syntax. Should be 'PICK UP <item name>' or 'PICK UP "
                                            "<number> <item name>'."),

    def test_pick_up_2(self):
        result = self.command_processor.process('pick up a gold coins')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Quantity_Unclear)
        self.assertEqual(result[0].message, 'Amount to pick up unclear. How many do you mean?')

    def test_pick_up_3(self):
        result = self.command_processor.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Item_Not_Found)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 15)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no gold coins here. However, there is 2 health potions and a '
                                            'mana potion here.')

    def test_pick_up_4(self):
        result = self.command_processor.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Item_Not_Found)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no short sword here. However, there is 2 health potions and a '
                                            'mana potion here.')

    def test_pick_up_5(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Item_Not_Found)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ())
        self.assertEqual(result[0].message, 'You see no short sword here.')
        self.command_processor.game_state.rooms_state.move(south=True)

    def test_pick_up_6(self):
        result = self.command_processor.process('pick up 2 mana potions')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Trying_to_Pick_up_More_than_Is_Present)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, "You can't pick up 2 mana potions. Only 1 is here.")

    def test_pick_up_7(self):
        result = self.command_processor.process('pick up a mana potion')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Item_Picked_up)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 1)
        self.assertEqual(result[0].message, 'You picked up a mana potion. You have 1 mana potion.')

    def test_pick_up_8(self):
        result = self.command_processor.process('pick up a health potion')  # check
        result = self.command_processor.process('pick up health potion')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Item_Picked_up)
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 2)
        self.assertEqual(result[0].message, 'You picked up a health potion. You have 2 health potions.')

    def test_pick_up_9(self):
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.rooms_state.cursor.items_here.set('Gold_Coin', 30, gold_coin)
        result = self.command_processor.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Item_Picked_up)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 15)
        self.assertEqual(result[0].message, 'You picked up 15 gold coins. You have 15 gold coins.')
        result = self.command_processor.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], Pick_up_Command_Item_Picked_up)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, 'You picked up 15 gold coins. You have 30 gold coins.')


class Test_Put_Command(unittest.TestCase):

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

    def test_put_1(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('take 20 gold coins from the wooden chest')
        result = self.command_processor.process('put 5 gold coins in the wooden chest')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 5)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, 'You put 5 gold coins in the wooden chest. You have 15 gold coins left.')

    def test_put_2(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        self.command_processor.process('take 15 gold coins from the wooden chest')
        result = self.command_processor.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 14)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have 14 gold coins left.')

    def test_put_3(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        self.command_processor.process('take 14 gold coins from the wooden chest')
        self.command_processor.process('put 12 gold coins in the wooden chest')
        result = self.command_processor.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have 1 gold coin left.')

    def test_put_4(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        self.command_processor.process('take 1 gold coin from the wooden chest')
        result = self.command_processor.process('put 1 gold coin in the wooden chest')
        self.assertIsInstance(result[0], Put_Command_Amount_Put)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, 'You put 1 gold coin in the wooden chest. You have no more gold coins.')

    def test_put_5(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take one short sword from the wooden chest')
        self.assertIsInstance(result[0], Take_Command_Item_Not_Found_in_Container)
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The wooden chest doesn't have a short sword in it.")

    def test_put_6(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('put gold coin in wooden chest')
        self.assertIsInstance(result[0], Various_Commands_Container_Is_Closed)
        self.assertEqual(result[0].target, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is closed.')

    def test_put_7(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('put in the wooden chest')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                         "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                         "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_put_8(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 1 gold coin in')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_put_9(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put in')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),

    def test_put_10(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 1 gold coin on the wooden chest')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, "PUT command: bad syntax. Should be 'PUT <item name> IN <chest name>', "
                                            "'PUT <number> <item name> IN <chest name>', 'PUT <item name> ON "
                                            "<corpse name>', or 'PUT <number> <item name> ON <corpse name>'."),


class Test_Quit_Command(unittest.TestCase):

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

    def test_quit_1(self):
        result = self.command_processor.process('quit the game now')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'QUIT')
        self.assertEqual(result[0].message, "QUIT command: bad syntax. Should be 'QUIT'.")

    def test_quit_2(self):
        result = self.command_processor.process('quit')  # check
        self.assertIsInstance(result[0], Quit_Command_Have_Quit_The_Game)
        self.assertEqual(result[0].message, "You have quit the game.")
        self.assertTrue(self.command_processor.game_state.game_has_ended)


class Test_Set_Name_Vs_Set_Class_Vs_Reroll_Vs_Begin_Game_Commands(unittest.TestCase):

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

    def test_reroll_1(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll stats')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")

    def test_begin_game_1(self):
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], Reroll_Command_Name_or_Class_Not_Set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            "reroll. Use SET NAME <name> to set your name and SET CLASS <Warrior, "
                                            "Thief, Mage or Priest> to select your class.")

    def test_begin_game_2(self):
        self.command_processor.process('set class to Warrior')
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], Reroll_Command_Name_or_Class_Not_Set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, 'Warrior')
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            "reroll. Use SET NAME <name> to set your name.")

    def test_begin_game_3(self):
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], Reroll_Command_Name_or_Class_Not_Set)
        self.assertEqual(result[0].character_name, 'Kerne')
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            "reroll. Use SET CLASS <Warrior, Thief, Mage or Priest> to select your "
                                            "class.")

    def test_begin_game_4(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll my stats')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")

    def test_begin_game_5(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], Set_Name_or_Class_Command_Display_Rolled_Stats)

    def test_set_name_vs_set_class_1(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        for bad_argument_str in ('set class', 'set class dread necromancer'):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], Command_Bad_Syntax)
            self.assertEqual(result[0].command, 'SET CLASS')
            self.assertEqual(result[0].message, "SET CLASS command: bad syntax. Should be 'SET CLASS <Warrior, Thief, "
                                                "Mage or Priest>'.")

        result = self.command_processor.process('set class to Warrior')
        self.assertIsInstance(result[0], Set_Class_Command_Class_Set)
        self.assertEqual(result[0].class_str, 'Warrior')
        self.assertEqual(result[0].message, 'Your class, Warrior, has been set.')

        result = self.command_processor.process('set name')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'SET NAME')
        self.assertEqual(result[0].message, "SET NAME command: bad syntax. Should be 'SET NAME <character name>'.")

        result = self.command_processor.process('set name to Kerne')
        self.assertIsInstance(result[0], Set_Name_Command_Name_Set)
        self.assertEqual(result[0].name, 'Kerne')
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")
        self.assertIsInstance(result[1], Set_Name_or_Class_Command_Display_Rolled_Stats)
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
        result = self.command_processor.process('reroll')
        second_roll = {'strength': result[0].strength, 'dexterity': result[0].dexterity,
                      'constitution': result[0].constitution, 'intelligence': result[0].intelligence,
                      'wisdom': result[0].wisdom, 'charisma': result[0].charisma}
        self.assertIsInstance(result[0], Set_Name_or_Class_Command_Display_Rolled_Stats)
        self.assertNotEqual(first_roll, second_roll)

        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], Begin_Game_Command_Game_Begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_2(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process("begin")
        self.assertIsInstance(result[0], Begin_Game_Command_Game_Begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_3(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process("begin the game now")
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN GAME'.")
        self.assertFalse(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_4(self):
        result = self.command_processor.process('set name to Kerne0')
        self.assertIsInstance(result[0], Set_Name_Command_Invalid_Part)
        self.assertEqual(result[0].name_part, 'Kerne0')
        self.assertEqual(result[0].message, 'The name Kerne0 is invalid; must be a capital letter followed by '
                                            'lowercase letters.')

        result = self.command_processor.process('set name to Kerne MacDonald0 Fahey1')
        self.assertIsInstance(result[0], Set_Name_Command_Invalid_Part)
        self.assertEqual(result[0].name_part, 'MacDonald0')
        self.assertEqual(result[0].message, 'The name MacDonald0 is invalid; must be a capital letter followed by '
                                            'lowercase letters.')
        self.assertIsInstance(result[1], Set_Name_Command_Invalid_Part)
        self.assertEqual(result[1].name_part, 'Fahey1')
        self.assertEqual(result[1].message, 'The name Fahey1 is invalid; must be a capital letter followed by '
                                            'lowercase letters.')

        result = self.command_processor.process('set name to Kerne')
        self.assertIsInstance(result[0], Set_Name_Command_Name_Set)
        self.assertEqual(result[0].name, 'Kerne')
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")

        result = self.command_processor.process('set class to Ranger')
        self.assertIsInstance(result[0], Set_Class_Command_Invalid_Class)
        self.assertEqual(result[0].bad_class, 'Ranger')
        self.assertEqual(result[0].message, "'Ranger' is not a valid class choice. Please choose Warrior, Thief, "
                                            "Mage, or Priest.")

        result = self.command_processor.process('set class to Warrior')
        self.assertIsInstance(result[0], Set_Class_Command_Class_Set)
        self.assertEqual(result[0].class_str, 'Warrior')
        self.assertEqual(result[0].message, 'Your class, Warrior, has been set.')
        self.assertIsInstance(result[1], Set_Name_or_Class_Command_Display_Rolled_Stats)
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
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process("begin the game now")
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN GAME'.")
        self.assertFalse(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_vs_reroll(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll please')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")
        self.assertFalse(self.command_processor.game_state.game_has_begun)
