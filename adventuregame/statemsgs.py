#!/usr/bin/python2

"""
This module contains Game_State_Message and its numerous subclasses.
adventuregame.processor.Command_Processor.process() processes a natural
language command from the player and tail calls a command method of the
adventuregame.processor.Command_Processor object. It always returns a tuple
of Game_State_Message subclass objects; each one represents a single possible
outcome of a command. A Game_State_Message subclass has an __init__ method that
assigns keyword arguments to object attributes and a message property which
contains the logic for rendering the semantic value of the message object in
natural language.
"""

import abc
import operator

import adventuregame.exceptions as excpt
import adventuregame.utility as util

__name__ = 'adventuregame.gamestatemessages'


class Game_State_Message(abc.ABC):
    """
This class is the abstract base class for all the game state message classes
in this module. It defines an abstract property message and an abstract method
__init__.
    """

    @property
    @abc.abstractmethod
    def message(self):
        """
The message property of a Game_State_Message subclass renders the data stored
in the object attributes to a natural language string which communicates the
semantic content of the object to the player. The message property is accessed
and printed by advgame.py.
        """
        pass

    @abc.abstractmethod
    def __init__(self, *argl, **argd):
        """
The __init__ method of a Game_State_Message subclass stores its keyword
arguments to object attributes, and performs no other task.
        """
        pass


class Command_Bad_Syntax(Game_State_Message):
    __slots__ = 'command', 'proper_syntax_options'

    """
This class implements an error object that is returned by command methods of
adventuregame.processor.Command_Processor when incorrect syntax for a command
has been used.
    """

    @property
    def message(self):
        # The proper_syntax_options tuple is drawn from
        # adventuregame.processor.COMMANDS_SYNTAX; it is comprised
        # of strings which spell out valid command arguments. \u00A0
        # (a nonbreaking space) is used in place of normal spaces to
        # ensure that a syntax line is never broken across a newline by
        # adventuregame.utilities.textwrapper(). (They become kindof unreadable
        # if they're word-wrapped.)
        #
        # This message property joins the command with each line of the
        # proper_syntax_options tuple, and presents a corrective outlining valid
        # syntax for this command.
        command = self.command.upper().replace(' ', '\u00A0')
        syntax_options = tuple(f"'{command}\u00A0{syntax_option}'"
                                if syntax_option
                                else f"'{command}'"
                                for syntax_option in self.proper_syntax_options)
        proper_syntax_options_str = util.join_str_seq_w_commas_and_conjunction(syntax_options, 'or')
        return f'{self.command.upper()} command: bad syntax. Should be {proper_syntax_options_str}.'

    def __init__(self, command, proper_syntax_options):
        self.command = command
        self.proper_syntax_options = proper_syntax_options


class Command_Class_Restricted(Game_State_Message):
    """
This class implements an error object that is returned by
adventuregame.processor.Command_Processor.processor() when the player has used a
command that is restricted to a class other than their own. (For example, only
thieves can use PICK LOCK.)
    """
    __slots__ = 'command', 'classes',

    @property
    def message(self):
        # This message property assembles a list of classes (in self.classes) which are
        # authorized to use the given command (in self.command).
        classes_plural = [class_str + 's' if class_str != 'thief' else 'thieves' for class_str in self.classes]
        class_str = util.join_str_seq_w_commas_and_conjunction(classes_plural, 'and')
        return f'Only {class_str} can use the {self.command.upper()} command.'

    def __init__(self, command, *classes):
        self.command = command
        self.classes = classes


