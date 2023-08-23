#!/usr/bin/python3

"""
The CommandProcessor class which processes a natural-language command
and executes it in the game object environment, modifying the game state
and generating a natural-language response.
"""


import itertools
import math
import operator
import re
import types

import adventuregame.elements as elem
import adventuregame.exceptions as excpt
import adventuregame.statemsgs as stmsg
import adventuregame.utility as util


__name__ = 'adventuregame.processor'


# This module consists solely of the CommandProcessor class and its supporting
# data structures. CommandProcessor is a monolithic class that has a process()
# method which accepts a natural language command and dispatches it to the
# appropriate command method. Every command in the game corresponds to a method of
# the CommandProcessor class, and each method always returns a tuple of one or
# more adventuregame.statemsgs.GameStateMessage subclass objects. Typically, the
# bulk of the logic in a given command method is devoted to detecting player error
# and handling each error discretely. The logic that completes the command task is
# often a brief coda to a sophisticated conditional handling all the cases where
# the command can't complete.



SPELL_DAMAGE = '3d8+5'

SPELL_MANA_COST = 5

STARTER_GEAR = dict(Warrior=dict(weapon='Longsword', armor='Studded_Leather', shield='Buckler'),
                    Thief=dict(weapon='Rapier', armor='Studded_Leather'),
                    Mage=dict(weapon='Staff'),
                    Priest=dict(weapon='Heavy_Mace', armor='Studded_Leather', shield='Buckler'))


# The COMMAND_SYNTAX dict is a compendium of usage examples for every command in
# the game. When a command method needs to return Command_Bad_Syntax object, it
# consults this dict for the second argument to its constructor.
#
# \u00A0 is a unicode nonbreaking space. I use it in the syntax examples so that
# the use of adventuregame.utility.textwrapper() in advgame.py doesn't break
# individual syntax examples across lines. The longer syntax examples become
# difficult to read if wrapped across a line.

COMMANDS_SYNTAX = {
    'ATTACK': ('<creature\u00A0name>',),
    'BEGIN GAME': ('',),
    'CAST SPELL': ('',),
    'CLOSE': ('<door\u00A0name>', '<chest\u00A0name>'),
    'DRINK': ('[THE]\u00A0<potion\u00A0name>', '<number>\u00A0<potion\u00A0name>(s)'),
    'DROP': ('<item\u00A0name>', '<number>\u00A0<item\u00A0name>'),
    'EQUIP': ('<armor\u00A0name>', '<shield\u00A0name>', '<wand\u00A0name>', '<weapon\u00A0name>'),
    'HELP': ('', '<command\u00A0name>'),
    'INVENTORY': ('',),
    'LOOK AT': ('<item\u00A0name>', '<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
                '<item\u00A0name>\u00A0IN\u00A0INVENTORY',
                '<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', '<compass\u00A0direction>\u00A0DOOR',
                '<compass\u00A0direction>\u00A0DOORWAY'),
    'LEAVE': ('[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOOR',
              '[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOORWAY',
              '[USING\u00A0or\u00A0VIA]\u00A0<door\u00A0name>',
              '[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0<door\u00A0name>'),
    'LOCK': ('<door\u00A0name>', '<chest\u00A0name>'),
    'OPEN': ('<door\u00A0name>', '<chest\u00A0name>'),
    'PICK LOCK': ('ON\u00A0[THE]\u00A0<chest\u00A0name>', 'ON\u00A0[THE]\u00A0<door\u00A0name>'),
    'PICK UP': ('<item\u00A0name>', '<number>\u00A0<item\u00A0name>'),
    'PUT': ('<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
            '<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
            '<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>',
            '<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>'),
    'REROLL': ('',),
    'QUIT': ('',),
    'SET CLASS': ('[TO]\u00A0<Warrior,\u00A0Thief,\u00A0Mage\u00A0or\u00A0Priest>',),
    'SET NAME': ('[TO]\u00A0<character\u00A0name>',),
    'STATUS': ('',),
    'TAKE': ('<item\u00A0name>\u00A0FROM\u00A0<container\u00A0name>',
             '<number>\u00A0<item\u00A0name>\u00A0FROM\u00A0<container\u00A0name>'),
    'UNEQUIP': ('<armor\u00A0name>', '<shield\u00A0name>', '<wand\u00A0name>', '<weapon\u00A0name>'),
    'UNLOCK': ('<door\u00A0name>', '<chest\u00A0name>')
}

# The COMMANDS_HELP dict is a compendium of help blurbs for use by
# Command_Processor.help_command(). Where the blurb explicitly suggests another
# command, a nonbreaking space is used again to ensure the command doesn't get
# wrapped and is readable.

COMMANDS_HELP = {
    'ATTACK': "The ATTACK command is used to attack creatures. Beware: if you attack a creature and don't kill it, it "
              'will attack you in return! After you kill a creature, you can check its corpse for loot using the LOOK '
              'AT command and take loot with the TAKE command.',
    'BEGIN GAME': 'The BEGIN GAME command is used to start the game after you have set your name and class and approved'
                  ' your ability scores. When you enter this command, you will automatically be equiped with your '
                  'starting gear and started in the antechamber of the dungeon.',
    'CAST SPELL': 'The CAST SPELL command can only be used by Mages and Priests. A Mage can cast an attack spell that '
                  'automatically hits creatures and does damage. A Priest can cast a healing spell on themselves.',
    'CLOSE': 'The CLOSE command can be used to close doors and chests.',
    'DRINK': 'The DRINK command can be used to drink health or mana potions.',
    'DROP': 'The DROP command can be used to remove items from your inventory and leave them on the floor. If you drop '
            'an item you had equipped, it will automatically be unequipped unless you have another on you.',
    'EQUIP': "The EQUIP command can be used to equip a weapon, armor, shield or wand from your inventory. You can't "
             'equip items from the floor.',
    'HELP': 'The HELP command can be used to get help about any game commands.',
    'INVENTORY': 'The INVENTORY command can be used to get a listing of the items in your inventory. If you want more '
                  "information about an item, say 'LOOK\u00A0AT\u00A0<item\u00A0title>\u00A0IN\u00A0INVENTORY'.",
    'LOOK AT': 'The LOOK at command can be used to get more information about doors, items on the floor or in a chest '
               'or on a corpse, chests, creatures and corpses.',
    'LEAVE': "The LEAVE command is used to exit the room you're in using the door you specify. If the door is locked "
             'you will be unable to leave using it until you can unlock it.',
    'LOCK': 'The LOCK command is used to lock doors and chests. You need a door key to lock doors and a chest key to '
            'lock chests. These keys can be found somewhere in the dungeon.',
    'OPEN': 'The OPEN command is used to open doors and chests.',
    'PICK LOCK': 'Only Thieves can use the pick lock command. The pick lock command enables you to unlock a door or '
                 'chest without needing a key. This saves some searching!',
    'PICK UP': 'The PICK UP command can be used to acquire items from the floor and put them in your inventory. To '
               "acquire items from a chest, say '<item\u00A0name>\u00A0FROM\u00A0<chest\u00A0name>'. For a corpse, say "
               "'<item\u00A0name>\u00A0FROM\u00A0<chest\u00A0name>'.",
    'PUT': "The PUT command can be used to remove items from your inventory and place them in a chest or on a corpse's "
           'person. To leave items on the floor, use DROP.',
    'REROLL': 'The REROLL command is used before game start to get a fresh selection of randomly generated ability '
              'scores. You can reroll your ability scores as many times as you want.',
    'QUIT': 'The QUIT command is used to exit the game.',
    'SET CLASS': 'The SET CLASS command is used before game start to pick a class for your character. Your options are '
                 'Warrior, Thief, Mage or Priest.',
    'SET NAME': 'The SET NAME command is used before game start to pick a name for your character. Your name can have '
                'as many parts as you like, but each one must be a capital letter followed by lowercase letters. '
                'Symbols and numbers are not allowed.',
    'STATUS': 'The STATUS command is used to see a summary of your hit points and current weapon, armor, shield '
              "choices. Spellcasters also see their mana points; and Mages see their current wand if they're using "
              'one.',
    'TAKE': 'The TAKE command is used to remove items from a chest or a corpse and place them in your inventory.',
    'UNEQUIP': 'The UNEQUIP command is used to unequip a weapon, armor, shield or wand from your inventory.',
    'UNLOCK': 'The UNLOCK command is used to unlock a door or chest. You need a door key to unlock doors and a chest '
              'key to unlock chests.'
}


