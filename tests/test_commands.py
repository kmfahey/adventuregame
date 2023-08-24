#!/usr/bin/python3

import operator
import unittest

import iniconfig

from .context import advgame as advg


__name__ = 'tests.test_commands'

containers_ini_config = iniconfig.IniConfig('./testing_data/containers.ini')
items_ini_config = iniconfig.IniConfig('./testing_data/items.ini')
doors_ini_config = iniconfig.IniConfig('./testing_data/doors.ini')
creatures_ini_config = iniconfig.IniConfig('./testing_data/creatures.ini')
rooms_ini_config = iniconfig.IniConfig('./testing_data/rooms.ini')


class Test_Attack_1(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
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
        result = self.command_processor.process('attack')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'ATTACK')
        self.assertEqual(result[0].message, "ATTACK command: bad syntax. Should be 'ATTACK\u00A0<creature\u00A0name>'.")

    def test_attack_2(self):
        self.command_processor.process('unequip longsword')
        result = self.command_processor.process('attack sorcerer')
        self.assertIsInstance(result[0], advg.stmsg.attack.YouHaveNoWeaponOrWandEquipped)
        self.assertEqual(result[0].message, "You have no weapon equipped; you can't attack.")
        self.command_processor.process('equip longsword')

    def test_attack_3(self):
        result = self.command_processor.process('attack sorcerer')
        self.assertIsInstance(result[0], advg.stmsg.attack.OpponentNotFound)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertEqual(result[0].opponent_present, 'kobold')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; but there is a kobold.")

    def test_attack_4(self):
        self.game_state.rooms_state.cursor.creature_here = None
        result = self.command_processor.process('attack sorcerer')
        self.assertIsInstance(result[0], advg.stmsg.attack.OpponentNotFound)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertIs(result[0].opponent_present, '')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; nobody is here.")

    def test_attack_5(self):
        self.game_state.rooms_state.cursor.creature_here = None
        result = self.command_processor.process('attack sorcerer')
        self.assertIsInstance(result[0], advg.stmsg.attack.OpponentNotFound)
        self.assertEqual(result[0].creature_title_given, 'sorcerer')
        self.assertIs(result[0].opponent_present, '')
        self.assertEqual(result[0].message, "This room doesn't have a sorcerer; nobody is here.")

    def test_attack_vs_be_attacked_by_vs_character_death_2(self):
        results = tuple()
        while not len(results) or not isinstance(results[-1], advg.stmsg.various.FoeDeath):
            self.setUp()
            results = self.command_processor.process('attack kobold')
            while not (isinstance(results[-1], advg.stmsg.be_atkd.CharacterDeath)
                       or isinstance(results[-1], advg.stmsg.various.FoeDeath)):
                results += self.command_processor.process('attack kobold')
            for index in range(0, len(results)):
                command_results = results[index]
                if isinstance(command_results, advg.stmsg.attack.AttackHit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertRegex(results[index].message, r'Your attack on the kobold hit! You did [1-9][0-9]* '
                                                             r'damage.( The kobold turns to attack!)?')
                elif isinstance(command_results, advg.stmsg.attack.AttackMissed):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertEqual(results[index].message, 'Your attack on the kobold missed. It turns to attack!')
                elif isinstance(command_results, advg.stmsg.be_atkd.AttackedAndNotHit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertEqual(results[index].message, 'The kobold attacks! Their attack misses.')
                elif isinstance(command_results, advg.stmsg.be_atkd.AttackedAndHit):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertTrue(isinstance(results[index].damage_done, int))
                    self.assertTrue(isinstance(results[index].hit_points_left, int))
                    self.assertRegex(results[index].message, r'The kobold attacks! Their attack hits. They did [0-9]+ '
                                                             r'damage! You have [0-9]+ hit points left.')
                elif isinstance(command_results, advg.stmsg.various.FoeDeath):
                    self.assertEqual(results[index].creature_title, 'kobold')
                    self.assertRegex(results[index].message, r'The kobold is slain.')
                elif isinstance(command_results, advg.stmsg.be_atkd.CharacterDeath):
                    self.assertRegex(results[index].message, r'You have died!')
            results_str_join = ' '.join(command_results.__class__.__name__ for command_results in results)

            # Got a little clever here. The sequence of `GameStateMessage` subclass objects that are returned during
            # a combat follows a particular pattern, and any deviation from that pattern is an error. I conjoin the
            # classnames into a string and use regular expressions to parse the sequence to verify that the required
            # pattern is conformed to.

            self.assertRegex(results_str_join,
                             r'(Attack(Hit|Missed) AttackedAnd(Not)?Hit)+ '
                             + r'(AttackHit FoeDeath|CharacterDeath)')
        self.assertIsInstance(self.game_state.rooms_state.cursor.container_here, advg.Corpse)
        corpse_belonging_list = sorted(self.game_state.rooms_state.cursor.container_here.items(),
                                       key=operator.itemgetter(0))
        self.gold_coin = self.game_state.items_state.get('Gold_Coin')
        health_potion = self.game_state.items_state.get('Health_Potion')
        short_sword = self.game_state.items_state.get('Short_Sword')
        small_leather_armor = self.game_state.items_state.get('Small_Leather_Armor')
        expected_list = [('Gold_Coin', (30, self.gold_coin)), ('Health_Potion', (1, health_potion)),
                         ('Short_Sword', (1, short_sword)), ('Small_Leather_Armor', (1, small_leather_armor))]
        self.assertEqual(corpse_belonging_list, expected_list)


class Test_Attack_2(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.game_state.character_name = 'Mialee'
        self.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        self.game_state.character.pick_up_item(self.items_state.get('Magic_Wand'))
        self.game_state.character.equip_wand(self.items_state.get('Magic_Wand'))

    # I'm trying to test how the specific `GameStateMessage` subclasses behave but the only way to get them is to run
    # an entire combat and gamble that both a hit and a miss occur in the fight. The inner loop continues til both occur
    # or the combat ends in a death, and the outer loop repeats indefinitely, but is continue'd if combat ended before
    # both show up to retry, or break'd if both objects I'm testing have occurred.

    def test_attack_1(self):
        results = tuple()
        kobold = self.game_state.rooms_state.cursor.creature_here
        while True:
            self.setUp()
            if kobold.hit_points < kobold.hit_point_total:
                kobold.heal_damage(kobold.hit_point_total - kobold.hit_points)
            results = self.command_processor.process('attack kobold')
            while ((not any(isinstance(result, advg.stmsg.attack.AttackMissed) for result in results)
                    and not any(isinstance(result, advg.stmsg.attack.AttackHit) for result in results))
                    or (isinstance(results[-1], (advg.stmsg.attack.AttackHit, advg.stmsg.be_atkd.CharacterDeath)))):
                results += self.command_processor.process('attack kobold')
            if isinstance(results[-1], (advg.stmsg.attack.AttackHit, advg.stmsg.be_atkd.CharacterDeath)):
                continue
            else:
                break
        for index in range(0, len(results)):
            result = results[index]
            if isinstance(result, advg.stmsg.attack.AttackMissed):
                self.assertEqual(result.creature_title, 'kobold')
                self.assertEqual(result.weapon_type, 'wand')
                self.assertEqual(result.message, 'A bolt of energy from your wand misses the kobold. It turns to '
                                                 'attack!')
            elif isinstance(result, advg.stmsg.attack.AttackHit):
                self.assertEqual(result.creature_title, 'kobold')
                self.assertEqual(result.weapon_type, 'wand')
                self.assertRegex(result.message, r'A bolt of energy from your wand hits the kobold! You did \d+ damage.'
                                                 r'( The kobold turns to attack!)?')


class Test_Begin_Game(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_begin_game_1(self):
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.NameOrClassNotSet)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, 'You need to set your character name and class before you begin the game. '
                                            'Use SET NAME <name> to set your name and SET CLASS <Warrior, Thief, Mage '
                                            'or Priest> to select your class.')

    def test_begin_game_2(self):
        self.command_processor.process('set class to Warrior')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.NameOrClassNotSet)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, 'Warrior')
        self.assertEqual(result[0].message, 'You need to set your character name before you begin the game. Use SET '
                                            'NAME <name> to set your name.')

    def test_begin_game_3(self):
        self.command_processor.process('set name to Niath')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.NameOrClassNotSet)
        self.assertEqual(result[0].character_name, 'Niath')
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, 'You need to set your character class before you begin the game. Use SET '
                                            'CLASS <Warrior, Thief, Mage or Priest> to select your class.')

    def test_begin_game_4(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Niath')
        result = self.command_processor.process('begin game now')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN\u00A0GAME'.")

    def test_begin_game_5(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Niath')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBegins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[-1], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[-1].room, advg.Room)
        self.assertEqual(result[-1].message, 'Entrance room.\nYou see a wooden chest here.\nThere is a kobold in the '
                                            'room.\nYou see a mana potion and 2 health potions on the floor.\nThere '
                                            'is an iron door to the north and an iron door to the east.')

    def test_begin_game_6(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Niath')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBegins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'studded leather armor')
        self.assertEqual(result[1].item_type, 'armor')
        self.assertRegex(result[1].message, r"^You're now wearing a suit of studded leather armor. Your armor class is now \d+.")
        self.assertIsInstance(result[2], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[2].item_title, 'buckler')
        self.assertEqual(result[2].item_type, 'shield')
        self.assertRegex(result[2].message, r"^You're now carrying a buckler. Your armor class is now \d+.")
        self.assertIsInstance(result[3], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[3].item_title, 'longsword')
        self.assertEqual(result[3].item_type, 'weapon')
        self.assertRegex(result[3].message, r"^You're now wielding a longsword. Your attack bonus is now [\d+-]+ and your"
                                            r' weapon damage is now [\dd+-]+.$')
        self.assertIsInstance(result[4], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[4].room, advg.Room)
        self.assertEqual(result[4].message, 'Entrance room.\nYou see a wooden chest here.\nThere is a kobold in the '
                                            'room.\nYou see a mana potion and 2 health potions on the floor.\nThere '
                                            'is an iron door to the north and an iron door to the east.')

    def test_begin_game_7(self):
        self.command_processor.process('set class to Thief')
        self.command_processor.process('set name to Lidda')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBegins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'studded leather armor')
        self.assertEqual(result[1].item_type, 'armor')
        self.assertRegex(result[1].message, r"^You're now wearing a suit of studded leather armor. Your armor class is "
                                            r'now \d+')
        self.assertIsInstance(result[2], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[2].item_title, 'rapier')
        self.assertEqual(result[2].item_type, 'weapon')
        self.assertRegex(result[2].message, r"^You're now wielding a rapier. Your attack bonus is now [\d+-]+ and your"
                                            r' weapon damage is now [\dd+-]+.$')
        self.assertIsInstance(result[3], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[3].room, advg.Room)
        self.assertEqual(result[3].message, 'Entrance room.\nYou see a wooden chest here.\nThere is a kobold in the '
                                            'room.\nYou see a mana potion and 2 health potions on the floor.\nThere '
                                            'is an iron door to the north and an iron door to the east.')

    def test_begin_game_8(self):
        self.command_processor.process('set class to Priest')
        self.command_processor.process('set name to Tordek')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBegins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'studded leather armor')
        self.assertEqual(result[1].item_type, 'armor')
        self.assertRegex(result[1].message, r"^You're now wearing a suit of studded leather armor. Your armor class is now \d+")
        self.assertIsInstance(result[2], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[2].item_title, 'buckler')
        self.assertEqual(result[2].item_type, 'shield')
        self.assertRegex(result[2].message, r"^You're now carrying a buckler. Your armor class is now \d+.")
        self.assertIsInstance(result[3], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[3].item_title, 'mace')
        self.assertEqual(result[3].item_type, 'weapon')
        self.assertRegex(result[3].message, r"^You're now wielding a mace. Your attack bonus is now [\d+-]+ and your"
                                            r' weapon damage is now [\dd+-]+.$')
        self.assertIsInstance(result[4], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[4].room, advg.Room)
        self.assertEqual(result[4].message, 'Entrance room.\nYou see a wooden chest here.\nThere is a kobold in the '
                                            'room.\nYou see a mana potion and 2 health potions on the floor.\nThere '
                                            'is an iron door to the north and an iron door to the east.')

    def test_begin_game_9(self):
        self.command_processor.process('set class to Mage')
        self.command_processor.process('set name to Mialee')
        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBegins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'staff')
        self.assertEqual(result[1].item_type, 'weapon')
        self.assertRegex(result[1].message, r"^You're now wielding a staff. Your attack bonus is now [\d+-]+ and your"
                                            r' weapon damage is now [\dd+-]+.$')
        self.assertIsInstance(result[2], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[2].room, advg.Room)
        self.assertEqual(result[2].message, 'Entrance room.\nYou see a wooden chest here.\nThere is a kobold in the '
                                            'room.\nYou see a mana potion and 2 health potions on the floor.\nThere '
                                            'is an iron door to the north and an iron door to the east.')


