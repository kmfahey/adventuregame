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


__all__ = "various", "unlock", "unequip", "take", "status", "setname", "setcls", "reroll", "quit", "put", "pickup", "open_",

__all__ += ("GameStateMessage", "Stmsg_CommandBadSyntax", "Stmsg_CommandClassRestricted", "Stmsg_CommandNotAllowedNow", "Stmsg_CommandNotRecognized", "Stmsg_Attack_AttackHit",
            "Stmsg_Attack_AttackMissed", "Stmsg_Attack_OpponentNotFound", "Stmsg_Attack_YouHaveNoWeaponOrWandEquipped", "Stmsg_Batkby_AttackedAndHit",
            "Stmsg_Batkby_AttackedAndNotHit", "Stmsg_Batkby_CharacterDeath", "Stmsg_Begin_GameBegins", "Stmsg_Begin_NameOrClassNotSet", "Stmsg_Cstspl_CastDamagingSpell",
            "Stmsg_Cstspl_CastHealingSpell", "Stmsg_Cstspl_InsufficientMana", "Stmsg_Cstspl_NoCreatureToTarget", "Stmsg_Close_ElementNotCloseable",
            "Stmsg_Close_ElementHasBeenClosed", "Stmsg_Close_ElementIsAlreadyClosed", "Stmsg_Close_ElementToCloseNotHere", "Stmsg_Drink_DrankManaPotion",
            "Stmsg_Drink_DrankManaPotion_when_Not_A_Spellcaster", "Stmsg_Drink_ItemNotDrinkable", "Stmsg_Drink_ItemNotInInventory", "Stmsg_Drink_TriedToDrinkMoreThanPossessed",
            "Stmsg_Drink_QuantityUnclear", "Stmsg_Drop_DroppedItem", "Stmsg_Drop_QuantityUnclear", "Stmsg_Drop_TryingToDropItemYouDontHave",
            "Stmsg_Drop_TryingToDropMoreThanYouHave", "Stmsg_Equip_ClassCantUseItem", "Stmsg_Equip_NoSuchItemInInventory", "Stmsg_Help_CommandNotRecognized",
            "Stmsg_Help_DisplayCommands", "Stmsg_Help_DisplayHelpForCommand", "Stmsg_Inven_DisplayInventory", "Stmsg_Leave_DoorIsLocked", "Stmsg_Leave_LeftRoom",
            "Stmsg_Leave_WonTheGame", "Stmsg_Lock_DontPossessCorrectKey", "Stmsg_Lock_ElementNotUnlockable", "Stmsg_Lock_ElementHasBeenUnlocked",
            "Stmsg_Lock_ElementIsAlreadyUnlocked", "Stmsg_Lock_ElementToUnlockNotHere")


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


# adventuregame/statemsgs/castsp.py