class Command_Processor(object):
    """
A processor that can parse a natural language command, modify the
game state appropriately, and return a GameStateMessage object that
stringifies to a natural language reply.
    """
    __slots__ = 'game_state', 'dispatch_table', 'game_ending_state_msg'

    # All return values from [a-z_]+_command methods in this class are
    # tuples. Every [a-z_]+_command method returns a tuple of one or more
    # adventuregame.statemsgs.Game_State_Message subclass objects reflecting a
    # change or set of changes in game State.
    #
    # For example, an ATTACK action that doesn't kill the foe will prompt
    # the foe to attack. The foe's attack might lead to the character's
    # death. So the return value might be a `Attack_Command_Attack_Hit`
    # object, a `Be_Attacked_by_Command_Attacked_and_Hit` object, and a
    # `Be_Attacked_by_Command_Character_Death` object, each bearing a message in
    # its `message` property. The frontend code will iterate through the tuple
    # printing each message in turn.

    valid_name_re = re.compile('^[A-Z][a-z]+$')

    pregame_commands = {'set_name', 'set_class', 'help', 'reroll', 'begin_game', 'quit'}

    ingame_commands = {'attack', 'cast_spell', 'close', 'help', 'drink', 'drop', 'equip', 'leave', 'inventory',
                       'look_at', 'lock', 'open', 'pick_lock', 'pick_up', 'quit', 'put', 'quit', 'status', 'take',
                       'unequip', 'unlock'}

    def __init__(self, game_state):
        """
Initialize the CommandProcessor before the beginning of the game.

:gamestate: A GameState object, which is composited of the game's
RoomsState, CreaturesState, ContainersState, DoorsState, and ItemsState
objects. Once the character_name and character_class attributes are set
on this object, a Character object will be added and the game can begin.
        """
        # This Game_State object contains & makes available Items_State,
        # Doors_State, Containers_State, Creatures_State, and Rooms_State
        # objects. It will later furnish a Character object when one can be
        # initialized. These comprise the game data that the player interacts
        # with during the game, and have already been initialized by the
        # frontend script before a Command_Processor object is instantiated.
        self.game_state = game_state

        # This attribute isn't used until the end of the game. Once the game
        # is over, self.game_state.game_has_ended is set to True, and any
        # further commands just get the Game_State_Message subclass object that
        # indicated end of game. It's saved in this attribute.
        self.game_ending_state_msg = None

        # This introspection associates each method whose name ends with
        # _command with a command whose text (with spaces replaced by
        # underscores) is the beginning of that name.
        self.dispatch_table = dict()
        commands_set = self.pregame_commands | self.ingame_commands
        for method_name in dir(type(self)):
            attrval = getattr(self, method_name, None)
            if not isinstance(attrval, types.MethodType):
                continue
            if not method_name.endswith('_command') or method_name.startswith('_'):
                continue
            command = method_name.rsplit('_', maxsplit=1)[0]
            self.dispatch_table[command] = attrval
            # This exception catches a programmer error if the pregame_commands
            # or ingame_commands wasn't updated with a new command.
            if command not in commands_set:
                raise excpt.Internal_Exception('Inconsistency between set list of commands and command methods found '
                                               f'by introspection: method {method_name}() does not correspond to a '
                                               'command in pregame_commands or ingame_commands.')
            commands_set.remove(command)
        # This exception catches a programmer error if a new command was added
        # to pregame_commands or ingame_commands but the corresponding method
        # hasn't been written or was misnamed.
        if len(commands_set):
            raise excpt.Internal_Exception('Inconsistency between set list of commands and command methods found by '
                                           f"introspection: command '{commands_set.pop()} does not correspond to a command "
                                           'in pregame_commands or ingame_commands.')

    def process(self, natural_language_str):
        """
Process and dispatch a natural language command string. The return value
is always a tuple even when it's length 1.

If the command is not recognized, returns a CommandNotRecognized object.

If a ingame command is used during the pregame (before name and class
have been set and ability scores have been rolled and accepted)
or a pregame command is used during the game proper, returns a
CommandNotAllowedNow object.

If this method is called after self.game_state.game_has_ended has been
set to True, the same object that was returned when the game ends is
returned again.

Otherwise, the command is processed and a state message object is
returned.

:natural_language_str: The player's command input as a natural language
string.
        """
        if self.game_state.game_has_ended:
            return (self.game_ending_state_msg,)
        tokens = natural_language_str.strip().split()
        command = tokens.pop(0).lower()

        # This block of conditionals is a set of preprocessing steps that handle
        # multi-token commands and commands which can be said different ways.
        if command == 'cast' and len(tokens) and tokens[0].lower() == 'spell':
            command += '_' + tokens.pop(0).lower()          # A two-word command.
        elif command == 'leave' and len(tokens) and tokens[0].lower() in ('using', 'via'):
            tokens.pop(0)                                   # 'via' or 'using' is dropped.
        elif command == 'begin':
            if len(tokens) >= 1 and tokens[0].lower() == 'game' or len(tokens) >= 2 and (tokens[0].lower(), tokens[1].lower()) == ('the', 'game'):
                if tokens[0].lower() == 'the':
                    tokens.pop(0)                           # 'begin the game' becomes 'begin game'.
                command += '_' + tokens.pop(0).lower()
            elif not len(tokens):
                command = 'begin_game'
        elif command == 'look' and len(tokens) and tokens[0].lower() == 'at':
            command += '_' + tokens.pop(0).lower()          # A two-word command.
        elif command == 'pick' and len(tokens) and (tokens[0].lower() == 'up' or tokens[0].lower() == 'lock'):
            command += '_' + tokens.pop(0).lower()          # Either 'pick lock' or 'pick up', a two-word command.
        elif command == 'quit':
            if len(tokens) >= 1 and tokens[0] == 'game' or len(tokens) >= 2 and tokens[0:2] == ['the', 'game']:
                if tokens[0] == 'the':
                    tokens.pop(0)                           # 'quit the game' or 'quit game' becomes 'quit'.
                tokens.pop(0)
        elif command == 'set' and len(tokens) and (tokens[0].lower() == 'name' or tokens[0].lower() == 'class'):
            command += '_' + tokens.pop(0).lower()
            if len(tokens) and tokens[0].lower() == 'to':   # 'set name to' becomes 'set name'.
                tokens.pop(0)                               # 'set class to' becomes 'set class'.
        elif command == 'show' and len(tokens) and tokens[0].lower() == 'inventory':
            command = tokens.pop(0).lower()                 # 'show inventory' becomes 'inventory'.
        if command not in ('set_name', 'set_class'):
            tokens = tuple(map(str.lower, tokens))          # 'set name' and 'set class' are case-sensitive;
                                                            #  the rest of the commands are not.

        # With the command normalized, I check for it in the dispatch table.
        # If it's not present, a Command_Not_Recognized error is returned. The
        # commands allowed in the current game mode are included.
        if command not in self.dispatch_table and not self.game_state.game_has_begun:
            return stmsg.Command_Not_Recognized(command, self.pregame_commands, self.game_state.game_has_begun),
        elif command not in self.dispatch_table and self.game_state.game_has_begun:
            return stmsg.Command_Not_Recognized(command, self.ingame_commands, self.game_state.game_has_begun),

        # If the player used an ingame command during the pregame, or a pregame
        # command during the ingame, a Command_Not_Allowed_Now error is returned
        # with a list of the currently allowed commands included.
        elif not self.game_state.game_has_begun and command not in self.pregame_commands:
            return stmsg.Command_Not_Allowed_Now(command, self.pregame_commands, self.game_state.game_has_begun),
        elif self.game_state.game_has_begun and command not in self.ingame_commands:
            return stmsg.Command_Not_Allowed_Now(command, self.ingame_commands, self.game_state.game_has_begun),

        # Having completed all the checks, I have a valid command and there is
        # a matching command method. The command method is tail called with the
        # remainder of the tokens as an argument.
        return self.dispatch_table[command](tokens)

    def attack_command(self, tokens):
        """
Execute the ATTACK command. The return value is always in a tuple even
when it's of length 1. The ATTACK command has the following usage:

ATTACK <creature name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If self.character has no weapon (or, for Mages, wand) equipped,
returns a AttackCommand_YouHaveNoWeaponOrWandEquipped object.

* If the creature name given doesn't match the title attribute of
the room object's creature_here attribute, or if that creature_here
attribute is None, returns a AttackCommand_OpponentNotFound object.

* If the attack misses, returns an AttackCommand_AttackMissed object
followed by the object(s) generated by the creature's followup attack.

* If the attack hits but doesn't kill the foe, returns an
AttackCommand_AttackHit object followed by the object(s) generated by the
creature's followup attack.

* If the attack hits and kills the foe, an AttackCommand_AttackHit object
and a VariousCommands_FoeDeath object are returned.
        """

        # If the player character has no weapon or wand equipped, an error is
        # returned right away.
        if (not self.game_state.character.weapon_equipped
                and (self.game_state.character_class != 'Mage' or not self.game_state.character.wand_equipped)):
            return stmsg.Attack_Command_You_Have_No_Weapon_or_Wand_Equipped(self.game_state.character_class),

        # Using this command with no argument is a syntax error.
        elif not tokens:
            return stmsg.Command_Bad_Syntax('ATTACK', COMMANDS_SYNTAX['ATTACK']),

        # This var is used by some return values.
        weapon_type = 'wand' if self.game_state.character.wand_equipped else 'weapon'
        creature_title = ' '.join(tokens)

        # If there's no creature in the current room, an error is returned.
        if not self.game_state.rooms_state.cursor.creature_here:
            return stmsg.Attack_Command_Opponent_Not_Found(creature_title),
        # If the arguments don't match the title of the creature in the current
        # room, an error is returned.
        elif self.game_state.rooms_state.cursor.creature_here.title.lower() != creature_title:
            return stmsg.Attack_Command_Opponent_Not_Found(creature_title,
                                                           self.game_state.rooms_state.cursor.creature_here.title),

        # All possible errors have been handles, so the actual attack is figured
        # on the creature here.
        creature = self.game_state.rooms_state.cursor.creature_here
        attack_roll_dice_expr = self.game_state.character.attack_roll
        damage_roll_dice_expr = self.game_state.character.damage_roll
        attack_result = util.roll_dice(attack_roll_dice_expr)

        # The attack doesn't meet or exceed the creature's armor class.
        if attack_result < creature.armor_class:

            # So a attack-missed return value is prepared.
            attack_missed_result = stmsg.Attack_Command_Attack_Missed(creature.title, weapon_type)

            # The _be_attacked_by_command() pseudo-command is triggered
            # by any attack command that doesn't kill the creature. Its
            # tuple of return values is appended to the attack-missed
            # return value and the combined tuple is returned.
            #
            # Please note that it's possible for self._be_attacked_by_command()
            # to end in Be_Attacked_by_Command_Character_Death; the game might
            # end right here.
            be_attacked_by_result = self._be_attacked_by_command(creature)
            return (attack_missed_result,) + be_attacked_by_result
        else:  # attack_result >= creature.armor_class
            # The attack roll met or exceeded the creature's armor class, so
            # damage is assessed and inflicted on the creature.
            damage_result = util.roll_dice(damage_roll_dice_expr)
            damage_result = creature.take_damage(damage_result)

            # If the creature was killed by that damage, the
            # Creature.convert_to_corpse() method is used to instantiate a
            # Corpse object from its data, that object is stored to the room's
            # container_here attribute, and its creature_here attribute is set
            # to None. Corpse is a Container, so the player can use TAKE to loot
            # the corpse.
            if creature.is_dead:
                corpse = creature.convert_to_corpse()
                self.game_state.rooms_state.cursor.container_here = corpse
                self.game_state.rooms_state.cursor.creature_here = None

                # The return tuple is comprised of an attack-hit value and a
                # foe-death value.
                return (stmsg.Attack_Command_Attack_Hit(creature.title, damage_result, True, weapon_type),
                        stmsg.Various_Commands_Foe_Death(creature.title))
            else:  # creature.is_alive == True
                # The attack hit but didn't kill, so the return tuple
                # begins with an attack-hit value. The creature lived, so
                # self._be_attacked_by_command() is called and its return tuple
                # is appended and the entire sequence is returned. Again, the
                # counterattack might kill the player character, so the game
                # might end right here.
                attack_hit_result = stmsg.Attack_Command_Attack_Hit(creature.title, damage_result, False, weapon_type)
                be_attacked_by_result = self._be_attacked_by_command(creature)
                return (attack_hit_result,) + be_attacked_by_result

    def _be_attacked_by_command(self, creature):
        # Called when a self.attack_command() execution included a
        # successful attack but didn't end in foe death. This is a
        # pseudo-command-method that can only be called internally. An
        # attack by the foe creature is calculated, if it hits damage
        # is assessed on the player character, and if character.is_dead
        # becomes True, the game ends.
        # 
        # :creature: The foe creature that was targeted by
        # self.attack_command().

        # The attack is calculated.
        attack_roll_dice_expr = creature.attack_roll
        damage_roll_dice_expr = creature.damage_roll
        attack_result = util.roll_dice(attack_roll_dice_expr)

        # If the attack roll didn't meet or exceed the player character's armor
        # class, an attacked-and-not-hit value is returned.
        if attack_result < self.game_state.character.armor_class:
            return stmsg.Be_Attacked_by_Command_Attacked_and_Not_Hit(creature.title),
        else:  # attack_result >= self.game_state.character.armor_class
            # The attack hit, so damage is rolled and inflicted.
            damage_done = util.roll_dice(damage_roll_dice_expr)
            self.game_state.character.take_damage(damage_done)
            if self.game_state.character.is_dead:
                # The attack killed the player character, so an attacked-and-hit
                # value and a character-death value are returned. Game over,
                # it's that easy. Combat comes with risk.
                return_tuple = (stmsg.Be_Attacked_by_Command_Attacked_and_Hit(creature.title, damage_done, 0),
                                stmsg.Be_Attacked_by_Command_Character_Death())

                # The game_has_ended boolean is set True, and the game-ending
                # return value is saved so that self.process() can return it if
                # the frontend accidentally tries to submit another command.
                self.game_state.game_has_ended = True
                self.game_ending_state_msg = return_tuple[-1]
                return return_tuple
            else:  # self.game_state.character.is_alive == True
                # The player character survived, so just an attacked-and-hit
                # value is returned.
                return (stmsg.Be_Attacked_by_Command_Attacked_and_Hit(creature.title, damage_done,
                                                                      self.game_state.character.hit_points),)

    def begin_game_command(self, tokens):
        """
Execute the BEGIN GAME command. The return value is always
in a tuple even when it's of length 1. Returns one or more
statemsgs.GameStateMessage subclass instances. Takes no arguments.

* If any arguments are given, returns a CommandBadSyntax object.

* If the command is used before the character's name and
class have been set with SET NAME and SET CLASS, returns a
BeginGameCommand_NameOrClassNotSet object.

* Otherwise, returns a BeginGameCommand_GameBegins object, one or more
VariousCommands_ItemEquipped objects, and a VariousCommands_EnteredRoom
object.
        """
        # This command begins the game. Most of the work done is devoted to
        # creating the character's starting gear and equipping all of it.

        # This command takes no argument; if any were used, a syntax error is
        # returned.
        if len(tokens):
            return stmsg.Command_Bad_Syntax('BEGIN GAME', COMMANDS_SYNTAX['BEGIN GAME']),

        # The game can't begin if the player hasn't used both SET NAME and SET
        # CLASS yet, so I check for that. If not, a name-or-class-not-set error
        # value is returned.
        character_name = getattr(self.game_state, 'character_name', None)
        character_class = getattr(self.game_state, 'character_class', None)
        if not character_name or not character_class:
            return stmsg.Begin_Game_Command_Name_or_Class_Not_Set(character_name, character_class),

        # The error checking is done, so Game_State.game_has_begun is set to
        # True, and a game-begins value is used to initialiZe the return_values
        # tuple.
        self.game_state.game_has_begun = True
        return_values = stmsg.Begin_Game_Command_Game_Begins(),

        # A player character receives starting equipment appropriate to their
        # class, as laid out in the STARTER_GEAR dict. The value there is a dict
        # of item types to item internal names. This loop looks up each internal
        # name in the Items_State object to get an Item subclass object.
        for item_type, item_internal_name in sorted(STARTER_GEAR[character_class].items(),  # This is sorted just to
                                                    key=operator.itemgetter(0)):            # make the results
                                                                                            # deterministic for ease
            item = self.game_state.items_state.get(item_internal_name)                      # of testing.
            self.game_state.character.pick_up_item(item)
            # Character.equip_{item_type} is looked up and called with the
            # Item subclass object to equip the character with this item of
            # equipment.
            getattr(self.game_state.character, 'equip_' + item_type)(item)

            # An appropriate item-equipped return value, complete with either
            # the updated armor_class value or the updated attack_bonus and
            # damage values, is appended to the return_values tuple.
            if item.item_type == 'armor':
                return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'armor',
                                                                armor_class=self.game_state.character.armor_class),)
            elif item.item_type == 'shield':
                return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'shield',
                                                                armor_class=self.game_state.character.armor_class),)
            elif item.item_type == 'wand':
                return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'wand',
                                                                attack_bonus=self.game_state.character.attack_bonus,
                                                                damage=self.game_state.character.damage_roll),)
            else:
                return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'weapon',
                                                                attack_bonus=self.game_state.character.attack_bonus,
                                                                damage=self.game_state.character.damage_roll),)

        # Lastly, an entered-room return value is appended to the return_values
        # tuple, so a description of the first room will print.
        return_values += (stmsg.Various_Commands_Entered_Room(self.game_state.rooms_state.cursor),)

        # From the player's perspective, the frontend printing out this entire
        # sequence of return values can look like:
        #
        # The game has begun!
        # You're now wearing a suit of studded leather armor. Your armor class
        # is now 11.
        # You're now carrying a buckler. Your armor class is now 12.
        # You're now wielding a mace. Your attack bonus is now +1 and your
        # weapon damage is now 1d6+1.
        # Antechamber of dungeon. There is a doorway to the north.

        return return_values

    def cast_spell_command(self, tokens):
        """
Execute the CAST SPELL command. The return value is always in a tuple
even when it's of length 1. Takes no arguments.

* If any arguments are given, returns a CommandBadSyntax object.

* If the character is a Warrior or a Thief, returns a
CommandClassRestricted object.

* This command costs mana points. If the character doesn't have enough,
returns a CastSpellCommand_InsufficientMana object.

* If the character is a Mage and there's no creature in the room,
returns a CastSpellCommand_NoCreatureToTarget object.

* If they're a Mage and there is a creature present, a damaging spell
is cast and the creature is wounded. If they don't die, returns a
CastSpellCommand_CastDamagingSpell object followed by the object(s)
generated by the creature's followup attack.

* If the creature is killed, returns a CastSpellCommand_CastDamagingSpell
object and a VariousCommands_FoeDeath object.

* If the character is a Priest, returns a
CastSpellCommand_CastHealingSpell object and a
VariousCommands_UnderwentHealingEffect object.
"""

        # The first error check detects if the player has used this command
        # while playing a Warrior or Thief. Those classes can't cast spells, so
        # a command-class-restricted error is returned.
        if self.game_state.character_class not in ('Mage', 'Priest'):
            return stmsg.Command_Class_Restricted('CAST SPELL', 'mage', 'priest'),

        # This command takes no arguments, so if any were used a syntax error is
        # returned.
        elif len(tokens):
            return stmsg.Command_Bad_Syntax('CAST SPELL', COMMANDS_SYNTAX['CAST SPELL']),

        # If the player character's mana is less than SPELL_MANA_COST, an
        # insufficient-mana error is returned.
        elif self.game_state.character.mana_points < SPELL_MANA_COST:
            return stmsg.Cast_Spell_Command_Insufficient_Mana(self.game_state.character.mana_points,
                                                            self.game_state.character.mana_point_total,
                                                            SPELL_MANA_COST),

        # The initial error handling is concluded, so now the execution handles
        # the Mage and Priest cases separately.
        elif self.game_state.character_class == 'Mage':

            # If the current room has no creature in it, a no-creature-to-target
            # error is returned.
            if self.game_state.rooms_state.cursor.creature_here is None:
                return stmsg.Cast_Spell_Command_No_Creature_to_Target(),
            else:
                # Otherwise, spell damage is rolled and inflicted on
                # creature_here. The spell always hits (it's styled after _magic
                # missile_, a classic D&D spell that always hits its target.
                damage_dealt = util.roll_dice(SPELL_DAMAGE)
                creature = self.game_state.rooms_state.cursor.creature_here
                damage_dealt = creature.take_damage(damage_dealt)
                self.game_state.character.spend_mana(SPELL_MANA_COST)

                # If the creature died, a cast-damaging-spell value and a
                # foe-death value are returned.
                if creature.is_dead:
                    corpse = creature.convert_to_corpse()
                    self.game_state.rooms_state.cursor.container_here = corpse
                    self.game_state.rooms_state.cursor.creature_here = None
                    return (stmsg.Cast_Spell_Command_Cast_Damaging_Spell(creature.title, damage_dealt,
                                                                         creature_slain=True),
                            stmsg.Various_Commands_Foe_Death(creature.title))
                else:
                    # Otherwise, like ATTACK, using this command and
                    # not killing your foe means they counterattack.
                    # cast-damaging-spell is conjoined with the outcome of
                    # self._be_attacked_by_command() and the total tuple is
                    # returned.
                    be_attacked_by_result = self._be_attacked_by_command(creature)
                    return operator.concat((stmsg.Cast_Spell_Command_Cast_Damaging_Spell(creature.title,
                                                                                           damage_dealt,
                                                                                           creature_slain=False),),
                                           be_attacked_by_result)
        else:
            # The Mage's spell is a damaging spell, but the Priest's spell is
            # a self-heal. The same SPELL_DAMAGE dice are used. The healing is
            # rolled and applied to the Character object. A cast-healing-spell
            # value and a underwent-healing-effect value are returned.
            damage_rolled = util.roll_dice(SPELL_DAMAGE)
            healed_amt = self.game_state.character.heal_damage(damage_rolled)
            self.game_state.character.spend_mana(SPELL_MANA_COST)
            return (stmsg.Cast_Spell_Command_Cast_Healing_Spell(),
                    stmsg.Various_Commands_Underwent_Healing_Effect(healed_amt, self.game_state.character.hit_points,
                                                                    self.game_state.character.hit_point_total))

    def _matching_door(self, target_door):
        # Fetches the corresponding door object in the room linked to by
        # a door object, so an operation can be performed on both door
        # objects representing the two sides of the same door element.
        # Returns None if the door being tested is the exit door of the
        # dungeon.
        #
        # :target_door: A door object. return: A door object, or None.

        # There's a limitation in the implementations of close_command(),
        # lock_command(), open_command(), pick_lock_command(), and
        # unlock_command(): when targetting a door, the door object that's
        # retrieved to unlock is the one that represents that exit from the
        # current room object; but the other room linked by that door uses a
        # different door object to represent the opposite side of the same
        # notional door game element. In order to operate on the same door in
        # two rooms, both door objects must have their state changed.

        # This dict is used to match opposing door attributes so that the
        # opposite door can be retrieved from the opposite room.
        opposite_compass_door_attrs = {'north_door': 'south_door', 'east_door': 'west_door',
                                       'south_door': 'north_door', 'west_door': 'east_door'}

        # First I iterate across the four possible doors in the current room
        # object to find which door_attr attribute name the door object is
        # stored under.
        door_found_at_attr = None
        for door_attr in ('north_door', 'south_door', 'east_door', 'west_door'):
            found_door = getattr(self.game_state.rooms_state.cursor, door_attr, None)
            if found_door is target_door:
                door_found_at_attr = door_attr
                break

        # I use the handy method Door.other_room_internal_name(), which returns
        # the internal_name of the linked room when given the internal_name of
        # the room the player is in.
        other_room_internal_name = target_door.other_room_internal_name(
                                       self.game_state.rooms_state.cursor.internal_name)

        # If the door is the exit to the dungeon, it will have 'Exit' as its
        # other_room_internal_name. There is no far room or far door object, so
        # I return None.
        if other_room_internal_name == 'Exit':
            return None

        # Otherwise, I fetch the opposite room, and use the opposite_door_attr
        # to fetch the other door object that represents the other side of the
        # game element door from the door object that I've got, and return it.
        opposite_room = self.game_state.rooms_state.get(other_room_internal_name)
        opposite_door_attr = opposite_compass_door_attrs[door_found_at_attr]
        opposite_door = getattr(opposite_room, opposite_door_attr)
        return opposite_door

    def close_command(self, tokens):
        """
Execute the CLOSE command. The return value is always in a tuple even
when it's of length 1. The CLOSE command has the following usage:

CLOSE <door name>
CLOSE <chest name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If there is no matching chest or door in the room, returns a
CloseCommand_ElementToCloseNotHere object.

* If there is no matching door, returns a
VariousCommands_DoorNotPresent object.

* If more than one door in the room matches, returns a
VariousCommands_AmbiguousDoorSpecifier object.

* If the door or chest specified is already closed, returns a
CloseCommand_ElementIsAlreadyClosed object.

* Otherwise, returns a CloseCommand_ElementHasBeenClosed object.
        """

        # The self.open_command(), self.close_command(),
        # self.lock_command(), and self.unlock_command() share the
        # majority of their logic in a private workhorse method,
        # self._preprocessing_for_lock_unlock_open_or_close().
        result = self._preprocessing_for_lock_unlock_open_or_close('CLOSE', tokens)

        # As with any workhorse method, it either returns an error value or the
        # object to operate on. So I type test if the result tuple's 1st element
        # is a Game_State_Message subclass object. If so, it's returned.
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            # Otherwise I extract the element to close.
            element_to_close, = result

        # If the element to close is already closed, a
        if element_to_close.is_closed:
            return stmsg.Close_Command_Element_Is_Already_Closed(element_to_close.title),
        elif isinstance(element_to_close, elem.Door):
            # This is a door object, and it only represents _this side_ of the
            # door game element; I use _matching_door() to fetch the door object
            # representing the opposite side so that the door game element will
            # be closed from the perspective of either room.
            opposite_door = self._matching_door(element_to_close)
            if opposite_door is not None:
                opposite_door.is_closed = True

        # I set the element's is_closed attribute to True, and return an
        # element-has-been-closed value.
        element_to_close.is_closed = True
        return stmsg.Close_Command_Element_Has_Been_Closed(element_to_close.title),

    def drink_command(self, tokens):
        """
Execute the DRINK command. The return value is always in a tuple even
when it's of length 1. The DRINK command has the following usage:

DRINK [THE] <potion name>
DRINK <number> <potion name>[s]

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the potion specified is not in the character's inventory, returns a
DrinkCommand_ItemNotInInventory object.

* If the name matches an undrinkable item, or a door, chest, creature,
or corpse, returns a DrinkCommand_ItemNotDrinkable object.

* If the <number> argument is used, and there's not that many of the
potion, returns a DrinkCommand_TriedToDrinkMoreThanPossessed
object.

* Otherwise, if it's a health potion, then that potion is
removed from inventory, the character is healed, and returns a
VariousCommands_UnderwentHealingEffect object.

* If it's a mana potion, and the character is a Warrior
or a Thief, the potion is removed from inventory, and returns a
DrinkCommand_DrankManaPotionWhenNotASpellcaster object.

* If it's a mana potion, and the character is a Mage or a Preist, then
the potion is removed from inventory, the character has some mana
restored, and a DrinkCommand_DrankManaPotion object is returned.
        """
        # This command requires an argument, which may include a direct or
        # indirect article. If that standard isn't met, a syntax error is
        # returned.
        if not len(tokens) or len(tokens) == 1 and tokens[0] in ('the', 'a', 'an'):
            return stmsg.Command_Bad_Syntax('DRINK', COMMANDS_SYNTAX['DRINK']),

        # Any leading article is stripped, but it signals that the quantity to
        # drink is 1, so qty_to_drink is set.
        if tokens[0] == 'the' or tokens[0] == 'a':
            qty_to_drink = 1
            tokens = tokens[1:]

        # Otherwise, I check if the first token is a digital or lexical integer.
        elif tokens[0].isdigit() or util.lexical_number_in_1_99_re.match(tokens[0]):
            # If the first token parses as an int, I cast it and
            # set qty_to_drink. Otherwise, the utility function
            # adventuregame.utilities.lexical_number_to_digits() is used to
            # transform a number word to an int.
            qty_to_drink = int(tokens[0]) if tokens[0].isdigit() else util.lexical_number_to_digits(tokens[0])
            if (qty_to_drink > 1 and not tokens[-1].endswith('s')) or (qty_to_drink == 1 and tokens[-1].endswith('s')):
                return stmsg.Command_Bad_Syntax('DRINK', COMMANDS_SYNTAX['DRINK']),

            # The first token is dropped off the tokens tuple.
            tokens = tokens[1:]
        else:

            # No quantifier was detected at the front of the tokens. That
            # implies qty_to_drink = 1; but if the last token has a plural 's',
            # the arguments are ambiguous as to quantity. So a quantity-unclear
            # error is returned.
            qty_to_drink = 1
            if tokens[-1].endswith('s'):
                return stmsg.Drink_Command_Quantity_Unclear(),

        # The initial error checking is out of the way, so we check the
        # Character's inventory for an item with a title that matches the
        # arguments.
        item_title = ' '.join(tokens).rstrip('s')
        matching_items_qtys_objs = tuple(filter(lambda argl: argl[1].title == item_title,
                                                self.game_state.character.list_items()))

        # The character has no such item, so an item-not-in-inventory error is returned.
        if not len(matching_items_qtys_objs):
            return stmsg.Drink_Command_Item_Not_in_Inventory(item_title),

        # An item by the title that the player specified was found, so the
        # object and its quantity are saved.
        item_qty, item = matching_items_qtys_objs[0]

        # If the item isn't a potion, an item-not-drinkable error is returned.
        if not item.title.endswith(' potion'):
            return stmsg.Drink_Command_Item_Not_Drinkable(item_title),

        # If the arguments specify a quantity to drink that's greater than the
        # quantity in inventory, a tried-to-drink-more-than-possessed error is
        # returned.
        elif qty_to_drink > item_qty:
            return stmsg.Drink_Command_Tried_to_Drink_More_than_Possessed(item_title, qty_to_drink, item_qty),

        # I execute the effect of a health potion or a mana potion, depending.
        # Mana potion first.
        elif item.title == 'health potion':

            # The amount of healing done by the potion is healed on the
            # character, and the potion is removed from inventory. A
            # underwent-healing-effect value is returned.
            hit_points_recovered = item.hit_points_recovered
            healed_amt = self.game_state.character.heal_damage(hit_points_recovered)
            self.game_state.character.drop_item(item)
            return stmsg.Various_Commands_Underwent_Healing_Effect(healed_amt, self.game_state.character.hit_points,
                                                                   self.game_state.character.hit_point_total),
        else:   # item.title == 'mana potion':
            # If the player character isn't a Mage or a Priest, a mana potion
            # does nothing; a drank-mana-potion-when-not-a-spellcaster error is
            # returned.
            if self.game_state.character_class not in ('Mage', 'Priest'):
                return stmsg.Drink_Command_Drank_Mana_Potion_when_Not_A_Spellcaster(),

            # The amount of mana recovery done by the potion is granted to the
            # character, and the potion is removed from inventory. A
            # drank-mana-potion value is returned.
            mana_points_recovered = item.mana_points_recovered
            regained_amt = self.game_state.character.regain_mana(mana_points_recovered)
            self.game_state.character.drop_item(item)
            return stmsg.Drink_Command_Drank_Mana_Potion(regained_amt, self.game_state.character.mana_points,
                                                         self.game_state.character.mana_point_total),

    def drop_command(self, tokens):
        """
Execute the DROP command. The return value is always in a tuple even
when it's of length 1. The DROP command has the following usage:

DROP <item name>
DROP <number> <item name>

* If the item specified isn't in inventory, returns a
DropCommand_TryingToDropItemYouDontHave object.

* If a number is specified, and that's more than how many of the item
are in inventory, returns a
DropCommand_TryingToDropMorethanYouHave object.

* If no number is used and the item is equipped, returns a
VariousCommands_ItemUnequipped object and a DropCommand_DroppedItem
object.

* Otherwise, the item is removed, or the specified number of the item
are removed, from inventory and a DropCommand_DroppedItem object is
returned.
        """
        # self.pick_up_command() and self.drop_command() share a lot of logic in
        # a private workhorse method self._pick_up_or_drop_preproc(). As with
        # all private workhorse methods, the return value is a tuple and might
        # consist of an error value; so the 1st element is type tested to see if
        # its a Game_State_Message subclass object.
        result = self._pick_up_or_drop_preproc('DROP', tokens)
        if len(result) == 1 and isinstance(result[0], stmsg.Game_State_Message):

            # The workhorse method returned an error, so I pass that along.
            return result
        else:

            # The workhorse method succeeded, I extract the item to drop and the
            # quantity from its return tuple.
            drop_quantity, item_title = result

        # The quantity of the item on the floor is reported by some
        # drop_command() return values, so I check the contents of items_here.
        if self.game_state.rooms_state.cursor.items_here is not None:
            items_here = tuple(self.game_state.rooms_state.cursor.items_here.values())
        else:
            items_here = ()

        # items_here's contents are filtered looking for an item by a matching
        # title. If one is found, the quantity already in the room is saved to
        # quantity_already_here.
        item_here_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_here))
        quantity_already_here = item_here_pair[0][0] if len(item_here_pair) else 0

        # In the same way, the Character's inventory is listed and filtered
        # looking for an item by a matching title.
        items_had_pair = tuple(filter(lambda pair: pair[1].title == item_title, self.game_state.character.list_items()))

        # The player character's inventory doesn't contain an item by that
        # title, so a trying-to-drop-an-item-you-don't-have error is returned.
        if not len(items_had_pair):
            return stmsg.Drop_Command_Trying_to_Drop_Item_You_Dont_Have(item_title, drop_quantity),

        # The item was found, so its object and quantity are saved.
        (item_had_qty, item), = items_had_pair

        if drop_quantity > item_had_qty:

            # If the quantity specified to drop is greater than the quantity in
            # inventory, a trying-to-drop-more-than-you-have error is returned.
            return stmsg.Drop_Command_Trying_to_Drop_More_than_You_Have(item_title, drop_quantity, item_had_qty),
        elif drop_quantity is math.nan:

            # The workhorse method returns math.nan as the drop_quantity if the
            # arguments didn't specify a quantity. I now know how many the
            # player character has, so I assume they mean to drop all of them. I
            # set drop_quantity to item_had_qty.
            drop_quantity = item_had_qty

        # If the player drops an item they had equipped, and they have
        # none left, it is unequipped. The return tuple is started with
        # unequip_return, which may be empty at the end of this conditional.
        unequip_return = ()
        if drop_quantity - item_had_qty == 0:

            # This only runs if the player character will have none left after
            # this drop. All four equipment types are separately checked to see
            # if they're the item being dropped. The unequip return value needs
            # to specify which game stats have been changed by the unequipping,
            # so this conditional is involved.
            armor_equipped = self.game_state.character.armor_equipped
            weapon_equipped = self.game_state.character.weapon_equipped
            shield_equipped = self.game_state.character.shield_equipped
            wand_equipped = self.game_state.character.wand_equipped

            # If the character's armor is being dropped, it's unequipped and a
            # item-unequipped error value is generated, noting the decreased
            # armor class.
            if (item.item_type == 'armor' and armor_equipped is not None
                    and armor_equipped.internal_name == item.internal_name):
                self.game_state.character.unequip_armor()
                unequip_return = stmsg.Various_Commands_Item_Unequipped(item.title, item.item_type,
                                     armor_class=self.game_state.character.armor_class),
            # If the character's shield is being dropped, it's unequipped and
            # a item-unequipped error value is generated, noting the decreased
            # armor class.
            elif (item.item_type == 'shield' and shield_equipped is not None
                      and shield_equipped.internal_name == item.internal_name):
                self.game_state.character.unequip_shield()
                unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'shield',
                                     armor_class=self.game_state.character.armor_class),

            # If the character's weapon is being dropped, it's unequipped,
            # and an item-unequipped error value is generated.
            elif (item.item_type == 'weapon' and weapon_equipped is not None
                      and weapon_equipped.internal_name == item.internal_name):
                self.game_state.character.unequip_weapon()
                if wand_equipped:
                    # If the player character is a mage and has a wand equipped,
                    # the wand's attack values are included since they will
                    # use the wand to attack. (An equipped wand always takes
                    # precedence over a weapon for a Mage.)
                    unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon',
                                         attack_bonus=self.game_state.character.attack_bonus,
                                         damage=self.game_state.character.damage_roll,
                                         attacking_with=wand_equipped),
                else:
                    # Otherwise, the player will be informed that they now can't
                    # attack.
                    unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon', now_cant_attack=True),

            # If the character's wand is being dropped, it's unequipped,
            # and an item-unequipped error value is generated.
            elif (item.item_type == 'wand' and wand_equipped is not None
                    and wand_equipped.internal_name == item.internal_name):
                self.game_state.character.unequip_wand()
                if weapon_equipped:
                    # If the player has a weapon equipped, the weapon's attack
                    # values are included since they will fall back on it.
                    unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'wand',
                                         attack_bonus=self.game_state.character.attack_bonus,
                                         damage=self.game_state.character.damage_roll,
                                         now_attacking_with=weapon_equipped),
                else:
                    # Otherwise, the player will be informed that they now can't
                    # attack.
                    unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'wand', now_cant_attack=True),

        # Finally, with all other preconditions handled, I actually drop the item.
        self.game_state.character.drop_item(item, qty=drop_quantity)

        # If there wasn't a Items_Multi_State set to items_here, I
        # instantiate one.
        if self.game_state.rooms_state.cursor.items_here is None:
            self.game_state.rooms_state.cursor.items_here = elem.ItemsMultiState()

        # The item is saved to items_here with the combined quantity of what was
        # already there (can be 0) and the quantity dropped.
        self.game_state.rooms_state.cursor.items_here.set(item.internal_name,
                                                          quantity_already_here + drop_quantity, item)

        # I calculate the quantity left in the character's inventory, and return
        # a dropped-item value with the quantity dropped, the quantity on the
        # floor, and the quantity remaining in inventory.
        quantity_had_now = item_had_qty - drop_quantity
        return unequip_return + (stmsg.Drop_Command_Dropped_Item(
                                     item_title, item.item_type, drop_quantity, quantity_already_here + drop_quantity,
                                     quantity_had_now),)

    def equip_command(self, tokens):
        """
Execute the EQUIP command. The return value is always in a tuple even
when it's of length 1. The EQUIP command has the following usage:

EQUIP <armor name>
EQUIP <shield name>
EQUIP <wand name>
EQUIP <weapon name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the item isn't in inventory, returns a
EquipCommand_NoSuchItemInInventory object.

* If the item can't be used by the character due to their class, returns
a EquipCommand_ClassCantUseItem object.

* If an item of the same kind is already equipped (for example
trying to equip a suit of armor when the character is already
wearing armor), that item is unequipped, the specified item is
equipped, and a VariousCommands_ItemUnequipped object and a
VariousCommands_ItemEquipped object are returned.

* Otherwise, the item is equipped, and a VariousCommands_ItemEquipped
object is returned.

        """
        # The equip command requires an argument; if none was given, a syntax
        # error is returned.
        if not tokens or len(tokens) == 1 and tokens[0] == 'the':
            return stmsg.Command_Bad_Syntax('EQUIP', COMMANDS_SYNTAX['EQUIP']),
        if tokens[0] == 'the':
            tokens = tokens[1:]

        # The title of the item to equip is formed from the arguments.
        item_title = ' '.join(tokens)

        # The inventory is filtered looking for an item with a matching title.
        matching_item_tuple = tuple(item for _, item in self.game_state.character.list_items()
                                             if item.title == item_title)

        # If no such item is found in the inventory, a no-such-item-in-inventory
        # error is returned.
        if not len(matching_item_tuple):
            return stmsg.Equip_Command_No_Such_Item_in_Inventory(item_title),

        # The Item subclass object was found and is saved.
        item, = matching_item_tuple[0:1]

        # I check that the item has a {class}_can_use = True attribute. If not,
        # a class-can't-use-item error is returned.
        can_use_attr = self.game_state.character_class.lower() + '_can_use'
        if not getattr(item, can_use_attr):
            return stmsg.Equip_Command_Class_Cant_Use_Item(self.game_state.character_class, item_title, item.item_type),

        # This conditional handles checking, for each type of equippable
        # item, whether the player character already has an item of that type
        # equipped; if so, it's unequipped, and a item-unequipped return value
        # is appended to the return values tuple.
        return_values = tuple()
        if item.item_type == 'armor' and self.game_state.character.armor_equipped:
            # The player is trying to equip armor but is already wearing armor,
            # so their existing armor is unequipped.
            old_equipped = self.game_state.character.armor_equipped
            self.game_state.character.unequip_armor()
            return_values += stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                                    armor_class=self.game_state.character.armor_class),
        elif item.item_type == 'shield' and self.game_state.character.shield_equipped:
            # The player is trying to equip shield but is already carrying a
            # shield, so their existing shield is unequipped.
            old_equipped = self.game_state.character.shield_equipped
            self.game_state.character.unequip_shield()
            return_values += stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                                    armor_class=self.game_state.character.armor_class),
        elif item.item_type == 'wand' and self.game_state.character.wand_equipped:
            # The player is trying to equip wand but is already using a wand, so
            # their existing wand is unequipped.
            old_equipped = self.game_state.character.wand_equipped
            self.game_state.character.unequip_wand()
            if self.game_state.character.weapon_equipped:
                return_values += stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                           attacking_with=self.game_state.character.weapon_equipped,
                                           attack_bonus=self.game_state.character.attack_bonus,
                                           damage=self.game_state.character.damage_roll),
            else:
                return_values += stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                                        now_cant_attack=True),
        elif item.item_type == 'weapon' and self.game_state.character.weapon_equipped:
            # The player is trying to equip weapon but is already wielding a
            # weapon, so their existing weapon is unequipped.
            old_equipped = self.game_state.character.weapon_equipped
            self.game_state.character.unequip_weapon()
            if self.game_state.character.wand_equipped:
                return_values += stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                           attacking_with=self.game_state.character.wand_equipped,
                                           attack_bonus=self.game_state.character.attack_bonus,
                                           damage=self.game_state.character.damage_roll),
            else:
                return_values += stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                                        now_cant_attack=True),

        # Now it's time to equip the new item; a item-equipped return value is
        # appended to return_values.
        if item.item_type == 'armor':
            # The player is equipping a suit of armor, so the
            # Character.equip_armor() method is called with the item object.
            self.game_state.character.equip_armor(item)
            return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'armor',
                                                                   armor_class=self.game_state.character.armor_class),)
        elif item.item_type == 'shield':
            # The player is equipping a shield, so the Character.equip_shield()
            # method is called with the item object.
            self.game_state.character.equip_shield(item)
            return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'shield',
                                  armor_class=self.game_state.character.armor_class),)
        elif item.item_type == 'wand':
            # The player is equipping a wand, so the Character.equip_wand()
            # method is called with the item object.
            self.game_state.character.equip_wand(item)
            return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'wand',
                                      attack_bonus=self.game_state.character.attack_bonus,
                                      damage=self.game_state.character.damage_roll),)
        else:
            # The player is equipping a weapon, so the Character.equip_weapon()
            # method is called with the item object.
            self.game_state.character.equip_weapon(item)

            # Because a wand equipped always supercedes any weapon equipped for
            # a Mage, the item-equipped return value is different if a wand is
            # equipped, so this extra conditional is necessary.
            if self.game_state.character.wand_equipped:
                return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'weapon',
                                      attack_bonus=self.game_state.character.attack_bonus,
                                      damage=self.game_state.character.damage_roll,
                                      attacking_with=self.game_state.character.wand_equipped),)
            else:
                return_values += (stmsg.Various_Commands_Item_Equipped(item.title, 'weapon',
                                      attack_bonus=self.game_state.character.attack_bonus,
                                      damage=self.game_state.character.damage_roll),)

        # The optional item-unequipped value and the item-equipped value are
        # returned.
        return return_values

    def help_command(self, tokens):
        """
Execute the HELP command. The return value is always in a tuple even
when it's of length 1. The HELP command has the following usage:

HELP
HELP <command name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the command is used with no arguments, returns a
HelpCommand_DisplayCommands object.

* If the argument is not a recognized command, returns a
HelpCommand_CommandNotRecognized object.

* Otherwise, returns a HelpCommand_DisplayHelpForCommand object.

        """
        # An ordered tuple of all commands in uppercase is displayed in some
        # return values so it is computed.

        # If called with no arguments, the help command displays a generic help
        # message listing all available commands.
        if len(tokens) == 0:
            commands_set = self.ingame_commands if self.game_state.game_has_begun else self.pregame_commands
            commands_tuple = tuple(sorted(map(lambda strval: strval.replace('_', ' ').upper(), commands_set)))
            return stmsg.Help_Command_Display_Commands(commands_tuple, self.game_state.game_has_begun),

        # A specific command was included as an argument.
        else:
            command_uc = ' '.join(tokens).upper()
            command_lc = '_'.join(tokens).lower()

            # If the command doesn't occur in commands_tuple, a
            # command-not-recognized error is returned.
            if command_lc not in (self.ingame_commands | self.pregame_commands):
                commands_tuple = tuple(sorted(map(lambda strval: strval.replace('_', ' ').upper(),
                                                  self.ingame_commands | self.pregame_commands)))
                return stmsg.Help_Command_Command_Not_Recognized(command_uc, commands_tuple),
            else:
                # Otherwise, a help message for the command specified is
                # returned.
                return stmsg.Help_Command_Display_Help_for_Command(command_uc, COMMANDS_SYNTAX[command_uc],
                                                                   COMMANDS_HELP[command_uc]),

    def inventory_command(self, tokens):
        """
Execute the INVENTORY command. The return value is always in a tuple
even when it's of length 1. The INVENTORY command takes no arguments.

* If the command is used with any arguments, returns a
CommandBadSyntax object.

* Otherwise, returns a InventoryCommand_DisplayInventory object.

        """
        # This command takes no arguments; if any are specified, a syntax error is returned.
        if len(tokens):
            return stmsg.Command_Bad_Syntax('INVENTORY', COMMANDS_SYNTAX['INVENTORY']),

        # There's not really any other error case, for once. The inventory
        # contents are stored in a tuple, and a display-inventory value is
        # returned with the tuple to display.
        inventory_contents = sorted(self.game_state.character.list_items(), key=lambda argl: argl[1].title)
        return stmsg.Inventory_Command_Display_Inventory(inventory_contents),

    def leave_command(self, tokens):
        """
Execute the LEAVE command. The return value is always in a tuple even
when it's of length 1. The LEAVE command has the following usage:

LEAVE [USING or VIA] <compass direction> DOOR
LEAVE [USING or VIA] <compass direction> DOORWAY
LEAVE [USING or VIA] <door name>
LEAVE [USING or VIA] <compass direction> <door name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the door by that name is not present in the room, returns a
VariousCommands_DoorNotPresent object.

* If the door specifier is ambiguous and matches more than one door
in the room, returns a VariousCommands_AmbiguousDoorSpecifier object.

* If the door is the exit to the dungeon, returns a LeaveCommand_LeftRoom
object and a LeaveCommand_WonTheGame object.

* Otherwise, a LeaveCommand_LeftRoom object and a
VariousCommands_EnteredRoom object are returned.
        """
        # This method takes arguments of a specific form; if the arguments don't
        # match it, a syntax error is returned.
        if (not len(tokens) or not 2 <= len(tokens) <= 4 or tokens[-1] not in ('door', 'doorway')):
            return stmsg.Command_Bad_Syntax('LEAVE', COMMANDS_SYNTAX['LEAVE']),

        # The format for specifying doors is flexible, and is implemented by a
        # private workhorse method.
        result = self._door_selector(tokens)

        # Like all workhorse methods, it may return an error. result[0] is
        # type-tested if it inherits from Game_State_Message. If it matches, the
        # result tuple is returned.
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            # Otherwise, the matching Door object is extracted from result.
            door, = result

        # The compass direction door type are extracted from the Door object.
        compass_dir = door.title.split(' ')[0]
        portal_type = door.door_type.split('_')[-1]

        # If the door is locked, a door-is-locked error is returned.
        if door.is_locked:
            return stmsg.Leave_Command_Door_Is_Locked(compass_dir, portal_type),

        # The exit to the dungeon is a special Door object marked with
        # is_exit=True. I test the Door object to see if this is the one.
        if door.is_exit:

            # If so, a left-room value will be returned along with a won-the-game value.
            return_tuple = (stmsg.Leave_Command_Left_Room(compass_dir, portal_type), stmsg.Leave_Command_Won_The_Game())

            # The game_has_ended boolean is set True, and the game-ending
            # return value is saved so that self.process() can return it if the
            # frontend accidentally tries to submit another command.
            self.game_state.game_has_ended = True
            self.game_ending_state_msg = return_tuple[-1]
            return return_tuple

        # Otherwise, Rooms_State.move is called with the compass direction, and
        # a left-room value is returned along with a entered-room value.
        self.game_state.rooms_state.move(**{compass_dir: True})
        return (stmsg.Leave_Command_Left_Room(compass_dir, portal_type),
                stmsg.Various_Commands_Entered_Room(self.game_state.rooms_state.cursor))

    def lock_command(self, tokens):
        """
Execute the LOCK command. The return value is always in a tuple even
when it's of length 1. The LOCK command has the following usage:

LOCK <door name>
LOCK <chest name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If no such door is present in the room, returns a
VariousCommands_DoorNotPresent object.

* If the command is ambiguous and matches more than one door in the
room, a VariousCommands_AmbiguousDoorSpecifier object is returned.

* If the object to lock is not present, returns a
LockCommand_ElementToLockNotHere object.

* If the object to lock is already locked, returns a LockCommand_ElementIsAlreadyLocked object.

* If the object to lock is not present, a LockCommand_ElementNotLockable is returned.

* If the character does not possess the requisite door or
chest key to lock the specified door or chest, returns a
LockCommand_DontPossessCorrectKey object.

* Otherwise, the object has its is_locked attribute set to True, If the
LockCommand_ElementHasBeenLocked
        """
        # This command requires an argument, so if tokens is zero-length a
        # syntax error is returned.
        if not len(tokens):
            return stmsg.Command_Bad_Syntax('LOCK', COMMANDS_SYNTAX['LOCK']),

        # A private workhorse method is used for logic shared with
        # self.unlock_command(), self.open_command(), self.close_command().
        result = self._preprocessing_for_lock_unlock_open_or_close('LOCK', tokens)

        # As always with a workhorse method, the result is checked to see if
        # it's an error value. If so, the result tuple is returned as-is.
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            # Otherwise, the element to lock is extracted from the return value.
            element_to_lock, = result

        # Locking something requires the matching key in inventory. The key's
        # item title is determined, and the player character's inventory is
        # searched for a matching Key object. The object isn't used for anything
        # (it's not expended), so I don't save it, just check if it's there.
        key_required = 'door key' if isinstance(element_to_lock, elem.Door) else 'chest key'
        if not any(item.title == key_required for _, item in self.game_state.character.list_items()):
            # Lacking the key, a don't-possess-correct-key error is returned.
            return stmsg.Lock_Command_Dont_Possess_Correct_Key(element_to_lock.title, key_required),

        # If the element_to_lock is already locked, a element-is-already-locked
        # error is returned.
        elif element_to_lock.is_locked:
            return stmsg.Lock_Command_Element_Is_Already_Locked(element_to_lock.title),
        elif isinstance(element_to_lock, elem.Door):
            # This is a door object, and it only represents _this side_ of the
            # door game element; I use _matching_door() to fetch the door object
            # representing the opposite side so that the door game element will
            # be locked from the perspective of either room.
            opposite_door = self._matching_door(element_to_lock)
            if opposite_door is not None:
                opposite_door.is_locked = True

        # The element_to_lock's is_locked attribute is set to rue, and a
        # Telement-has-been-locked value is returned.
        element_to_lock.is_locked = True
        return stmsg.Lock_Command_Element_Has_Been_Locked(element_to_lock.title),

    # This private workhorse method handles the shared logic between lock,
    # unlock, open or close: 

    def _preprocessing_for_lock_unlock_open_or_close(self, command, tokens):

        # This private workhorse method handles the shared logic
        # for lock_command(), unlock_command(), open_command() and
        # close_command(). All four commands have the same type of game
        # elements as their targets, and a player specifying such an
        # element has the same failure modes.
        #
        # :command: The command that the calling method was executing.
        # One of LOCK, UNLOCK, OPEN, or CLOSE.
        # :tokens: The arguments that the calling method was called
        # with. Must be non-null.
        #
        # * If the calling command received a zero-length tokens
        # argument, a syntax error is returned. The COMMANDS_SYNTAX used
        # for the error uses the command argument iso t matches the
        # calling method's context
        #
        # * If the specified game element is not present in the
        # current room, one of UnlockCommand_ElementToUnlockNotHere,
        # LockCommand_ElementToLockNotHere,
        # OpenCommand_ElementtoOpenNotHere, or
        # CloseCommand_ElementToCloseNotHere is returned, depending on
        # the command argument
        #
        # * If the specified game element is a corpse, creature,
        # doorway or item, it's an invalid element for any of the
        # calling methods; one of LockCommand_ElementNotLockable,
        # UnlockCommand_ElementNotUnlockable,
        # OpenCommand_ElementNotOpenable, or
        # CloseCommand_ElementNotClosable is returned, depending on the
        # command argument.

        # If the command was used with no arguments, a syntax error is returned.
        if not len(tokens):
            return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),

        # door is initialized to None so whether it's non-None later can be a
        # signal.
        door = None

        # These booleans are initialized to False; later if any one of them is
        # true, an error value will be returned.
        tried_to_operate_on_doorway = tried_to_operate_on_creature = tried_to_operate_on_corpse = \
            tried_to_operate_on_item = False

        # If the arguments indicate a door(way), a further private workhorse
        # method self._door_selector() is used to implement the flexible door
        # specifier syntax. As always with a private workhorse method, result[0]
        # is type-tested to see if it's a error value. If so, the result tuple
        # is returned.
        if tokens[-1] in ('door', 'doorway'):
            result = self._door_selector(tokens)
            if isinstance(result[0], stmsg.Game_State_Message):
                return result
            else:
                # Otherwise, the Door object is extracted. But it may be a
                # doorway, that's tested later.
                door, = result

        # The target title is formed, and container_here & creature_here are
        # assigned to local variables as they're referenced frequently.
        target_title = ' '.join(tokens) if door is None else door.title
        container = self.game_state.rooms_state.cursor.container_here
        creature = self.game_state.rooms_state.cursor.creature_here

        if door is not None:
            # If the Door object is a Doorway, that failure mode boolean is set.
            if door.door_type == 'doorway':
                tried_to_operate_on_doorway = True
            else:
                # Otherwise, it's a valid target for the calling method, and
                # it's returned.
                return door,
        elif creature is not None and creature.title == target_title:
            # If the target matches the title for the creature in this room,
            # that failure mode boolean is set.
            tried_to_operate_on_creature = True
        elif container is not None and container.title == target_title:
            # If the target matches the title for a container here...
            if isinstance(container, elem.Corpse):
                # If the container is a corpse, that failure mode boolean is set.
                tried_to_operate_on_corpse = True
            else:
                # Otherwise, it's a valid target for the calling method, and
                # it's returned.
                return container,

        # If I reach this point, the method is in a failure mode. If a door or
        # chest matched it would already have been returned. If the other three
        # failure modes don't obtain, the fourth-- an item-- is checked for.
        if (not any((tried_to_operate_on_doorway, tried_to_operate_on_corpse, tried_to_operate_on_corpse))
                and self.game_state.rooms_state.cursor.items_here is not None):
            # The room's items_here State object and the Character's inventory
            # are both searched through looking for an item whose title matches
            # the target.
            for _, item in itertools.chain(self.game_state.rooms_state.cursor.items_here.values(),
                                           self.game_state.character.list_items()):
                if item.title != target_title:
                    continue
                # If a match is found, that failure mode boolean is set and the
                # loop is broken.
                tried_to_operate_on_item = True
                item_targetted = item
                break

        # If any of the four failure modes occurred, then the player specified
        # an existing element that is not openable/closable/lockable/unlockable.
        # An appropriate argd is constructed and an appropriate error value is
        # returned identifying the mistargeted element.
        if any((tried_to_operate_on_doorway, tried_to_operate_on_corpse, tried_to_operate_on_item,
                tried_to_operate_on_creature)):
            argd = {'target_type': 'doorway' if tried_to_operate_on_doorway
                                   else 'corpse' if tried_to_operate_on_corpse
                                   else 'creature' if tried_to_operate_on_creature
                                   else item_targetted.__class__.__name__.lower()}
            if command.lower() == 'unlock':
                return stmsg.Unlock_Command_Element_Not_Unlockable(target_title, **argd),
            elif command.lower() == 'lock':
                return stmsg.Lock_Command_Element_Not_Lockable(target_title, **argd),
            elif command.lower() == 'open':
                return stmsg.Open_Command_Element_Not_Openable(target_title, **argd),
            else:
                return stmsg.Close_Command_Element_Not_Closable(target_title, **argd),
        else:
            # Otherwise, the target didn't match *any* game element within
            # the player's reach, so the appropriate error value is returned
            # indicating the target isn't present.
            if command.lower() == 'unlock':
                return stmsg.Unlock_Command_Element_to_Unlock_Not_Here(target_title),
            elif command.lower() == 'lock':
                return stmsg.Lock_Command_Element_to_Lock_Not_Here(target_title),
            elif command.lower() == 'open':
                return stmsg.Open_Command_Element_to_Open_Not_Here(target_title),
            else:
                return stmsg.Close_Command_Element_to_Close_Not_Here(target_title),

    def _door_selector(self, tokens):

        # This is a private workhorse method implementing a flexible
        # door specifier syntax. The methods close_command(),
        # leave_command(), lock_command(), look_at_command(),
        # open_command(), pick_lock_command(), pick_up_command(),
        # unlock_command() all use _door_selector() to apply that
        # syntax. A door can be specified using any combination of its
        # compass direction, title, or portal type.
        #
        # :tokens: The arguments token tuple pased to the calling
        # method.
        #
        # * If the door specifier doesn't match any door in the room, a
        # VariousCommands_DoorNotPresent object is returned
        #
        # * If the door specifier matches more than one door in the
        # room, a VariousCommands_AmbiguousDoorSpecifier object is
        # returned.

        # These variables are initialized to None so they can be checked for
        # non-None values later.
        compass_dir = door_title = door_type = None

        # If the first token is a compass direction, compass_dir is set to it.
        # This method is always called from a context where the last token has
        # tested equal to 'door' or 'doorway', so I rely on that and compose the
        # door title that the door will be found under in Rooms_State.
        if tokens[0] in ('north', 'east', 'south', 'west'):
            compass_dir = tokens[0]
            door_title = f'{compass_dir} {tokens[-1]}'
            tokens = tokens[1:]

        # If the first token matches 'iron' or 'wooden' and the last token is
        # 'door' (not 'doorway'), I can match the door_type. I construct the
        # door_type value.
        if ((len(tokens) == 2 and tokens[0] in ('iron', 'wooden') and tokens[1] == 'door')
                or len(tokens) == 1 and tokens[0] == 'doorway'):
            door_type = ' '.join(tokens).replace(' ', '_')

        # The tuple of doors in the current room is assigned to a local
        # variable, and I iterate across it trying to match compass_dir,
        # door_type, or both. As a fallback, 'door' vs. 'doorway' in the title
        # is tested. Matches are saved to matching_doors.
        doors = self.game_state.rooms_state.cursor.doors
        matching_doors = list()
        for door in doors:
            if compass_dir is not None and door_type is not None:
                if not (door.title.startswith(compass_dir) and door.door_type == door_type):
                    continue
            elif compass_dir is not None:
                if not door.title.startswith(compass_dir):
                    continue
            elif door_type is not None:
                if door.door_type != door_type:
                    continue
            else:
                if not door.title.endswith(tokens[-1]):
                    continue
            matching_doors.append(door)

        # If no doors matched, a door-not-present error is returned.
        if len(matching_doors) == 0:
            return stmsg.Various_Commands_Door_Not_Present(compass_dir, tokens[-1]),
        elif len(matching_doors) > 1:
            # Otherwise if more than one door matches, a
            # ambiguous-door-specifier error is returned. If possible, it's
            # constructed with a door_type value to give a more useful error
            # message.
            compass_dirs = tuple(door.title.split(' ')[0] for door in matching_doors)
            # Checks that all door_types are the same.
            door_type = (matching_doors[0].door_type if len(set(door.door_type
                             for door in matching_doors)) == 1 else None)
            return stmsg.Various_Commands_Ambiguous_Door_Specifier(compass_dirs, tokens[-1], door_type),
        else:
            # Otherwise matching_doors is length 1; I have a match, so I return
            # it.
            return matching_doors

    look_at_door_re = re.compile(r"""(
                                         (north|east|south|west) \s  # For example, this regex matches
                                     |                               # 'north iron door', 'north door', 'iron door',
                                         (iron|wooden) \s            # and 'door'. But it won't match 'iron doorway'.
                                     |
                                         (
                                             (north|east|south|west) \s (iron|wooden) \s
                                         )
                                     )?
                                     (door|doorway)
                                     (?<! iron \s doorway)           # Lookbehinds must be fixed-width so I use 2.
                                     (?<! wooden \s doorway)
                                     """, re.X)

    def look_at_command(self, tokens):
        """
Execute the LOOK AT command. The return value is always in a tuple even
when it's of length 1. The LOOK AT command has the following usage:

LOOK AT <item name>
LOOK AT <item name> IN <chest name>
LOOK AT <item name> IN INVENTORY
LOOK AT <item name> ON <corpse name>
LOOK AT <compass direction> DOOR
LOOK AT <compass direction> DOORWAY

* If that syntax is not followed, returns a CommandBadSyntax object.

* If looking at a door which is not present in the room, returns a
VariousCommands_DoorNotPresent object.

* If looking at a door, but the arguments are ambiguous
and match more than one door in the room, returns a
VariousCommands_AmbiguousDoorSpecifier object.

* If looking at a chest or corpse which is not present in the room,
returns a VariousCommands_ContainerNotFound object.

* If looking at an item which isn't present (per the arguments)
on the floor, in a chest, on a corpse, or in inventory, a
LookAtCommand_FoundNothing object is returned.

* If looking at a chest or corpse which is present, returns a
LookAtCommand_FoundCreatureHere object.

* If looking at a creature which is present, returns a
LookAtCommand_FoundCreatureHere object.

* If looking at a door or doorway which is present, returns a
LookAtCommand_FoundDoorOrDoorway object.

* If looking at an item which is present, a
LookAtCommand_FoundItemOrItemsHere object is returned.
        """
        # The LOOK AT command can target an item in a chest or on a corpse, so
        # the presence of either 'in' or 'on' in the tokens tuple indicates
        # that case. The tokens tuple is checked for a consistent container
        # specifier; if it's poorly-constructed, an error value is returned.
        if (not tokens or tokens[0] in ('in', 'on') or tokens[-1] in ('in', 'on')
                or ('in' in tokens and tokens[-1] == 'corpse')
                or ('on' in tokens and tokens[-1] == 'chest')):
            return stmsg.Command_Bad_Syntax('LOOK AT', COMMANDS_SYNTAX['LOOK AT']),

        # This conditional is more easily accomplished with a regex than a multi-line boolean chain.
        # `look_at_door_re` is defined above.
        elif tokens[-1] in ('door', 'doorway') and not self.look_at_door_re.match(' '.join(tokens)):
            return stmsg.Command_Bad_Syntax('LOOK AT', COMMANDS_SYNTAX['LOOK AT']),

        # These four booleans are initialized to False so they can be tested for
        # True values later.
        item_contained = item_in_inventory = item_in_chest = item_on_corpse = False

        # If 'in' or 'on' is used, the tokens can be divided at the point it
        # occurs into a left-hand value which is the title of an item, and a
        # right-hand value which is the title of a container or is 'inventory'.
        if 'in' in tokens or 'on' in tokens:
            if 'in' in tokens:
                # This signal value will control an upcoming conditional tree.
                item_contained = True
                joinword_index = tokens.index('in')
                # As will one of these two.
                if tokens[joinword_index+1:] == ('inventory',):
                    item_in_inventory = True
                else:
                    item_in_chest = True
            else:
                joinword_index = tokens.index('on')
                if tokens[-1] != 'floor':
                    # These signal values will control an upcoming conditional.
                    item_contained = True
                    item_on_corpse = True

            # joinword_index has been set, so target_title and location_title
            # are derived from the tokens before that index, and the tokens
            # after, respectively.
            target_title = ' '.join(tokens[:joinword_index])
            location_title = ' '.join(tokens[joinword_index+1:])

        # If the tokens contain neither 'in' or 'on, and the last token is 'door' or 'dooray', _door_selector is used.
        elif tokens[-1] == 'door' or tokens[-1] == 'doorway':
            result = self._door_selector(tokens)
            if isinstance(result, tuple) and isinstance(result[0], stmsg.Game_State_Message):
                # If it returns an error, that's passed along.
                return result
            else:
                # Otherwise the door it returns is the target, and a
                # found-door-or-doorway value is returned with that door object
                # informing the message.
                door, = result
                return stmsg.Look_At_Command_Found_Door_or_Doorway(door.title.split(' ')[0], door),
        else:
            # The tokens don't indicate a door and don't have a location_title
            # to break off the end. The target_title is formed from the tokens.
            target_title = ' '.join(tokens)

        # creature_here and container_here are assigned to local variables.
        creature_here = self.game_state.rooms_state.cursor.creature_here
        container_here = self.game_state.rooms_state.cursor.container_here

        # If earlier reasoning concluded the item is meant to be found in a
        # chest, but the container here is None or a corpse, a syntax error is
        # returned.
        if (item_in_chest and isinstance(container_here, elem.Corpse)
                or item_on_corpse and isinstance(container_here, elem.Chest)):
            return stmsg.Command_Bad_Syntax('look at', COMMANDS_SYNTAX['LOOK AT']),

        # If the target_title matches the creature in this room, a
        # found-creature-here value is returned.
        if creature_here is not None and creature_here.title == target_title.lower():
            return stmsg.Look_At_Command_Found_Creature_Here(creature_here.description),

        # If the container here is not None and matches, a found-container-here
        # value is returned.
        elif container_here is not None and container_here.title == target_title.lower():
            return stmsg.Look_At_Command_Found_Container_Here(container_here),

        # Otherwise, if the command specified an item that is contained in
        # something (including the inventory), so I test all the valid states.
        elif item_contained:

            # If the item is supposed to be in the character's inventory, I
            # iterate through the inventory looking for a matching title.
            if item_in_inventory:
                for item_qty, item in self.game_state.character.list_items():
                    if item.title != target_title:
                        continue
                    # If found, a found-item-here value is returned.
                    # _look_at_item_detail() is used to supply a detailed
                    # accounting of the item.
                    return stmsg.Look_At_Command_Found_Item_or_Items_Here(self._look_at_item_detail(item),
                                                                          item_qty, 'inventory'),
                # Otherwise, a found-nothing value is returned.
                return stmsg.Look_At_Command_Found_Nothing(target_title, 'inventory'),
            else:
                # Otherwise, the item is in a chest or on a corpse. Either one
                # would need to be the value for container_here, so I test its
                # title against the location_title.
                if container_here is None or container_here.title != location_title:

                    # If it doesn't match, a container-not-found error is
                    # returned.
                    return stmsg.Various_Commands_Container_Not_Found(location_title),

                # Otherwise, if the container is non-None and its title matches,
                # I iterate through the container's contents looking for a
                # matching item title.
                elif container_here is not None and container_here.title == location_title:
                    for item_qty, item in container_here.values():
                        if item.title != target_title:
                            continue
                        # If I find a match, I return a found-item-here value.
                        # _look_at_item_detail() is used to supply a detailed
                        # accounting of the item.
                        return stmsg.Look_At_Command_Found_Item_or_Items_Here(self._look_at_item_detail(item),
                                                                              item_qty, container_here.title,
                                                                              container_here.container_type),
                    # Otherwise, I return a found-nothing value.
                    return stmsg.Look_At_Command_Found_Nothing(target_title, location_title,
                                                               'chest' if item_in_chest else 'corpse'),
                else:
                    # The container wasn't found, so I return a
                    # container-not-found error.
                    return stmsg.Various_Commands_Container_Not_Found(location_title),
        else:

            # The target isn't a creature, or a container, or in a container, or
            # in the character's inventory, so I check the floor. Again I
            # iterate through items looking for a match.
            for item_name, (item_qty, item) in self.game_state.rooms_state.cursor.items_here.items():
                if item.title != target_title:
                    continue
                # If I find a match, I return a found-item-here value.
                # _look_at_item_detail() is used to supply a detailed accounting
                # of the item.
                return stmsg.Look_At_Command_Found_Item_or_Items_Here(self._look_at_item_detail(item),
                                                                      item_qty, 'floor'),
            # Otherwise, a found-nothing value is returned.
            return stmsg.Look_At_Command_Found_Nothing(target_title, 'floor'),

    def _look_at_item_detail(self, element):

        # This private utility method handles the task of constructing
        # a detailed description of an item, mentioning everything
        # about it that the game data can show. It doesn't return any
        # Game_State_Message subclass objects; it's a utility method
        # that accomplishes a task that look_command() needs to execute
        # in 3 different places in its code, so it's refactored into its
        # own method.
        #
        # :element: The Item subclass object to derive a detailed
        # description of.

        descr_append_str = ''
        # If the item is equipment, its utility as an equippable item will be
        # detailed.
        if isinstance(element, elem.EquippableItem):
            if isinstance(element, (elem.Wand, elem.Weapon)):
                # If the item can be attacked with, its attack bonus and damage
                # are mentioned.
                descr_append_str = (f' Its attack bonus is +{element.attack_bonus} and its damage is '
                                    f'{element.damage}. ')
            else:  # isinstance(element, (elem.Armor, elem.Shield))
                # It's a defensive item, so its armor bonus is mentioned.
                descr_append_str = f' Its armor bonus is +{element.armor_bonus}. '
            can_use_list = []
            # All Equippable items have *_can_use attributes expresing class
            # limitations, so I survey those.
            for character_class in ('warrior', 'thief', 'mage', 'priest'):
                if getattr(element, f'{character_class}_can_use', False):
                    can_use_list.append(f'{character_class}s' if character_class != 'thief' else 'thieves')
            # The first class name is titlecased because it's the start of a
            # sentence, and the list of classes is formed into a sentence
            # appended to the working string.
            can_use_list[0] = can_use_list[0].title()
            descr_append_str += util.join_str_seq_w_commas_and_conjunction(can_use_list, 'and')
            descr_append_str += ' can use this.'
        elif isinstance(element, elem.Potion):
            # If it's a potion, the points recovered are mentioned.
            if element.title == 'mana potion':
                descr_append_str = f' It restores {element.mana_points_recovered} mana points.'
            elif element.title == 'health potion':
                descr_append_str = f' It restores {element.hit_points_recovered} hit points.'
        elif isinstance(element, elem.Door):
            # If it's a door, whether it's open or closed is mentioned.
            if element.closable:
                descr_append_str = ' It is closed.' if element.is_closed else ' It is open.'

        # The base element description is returned along with the extended
        # description derived above.
        return element.description + descr_append_str

    def open_command(self, tokens):
        """
Execute the OPEN command. The return value is always in a tuple even
when it's of length 1. The OPEN command has the following usage:

OPEN <door name>
OPEN <chest name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If trying to open a door which is not present in the room, returns a
VariousCommands_DoorNotPresent object.

* If trying to open a door, but the command is ambiguous and matches
more than one door, returns a VariousCommands_AmbiguousDoorSpecifier
object.

* If trying to open an item, creature, corpse or doorway, returns a
OpenCommand_ElementNotOpenable object.

* If trying to open a chest that is not present in the room, returns a OpenCommand_ElementtoOpenNotHere object.

* If trying to open a door or chest that is locked, returns a OpenCommand_ElementIsLocked object.

* If trying to open a door or chest that is already open, returns a OpenCommand_ElementIsAlreadyOpen object.

* Otherwise, the chest or door has its is_closed attribute set to False,
and returns returns a OpenCommand_ElementHasBeenOpened..

        """
        # The shared private workhorse method is called and it handles the
        # majority of the error-checking. If it returns an error that is passed
        # along.
        result = self._preprocessing_for_lock_unlock_open_or_close('OPEN', tokens)
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            # Otherwise the element to open is extracted from the return tuple.
            element_to_open, = result

        # If the element is locked, a element-is-locked error is returned.
        if element_to_open.is_locked:
            return stmsg.Open_Command_Element_Is_Locked(element_to_open.title),
        elif not element_to_open.is_closed:
            # Otherwise if it's alreadty open, an element-is-already-open error
            # is returned.
            return stmsg.Open_Command_Element_Is_Already_Open(element_to_open.title),
        elif isinstance(element_to_open, elem.Door):
            # This is a door object, and it only represents _this side_ of the
            # door game element; I use _matching_door() to fetch the door object
            # representing the opposite side so that the door game element will
            # be open from the perspective of either room.
            opposite_door = self._matching_door(element_to_open)
            if opposite_door is not None:
                opposite_door.is_closed = False

        # The element has is_closed set to False and an element-has-been-opened
        # value is returned.
        element_to_open.is_closed = False
        return stmsg.Open_Command_Element_Has_Been_Opened(element_to_open.title),

    def pick_lock_command(self, tokens):
        """
Execute the PICK LOCK command. The return value is always in a tuple even when it's of length 1.

This method implements the PICK LOCK command. (The command is only usable
if the player is playing a Thief.) It accepts a tokens tuple that is
the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The PICK LOCK
command has the following usage:

PICK LOCK ON [THE] <chest name>
PICK LOCK ON [THE] <door name>

* If that syntax is not followed, returns a CommandBadSyntax object. 

* If the player tries to use this command while playing a Warrior, Mage or
Priest, returns a CommandClassRestricted object.

* If the arguments specify a door, and that door is not present in the current room, returns a VariousCommands_DoorNotPresent object.

* If the arguments specify a door, and more than one door matches that specification, returns a VariousCommands_AmbiguousDoorSpecifier object.

* If the arguments specify a doorway, creature, item, or corpse, returns a PickLockCommand_ElementNotUnlockable object.

* If the arguments specify a chest that is not present in the current room, returns a PickLockCommand_TargetNotFound object.

* If the arguments specify a door or chest is that is already unlocked, returns a PickLockCommand_TargetNotLocked object.

* Otherwise, the specified door or chest has its is_locked attribute set to False, and a PickLockCommand_TargetHasBeenUnlocked object is returned.
        """
        # These error booleans are initialized to False so they can be checked
        # for True values later.
        tried_to_operate_on_doorway = tried_to_operate_on_creature = tried_to_operate_on_corpse = \
            tried_to_operate_on_item = False

        # This command is restricted to Thieves; if the player character is of
        # another class, a command-class-restricted error is returned.
        if self.game_state.character_class != 'Thief':
            return stmsg.Command_Class_Restricted('PICK LOCK', 'thief'),

        # This command requires an argument. If called with no argument or a
        # patently invalid one, a syntax error is returned.
        if not len(tokens) or tokens[0] != 'on' or tokens == ('on',) or tokens == ('on', 'the',):
            return stmsg.Command_Bad_Syntax('PICK LOCK', COMMANDS_SYNTAX['PICK LOCK']),
        elif tokens[:2] == ('on', 'the'):
            tokens = tokens[2:]
        elif tokens[0] == 'on':
            tokens = tokens[1:]

        # I form the target_title from the tokens.
        target_title = ' '.join(tokens)

        # container_here and creature_here are assigned to local variables.
        container = self.game_state.rooms_state.cursor.container_here
        creature = self.game_state.rooms_state.cursor.creature_here

        # If the target is a door or doorway. the _door_selector() is used.
        if tokens[-1] in ('door', 'doorway'):
            result = self._door_selector(tokens)
            # If it returns an error, the error value is returned.
            if isinstance(result[0], stmsg.Game_State_Message):
                return result
            else:
                # Otherwise, the Door object is extracted from its return value.
                door, = result

            # If the Door is a doorway, it can't be unlocked; a failure mode boolean is assigned.
            if isinstance(door, elem.Doorway):
                tried_to_operate_on_doorway = True
            elif not door.is_locked:
                # Otherwise if the door isn't locked, a target-not-locked error value is returned.
                return stmsg.Pick_Lock_Command_Target_Not_Locked(target_title),
            else:
                # This is a door object, and it only represents _this side_ of
                # the door game element; I use _matching_door() to fetch the
                # door object representing the opposite side so that the door
                # game element will be unlocked from the perspective of either
                # room.
                opposite_door = self._matching_door(door)
                if opposite_door is not None:
                    opposite_door.is_locked = False

                # The door's is_locked attribute is set to False, and a
                # target-has-been-unlocked value is returned.
                door.is_locked = False
                return stmsg.Pick_Lock_Command_Target_Has_Been_Unlocked(target_title),
        # The target isn't a door. If there is a container here and its title matches....
        elif container is not None and container.title == target_title:
            # If it's a Corpse, the failure mode boolean is set.
            if isinstance(container, elem.Corpse):
                tried_to_operate_on_corpse = True
            elif not getattr(container, 'is_locked', False):
                # Otherwise if it's not locked, a target-not-locked error value is returned.
                return stmsg.Pick_Lock_Command_Target_Not_Locked(target_title),
            else:
                # Otherwise, its is_locked attribute is set to False, and a
                # target-has-been-unlocked error is returned.
                container.is_locked = False
                return stmsg.Pick_Lock_Command_Target_Has_Been_Unlocked(target_title),

        # The Door and Chest case have been handled and any possible success
        # value has been rejected. Everything from here on down is error
        # handling.
        elif creature is not None and creature.title == target_title:
            # If there's a creature here and its title matches target_title,
            # that failure mode boolean is set.
            tried_to_operate_on_creature = True
        else:
            # I check through items_here (if any) and the player character's
            # inventory looking for an item with a title matching target_title.
            for _, item in itertools.chain((self.game_state.rooms_state.cursor.items_here.values()
                                            if self.game_state.rooms_state.cursor.items_here is not None
                                            else ()),
                                           self.game_state.character.list_items()):
                if item.title != target_title:
                    continue
                # If one is found, the appropriate failure mode boolean is set,
                # and the loop is broken.
                tried_to_operate_on_item = True
                item_targetted = item
                break

        # If any of the failure mode booleans were set, the appropriate argd is
        # constructed, and a element-not-unlockable error value is instanced
        # with it and returned.
        if any((tried_to_operate_on_doorway, tried_to_operate_on_corpse, tried_to_operate_on_item,
                tried_to_operate_on_creature)):
            argd = {'target_type': 'doorway' if tried_to_operate_on_doorway
                                   else 'corpse' if tried_to_operate_on_corpse
                                   else 'creature' if tried_to_operate_on_creature
                                   else item_targetted.__class__.__name__.lower()}
            return stmsg.Pick_Lock_Command_Element_Not_Unlockable(target_title, **argd),
        else:
            # The target_title didn't match anything in the current room, so a
            # target-not-found error value is returned.
            return stmsg.Pick_Lock_Command_Target_Not_Found(target_title),

    def pick_up_command(self, tokens):
        """
Execute the PICK UP command. The return value is always in a tuple even when it's of length 1.

This method implements the PICK UP command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The PICK UP command
has the following usage:

PICK UP <item name>
PICK UP <number> <item name>),

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the arguments are ungrammatical and are unclear about the quantity to pick up, returns a PickUpCommand_QuantityUnclear object.

* If the arguments specify a chest, corpse, creature or door, returns a PickUpCommand_CantPickUpChestCorpseCreatureOrDoor object.

* If the arguments specify an item to pick up that is not present in self.game_state.rooms_state.cursor.items_here, returns a PickUpCommand_ItemNotFound object.

* If the arguments specify a quantity to pick up that is greater than the quantity present in self.game_state.rooms_state.cursor.items_here, returns a PickUpCommand_TryingToPickUpMoreThanIsPresent object.

* Otherwise, the specified quantity of the matching item is deducted from self.game_state.rooms_state.cursor.items_here, and added to self.game_state.character, and a PickUpCommand_ItemPickedUp object is returned.
        """
        # The door var is set to None so later it can be checked for a non-None value.
        door = None
        pick_up_quantity = 0

        # If the contents of tokens is a door specifier, _door_selector() is used.
        if tokens[-1] in ('door', 'doorway'):
            result = self._door_selector(tokens)
            # If an error value was returned, it's returned.
            if isinstance(result[0], stmsg.Game_State_Message):
                return result
            else:
                # Otherwise the Door object is extracted from the result tuple.
                # Doors can't be picked up but we at least want to match
                # exactly.
                door, = result
                target_title = door.title
        else:
            # Otherwise, a private workhorse method is used to parse the arguments.
            result = self._pick_up_or_drop_preproc('PICK UP', tokens)
            if isinstance(result[0], stmsg.Game_State_Message):
                return result
            else:
                pick_up_quantity, target_title = result

        # unpickupable_item_type is initialized to None so it can be tested for
        # a non-None value later. If it acquires another value, an error value
        # will be returned.
        unpickupable_element_type = None
        if door is not None:

            # The arguments specified a door, so unpickupable_item_type is set to 'door'.
            unpickupable_element_type = 'door'

        # Otherwise, if the current room has a creature_here and its title
        # matches, unpickupable_item_type is set to 'creature'.
        elif (self.game_state.rooms_state.cursor.creature_here is not None
                  and self.game_state.rooms_state.cursor.creature_here.title == target_title):
            unpickupable_element_type = 'creature'

        # Otherwise, if the current room has a container_here and its title
        # matches, unpickupable_item_type is set to its container_type.
        elif (self.game_state.rooms_state.cursor.container_here is not None and
                self.game_state.rooms_state.cursor.container_here.title == target_title):
            unpickupable_element_type = self.game_state.rooms_state.cursor.container_here.container_type

        # If unpickupable_element_type acquired a value, a cant-pick-up-element
        # error is returned.
        if unpickupable_element_type:
            return stmsg.Pick_Up_Command_Cant_Pick_Up_Chest_Corpse_Creature_or_Door(unpickupable_element_type,
                                                                                    target_title),

        # If this room has no items_here Items_Multi_State object, nothing can
        # be picked up, and a item-not-found error is returned.
        if self.game_state.rooms_state.cursor.items_here is None:
            return stmsg.Pick_Up_Command_Item_Not_Found(target_title, pick_up_quantity),

        # The items_here.values() sequence is cast to tuple and assigned to a
        # local variable, and the character's inventory is also so assigned. I
        # iterate through both of them looking for items with titles matching
        # target_title.
        items_here = tuple(self.game_state.rooms_state.cursor.items_here.values())
        items_had = tuple(self.game_state.character.list_items())
        item_here_pair = tuple(filter(lambda pair: pair[1].title == target_title, items_here))
        items_had_pair = tuple(filter(lambda pair: pair[1].title == target_title, items_had))

        # If no item was found in items_here matching target_title, a tuple
        # of items that *are* here is formed, and a item-not-found error is
        # instanced with it as an argument and returned.
        if not len(item_here_pair):
            items_here_qtys_titles = tuple((item_qty, item.title) for item_qty, item in items_here)
            return stmsg.Pick_Up_Command_Item_Not_Found(target_title, pick_up_quantity, *items_here_qtys_titles),

        # Otherwise, the item was found here, so its quantity and the Item
        # subclass object are extracted and saved.
        (quantity_here, item), = item_here_pair

        # _pick_up_or_drop_preproc() returns math.nan if it couldn't determine a
        # quantity. If it did, I assume the player meant all of the item that's
        # here, and set pick_up_quantity to quantity_here.
        if pick_up_quantity is math.nan:
            pick_up_quantity = quantity_here

        # quantity_in_inventory is needed for the item-picked-up return value
        # constructor. If the item title had a match in the inventory, the
        # quantity there is assigned to quantity_in_inventory, otherwise it's
        # set to 0.
        quantity_in_inventory = items_had_pair[0][0] if len(items_had_pair) else 0

        # If the quantity to pick up specified in the command is greater than
        # the quantity in items_here, a trying-to-pick-up-more-than-is-present
        # error is returned.
        if quantity_here < pick_up_quantity:
            return stmsg.Pick_Up_Command_Trying_to_Pick_Up_More_than_Is_Present(target_title, pick_up_quantity,
                                                                                quantity_here),
        else:
            # Otherwise, that quantity of the item is added to the player
            # character's inventory.
            self.game_state.character.pick_up_item(item, qty=pick_up_quantity)

            # If the entire quantity of the item in items_here was picked up,
            # it's deleted from items_here.
            if quantity_here == pick_up_quantity:
                self.game_state.rooms_state.cursor.items_here.delete(item.internal_name)
            else:
                # Otherwise its new quantity is set in items_here.
                self.game_state.rooms_state.cursor.items_here.set(item.internal_name,
                                                                  quantity_here - pick_up_quantity, item)
            # The quantity now possessed is computed, and used to construct a
            # item-picked-up return value, which is returned.
            quantity_had_now = quantity_in_inventory + pick_up_quantity
            return stmsg.Pick_Up_Command_Item_Picked_Up(target_title, pick_up_quantity, quantity_had_now),

    # Both PUT and TAKE have the same preprocessing challenges, so I refactored
    # their logic into a shared private preprocessing method.

    def _pick_up_or_drop_preproc(self, command, tokens):
        """
This private workhorse method handles argument processing logic which is common
to pick_up_command() and drop_command(). It detects the quantity intended and
screens for ambiguous command arguments.

:command: The command the calling method is executing.
:tokens:  The tokenized command arguments.

* If invalid arguments are sent, returns a CommandBadSyntax object.

* If the player submitted an ungrammatical sentence which is ambiguous as to the quantity intended, a DropCommand_QuantityUnclear object or a PickUpCommand_QuantityUnclear object is returned depending on the value in command.
        """
        # This long boolean checks whether the first token in tokens can
        # indicate quantity.
        if tokens[0] in ('a', 'an', 'the') or tokens[0].isdigit() or util.lexical_number_in_1_99_re.match(tokens[0]):
            # If the quantity indicator is all there is, a syntax error is
            # returned.
            if len(tokens) == 1:
                return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),
            # The item title is formed from the rest of the tokens.
            item_title = ' '.join(tokens[1:])

            # If the first token is an indirect article...
            if tokens[0] == 'a' or tokens[0] == 'an':
                if tokens[-1].endswith('s'):
                    # but the end of the last token has a pluralizing 's' on
                    # it, I return a quantity-unclear error appropriate to the
                    # caller.
                    return ((stmsg.Drop_Command_Quantity_Unclear(),) if command.lower() == 'drop'
                            else (stmsg.Pick_Up_Command_Quantity_Unclear(),))
                # Otherwise it implies a quantity of 1.
                item_quantity = 1
            elif tokens[0].isdigit():

                # Otherwise if it parses as an int, I save that quantity.
                item_quantity = int(tokens[0])

            # If it's a direct article...
            elif tokens[0] == 'the':

                # And the last token ends with a pluralizing 's', the player
                # means to pick up or drop the total quantity possible. I don't
                # know what that is now, so I set the item_quantity to math.nan
                # as a signal value. When the caller gets as far as identifying
                # the total quantity possible, it will replace this value with
                # that one.
                if tokens[-1].endswith('s'):
                    item_quantity = math.nan
                else:
                    # Otherwise it implies a quantity of 1.
                    item_quantity = 1
            else:
                # Based on the enclosing conditional, this else implies
                # util.lexical_number_in_1_99_re.match(tokens[0]) == True. So I
                # use util.lexical_number_to_digits to parse the 1st token to an
                # int.
                item_quantity = util.lexical_number_to_digits(tokens[0])

                # lexical_number_to_digits also uses math.nan as a signal value;
                # it returns that value if the lexical number was outside the
                # range of one to ninety-nine. If so, I return a syntax error.
                if item_quantity is math.nan:
                    return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),
            if item_quantity == 1 and item_title.endswith('s'):
                # Repeating an earlier check on a wider set. If the
                # item_quantity is 1 but the last token ends in a pluralizing
                # 's', I return the appropriate quantity-unclear value.
                return ((stmsg.Drop_Command_Quantity_Unclear(),) if command.lower() == 'drop'
                        else (stmsg.Pick_Up_Command_Quantity_Unclear(),))
        else:
            # I form the item title.
            item_title = ' '.join(tokens)

            # The first token didn't parse as any kind of number, so I check if
            # the item_title ends with a pluralizing 's'.
            if item_title.endswith('s'):
                # If so, the player is implying they want the total quantity
                # possible. As above, I set item_quantity to math.nan as a
                # signal value; it'll be replaced by the caller when the total
                # quantity possible is known.
                item_quantity = math.nan
            else:

                # Otherwise item_quantity is implied to be 1.
                item_quantity = 1
        item_title = item_title.rstrip('s')

        # Return the item_quantity and item_title parsed from tokens as a 2-tuple.
        return item_quantity, item_title

    def put_command(self, tokens):
        """
Execute the PUT command. The return value is always in a tuple even when it's of length 1.

This method implements the PUT command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The PUT command has
the following usage:

PUT <item name> IN <chest name>
PUT <number> <item name> IN <chest name>
PUT <item name> ON <corpse name>
PUT <number> <item name> ON <corpse name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the arguments specify a chest or corpse that is not present in the current room, returns a VariousCommands_ContainerNotFound object.

* If the arguments specify a chest that is closed, returns a VariousCommands_ContainerIsClosed object.

* If the arguments are an ungrammatical sentence and are ambiguous about the quantity to put, a PutCommand_QuantityUnclear object is returned.

* If the arguments specify an item to put that is not present in self.game_state.character.inventory, a PutCommand_ItemNotInInventory object is returned.

* If the arguments specify a quantity of an item to put that is greater than the quantity of that item in self.game_state.character.inventory, a PutCommand_TryingToPutMorethanYouHave object is returned.

* Otherwise, the specified quantity of the item is deducted from self.game_state.character, and put in the chest or on the corpse, and a PutCommand_AmountPut object is returned.
        """
        # The shared private workhorse method is called and it handles the
        # majority of the error-checking. If it returns an error that is passed
        # along.
        results = self._put_or_take_preproc('PUT', tokens)

        if len(results) == 1 and isinstance(results[0], stmsg.Game_State_Message):
            # If it returned an error, I return the tuple.
            return results
        else:
            # Otherwise, I recover put_amount (nt), item_title (str),
            # container_title (str) and container (Chest or Corpse) from the
            # results.
            put_amount, item_title, container_title, container = results

        # I read off the player's Inventory and filter it for a (qty,obj) pair
        # whose title matches the supplied Item name.
        inventory_list = tuple(filter(lambda pair: pair[1].title == item_title, self.game_state.character.list_items()))

        if len(inventory_list) == 1:

            # The player has the Item in their Inventory, so I save the qty they
            # possess and the Item object.
            amount_possessed, item = inventory_list[0]
        else:

            # Otherwise I return an item-not-in-inventory error.
            return stmsg.Put_Command_Item_Not_in_Inventory(item_title, put_amount),

        # I use the Item subclass object to get the internal_name, and look it
        # up in the container to see if any amount is already there. If so I
        # record the amount, otherwise the amount is saved as 0.
        if container.contains(item.internal_name):
            amount_in_container, _ = container.get(item.internal_name)
        else:
            amount_in_container = 0

        if put_amount > amount_possessed:
            # If the amount to put is more than the amount in inventory, I
            # return a trying-to-put-more-than-you-have error.
            return stmsg.Put_Command_Trying_to_Put_More_than_You_Have(item_title, amount_possessed),
        elif put_amount is math.nan:
            # Otherwise if _put_or_take_preproc returned math.nan for the
            # put_amount, that means it couldn't be determined from the
            # arguments but is implied, so I set it equal to the total amount
            # possessed, and set the amount_possessed to 0.
            put_amount = amount_possessed
            amount_possessed = 0
        else:

            # Otherwise I decrement the amount_possessed by the put amount.
            amount_possessed -= put_amount

        # I remove the item in the given quantity from the player character's
        # inventory, and add the item in that quantity to the container. Then I
        # return a amount-put value.
        self.game_state.character.drop_item(item, qty=put_amount)
        container.set(item.internal_name, amount_in_container + put_amount, item)
        return stmsg.Put_Command_Amount_Put(item_title, container_title, container.container_type, put_amount,
                                            amount_possessed),

    def _put_or_take_preproc(self, command, tokens):
        """
This private workhorse method handles logic that is common to put_command() and
take_command(). It determines the quantity, item title, container (and container
title) from the tokens argument.

:command: The command being executed by the calling method. Either 'PUT' or 'TAKE'.
:tokens:  The tokens argument the calling method was called with.

* If the tokens argument is zero-length or doesn't container the appropriate joinword ('FROM' for TAKE, 'IN' for PUT with chests, or 'ON' for put with corpses), returns a CommandBadSyntax object.

* If the arguments are an ungrammatical sentence and are ambiguous about the quantity of the item, returns a PutCommand_QuantityUnclear object or a TakeCommand_QuantityUnclear object.

* If the arguments specify a container title that doesn't match the title of the container in the current room, returns a VariousCommands_ContainerNotFound object.

* If the arguments targeted a chest and the chest is closed, returns a VariousCommands_ContainerIsClosed object.
        """
        # The current room's container_here value is assigned to a local variable.
        container = self.game_state.rooms_state.cursor.container_here

        command = command.lower()

        # I seek the joinword in the tokens tuple and record its index so I
        # can use it to break the tokens tuple into an item-title-part and a
        # container-title-part.
        if command == 'take':
            try:
                joinword_index = tokens.index('from')
            except ValueError:
                joinword_index = -1
            else:
                joinword = 'from'
        else:
            # The PUT command uses joinword IN for chests and ON for corpses so
            # I seek either one.
            try:
                joinword_index = tokens.index('on')
            except ValueError:
                joinword_index = -1
            else:
                joinword = 'on'
            if joinword_index == -1:
                try:
                    joinword_index = tokens.index('in')
                except ValueError:
                    joinword_index = -1
                else:
                    joinword = 'in'

        # If the joinword wasn't found, or if it's at the beginning or end of
        # the tokens tuple, I return a syntax error.
        if joinword_index == -1 or joinword_index == 0 or joinword_index + 1 == len(tokens):
            return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),

        # I use the joinword_index to break the tokens tuple into an item_tokens
        # tuple and a container_tokens tuple.
        item_tokens = tokens[:joinword_index]
        container_tokens = tokens[joinword_index+1:]

        # The first token is a digital number, so I cast it to int and set quantity.
        if util.digit_re.match(item_tokens[0]):
            quantity = int(item_tokens[0])
            item_tokens = item_tokens[1:]

        # The first token is a lexical number, so I convert it and set quantity.
        elif util.lexical_number_in_1_99_re.match(tokens[0]):
            quantity = util.lexical_number_to_digits(item_tokens[0])
            item_tokens = item_tokens[1:]

        # The first token is an indirect article, which would mean '1'.
        elif item_tokens[0] == 'a' or item_tokens[0] == 'an' or item_tokens[0] == 'the':
            if len(item_tokens) == 1:
                # item_tokens is *just* ('a',) or ('an',) or ('the',) which is a
                # syntax error.
                return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),
            else:
                # Otherwise quantity is 1.
                quantity = 1
            item_tokens = item_tokens[1:]

        else:
            # I wasn't able to determine quantity which means it's implied; I
            # assume the player means 'the total amount available', and set
            # quantity to math.nan as a signal value. The caller will replace
            # this with the total amount available when it's known.
            quantity = math.nan

        if item_tokens[-1].endswith('s'):
            if quantity == 1:
                # quantity is 1 but the item title is plural, so I return a
                # syntax error.
                return ((stmsg.Take_Command_Quantity_Unclear(),) if command == 'take'
                        else (stmsg.Put_Command_Quantity_Unclear(),))

            # I strip the plural s.
            item_tokens = item_tokens[:-1] + (item_tokens[-1].rstrip('s'),)

        if container_tokens[-1].endswith('s'):
            # The container title is plural, which is a syntax error.
            return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),

        if container_tokens[0] == 'a' or container_tokens[0] == 'an' or container_tokens[0] == 'the':
            if len(container_tokens) == 1:
                # The container title is *just* ('a',) or ('an',) or ('the',),
                # so I return a syntax error.
                return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),

            # I strip the article from the container tokens.
            container_tokens = container_tokens[1:]

        # I construct the item_title and the container_title.
        item_title = ' '.join(item_tokens)
        container_title = ' '.join(container_tokens)

        if container is None:

            # There is no container in this room, so I return a container-not-found error.
            return stmsg.Various_Commands_Container_Not_Found(container_title),
        elif not container_title == container.title:

            # The container name specified doesn't match the name of the
            # container in this Room, so I return a container-not-found error.
            return stmsg.Various_Commands_Container_Not_Found(container_title, container.title),

        elif (isinstance(container, elem.Chest) and joinword == 'on' or isinstance(container, elem.Corpse)
                  and joinword == 'in'):

            # The joinword used doesn't match the one appropriate to the type of
            # container here, so I return a syntax error.
            return stmsg.Command_Bad_Syntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),

        elif container.is_closed:

            # The container is closed, so I return a container-is-closed error.
            return stmsg.Various_Commands_Container_Is_Closed(container.title),

        # All the error checks passed, so I return the values determined from
        # the tokens argument.
        return quantity, item_title, container_title, container

    def quit_command(self, tokens):
        """
Execute the QUIT command. The return value is always in a tuple even when it's of length 1.

This method implements the QUIT command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The QUIT command
takes no arguments.

* If the command is used with any arguments, returns a CommandBadSyntax object.

* Otherwise, self.game_state.game_has_ended is set to True, and a QuitCommand_HaveQuitTheGame object is returned.
        """
        # This command takes no arguments, so if any were supplied, I return a syntax error.
        if len(tokens):
            return stmsg.Command_Bad_Syntax('QUIT', COMMANDS_SYNTAX['QUIT']),

        # I devise the quit-the-game return value, set game_has_ended to True,
        # store the return value in game_ending_state_msg so process() can reuse
        # it if needs be, and return the value.
        return_tuple = stmsg.Quit_Command_Have_Quit_The_Game(),
        self.game_state.game_has_ended = True
        self.game_ending_state_msg = return_tuple[-1]
        return return_tuple

    def reroll_command(self, tokens):
        """
Execute the REROLL command. The return value is always in a tuple even when it's of length 1.

This method implements the REROLL command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The REROLL command
takes no arguments.

* If the command is used with any arguments, this method returns a CommandBadSyntax object.

* If the character's name or class has not been set yet, returns a RerollCommand_NameOrClassNotSet object.

* Otherwise, self.game_state.character.roll_stats() is called, and a VariousCommands_DisplayRolledStats is returned.
        """
        # This command takes no arguments, so if any were supplied, I return a
        # syntax error.
        if len(tokens):
            return stmsg.Command_Bad_Syntax('REROLL', COMMANDS_SYNTAX['REROLL']),

        # This command is only valid during the pregame after the character's
        # name and class have been set (and, therefore, their stats have been
        # rolled). If either one is None, I return a name-or-class-not-set
        # error.
        character_name = getattr(self.game_state, 'character_name', None)
        character_class = getattr(self.game_state, 'character_class', None)
        if not character_name or not character_class:
            return stmsg.Reroll_Command_Name_or_Class_Not_Set(character_name, character_class),

        # I reroll the player character's stats, and return a
        # display-rolled-stats value.
        self.game_state.character.ability_scores.roll_stats()
        return stmsg.Various_Commands_Display_Rolled_Stats(
                   strength=self.game_state.character.strength,
                   dexterity=self.game_state.character.dexterity,
                   constitution=self.game_state.character.constitution,
                   intelligence=self.game_state.character.intelligence,
                   wisdom=self.game_state.character.wisdom,
                   charisma=self.game_state.character.charisma),

    def set_class_command(self, tokens):
        """
Execute the SET CLASS command. The return value is always in a tuple even when it's of length 1.

This method implements the SET CLASS command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The SET CLASS
command has the following usage:

SET CLASS [TO] <Warrior, Thief, Mage or Priest>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If a class other than Warrior, Thief, Mage or Priest is specified, returns a SetClassCommand_InvalidClass object.

* If the name has not yet been set, then the class is set, and a SetClassCommand_ClassSet object is returned.

* If the name has been set, then the class is set, self.game_state.character.roll_stats() is called as a side effect, and a 2-tuple of a SetClassCommand_ClassSet object and a Various_Commands_Display_Rolled_Stats object is returned.
        """
        # This command takes exactly one argument, so I return a syntax error if
        # I got 0 or more than 1.
        if len(tokens) == 0 or len(tokens) > 1:
            return stmsg.Command_Bad_Syntax('SET CLASS', COMMANDS_SYNTAX['SET CLASS']),

        # If the user specified something other than one of the four classes, I
        # return an invalid-class error.
        elif tokens[0] not in ('Warrior', 'Thief', 'Mage', 'Priest'):
            return stmsg.Set_Class_Command_Invalid_Class(tokens[0]),

        # I assign the chosen classname, record whether this is the first
        # time this command is used, and set the class.
        class_str = tokens[0]
        class_was_none = self.game_state.character_class is None
        self.game_state.character_class = class_str

        # If character name was already set and this is the first setting of
        # character class, the Character object will have been initialized as a
        # side effect, so I return a class-set value and a display-rolled-stats
        # value.
        if self.game_state.character_name is not None and class_was_none:
            return (stmsg.Set_Class_Command_Class_Set(class_str),
                    stmsg.Various_Commands_Display_Rolled_Stats(
                        strength=self.game_state.character.strength,
                        dexterity=self.game_state.character.dexterity,
                        constitution=self.game_state.character.constitution,
                        intelligence=self.game_state.character.intelligence,
                        wisdom=self.game_state.character.wisdom,
                        charisma=self.game_state.character.charisma
            ))
        else:
            # Otherwise I return only the class-set value.
            return stmsg.Set_Class_Command_Class_Set(class_str),

    def set_name_command(self, tokens):
        """
Execute the SET NAME command. The return value is always in a tuple even when it's of length 1.

This method implements the SET NAME command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The SET NAME
command has the following usage:

SET NAME [TO] <character name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If a name is specified that doesn't match the pattern [A-Z][a-z]+( [A-Z][a-z]+)*, returns a SetNameCommand_InvalidPart object.

* If the class has not yet been set, then the name is set, and a SetNameCommand_NameSet object is returned.

* If the class has been set, then the name is set, self.game_state.character.roll_stats() is called as a side effect, and a 2-tuple of a SetNameCommand_NameSet object and a VariousCommands_DisplayRolledStats object is returned.
        """
        # This command requires one or more arguments, so if len(tokens) == 0 I
        # return a syntax error.
        if len(tokens) == 0:
            return stmsg.Command_Bad_Syntax('SET NAME', COMMANDS_SYNTAX['SET NAME']),

        # valid_name_re.pattern == '^[A-Z][a-z]+$'. I test each token for a
        # match, and non-matching name parts are saved. If invalid_name_parts is
        # nonempty afterwards, a separate invalid-name-part error is returned
        # for each failing name part.
        invalid_name_parts = list()
        for name_part in tokens:
            if self.valid_name_re.match(name_part):
                continue
            invalid_name_parts.append(name_part)
        if len(invalid_name_parts):
            return tuple(map(stmsg.Set_Name_Command_Invalid_Part, invalid_name_parts))

        # If the name wasn't set before this call, I save that fact, then set the character name.
        name_was_none = self.game_state.character_name is None
        name_str = ' '.join(tokens)
        self.game_state.character_name = ' '.join(tokens)

        # If the character class is set and this command is the first time the
        # name has been set, that means that self.game_state has instantiated a
        # Character object as a side effect, so I return a 2-tuple of a name-set
        # value and a display-rolled-stats value.
        if self.game_state.character_class is not None and name_was_none:
            return (stmsg.Set_Name_Command_Name_Set(name_str), stmsg.Various_Commands_Display_Rolled_Stats(
                        strength=self.game_state.character.strength,
                        dexterity=self.game_state.character.dexterity,
                        constitution=self.game_state.character.constitution,
                        intelligence=self.game_state.character.intelligence,
                        wisdom=self.game_state.character.wisdom,
                        charisma=self.game_state.character.charisma
            ))
        else:
            # Otherwise I just return a name-set value.
            return stmsg.Set_Name_Command_Name_Set(self.game_state.character_name),

    def status_command(self, tokens):
        """
Execute the STATUS command. The return value is always in a tuple even when it's of length 1.

This method implements the STATUS command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The STATUS command
takes no arguments.

* If the command is used with any arguments, returns a CommandBadSyntax object.

* Otherwise, returns a StatusCommand_Output object.

        """
        # This command takes no arguments so if any were supplied I return a
        # syntax error.
        if len(tokens):
            return stmsg.Command_Bad_Syntax('STATUS', COMMANDS_SYNTAX['STATUS']),

        # A lot of data goes into a status command so I build the argd to
        # Status_Command_Output key by key.
        character = self.game_state.character
        status_gsm_argd = dict()
        status_gsm_argd['hit_points'] = character.hit_points
        status_gsm_argd['hit_point_total'] = character.hit_point_total

        # Mana points are only part of a status line if the player character is
        # a Mage or Priest.
        if character.character_class in ('Mage', 'Priest'):
            status_gsm_argd['mana_points'] = character.mana_points
            status_gsm_argd['mana_point_total'] = character.mana_point_total
        else:
            status_gsm_argd['mana_points'] = None
            status_gsm_argd['mana_point_total'] = None

        status_gsm_argd['armor_class'] = character.armor_class

        # attack_bonus and damage are only set if a weapon is equipped... or if
        # the player character is a Mage and a wand is equipped.
        if character.weapon_equipped or (character.character_class == 'Mage' and character.wand_equipped):
            status_gsm_argd['attack_bonus'] = character.attack_bonus
            status_gsm_argd['damage'] = character.damage_roll
        else:
            status_gsm_argd['attack_bonus'] = 0
            status_gsm_argd['damage'] = ''

        # The status line can display the currently equipped armor, shield,
        # weapon and wand, and if an item isn't equipped in a given slot it
        # can display 'none'; but it only shows '<Equipment>: none' if that
        # equipment type is one the player character's class can use. So I use
        # class-tests to determine whether to add each equipment-type argument.
        if character.character_class != 'Mage':
            status_gsm_argd['armor'] = character.armor.title if character.armor_equipped else None
        if character.character_class not in ('Thief', 'Mage'):
            status_gsm_argd['shield'] = character.shield.title if character.shield_equipped else None
        if character.character_class == 'Mage':
            status_gsm_argd['wand'] = character.wand.title if character.wand_equipped else None

        status_gsm_argd['weapon'] = character.weapon.title if character.weapon_equipped else None
        status_gsm_argd['character_class'] = character.character_class

        # The entire argd has been assembled so I return a status-ouput value.
        return stmsg.Status_Command_Output(**status_gsm_argd),

    def take_command(self, tokens):
        """
Execute the TAKE command. The return value is always in a tuple even when it's of length 1.

This method implements the TAKE command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The TAKE command
has the following usage:

TAKE <item name> FROM <container name>
TAKE <number> <item name> FROM <container name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the specified container isn't present in the current room, returns a VariousCommands_ContainerNotFound object.

* If the specified container is a chest and the chest is closed, returns a VariousCommands_ContainerIsClosed object.

* If the arguments are an ungrammatical sentence and are ambiguous as to what quantity the player means to take, returns a TakeCommand_QuantityUnclear object.

* If the specified item is not present in the specified chest or on the specified corpse, returns a TakeCommand_ItemNotFoundInContainer object.

* If the specified quantity of the item is greater than the quantity of that item in self.game_state.rooms_state.cursor.container_here, returns a TakeCommand_TryingToTakeMoreThanIsPresent object.

* Otherwise, the specified quantity of the specified item is deduced from self.game_state.rooms_state.cursor.container_here and added to self.game_state.character, and a TakeCommand_ItemOrItemsTaken object is returned.
        """
        # take_command() shares logic with put_command() in a private workhorse
        # method _put_or_take_preproc().
        results = self._put_or_take_preproc('TAKE', tokens)

        # As always with private workhorse methods, it may have returned an
        # error value; if so, I return it.
        if len(results) == 1 and isinstance(results[0], stmsg.Game_State_Message):
            return results
        else:
            # Otherwise, I extract the values parsed out of tokens from the
            # results tuple.
            quantity_to_take, item_title, container_title, container = results

        # The following loop iterates over all the items in the Container. I use
        # a while loop so it's possible for the search to fall off the end of
        # the loop. If that code is reached, the specified Item isn't in this
        # Container.
        matching_item = tuple(filter(lambda argl: argl[1][1].title == item_title, container.items()))
        if len(matching_item) == 0:
            return stmsg.Take_Command_Item_Not_Found_in_Container(
                       container_title, quantity_to_take, container.container_type, item_title),

        (item_internal_name, (item_quantity, item)), = matching_item

        # The private workhorse method couldn't determine a quantity and
        # returned the signal value math.nan, so I assume the entire amount
        # present is intended, and set quantity_to_take to item_quantity.
        if quantity_to_take is math.nan:
            quantity_to_take = item_quantity
        if quantity_to_take > item_quantity:
            # The amount specified is more than how much is in the Container, so
            # I return a trying-to-take-more-than-is-present error.
            return stmsg.Take_Command_Trying_to_Take_More_than_Is_Present(
                             container_title, container.container_type,
                             item_title, item.item_type, quantity_to_take, item_quantity),

        if quantity_to_take == item_quantity:
            # The amount to remove is the total amount present, so I delete it
            # from the container.
            container.delete(item_internal_name)
        else:
            # The quantity to take is less thant the amount present, so I set
            # the item in the container to the new lower quantity.
            container.set(item_internal_name, item_quantity - quantity_to_take, item)

        # I add the item in the given quantity to the player character's
        # inventory and return an item-or-items-taken value.
        self.game_state.character.pick_up_item(item, qty=quantity_to_take)
        return stmsg.Take_Command_Item_or_Items_Taken(container_title, item_title, quantity_to_take),

    def unequip_command(self, tokens):
        """
Execute the UNEQUIP command. The return value is always in a tuple even when it's of length 1.

This method implements the UNEQUIP command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The UNEQUIP command
has the following usage:

UNEQUIP <armor name>
UNEQUIP <shield name>
UNEQUIP <wand name>
UNEQUIP <weapon name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the specified item is not equipped in self.game_state.rooms_state.character, returns a UnequipCommand_ItemNotEquipped object.

* Otherwise, the specified item is unequipped in self.game_state.rooms_state.character, and a VariousCommands_ItemUnequipped is returned.
        """
        # This command requires an argument so if none was supplied I return a
        # syntax error.
        if not tokens:
            return stmsg.Command_Bad_Syntax('UNEQUIP', COMMANDS_SYNTAX['UNEQUIP']),

        # I construct the item title and search for it in the player character's
        # inventory.
        item_title = ' '.join(tokens)
        matching_item_tuple = tuple(item for _, item in self.game_state.character.list_items()
                                    if item.title == item_title)

        # If the item isn't found in the player character's inventory, I search
        # for it in the items_state just to get the item_type; I return an
        # item-not-equipped error informed by the found item_type if possible.
        if not len(matching_item_tuple):
            matching_item_tuple = tuple(item for item in self.game_state.items_state.values()
                                        if item.title == item_title)
            if matching_item_tuple:
                item, = matching_item_tuple[0:1]
                return stmsg.Unequip_Command_Item_Not_Equipped(item.title, item.item_type),
            else:
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title),

        # I extract the matched item.
        item, = matching_item_tuple[0:1]

        # This code is very repetitive but it can't easily be condensed into a
        # loop due to the special case handling in the weapon section vis a vis
        # wands, so I just deal with repetitive code.
        if item.item_type == 'armor':
            if self.game_state.character.armor_equipped is None:
                # If I'm unequipping armor but the player character has no armor
                # equipped I return a item-not-equipped error.
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'armor'),
            else:
                if self.game_state.character.armor_equipped.title != item_title:
                    # If armor_equipped's title doesn't match the argument
                    # item_title, I return an item-not-equipped error.
                    return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'armor',
                                                                   self.game_state.character.armor_equipped.title),
                else:
                    # Otherwise, the title matches, so I unequip the armor and
                    # return a item-unequipped value.
                    self.game_state.character.unequip_armor()
                    return stmsg.Various_Commands_Item_Unequipped(item_title, 'armor',
                                                                  armor_class=self.game_state.character.armor_class),
        elif item.item_type == 'shield':
            if self.game_state.character.shield_equipped is None:
                # If I'm unequipping a shield but the player character has no shield
                # equipped I return a item-not-equipped error.
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'shield'),
            else:
                if self.game_state.character.shield_equipped.title != item_title:
                    # If shield_equipped's title doesn't match the argument
                    # item_title, I return an item-not-equipped error.
                    return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'shield',
                                                                   self.game_state.character.shield_equipped.title),
                else:
                    # Otherwise, the title matches, so I unequip the shield and
                    # return a item-unequipped value.
                    self.game_state.character.unequip_shield()
                    return stmsg.Various_Commands_Item_Unequipped(item_title, 'shield',
                                                                  armor_class=self.game_state.character.armor_class),
        elif item.item_type == 'wand':
            if self.game_state.character.wand_equipped is None:
                # If I'm unequipping a wand but the player character has no wand
                # equipped I return a item-not-equipped error.
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'wand'),
            else:
                if self.game_state.character.wand_equipped.title != item_title:
                    # If wand_equipped's title doesn't match the argument
                    # item_title, I return an item-not-equipped error.
                    return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'wand'),
                else:
                    # Otherwise, the title matches, so I unequip the wand.
                    self.game_state.character.unequip_wand()
                    weapon_equipped = self.game_state.character.weapon_equipped
                    # If a weapon is equipped, the player character will
                    # still be able to attack with *that*, so I return an
                    # item-unequipped value initialized with the weapon's info.
                    if weapon_equipped is not None:
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'wand',
                                                                      attack_bonus=self.game_state.character.
                                                                          attack_bonus,
                                                                      damage=self.game_state.character.damage_roll,
                                                                      now_attacking_with=weapon_equipped),
                    else:
                        # Otherwise, I return an item-unequipped value with
                        # cant_attack set to True.
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'wand', cant_attack=True),
        elif item.item_type == 'weapon':
            # If I'm unequipping a weapon but the player character has no weapon
            # equipped I return a item-not-equipped error.
            if self.game_state.character.weapon_equipped is None:
                return stmsg.Unequip_Command_Item_Not_Equipped(item.title, 'weapon'),
            else:
                if self.game_state.character.weapon_equipped.title != item_title:
                    # If weapon_equipped's title doesn't match the argument
                    # item_title, I return an item-not-equipped error.
                    return stmsg.Unequip_Command_Item_Not_Equipped(item.title, 'weapon'),
                else:
                    # Otherwise, the title matches, so I unequip the weapon.
                    self.game_state.character.unequip_weapon()
                    wand_equipped = self.game_state.character.wand_equipped
                    # If the player character has a wand equipped, they'll
                    # be attacking with that regardless of their weapon, so
                    # I return an item-unequipped value initialized with the
                    # wand's info.
                    if wand_equipped is not None:
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon',
                                                                      attack_bonus=self.game_state.character.
                                                                          attack_bonus,
                                                                      damage=self.game_state.character.damage_roll,
                                                                      attacking_with=wand_equipped),
                    else:
                        # Otherwise I return an item-unequipped value with
                        # now_cant_attack set to True.
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon', now_cant_attack=True),

    def unlock_command(self, tokens):
        """
Execute the UNLOCK command. The return value is always in a tuple even when it's of length 1.

This method implements the UNLOCK command. It accepts a tokens tuple that
is the command's arguments, tokenized. It returns a tuple of one or more
adventuregame.statemsgs.GameStateMessage subclass objects. The UNLOCK command
has the following usage:

UNLOCK <door\u00A0name>
UNLOCK <chest\u00A0name>

* If that syntax is not followed, returns a CommandBadSyntax object.

* If the arguments specify a door that is not present in the room, returns a VariousCommands_DoorNotPresent object.

* If the arguments given match more than one door in the room, returns a VariousCommands_AmbiguousDoorSpecifier object.

* If the specified door or chest is not present in the current room, returns an UnlockCommand_ElementToUnlockNotHere object.

* If the specified element is a doorway, item, creature or corpse, returns an UnlockCommand_ElementNotUnlockable object.

* If the character does not possess the requisite door or chest key to lock the specified door or chest, returns an UnlockCommand_DontPossessCorrectKey object.

* If the specified door or chest is already unlocked, returns a UnlockCommand_ElementIsAlreadyUnlocked object.

* Otherwise, the specified door's or chest's is_locked attribute is set to False, and an UnlockCommand_ElementHasBeenUnlocked object is returned.
        """
        # This command requires an argument; so if it was called with no
        # arguments, I return a syntax error.
        if len(tokens) == 0:
            return stmsg.Command_Bad_Syntax('UNLOCK', COMMANDS_SYNTAX['UNLOCK']),

        # unlock_command() shares preprocessing logic with lock_command(),
        # open_command() and close_command(), so a private workhorse method is
        # called.
        result = self._preprocessing_for_lock_unlock_open_or_close('UNLOCK', tokens)
        if isinstance(result[0], stmsg.Game_State_Message):
            # If an error value is returned, I return it in turn.
            return result
        else:
            # Otherwise I extract the element_to_unlock from the result tuple.
            element_to_unlock, = result

        # A key is required to unlock something; the chest key for chests and
        # the door key for doors. So I search the player character's inventory
        # for it. The key is not consumed by use, so I only need to know it's
        # there, not retrieve the Key object and operate on it.
        key_required = 'door key' if isinstance(element_to_unlock, elem.Door) else 'chest key'
        if not any(item.title == key_required for _, item in self.game_state.character.list_items()):
            # If the required key is not present, I return a
            # don't-possess-correct-key error.
            return stmsg.Unlock_Command_Dont_Possess_Correct_Key(element_to_unlock.title, key_required),
        elif element_to_unlock.is_locked is False:
            # Otherwise, if the item is already unlocked, I return an
            # element-is-already-unlocked error.
            return stmsg.Unlock_Command_Element_Is_Already_Unlocked(element_to_unlock.title),
        elif isinstance(element_to_unlock, elem.Door):
            # This is a door object, and it only represents _this side_ of the
            # door game element; I use _matching_door() to fetch the door object
            # representing the opposite side so that the door game element will
            # be unlocked from the perspective of either room.
            opposite_door = self._matching_door(element_to_unlock)
            if opposite_door is not None:
                opposite_door.is_locked = False

        # I unlock the element, and return an element-has-been-unlocked value.
        element_to_unlock.is_locked = False
        return stmsg.Unlock_Command_Element_Has_Been_Unlocked(element_to_unlock.title),