class Test_Cast_Spell(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_cast_spell1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], advg.stmsg.command.ClassRestricted)
        self.assertEqual(result[0].command, 'CAST SPELL')
        self.assertEqual(result[0].classes, ('mage', 'priest',))
        self.assertEqual(result[0].message, 'Only mages and priests can use the CAST SPELL command.')

    def test_cast_spell2(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        for bad_argument_str in ('cast spell at kobold', 'cast spell at',):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
            self.assertEqual(result[0].command, 'CAST SPELL')
            self.assertEqual(result[0].message, "CAST SPELL command: bad syntax. Should be 'CAST\u00A0SPELL'.")

    def test_cast_spell3(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_point_total = self.command_processor.game_state.character.mana_point_total
        mana_spending_outcome = self.command_processor.game_state.character.spend_mana(mana_point_total - 4)
        current_mana_points = 4
        self.assertTrue(mana_spending_outcome)
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], advg.stmsg.castspl.InsufficientMana)
        self.assertEqual(result[0].current_mana_points, self.command_processor.game_state.character.mana_points)
        self.assertEqual(result[0].mana_point_total, self.command_processor.game_state.character.mana_point_total)
        self.assertEqual(result[0].spell_mana_cost, advg.SPELL_MANA_COST)
        self.assertEqual(result[0].message,  "You don't have enough mana points to cast a spell. Casting a spell costs "
                                            f'{advg.SPELL_MANA_COST} mana points. Your mana points are '
                                            f'{current_mana_points}/{mana_point_total}.')

    def test_cast_spell4(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], advg.stmsg.castspl.CastDamagingSpell)
        self.assertEqual(result[0].creature_title, 'kobold')
        self.assertIsInstance(result[0].damage_dealt, int)
        self.assertRegex(result[0].message, r'A magic missile springs from your gesturing hand and unerringly strikes '
                                            r'the kobold. You have done \d+ points of damage.')
        self.assertIsInstance(result[1], (advg.stmsg.various.FoeDeath,
                                          advg.stmsg.be_atkd.AttackedAndNotHit,
                                          advg.stmsg.be_atkd.AttackedAndHit))
        if not isinstance(result[1], advg.stmsg.various.FoeDeath):
            spell_cast_count = 1
            while result[0].damage_dealt >= 20:
                self.command_processor.game_state.rooms_state.cursor.creature_here.heal_damage(20)
                result = self.command_processor.process('cast spell')
                spell_cast_count += 1
            self.assertRegex(result[0].message, 'A magic missile springs from your gesturing hand and unerringly strikes '
                                                r'the kobold. You have done \d+ points of damage. The kobold turns to '
                                                'attack!')
            self.assertEqual(self.command_processor.game_state.character.mana_points
                             + spell_cast_count * advg.SPELL_MANA_COST,
                             self.command_processor.game_state.character.mana_point_total)

    def test_cast_spell5(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('cast spell')
        self.assertIsInstance(result[0], advg.stmsg.castspl.CastHealingSpell)
        self.assertRegex(result[0].message, r'You cast a healing spell on yourself.')
        self.assertIsInstance(result[1], advg.stmsg.various.UnderwentHealingEffect)
        self.assertEqual(self.command_processor.game_state.character.mana_points + advg.SPELL_MANA_COST,
                         self.command_processor.game_state.character.mana_point_total)


class Test_Close(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
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
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'CLOSE')
        self.assertEqual(result[0].message, "CLOSE command: bad syntax. Should be 'CLOSE\u00A0<door\u00A0name>' or "
                                            "'CLOSE\u00A0<chest\u00A0name>'."),

    def test_close_2(self):
        result = self.command_processor.process(f'close {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosed)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already closed.')
        self.assertTrue(self.chest.is_closed)

    def test_close_3(self):
        self.chest.is_closed = False
        result = self.command_processor.process(f'close {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementHasBeenClosed)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have closed the {self.chest_title}.')
        self.assertTrue(self.chest.is_closed)

    def test_close_5(self):
        result = self.command_processor.process('close west door')
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresent)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].portal_type, 'door')
        self.assertEqual(result[0].message, 'This room does not have a west door.'),

    def test_close_6(self):
        result = self.command_processor.process(f'close {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosed)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already closed.')
        self.assertTrue(self.door.is_closed)

    def test_close_7(self):
        self.door.is_closed = False
        result = self.command_processor.process(f'close {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementHasBeenClosed)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have closed the {self.door_title}.')
        self.assertTrue(self.door.is_closed)
        result = self.command_processor.process('pick lock on east door')
        result = self.command_processor.process('leave via east door')
        result = self.command_processor.process('pick lock on north door')
        result = self.command_processor.process('leave via north door')
        result = self.command_processor.process('pick lock on west door')
        result = self.command_processor.process('leave via west door')
        result = self.command_processor.process('close south door')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosed)
        self.assertEqual(result[0].target, 'south door')
        self.assertEqual(result[0].message, f'The south door is already closed.')
        self.assertTrue(self.door.is_closed)

    def test_close_8(self):
        result = self.command_processor.process('close north iron door')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementIsAlreadyClosed)
        self.assertEqual(result[0].target, 'north door')
        self.assertEqual(result[0].message, 'The north door is already closed.'),

    def test_close_9(self):
        result = self.command_processor.process('close mana potion')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseable)
        self.assertEqual(result[0].target_title, 'mana potion')
        self.assertEqual(result[0].target_type, 'potion')
        self.assertEqual(result[0].message, "You can't close the mana potion; potions are not closable."),

    def test_close_10(self):
        result = self.command_processor.process('close kobold')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseable)
        self.assertEqual(result[0].target_title, 'kobold')
        self.assertEqual(result[0].target_type, 'creature')
        self.assertEqual(result[0].message, "You can't close the kobold; creatures are not closable."),

    def test_close_11(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('close kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseable)
        self.assertEqual(result[0].target_title, 'kobold corpse')
        self.assertEqual(result[0].target_type, 'corpse')
        self.assertEqual(result[0].message, "You can't close the kobold corpse; corpses are not closable."),

    def test_close_12(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('close east doorway')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseable)
        self.assertEqual(result[0].target_title, 'east doorway')
        self.assertEqual(result[0].target_type, 'doorway')
        self.assertEqual(result[0].message, "You can't close the east doorway; doorways are not closable.")

    def test_open_13(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        studded_leather_armor = self.items_state.get('Studded_Leather')
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process('close studded leather armor')
        self.assertIsInstance(result[0], advg.stmsg.close.ElementNotCloseable)
        self.assertEqual(result[0].target_title, 'studded leather armor')
        self.assertEqual(result[0].target_type, 'armor')
        self.assertEqual(result[0].message, "You can't close the studded leather armor; suits of armor are not closable."),


class Test_Drink(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_drink1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        for bad_argument_str in ('drink', 'drink the', 'drink 2 mana potion', 'drink 1 mana potions'):
            result = self.command_processor.process(bad_argument_str)
            self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
            self.assertEqual(result[0].command, 'DRINK')
            self.assertEqual(result[0].message, 'DRINK command: bad syntax. Should be '
                                                "'DRINK\u00A0[THE]\u00A0<potion\u00A0name>' or "
                                                "'DRINK\u00A0<number>\u00A0<potion\u00A0name>(s)'.")

    def test_drink2(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('drink health potion')
        self.assertIsInstance(result[0], advg.stmsg.drink.ItemNotInInventory)
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
        self.assertIsInstance(result[0], advg.stmsg.various.UnderwentHealingEffect)
        self.assertEqual(result[0].amount_healed, 10)
        self.assertRegex(result[0].message, r"You regained 10 hit points. You're fully healed! Your hit points are "
                                            r'(\d+)/\1.')

    def test_drink4(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get('Health_Potion')
        self.command_processor.game_state.character.pick_up_item(health_potion)
        self.command_processor.game_state.character.take_damage(30)
        result = self.command_processor.process('drink health potion')
        self.assertEqual(health_potion.hit_points_recovered, 20)
        self.assertIsInstance(result[0], advg.stmsg.various.UnderwentHealingEffect)
        self.assertEqual(result[0].amount_healed, 20)
        self.assertRegex(result[0].message, r'You regained 20 hit points. Your hit points are (?!(\d+)/\1)\d+/\d+.')

    def test_drink5(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        health_potion = self.command_processor.game_state.items_state.get('Health_Potion')
        self.command_processor.game_state.character.pick_up_item(health_potion)
        result = self.command_processor.process('drink health potion')
        self.assertIsInstance(result[0], advg.stmsg.various.UnderwentHealingEffect)
        self.assertEqual(result[0].amount_healed, 0)
        self.assertRegex(result[0].message, r"You didn't regain any hit points. You're fully healed! Your hit points are \d+/\d+.")

    def test_drink6(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        self.command_processor.game_state.character.spend_mana(10)
        result = self.command_processor.process('drink mana potion')
        self.assertEqual(mana_potion.mana_points_recovered, 20)
        self.assertIsInstance(result[0], advg.stmsg.drink.DrankManaPotion)
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
        self.assertIsInstance(result[0], advg.stmsg.drink.DrankManaPotion)
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
        self.assertIsInstance(result[0], advg.stmsg.drink.DrankManaPotion)
        self.assertEqual(result[0].amount_regained, 0)
        self.assertRegex(result[0].message, r"You didn't regain any mana points. You have full mana points! Your mana points are (\d+)/\1.")

    def test_drink9(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process('drink mana potion')
        self.assertIsInstance(result[0], advg.stmsg.drink.DrankManaPotionWhenNotASpellcaster)
        self.assertEqual(result[0].message, 'You feel a little strange, but otherwise nothing happens.')

    def test_drink10(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.command_processor.game_state.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin)
        result = self.command_processor.process('drink gold coin')
        self.assertIsInstance(result[0], advg.stmsg.drink.ItemNotDrinkable)
        self.assertEqual(result[0].message, 'A gold coin is not drinkable.')

    def test_drink11(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process('drink 3 mana potions')
        self.assertIsInstance(result[0], advg.stmsg.drink.TriedToDrinkMoreThanPossessed)
        self.assertEqual(result[0].message, "You can't drink 3 mana potions. You only have 1 of them.")

    def test_drink12(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process('drink three mana potions')
        self.assertIsInstance(result[0], advg.stmsg.drink.TriedToDrinkMoreThanPossessed)
        self.assertEqual(result[0].message, "You can't drink 3 mana potions. You only have 1 of them.")

    def test_drink13(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        mana_potion = self.command_processor.game_state.items_state.get('Mana_Potion')
        self.command_processor.game_state.character.pick_up_item(mana_potion)
        result = self.command_processor.process('drink mana potions')
        self.assertIsInstance(result[0], advg.stmsg.drink.QuantityUnclear)
        self.assertEqual(result[0].message, 'Amount to drink unclear. How many do you mean?')


class Test_Drop(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_drop_1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop the')  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'DROP')
        self.assertEqual(result[0].message, "DROP command: bad syntax. Should be 'DROP\u00A0<item\u00A0name>' or "
                                            "'DROP\u00A0<number>\u00A0<item\u00A0name>'."),

    def test_drop_2(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop a gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.QuantityUnclear)
        self.assertEqual(result[0].message, 'Amount to drop unclear. How many do you mean?')

    def test_drop_3(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop a mana potion')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.TryingToDropItemYouDontHave)
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
        self.assertIsInstance(result[0], advg.stmsg.drop.TryingToDropMoreThanYouHave)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 45)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, "You can't drop 45 gold coins. You only have 30 gold coins in your "
                                            'inventory.')

    def test_drop_5(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop forty-five gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.TryingToDropMoreThanYouHave)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 45)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, "You can't drop 45 gold coins. You only have 30 gold coins in your "
                                            'inventory.')

    def test_drop_6(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop 15 gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 15)
        self.assertEqual(result[0].amount_on_floor, 15)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, 'You dropped 15 gold coins. You see 15 gold coins here. You have 15 gold '
                                            'coins left.')

        result = self.command_processor.process('drop 14 gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 14)
        self.assertEqual(result[0].amount_on_floor, 29)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, 'You dropped 14 gold coins. You see 29 gold coins here. You have 1 gold '
                                            'coin left.')

    def test_drop_7(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        self.command_processor.process('pick up 29 gold coins')  # check
        result = self.command_processor.process('drop 1 gold coin')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 29)
        self.assertEqual(result[0].message, 'You dropped a gold coin. You see a gold coin here. You have 29 gold '
                                            'coins left.')

    def test_drop_8(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.character.pick_up_item(gold_coin, qty=30)
        result = self.command_processor.process('drop 30 gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_dropped, 30)
        self.assertEqual(result[0].amount_on_floor, 30)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, 'You dropped 30 gold coins. You see 30 gold coins here. You have no '
                                            'gold coins left.')

    def test_drop_9(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        longsword = self.items_state.get('Longsword')
        self.command_processor.game_state.character.pick_up_item(longsword)
        self.command_processor.game_state.character.equip_weapon(longsword)
        result = self.command_processor.process('drop longsword')  # check
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "You're no longer wielding a longsword. You now can't attack.")
        self.assertIsInstance(result[1], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[1].item_title, 'longsword')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a longsword. You see a longsword here. You have no longswords '
                                            'left.')

    def test_drop_10(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        steel_shield = self.items_state.get('Steel_Shield')
        self.command_processor.game_state.character.pick_up_item(steel_shield)
        self.command_processor.game_state.character.equip_shield(steel_shield)
        result = self.command_processor.process('drop steel shield')  # check
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertRegex(result[0].message, r"You're no longer carrying a steel shield. Your armor class is now \d+.")
        self.assertIsInstance(result[1], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[1].item_title, 'steel shield')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a steel shield. You see a steel shield here. You have no steel'
                                            ' shields left.')

    def test_drop_11(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        magic_wand = self.items_state.get('Magic_Wand')
        self.command_processor.game_state.character.pick_up_item(magic_wand)
        self.command_processor.game_state.character.equip_wand(magic_wand)
        result = self.command_processor.process('drop magic wand')  # check
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"You're no longer using a magic wand. You now can't attack.")
        self.assertIsInstance(result[1], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[1].item_title, 'magic wand')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a magic wand. You see a magic wand here. You have no '
                                            'magic wands left.')

    def test_drop_12(self):
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
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"You're no longer using a magic wand. You're now attacking with your staff.")
        self.assertIsInstance(result[1], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[1].item_title, 'magic wand')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a magic wand. You see a magic wand here. You have no '
                                            'magic wands left.')

    def test_drop_13(self):
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
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'staff')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertRegex(result[0].message, r"You're no longer wielding a staff. You're attacking with your magic "
                                            r'wand. Your attack bonus is [\d+-]+ and your magic wand damage is '
                                            r'\d+d\d+([+-]\d+)?.')
        self.assertIsInstance(result[1], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[1].item_title, 'staff')
        self.assertEqual(result[1].amount_dropped, 1)
        self.assertEqual(result[1].amount_on_floor, 1)
        self.assertEqual(result[1].amount_left, 0)
        self.assertEqual(result[1].message, 'You dropped a staff. You see a staff here. You have no '
                                            'staffs left.')

    def test_drop_14(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        longsword = self.items_state.get('Longsword')
        self.command_processor.game_state.character.pick_up_item(longsword, qty=3)
        self.command_processor.game_state.character.equip_weapon(longsword)
        result = self.command_processor.process('drop longsword')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 2)
        self.assertEqual(result[0].message, 'You dropped a longsword. You see a longsword here. You have 2 longswords '
                                            'left.')

    def test_drop_15(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        longsword = self.items_state.get('Longsword')
        self.command_processor.game_state.character.pick_up_item(longsword, qty=3)
        self.command_processor.game_state.character.equip_weapon(longsword)
        result = self.command_processor.process('drop longsword')  # check
        self.assertIsInstance(result[0], advg.stmsg.drop.DroppedItem)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].amount_dropped, 1)
        self.assertEqual(result[0].amount_on_floor, 1)
        self.assertEqual(result[0].amount_left, 2)
        self.assertEqual(result[0].message, 'You dropped a longsword. You see a longsword here. You have 2 longswords '
                                            'left.')


class Test_Equip_1(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.longsword = self.command_processor.game_state.items_state.get('Longsword')
        self.scale_mail = self.command_processor.game_state.items_state.get('Scale_Mail')
        self.shield = self.command_processor.game_state.items_state.get('Steel_Shield')
        self.magic_wand = self.command_processor.game_state.items_state.get('Magic_Wand')
        self.magic_wand_2 = self.command_processor.game_state.items_state.get('Magic_Wand_2')
        self.staff = self.command_processor.game_state.items_state.get('Staff')
        self.command_processor.game_state.character_name = 'Arliss'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.pick_up_item(self.longsword)
        self.command_processor.game_state.character.pick_up_item(self.scale_mail)
        self.command_processor.game_state.character.pick_up_item(self.staff)
        self.command_processor.game_state.character.pick_up_item(self.shield)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand_2)

    def test_equip_1(self):
        self.command_processor.game_state.character_name = 'Arliss'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True

        result = self.command_processor.process('equip')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'EQUIP')
        self.assertEqual(result[0].message, "EQUIP command: bad syntax. Should be 'EQUIP\u00A0<armor\u00A0name>', "
                                            "'EQUIP\u00A0<shield\u00A0name>', 'EQUIP\u00A0<wand\u00A0name>', or "
                                            "'EQUIP\u00A0<weapon\u00A0name>'.")

        result = self.command_processor.process('drop longsword')
        result = self.command_processor.process('equip longsword')
        self.assertIsInstance(result[0], advg.stmsg.equip.NoSuchItemInInventory)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].message, "You don't have a longsword in your inventory.")

    def test_equip_2(self):
        result = self.command_processor.process('equip longsword')
        self.assertIsInstance(result[0], advg.stmsg.equip.ClassCantUseItem)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "Mages can't wield longswords.")

    def test_equip_3(self):
        result = self.command_processor.process('equip scale mail armor')
        self.assertIsInstance(result[0], advg.stmsg.equip.ClassCantUseItem)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertEqual(result[0].message, "Mages can't wear scale mail armor.")

    def test_equip_4(self):
        result = self.command_processor.process('equip steel shield')
        self.assertIsInstance(result[0], advg.stmsg.equip.ClassCantUseItem)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertEqual(result[0].message, "Mages can't carry steel shields.")

    def test_equip_5(self):
        result = self.command_processor.process('equip magic wand')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"^You're now using a magic wand. Your attack bonus is now [\d+-]+ and your "
                                            r'wand damage is now [\dd+-]+.$')

    def test_equip_6(self):
        self.command_processor.process('equip magic wand')
        result = self.command_processor.process('equip magic wand 2')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertEqual(result[0].message, "You're no longer using a magic wand. You now can't attack.")
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'magic wand 2')
        self.assertEqual(result[1].item_type, 'wand')
        self.assertRegex(result[1].message, r"^You're now using a magic wand 2. Your attack bonus is now [\d+-]+ and "
                                            r'your wand damage is now [\dd+-]+.$')

    def test_equip_7(self):
        self.command_processor.process('equip staff')
        result = self.command_processor.process('equip magic wand')
        result = self.command_processor.process('equip magic wand 2')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].item_type, 'wand')
        self.assertRegex(result[0].message, r"You're no longer using a magic wand. You're attacking with your staff. "
                                            r'Your attack bonus is [+-]\d+ and your staff damage is \d+d\d+([+-]\d+)?.')
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'magic wand 2')
        self.assertEqual(result[1].item_type, 'wand')
        self.assertRegex(result[1].message, r"^You're now using a magic wand 2. Your attack bonus is now [\d+-]+ and "
                                            r'your wand damage is now [\dd+-]+.$')


