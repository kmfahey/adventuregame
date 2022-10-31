#!/usr/bin/python3

import operator
import unittest

from .context import *
from .testing_game_data import *

__name__ = 'adventuregame.test_command_processor_game_state_messages_a_to_eq'


class Test_Attack(unittest.TestCase):

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

    def test_attack_1(self):
        self.command_processor.process('unequip longsword')
        result = self.command_processor.process('attack sorcerer')
        self.assertIsInstance(result[0], Attack_Command_You_Have_No_Weapon_or_Wand_Equipped)
        self.assertEqual(result[0].message, "You have no weapon equipped; you can't attack.")
        self.command_processor.process('equip longsword')

    def test_attack_2(self):
        result = self.command_processor.process('attack sorcerer')
        self.assertIsInstance(result[0], Attack_Command_Opponent_Not_Found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertEqual(result[0].opponent_present, 'kobold')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; but there is a kobold.")

    def test_attack_3(self):
        self.game_state.rooms_state.cursor.creature_here = None
        result = self.command_processor.process('attack sorcerer')
        self.assertIsInstance(result[0], Attack_Command_Opponent_Not_Found)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertIs(result[0].opponent_present, '')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; nobody is here.")

    def test_attack_vs_be_attacked_by_vs_character_death_1(self):
        results = tuple()
        while not len(results) or not isinstance(results[-1], Various_Commands_Foe_Death):
            self.setUp()
            results = self.command_processor.process('attack kobold')
            while not (isinstance(results[-1], Be_Attacked_by_Command_Character_Death)
                       or isinstance(results[-1], Various_Commands_Foe_Death)):
                results += self.command_processor.process('attack kobold')
            for index in range(0, len(results)):
                command_results = results[index]
                if isinstance(command_results, Attack_Command_Attack_Hit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertRegex(results[index].message, r'Your attack on the kobold hit! You did [1-9][0-9]* '
                                                             r'damage.( The kobold turns to attack!)?')
                elif isinstance(command_results, Attack_Command_Attack_Missed):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertEqual(results[index].message, 'Your attack on the kobold missed. It turns to attack!')
                elif isinstance(command_results, Be_Attacked_by_Command_Attacked_and_Not_Hit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertEqual(results[index].message, 'The kobold attacks! Their attack misses.')
                elif isinstance(command_results, Be_Attacked_by_Command_Attacked_and_Hit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertTrue(isinstance(results[index].hit_points_left, int))
                    self.assertRegex(results[index].message, r'The kobold attacks! Their attack hits. They did [0-9]+ '
                                                             r'damage! You have [0-9]+ hit points left.')
                elif isinstance(command_results, Various_Commands_Foe_Death):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertRegex(results[index].message, r'The kobold is slain.')
                elif isinstance(command_results, Be_Attacked_by_Command_Character_Death):
                    self.assertRegex(results[index].message, r'You have died!')
            results_str_join = ' '.join(command_results.__class__.__name__ for command_results in results)
            self.assertRegex(results_str_join, r'(Attack_Command_Attack_(Hit|Missed) '
                                               r'Be_Attacked_by_Command_Attacked_and_(Not_)?Hit)+ '
                                               r'(Attack_Command_Attack_Hit Various_Commands_Foe_Death'
                                               r'|Be_Attacked_by_Command_Character_Death)')
        self.assertIsInstance(self.game_state.rooms_state.cursor.container_here, Corpse)
        corpse_belonging_list = sorted(self.game_state.rooms_state.cursor.container_here.items(),
                                       key=operator.itemgetter(0))
        self.gold_coin = self.game_state.items_state.get('Gold_Coin')
        health_potion = self.game_state.items_state.get('Health_Potion')
        short_sword = self.game_state.items_state.get('Short_Sword')
        small_leather_armor = self.game_state.items_state.get('Small_Leather_Armor')
        expected_list = [('Gold_Coin', (30, self.gold_coin)), ('Health_Potion', (1, health_potion)),
                         ('Short_Sword', (1, short_sword)), ('Small_Leather_Armor', (1, small_leather_armor))]
        self.assertEqual(corpse_belonging_list, expected_list)


class Test_Begin_Game_Command(unittest.TestCase):

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

    def test_begin_game_1(self):
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], Begin_Game_Command_Name_or_Class_Not_Set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "You need to set your character name and class before you begin the game. "
                                            "Use SET NAME <name> to set your name and SET CLASS <Warrior, Thief, Mage "
                                            "or Priest> to select your class.")

    def test_begin_game_2(self):
        self.command_processor.process('set class to Warrior')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], Begin_Game_Command_Name_or_Class_Not_Set)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, 'Warrior')
        self.assertEqual(result[0].message, "You need to set your character name before you begin the game. Use SET "
                                            "NAME <name> to set your name.")

    def test_begin_game_3(self):
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], Begin_Game_Command_Name_or_Class_Not_Set)
        self.assertEqual(result[0].character_name, 'Kerne')
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "You need to set your character class before you begin the game. Use SET "
                                            "CLASS <Warrior, Thief, Mage or Priest> to select your class.")

    def test_begin_game_4(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('begin game now')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN GAME'.")

    def test_begin_game_5(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], Begin_Game_Command_Game_Begins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], Various_Commands_Entered_Room)
        self.assertIsInstance(result[1].room, Room)
        self.assertEqual(result[1].message, 'Entrance room. You see a wooden chest here. There is a kobold in the '
                                            'room. You see a mana potion and 2 health potions on the floor.')