class Command_Not_Allowed_Now(Game_State_Message):
    """
This class implements an error object that is returned by
adventuregame.processor.Command_Processor.processor() when the player has used
a command that is not allowed in the current game mode. The game has two modes:
pregame, when name and class are chosen and ability scores are rolled, and
in-game, when the player plays the game. Different command sets are allowed in
each mode. See adventuregame.processor.Command_Processor.pregame_commands and
adventuregame.processor.Command_Processor.ingame_commands for the lists.
    """
    __slots__ = 'command', 'allowed_commands', 'game_has_begun'

    @property
    def message(self):
        # This message property responds to a user using a pregame command
        # during ingame or an ingame command during pregame; it assembles a
        # list of allowed commands from self.allowed commands and returns a
        # remonstrative message informing the player that the command they
        # tried (in self.command) can't be used in the current game mode
        # (game_state_str), but commands in this list (commands_str) can.
        game_state_str = 'before game start' if not self.game_has_begun else 'during the game'
        message_str = f"Command '{self.command}' not allowed {game_state_str}. "
        commands_str = util.join_str_seq_w_commas_and_conjunction(
                            tuple(command.upper().replace('_', ' ')
                                  for command in sorted(self.allowed_commands)),
                            'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun


class Command_Not_Recognized(Game_State_Message):
    """
This class implements an error object that is returned by
adventuregame.processor.Command_Processor.processor() when a command was entered
that is not known to the command processor.
    """
    __slots__ = 'command', 'allowed_commands', 'game_has_begun'

    @property
    def message(self):
        # This message property responds to a user entering a command that's not
        # recognized; it assembles a list of allowed commands from self.allowed
        # commands and returns a message informing the player that the command
        # they used (in self.command) isn't recognized but in the current game
        # mode (game_state_str) commands in this list (commands_str) can.
        message_str = f"Command '{self.command}' not recognized. "
        game_state_str = 'before game start' if not self.game_has_begun else 'during the game'
        commands_str = util.join_str_seq_w_commas_and_conjunction(tuple(command.upper().replace('_', ' ') for command in sorted(self.allowed_commands)), 'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun


class Attack_Command_Attack_Hit(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.attack_command() when the player's
attack connected with their foe. Because attack_command() always triggers the
hidden _be_attacked_by_command() pseudo-command, an Attack_Command_Attack_Hit
object tracks if the foe was slain. If so, nothing relating to foe death is
conveyed; describing foe death is handled by the Various_Commands_Foe_Death
class. If not, its message includes a clause about the foe turning to attack.
    """
    __slots__ = 'creature_title', 'damage_done', 'creature_slain'

    @property
    def message(self):
        # This message property returns a message announcing the result of a
        # successful attack on a creature in one of four cases:
        #
        # The attack was with a weapon and the creature died.
        if self.creature_slain and self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage.'
        # The attack was with a wand and the creature died.
        elif self.creature_slain and self.weapon_type == 'wand':
            return (f'A bolt of energy from your wand hits the {self.creature_title}! You did {self.damage_done} '
                    f'damage. The {self.creature_title} turns to attack!')
        # The attack was with a weapon, the creature didn't die, and they're
        # counterattacking.
        elif not self.creature_slain and self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage.'
        # The attack was with a wand, the creature didn't die, and they're
        # counterattacking.
        else:
            return (f'A bolt of energy from your wand hits the {self.creature_title}! You did {self.damage_done} '
                    f'damage. The {self.creature_title} turns to attack!')

    def __init__(self, creature_title, damage_done, creature_slain, weapon_type):
        self.creature_title = creature_title
        self.damage_done = damage_done
        self.creature_slain = creature_slain
        self.weapon_type = weapon_type


class Attack_Command_Attack_Missed(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.attack_command() when the player's
attack missed. Like Attack_Command_Attack_Hit, it mentions the foe turning to
attack, because an attack on a foe always leads to a counterattack if they live.
    """
    __slots__ = 'creature_title', 'weapon_type'

    @property
    def message(self):
        # This message property returns a message announcing the result of a
        # failed attack on a creature in one of two cases:
        #
        # The attack was with a weapon, and the creature is counterattacking.
        if self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} missed. It turns to attack!'
        # The attack was with a wand, and the creature is counterattacking.
        else:
            return f'A bolt of energy from your wand misses the {self.creature_title}. It turns to attack!'

    def __init__(self, creature_title, weapon_type):
        self.creature_title = creature_title
        self.weapon_type = weapon_type


class Attack_Command_Opponent_Not_Found(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.attack_command() when the player has
used an attack command that refers to a foe that is not present in the game's
current room.
    """
    __slots__ = 'creature_title_given', 'opponent_present'

    @property
    def message(self):
        # This message property handles two cases:
        #
        # There is a creature in the room by a different title and they can be
        # suggested as a better target.
        if self.opponent_present:
            return f"This room doesn't have a {self.creature_title_given}; but there is a {self.opponent_present}."
        # There is no creature in this room.
        else:
            return f"This room doesn't have a {self.creature_title_given}; nobody is here."

    def __init__(self, creature_title_given, opponent_present=''):
        self.creature_title_given = creature_title_given
        self.opponent_present = opponent_present


class Attack_Command_You_Have_No_Weapon_or_Wand_Equipped(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.attack_method() when the player
has used the attack command while having no weapon (or, for Mages, no wand)
equipped. It tracks player class so it knows to display the wand option for
Mages.
    """
    __slots__ = 'character_class',

    @property
    def message(self):
        # This message property handles two cases:
        #
        # The player's character is a Mage and has neither a wand or a weapon
        # equipped.
        if self.character_class == 'Mage':
            return "You have no wand or weapon equipped; you can't attack."
        # The player's character is a Warrior, Thief or Priest and has no
        # weapon equipped.
        else:
            return "You have no weapon equipped; you can't attack."

    def __init__(self, character_class):
        self.character_class = character_class


class Be_Attacked_by_Command_Attacked_and_Hit(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor._be_attacked_by_command() when the
foe's counterattack connects. It conveys the damage done and how many hit points
the player's character has left.
    """
    __slots__ = 'creature_title', 'damage_done', 'hit_points_left'

    @property
    def message(self):
        # This message property informs the player of the effect of a creature's
        # attack on their hit points.
        return (f'The {self.creature_title} attacks! Their attack hits. They did {self.damage_done} damage! You have '
                f'{self.hit_points_left} hit points left.')

    def __init__(self, creature_title, damage_done, hit_points_left):
        self.creature_title = creature_title
        self.damage_done = damage_done
        self.hit_points_left = hit_points_left


class Be_Attacked_by_Command_Attacked_and_Not_Hit(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor._be_attacked_by_command() when the
foe's counterattack did not connect.
    """
    __slots__ = 'creature_title',

    @property
    def message(self):
        return f'The {self.creature_title} attacks! Their attack misses.'

    def __init__(self, creature_title):
        self.creature_title = creature_title


class Be_Attacked_by_Command_Character_Death(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor._be_attacked_by_command() when the
foe's counter attack killed the player's character. The game is now over, and
advgame.py responds to receiving this object by printing its message and then
exiting the program.
    """

    @property
    def message(self):
        return 'You have died!'

    def __init__(self):
        pass


class Begin_Game_Command_Game_Begins(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.begin_game_command() when the command
executes successfully. The game has begun.
    """

    @property
    def message(self):
        return 'The game has begun!'

    def __init__(self):
        pass


class Begin_Game_Command_Name_or_Class_Not_Set(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.begin_game_command() when the player
has used the BEGIN GAME command prematurely. The player must set a name and a
class before the game can begin; this object is returned if they fail to.
    """
    __slots__ = 'character_name', 'character_class'

    @property
    def message(self):
        # This message property covers three cases:
        #
        # The player needs to use both the SET NAME and the SET CLASS commands
        # before proceeding.
        if not self.character_name and not self.character_class:
            return ('You need to set your character name and class before you begin the game. Use SET NAME <name> to '
                    'set your name and SET CLASS <Warrior, Thief, Mage or Priest> to select your class.')
        # The player needs to use the SET NAME command before proceeding.
        elif not self.character_name:
            return ('You need to set your character name before you begin the game. Use SET NAME <name> to set your '
                    'name.')
        # The player needs to use the SET CLASS command before proceeding.
        else:
            return ('You need to set your character class before you begin the game. Use SET CLASS <Warrior, Thief, '
                    'Mage or Priest> to select your class.')

    def __init__(self, character_name, character_class):
        self.character_name = character_name
        self.character_class = character_class


class Cast_Spell_Command_Cast_Damaging_Spell(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.cast_spell_command() when the player,
while playing a Mage, has cast a damaging spell. Like Attack_Command_Attack_Hit,
it tracks whether the foe was slain, and adds a 'they turn to attack' sentence
if not.
    """
    __slots__ = 'creature_title', 'damage_dealt'

    @property
    def message(self):
        # This message property handles two cases:
        #
        # The player character's spell killed their foe.
        if self.creature_slain:
            return (f'A magic missile springs from your gesturing hand and unerringly strikes the {self.creature_title}. '
                    f'You have done {self.damage_dealt} points of damage.')
        # The player character's spell didn't kill their foe, and, as with any
        # use of the ATTACK command, the creature is counterattacking.
        else:
            return (f'A magic missile springs from your gesturing hand and unerringly strikes the {self.creature_title}. '
                    f'You have done {self.damage_dealt} points of damage. The {self.creature_title} turns to attack!')

    def __init__(self, creature_title, damage_dealt, creature_slain):
        self.creature_title = creature_title
        self.damage_dealt = damage_dealt
        self.creature_slain = creature_slain


class Cast_Spell_Command_Cast_Healing_Spell(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.cast_spell_command() when used by
a Priest. It doesn't need to mention how much damage was healed because it's
followed by a Various_Commands_Underwent_Healing_Effect instance that does that.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You cast a healing spell on yourself.'

    def __init__(self):
        pass


class Cast_Spell_Command_Insufficient_Mana(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.cast_spell_command() when the player
tries to cast a spell with insufficient mana points.
    """
    __slots__ = 'current_mana_points', 'mana_point_total', 'spell_mana_cost'

    @property
    def message(self):
        return ("You don't have enough mana points to cast a spell. Casting a spell costs "
                f'{self.spell_mana_cost} mana points. Your mana points are '
                f'{self.current_mana_points}/{self.mana_point_total}.')

    def __init__(self, current_mana_points, mana_point_total, spell_mana_cost):
        self.current_mana_points = current_mana_points
        self.mana_point_total = mana_point_total
        self.spell_mana_cost = spell_mana_cost


class Cast_Spell_Command_No_Creature_to_Target(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.cast_spell_command() when the player
uses the command in a room with no creature to attack.
    """
    __slots__ = ()

    @property
    def message(self):
        return "You can't cast magic missile here; there is no creature here to target."

    def __init__(self):
        pass


class Close_Command_Element_Not_Closable(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.close_command() when the player
attempts to close a corpse, creature, doorway or item.
    """
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        if self.target_type == 'armor':
            return f"You can't close the {self.target_title}; suits of {self.target_type} are not closable."
        else:
            return f"You can't close the {self.target_title}; {self.target_type}s are not closable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class Close_Command_Element_Has_Been_Closed(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.close_command() when the player
succeeds in closing a door or chest.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'You have closed the {self.target}.'

    def __init__(self, target):
        self.target = target


class Close_Command_Element_Is_Already_Closed(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.close_command() when the closable
object the player targeted is already closed.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already closed.'

    def __init__(self, target):
        self.target = target


class Close_Command_Element_to_Close_Not_Here(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.close_command() when the player
specifies a target to the command that is not present in the current room of the
game.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to close.'

    def __init__(self, target_title):
        self.target_title = target_title


class Drink_Command_Drank_Mana_Potion(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_coomand() when the player
uses it to drink a mana potion. It is only returned if the player's
character is a Mage or Priest. If they're playing a Warrior or Thief, a
Drink_Command_Drank_Mana_Potion_when_Not_A_Spellcaster object is returned
instead.
    """
    __slots__ = 'amount_regained', 'current_mana_points', 'mana_point_total',

    @property
    def message(self):
        # This message property handles three cases:
        # * The player regained mana points and now has their maximum hit points.
        # * The player regained mana points but are still short of their maximum.
        # * The player didn't regain any mana points because their mana points were
        #   already at maximum.
        return_str = (f'You regained {self.amount_regained} mana points.' if self.amount_regained != 0
                      else "You didn't regain any mana points.")
        if self.current_mana_points == self.mana_point_total:
            return_str += ' You have full mana points!'
        return_str += f' Your mana points are {self.current_mana_points}/{self.mana_point_total}.'
        return return_str

    def __init__(self, amount_regained, current_mana_points, mana_point_total):
        self.amount_regained = amount_regained
        self.current_mana_points = current_mana_points
        self.mana_point_total = mana_point_total


class Drink_Command_Drank_Mana_Potion_when_Not_A_Spellcaster(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_command() when the player drinks
a mana potion but they're playing a Warrior or Thief and have no mana points to
restore.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You feel a little strange, but otherwise nothing happens.'

    def __init__(self):
        pass


class Drink_Command_Item_Not_Drinkable(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_command() when the player
targets an item that is not a potion.
    """
    __slots__ = 'item_title',

    @property
    def message(self):
        return f'A {self.item_title} is not drinkable.'

    def __init__(self, item_title):
        self.item_title = item_title


class Drink_Command_Item_Not_in_Inventory(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_command() when the player tries
to drink a potion that isn't in their inventory.
    """
    __slots__ = 'item_title',

    @property
    def message(self):
        return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title):
        self.item_title = item_title


class Drink_Command_Tried_to_Drink_More_than_Possessed(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_command() when the player
specifies drinking a quantity of potions that is greater than the number they
have in their inventory.
    """
    __slots__ = 'item_title', 'attempted_qty', 'possessed_qty'

    @property
    def message(self):
        return f"You can't drink {self.attempted_qty} {self.item_title}s. You only have {self.possessed_qty} of them."

    def __init__(self, item_title, attempted_qty, possessed_qty):
        self.item_title = item_title
        self.attempted_qty = attempted_qty
        self.possessed_qty = possessed_qty


class Drink_Command_Quantity_Unclear(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_command() when the player writes
an ungrammatical sentence that is ambiguous as to how many of the item they
intend to target.
    """

    @property
    def message(self):
        return 'Amount to drink unclear. How many do you mean?'

    def __init__(self):
        pass


class Drop_Command_Dropped_Item(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drop_command() when the player
successfully drops an item on the floor.
    """
    __slots__ = 'item_title', 'item_type', 'amount_dropped', 'amount_on_floor', 'amount_left'

    @property
    def message(self):
        # This message property handles assembling a string that informs the
        # player how many of the item they dropped (always nonzero), how many
        # are on the floor now (always nonzero), and how many of the item they
        # have left (may be zero).
        #
        # Armor is handled specially because the proper way to refer to a
        # singular armor piece isn't "a studded leather armor" but "a suit of
        # studded leather armor'.
        drop_qty_or_ind_artcl = (f'{self.amount_dropped} ' if self.amount_on_floor > 1
                                 else 'a suit of ' if self.item_type == 'armor'
                                 else 'an ' if self.item_title[0] in 'aeiou'
                                 else 'a ')
        floor_qty_or_ind_artcl = (f'{self.amount_on_floor} ' if self.amount_on_floor > 1
                                  else 'a suit of ' if self.item_type == 'armor'
                                  else 'an ' if self.item_title[0] in 'aeiou'
                                  else 'a ')
        # The *_pluralizer strings are appended to the item titles, and are 's'
        # if the item qty is more than 1, or '' if the item qty is 1.
        drop_qty_pluralizer = '' if self.amount_dropped == 1 else 's'
        floor_qty_pluralizer = '' if self.amount_on_floor == 1 else 's'

        # The amount dropped and the amount on the floor both must be nonzero,
        # but the amount left may be zero. If the player has none of the item
        # left, this isn't used.
        left_qty_plr_or_sing_term = (f'suits of {self.item_title}' if self.item_type == 'armor'
                                     else f'{self.item_title}s' if self.amount_left != 1
                                     else self.item_title)
        if self.amount_left >= 1:
            return (f'You dropped {drop_qty_or_ind_artcl}{self.item_title}{drop_qty_pluralizer}. You see {floor_qty_or_ind_artcl}'
                    f'{self.item_title}{floor_qty_pluralizer} here. You have {self.amount_left} {left_qty_plr_or_sing_term} left.')
        else:
            return (f'You dropped {drop_qty_or_ind_artcl}{self.item_title}{drop_qty_pluralizer}. You see {floor_qty_or_ind_artcl}'
                    f'{self.item_title}{floor_qty_pluralizer} here. You have no {left_qty_plr_or_sing_term} left.')

    def __init__(self, item_title, item_type, amount_dropped, amount_on_floor, amount_left):
        self.item_title = item_title
        self.item_type = item_type
        self.amount_dropped = amount_dropped
        self.amount_on_floor = amount_on_floor
        self.amount_left = amount_left


class Drop_Command_Quantity_Unclear(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drop_command() when the player writes
an ungrammatical sentence that is ambiguous as to how many of the item they
intend to target.
    """

    @property
    def message(self):
        return 'Amount to drop unclear. How many do you mean?'

    def __init__(self):
        pass


class Drop_Command_Trying_to_Drop_Item_You_Dont_Have(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drop_command() when the player
specifies an item to drop that is not in their inventory.
    """
    __slots__ = 'item_title', 'amount_attempted'

    @property
    def message(self):
        # This message property assembles a string informing the player they
        # don't have the item in their inventory, hanlding both the singular and
        # the plural cases.
        article_or_pronoun = 'a' if self.amount_attempted == 1 else 'any'
        pluralizer = '' if self.amount_attempted == 1 else 's'
        return f"You don't have {article_or_pronoun} {self.item_title}{pluralizer} in your inventory."

    def __init__(self, item_title, amount_attempted):
        self.item_title = item_title
        self.amount_attempted = amount_attempted


class Drop_Command_Trying_to_Drop_More_than_You_Have(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drop_command() when the player
specifies a quantity of a certain item to drop that is more than the quantity of
that item that they actually possess.
    """
    __slots__ = 'item_title', 'amount_attempted', 'amount_had'

    @property
    def message(self):
        # This message assumes the quantity the player attempted to drop is
        # greater than 1. They're getting this message because they tried to
        # drop a quantity of the item greater than the quantity they possess;
        # but they must possess at least 1 to get this message, so the quantity
        # they tried to drop must be more than that.
        pluralizer = '' if self.amount_had == 1 else 's'
        return f"You can't drop {self.amount_attempted} {self.item_title}s. You only have {self.amount_had} "\
               f'{self.item_title}{pluralizer} in your inventory.'

    def __init__(self, item_title, amount_attempted, amount_had):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_had = amount_had


class Equip_Command_Class_Cant_Use_Item(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.equip_command() when the player tries
to equip an item that is not allowed for their class. As an example, a Mage
would get this result if they tried to equip a suit of armor or a shield, and
anyone besides a Mage would get this result if they tried to equip a wand.
    """
    __slots__ = 'character_class', 'item_title', 'item_type'

    @property
    def message(self):
        # This message property assembles a string to inform the player
        # that they can't equip an item due to class restrictions. Like
        # Drop_Command_Dropped_Item.message, it omits the indirect article if
        # the item is a suit of armor.
        item_usage_verb = util.usage_verb(self.item_type, gerund=False)
        pluralizer = 's' if self.item_type != 'armor' else ''
        return f"{self.character_class}s can't {item_usage_verb} {self.item_title}{pluralizer}."

    def __init__(self, character_class, item_title, item_type):
        self.character_class = character_class
        self.item_title = item_title
        self.item_type = item_type


class Equip_Command_No_Such_Item_in_Inventory(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.equip_command() when the player tries
to equip an item that they don't have in their inventory.
    """
    __slots__ = 'item_title',

    @property
    def message(self):
        return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title):
        self.item_title = item_title


class Help_Command_Command_Not_Recognized(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.help_command() when the player tries
to get help with a command that is not in the game.
    """
    __slots__ = 'command_attempted', 'commands_available',

    @property
    def message(self):
        return_lines = [f"The command '{self.command_attempted.upper()}' is not recognized. "
                         'The full list of commands is:', '']
        return_lines.extend((util.join_str_seq_w_commas_and_conjunction(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return '\n'.join(return_lines)

    def __init__(self, command_attempted, commands_available):
        self.command_attempted = command_attempted
        self.commands_available = commands_available


class Help_Command_Display_Commands(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.help_command() when the player calls
it with no arguments; it displays all the commands in the game and prompts the
player to ask for help with one of them.
    """
    __slots__ = 'commands_available',

    @property
    def message(self):
        return_lines = ['The full list of commands is:', '']
        return_lines.extend((util.join_str_seq_w_commas_and_conjunction(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return '\n'.join(return_lines)

    def __init__(self, commands_available):
        self.commands_available = commands_available


class Help_Command_Display_Help_for_Command(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.help_command() when the player asks
for help with a specific command. It summarizes the syntax for them and prints
an informative blurb about the command.
    """
    __slots__ = 'command', 'syntax_tuple', 'instructions',

    @property                   #
    def message(self):          #
        # Like Command_Bad_Syntax, this message property accepts syntax
        # outlines from adventuregame.processor.COMMANDS_SYNTAX and assembles
        # them into a list of valid usages, using unicode nonbreaking
        # spaces so the usage examples aren't broken across lines by
        # adventuregame.utilities.textwrapper().
        syntax_str_list = [f"'{self.command}\u00A0{syntax_entry}'" if syntax_entry else f"'{self.command}'"
                               for syntax_entry in self.syntax_tuple]
        return_lines = [f'Help for the {self.command} command:', '']
        return_lines.extend(('Usage: ' + util.join_str_seq_w_commas_and_conjunction(syntax_str_list, 'or'), ''))
        return_lines.extend((self.instructions, ''))
        return '\n'.join(return_lines)

    def __init__(self, command, syntax_tuple=None, instructions=None):
        self.command = command
        self.syntax_tuple = syntax_tuple
        self.instructions = instructions


class Inventory_Command_Display_Inventory(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.inventory_command(). It lists all the
items in the character's inventory by title and quantity. If they want more
information they need to say 'LOOK AT <item title> IN INVENTORY'.
    """
    __slots__ = 'inventory_contents',

    @property
    def message(self):
        display_strs_list = list()
        for item_qty, item in self.inventory_contents:
            indir_artcl_or_qty = (str(item_qty) if item_qty > 1
                                  else 'a suit of' if item.item_type == 'armor'
                                  else 'an' if item.title[0] in 'aeiou'
                                  else 'a')
            pluralizer = 's' if item_qty > 1 else ''
            display_strs_list.append(f'{indir_artcl_or_qty} {item.title}{pluralizer}')
        return 'You have ' + util.join_str_seq_w_commas_and_conjunction(display_strs_list, 'and') + ' in your inventory.'

    def __init__(self, inventory_contents_list):
        self.inventory_contents = inventory_contents_list


class Leave_Command_Door_Is_Locked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.leave_command() if the player tries to
leave through a door that is locked.
    """
    __slots__ = 'compass_dir', 'portal_type'

    @property
    def message(self):
        return (f"You can't leave the room via the {self.compass_dir} {self.portal_type}: the {self.portal_type} is "
                 'locked.')

    def __init__(self, compass_dir, portal_type):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class Leave_Command_Left_Room(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.leave_command() when the player uses
it to leave the current dungeon room.
    """
    __slots__ = 'compass_dir', 'portal_type'

    @property
    def message(self):
        return f'You leave the room via the {self.compass_dir} {self.portal_type}.'

    def __init__(self, compass_dir, portal_type):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class Leave_Command_Won_The_Game(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.leave_command() when the player
chances upon the door that is the exit to the dungeon. They have won the game;
when advgame.py receives this game state message it prints its message and then
exits the program.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You found the exit to the dungeon. You have won the game!'

    def __init__(self):
        pass


class Lock_Command_Dont_Possess_Correct_Key(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.lock_command() when the player tries
to lock a chest while they don't possess the chest key, or a door while they
don't possess the door key.
    """
    __slots__ = 'object_to_lock_title', 'key_needed',

    @property
    def message(self):
        return f'To lock the {self.object_to_lock_title} you need a {self.key_needed}.'

    def __init__(self, object_to_lock_title, key_needed):
        self.object_to_lock_title = object_to_lock_title
        self.key_needed = key_needed


class Lock_Command_Element_Not_Lockable(Game_State_Message):
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        # This message property returns a string that informs the player that
        # they tried to lock something that can't be locked (a corpse, creature,
        # doorway or item). It omits the direct article is the item is armor.
        if self.target_type == 'armor':
            return f"You can't lock the {self.target_title}; suits of {self.target_type} are not lockable."
        else:
            return f"You can't lock the {self.target_title}; {self.target_type}s are not lockable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class Lock_Command_Element_Has_Been_Locked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.lock_command() when the player
successfully locks a chest or door.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'You have locked the {self.target}.'

    def __init__(self, target):
        self.target = target


class Lock_Command_Element_Is_Already_Locked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.lock_command() when the player tries
to lock a chest or door that is already locked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already locked.'

    def __init__(self, target):
        self.target = target


class Lock_Command_Element_to_Lock_Not_Here(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.lock_command() when the player
specifies an object to lock that is not present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to lock.'

    def __init__(self, target_title):
        self.target_title = target_title


class Look_At_Command_Found_Container_Here(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.look_at_command() when the player
targets a chest or a corpse. If it's a chest and it's unlocked, the contents of
the chest are conveyed. If it's a corpse, the corpse's possessions are conveyed.
    """
    __slots__ = 'container_description', 'container_type', 'container', 'is_locked', 'is_closed'

    @property
    def message(self):
        # This message property handles looking at a chest or corpse. If it's
        # a chest, the property handles all possible combinations of is_locked
        # in (True, False, None) and is_closed in (True, False, None). If the
        # chest isn't locked or closed, it lists the chest's contents. If it's
        # a corpse, contents are listed. Since contents listing appears at
        # several points in the conditional, it's handled by a private property,
        # _contents (see below).
        if self.container_type == 'chest':
            if self.is_locked is True and self.is_closed is True:
                return f'{self.container_description} It is closed and locked.'
            elif self.is_locked is False and self.is_closed is True:
                return f'{self.container_description} It is closed but unlocked.'
            elif self.is_locked is False and self.is_closed is False:
                return f'{self.container_description} It is unlocked and open. {self._contents}'
            elif self.is_locked is True and self.is_closed is False:
                raise excpt.Internal_Exception('Look_At_Command_Found_Container_Here.message accessed to describe a chest '
                                         'with the impossible combination of is_locked = True and is_closed = False.')
            elif self.is_locked is None and self.is_closed is True:
                return f'{self.container_description} It is closed.'
            elif self.is_locked is None and self.is_closed is False:
                return f'{self.container_description} It is open. {self._contents}'
            elif self.is_locked is True and self.is_closed is None:
                return f'{self.container_description} It is locked.'
            elif self.is_locked is False and self.is_closed is None:
                return f'{self.container_description} It is unlocked.'
            else:  # None and None
                return self.container_description
        elif self.container_type == 'corpse':
            return f'{self.container_description} {self._contents}'

    # This property assembles a sentence listing off the items the container
    # has. It's implemented separately because several different outcomes of the
    # logic in the message property above can lead to conveying the container's
    # contents.

    @property
    def _contents(self):
        # A list of strings comprising the item title and qty for each item in sorted order by title is formed.
        contents_strs_tuple = tuple(f'{qty} {item.title}s' if qty > 1
                                   else f'an {item.title}' if item.title[0] in 'aeiou'
                                   else f'a {item.title}'
                                   for qty, item in sorted(self.container.values(), key=lambda arg: arg[1].title))
        # The list is condensed to a comma-separated string using a utility function.
        contents_str = util.join_str_seq_w_commas_and_conjunction(contents_strs_tuple, 'and')
        # If the list is zero-length, the message conveys that the container is empty.
        if len(contents_strs_tuple) == 0:
            return 'It is empty.' if self.container_type == 'chest' else 'They have nothing on them.'
        # Otherwise a container-specific framing str is used to convey the contents.
        elif self.container_type == 'chest':
            return f'It contains {contents_str}.'
        else:
            return f'They have {contents_str} on them.'

    def __init__(self, container):
        self.container = container
        self.container_description = container.description
        self.is_locked = container.is_locked
        self.is_closed = container.is_closed
        self.container_type = container.container_type
        if self.is_locked is True and self.is_closed is False:
            raise excpt.Internal_Exception(f'Container {container.internal_name} has is_locked = True and is_open = '
                                      'False, invalid combination of parameters.')


class Look_At_Command_Found_Creature_Here(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.look_command() when the player targets
a creature in the dungeon's current room.
    """
    __slots__ = 'creature_description',

    @property
    def message(self):
        return self.creature_description

    def __init__(self, creature_description):
        self.creature_description = creature_description


class Look_At_Command_Found_Door_or_Doorway(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.look_at_command() when the player
targets a door or doorway in the current dungeon room.
    """
    __slots__ = 'compass_dir', 'door'

    @property
    def message(self):
        # This message property combines the Door object's description, a
        # statement of which wall the door is on, and a statement of its
        # closed/locked status.
        closed_locked_str = ('It is closed and locked.' if self.door.is_closed and self.door.is_locked
                             else 'It is closed but unlocked.' if self.door.is_closed and not self.door.is_locked
                             else 'It is open.')
        return f'{self.door.description} It is set in the {self.compass_dir} wall. {closed_locked_str}'

    def __init__(self, compass_dir, door):
        self.compass_dir = compass_dir
        self.door = door


class Look_At_Command_Found_Item_or_Items_Here(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.look_at_command() when the player
targets an item that is present on the floor of current room or in their
inventory or in a chest or on a corpse's person as specified by the player. It
conveys the item's description attribute and specifies how many are present.
    """
    __slots__ = 'item_description', 'item_qty'

    @property
    def message(self):
        # This message property combines the given item description with a
        # sentence indicating how many there are and where they are: on the
        # floor, in the character's inventory, in a chest or on a corpse's
        # person.
        to_be_conjug = 'is' if self.item_qty == 1 else 'are'
        item_location = ('on the floor' if self.container_title == 'floor'
                         else 'in your inventory' if self.container_title == 'inventory'
                         else f'in the {self.container_title}' if self.container_type == 'chest'
                         else f"on the {self.container_title}'s person")
        return f'{self.item_description} There {to_be_conjug} {self.item_qty} {item_location}.'

    def __init__(self, item_description, item_qty, container_title, container_type=None):
        self.item_description = item_description
        self.item_qty = item_qty
        self.container_title = container_title
        self.container_type = container_type


class Look_At_Command_Found_Nothing(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.look_at_command() when the player
targets an item that can't be found where they said it was.
    """
    __slots__ = 'item_title', 'item_location', 'location_type'

    @property
    def message(self):
        # This message property conveys that an item doesn't exist where the
        # player looked for it: in a chest, on a corpse, on the floor or in
        # their inventory. If the call wasn't specific, a generic 'You see no X
        # here' is returned.
        if self.item_location is not None:
            if self.location_type == 'chest':
                return f'The {self.item_location} has no {self.item_title} in it.'
            elif self.location_type == 'corpse':
                return f'The {self.item_location} has no {self.item_title} on its person.'
            elif self.item_location == 'floor':
                return f'There is no {self.item_title} on the floor.'
            elif self.item_location == 'inventory':
                return f'You have no {self.item_title} in your inventory.'
            else:
                raise excpt.Internal_Exception(f'Location type {self.location_type} not recognized.')
        else:
            return f'You see no {self.item_title} here.'

    def __init__(self, item_title, item_location=None, location_type=None):
        self.item_title = item_title
        self.item_location = item_location
        self.location_type = location_type


class Open_Command_Element_Not_Openable(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.open_command() when the player
attempts to open a corpse, creature, doorway or item.
    """
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        # This message conveys that a corpse, creature, door or item isn't
        # openable, handling armor separately so 'suits of [armor title]' can
        # be used.
        if self.target_type == 'armor':
            return f"You can't open the {self.target_title}; suits of {self.target_type} are not openable."
        else:
            return f"You can't open the {self.target_title}; {self.target_type}s are not openable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class Open_Command_Element_Has_Been_Opened(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.open_command() when the player
successfully opens a chest or door.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'You have opened the {self.target}.'

    def __init__(self, target):
        self.target = target


class Open_Command_Element_Is_Already_Open(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.open_command() when the player targets
a door or chest that is already open.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already open.'

    def __init__(self, target):
        self.target = target


class Open_Command_Element_Is_Locked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.open_command() when the player targets
a door or chest that is locked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is locked.'

    def __init__(self, target):
        self.target = target


class Open_Command_Element_to_Open_Not_Here(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.open_command() when the player targets
a door or chest that is not present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to open.'

    def __init__(self, target_title):
        self.target_title = target_title


class Pick_Lock_Command_Element_Not_Unlockable(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_lock_command() when the player
attempts to pick a lock on a corpse, creature, doorway or item.
    """
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        # This message conveys that a corpse, creature, door or item isn't
        # unlockable, handling armor separately so 'suits of [armor title]' can
        # be used.
        if self.target_type == 'armor':
            return f"You can't pick a lock on the {self.target_title}; suits of {self.target_type} are not unlockable."
        else:
            return f"You can't pick a lock on the {self.target_title}; {self.target_type}s are not unlockable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class Pick_Lock_Command_Target_Has_Been_Unlocked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_lock_command() when the player
successfully unlocks the chest or door.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You have unlocked the {self.target_title}.'

    def __init__(self, target_title):
        self.target_title = target_title


class Pick_Lock_Command_Target_Not_Found(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_lock_command() when the player
targets a door or chest that is not present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'This room has no {self.target_title}.'

    def __init__(self, target_title):
        self.target_title = target_title


class Pick_Lock_Command_Target_Not_Locked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_lock_command() when the player
targets a door or chest that is not locked.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'The {self.target_title} is not locked.'

    def __init__(self, target_title):
        self.target_title = target_title


class Pick_Up_Command_Cant_Pick_Up_Chest_Corpse_Creature_or_Door(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_up_command() when the player has
specifies a game element that is a chest, corpse, creature or door and can't be
picked up.
    """
    __slots__ = 'element_type', 'element_title'

    @property
    def message(self):
        return f"You can't pick up the {self.element_title}: can't pick up {self.element_type}s!"

    def __init__(self, element_type, element_title):
        self.element_type = element_type
        self.element_title = element_title


class Pick_Up_Command_Item_Not_Found(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_up_command() when the player
targets an item to pick up that is not present in the current dungeon room. If
they meant to acquire an item from a chest or corpse, they need to say `TAKE
<item name> FROM <corpse or chest name>`.
    """
    __slots__ = 'item_title', 'amount_attempted', 'items_here'

    @property
    def message(self):
        # This message property assembles a string that indicates the specified
        # item isn't present. The object is initialized with the items_here
        # attribute of the current room object, and if it's non-null the items
        # are listed as alternatives.
        item_pluralizer = 's' if self.amount_attempted > 1 else ''
        if self.items_here:
            items_here_str_tuple = tuple(f'{item_count} {item_title}s' if item_count > 1
                                         else f'an {item_title}' if item_title[0] in 'aeiou'
                                         else f'a {item_title}'
                                             for item_count, item_title in self.items_here)
            items_here_str = util.join_str_seq_w_commas_and_conjunction(items_here_str_tuple, 'and')
            return f'You see no {self.item_title}{item_pluralizer} here. However, there is {items_here_str} here.'
        else:
            return f'You see no {self.item_title}{item_pluralizer} here.'

    def __init__(self, item_title, amount_attempted, *items_here):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.items_here = tuple(sorted(items_here, key=operator.itemgetter(1)))


class Pick_Up_Command_Item_Picked_Up(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_up_command() when the player
successfully acquires an item from the floor of the current dungeon room.
    """
    __slots__ = 'item_title', 'pick_up_amount', 'amount_had'

    @property
    def message(self):
        # This message property assembles a sentence conveying that one or more
        # items were picked up, and mentioning how many the player character now
        # has. It picks the article or determiner and the use of a pluralizing s
        # suffix.
        picked_up_indir_artcl_or_qty = (str(self.pick_up_amount) if self.pick_up_amount > 1
                                        else 'an' if self.item_title[0] in 'aeiou'
                                        else 'a')
        picked_up_pluralizer = 's' if self.pick_up_amount > 1 else ''
        amt_had_indir_artcl_or_qty = (str(self.amount_had) if self.amount_had > 1
                                      else 'an' if self.item_title[0] in 'aeiou'
                                      else 'a')
        amt_had_pluralizer = 's' if self.amount_had > 1 else ''
        return (f'You picked up {picked_up_indir_artcl_or_qty} {self.item_title}{picked_up_pluralizer}. You have '
                f'{amt_had_indir_artcl_or_qty} {self.item_title}{amt_had_pluralizer}.')

    def __init__(self, item_title, pick_up_amount, amount_had):
        self.item_title = item_title
        self.pick_up_amount = pick_up_amount
        self.amount_had = amount_had


class Pick_Up_Command_Quantity_Unclear(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_up_command() when the player has
entered an ungrammatical sentence that is ambiguous as to how many it means to
specify.
    """

    @property
    def message(self):
        return 'Amount to pick up unclear. How many do you mean?'

    def __init__(self):
        pass


class Pick_Up_Command_Trying_to_Pick_Up_More_than_Is_Present(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.pick_up_command() when the player has
targeted an item that is present, but has specified a quantity to pick up that
is greater than the number of that item that is present in the current dungeon
room.
    """
    __slots__ = 'item_title', 'amount_attempted', 'amount_present'

    @property
    def message(self):
        return f"You can't pick up {self.amount_attempted} {self.item_title}s. Only {self.amount_present} is here."

    def __init__(self, item_title, amount_attempted, amount_present):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_present = amount_present


class Put_Command_Amount_Put(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player
successfully places one or more items in a chest or on a corpse's person.
    """
    __slots__ = 'item_title', 'container_title', 'container_type', 'amount_put', 'amount_left'

    @property
    def message(self):
        # This message property constructs a pair of sentences that convey how
        # many of what item was put where, and how many the player character has
        # left.
        amount_put_pluralizer = 's' if self.amount_put > 1 else ''
        amount_left_pluralizer = 's' if self.amount_left > 1 or not self.amount_left else ''
        container_placed_location_clause = (f'in the {self.container_title}' if self.container_type == 'chest'
                              else f"on the {self.container_title}'s person")
        amount_left_clause = (f'{self.amount_left} {self.item_title}{amount_left_pluralizer} left' if self.amount_left != 0
                        else f'no more {self.item_title}{amount_left_pluralizer}')
        return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} {container_placed_location_clause}. '
                f'You have {amount_left_clause}.')

    def __init__(self, item_title, container_title, container_type, amount_put, amount_left):
        self.item_title = item_title
        self.container_title = container_title
        self.container_type = container_type
        self.amount_put = amount_put
        self.amount_left = amount_left


class Put_Command_Item_Not_in_Inventory(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player attempts
to put an item in a chest or on a corpse that is not in their inventory.
    """
    __slots__ = 'amount_attempted', 'item_title'

    @property
    def message(self):
        if self.amount_attempted > 1:
            return f"You don't have any {self.item_title}s in your inventory."
        else:
            return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title, amount_attempted):
        self.amount_attempted = amount_attempted
        self.item_title = item_title


class Put_Command_Quantity_Unclear(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player writes
an ungrammatical sentence that is ambiguous as to how many of the item they mean
to put in the chest or on the corpse.
    """

    @property
    def message(self):
        return 'Amount to put unclear. How many do you mean?'

    def __init__(self):
        pass


class Put_Command_Trying_to_Put_More_than_You_Have(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() when the player tries to
put a quantity of an item in a chest or on a corpse that that is more than they
have in their inventory.
    """
    __slots__ = 'item_title', 'amount_present'

    @property
    def message(self):
        pluralizer = 's' if self.amount_present > 1 else ''
        return f'You only have {self.amount_present} {self.item_title}{pluralizer} in your inventory.'

    def __init__(self, item_title, amount_present):
        self.item_title = item_title
        self.amount_present = amount_present


class Quit_Command_Have_Quit_The_Game(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.quit_command() when the player
executes the command. When advgame.py receives this object, it prints the
message and then exits the program.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You have quit the game.'

    def __init__(self):
        pass


class Reroll_Command_Name_or_Class_Not_Set(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.reroll_command() when the player tries
to use it before they have set their name and class. The player's ability scores
aren't rolled until they've chosen a name and class, and therefore can't be
rerolled yet.
    """
    __slots__ = 'character_name', 'character_class'

    @property
    def message(self):
        # This mesage property constructs a string that indicates which of the
        # two commands, SET NAME and SET CLASS, the player needs to use before
        # REROLL can be used.
        reroll_str = "Your character's stats haven't been rolled yet, so there's nothing to reroll."
        set_name_str = 'SET NAME <name> to set your name'
        set_class_str = 'SET CLASS <Warrior, Thief, Mage or Priest> to select your class'
        if self.character_name is None and self.character_class is None:
            return reroll_str + f' Use {set_name_str} and {set_class_str}.'
        elif self.character_class is None:
            return reroll_str + f' Use {set_class_str}.'
        else:
            return reroll_str + f' Use {set_name_str}.'

    def __init__(self, character_name, character_class):
        self.character_name = character_name
        self.character_class = character_class


class Set_Class_Command_Class_Set(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.set_class_command() when the player
selects a class from the choices Warrior, Thief, Mage and Priest.
    """
    __slots__ = 'class_str',

    @property
    def message(self):
        return f'Your class, {self.class_str}, has been set.'

    def __init__(self, class_str):
        self.class_str = class_str


class Set_Class_Command_Invalid_Class(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.set_class_command() when the player
specifies a class that is not one of Warrior, Thief, Mage or Priest.
    """
    __slots__ = 'bad_class',

    @property
    def message(self):
        return f"'{self.bad_class}' is not a valid class choice. Please choose Warrior, Thief, Mage, or Priest."

    def __init__(self, bad_class):
        self.bad_class = bad_class


class Set_Name_Command_Invalid_Part(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.set_name_command() when the player
tries to set a name that is not one or more alphabetic titelcased strings.
    """
    __slots__ = 'name_part',

    @property
    def message(self):
        return f'The name {self.name_part} is invalid; must be a capital letter followed by lowercase letters.'

    def __init__(self, name_part):
        self.name_part = name_part


class Set_Name_Command_Name_Set(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.set_name_command() when the player
sets a name.
    """
    __slots__ = 'name',

    @property
    def message(self):
        return f"Your name, '{self.name}', has been set."

    def __init__(self, name):
        self.name = name


class Status_Command_Output(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.status_command() when the player
executes it. The status line conveyed by the message property includes the
player's current and total hit points, current and total mana points if they're
a spellcaster, their attack and damage, their armor class, their armor equipped
if not a Mage, their shield equipped if a Warrior or Priest, their Wand equipped
if a Mage, and their Weapon equipped.
    """
    __slots__ = ('hit_points', 'hit_point_total', 'armor_class', 'attack_bonus', 'damage', 'mana_points',
                 'mana_point_total', 'armor', 'shield', 'weapon', 'wand', 'character_class')

    @property
    def message(self):
        # This long message property assembles a detailed listing of the player
        # character's status, including current & max hit points, current & max
        # mana points (if a spellcaster), armor class, attack & damage, and
        # items equipped.

        # The player character's hit points.
        hp_str = f'Hit Points: {self.hit_points}/{self.hit_point_total}'

        if self.character_class in ('Mage', 'Priest'):
            # The player character's mana points if they're a Mage or a Priest.
            mp_str = f'Mana Points: {self.mana_points}/{self.mana_point_total}'

        # The player character's attack bonus and damage. If they don't have a
        # weapon equipped, or (if they're a Mage) don't have a wand equipped, a
        # message to that effect is shown isntead.
        if self.weapon or self.character_class == 'Mage' and self.wand:
            atk_plussign = '+' if self.attack_bonus >= 0 else ''
            atk_dmg_str = f'Attack: {atk_plussign}{self.attack_bonus} ({self.damage} damage)'
        elif self.character_class == 'Mage':
            atk_dmg_str = 'Attack: no wand or weapon equipped'
        else:
            atk_dmg_str = 'Attack: no weapon equipped'

        # The player character's armor class.
        ac_str = f'Armor Class: {self.armor_class}'

        # The armor, shield, wand and weapon equipped strings are built. If
        # an item is present it's included (since it must be allowed to the
        # class), but a '<item type>: none' value is only included if the player
        # character is of a class that can equip items of that type.
        armor_str = (f'Armor: {self.armor}' if self.armor
                     else 'Armor: none' if self.character_class != 'Mage'
                     else '')
        shield_str = (f'Shield: {self.shield}' if self.shield
                      else 'Shield: none' if self.character_class in ('Warrior', 'Priest')
                      else '')
        wand_str = (f'Wand: {self.wand}' if self.wand
                    else 'Wand: none' if self.character_class == 'Mage'
                    else '')
        weapon_str = (f'Weapon: {self.weapon}' if self.weapon else 'Weapon: none')

        # The previously defined components of the status line are assembled
        # into three hyphen-separated displays.
        points_display = f'{hp_str} - {mp_str}' if self.character_class in ('Mage', 'Priest') else hp_str
        stats_display = f'{atk_dmg_str} - {ac_str}'
        equip_display = weapon_str
        equip_display += f' - {wand_str}' if wand_str else ''
        equip_display += f' - {armor_str}' if armor_str else ''
        equip_display += f' - {shield_str}' if shield_str else ''

        # The three displays are combined in a bar-separated string and returned.
        return f'{points_display} | {stats_display} | {equip_display}'

    def __init__(self, armor_class, attack_bonus, damage, weapon, hit_points, hit_point_total, armor=None, shield=None,
                 wand=None, mana_points=None, mana_point_total=None, character_class=None):
        self.armor_class = armor_class
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.armor = armor
        self.shield = shield
        self.weapon = weapon
        self.wand = wand
        self.hit_points = hit_points
        self.hit_point_total = hit_point_total
        self.mana_points = mana_points
        self.mana_point_total = mana_point_total
        self.character_class = character_class


class Take_Command_Item_Not_Found_in_Container(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.take_command() if the player specifies
an item to take from a chest that is not in that chest or from a corpse that is
not on the corpse.
    """
    __slots__ = 'container_title', 'amount_attempted', 'container_type', 'item_title'

    @property
    def message(self):
        # This message property assembles a single sentence which conveys that
        # the container mentioned doesn't contain the item sought.
        base_str = f"The {self.container_title} doesn't have"
        indirect_article_or_determiner = ('any' if self.amount_attempted > 1
                               else 'an' if self.item_title[0] in 'aeiou'
                               else 'a')
        container_clause = 'in it' if self.container_type == 'chest' else 'on them'
        pluralizer = 's' if self.amount_attempted > 1 else ''
        return f'{base_str} {indirect_article_or_determiner} {self.item_title}{pluralizer} {container_clause}.'

    def __init__(self, container_title, amount_attempted, container_type, item_title):
        self.container_title = container_title
        self.amount_attempted = amount_attempted
        self.container_type = container_type
        self.item_title = item_title


class Take_Command_Item_or_Items_Taken(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.take_command() when the player
successfully acquires an item from a chest or corpse.
    """
    __slots__ = 'container_title', 'item_title', 'amount_taken'

    @property
    def message(self):
        # This message property assembles a sentence which conveys that the
        # player character took an amount of an item from a chest or corpse.
        indirect_article_or_quantity = (str(self.amount_taken) if self.amount_taken > 1
                                        else 'an' if self.item_title[0] in 'aeiou'
                                        else 'a')
        pluralizer = 's' if self.amount_taken > 1 else ''
        return f'You took {indirect_article_or_quantity} {self.item_title}{pluralizer} from the {self.container_title}.'

    def __init__(self, container_title, item_title, amount_taken):
        self.container_title = container_title
        self.item_title = item_title
        self.amount_taken = amount_taken


class Take_Command_Quantity_Unclear(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.take_command() when the player writes
an ungrammatical sentence that is ambiguous as to how many of the item the
player means to take.
    """

    @property
    def message(self):
        return 'Amount to take unclear. How many do you want?'

    def __init__(self):
        pass


class Take_Command_Trying_to_Take_More_than_Is_Present(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.take_command() when the player
specifies a quantity of an item to take from a chest that is more than is
present in that chest, or from a corpse that is more than is present on that
corpse.
    """
    __slots__ = 'container_title', 'container_type', 'item_title', 'amount_attempted', 'amount_present'

    @property
    def message(self):
        # This message property assembles a sentence conveying that the quantity
        # of the item sought can't be taken from the container because only a
        # smaller quantity is there. The lowest value self.amount_present can
        # be is 1, and self.amount_attempted must be greater than that if this
        # error is being returned, so we know that self.amount_attempted > 1.
        item_specifier = f'suits of {self.item_title}' if self.item_type == 'armor' else f'{self.item_title}s'
        return (f"You can't take {self.amount_attempted} {item_specifier} from the {self.container_title}. Only "
                f'{self.amount_present} is there.')

    def __init__(self, container_title, container_type, item_title, item_type, amount_attempted, amount_present):
        self.container_title = container_title
        self.container_type = container_type
        self.item_title = item_title
        self.item_type = item_type
        self.amount_attempted = amount_attempted
        self.amount_present = amount_present


class Unequip_Command_Item_Not_Equipped(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.unequip_command() when the player
tries to unequip an item that is not equipped.
    """
    __slots__ = 'item_specified_title', 'item_specified_type', 'item_present_title'

    @property
    def message(self):
        # This message property assembles 1-2 sentences that indicate the
        # specified item can't be unequipped because it wasn't equipped to begin
        # with.
        if self.item_specified_type is not None:

            # This convenience function returns the correct verb to use to refer
            # to using an item of the given type.
            item_usage_verb = util.usage_verb(self.item_specified_type, gerund=True)
            article_or_suit = ('a suit of' if self.item_specified_type == 'armor'
                               else 'an' if self.item_specified_title[0] in 'aeiou'
                               else 'a')
            return_str = f"You're not {item_usage_verb} {article_or_suit} {self.item_specified_title}."

            # If the player character has another item of that type equipped
            # instead, a sentence referring to it is included, so the player can
            # amend their EQUIP command.
            if self.item_present_title:
                return_str += f" You're {item_usage_verb} {article_or_suit} {self.item_present_title}."
        else:
            # The returning method didn't know what type the specified item was,
            # so I use a generic reply.
            return_str = f"You don't have a {self.item_specified_title} equipped."
        return return_str

    def __init__(self, item_specified_title, item_specified_type=None, item_present_title=None):
        self.item_specified_title = item_specified_title
        self.item_specified_type = item_specified_type
        self.item_present_title = item_present_title


class Unlock_Command_Dont_Possess_Correct_Key(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.unlock_command() when the player tries
to unlock a door while not possessing the door key, or unlock a chest while not
possessing the chest key.
    """
    __slots__ = 'object_to_unlock_title', 'key_needed',

    @property
    def message(self):
        return f'To unlock the {self.object_to_unlock_title} you need a {self.key_needed}.'

    def __init__(self, object_to_unlock_title, key_needed):
        self.object_to_unlock_title = object_to_unlock_title
        self.key_needed = key_needed


class Unlock_Command_Element_Not_Unlockable(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.unlock_command() when the player
attempts to unlock a corpse, creature, doorway or item.
    """
    __slots__ = 'target_title', 'target_type'

    @property
    def message(self):
        singular_item = f'the suit of {self.target_title}' if self.target_type == 'armor' else f'the {self.target_title}'
        item_pluralized = f'suits of {self.target_type}' if self.target_type == 'armor' else f'{self.target_type}s'
        return f"You can't unlock {singular_item}; {item_pluralized} are not unlockable."

    def __init__(self, target_title, target_type):
        self.target_title = target_title
        self.target_type = target_type


class Unlock_Command_Element_Has_Been_Unlocked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.unlock_command() when the player
successfully unlocks a chest or door.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'You have unlocked the {self.target}.'

    def __init__(self, target):
        self.target = target


class Unlock_Command_Element_Is_Already_Unlocked(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.unlock_command() when the player tries
to unlock a door or chest that is already unlocked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already unlocked.'

    def __init__(self, target):
        self.target = target


class Unlock_Command_Element_to_Unlock_Not_Here(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.unlock_command() when the player tries
to unlock a door or chest that is not present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to unlock.'

    def __init__(self, target_title):
        self.target_title = target_title


class Various_Commands_Ambiguous_Door_Specifier(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.lock_command(), .unlock_command(),
.open_command() and .close_command() when the player has used a specifier for a
door that matches more than one door in the current dungeon room; for example,
saying 'unlock wooden door' when there's two wooden doors.
    """
    __slots__ = 'compass_dirs', 'door_or_doorway', 'door_type'

    @property
    def message(self):
        # This message property assembles a pair of sentences that describe
        # every door in the room that matches the user's ambiguous command and
        # asks them which one they mean.
        door_type = self.door_type.replace('_', ' ') if self.door_type else None
        message_str = 'More than one door in this room matches your command. Do you mean '
        if door_type is not None:
            door_str_list = [f'the {compass_dir} {door_type}' for compass_dir in self.compass_dirs]
        else:
            door_str_list = [f'the {compass_dir} {self.door_or_doorway}' for compass_dir in self.compass_dirs]
        message_str += util.join_str_seq_w_commas_and_conjunction(door_str_list, 'or') + '?'
        return message_str

    def __init__(self, compass_dirs, door_or_doorway, door_type):
        self.compass_dirs = compass_dirs
        self.door_or_doorway = door_or_doorway
        self.door_type = door_type


class Various_Commands_Container_Is_Closed(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command() or .take_command() when
the player tries to access a chest that is closed.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is closed.'

    def __init__(self, target):
        self.target = target


class Various_Commands_Container_Not_Found(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.put_command(), .take_command(), or
.look_at_command() when trying to look in a chest that isn't present in the
current dungeon room, or check a corpse that isn't present in the current
dungeon room.
    """
    __slots__ = 'container_not_found_title', 'container_present_title'

    @property
    def message(self):
        return_str = f'There is no {self.container_not_found_title} here.'
        if self.container_present_title is not None:
            return_str += f' However, there *is* a {self.container_present_title} here.'
        return return_str

    def __init__(self, container_not_found_title, container_present_title=None):
        self.container_not_found_title = container_not_found_title
        self.container_present_title = container_present_title


class Various_Commands_Display_Rolled_Stats(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.set_name_command() or
.set_class_command() when both name and class have been set, or by
.reroll_command(). It displays the character's randomly generated ability
scores.
    """
    __slots__ = 'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'

    @property
    def message(self):
        return (f'Your ability scores are '
                f'Strength\u00A0{self.strength}, '
                f'Dexterity\u00A0{self.dexterity}, '
                f'Constitution\u00A0{self.constitution}, '
                f'Intelligence\u00A0{self.intelligence}, '
                f'Wisdom\u00A0{self.wisdom}, '
                f'Charisma\u00A0{self.charisma}.\n\n'
                f'Would you like to reroll or begin the game?')

    def __init__(self, strength, dexterity, constitution, intelligence, wisdom, charisma):
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma


class Various_Commands_Door_Not_Present(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.close_command(), .leave_command(),
.lock_command(), .look_at_command(), .open_command(), .pick_lock_command(), or
.unlock_command() when the player specifies a door that is not present in the
current dungeon room.
    """
    __slots__ = 'compass_dir', 'portal_type'

    @property
    def message(self):
        # This message property assembles a sentence which informs the player
        # that the door they specified in their command is not present in this
        # room.
        return_str = 'This room does not have a'
        if self.compass_dir is not None and self.portal_type is not None:
            # This concatenation varies slightly to turn 'a' into 'an' if the
            # word after it is 'east'.
            return_str += (f'n {self.compass_dir} {self.portal_type}.' if self.compass_dir == 'east'
                           else f' {self.compass_dir} {self.portal_type}.')
        elif self.portal_type is not None:
            return_str += f'a {self.portal_type}.'
        elif self.compass_dir is not None:
            # This concatenation varies slightly to turn 'a' into 'an' if the
            # word after it is 'east'.
            return_str += (f'n {self.compass_dir} door or doorway.' if self.compass_dir == 'east'
                           else f' {self.compass_dir} door or doorway.')
        return return_str

    def __init__(self, compass_dir, portal_type=None):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class Various_Commands_Entered_Room(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.leave_command() when the player leaves
a room and enters a new one, or by .begin_command() when the player starts the
game in the first room. It prints the room description, lists the items on the
floor if any, mentions any chest or creature, and lists the exits to the room by
compass direction.
    """
    __slots__ = 'room',

    @property
    def message(self):
        # This message property assembles a room description, mentioning
        # any chest, corpse, or creatures, items on the floor, and each of
        # the doors, by building a list of sentences, then joining them and
        # returning the string.
        message_list = list()

        # It starts with the room description.
        message_list.append(self.room.description)

        # If there's a container here, a sentence mentioning it is added to the list.
        if self.room.container_here is not None:
            message_list.append(f'You see a {self.room.container_here.title} here.')

        # If there's a creature here, a sentence mentioning them is added to the list.
        if self.room.creature_here is not None:
            message_list.append(f'There is a {self.room.creature_here.title} in the room.')

        # If the items_here attribute is a Items_Multi_State object, its
        # contents are assembled into a list, joined into a comma-separated
        # string, and that string is added to the list.
        if self.room.items_here is not None:
            room_items = list()
            for item_qty, item in self.room.items_here.values():
                quantifier = str(item_qty) if item_qty > 1 else 'an' if item.title[0] in 'aeiou' else 'a'
                pluralizer = 's' if item_qty > 1 else ''
                room_items.append(f'{quantifier} {item.title}{pluralizer}')
            items_here_str = util.join_str_seq_w_commas_and_conjunction(room_items, 'and')
            message_list.append(f'You see {items_here_str} on the floor.')

        # A list of door titles and directions is assembled, joined into a
        # string, and that string is added to the list.
        door_list = list()
        for compass_dir in ('north', 'east', 'south', 'west'):
            dir_attr = compass_dir + '_door'
            door = getattr(self.room, dir_attr, None)
            if door is None:
                continue
            door_ersatz_title = door.door_type.replace('_', ' ')
            door_list.append(f'a {door_ersatz_title} to the {compass_dir}')
        door_str = 'There is ' + util.join_str_seq_w_commas_and_conjunction(door_list, 'and') + '.'
        message_list.append(door_str)

        # The list of sentences is joined into a string and returned.
        return ' '.join(message_list)

    def __init__(self, room):
        self.room = room


class Various_Commands_Foe_Death(Game_State_Message):
    __slots__ = 'creature_title',

    @property
    def message(self):
        return f'The {self.creature_title} is slain.'

    def __init__(self, creature_title):
        self.creature_title = creature_title


class Various_Commands_Item_Equipped(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.begin_game() or .equip_command() when
the player equips an item. It lists the item equipped and mentions how the
relevant game parameters have changed as a result.
    """
    __slots__ = ('item_title', 'item_type', 'attack_bonus', 'damage', 'armor_class'
                'change_text')

    @property
    def message(self):
        # This message property assembles a sentence that informs the user of
        # the new wand, weapon, armor or shield they've equipped. If it's a suit
        # of armor or shield, their new armor class is mentioned. If it's a
        # weapon or wand, their new attack bonus and damage is mentioned.
        item_usage_verb = util.usage_verb(self.item_type, gerund=True)
        referent = ('a suit of' if self.item_type == 'armor'
                    else 'an' if self.item_title[0] in 'aeiou'
                    else 'a')
        if self.attacking_with is not None:
            item_usage_verb = util.usage_verb(self.attacking_with.item_type, gerund=True)
            referent = ('an' if self.attacking_with.title[0] in 'aeiou' else 'a')
            return_str = f"You're {item_usage_verb} {referent} {self.attacking_with.title}. "
        else:
            return_str = f"You're now {item_usage_verb} {referent} {self.item_title}. "
        if self.armor_class is not None:
            return_str += f'Your armor class is now {self.armor_class}.'
        else:  # attack_bonus is not None and damage != ''
            plussign = '+' if self.attack_bonus >= 0 else ''
            tense = 'now ' if not self.attacking_with else ''
            return_str += (f'Your attack bonus is {tense}{plussign}{self.attack_bonus} '
                           f'and your {self.item_type} damage is {tense}{self.damage}.')
        return return_str

    def __init__(self, item_title, item_type, attack_bonus=None, damage='', armor_class=None, attacking_with=None):
        self.item_title = item_title
        self.item_type = item_type
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.armor_class = armor_class
        self.attacking_with = attacking_with


class Various_Commands_Item_Unequipped(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.equip_command(), .unequip_command(),
or .drop_command(). It's returned by .unequip_command() when the player unequips
an item; .equip_command() returns it if the player already had an item equipped
in that slot to convey the previous item's removal; and .drop_command() returns
it if the item the character dropped was equipped and they no longer have any of
the item in their inventory.
    """
    __slots__ = ('item_title', 'item_type', 'changed_value_1', 'value_type_1', 'changed_value_2', 'value_type_2',
                'change_text')

    @property
    def message(self):
        # This message property constructs a series of sentences that inform the
        # player that they unequipped an item, and what the changes to their
        # stats are and if they can still attack. Nota Bene: if a Mage equips
        # a wand, they will always use it instead of their weapon. If a Mage
        # unequips their wand their attack and damage won't change; and if they
        # unequip their wand their new attack and damage are from the weapon
        # they still have equipped.
        item_usage_verb = util.usage_verb(self.item_type, gerund=True)
        referent = 'a suit of' if self.item_type == 'armor' else 'an' if self.item_title[0] in 'aeiou' else 'a'
        return_str = f"You're no longer {item_usage_verb} {referent} {self.item_title}."
        if self.armor_class is not None:

            # If the player just unequipped armor or a weapon, their armor class
            # has changed.
            return_str += (f' Your armor class is now {self.armor_class}.')
        elif self.attack_bonus is not None and self.damage is not None:

            # Only a mage can still have an attack bonus and damage after
            # unequipping something.
            plussign = '+' if self.attack_bonus >= 0 else ''
            if self.now_attacking_with:
                implement = self.now_attacking_with
                return_str += f" You're now attacking with your {self.now_attacking_with.title}."
                tense = 'now '
            elif self.attacking_with:
                implement = self.attacking_with
                return_str += f" You're attacking with your {implement.title}."
                tense = ''
            return_str += (f' Your attack bonus is {tense}{plussign}{self.attack_bonus} and your '
                           f'{implement.title} damage is {tense}{self.damage}.')
        elif self.now_cant_attack:

            # Any other class that just unequipped a weapon gets this message.
            return_str += " You now can't attack."
        return return_str

    def __init__(self, item_title, item_type, attack_bonus=None, damage=None, armor_class=None, attacking_with=None,
                       now_attacking_with=None, now_cant_attack=False):
        self.item_title = item_title
        self.item_type = item_type
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.armor_class = armor_class
        self.attacking_with = attacking_with
        self.now_attacking_with = now_attacking_with
        self.now_cant_attack = now_cant_attack


class Various_Commands_Underwent_Healing_Effect(Game_State_Message):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_command() or
.cast_spell_command(). It's returned by .drink_command() if the player drinks a
health potion; and it's returned by the .cast_spell_command() if the player is a
Priest and they successfully cast a healing spell.
    """
    __slots__ = 'amount_healed', 'current_hit_points', 'hit_point_total',

    @property
    def message(self):
        # This message property handles three cases:
        # * The player regained hit points and now has their maximum hit points.
        # * The player regained hit points but are still short of their maximum.
        # * The player didn't regain any hit points because their hit points were
        #   already at maximum.
        return_str = (f'You regained {self.amount_healed} hit points.' if self.amount_healed != 0
                      else "You didn't regain any hit points.")
        if self.current_hit_points == self.hit_point_total:
            return_str += " You're fully healed!"
        return_str += f' Your hit points are {self.current_hit_points}/{self.hit_point_total}.'
        return return_str

    def __init__(self, amount_healed, current_hit_points, hit_point_total):
        self.amount_healed = amount_healed
        self.current_hit_points = current_hit_points
        self.hit_point_total = hit_point_total