class Test_Equip_2(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.buckler = self.command_processor.game_state.items_state.get('Buckler')
        self.longsword = self.command_processor.game_state.items_state.get('Longsword')
        self.mace = self.command_processor.game_state.items_state.get('Heavy_Mace')
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
        self.assertIsInstance(result[0], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertRegex(result[0].message, r"^You're now wielding a longsword. Your attack bonus is now [\d+-]+ and "
                                            r'your weapon damage is now [\dd+-]+.$')
        result = self.command_processor.process('equip mace')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_type, 'weapon')
        self.assertEqual(result[0].message, "You're no longer wielding a longsword. You now can't attack.")
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'mace')
        self.assertEqual(result[1].item_type, 'weapon')
        self.assertRegex(result[1].message, r"^You're now wielding a mace. Your attack bonus is now [\d+-]+ and your "
                                            r'weapon damage is now [\dd+-]+.$')

    def test_equip_3(self):
        result = self.command_processor.process('equip scale mail armor')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertRegex(result[0].message, r"^You're now wearing a suit of scale mail armor. Your armor class is now \d+.$")
        result = self.command_processor.process('equip studded leather armor')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertEqual(result[0].item_type, 'armor')
        self.assertRegex(result[0].message, r"^You're no longer wearing a suit of scale mail armor. Your armor class is now \d+.$")
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'studded leather armor')
        self.assertEqual(result[1].item_type, 'armor')
        self.assertRegex(result[1].message, r"^You're now wearing a suit of studded leather armor. Your armor class is now \d+.$")

    def test_equip_4(self):
        result = self.command_processor.process('equip steel shield')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertRegex(result[0].message, r"^You're now carrying a steel shield. Your armor class is now \d+.$")
        result = self.command_processor.process('equip buckler')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertEqual(result[0].item_type, 'shield')
        self.assertRegex(result[0].message, r"^You're no longer carrying a steel shield. Your armor class is now \d+.$")
        self.assertIsInstance(result[1], advg.stmsg.various.ItemEquipped)
        self.assertEqual(result[1].item_title, 'buckler')
        self.assertEqual(result[1].item_type, 'shield')
        self.assertRegex(result[1].message, r"^You're now carrying a buckler. Your armor class is now [\d+-]+.$")

    def test_equip_5(self):
        result = self.command_processor.process('equip magic wand')
        self.assertIsInstance(result[0], advg.stmsg.equip.ClassCantUseItem)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertEqual(result[0].message, "Warriors can't use magic wands.")


class Test_Help_1(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.process('set name to Niath')
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('begin game')

    def test_help_1(self):
        result = self.command_processor.process('help')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayCommands)
        self.assertEqual(result[0].commands_available, ('ATTACK', 'CAST SPELL', 'CLOSE', 'DRINK', 'DROP', 'EQUIP',
                                                        'HELP', 'INVENTORY', 'LEAVE', 'LOCK', 'LOOK AT', 'OPEN',
                                                        'PICK LOCK', 'PICK UP', 'PUT', 'QUIT', 'STATUS', 'TAKE',
                                                        'UNEQUIP', 'UNLOCK',))
        self.assertEqual(result[0].message, """The list of commands available during the game is:

ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, \
PICK UP, PUT, QUIT, STATUS, TAKE, UNEQUIP, and UNLOCK

Which one do you want help with?
""")

    def test_help_2(self):
        result = self.command_processor.process('help juggle')
        self.assertIsInstance(result[0], advg.stmsg.help_.NotRecognized)
        self.assertEqual(result[0].commands_available, ('ATTACK', 'BEGIN GAME', 'CAST SPELL', 'CLOSE', 'DRINK', 'DROP',
                                                        'EQUIP', 'HELP', 'INVENTORY', 'LEAVE', 'LOCK', 'LOOK AT',
                                                        'OPEN', 'PICK LOCK', 'PICK UP', 'PUT', 'QUIT', 'REROLL',
                                                        'SET CLASS', 'SET NAME', 'STATUS', 'TAKE', 'UNEQUIP',
                                                        'UNLOCK',))
        self.assertEqual(result[0].message, """The command 'JUGGLE' is not recognized. The full list of commands is:

ATTACK, BEGIN GAME, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, \
PICK UP, PUT, QUIT, REROLL, SET CLASS, SET NAME, STATUS, TAKE, UNEQUIP, and UNLOCK

Which one do you want help with?
""")

    def test_help_3(self):
        result = self.command_processor.process('help attack')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'ATTACK')
        self.assertEqual(result[0].syntax_tuple, ('<creature\u00A0name>',))
        self.assertEqual(result[0].message, """Help for the ATTACK command:

Usage: 'ATTACK\u00A0<creature\u00A0name>'

The ATTACK command is used to attack creatures. Beware: if you attack a creature and don't kill it, it will attack you \
in return! After you kill a creature, you can check its corpse for loot using the LOOK AT command and take loot with \
the TAKE command.
""")

    def test_help_4(self):
        result = self.command_processor.process('help close')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'CLOSE')
        self.assertEqual(result[0].syntax_tuple, ('<door\u00A0name>', '<chest\u00A0name>'))
        self.assertEqual(result[0].message, """Help for the CLOSE command:

Usage: 'CLOSE\u00A0<door\u00A0name>' or 'CLOSE\u00A0<chest\u00A0name>'

The CLOSE command can be used to close doors and chests.
""")

    def test_help_5(self):
        result = self.command_processor.process('help put')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].syntax_tuple, ('<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
                                                  '<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
                                                  '<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>',
                                                  '<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'))
        self.assertEqual(result[0].message, """Help for the PUT command:

Usage: 'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'

The PUT command can be used to remove items from your inventory and place them in a chest or on a corpse's person. To \
leave items on the floor, use DROP.
""")

    def test_help_6(self):
        result = self.command_processor.process('help begin game')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].syntax_tuple, ('',)),
        self.assertEqual(result[0].message, """Help for the BEGIN GAME command:

Usage: 'BEGIN GAME'

The BEGIN GAME command is used to start the game after you have set your name and class and approved your ability scores. When you enter this command, you will automatically be equiped with your starting gear and started in the antechamber of the dungeon.
""")