class Test_Cast_Spell_Command(unittest.TestCase):

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

    def test_cast_spell1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], Command_Class_Restricted)
        self.assertEqual(result[0].command, 'CAST SPELL')
        self.assertEqual(result[0].classes, ('mage', 'priest',))
        self.assertEqual(result[0].message, 'Only mages and priests can use the CAST SPELL command.')

    def test_cast_spell2(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        for bad_argument_str in ('cast spell at kobold', 'cast spell at',):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], Command_Bad_Syntax)
            self.assertEqual(result[0].command, 'CAST SPELL')
            self.assertEqual(result[0].message, "CAST SPELL command: bad syntax. Should be 'CAST SPELL'.")

    def test_cast_spell3(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_point_total = self.command_processor.game_state.character.mana_point_total
        mana_spending_outcome = self.command_processor.game_state.character.spend_mana(mana_point_total - 4)
        current_mana_points = 4
        self.assertTrue(mana_spending_outcome)
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], Cast_Spell_Command_Insuffient_Mana)
        self.assertEqual(result[0].current_mana_points, self.command_processor.game_state.character.mana_points)
        self.assertEqual(result[0].mana_point_total, self.command_processor.game_state.character.mana_point_total)
        self.assertEqual(result[0].spell_mana_cost, Spell_Mana_Cost)
        self.assertEqual(result[0].message,  "You don't have enough mana points to cast a spell. Casting a spell costs "
                                            f'{Spell_Mana_Cost} mana points. Your mana points are '
                                            f'{current_mana_points}/{mana_point_total}.')

    def test_cast_spell4(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], Cast_Spell_Command_Cast_Damaging_Spell)
        self.assertEqual(result[0].creature_title, 'kobold')
        self.assertIsInstance(result[0].damage_dealt, int)
        self.assertRegex(result[0].message, r'A magic missile springs from your gesturing hand and unerringly strikes '
                                            r'the kobold. You have done \d+ points of damage.')
        self.assertIsInstance(result[1], (Various_Commands_Foe_Death, Be_Attacked_by_Command_Attacked_and_Not_Hit,
                                          Be_Attacked_by_Command_Attacked_and_Hit))
        if isinstance(result[1], Be_Attacked_by_Command_Attacked_and_Hit) and len(result) == 3:
            self.assertIsInstance(result[2], Be_Attacked_by_Command_Character_Death)

    def test_cast_spell5(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], Cast_Spell_Command_Cast_Healing_Spell)
        self.assertRegex(result[0].message, r'You cast a healing spell on yourself.')
        self.assertIsInstance(result[1], Various_Commands_Underwent_Healing_Effect)