class Stmsg_Cstspl_CastDamagingSpell(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.cast_spell_command() when the player,
while playing a Mage, has cast a damaging spell. Like Stmsg_Attack_AttackHit,
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


class Stmsg_Cstspl_CastHealingSpell(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.cast_spell_command() when used by
a Priest. It doesn't need to mention how much damage was healed because it's
followed by a Stmsg_Various_UnderwentHealingEffect instance that does that.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You cast a healing spell on yourself.'

    def __init__(self):
        pass


class Stmsg_Cstspl_InsufficientMana(GameStateMessage):
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


class Stmsg_Cstspl_NoCreatureToTarget(GameStateMessage):
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


# adventuregame/statemsgs/close.py

class Stmsg_Close_ElementNotCloseable(GameStateMessage):
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


class Stmsg_Close_ElementHasBeenClosed(GameStateMessage):
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


class Stmsg_Close_ElementIsAlreadyClosed(GameStateMessage):
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


class Stmsg_Close_ElementToCloseNotHere(GameStateMessage):
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


# adventuregame/statemsgs/drink.py

class Stmsg_Drink_DrankManaPotion(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.drink_coomand() when the player
uses it to drink a mana potion. It is only returned if the player's
character is a Mage or Priest. If they're playing a Warrior or Thief, a
Stmsg_Drink_DrankManaPotion_when_Not_A_Spellcaster object is returned
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


class Stmsg_Drink_DrankManaPotion_when_Not_A_Spellcaster(GameStateMessage):
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


class Stmsg_Drink_ItemNotDrinkable(GameStateMessage):
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


class Stmsg_Drink_ItemNotInInventory(GameStateMessage):
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


class Stmsg_Drink_TriedToDrinkMoreThanPossessed(GameStateMessage):
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


class Stmsg_Drink_QuantityUnclear(GameStateMessage):
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


# adventuregame/statemsgs/drop.py

class Stmsg_Drop_DroppedItem(GameStateMessage):
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


class Stmsg_Drop_QuantityUnclear(GameStateMessage):
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


class Stmsg_Drop_TryingToDropItemYouDontHave(GameStateMessage):
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
        article_or_pronoun = 'any' if self.amount_attempted > 1 else 'an' if self.item_title[0] in 'aeiou' else 'a'
        pluralizer = '' if self.amount_attempted == 1 else 's'
        return f"You don't have {article_or_pronoun} {self.item_title}{pluralizer} in your inventory."

    def __init__(self, item_title, amount_attempted):
        self.item_title = item_title
        self.amount_attempted = amount_attempted


class Stmsg_Drop_TryingToDropMoreThanYouHave(GameStateMessage):
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


# adventuregame/statemsgs/equip.py

class Stmsg_Equip_ClassCantUseItem(GameStateMessage):
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
        # Stmsg_Drop_DroppedItem.message, it omits the indirect article if
        # the item is a suit of armor.
        item_usage_verb = usage_verb(self.item_type, gerund=False)
        pluralizer = 's' if self.item_type != 'armor' else ''
        return f"{self.character_class}s can't {item_usage_verb} {self.item_title}{pluralizer}."

    def __init__(self, character_class, item_title, item_type):
        self.character_class = character_class
        self.item_title = item_title
        self.item_type = item_type


class Stmsg_Equip_NoSuchItemInInventory(GameStateMessage):
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


# adventuregame/statemsgs/help_.py

class Stmsg_Help_CommandNotRecognized(GameStateMessage):
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
        return_lines.extend((join_str_seq_w_commas_and_conjunction(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return '\n'.join(return_lines)

    def __init__(self, command_attempted, commands_available):
        self.command_attempted = command_attempted
        self.commands_available = commands_available


class Stmsg_Help_DisplayCommands(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.help_command() when the player calls
it with no arguments; it displays all the commands in the game and prompts the
player to ask for help with one of them.
    """
    __slots__ = 'commands_available', 'game_started'

    @property
    def message(self):
        if self.game_started:
            return_lines = ['The list of commands available during the game is:', '']
        else:
            return_lines = ['The list of commands available before game start is:', '']
        return_lines.extend((join_str_seq_w_commas_and_conjunction(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return '\n'.join(return_lines)

    def __init__(self, commands_available, game_started=True):
        self.commands_available = commands_available
        self.game_started = game_started


class Stmsg_Help_DisplayHelpForCommand(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.help_command() when the player asks
for help with a specific command. It summarizes the syntax for them and prints
an informative blurb about the command.
    """
    __slots__ = 'command', 'syntax_tuple', 'instructions',

    @property                   #
    def message(self):          #
        # Like Stmsg_CommandBadSyntax, this message property accepts syntax
        # outlines from adventuregame.processor.COMMANDS_SYNTAX and assembles
        # them into a list of valid usages, using unicode nonbreaking
        # spaces so the usage examples aren't broken across lines by
        # adventuregame.utilities.textwrapper().
        syntax_str_list = [f"'{self.command}\u00A0{syntax_entry}'" if syntax_entry else f"'{self.command}'"
                               for syntax_entry in self.syntax_tuple]
        return_lines = [f'Help for the {self.command} command:', '']
        return_lines.extend(('Usage: ' + join_str_seq_w_commas_and_conjunction(syntax_str_list, 'or'), ''))
        return_lines.extend((self.instructions, ''))
        return '\n'.join(return_lines)

    def __init__(self, command, syntax_tuple=None, instructions=None):
        self.command = command
        self.syntax_tuple = syntax_tuple
        self.instructions = instructions


# adventuregame/statemsgs/inven.py

class Stmsg_Inven_DisplayInventory(GameStateMessage):
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
        return 'You have ' + join_str_seq_w_commas_and_conjunction(display_strs_list, 'and') + ' in your inventory.'

    def __init__(self, inventory_contents_list):
        self.inventory_contents = inventory_contents_list


# adventuregame/statemsgs/leave.py

class Stmsg_Leave_DoorIsLocked(GameStateMessage):
    """
This class implements an object that is returned by
adventuregame.processor.Command_Processor.leave_command() if the player tries to
leave through a door that is locked.
    """
    __slots__ = 'compass_dir', 'portal_type'

    @property
    def message(self):
        return (f"You can't leave the room via the {self.compass_dir} {self.portal_type}. The {self.portal_type} is "
                 'locked.')

    def __init__(self, compass_dir, portal_type):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class Stmsg_Leave_LeftRoom(GameStateMessage):
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


class Stmsg_Leave_WonTheGame(GameStateMessage):
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


# adventuregame/statemsgs/lock.py

class Stmsg_Lock_DontPossessCorrectKey(GameStateMessage):
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


class Stmsg_Lock_ElementNotUnlockable(GameStateMessage):
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


class Stmsg_Lock_ElementHasBeenUnlocked(GameStateMessage):
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


class Stmsg_Lock_ElementIsAlreadyUnlocked(GameStateMessage):
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


class Stmsg_Lock_ElementToUnlockNotHere(GameStateMessage):
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