class Test_Help_2(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_help_1(self):
        result = self.command_processor.process('help')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayCommands)
        self.assertEqual(result[0].commands_available, ('BEGIN GAME', 'HELP', 'QUIT', 'REROLL', 'SET CLASS',
                                                        'SET NAME'))
        self.assertEqual(result[0].message, """The list of commands available before game start is:

BEGIN GAME, HELP, QUIT, REROLL, SET CLASS, and SET NAME

Which one do you want help with?
""")

    def test_help_2(self):
        result = self.command_processor.process('help juggle')
        self.assertIsInstance(result[0], advg.stmsg.help_.NotRecognized)
        self.assertEqual(result[0].commands_available, ('ATTACK', 'BEGIN GAME', 'CAST SPELL', 'CLOSE', 'DRINK', 'DROP',
                                                        'EQUIP', 'HELP', 'INVENTORY', 'LEAVE', 'LOCK', 'LOOK AT',
                                                        'OPEN', 'PICK LOCK', 'PICK UP', 'PUT', 'QUIT', 'REROLL',
                                                        'SET CLASS', 'SET NAME', 'STATUS', 'TAKE', 'UNEQUIP',
                                                        'UNLOCK',))
        self.assertEqual(result[0].message, """The command 'JUGGLE' is not recognized. The full list of commands is:

ATTACK, BEGIN GAME, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, \
PICK UP, PUT, QUIT, REROLL, SET CLASS, SET NAME, STATUS, TAKE, UNEQUIP, and UNLOCK

Which one do you want help with?
""")

    def test_help_3(self):
        result = self.command_processor.process('help attack')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'ATTACK')
        self.assertEqual(result[0].syntax_tuple, ('<creature\u00A0name>',))
        self.assertEqual(result[0].message, """Help for the ATTACK command:

Usage: 'ATTACK\u00A0<creature\u00A0name>'

The ATTACK command is used to attack creatures. Beware: if you attack a creature and don't kill it, it will attack you \
in return! After you kill a creature, you can check its corpse for loot using the LOOK AT command and take loot with \
the TAKE command.
""")

    def test_help_4(self):
        result = self.command_processor.process('help close')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'CLOSE')
        self.assertEqual(result[0].syntax_tuple, ('<door\u00A0name>', '<chest\u00A0name>'))
        self.assertEqual(result[0].message, """Help for the CLOSE command:

Usage: 'CLOSE\u00A0<door\u00A0name>' or 'CLOSE\u00A0<chest\u00A0name>'

The CLOSE command can be used to close doors and chests.
""")

    def test_help_5(self):
        result = self.command_processor.process('help put')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].syntax_tuple, ('<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
                                                  '<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
                                                  '<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>',
                                                  '<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'))
        self.assertEqual(result[0].message, """Help for the PUT command:

Usage: 'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', \
'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or \
'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'

The PUT command can be used to remove items from your inventory and place them in a chest or on a corpse's person. To \
leave items on the floor, use DROP.
""")

    def test_help_6(self):
        result = self.command_processor.process('help begin game')
        self.assertIsInstance(result[0], advg.stmsg.help_.DisplayHelpForCommand)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].syntax_tuple, ('',)),
        self.assertEqual(result[0].message, """Help for the BEGIN GAME command:

Usage: 'BEGIN GAME'

The BEGIN GAME command is used to start the game after you have set your name and class and approved your ability scores. When you enter this command, you will automatically be equiped with your starting gear and started in the antechamber of the dungeon.
""")


class Test_Inventory(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        containers_ini_config.sections['Wooden_Chest_1']['contents'] = ('[20xGold_Coin,1xWarhammer,'
                                                                                 '1xMana_Potion,1xHealth_Potion,'
                                                                                 '1xSteel_Shield,1xScale_Mail,'
                                                                                 '1xMagic_Wand]')
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
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
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'INVENTORY')
        self.assertEqual(result[0].message, "INVENTORY command: bad syntax. Should be 'INVENTORY'.")

    def test_inventory_2(self):
        result = self.command_processor.process('inventory')
        self.assertIsInstance(result[0], advg.stmsg.inven.DisplayInventory)
        self.assertEqual(tuple(map(operator.itemgetter(0), result[0].inventory_contents)), (30, 1, 1, 2, 1, 1))
        self.assertIsInstance(result[0].inventory_contents[0][1], advg.Coin)
        self.assertIsInstance(result[0].inventory_contents[1][1], advg.Weapon)
        self.assertIsInstance(result[0].inventory_contents[2][1], advg.Wand)
        self.assertIsInstance(result[0].inventory_contents[3][1], advg.Potion)
        self.assertIsInstance(result[0].inventory_contents[4][1], advg.Armor)
        self.assertIsInstance(result[0].inventory_contents[5][1], advg.Shield)
        self.assertEqual(result[0].message, 'You have 30 gold coins, a longsword, a magic wand, 2 mana potions, '
                                            'a suit of scale mail armor, and a steel shield in your inventory.')


class Test_Leave(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        containers_ini_config.sections['Wooden_Chest_1']['contents'] = \
            '[20xGold_Coin,1xWarhammer,1xMana_Potion,1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]'
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True

    def test_leave_1(self):
        result = self.command_processor.process('leave')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('leave using')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('leave using north')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'LEAVE')
        self.assertEqual(result[0].message, 'LEAVE command: bad syntax. Should be '
                    "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOOR', "
                    "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOORWAY', "
                    "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<door\u00A0name>', or "
                    "'LEAVE\u00A0[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0<door\u00A0name>'.")

    def test_leave_2(self):
        result = self.command_processor.process('leave using west door')
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresent)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].message, 'This room does not have a west door.')

    def test_leave_3(self):
        result = self.command_processor.process('leave using north door')
        self.assertIsInstance(result[0], advg.stmsg.leave.LeftRoom)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'You leave the room via the north door.')
        self.assertIsInstance(result[1], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[1].room, advg.Room)
        self.assertEqual(result[1].message, 'Nondescript room.\nThere is a doorway to the east and an iron door to the '
                                            'south.')
        result = self.command_processor.process('leave using south door')
        self.assertIsInstance(result[0], advg.stmsg.leave.LeftRoom)
        self.assertEqual(result[0].compass_dir, 'south')
        self.assertEqual(result[0].message, 'You leave the room via the south door.')
        self.assertIsInstance(result[1], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[1].room, advg.Room)
        self.assertEqual(result[1].message, 'Entrance room.\nYou see a wooden chest here.\nThere is a kobold in the '
                                            'room.\nYou see a mana potion and 2 health potions on the floor.\nThere '
                                            'is an iron door to the north and an iron door to the east.')

    def test_leave_4(self):
        result = self.command_processor.process('leave using north iron door')
        self.assertIsInstance(result[0], advg.stmsg.leave.LeftRoom)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'You leave the room via the north door.')
        self.assertIsInstance(result[1], advg.stmsg.various.EnteredRoom)
        self.assertIsInstance(result[1].room, advg.Room)
        self.assertEqual(result[1].message, 'Nondescript room.\nThere is a doorway to the east and an iron door to the '
                                            'south.')

    def test_leave_5(self):
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertEqual(self.command_processor.game_state.rooms_state.cursor.title, 'southwest dungeon room')
        self.command_processor.process('leave using north door')
        self.assertEqual(self.command_processor.game_state.rooms_state.cursor.title, 'northwest dungeon room')
        self.command_processor.process('leave using east doorway')
        self.assertEqual(self.command_processor.game_state.rooms_state.cursor.title, 'northeast dungeon room')
        result = self.command_processor.process('leave using north door')
        self.assertIsInstance(result[0], advg.stmsg.leave.DoorIsLocked)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].portal_type, 'door')
        self.assertEqual(result[0].message, "You can't leave the room via the north door. The door is locked.")
        result = self.command_processor.process('pick lock on north door')
        result = self.command_processor.process('leave using north door')
        self.assertIsInstance(result[0], advg.stmsg.leave.LeftRoom)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'You leave the room via the north door.')
        self.assertIsInstance(result[1], advg.stmsg.leave.WonTheGame)
        self.assertEqual(result[1].message, 'You found the exit to the dungeon. You have won the game!')