class Test_Close_Command(unittest.TestCase):

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
        self.chest.is_closed = True
        self.chest.is_locked = False
        self.chest_title = self.chest.title
        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_closed = True
        self.door_title = self.door.title

    def test_close_1(self):
        result = self.command_processor.process('close')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'CLOSE')
        self.assertEqual(result[0].message, "CLOSE command: bad syntax. Should be 'CLOSE <door name>' or "
                                            "'CLOSE <chest name>'."),

    def test_close_2(self):
        result = self.command_processor.process(f'close {self.chest_title}')
        self.assertIsInstance(result[0], Close_Command_Object_Is_Already_Closed)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already closed.')
        self.assertTrue(self.chest.is_closed)

    def test_close_3(self):
        self.chest.is_closed = False
        result = self.command_processor.process(f'close {self.chest_title}')
        self.assertIsInstance(result[0], Close_Command_Object_Has_Been_Closed)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have closed the {self.chest_title}.')
        self.assertTrue(self.chest.is_closed)

    def test_close_5(self):
        result = self.command_processor.process('close west door')
        self.assertIsInstance(result[0], Close_Command_Object_to_Close_Not_Here)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'You found no west door here to close.'),

    def test_close_6(self):
        result = self.command_processor.process(f'close {self.door_title}')
        self.assertIsInstance(result[0], Close_Command_Object_Is_Already_Closed)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already closed.')
        self.assertTrue(self.door.is_closed)

    def test_close_7(self):
        self.door.is_closed = False
        result = self.command_processor.process(f'close {self.door_title}')
        self.assertIsInstance(result[0], Close_Command_Object_Has_Been_Closed)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have closed the {self.door_title}.')
        self.assertTrue(self.door.is_closed)


class Test_Command_Processor_Process(unittest.TestCase):

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

    def test_command_not_recognized_in_pregame(self):
        result = self.command_processor.process('juggle')
        self.assertIsInstance(result[0], Command_Not_Recognized)
        self.assertEqual(result[0].command, 'juggle')
        self.assertEqual(result[0].allowed_commands, {'begin_game', 'set_name', 'quit', 'set_class', 'reroll'})
        self.assertEqual(result[0].message, "Command 'juggle' not recognized. Commands allowed before game start are "
                                            "BEGIN GAME, QUIT, REROLL, SET CLASS, and SET NAME.")

    def test_command_not_recognized_during_game(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.command_processor.game_state.game_has_begun = True
        result = self.command_processor.process('juggle')
        self.assertIsInstance(result[0], Command_Not_Recognized)
        self.assertEqual(result[0].command, 'juggle')
        self.assertEqual(result[0].allowed_commands, {'attack', 'cast_spell', 'close', 'drink', 'drop', 'equip',
                                                      'leave', 'inventory', 'leave', 'look_at', 'lock', 'inspect',
                                                      'open', 'pick_lock', 'pick_up', 'put', 'quit', 'status', 'take',
                                                      'unequip', 'unlock'})
        self.assertEqual(result[0].message, "Command 'juggle' not recognized. Commands allowed during the game are "
                                            "ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, INSPECT, INVENTORY, LEAVE, "
                                            "LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, QUIT, STATUS, TAKE, "
                                            "UNEQUIP, and UNLOCK.")

    def test_command_not_allowed_in_pregame(self):
        result = self.command_processor.process('attack kobold')
        self.assertIsInstance(result[0], Command_Not_Allowed_Now)
        self.assertEqual(result[0].command, 'attack')
        self.assertEqual(result[0].allowed_commands, {'begin_game', 'reroll', 'set_name', 'quit', 'set_class'})
        self.assertEqual(result[0].message, "Command 'attack' not allowed before game start. Commands allowed before "
                                            "game start are BEGIN GAME, QUIT, REROLL, SET CLASS, and SET NAME.")

    def test_command_not_allowed_during_game(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.command_processor.game_state.game_has_begun = True
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], Command_Not_Allowed_Now)
        self.assertEqual(result[0].command, 'reroll')
        self.assertEqual(result[0].allowed_commands, {'attack', 'cast_spell', 'close', 'drink', 'drop', 'equip',
                                                      'leave', 'inventory', 'leave', 'look_at', 'lock', 'inspect',
                                                      'open', 'pick_lock', 'pick_up', 'quit', 'put', 'quit', 'status',
                                                      'take', 'unequip', 'unlock'})
        self.assertEqual(result[0].message, "Command 'reroll' not allowed during the game. Commands allowed during "
                                            "the game are ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, INSPECT, "
                                            "INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, QUIT, "
                                            "STATUS, TAKE, UNEQUIP, and UNLOCK.")


