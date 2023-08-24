#!/usr/bin/python32

"""
This module contains GameStateMessage and its numerous subclasses.
adventuregame.processor.Command_Processor.process() processes a natural
language command from the player and tail calls a command method of the
adventuregame.processor.Command_Processor object. It always returns a tuple
of GameStateMessage subclass objects; each one represents a single possible
outcome of a command. A GameStateMessage subclass has an __init__ method that
assigns keyword arguments to object attributes and a message property which
contains the logic for rendering the semantic value of the message object in
natural language.
"""

import abc
import operator

from adventuregame.exceptions import InternalError
from adventuregame.utility import join_str_seq_w_commas_and_conjunction, usage_verb


__name__ = 'adventuregame.statemsgs'


__all__ = "various", "unlock", "unequip", "take", "status", "setname", "setcls", "reroll", "quit", "put", "pickup", "open_", "lookat", "lock", "leave", "help_", "equip", "drop", "drink", "close", "castspl",

__all__ += ("GameStateMessage", "Stmsg_CommandBadSyntax", "Stmsg_CommandClassRestricted", "Stmsg_CommandNotAllowedNow", "Stmsg_CommandNotRecognized", "Stmsg_Attack_AttackHit",
            "Stmsg_Attack_AttackMissed", "Stmsg_Attack_OpponentNotFound", "Stmsg_Attack_YouHaveNoWeaponOrWandEquipped", "Stmsg_Batkby_AttackedAndHit",
            "Stmsg_Batkby_AttackedAndNotHit", "Stmsg_Batkby_CharacterDeath", "Stmsg_Begin_GameBegins", "Stmsg_Begin_NameOrClassNotSet")


class GameStateMessage(abc.ABC):
    """
This class is the abstract base class for all the game state message classes
in this module. It defines an abstract property message and an abstract method
__init__.
    """

    @property
    @abc.abstractmethod
    def message(self):
        """
The message property of a GameStateMessage subclass renders the data stored
in the object attributes to a natural language string which communicates the
semantic content of the object to the player. The message property is accessed
and printed by advgame.py.
        """
        pass

    @abc.abstractmethod
    def __init__(self, *argl, **argd):
        """
The __init__ method of a GameStateMessage subclass stores its keyword
arguments to object attributes, and performs no other task.
        """
        pass


# adventuregame/statemsgs/_common.py

class Stmsg_CommandBadSyntax(GameStateMessage):
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
        proper_syntax_options_str = join_str_seq_w_commas_and_conjunction(syntax_options, 'or')
        return f'{self.command.upper()} command: bad syntax. Should be {proper_syntax_options_str}.'

    def __init__(self, command, proper_syntax_options):
        self.command = command
        self.proper_syntax_options = proper_syntax_options


class Stmsg_CommandClassRestricted(GameStateMessage):
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
        class_str = join_str_seq_w_commas_and_conjunction(classes_plural, 'and')
        return f'Only {class_str} can use the {self.command.upper()} command.'

    def __init__(self, command, *classes):
        self.command = command
        self.classes = classes


class Stmsg_CommandNotAllowedNow(GameStateMessage):
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
        commands_str = join_str_seq_w_commas_and_conjunction(
                            tuple(command.upper().replace('_', ' ')
                                  for command in sorted(self.allowed_commands)),
                            'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun


class Stmsg_CommandNotRecognized(GameStateMessage):
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
        commands_str = join_str_seq_w_commas_and_conjunction(tuple(command.upper().replace('_', ' ') for command in sorted(self.allowed_commands)), 'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun


# adventuregame/statemsgs/attack.py

class Stmsg_Attack_AttackHit(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.attack_command() when the player's
attack connected with their foe. Because attack_command() always triggers the
hidden _be_attacked_by_command() pseudo-command, an Stmsg_Attack_AttackHit
object tracks if the foe was slain. If so, nothing relating to foe death is
conveyed; describing foe death is handled by the Stmsg_Various_FoeDeath
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
            return (f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage. The '
                    f'{self.creature_title} turns to attack!')
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


class Stmsg_Attack_AttackMissed(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.attack_command() when the player's
attack missed. Like Stmsg_Attack_AttackHit, it mentions the foe turning to
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


class Stmsg_Attack_OpponentNotFound(GameStateMessage):
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


class Stmsg_Attack_YouHaveNoWeaponOrWandEquipped(GameStateMessage):
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


# adventuregame/statemsgs/batkby.py

class Stmsg_Batkby_AttackedAndHit(GameStateMessage):
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


class Stmsg_Batkby_AttackedAndNotHit(GameStateMessage):
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


class Stmsg_Batkby_CharacterDeath(GameStateMessage):
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


# adventuregame/statemsgs/begingm.py

class Stmsg_Begin_GameBegins(GameStateMessage):
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


class Stmsg_Begin_NameOrClassNotSet(GameStateMessage):
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


import adventuregame.statemsgs.castspl as castspl # 22/27

import adventuregame.statemsgs.close as close # 21/27

import adventuregame.statemsgs.drink as drink # 20/27

import adventuregame.statemsgs.drop as drop # 19/27

import adventuregame.statemsgs.equip as equip # 18/27

import adventuregame.statemsgs.help_ as help_ # 17/27

import adventuregame.statemsgs.inven as inven # 16/27

import adventuregame.statemsgs.leave as leave # 15/27

import adventuregame.statemsgs.lock as lock # 14/27

import adventuregame.statemsgs.lookat as lookat # 13/27

import adventuregame.statemsgs.open_ as open_ # 12/27

import adventuregame.statemsgs.pklock as pklock # 11/27

import adventuregame.statemsgs.pickup as pickup # 11/27

import adventuregame.statemsgs.put as put # 10/27

import adventuregame.statemsgs.quit as quit # 9/27

import adventuregame.statemsgs.reroll as reroll # 8/27

import adventuregame.statemsgs.setcls as setcls # 7/27

import adventuregame.statemsgs.setname as setname # 6/27

import adventuregame.statemsgs.status as status # 5/27

import adventuregame.statemsgs.take as take # 4/27

import adventuregame.statemsgs.unequip as unequip # 3/27

import adventuregame.statemsgs.unlock as unlock # 2/27

import adventuregame.statemsgs.various as various # 1/27