class Test_Lock(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_locked = True
        self.door_title = self.command_processor.game_state.rooms_state.cursor.north_door.title
        self.chest = self.command_processor.game_state.rooms_state.cursor.container_here
        self.chest.is_locked = False
        self.chest_title = self.chest.title

    def test_lock_1(self):
        result = self.command_processor.process('lock')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'LOCK')
        self.assertEqual(result[0].message, "LOCK command: bad syntax. Should be 'LOCK\u00A0<door\u00A0name>' or "
                                            "'LOCK\u00A0<chest\u00A0name>'."),

    def test_lock_2(self):
        result = self.command_processor.process('lock west door')
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresent)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].portal_type, 'door')
        self.assertEqual(result[0].message, 'This room does not have a west door.'),
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked
        self.door_title = self.command_processor.game_state.rooms_state.cursor.north_door.title

    def test_lock_3(self):
        self.door.is_locked = False
        result = self.command_processor.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.lock.DontPossessCorrectKey)
        self.assertEqual(result[0].object_to_lock_title, self.door_title)
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, f'To lock the {self.door_title} you need a door key.')
        self.assertFalse(self.door.is_locked)

    def test_lock_4(self):
        self.door.is_locked = True
        key = self.command_processor.game_state.items_state.get('Door_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementIsAlreadyUnlocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already locked.')
        self.assertTrue(self.door.is_locked)

        self.door.is_locked = False
        result = self.command_processor.process(f'lock {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementHasBeenUnlocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have locked the {self.door_title}.')
        self.assertTrue(self.door.is_locked)
        result = self.command_processor.process('unlock east door')
        result = self.command_processor.process('leave via east door')
        result = self.command_processor.process('unlock north door')
        result = self.command_processor.process('leave via north door')
        result = self.command_processor.process('unlock west door')
        result = self.command_processor.process('leave via west door')
        result = self.command_processor.process('lock south door')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementIsAlreadyUnlocked)
        self.assertEqual(result[0].target, 'south door')
        self.assertEqual(result[0].message, 'The south door is already locked.')

    def test_lock_5(self):
        result = self.command_processor.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.lock.DontPossessCorrectKey)
        self.assertEqual(result[0].object_to_lock_title, self.chest_title)
        self.assertEqual(result[0].key_needed, 'chest key')
        self.assertEqual(result[0].message, f'To lock the {self.chest_title} you need a chest key.')

    def test_lock_6(self):
        self.chest.is_locked = True
        key = self.command_processor.game_state.items_state.get('Chest_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementIsAlreadyUnlocked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already locked.')

        self.chest.is_locked = False
        result = self.command_processor.process(f'lock {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementHasBeenUnlocked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have locked the {self.chest_title}.')
        self.assertTrue(self.chest.is_locked)

    def test_lock_7(self):
        result = self.command_processor.process('lock north iron door')
        self.assertIsInstance(result[0], advg.stmsg.lock.DontPossessCorrectKey)
        self.assertEqual(result[0].object_to_lock_title, 'north door')
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, 'To lock the north door you need a door key.')

    def test_lock_8(self):
        result = self.command_processor.process('lock mana potion')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'mana potion')
        self.assertEqual(result[0].target_type, 'potion')
        self.assertEqual(result[0].message, "You can't lock the mana potion; potions are not lockable."),

    def test_lock_9(self):
        studded_leather_armor = self.items_state.get('Studded_Leather')
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process('lock studded leather armor')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'studded leather armor')
        self.assertEqual(result[0].target_type, 'armor')
        self.assertEqual(result[0].message, "You can't lock the studded leather armor; suits of armor are not lockable."),

    def test_lock_10(self):
        result = self.command_processor.process('lock mana potion')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'mana potion')
        self.assertEqual(result[0].target_type, 'potion')
        self.assertEqual(result[0].message, "You can't lock the mana potion; potions are not lockable."),

    def test_lock_11(self):
        result = self.command_processor.process('lock kobold')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'kobold')
        self.assertEqual(result[0].target_type, 'creature')
        self.assertEqual(result[0].message, "You can't lock the kobold; creatures are not lockable."),

    def test_lock_12(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('lock kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'kobold corpse')
        self.assertEqual(result[0].target_type, 'corpse')
        self.assertEqual(result[0].message, "You can't lock the kobold corpse; corpses are not lockable."),

    def test_lock_13(self):
        result = self.command_processor.process('pick lock on north door')
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('lock east doorway')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'east doorway')
        self.assertEqual(result[0].target_type, 'doorway')
        self.assertEqual(result[0].message, "You can't lock the east doorway; doorways are not lockable.")

    def test_lock_14(self):
        studded_leather_armor = self.items_state.get('Studded_Leather')
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process('lock studded leather armor')
        self.assertIsInstance(result[0], advg.stmsg.lock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'studded leather armor')
        self.assertEqual(result[0].target_type, 'armor')
        self.assertEqual(result[0].message, "You can't lock the studded leather armor; suits of armor are not lockable."),


class Test_Look_At_1(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
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

    def test_look_at_1(self):
        result = self.command_processor.process('look at kobold')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundCreatureHere)
        self.assertEqual(result[0].creature_description,
                         self.game_state.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, self.game_state.rooms_state.cursor.creature_here.description)

    def test_look_at_2(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('look at kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} They '
                                             'have 30 gold coins, a health potion, a short sword, and a small leather '
                                             'armor on them.')

    def test_look_at_3(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is closed and locked.')

    def test_look_at_4(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is closed but unlocked.')

    def test_look_at_5(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is unlocked and open. It contains 20 gold coins, a health potion, a '
                                             'magic wand, a mana potion, a scale mail armor, a steel shield, and a '
                                             'warhammer.')

    def test_look_at_6(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        with self.assertRaises(advg.InternalError):
            self.command_processor.process('look at wooden chest')

    def test_look_at_7(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is closed.')

    def test_look_at_8(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is open. It contains 20 gold coins, a health potion, a magic wand, a '
                                             'mana potion, a scale mail armor, a steel shield, and a warhammer.')

    def test_look_at_9(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is locked.')

    def test_look_at_10(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description} It '
                                             'is unlocked.')

    def test_look_at_11(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process('look at wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundContainerHere)
        self.assertEqual(result[0].container_description,
                         self.game_state.rooms_state.cursor.container_here.description)
        self.assertEqual(result[0].is_locked, self.game_state.rooms_state.cursor.container_here.is_locked)
        self.assertEqual(result[0].is_closed, self.game_state.rooms_state.cursor.container_here.is_closed)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.container_here.description}')

    def test_look_at_12(self):
        result = self.command_processor.process('look at kobold')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundCreatureHere)
        self.assertEqual(result[0].creature_description,
                         self.game_state.rooms_state.cursor.creature_here.description)
        self.assertEqual(result[0].message, f'{self.game_state.rooms_state.cursor.creature_here.description}')

    def test_look_at_13(self):
        result = self.command_processor.process('look at north iron door')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundDoorOrDoorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertIsInstance(result[0].door, advg.Door)
        self.assertEqual(result[0].message, 'This door is bound in iron plates with a small barred window set up high.'
                                            ' It is set in the north wall. It is closed but unlocked.')


class Test_Look_At_2(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        containers_ini_config.sections['Wooden_Chest_1']['contents'] = \
            '[20xGold_Coin,1xWarhammer,1xMana_Potion,1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]'
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True

    def test_look_at_1(self):
        result = self.command_processor.process('look at')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('look at on')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('look at in')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('look at mana potion in')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('look at health potion on')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('look at health potion on wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('look at mana potion in kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'LOOK AT')
        self.assertEqual(result[0].message, 'LOOK AT command: bad syntax. '
                                            "Should be 'LOOK\u00A0AT\u00A0<item\u00A0name>', "
                                    "'LOOK\u00A0AT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                    "'LOOK\u00A0AT\u00A0<item\u00A0name>\u00A0IN\u00A0INVENTORY', "
                                    "'LOOK\u00A0AT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', "
                                    "'LOOK\u00A0AT\u00A0<compass\u00A0direction>\u00A0DOOR', or "
                                    "'LOOK\u00A0AT\u00A0<compass\u00A0direction>\u00A0DOORWAY'.")

    def test_look_at_2(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process('look at mana potion in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerNotFound)
        self.assertEqual(result[0].container_not_found_title, 'wooden chest')
        self.assertEqual(result[0].message, 'There is no wooden chest here.')

    def test_look_at_3(self):
        result = self.command_processor.process('look at gold coin in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 20)
        self.assertEqual(result[0].item_description, 'A small shiny gold coin imprinted with an indistinct bust on one '
                                                     'side and a worn state seal on the other.')
        self.assertEqual(result[0].message, 'A small shiny gold coin imprinted with an indistinct bust on one side and '
                                            'a worn state seal on the other. There are 20 in the wooden chest.')

    def test_look_at_4(self):
        result = self.command_processor.process('look at warhammer in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A heavy hammer with a heavy iron head with a tapered striking '
                                                     'point and a long leather-wrapped haft. Its attack bonus is +0 '
                                                     'and its damage is 1d8. Warriors and priests can use this.')
        self.assertEqual(result[0].message, 'A heavy hammer with a heavy iron head with a tapered striking point and '
                                            'a long leather-wrapped haft. Its attack bonus is +0 and its damage is 1d8.'
                                            ' Warriors and priests can use this. There is 1 in the wooden chest.')

    def test_look_at_5(self):
        result = self.command_processor.process('look at steel shield in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A broad panel of leather-bound steel with a metal rim that is '
                                                     'useful for sheltering behind. Its armor bonus is +2. Warriors '
                                                     'and priests can use this.')
        self.assertEqual(result[0].message, 'A broad panel of leather-bound steel with a metal rim that is useful for '
                                            'sheltering behind. Its armor bonus is +2. Warriors and priests can use '
                                            'this. There is 1 in the wooden chest.')

    def test_look_at_6(self):
        result = self.command_processor.process('look at steel shield in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A broad panel of leather-bound steel with a metal rim that is '
                                                     'useful for sheltering behind. Its armor bonus is +2. Warriors '
                                                     'and priests can use this.')
        self.assertEqual(result[0].message, 'A broad panel of leather-bound steel with a metal rim that is useful for '
                                            'sheltering behind. Its armor bonus is +2. Warriors and priests can use '
                                            'this. There is 1 in the wooden chest.')

    def test_look_at_7(self):
        result = self.command_processor.process('look at mana potion in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A small, stoppered bottle that contains a pungeant but drinkable '
                                                     'blue liquid with a discernable magic aura. It restores 20 mana '
                                                     'points.')
        self.assertEqual(result[0].message, 'A small, stoppered bottle that contains a pungeant but drinkable blue '
                                            'liquid with a discernable magic aura. It restores 20 mana points. There '
                                            'is 1 in the wooden chest.')

    def test_look_at_8(self):
        result = self.command_processor.process('look at health potion in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A small, stoppered bottle that contains a pungeant but drinkable '
                                                     'red liquid with a discernable magic aura. It restores 20 hit '
                                                     'points.')
        self.assertEqual(result[0].message, 'A small, stoppered bottle that contains a pungeant but drinkable red '
                                            'liquid with a discernable magic aura. It restores 20 hit points. There '
                                            'is 1 in the wooden chest.')

    def test_look_at_9(self):
        result = self.command_processor.process('look at north door')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundDoorOrDoorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is bound in iron plates with a small barred window set up '
                                            'high. It is set in the north wall. It is closed but unlocked.')

    def test_look_at_10(self):
        result = self.command_processor.process('look at mana potion in inventory')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundNothing)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].item_location, 'inventory')
        self.assertIs(result[0].location_type, None)
        self.assertEqual(result[0].message, 'You have no mana potion in your inventory.')

    def test_look_at_11(self):
        result = self.command_processor.process('look at longsword on the floor')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundNothing)
        self.assertEqual(result[0].item_title, 'longsword')
        self.assertEqual(result[0].item_location, 'floor')
        self.assertIs(result[0].location_type, None)
        self.assertEqual(result[0].message, 'There is no longsword on the floor.')

    def test_look_at_12(self):
        result = self.command_processor.process('pick lock on wooden chest')
        result = self.command_processor.process('open wooden chest')
        result = self.command_processor.process('take mana potion from wooden chest')
        result = self.command_processor.process('look at mana potion in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundNothing)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].item_location, 'wooden chest')
        self.assertEqual(result[0].location_type, 'chest')
        self.assertEqual(result[0].message, 'The wooden chest has no mana potion in it.')

    def test_look_at_13(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked = True
        result = self.command_processor.process('look at north door')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundDoorOrDoorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is bound in iron plates with a small barred window set up high. It '
                                            'is set in the north wall. It is closed and locked.')

    def test_look_at_14(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_closed = False
        result = self.command_processor.process('look at north door')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundDoorOrDoorway)
        self.assertEqual(result[0].compass_dir, 'north')
        self.assertEqual(result[0].message, 'This door is bound in iron plates with a small barred window set up high. It '
                                            'is set in the north wall. It is open.')

    def test_look_at_15(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_closed = False
        result = self.command_processor.process('look at west door')
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresent)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].message, 'This room does not have a west door.')

    def test_look_at_16(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('look at east doorway')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundDoorOrDoorway)
        self.assertEqual(result[0].compass_dir, 'east')
        self.assertEqual(result[0].message, 'This open doorway is outlined by a stone arch set into the wall. It is '
                                            'set in the east wall. It is open.')

        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_closed)
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)

    def test_look_at_17(self):
        self.command_processor.game_state.character.pick_up_item(
            self.command_processor.game_state.items_state.get('Longsword'))
        result = self.command_processor.process('look at longsword in inventory')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A hefty sword with a long blade, a broad hilt and a leathern '
                                                     'grip. Its attack bonus is +0 and its damage is 1d8. Warriors can '
                                                     'use this.')
        self.assertEqual(result[0].message, 'A hefty sword with a long blade, a broad hilt and a leathern grip. Its '
                                            'attack bonus is +0 and its damage is 1d8. Warriors can use this. There '
                                            'is 1 in your inventory.')

    def test_look_at_18(self):
        self.command_processor.game_state.character.pick_up_item(
            self.command_processor.game_state.items_state.get('Magic_Wand'))
        result = self.command_processor.process('look at magic wand in inventory')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A palpably magical tapered length of polished ash wood tipped '
                                                     'with a glowing red carnelian gem. Its attack bonus is +3 and '
                                                     'its damage is 3d8+5. Mages can use this.')
        self.assertEqual(result[0].message, 'A palpably magical tapered length of polished ash wood tipped with a '
                                            'glowing red carnelian gem. Its attack bonus is +3 and its damage is '
                                            '3d8+5. Mages can use this. There is 1 in your inventory.')

    def test_look_at_19(self):
        result = self.command_processor.process('look at door')
        self.assertIsInstance(result[0], advg.stmsg.various.AmbiguousDoorSpecifier)
        self.assertEqual(set(result[0].compass_dirs), {'north', 'east'})
        self.assertEqual(result[0].door_type, 'iron_door')
        self.assertEqual(result[0].door_or_doorway, 'door')
        self.assertEqual(result[0].message, 'More than one door in this room matches your command. Do you mean the '
                                            'north iron door or the east iron door?')

    def test_look_at_20(self):
        result = self.command_processor.process('look at mana potion')
        self.assertIsInstance(result[0], advg.stmsg.lookat.FoundItemOrItemsHere)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(result[0].item_description, 'A small, stoppered bottle that contains a pungeant but '
                                                     'drinkable blue liquid with a discernable magic aura. It '
                                                     'restores 20 mana points.')
        self.assertEqual(result[0].message, 'A small, stoppered bottle that contains a pungeant but drinkable blue '
                                            'liquid with a discernable magic aura. It restores 20 mana points. There '
                                            'is 1 on the floor.')