class Test_Drink_Command(unittest.TestCase):

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

    def test_drink1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        for bad_argument_str in ('drink', 'drink the', 'drink 2 mana potion', 'drink 1 mana potions'):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], Command_Bad_Syntax)
            self.assertEqual(result[0].command, 'DRINK')
            self.assertEqual(result[0].message, "DRINK command: bad syntax. Should be 'DRINK [THE] <potion name>'.")

    def test_drink2(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('drink health potion')
        self.assertIsInstance(result[0], Drink_Command_Item_Not_in_Inventory)
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].message, "You don't have a health potion in your inventory.")

    def test_drink3(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get('Health_Potion')
        self.command_processor.game_state.character.pick_up_item(health_potion)
        self.command_processor.game_state.character.take_damage(10)
        result = self.command_processor.process('drink health potion')
        self.assertIsInstance(result[0], Various_Commands_Underwent_Healing_Effect)
        self.assertEqual(result[0].amount_healed, 10)
        self.assertRegex(result[0].message, r"You regained 10 hit points. You're fully healed! Your hit points are "
                                            r"(\d+)/\1.")

    def test_drink4(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get('Health_Potion')
        self.command_processor.game_state.character.pick_up_item(health_potion)
        self.command_processor.game_state.character.take_damage(30)
        result = self.command_processor.process('drink health potion')
        self.assertEqual(health_potion.hit_points_recovered, 20)
        self.assertIsInstance(result[0], Various_Commands_Underwent_Healing_Effect)
        self.assertEqual(result[0].amount_healed, 20)
        self.assertRegex(result[0].message, r'You regained 20 hit points. Your hit points are (?!(\d+)/\1)\d+/\d+.')

    def test_drink5(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get('Health_Potion')
        self.command_processor.game_state.character.pick_up_item(health_potion)
        result = self.command_processor.process('drink health potion')
        self.assertIsInstance(result[0], Various_Commands_Underwent_Healing_Effect)
        self.assertEqual(result[0].amount_healed, 0)
        self.assertRegex(result[0].message, r"You didn't regain any hit points. Your hit points are \d+/\d+.")

    def test_drink6(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        self.command_processor.game_state.character.spend_mana(10)
        result = self.command_processor.process('drink mana potion')
        self.assertEqual(mana_potion.mana_points_recovered, 20)
        self.assertIsInstance(result[0], Drink_Command_Drank_Mana_Potion)
        self.assertEqual(result[0].amount_regained, 10)
        self.assertRegex(result[0].message, r'You regained 10 mana points. You have full mana points! Your mana '
                                            r'points are (\d+)/\1.')

    def test_drink7(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        mana_potion.mana_points_recovered = 11
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        self.command_processor.game_state.character.spend_mana(15)
        result = self.command_processor.process('drink mana potion')
        self.assertEqual(mana_potion.mana_points_recovered, 11)
        self.assertIsInstance(result[0], Drink_Command_Drank_Mana_Potion)
        self.assertEqual(result[0].amount_regained, 11)
        self.assertRegex(result[0].message, r'You regained 11 mana points. Your mana points are (?!(\d+)/\1)\d+/\d+.')

    def test_drink8(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process('drink mana potion')
        self.assertEqual(mana_potion.mana_points_recovered, 20)
        self.assertIsInstance(result[0], Drink_Command_Drank_Mana_Potion)
        self.assertEqual(result[0].amount_regained, 0)
        self.assertRegex(result[0].message, r"You didn't regain any mana points. Your mana points are (\d+)/\1.")

    def test_drink9(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process('drink mana potion')
        self.assertIsInstance(result[0], Drink_Command_Drank_Mana_Potion_when_Not_A_Spellcaster)
        self.assertEqual(result[0].message, 'You feel a little strange, but otherwise nothing happens.')

    def test_drink10(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.command_processor.game_state.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin)
        result = self.command_processor.process('drink gold coin')
        self.assertIsInstance(result[0], Drink_Command_Item_Not_Drinkable)
        self.assertEqual(result[0].message, 'A gold coin is not drinkable.')

    def test_drink11(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process('drink 3 mana potions')
        self.assertIsInstance(result[0], Drink_Command_Tried_to_Drink_More_than_Possessed)
        self.assertEqual(result[0].message, "You can't drink 3 mana potions. You only have 1 of them.")


class Test_Drop_Command(unittest.TestCase):

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

    def test_drop_1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop the')  # check
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'DROP')
        self.assertEqual(result[0].message, "DROP command: bad syntax. Should be 'DROP <item name>' or 'DROP <number> "
                                            "<item name>'."),

    def test_drop_2(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop a gold coins')  # check
        self.assertIsInstance(result[0], Drop_Command_Quantity_Unclear)
        self.assertEqual(result[0].message, 'Amount to drop unclear. How many do you mean?')

    def test_drop_3(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop a mana potion')  # check
        self.assertIsInstance(result[0], Drop_Command_Trying_to_Drop_Item_You_Dont_Have)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].message, "You don't have a mana potion in your inventory.")

    def test_drop_4(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop 45 gold coins')  # check
        self.assertIsInstance(result[0], Drop_Command_Trying_to_Drop_More_than_You_Have)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 45)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, "You can't drop 45 gold coins. You only have 30 gold coins in your "
                                            "inventory.")

    def test_drop_5(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop 15 gold coins')  # check
        self.assertIsInstance(result[0], Drop_Command_Dropped_Item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 15)
        self.assertEqual(result[0].amount_on_floor, 15)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, 'You dropped 15 gold coins. You see 15 gold coins here. You have 15 gold '
                                            'coins left.')

        result = self.command_processor.process('drop 14 gold coins')  # check
        self.assertIsInstance(result[0], Drop_Command_Dropped_Item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 14)
        self.assertEqual(result[0].amount_on_floor, 29)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, 'You dropped 14 gold coins. You see 29 gold coins here. You have 1 gold '
                                            'coin left.')

    def test_drop_6(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        self.command_processor.process('pick up 29 gold coins')  # check
        result = self.command_processor.process('drop 1 gold coin')  # check
        self.assertIsInstance(result[0], Drop_Command_Dropped_Item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 29)
        self.assertEqual(result[0].message, 'You dropped a gold coin. You see a gold coin here. You have 29 gold '
                                            'coins left.')

    def test_drop_7(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop 30 gold coins')  # check
        self.assertIsInstance(result[0], Drop_Command_Dropped_Item)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 30)
        self.assertEqual(result[0].amount_on_floor, 30)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, 'You dropped 30 gold coins. You see 30 gold coins here. You have no '
                                            'gold coins left.')

    def test_drop_8(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        longsword = self.items_state.get('Longsword')
        self.command_processor.game_state.character.pick_up_item(longsword)
        self.command_processor.game_state.character.equip_weapon(longsword)
        result = self.command_processor.process('drop longsword')  # check
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "You're no longer wielding a longsword. You now can't attack.")
        self.assertIsInstance(result[1], Drop_Command_Dropped_Item)
        self.assertEqual(result[1].item_title, 'longsword')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a longsword. You see a longsword here. You have no longswords '
                                            'left.')

    def test_drop_9(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        steel_shield = self.items_state.get('Steel_Shield')
        self.command_processor.game_state.character.pick_up_item(steel_shield)
        self.command_processor.game_state.character.equip_shield(steel_shield)
        result = self.command_processor.process('drop steel shield')  # check
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertRegex(result[0].message, r"You're no longer carrying a steel shield. Your armor class is \d+.")
        self.assertIsInstance(result[1], Drop_Command_Dropped_Item)
        self.assertEqual(result[1].item_title, 'steel shield')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a steel shield. You see a steel shield here. You have no steel'
                                            ' shields left.')

    def test_drop_10(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        magic_wand = self.items_state.get('Magic_Wand')
        self.command_processor.game_state.character.pick_up_item(magic_wand)
        self.command_processor.game_state.character.equip_wand(magic_wand)
        result = self.command_processor.process('drop magic wand')  # check
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"You're no longer using a magic wand. You now can't attack.")
        self.assertIsInstance(result[1], Drop_Command_Dropped_Item)
        self.assertEqual(result[1].item_title, 'magic wand')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a magic wand. You see a magic wand here. You have no '
                                            'magic wands left.')

    def test_drop_10(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        staff = self.items_state.get('Staff')
        self.command_processor.game_state.character.pick_up_item(staff)
        self.command_processor.game_state.character.equip_weapon(staff)
        magic_wand = self.items_state.get('Magic_Wand')
        self.command_processor.game_state.character.pick_up_item(magic_wand)
        self.command_processor.game_state.character.equip_wand(magic_wand)
        result = self.command_processor.process('drop magic wand')  # check
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"You're no longer using a magic wand. You're now attacking with your staff.")
        self.assertIsInstance(result[1], Drop_Command_Dropped_Item)
        self.assertEqual(result[1].item_title, 'magic wand')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a magic wand. You see a magic wand here. You have no '
                                            'magic wands left.')

    def test_drop_11(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        staff = self.items_state.get('Staff')
        self.command_processor.game_state.character.pick_up_item(staff)
        self.command_processor.game_state.character.equip_weapon(staff)
        magic_wand = self.items_state.get('Magic_Wand')
        self.command_processor.game_state.character.pick_up_item(magic_wand)
        self.command_processor.game_state.character.equip_wand(magic_wand)
        result = self.command_processor.process('drop staff')  # check
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'staff')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertRegex(result[0].message, r"You're no longer wielding a staff. You're still attacking with your wand.")
        self.assertIsInstance(result[1], Drop_Command_Dropped_Item)
        self.assertEqual(result[1].item_title, 'staff')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a staff. You see a staff here. You have no '
                                            'staffs left.')


class Test_Equip_Command_1(unittest.TestCase):

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
        self.longsword = self.command_processor.game_state.items_state.get('Longsword')
        self.scale_mail = self.command_processor.game_state.items_state.get('Scale_Mail')
        self.shield = self.command_processor.game_state.items_state.get('Steel_Shield')
        self.magic_wand = self.command_processor.game_state.items_state.get('Magic_Wand')
        self.magic_wand_2 = self.command_processor.game_state.items_state.get('Magic_Wand_2')
        self.command_processor.game_state.character_name = 'Arliss'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.pick_up_item(self.longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand_2)

    def test_equip_1(self):
        self.command_processor.game_state.character_name = 'Arliss'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True

        result = self.command_processor.process('equip')
        self.assertIsInstance(result[0], Command_Bad_Syntax)
        self.assertEqual(result[0].command, 'EQUIP')
        self.assertEqual(result[0].message, "EQUIP command: bad syntax. Should be 'EQUIP <armor name>', "
                                            "'EQUIP <shield name>', 'EQUIP <wand name>', or 'EQUIP <weapon name>'.")

        result = self.command_processor.process('drop longsword')
        result = self.command_processor.process('equip longsword')
        self.assertIsInstance(result[0], Equip_Command_No_Such_Item_in_Inventory)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].message, "You don't have a longsword in your inventory.")

    def test_equip_2(self):
        result = self.command_processor.process('equip longsword')
        self.assertIsInstance(result[0], Equip_Command_Class_Cant_Use_Item)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "Mages can't wield longswords.")

    def test_equip_3(self):
        result = self.command_processor.process('equip scale mail armor')
        self.assertIsInstance(result[0], Equip_Command_Class_Cant_Use_Item)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertEqual(result[0].message, "Mages can't wear scale mail armor.")

    def test_equip_4(self):
        result = self.command_processor.process('equip steel shield')
        self.assertIsInstance(result[0], Equip_Command_Class_Cant_Use_Item)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertEqual(result[0].message, "Mages can't carry steel shields.")

    def test_equip_5(self):
        result = self.command_processor.process('equip magic wand')
        self.assertIsInstance(result[0], Equip_Command_Item_Equipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"^You're now using a magic wand. Your attack bonus is [\d+-]+, and your "
                                            r"damage is [\dd+-]+.$")

    def test_equip_6(self):
        self.command_processor.process('equip magic wand')
        result = self.command_processor.process('equip magic wand 2')
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertEqual(result[0].message, "You're no longer using a magic wand. You now can't attack.")
        self.assertIsInstance(result[1], Equip_Command_Item_Equipped)
        self.assertEqual(result[1].item_title, 'magic wand 2')
        self.assertEqual(result[1].item_type, 'wand')
        self.assertRegex(result[1].message, r"^You're now using a magic wand 2. Your attack bonus is [\d+-]+, and "
                                            r"your damage is [\dd+-]+.$")