class Test_Open(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
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
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'OPEN')
        self.assertEqual(result[0].message, "OPEN command: bad syntax. Should be 'OPEN\u00A0<door\u00A0name>' or "
                                            "'OPEN\u00A0<chest\u00A0name>'."),

    def test_open_2(self):
        self.chest.is_closed = True
        self.chest.is_locked = True
        result = self.command_processor.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementIsLocked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is locked.')

    def test_open_3(self):
        self.chest.is_locked = False
        self.chest.is_closed = False
        self.chest_title = self.chest.title
        result = self.command_processor.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementIsAlreadyOpen)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already open.')
        self.assertFalse(self.chest.is_closed)

        self.chest.is_closed = True
        result = self.command_processor.process(f'open {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementHasBeenOpened)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have opened the {self.chest_title}.')
        self.assertFalse(self.chest.is_closed)

    def test_open_4(self):
        result = self.command_processor.process('open west door')
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresent)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].portal_type, 'door')
        self.assertEqual(result[0].message, 'This room does not have a west door.'),

    def test_open_5(self):
        result = self.command_processor.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementIsAlreadyOpen)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already open.')
        self.assertFalse(self.door.is_closed)

    def test_open_6(self):
        self.door.is_closed = True
        result = self.command_processor.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementHasBeenOpened)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have opened the {self.door_title}.')
        self.assertFalse(self.door.is_closed)

        result = self.command_processor.process(f'leave using {self.door_title}')
        result = self.command_processor.process(f'open south door')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementIsAlreadyOpen)
        self.assertEqual(result[0].target, 'south door')
        self.assertEqual(result[0].message, f'The south door is already open.')
        self.assertFalse(self.door.is_closed)


    def test_open_7(self):
        self.door.is_closed = True
        self.door.is_locked = True
        result = self.command_processor.process(f'open {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementIsLocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is locked.')
        self.assertTrue(self.door.is_closed)

    def test_open_8(self):
        self.door.is_closed = True
        self.door.is_locked = True
        alternate_title = self.door.door_type.replace('_', ' ')
        result = self.command_processor.process(f'open north {alternate_title}')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementIsLocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is locked.')
        self.assertTrue(self.door.is_closed)

    def test_open_9(self):
        result = self.command_processor.process('open north iron door')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementIsAlreadyOpen)
        self.assertEqual(result[0].target, 'north door')
        self.assertEqual(result[0].message, 'The north door is already open.'),

    def test_open_10(self):
        result = self.command_processor.process('open mana potion')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementNotOpenable)
        self.assertEqual(result[0].target_title, 'mana potion')
        self.assertEqual(result[0].target_type, 'potion')
        self.assertEqual(result[0].message, "You can't open the mana potion; potions are not openable."),

    def test_open_11(self):
        result = self.command_processor.process('open kobold')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementNotOpenable)
        self.assertEqual(result[0].target_title, 'kobold')
        self.assertEqual(result[0].target_type, 'creature')
        self.assertEqual(result[0].message, "You can't open the kobold; creatures are not openable."),

    def test_open_12(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('open kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementNotOpenable)
        self.assertEqual(result[0].target_title, 'kobold corpse')
        self.assertEqual(result[0].target_type, 'corpse')
        self.assertEqual(result[0].message, "You can't open the kobold corpse; corpses are not openable."),

    def test_open_13(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('open east doorway')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementNotOpenable)
        self.assertEqual(result[0].target_title, 'east doorway')
        self.assertEqual(result[0].target_type, 'doorway')
        self.assertEqual(result[0].message, "You can't open the east doorway; doorways are not openable.")

    def test_open_14(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        studded_leather_armor = self.items_state.get('Studded_Leather')
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process('open studded leather armor')
        self.assertIsInstance(result[0], advg.stmsg.open_.ElementNotOpenable)
        self.assertEqual(result[0].target_title, 'studded leather armor')
        self.assertEqual(result[0].target_type, 'armor')
        self.assertEqual(result[0].message, "You can't open the studded leather armor; suits of armor are not openable."),


class Test_Pick_Lock(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_pick_lock_1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.command.ClassRestricted)
        self.assertEqual(result[0].command, 'PICK LOCK')
        self.assertEqual(result[0].classes, ('thief',))
        self.assertEqual(result[0].message, 'Only thieves can use the PICK LOCK command.')

    def test_pick_lock_2(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('pick lock on')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('pick lock on the')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('pick lock wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'PICK LOCK')
        self.assertEqual(result[0].message, 'PICK LOCK command: bad syntax. Should be '
                                            "'PICK\u00A0LOCK\u00A0ON\u00A0[THE]\u00A0<chest\u00A0name>' or "
                                            "'PICK\u00A0LOCK\u00A0ON\u00A0[THE]\u00A0<door\u00A0name>'.")

    def test_pick_lock_3(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on west door')
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresent)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].portal_type, 'door')
        self.assertEqual(result[0].message, 'This room does not have a west door.')

    def test_pick_lock_4(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on north iron door')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetNotLocked)
        self.assertEqual(result[0].target_title, 'north iron door')
        self.assertEqual(result[0].message, 'The north iron door is not locked.')

    def test_pick_lock_5(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on north door')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetNotLocked)
        self.assertEqual(result[0].target_title, 'north door')
        self.assertEqual(result[0].message, 'The north door is not locked.')

    def test_pick_lock_6(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetNotFound)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, 'This room has no wooden chest.')

    def test_pick_lock_7(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here.is_locked = False
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetNotLocked)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is not locked.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.container_here.is_locked)

    def test_pick_lock_8(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)
        result = self.command_processor.process('pick lock on east door')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetHasBeenUnlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)

    def test_pick_lock_9(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)
        result = self.command_processor.process('pick lock on east door')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetHasBeenUnlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)
        result = self.command_processor.process('leave via east door')
        result = self.command_processor.process('pick lock on west door')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetNotLocked)
        self.assertEqual(result[0].target_title, 'west door')
        self.assertEqual(result[0].message, 'The west door is not locked.')

    def test_pick_lock_10(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)
        result = self.command_processor.process('pick lock on east door')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetHasBeenUnlocked)
        self.assertEqual(result[0].target_title, 'east door')
        self.assertEqual(result[0].message, 'You have unlocked the east door.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.east_door.is_locked)

    def test_pick_lock_11(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.assertTrue(self.command_processor.game_state.rooms_state.cursor.container_here.is_locked)
        result = self.command_processor.process('pick lock on wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.pklock.TargetHasBeenUnlocked)
        self.assertEqual(result[0].target_title, 'wooden chest')
        self.assertEqual(result[0].message, 'You have unlocked the wooden chest.')
        self.assertFalse(self.command_processor.game_state.rooms_state.cursor.container_here.is_locked)

    def test_pick_lock_12(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on mana potion')
        self.assertIsInstance(result[0], advg.stmsg.pklock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'mana potion')
        self.assertEqual(result[0].target_type, 'potion')
        self.assertEqual(result[0].message, "You can't pick a lock on the mana potion; potions are not unlockable."),

    def test_pick_lock_13(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('pick lock on kobold')
        self.assertIsInstance(result[0], advg.stmsg.pklock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'kobold')
        self.assertEqual(result[0].target_type, 'creature')
        self.assertEqual(result[0].message, "You can't pick a lock on the kobold; creatures are not unlockable."),

    def test_pick_lock_14(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('pick lock on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.pklock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'kobold corpse')
        self.assertEqual(result[0].target_type, 'corpse')
        self.assertEqual(result[0].message, "You can't pick a lock on the kobold corpse; corpses are not unlockable."),

    def test_pick_lock_15(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('pick lock on east doorway')
        self.assertIsInstance(result[0], advg.stmsg.pklock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'east doorway')
        self.assertEqual(result[0].target_type, 'doorway')
        self.assertEqual(result[0].message, "You can't pick a lock on the east doorway; doorways are not unlockable.")

    def test_pick_lock_16(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        studded_leather_armor = self.items_state.get('Studded_Leather')
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process('pick lock on studded leather armor')
        self.assertIsInstance(result[0], advg.stmsg.pklock.ElementNotUnlockable)
        self.assertEqual(result[0].target_title, 'studded leather armor')
        self.assertEqual(result[0].target_type, 'armor')
        self.assertEqual(result[0].message, "You can't pick a lock on the studded leather armor; suits of armor are not unlockable."),


class Test_Pick_Up(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True

    def test_pick_up_1(self):
        result = self.command_processor.process('pick up the')  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'PICK UP')
        self.assertEqual(result[0].message, "PICK UP command: bad syntax. Should be 'PICK\u00A0UP\u00A0<item\u00A0name>"
                                            "' or 'PICK\u00A0UP\u00A0<number>\u00A0<item\u00A0name>'."),

    def test_pick_up_2(self):
        result = self.command_processor.process('pick up a gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.QuantityUnclear)
        self.assertEqual(result[0].message, 'Amount to pick up unclear. How many do you mean?')

    def test_pick_up_3(self):
        result = self.command_processor.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemNotFound)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 15)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no gold coins here. However, there is 2 health potions and a '
                                            'mana potion here.')

    def test_pick_up_4(self):
        result = self.command_processor.process('pick up fifteen gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemNotFound)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 15)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no gold coins here. However, there is 2 health potions and a '
                                            'mana potion here.')

    def test_pick_up_5(self):
        result = self.command_processor.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemNotFound)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ((2, 'health potion'), (1, 'mana potion')))
        self.assertEqual(result[0].message, 'You see no short sword here. However, there is 2 health potions and a '
                                            'mana potion here.')

    def test_pick_up_6(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('pick up a short sword')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemNotFound)
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].items_here, ())
        self.assertEqual(result[0].message, 'You see no short sword here.')
        self.command_processor.game_state.rooms_state.move(south=True)

    def test_pick_up_7(self):
        result = self.command_processor.process('pick up 2 mana potions')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.TryingToPickUpMoreThanIsPresent)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, "You can't pick up 2 mana potions. Only 1 is here.")

    def test_pick_up_8(self):
        result = self.command_processor.process('pick up a mana potion')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemPickedUp)
        self.assertEqual(result[0].item_title, 'mana potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 1)
        self.assertEqual(result[0].message, 'You picked up a mana potion. You have a mana potion.')

    def test_pick_up_9(self):
        result = self.command_processor.process('pick up a health potion')  # check
        result = self.command_processor.process('pick up health potion')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemPickedUp)
        self.assertEqual(result[0].item_title, 'health potion')
        self.assertEqual(result[0].pick_up_amount, 1)
        self.assertEqual(result[0].amount_had, 2)
        self.assertEqual(result[0].message, 'You picked up a health potion. You have 2 health potions.')

    def test_pick_up_10(self):
        gold_coin = self.items_state.get('Gold_Coin')
        self.command_processor.game_state.rooms_state.cursor.items_here.set('Gold_Coin', 30, gold_coin)
        result = self.command_processor.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemPickedUp)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 15)
        self.assertEqual(result[0].message, 'You picked up 15 gold coins. You have 15 gold coins.')
        result = self.command_processor.process('pick up 15 gold coins')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.ItemPickedUp)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].pick_up_amount, 15)
        self.assertEqual(result[0].amount_had, 30)
        self.assertEqual(result[0].message, 'You picked up 15 gold coins. You have 30 gold coins.')

    def test_pick_up_11(self):
        result = self.command_processor.process('pick up wooden chest')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.CantPickUpChestCorpseCreatureOrDoor)
        self.assertEqual(result[0].element_type, 'chest')
        self.assertEqual(result[0].element_title, 'wooden chest')
        self.assertEqual(result[0].message, "You can't pick up the wooden chest: can't pick up chests!")

    def test_pick_up_12(self):
        result = self.command_processor.process('pick up kobold')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.CantPickUpChestCorpseCreatureOrDoor)
        self.assertEqual(result[0].element_type, 'creature')
        self.assertEqual(result[0].element_title, 'kobold')
        self.assertEqual(result[0].message, "You can't pick up the kobold: can't pick up creatures!")

    def test_pick_up_13(self):
        result = self.command_processor.process('pick up north iron door')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.CantPickUpChestCorpseCreatureOrDoor)
        self.assertEqual(result[0].element_type, 'door')
        self.assertEqual(result[0].element_title, 'north door')
        self.assertEqual(result[0].message, "You can't pick up the north door: can't pick up doors!")

    def test_pick_up_14(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('pick up kobold corpse')  # check
        self.assertIsInstance(result[0], advg.stmsg.pickup.CantPickUpChestCorpseCreatureOrDoor)
        self.assertEqual(result[0].element_type, 'corpse')
        self.assertEqual(result[0].element_title, 'kobold corpse')
        self.assertEqual(result[0].message, "You can't pick up the kobold corpse: can't pick up corpses!")


class Test_Processor_Process(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_command_not_recognized_in_pregame(self):
        result = self.command_processor.process('juggle')
        self.assertIsInstance(result[0], advg.stmsg.command.NotRecognized)
        self.assertEqual(result[0].command, 'juggle')
        self.assertEqual(result[0].allowed_commands, {'begin_game', 'set_name', 'help', 'quit', 'set_class', 'reroll'})
        self.assertEqual(result[0].message, "Command 'juggle' not recognized. Commands allowed before game start are "
                                            'BEGIN GAME, HELP, QUIT, REROLL, SET CLASS, and SET NAME.')

    def test_command_not_recognized_during_game(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.command_processor.game_state.game_has_begun = True
        result = self.command_processor.process('juggle')
        self.assertIsInstance(result[0], advg.stmsg.command.NotRecognized)
        self.assertEqual(result[0].command, 'juggle')
        self.assertEqual(result[0].allowed_commands, {'attack', 'cast_spell', 'close', 'drink', 'drop', 'equip',
                                                      'leave', 'inventory', 'leave', 'look_at', 'lock', 'open', 'help',
                                                      'pick_lock', 'pick_up', 'put', 'quit', 'status', 'take',
                                                      'unequip', 'unlock'})
        self.assertEqual(result[0].message, "Command 'juggle' not recognized. Commands allowed during the game are "
                                            'ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, INVENTORY, LEAVE, '
                                            'LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, QUIT, STATUS, TAKE, UNEQUIP,'
                                            ' and UNLOCK.')

    def test_command_not_allowed_in_pregame(self):
        result = self.command_processor.process('attack kobold')
        self.assertIsInstance(result[0], advg.stmsg.command.NotAllowedNow)
        self.assertEqual(result[0].command, 'attack')
        self.assertEqual(result[0].allowed_commands, {'begin_game', 'help', 'reroll', 'set_name', 'quit', 'set_class'})
        self.assertEqual(result[0].message, "Command 'attack' not allowed before game start. Commands allowed before "
                                            'game start are BEGIN GAME, HELP, QUIT, REROLL, SET CLASS, and SET NAME.')

    def test_command_not_allowed_during_game(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.command_processor.game_state.game_has_begun = True
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], advg.stmsg.command.NotAllowedNow)
        self.assertEqual(result[0].command, 'reroll')
        self.assertEqual(result[0].allowed_commands, {'attack', 'cast_spell', 'close', 'drink', 'drop', 'equip', 'help',
                                                      'leave', 'inventory', 'leave', 'look_at', 'lock', 'open',
                                                      'pick_lock', 'pick_up', 'quit', 'put', 'quit', 'status', 'take',
                                                      'unequip', 'unlock'})
        self.assertEqual(result[0].message, "Command 'reroll' not allowed during the game. Commands allowed during "
                                            'the game are ATTACK, CAST SPELL, CLOSE, DRINK, DROP, EQUIP, HELP, '
                                            'INVENTORY, LEAVE, LOCK, LOOK AT, OPEN, PICK LOCK, PICK UP, PUT, QUIT, '
                                            'STATUS, TAKE, UNEQUIP, and UNLOCK.')


class Test_Put(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
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
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
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
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
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
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
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
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
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
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainer)
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
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerIsClosed)
        self.assertEqual(result[0].target, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is closed.')

    def test_put_7(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('put in')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('put 1 gold coin in')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('put in the wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('put 1 gold coin on the wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, 'PUT command: bad syntax. Should be '
                                            "'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0"
                                            "name>', 'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', "
                                            "or 'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0"
                                            "name>'."),

    def test_put_8(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take gold coins from wooden chest')
        result = self.command_processor.process('put gold coins in wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].amount_put, 15)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, 'You put 15 gold coins in the wooden chest. You have no more gold coins.')


class Test_Quit(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_quit_1(self):
        result = self.command_processor.process('quit the game now')  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'QUIT')
        self.assertEqual(result[0].message, "QUIT command: bad syntax. Should be 'QUIT'.")

    def test_quit_2(self):
        result = self.command_processor.process('quit')  # check
        self.assertIsInstance(result[0], advg.stmsg.quit.HaveQuitTheGame)
        self.assertEqual(result[0].message, 'You have quit the game.')
        self.assertTrue(self.command_processor.game_state.game_has_ended)


class Test_Set_Name_Vs_Set_Class_Vs_Reroll_Vs_Begin_Games(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_reroll_1(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll stats')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")

    def test_begin_game_1(self):
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], advg.stmsg.reroll.NameOrClassNotSet)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            'reroll. Use SET NAME <name> to set your name and SET CLASS <Warrior, '
                                            'Thief, Mage or Priest> to select your class.')

    def test_begin_game_2(self):
        self.command_processor.process('set class to Warrior')
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], advg.stmsg.reroll.NameOrClassNotSet)
        self.assertEqual(result[0].character_name, None)
        self.assertEqual(result[0].character_class, 'Warrior')
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            'reroll. Use SET NAME <name> to set your name.')

    def test_begin_game_3(self):
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], advg.stmsg.reroll.NameOrClassNotSet)
        self.assertEqual(result[0].character_name, 'Kerne')
        self.assertEqual(result[0].character_class, None)
        self.assertEqual(result[0].message, "Your character's stats haven't been rolled yet, so there's nothing to "
                                            'reroll. Use SET CLASS <Warrior, Thief, Mage or Priest> to select your '
                                            'class.')

    def test_begin_game_4(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll my stats')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")

    def test_begin_game_5(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll')
        self.assertIsInstance(result[0], advg.stmsg.various.DisplayRolledStats)

    def test_set_name_vs_set_class_1(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        result = self.command_processor.process('set class')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('set class dread necromancer')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'SET CLASS')
        self.assertEqual(result[0].message, 'SET CLASS command: bad syntax. Should be '
                                            "'SET\u00A0CLASS\u00A0[TO]\u00A0<Warrior,\u00A0Thief,\u00A0Mage\u00A0"
                                            "or\u00A0Priest>'.")

        result = self.command_processor.process('set class to Warrior')
        self.assertIsInstance(result[0], advg.stmsg.setcls.ClassSet)
        self.assertEqual(result[0].class_str, 'Warrior')
        self.assertEqual(result[0].message, 'Your class, Warrior, has been set.')

        result = self.command_processor.process('set name')  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'SET NAME')
        self.assertEqual(result[0].message, 'SET NAME command: bad syntax. Should be '
                                            "'SET\u00A0NAME\u00A0[TO]\u00A0<character\u00A0name>'.")

        result = self.command_processor.process('set name to Kerne')
        self.assertIsInstance(result[0], advg.stmsg.setname.NameSet)
        self.assertEqual(result[0].name, 'Kerne')
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")
        self.assertIsInstance(result[1], advg.stmsg.various.DisplayRolledStats)
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
        self.assertEqual(result[1].message, f'Your ability scores are Strength\u00A0{result[1].strength}, '
                                            f'Dexterity\u00A0{result[1].dexterity}, '
                                            f'Constitution\u00A0{result[1].constitution}, '
                                            f'Intelligence\u00A0{result[1].intelligence}, '
                                            f'Wisdom\u00A0{result[1].wisdom}, '
                                            f'Charisma\u00A0{result[1].charisma}.\n\n'
                                            'Would you like to reroll or begin the game?')
        first_roll = second_roll = {'strength': result[1].strength, 'dexterity': result[1].dexterity,
                                    'constitution': result[1].constitution, 'intelligence': result[1].intelligence,
                                    'wisdom': result[1].wisdom, 'charisma': result[1].charisma}
        while first_roll == second_roll:
            result = self.command_processor.process('reroll')
            second_roll = {'strength': result[0].strength, 'dexterity': result[0].dexterity,
                          'constitution': result[0].constitution, 'intelligence': result[0].intelligence,
                      'wisdom': result[0].wisdom, 'charisma': result[0].charisma}
        self.assertIsInstance(result[0], advg.stmsg.various.DisplayRolledStats)
        self.assertNotEqual(first_roll, second_roll)

        result = self.command_processor.process('begin game')
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBegins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_2(self):
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('begin')
        self.assertIsInstance(result[0], advg.stmsg.begin.GameBegins)
        self.assertEqual(result[0].message, 'The game has begun!')
        self.assertTrue(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_3(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('begin the game now')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN\u00A0GAME'.")
        self.assertFalse(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_4(self):
        result = self.command_processor.process('set name to Kerne0')
        self.assertIsInstance(result[0], advg.stmsg.setname.InvalidPart)
        self.assertEqual(result[0].name_part, 'Kerne0')
        self.assertEqual(result[0].message, 'The name Kerne0 is invalid; must be a capital letter followed by '
                                            'lowercase letters.')

        result = self.command_processor.process('set name to Kerne MacDonald0 Fahey1')
        self.assertIsInstance(result[0], advg.stmsg.setname.InvalidPart)
        self.assertEqual(result[0].name_part, 'MacDonald0')
        self.assertEqual(result[0].message, 'The name MacDonald0 is invalid; must be a capital letter followed by '
                                            'lowercase letters.')
        self.assertIsInstance(result[1], advg.stmsg.setname.InvalidPart)
        self.assertEqual(result[1].name_part, 'Fahey1')
        self.assertEqual(result[1].message, 'The name Fahey1 is invalid; must be a capital letter followed by '
                                            'lowercase letters.')

        result = self.command_processor.process('set name to Kerne')
        self.assertIsInstance(result[0], advg.stmsg.setname.NameSet)
        self.assertEqual(result[0].name, 'Kerne')
        self.assertEqual(result[0].message, "Your name, 'Kerne', has been set.")

        result = self.command_processor.process('set class to Ranger')
        self.assertIsInstance(result[0], advg.stmsg.setcls.InvalidClass)
        self.assertEqual(result[0].bad_class, 'Ranger')
        self.assertEqual(result[0].message, "'Ranger' is not a valid class choice. Please choose Warrior, Thief, "
                                            'Mage, or Priest.')

        result = self.command_processor.process('set class to Warrior')
        self.assertIsInstance(result[0], advg.stmsg.setcls.ClassSet)
        self.assertEqual(result[0].class_str, 'Warrior')
        self.assertEqual(result[0].message, 'Your class, Warrior, has been set.')
        self.assertIsInstance(result[1], advg.stmsg.various.DisplayRolledStats)
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
        result = self.command_processor.process('begin the game now')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'BEGIN GAME')
        self.assertEqual(result[0].message, "BEGIN GAME command: bad syntax. Should be 'BEGIN\u00A0GAME'.")
        self.assertFalse(self.command_processor.game_state.game_has_begun)

    def test_set_name_vs_set_class_vs_reroll(self):
        self.assertFalse(self.command_processor.game_state.game_has_begun)
        self.command_processor.process('set class to Warrior')
        self.command_processor.process('set name to Kerne')
        result = self.command_processor.process('reroll please')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'REROLL')
        self.assertEqual(result[0].message, "REROLL command: bad syntax. Should be 'REROLL'.")
        self.assertFalse(self.command_processor.game_state.game_has_begun)


class Test_Status(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)

    def test_status1(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status status')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
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
        self.assertIsInstance(result[0], advg.stmsg.status.StatusOutput)
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
        self.assertIsInstance(result[0], advg.stmsg.status.StatusOutput)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: [+-]\d+ '
                                            r'\(\d+d[\d+-]+ damage\) - Armor Class: \d+ \| Weapon: [a-z ]+ - Wand: '
                                            r'[a-z ]+')

    def test_status4(self):
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], advg.stmsg.status.StatusOutput)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: no wand or weapon '
                                            r'equipped - Armor Class: \d+ \| Weapon: none - Wand: none')

    def test_status5(self):
        self.command_processor.game_state.character_name = 'Niath'
        self.command_processor.game_state.character_class = 'Warrior'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], advg.stmsg.status.StatusOutput)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ \| Attack: no weapon equipped - Armor Class: \d+ \| '
                                            r'Weapon: none - Armor: none - Shield: none')

    def test_status6(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], advg.stmsg.status.StatusOutput)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: \d+/\d+ \| Attack: no weapon equipped '
                                            r'- Armor Class: \d+ \| Weapon: none - Armor: none - Shield: none')

    def test_status7(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.take_damage(10)
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], advg.stmsg.status.StatusOutput)
        self.assertRegex(result[0].message, r'Hit Points: (?!(\d+)/\1)\d+/\d+ - Mana Points: \d+/\d+ \| Attack: no '
                                            r'weapon equipped - Armor Class: \d+ \| Weapon: none - Armor: none - '
                                             'Shield: none')

    def test_status8(self):
        self.command_processor.game_state.character_name = 'Kaeva'
        self.command_processor.game_state.character_class = 'Priest'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.spend_mana(10)
        result = self.command_processor.process('status')
        self.assertIsInstance(result[0], advg.stmsg.status.StatusOutput)
        self.assertRegex(result[0].message, r'Hit Points: \d+/\d+ - Mana Points: (?!(\d+)/\1)\d+/\d+ \| Attack: no '
                                            r'weapon equipped - Armor Class: \d+ \| Weapon: none - Armor: none - '
                                             'Shield: none')


class Test_Take(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
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
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTaken)
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
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTaken)
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
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTaken)

    def test_take_4(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take one small leather armor from the kobold corpses')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('take one small leather armor')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('take the from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        result = self.command_processor.process('take the short sword from the')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'TAKE')
        self.assertEqual(result[0].message, 'TAKE command: bad syntax. Should be '
                                            "'TAKE\u00A0<item\u00A0name>\u00A0FROM\u00A0<container\u00A0name>' or "
                                            "'TAKE\u00A0<number>\u00A0<item\u00A0name>\u00A0FROM\u00A0<container"
                                            "\u00A0name>'."),

    def test_take_5(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take the short sword from the sorcerer corpse')  # check
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerNotFound)
        self.assertEqual(result[0].container_not_found_title, 'sorcerer corpse')
        self.assertEqual(result[0].container_present_title, 'kobold corpse')
        self.assertEqual(result[0].message, 'There is no sorcerer corpse here. However, there *is* a kobold corpse '
                                            'here.')

    def test_take_6(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        container = self.command_processor.game_state.rooms_state.cursor.container_here  # check
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process('take the short sword from the sorcerer corpse')
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerNotFound)
        self.assertEqual(result[0].container_not_found_title, 'sorcerer corpse')
        self.assertIs(result[0].container_present_title, None)
        self.assertEqual(result[0].message, 'There is no sorcerer corpse here.')
        self.command_processor.game_state.rooms_state.cursor.container_here = container

    def test_take_7(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take 3 small leather armors from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.take.TryingToTakeMoreThanIsPresent)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'small leather armor')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, "You can't take 3 suits of small leather armor from the kobold corpse. "
                                            'Only 1 is there.')

    def test_take_8(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.process('take the short sword from the kobold corpse')
        result = self.command_processor.process('take the short sword from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainer)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertIs(result[0].amount_attempted, 1)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The kobold corpse doesn't have a short sword on them.")

    def test_take_9(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.process('take the short sword from the kobold corpse')
        result = self.command_processor.process('take three short swords from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainer)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The kobold corpse doesn't have any short swords on them.")

    def test_take_10(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('take fifteen gold coins from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTaken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

    def test_take_11(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take gold coins from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTaken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

    def test_take_12(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take gold coin from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTaken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 15)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].message, 'You took 15 gold coins from the kobold corpse.')

    def test_take_13(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take a small leather armor from the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.take.ItemOrItemsTaken)
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].amount_taken, 1)
        self.assertEqual(result[0].item_title, 'small leather armor')
        self.assertEqual(result[0].message, 'You took a small leather armor from the kobold corpse.')

    def test_take_14(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 30, self.gold_coin)
        result = self.command_processor.process('take 30 gold coins from the kobold corpse')
        result = self.command_processor.process('put 15 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 15)
        self.assertEqual(result[0].amount_left, 15)
        self.assertEqual(result[0].message, "You put 15 gold coins on the kobold corpse's person. You have 15 gold "
                                            'coins left.')

    def test_take_15(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 15 gold coins from the kobold corpse')
        result = self.command_processor.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 14)
        self.assertEqual(result[0].message, "You put 1 gold coin on the kobold corpse's person. You have 14 gold "
                                            'coins left.')

    def test_take_16(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 14 gold coins from the kobold corpse')
        result = self.command_processor.process('put 13 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 13)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, "You put 13 gold coins on the kobold corpse's person. You have 1 gold "
                                            'coin left.')

    def test_take_17(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take fourteen gold coins from the kobold corpse')
        result = self.command_processor.process('put thirteen gold coins on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 13)
        self.assertEqual(result[0].amount_left, 1)
        self.assertEqual(result[0].message, "You put 13 gold coins on the kobold corpse's person. You have 1 gold "
                                            'coin left.')

    def test_take_18(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 1 gold coin from the kobold corpse')
        result = self.command_processor.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.PutAmountOfItem)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].container_title, 'kobold corpse')
        self.assertEqual(result[0].container_type, 'corpse')
        self.assertEqual(result[0].amount_put, 1)
        self.assertEqual(result[0].amount_left, 0)
        self.assertEqual(result[0].message, "You put 1 gold coin on the kobold corpse's person. You have no more gold "
                                            'coins.')

    def test_take_19(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 2 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.ItemNotInInventory)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 2)
        self.assertEqual(result[0].message, "You don't have any gold coins in your inventory.")

    def test_take_20(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 1 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.ItemNotInInventory)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_attempted, 1)
        self.assertEqual(result[0].message, "You don't have a gold coin in your inventory.")

    def test_take_21(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take five gold coins from the kobold corpse')
        result = self.command_processor.process('put ten gold coin on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.TryingToPutMoreThanYouHave)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_present, 5)
        self.assertEqual(result[0].message, 'You only have 5 gold coins in your inventory.')

    def test_take_22(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 5 gold coins from the kobold corpse')
        result = self.command_processor.process('put 10 gold coin on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.TryingToPutMoreThanYouHave)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_present, 5)
        self.assertEqual(result[0].message, 'You only have 5 gold coins in your inventory.')

    def test_take_23(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('take 5 gold coins from the kobold corpse')
        result = self.command_processor.process('put 4 gold coins on the kobold corpse')
        result = self.command_processor.process('put 4 gold coins on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.TryingToPutMoreThanYouHave)
        self.assertEqual(result[0].item_title, 'gold coin')
        self.assertEqual(result[0].amount_present, 1)
        self.assertEqual(result[0].message, 'You only have 1 gold coin in your inventory.')

    def test_take_24(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put a gold coins on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.put.QuantityUnclear)
        self.assertEqual(result[0].message, 'Amount to put unclear. How many do you mean?')

    def test_take_25(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put on the kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, 'PUT command: bad syntax. Should be '
                                            "'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'"
                                            '.'),

    def test_take_26(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put one small leather armor on')  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, 'PUT command: bad syntax. Should be '
                                            "'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>"
                                            "'."),

    def test_take_27(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put on')  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, 'PUT command: bad syntax. Should be '
                                            "'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'"
                                            '.'),

    def test_take_28(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        self.command_processor.game_state.rooms_state.cursor.container_here.set('Gold_Coin', 15, self.gold_coin)
        result = self.command_processor.process('put 1 gold coin in the kobold corpse')  # check
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'PUT')
        self.assertEqual(result[0].message, 'PUT command: bad syntax. Should be '
                                            "'PUT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
                                            "'PUT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', or "
                                            "'PUT\u00A0<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>"
                                            "'."),

    def test_take_29(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process('take three short swords from the wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.take.ItemNotFoundInContainer)
        self.assertEqual(result[0].container_title, 'wooden chest')
        self.assertEqual(result[0].amount_attempted, 3)
        self.assertEqual(result[0].container_type, 'chest')
        self.assertEqual(result[0].item_title, 'short sword')
        self.assertEqual(result[0].message, "The wooden chest doesn't have any short swords in it.")

    def test_take_30(self):
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process('take gold coin from wooden chest')
        self.assertIsInstance(result[0], advg.stmsg.various.ContainerIsClosed)
        self.assertEqual(result[0].target, 'wooden chest')
        self.assertEqual(result[0].message, 'The wooden chest is closed.')


class Test_Unequip_1(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.buckler = self.command_processor.game_state.items_state.get('Buckler')
        self.longsword = self.command_processor.game_state.items_state.get('Longsword')
        self.mace = self.command_processor.game_state.items_state.get('Heavy_Mace')
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
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'UNEQUIP')
        self.assertEqual(result[0].message, "UNEQUIP command: bad syntax. Should be 'UNEQUIP\u00A0<armor\u00A0name>', "
                                            "'UNEQUIP\u00A0<shield\u00A0name>', 'UNEQUIP\u00A0<wand\u00A0name>', or "
                                            "'UNEQUIP\u00A0<weapon\u00A0name>'.")

    def test_unequip_2(self):
        result = self.command_processor.process('unequip mace')
        self.assertIsInstance(result[0], advg.stmsg.unequip.ItemNotEquipped)
        self.assertEqual(result[0].item_specified_title, 'mace')
        self.assertEqual(result[0].message, "You're not wielding a mace.")

    def test_unequip_3(self):
        result = self.command_processor.process('unequip steel shield')
        self.assertIsInstance(result[0], advg.stmsg.unequip.ItemNotEquipped)
        self.assertEqual(result[0].item_specified_title, 'steel shield')
        self.assertEqual(result[0].message, "You're not carrying a steel shield.")

    def test_unequip_4(self):
        result = self.command_processor.process('unequip scale mail armor')
        self.assertIsInstance(result[0], advg.stmsg.unequip.ItemNotEquipped)
        self.assertEqual(result[0].item_specified_title, 'scale mail armor')
        self.assertEqual(result[0].message, "You're not wearing a suit of scale mail armor.")

    def test_unequip_5(self):
        result = self.command_processor.process('unequip magic wand')
        self.assertIsInstance(result[0], advg.stmsg.unequip.ItemNotEquipped)
        self.assertEqual(result[0].item_specified_title, 'magic wand')
        self.assertEqual(result[0].message, "You're not using a magic wand.")

    def test_unequip_6(self):
        result = self.command_processor.process('equip mace')
        result = self.command_processor.process('unequip mace')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'mace')
        self.assertEqual(result[0].message, "You're no longer wielding a mace. You now can't attack.")

    def test_unequip_7(self):
        result = self.command_processor.process('equip steel shield')
        result = self.command_processor.process('unequip steel shield')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'steel shield')
        self.assertRegex(result[0].message, r"^You're no longer carrying a steel shield. Your armor class is now \d+.$")

    def test_unequip_8(self):
        result = self.command_processor.process('equip scale mail armor')
        result = self.command_processor.process('unequip scale mail armor')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'scale mail armor')
        self.assertRegex(result[0].message, r"^You're no longer wearing a suit of scale mail armor. Your armor class is now \d+.$")


class Test_Unequip_2(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.staff = self.command_processor.game_state.items_state.get('Staff')
        self.magic_wand = self.command_processor.game_state.items_state.get('Magic_Wand')
        self.command_processor.game_state.character_name = 'Mialee'
        self.command_processor.game_state.character_class = 'Mage'
        self.game_state.game_has_begun = True
        self.command_processor.game_state.character.pick_up_item(self.staff)
        self.command_processor.game_state.character.pick_up_item(self.magic_wand)

    def test_unequip_8(self):
        result = self.command_processor.process('equip staff')
        result = self.command_processor.process('equip magic wand')
        result = self.command_processor.process('unequip magic wand')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'magic wand')
        self.assertRegex(result[0].message, r"^You're no longer using a magic wand. You're now attacking with your "
                                            r'staff. Your attack bonus is now [+-]\d+ and your staff damage is now '
                                            r'\d+d\d+([+-]\d+)?.$')

    def test_unequip_9(self):
        result = self.command_processor.process('equip staff')
        result = self.command_processor.process('equip magic wand')
        result = self.command_processor.process('unequip staff')
        self.assertIsInstance(result[0], advg.stmsg.various.ItemUnequipped)
        self.assertEqual(result[0].item_title, 'staff')
        self.assertRegex(result[0].message, r"^You're no longer wielding a staff. You're attacking with your "
                                            r'magic wand. Your attack bonus is [+-]\d+ and your magic wand damage '
                                            r'is \d+d\d+([+-]\d+)?.$')


class Test_Unlock(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = advg.ItemsState(**items_ini_config.sections)
        self.doors_state = advg.DoorsState(**doors_ini_config.sections)
        self.containers_state = advg.ContainersState(self.items_state, **containers_ini_config.sections)
        self.creatures_state = advg.CreaturesState(self.items_state, **creatures_ini_config.sections)
        self.rooms_state = advg.RoomsState(self.creatures_state, self.containers_state, self.doors_state,
                                           self.items_state, **rooms_ini_config.sections)
        self.game_state = advg.GameState(self.rooms_state, self.creatures_state, self.containers_state,
                                         self.doors_state, self.items_state)
        self.command_processor = advg.Command_Processor(self.game_state)
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True

        self.door = self.command_processor.game_state.rooms_state.cursor.north_door
        self.door.is_locked = True
        self.door_title = self.command_processor.game_state.rooms_state.cursor.north_door.title
        self.chest = self.command_processor.game_state.rooms_state.cursor.container_here
        self.chest.is_locked = True
        self.chest_title = self.chest.title

    def test_unlock_1(self):
        result = self.command_processor.process('unlock')
        self.assertIsInstance(result[0], advg.stmsg.command.BadSyntax)
        self.assertEqual(result[0].command, 'UNLOCK')
        self.assertEqual(result[0].message, "UNLOCK command: bad syntax. Should be 'UNLOCK\u00A0<door\u00A0name>' or "
                                            "'UNLOCK\u00A0<chest\u00A0name>'."),

    def test_unlock_2(self):
        result = self.command_processor.process('unlock west door')
        self.assertIsInstance(result[0], advg.stmsg.various.DoorNotPresent)
        self.assertEqual(result[0].compass_dir, 'west')
        self.assertEqual(result[0].portal_type, 'door')
        self.assertEqual(result[0].message, 'This room does not have a west door.'),
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked
        self.door_title = self.command_processor.game_state.rooms_state.cursor.north_door.title

    def test_unlock_3(self):
        result = self.command_processor.process(f'unlock {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.unlock.DontPossessCorrectKey)
        self.assertEqual(result[0].object_to_unlock_title, self.door_title)
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, f'To unlock the {self.door_title} you need a door key.')
        self.assertTrue(self.door.is_locked)

    def test_unlock_4(self):
        self.door.is_locked = False
        key = self.command_processor.game_state.items_state.get('Door_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'unlock {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementIsAlreadyLocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'The {self.door_title} is already unlocked.')
        self.assertFalse(self.door.is_locked)

        self.door.is_locked = True
        result = self.command_processor.process(f'unlock {self.door_title}')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementHasBeenLocked)
        self.assertEqual(result[0].target, self.door_title)
        self.assertEqual(result[0].message, f'You have unlocked the {self.door_title}.')
        self.assertFalse(self.door.is_locked)
        self.command_processor.game_state.rooms_state.move(north=True)

        result = self.command_processor.process(f'unlock south door')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementIsAlreadyLocked)
        self.assertEqual(result[0].target, 'south door')
        self.assertEqual(result[0].message, f'The south door is already unlocked.')

    def test_unlock_5(self):
        result = self.command_processor.process(f'unlock {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.unlock.DontPossessCorrectKey)
        self.assertEqual(result[0].object_to_unlock_title, self.chest_title)
        self.assertEqual(result[0].key_needed, 'chest key')
        self.assertEqual(result[0].message, f'To unlock the {self.chest_title} you need a chest key.')
        self.assertTrue(self.chest.is_locked)

    def test_unlock_6(self):
        self.chest.is_locked = False
        key = self.command_processor.game_state.items_state.get('Chest_Key')
        self.command_processor.game_state.character.pick_up_item(key)
        result = self.command_processor.process(f'unlock {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementIsAlreadyLocked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'The {self.chest_title} is already unlocked.')
        self.assertFalse(self.chest.is_locked)

        self.chest.is_locked = True
        result = self.command_processor.process(f'unlock {self.chest_title}')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementHasBeenLocked)
        self.assertEqual(result[0].target, self.chest_title)
        self.assertEqual(result[0].message, f'You have unlocked the {self.chest_title}.')
        self.assertFalse(self.chest.is_locked)

    def test_unlock_7(self):
        result = self.command_processor.process('unlock north iron door')
        self.assertIsInstance(result[0], advg.stmsg.unlock.DontPossessCorrectKey)
        self.assertEqual(result[0].object_to_unlock_title, 'north door')
        self.assertEqual(result[0].key_needed, 'door key')
        self.assertEqual(result[0].message, 'To unlock the north door you need a door key.')

    def test_unlock_8(self):
        result = self.command_processor.process('unlock mana potion')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementNotLockable)
        self.assertEqual(result[0].target_title, 'mana potion')
        self.assertEqual(result[0].target_type, 'potion')
        self.assertEqual(result[0].message, "You can't unlock the mana potion; potions are not unlockable."),

    def test_unlock_9(self):
        result = self.command_processor.process('unlock kobold')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementNotLockable)
        self.assertEqual(result[0].target_title, 'kobold')
        self.assertEqual(result[0].target_type, 'creature')
        self.assertEqual(result[0].message, "You can't unlock the kobold; creatures are not unlockable."),

    def test_unlock_10(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = \
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        result = self.command_processor.process('unlock kobold corpse')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementNotLockable)
        self.assertEqual(result[0].target_title, 'kobold corpse')
        self.assertEqual(result[0].target_type, 'corpse')
        self.assertEqual(result[0].message, "You can't unlock the kobold corpse; corpses are not unlockable."),

    def test_unlock_11(self):
        result = self.command_processor.process('pick lock on north door')
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process('unlock east doorway')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementNotLockable)
        self.assertEqual(result[0].target_title, 'east doorway')
        self.assertEqual(result[0].target_type, 'doorway')
        self.assertEqual(result[0].message, "You can't unlock the east doorway; doorways are not unlockable.")

    def test_unlock_12(self):
        self.command_processor.game_state.character_name = 'Lidda'
        self.command_processor.game_state.character_class = 'Thief'
        self.game_state.game_has_begun = True
        studded_leather_armor = self.items_state.get('Studded_Leather')
        self.command_processor.game_state.character.pick_up_item(studded_leather_armor)
        result = self.command_processor.process('unlock studded leather armor')
        self.assertIsInstance(result[0], advg.stmsg.unlock.ElementNotLockable)
        self.assertEqual(result[0].target_title, 'studded leather armor')
        self.assertEqual(result[0].target_type, 'armor')
        self.assertEqual(result[0].message, "You can't unlock the suit of studded leather armor; suits of armor are not unlockable."),