class Test_Equip_Command_2(unittest.TestCase):

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

    def test_equip_2(self):
        result = self.command_processor.process('equip longsword')
        self.assertIsInstance(result[0], Equip_Command_Item_Equipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertRegex(result[0].message, r"^You're now wielding a longsword. Your attack bonus is [\d+-]+, and "
                                            r"your damage is [\dd+-]+.$")
        result = self.command_processor.process('equip mace')
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "You're no longer wielding a longsword. You now can't attack.")
        self.assertIsInstance(result[1], Equip_Command_Item_Equipped)
        self.assertEqual(result[1].item_title, 'mace')
        self.assertEqual(result[1].item_type, 'weapon')
        self.assertRegex(result[1].message, r"^You're now wielding a mace. Your attack bonus is [\d+-]+, and your "
                                            r"damage is [\dd+-]+.$")

    def test_equip_3(self):
        result = self.command_processor.process('equip scale mail armor')
        self.assertIsInstance(result[0], Equip_Command_Item_Equipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertRegex(result[0].message, r"^You're now wearing scale mail armor. Your armor class is \d+.$")
        result = self.command_processor.process('equip studded leather armor')
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertRegex(result[0].message, r"^You're no longer wearing scale mail armor. Your armor class is \d+.$")
        self.assertIsInstance(result[1], Equip_Command_Item_Equipped)
        self.assertEqual(result[1].item_title, 'studded leather armor')
        self.assertEqual(result[1].item_type, 'armor')
        self.assertRegex(result[1].message, r"^You're now wearing studded leather armor. Your armor class is \d+.$")

    def test_equip_4(self):
        result = self.command_processor.process('equip steel shield')
        self.assertIsInstance(result[0], Equip_Command_Item_Equipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertRegex(result[0].message, r"^You're now carrying a steel shield. Your armor class is \d+.$")
        result = self.command_processor.process('equip buckler')
        self.assertIsInstance(result[0], Various_Commands_Item_Unequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertRegex(result[0].message, r"^You're no longer carrying a steel shield. Your armor class is \d+.$")
        self.assertIsInstance(result[1], Equip_Command_Item_Equipped)
        self.assertEqual(result[1].item_title, 'buckler')
        self.assertEqual(result[1].item_type, 'shield')
        self.assertRegex(result[1].message, r"^You're now carrying a buckler. Your armor class is [\d+-]+.$")

    def test_equip_5(self):
        result = self.command_processor.process('equip magic wand')
        self.assertIsInstance(result[0], Equip_Command_Class_Cant_Use_Item)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].message, "Warriors can't use magic wands.")
