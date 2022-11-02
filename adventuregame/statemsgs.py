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
import math
import operator

from adventuregame.utility import usage_verb, join_str_seq_w_commas_and_conjunction
from adventuregame.exceptions import Internal_Exception

__name__ = 'adventuregame.gamestatemessages'


class Game_State_Message(abc.ABC):
    """
    This class is the abstract base class for all the game state message classes
    in this module. It defines an abstract property message and an abstract
    method __init__.
    """

    @property
    @abc.abstractmethod
    def message(self):
        """
        The message property of a Game_State_Message subclass renders the data
        stored in the object attributes to a natural language string which
        communicates the semantic content of the object to the player. The
        message property is accessed and printed by advgame.py.
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
    This class implements an error object that is returned by command methods
    of adventuregame.processor.Command_Processor when incorrect syntax for a
    command has been used.
    """

    @property
    def message(self):
        command = self.command.upper().replace(' ', '\u00A0')
        syntax_options = tuple(f"'{command}\u00A0{syntax_option}'"
                                if syntax_option
                                else f"'{command}'"
                                for syntax_option in self.proper_syntax_options)
        if len(syntax_options) == 1:
            proper_syntax_options_str = syntax_options[0]
        elif len(syntax_options) == 2:
            proper_syntax_options_str = ' or '.join(syntax_options)
        else:
            proper_syntax_options_str = syntax_options[0]
            for index in range(1, len(syntax_options)):
                proper_syntax_options_str += ', '
                if index == len(syntax_options) - 1:
                    proper_syntax_options_str += 'or '
                proper_syntax_options_str += syntax_options[index]
        return f'{self.command.upper()} command: bad syntax. Should be {proper_syntax_options_str}.'

    def __init__(self, command, *proper_syntax_options):
        self.command = command
        self.proper_syntax_options = proper_syntax_options


class Command_Class_Restricted(Game_State_Message):
    """
    This class implements an error object that is returned by
    adventuregame.processor.Command_Processor.processor() when the player has
    used a command that is restricted to a class other than their own. (For
    example, only thieves can use PICK LOCK.)
    """
    __slots__ = 'command', 'classes',

    @property
    def message(self):
        class_str = ''
        classes_plural = [class_str + 's' if class_str != 'thief' else 'thieves' for class_str in self.classes]
        if len(classes_plural) == 1:
            class_str = classes_plural[0]
        elif len(classes_plural) == 2:
            class_str = ' and '.join(classes_plural)
        else:
            class_str = ', '.join(classes_plural[:-1])
            class_str += ', and ' + classes_plural[-1]
        return f'Only {class_str} can use the {self.command.upper()} command.'

    def __init__(self, command, *classes):
        self.command = command
        self.classes = classes


class Command_Not_Allowed_Now(Game_State_Message):
    """
    This class implements an error object that is returned by
    adventuregame.processor.Command_Processor.processor() when the
    player has used a command that is not allowed in the current game
    mode. The game has two modes: pregame, when name and class are
    chosen and ability scores are rolled, and in-game, when the player
    plays the game. Different command sets are allowed in each mode.
    See adventuregame.processor.Command_Processor.pregame_commands and
    adventuregame.processor.Command_Processor.ingame_commands for the lists.
    """
    __slots__ = 'command', 'allowed_commands', 'game_has_begun'

    @property
    def message(self):
        game_state_str = 'before game start' if not self.game_has_begun else 'during the game'
        message_str = f"Command '{self.command}' not allowed {game_state_str}. "
        commands_str = join_str_seq_w_commas_and_conjunction(tuple(command.upper().replace('_', ' ') for command in sorted(self.allowed_commands)), 'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun


class Command_Not_Recognized(Game_State_Message):
    """
    This class implements an error object that is returned by
    adventuregame.processor.Command_Processor.processor() when a command was
    entered that is not known to the command processor.
    """
    __slots__ = 'command', 'allowed_commands', 'game_has_begun'

    @property
    def message(self):
        message_str = f"Command '{self.command}' not recognized. "
        game_state_str = 'before game start' if not self.game_has_begun else 'during the game'
        commands_str = join_str_seq_w_commas_and_conjunction(tuple(command.upper().replace('_', ' ') for command in sorted(self.allowed_commands)), 'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun


class Attack_Command_Attack_Hit(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.attack_command() when the
    player's attack connected with their foe. Because attack_command()
    alwayss triggers the hidden _be_attacked_by_command() pseudo-command, an
    Attack_Command_Attack_Hit object track if the foe was slain. If not, its
    message includes a clause about the foe turning to attack. If not, nothing
    relating to foe death is conveyed; describing foe death is handled by the
    Various_Commands_Foe_Death class.
    """
    __slots__ = 'creature_title', 'damage_done', 'creature_slain'

    @property
    def message(self):
        if self.creature_slain and self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage.'
        elif self.creature_slain and self.weapon_type == 'wand':
            return (f'A bolt of energy from your wand hits the {self.creature_title}! You did {self.damage_done} '
                    f'damage. The {self.creature_title} turns to attack!')
        elif not self.creature_slain and self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage.'
        else:  # not self.creature_slain and self.weapon_type == 'wand':
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
    attack missed. Like Attack_Command_Attack_Hit, it mentions the foe turning
    to attack, because an attack on a foe always leads to a counterattack if
    they live.
    """
    __slots__ = 'creature_title', 'weapon_type'

    @property
    def message(self):
        if self.weapon_type == 'weapon':
            return f'Your attack on the {self.creature_title} missed. It turns to attack!'
        else:
            return f'A bolt of energy from your wand misses the {self.creature_title}. It turns to attack!'

    def __init__(self, creature_title, weapon_type):
        self.creature_title = creature_title
        self.weapon_type = weapon_type


class Attack_Command_Opponent_Not_Found(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.attack_command() when the player
    has used an attack command that refers to a foe that is not present in the
    game's current room.
    """
    __slots__ = 'creature_title_given', 'opponent_present'

    @property
    def message(self):
        if self.opponent_present:
            return f"This room doesn't have a {self.creature_title_given}; but there is a {self.opponent_present}."
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
        if self.character_class == 'Mage':
            return "You have no wand or weapon equipped; you can't attack."
        else:
            return "You have no weapon equipped; you can't attack."

    def __init__(self, character_class):
        self.character_class = character_class


class Be_Attacked_by_Command_Attacked_and_Hit(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor._be_attacked_by_command() when the
    foe's counterattack connects. It conveys the damage done and how many hit
    points the player's character has left.
    """
    __slots__ = 'creature_title', 'damage_done', 'hit_points_left'

    @property
    def message(self):
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
    foe's counter attack killed the player's character. The game is now over,
    and advgame.py responds to receiving this object by printing its message and
    then exitting the program.
    """

    @property
    def message(self):
        return 'You have died!'

    def __init__(self):
        pass


class Begin_Game_Command_Game_Begins(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.begin_game_command() when the
    command executes successfully. The game has begun.
    """

    @property
    def message(self):
        return 'The game has begun!'

    def __init__(self):
        pass


class Begin_Game_Command_Name_or_Class_Not_Set(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.begin_game_command() when the
    player has used the BEGIN GAME command prematurely. The player must set a
    name and a class before the game can begin; this object is returned if they
    fail to.
    """
    __slots__ = 'character_name', 'character_class'

    @property
    def message(self):
        if not self.character_name and not self.character_class:
            return ('You need to set your character name and class before you begin the game. Use SET NAME <name> to '
                    'set your name and SET CLASS <Warrior, Thief, Mage or Priest> to select your class.')
        elif not self.character_name:
            return ('You need to set your character name before you begin the game. Use SET NAME <name> to set your '
                    'name.')
        else:  # not self.character_class:
            return ('You need to set your character class before you begin the game. Use SET CLASS <Warrior, Thief, '
                    'Mage or Priest> to select your class.')

    def __init__(self, character_name, character_class):
        self.character_name = character_name
        self.character_class = character_class


class Cast_Spell_Command_Cast_Damaging_Spell(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.cast_spell_command() when
    the player, while playing a Mage, has cast a damaging spell. Like
    Attack_Command_Attack_Hit, it tracks whether the foe was slain, and adds a
    "they turn to attack" sentence if not.
    """
    __slots__ = 'creature_title', 'damage_dealt'

    @property
    def message(self):
        if self.creature_slain:
            return (f'A magic missile springs from your gesturing hand and unerringly strikes the {self.creature_title}. '
                    f'You have done {self.damage_dealt} points of damage.')
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
    followed by a Various_Commands_Underwent_Healing_Effect instance that does
    that.
    """
    __slots__ = ()

    @property
    def message(self):
        return 'You cast a healing spell on yourself.'

    def __init__(self):
        pass


class Cast_Spell_Command_Insuffient_Mana(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.cast_spell_command() when the
    player tries to cast a spell with insufficient mana points.
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
    adventuregame.processor.Command_Processor.cast_spell_command() when the
    player uses the command in a room with no creature to attack.
    """
    __slots__ = ()

    @property
    def message(self):
        return "You can't cast magic missile here; there is no creature here to target."

    def __init__(self):
        pass


class Close_Command_Object_Has_Been_Closed(Game_State_Message):
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


class Close_Command_Object_Is_Already_Closed(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.close_command() when the closeable
    object the player targeted is already closed.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already closed.'

    def __init__(self, target):
        self.target = target


class Close_Command_Object_to_Close_Not_Here(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.close_command() when the player
    specifies a target to the command that is not present in the current room of
    the game.
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
        if self.amount_regained and self.current_mana_points == self.mana_point_total:
            return (f'You regained {self.amount_regained} mana points. You have full mana points! '
                    f'Your mana points are {self.current_mana_points}/{self.mana_point_total}.')
        elif self.amount_regained:
            return (f'You regained {self.amount_regained} mana points. Your mana points are '
                    f'{self.current_mana_points}/{self.mana_point_total}.')
        else:
            return (f"You didn't regain any mana points. Your mana points are "
                    f'{self.current_mana_points}/{self.mana_point_total}.')

    def __init__(self, amount_regained, current_mana_points, mana_point_total):
        self.amount_regained = amount_regained
        self.current_mana_points = current_mana_points
        self.mana_point_total = mana_point_total


class Drink_Command_Drank_Mana_Potion_when_Not_A_Spellcaster(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.drink_command() when the player
    drinks a mana potion but they're playing a Warrior or Thief and have no mana
    points to restore.
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
    adventuregame.processor.Command_Processor.drink_command() when the player
    tries to drink a potion that isn't in their inventory.
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
    specifies drinking a quantity of potions that is greater than the number
    they have in their inventory.
    """
    __slots__ = 'item_title', 'attempted_qty', 'possessed_qty'

    @property
    def message(self):
        return f"You can't drink {self.attempted_qty} {self.item_title}s. You only have {self.possessed_qty} of them."

    def __init__(self, item_title, attempted_qty, possessed_qty):
        self.item_title = item_title
        self.attempted_qty = attempted_qty
        self.possessed_qty = possessed_qty


class Drop_Command_Dropped_Item(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.drop_command() when the player
    successfully drops an item on the floor.
    """
    __slots__ = 'item_title', 'item_type', 'amount_dropped', 'amount_on_floor', 'amount_left'

    @property
    def message(self):
        # The amount dropped and the amount on the floor both must be nonzero, but the amount left may be zero.
        drop_qty_str, drop_qty_pluralizer = (('a ', '') if self.amount_dropped == 1 else (str(self.amount_dropped) + ' ', 's'))
        if drop_qty_str == 'a ' and self.item_type == 'armor':
            drop_qty_str = ''
        floor_qty_str, floor_qty_pluralizer = (('a ', '') if self.amount_on_floor == 1 else (str(self.amount_on_floor) + ' ', 's'))
        if floor_qty_str == 'a ' and self.item_type == 'armor':
            floor_qty_str = ''
        left_qty_pluralizer = ('' if self.amount_left == 1 else 's' if self.amount_left > 1 else None)

        if left_qty_pluralizer is not None:
            return (f'You dropped {drop_qty_str}{self.item_title}{drop_qty_pluralizer}. You see {floor_qty_str}'
                    f'{self.item_title}{floor_qty_pluralizer} here. You have {self.amount_left} {self.item_title}'
                    f'{left_qty_pluralizer} left.')
        else:
            return (f'You dropped {drop_qty_str}{self.item_title}{drop_qty_pluralizer}. You see {floor_qty_str}'
                    f'{self.item_title}{floor_qty_pluralizer} here. You have no {self.item_title}s left.')

    def __init__(self, item_title, item_type, amount_dropped, amount_on_floor, amount_left):
        self.item_title = item_title
        self.item_type = item_type
        self.amount_dropped = amount_dropped
        self.amount_on_floor = amount_on_floor
        self.amount_left = amount_left


class Drop_Command_Quantity_Unclear(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.drop_command() when the player
    writes an ungrammatical sentence that is ambiguous as to how many of the
    item they intend to target.
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
        if self.amount_attempted > 1:
            return f"You don't have any {self.item_title}s in your inventory."
        else:
            return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title, amount_attempted):
        self.item_title = item_title
        self.amount_attempted = amount_attempted


class Drop_Command_Trying_to_Drop_More_than_You_Have(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.drop_command() when the player
    specifies a quantity of a certain item to drop that is more than the
    quantity of that item that they actually possess.
    """
    __slots__ = 'item_title', 'amount_attempted', 'amount_had'

    @property
    def message(self):
        if self.amount_attempted > 1 and self.amount_had == 1:
            return f"You can't drop {self.amount_attempted} {self.item_title}s. You only have {self.amount_had} "\
                   f'{self.item_title} in your inventory.'
        else:   # self.amount_attempted > 1 and self.amount_had > 1
            return f"You can't drop {self.amount_attempted} {self.item_title}s. You only have {self.amount_had} "\
                   f'{self.item_title}s in your inventory.'

    def __init__(self, item_title, amount_attempted, amount_had):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_had = amount_had


class Equip_Command_Class_Cant_Use_Item(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.equip_command() when the player
    tries to equip an item that is not allowed for their class. As an example,
    a Mage would get this result if they tried to equip a suit of armor or a
    shield, and anyone besides a Mage would get this result if they tried to
    equip a wand.
    """
    __slots__ = 'character_class', 'item_title', 'item_type'

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_type, gerund=False)
        pluralizer = 's' if self.item_type != 'armor' else ''
        return f"{self.character_class}s can't {item_usage_verb} {self.item_title}{pluralizer}."

    def __init__(self, character_class, item_title, item_type):
        self.character_class = character_class
        self.item_title = item_title
        self.item_type = item_type


class Equip_Command_No_Such_Item_in_Inventory(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.equip_command() when the player
    tries to equip an item that they don't have in their inventory.
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
    adventuregame.processor.Command_Processor.help_command() when the player
    tries to get help with a command that is not in the game.
    """
    __slots__ = 'command_attempted', 'commands_available',

    @property
    def message(self):
        return_lines = [f"The command '{self.command_attempted.upper()}' is not recognized. "
                         'The full list of commands is:', '']
        return_lines.extend((join_str_seq_w_commas_and_conjunction(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return "\n".join(return_lines)

    def __init__(self, command_attempted, commands_available):
        self.command_attempted = command_attempted
        self.commands_available = commands_available


class Help_Command_Display_Commands(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.help_command() when the player
    calls it with no arguments; it displays all the commands in the game and
    prompts the player to ask for help with one of them.
    """
    __slots__ = 'commands_available', 

    @property
    def message(self):
        return_lines = [f'The full list of commands is:', '']
        return_lines.extend((join_str_seq_w_commas_and_conjunction(self.commands_available, 'and'), ''))
        return_lines.extend(('Which one do you want help with?', ''))
        return "\n".join(return_lines)

    def __init__(self, commands_available):
        self.commands_available = commands_available


class Help_Command_Display_Help_for_Command(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.help_command() when the player
    asks for help with a specific command. It summarizes the syntax for them and
    prints an informative blurb about the command.
    """
    __slots__ = 'command', 'syntax_tuple', 'instructions',

    @property                   # \u00A0 is a nonbreaking space. It's used to prevent
    def message(self):          # syntax examples from being broken across lines.
        syntax_str_list = [f"'{self.command}\u00A0{syntax_entry}'" if syntax_entry else f"'{self.command}'"
                               for syntax_entry in self.syntax_tuple]
        return_lines = [f'Help for the {self.command} command:', '']
        return_lines.extend((f'Usage: ' + join_str_seq_w_commas_and_conjunction(syntax_str_list, 'or'), ''))
        return_lines.extend((self.instructions, ''))
        return "\n".join(return_lines)

    def __init__(self, command, syntax_tuple=None, instructions=None):
        self.command = command
        self.syntax_tuple = syntax_tuple
        self.instructions = instructions


class Inventory_Command_Display_Inventory(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.inventory_command(). It lists all
    the items in the character's inventory by title and quantity. If they want
    more information they need to say 'LOOK AT <item title> IN INVENTORY'.
    """
    __slots__ = 'inventory_contents',

    @property
    def message(self):
        display_strs_list = list()
        for item_qty, item in self.inventory_contents:
            if item.item_type == 'armor' and item_qty == 1:
                display_strs_list.append(f'a suit of {item.title}')
            elif item.item_type == 'armor' and item_qty > 1:
                display_strs_list.append(f'{item_qty} suits of {item.title}')
            elif item_qty == 1 and item.title[0] in 'aeiou':
                display_strs_list.append(f'an {item.title}')
            elif item_qty == 1:
                display_strs_list.append(f'a {item.title}')
            else:
                display_strs_list.append(f'{item_qty} {item.title}s')
        return 'You have ' + join_str_seq_w_commas_and_conjunction(display_strs_list, 'and') + ' in your inventory.'

    def __init__(self, inventory_contents_list):
        self.inventory_contents = inventory_contents_list


class Leave_Command_Left_Room(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.leave_command() when the player
    uses it to leave the current dungeon room.
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
    chances upon the door that is the exit to the dungeon. They have won the
    game; when advgame.py receives this game state message it prints its message
    and then exits the program.
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
    adventuregame.processor.Command_Processor.lock_command() when the player
    tries to lock a chest while they don't possess the chest key, or a door
    while they don't possess the door key.
    """
    __slots__ = 'object_to_lock_title', 'key_needed',

    @property
    def message(self):
        return f'To lock the {self.object_to_lock_title} you need a {self.key_needed}.'

    def __init__(self, object_to_lock_title, key_needed):
        self.object_to_lock_title = object_to_lock_title
        self.key_needed = key_needed


class Lock_Command_Object_Has_Been_Locked(Game_State_Message):
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


class Lock_Command_Object_Is_Already_Locked(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.lock_command() when the player
    tries to lock a chest or door that is already locked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already locked.'

    def __init__(self, target):
        self.target = target


class Lock_Command_Object_to_Lock_Not_Here(Game_State_Message):
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
    targets a chest or a corpse. If it's a chest and it's unlocked, the contents
    of the chest are conveyed. If it's a corpse, the corpse's possessions are
    conveyed.
    """
    __slots__ = 'container_description', 'container_type', 'container', 'is_locked', 'is_closed'

    @property
    def message(self):
        if self.container_type == 'chest':
            if self.is_locked is True and self.is_closed is True:
                return f'{self.container_description} It is closed and locked.'
            elif self.is_locked is False and self.is_closed is True:
                return f'{self.container_description} It is closed but unlocked.'
            elif self.is_locked is False and self.is_closed is False:
                return f'{self.container_description} It is unlocked and open. {self._contents}'
            # `self.is_locked is True and self.is_closed is False` is not a possible outcome of these tests because
            # it's an invalid combination, and is checked for in __init__. If that is the combination of booleans, an
            # exception is raised.
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
        content_qty_obj_pairs = sorted(self.container.values(), key=lambda arg: arg[1].title)
        contents_str_tuple = tuple('a ' + item.title if qty == 1 else str(qty) + ' ' + item.title + 's'
                                       for qty, item in content_qty_obj_pairs)
        if self.container_type == 'chest':
            if len(contents_str_tuple) == 0:
                return 'It is empty.'
            else:
                return 'It contains ' + join_str_seq_w_commas_and_conjunction(contents_str_tuple, 'and') + '.'
        else:
            if len(contents_str_tuple) == 0:
                return 'They have nothing on them.'
            else:
                return 'They have ' + join_str_seq_w_commas_and_conjunction(contents_str_tuple, 'and') + ' on them.'

    def __init__(self, container):
        self.container = container
        self.container_description = container.description
        self.is_locked = container.is_locked
        self.is_closed = container.is_closed
        self.container_type = container.container_type
        if self.is_locked is True and self.is_closed is False:
            raise Internal_Exception(f'Container {container.internal_name} has is_locked = True and is_open = '
                                      'False, invalid combination of parameters.')


class Look_At_Command_Found_Creature_Here(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.look_command() when the player
    targets a creature in the dungeon's current room.
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
        door_or_doorway = 'doorway' if self.door.door_type == 'doorway' else 'door'
        descr_str = (f'This {door_or_doorway} is set into the {self.compass_dir} wall of the room. '
                     f'{self.door.description}')
        if self.door.closeable:
            if self.door.is_closed and self.door.is_locked:
                descr_str += ' It is closed and locked.'
            elif self.door.is_closed and not self.door.is_locked:
                descr_str += ' It is closed but unlocked.'
            else:
                descr_str += ' It is open.'
        return descr_str

    def __init__(self, compass_dir, door):
        self.compass_dir = compass_dir
        self.door = door


class Look_At_Command_Found_Item_or_Items_Here(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.look_at_command() when the player
    targets an item that is present on the floor of current room or in their
    inventory or in a chest or on a corpse's person as specified by the player.
    It conveys the item's description attribute and specifies how many are
    present.
    """
    __slots__ = 'item_description', 'item_qty'

    @property
    def message(self):
        if self.item_qty > 1:
            return f'{self.item_description} You see {self.item_qty} here.'
        else:
            return self.item_description

    def __init__(self, item_description, item_qty):
        self.item_description = item_description
        self.item_qty = item_qty


class Look_At_Command_Found_Nothing(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.look_at_command() when the player
    targets an item that can't be found where they said it was.
    """
    __slots__ = 'item_title', 'item_container', 'container_type'

    @property
    def message(self):
        if self.item_container is not None:
            if self.container_type == 'chest':
                return f'The {self.item_container} has no {self.item_title} in it.'
            elif self.container_type == 'corpse':
                return f'The {self.item_container} has no {self.item_title} on it.'
            else:
                return f'You have no {self.item_title} in your inventory.'
        else:
            return f'You see no {self.item_title} here.'

    def __init__(self, item_title, item_container=None, container_type=None):
        self.item_title = item_title


class Open_Command_Object_Has_Been_Opened(Game_State_Message):
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


class Open_Command_Object_Is_Already_Open(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.open_command() when the player
    targets a door or chest that is already open.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already open.'

    def __init__(self, target):
        self.target = target


class Open_Command_Object_Is_Locked(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.open_command() when the player
    targets a door or chest that is locked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is locked.'

    def __init__(self, target):
        self.target = target


class Open_Command_Object_to_Open_Not_Here(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.open_command() when the player
    targets a door or chest that is not present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f'You found no {self.target_title} here to open.'

    def __init__(self, target_title):
        self.target_title = target_title


class Pick_Lock_Command_Target_Cant_Be_Unlocked_or_Not_Found(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.pick_lock_command() when the
    player specifies a door or chest that is either not unlockable or isn't
    present in the current dungeon room.
    """
    __slots__ = 'target_title',

    @property
    def message(self):
        return f"The {self.target_title} is not found or can't be unlocked."

    def __init__(self, target_title):
        self.target_title = target_title


class Pick_Lock_Command_Target_Has_Been_Unlocked(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.pick_lock_command() when the
    player successfully unlocks the chest or door.
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
    adventuregame.processor.Command_Processor.pick_lock_command() when the
    player targets a door or chest that is not present in the current dungeon
    room.
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
    adventuregame.processor.Command_Processor.pick_lock_command() when the
    player targets a door or chest that is not locked.
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
    adventuregame.processor.Command_Processor.pick_up_command() when the player
    has specifies a game element that is a chest, corpse, creature or door and
    can't be picked up.
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
    targets an item to pick up that is not present in the current dungeon room.
    If they meant to acquire an item from a chest or corpse, they need to say
    `TAKE <item name> FROM <corpse or chest name>`.
    """
    __slots__ = 'item_title', 'amount_attempted', 'items_here'

    @property
    def message(self):
        item_pluralizer = 's' if self.amount_attempted > 1 else ''
        if self.items_here:
            items_here_str_tuple = tuple(f'a {item_title}' if item_count == 1 else f'{item_count} {item_title}s'
                                         for item_count, item_title in self.items_here)
            items_here_str = join_str_seq_w_commas_and_conjunction(items_here_str_tuple, 'and')
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
        if self.pick_up_amount == 1 and self.amount_had == 1:
            return f'You picked up a {self.item_title}. You have 1 {self.item_title}.'
        elif self.pick_up_amount == 1 and self.amount_had > 1:
            return f'You picked up a {self.item_title}. You have {self.amount_had} {self.item_title}s.'
        else:
            return f'You picked up {self.pick_up_amount} {self.item_title}s. You have {self.amount_had} '\
                   f'{self.item_title}s.'

    def __init__(self, item_title, pick_up_amount, amount_had):
        self.item_title = item_title
        self.pick_up_amount = pick_up_amount
        self.amount_had = amount_had


class Pick_Up_Command_Quantity_Unclear(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.pick_up_command() when the player
    has entered an ungrammatical sentence that is ambiguous as to how many it
    means to specify.
    """

    @property
    def message(self):
        return 'Amount to pick up unclear. How many do you mean?'

    def __init__(self):
        pass


class Pick_Up_Command_Trying_to_Pick_Up_More_than_Is_Present(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.pick_up_command() when the player
    has targeted an item that is present, but has specified a quantity to pick
    up that is greater than the number of that item that is present in the
    current dungeon room.
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
        amount_put_pluralizer = 's' if self.amount_put > 1 else ''
        amount_left_pluralizer = 's' if self.amount_left > 1 or not self.amount_left else ''
        if self.amount_left and self.container_type == 'chest':
            return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} in the {self.container_title}.'
                    f' You have {self.amount_left} {self.item_title}{amount_left_pluralizer} left.')
        elif not self.amount_left and self.container_type == 'chest':
            return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} in the {self.container_title}.'
                    f' You have no more {self.item_title}{amount_left_pluralizer}.')
        elif self.amount_left and self.container_type == 'corpse':
            return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} on the '
                    f"{self.container_title}'s person. You have {self.amount_left} "
                    f'{self.item_title}{amount_left_pluralizer} left.')
        else:  # not self.amount_left and self.container_type == 'corpse':
            return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} on the '
                    f"{self.container_title}'s person. You have no more {self.item_title}{amount_left_pluralizer}.")

    def __init__(self, item_title, container_title, container_type, amount_put, amount_left):
        self.item_title = item_title
        self.container_title = container_title
        self.container_type = container_type
        self.amount_put = amount_put
        self.amount_left = amount_left


class Put_Command_Item_Not_in_Inventory(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.put_command() when the player
    attempts to put an item in a chest or on a corpse that is not in their
    inventory.
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
    adventuregame.processor.Command_Processor.put_command() when the player
    writes an ungrammatical sentence that is ambiguous as to how many of the
    item they mean to put in the chest or on the corpse.
    """

    @property
    def message(self):
        return 'Amount to put unclear. How many do you mean?'

    def __init__(self):
        pass


class Put_Command_Trying_to_Put_More_than_You_Have(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.put_command() when the player
    tries to put a quantity of an item in a chest or on a corpse that that is
    more than they have in their inventory.
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
    adventuregame.processor.Command_Processor.reroll_command() when the player
    tries to use it before they have set their name and class. The player's
    ability scores aren't rolled until they've chosen a name and class, and
    therefore can't be rerolled yet.
    """
    __slots__ = 'character_name', 'character_class'

    @property
    def message(self):
        if not self.character_name and not self.character_class:
            return ("Your character's stats haven't been rolled yet, so there's nothing to reroll. Use SET NAME "
                    '<name> to set your name and SET CLASS <Warrior, Thief, Mage or Priest> to select your class.')
        elif not self.character_name:
            return ("Your character's stats haven't been rolled yet, so there's nothing to reroll. Use SET NAME "
                    '<name> to set your name.')
        else:  # not self.character_class:
            return ("Your character's stats haven't been rolled yet, so there's nothing to reroll. Use SET CLASS "
                    '<Warrior, Thief, Mage or Priest> to select your class.')

    def __init__(self, character_name, character_class):
        self.character_name = character_name
        self.character_class = character_class


class Set_Class_Command_Class_Set(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.set_class_command() when the
    player selects a class from the choices Warrior, Thief, Mage and Priest.
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
    adventuregame.processor.Command_Processor.set_class_command() when the
    player specifies a class that is not one of Warrior, Thief, Mage or Priest.
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
    player's current and total hit points, current and total mana points if
    they're a spellcaster, their attack and damage, their armor class, their
    armor equipped if not a Mage, their shield equipped if a Warrior or Priest,
    their Wand equipped if a Mage, and their Weapon equipped.
    """
    __slots__ = ('hit_points', 'hit_point_total', 'armor_class', 'attack_bonus', 'damage', 'mana_points',
                 'mana_point_total', 'armor', 'shield', 'weapon', 'wand', 'character_class')

    @property
    def message(self):
        hp_str = f'Hit Points: {self.hit_points}/{self.hit_point_total}'
        if self.mana_points:
            mp_str = f'Mana Points: {self.mana_points}/{self.mana_point_total}'
        armor_str = f'Armor: {self.armor}' if self.armor else 'Armor: none' if self.character_class != 'Mage' else ''
        shield_str = f'Shield: {self.shield}' if self.shield else 'Shield: none' if self.character_class in ('Warrior', 'Priest') else ''
        if self.weapon or self.character_class == 'Mage' and self.wand:
            atk_plussign = '+' if self.attack_bonus >= 0 else ''
            atk_dmg_str = f'Attack: {atk_plussign}{self.attack_bonus} ({self.damage} damage)'
        elif self.character_class == 'Mage':
            atk_dmg_str = 'Attack: no wand or weapon equipped'
        else:
            atk_dmg_str = 'Attack: no weapon equipped'
        wand_str = f'Wand: {self.wand}' if self.wand else 'Wand: none' if self.character_class == 'Mage' else ''
        weapon_str = f'Weapon: {self.weapon}' if self.weapon else 'Weapon: none'
        ac_str = f'Armor Class: {self.armor_class}'
        points_display = f'{hp_str} - {mp_str}' if self.mana_points else hp_str
        stats_display = f'{atk_dmg_str} - {ac_str}'
        equip_display = f'{wand_str} - ' if wand_str else ''
        equip_display += weapon_str
        equip_display += f' - {armor_str}' if self.character_class != 'Mage' else ''
        equip_display += f' - {shield_str}' if self.character_class in ('Warrior', 'Priest') else ''
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
    adventuregame.processor.Command_Processor.take_command() if the player
    specifies an item to take from a chest that is not in that chest or from a
    corpse that is not on the corpse.
    """
    __slots__ = 'container_title', 'amount_attempted', 'container_type', 'item_title'

    @property
    def message(self):
        if self.container_type == 'chest' and (self.amount_attempted == 1 or self.amount_attempted is math.nan):
            return f"The {self.container_title} doesn't have a {self.item_title} in it."
        elif self.container_type == 'chest' and self.amount_attempted > 1:
            return f"The {self.container_title} doesn't have any {self.item_title}s in it."
        elif self.container_type == 'corpse' and (self.amount_attempted == 1 or self.amount_attempted is math.nan):
            return f"The {self.container_title} doesn't have a {self.item_title} on them."
        else:  # self.container_type == 'corpse' and self.amount_attempted > 1:
            return f"The {self.container_title} doesn't have any {self.item_title}s on them."

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
        if self.amount_taken > 1:
            return f'You took {self.amount_taken} {self.item_title}s from the {self.container_title}.'
        else:
            return f'You took a {self.item_title} from the {self.container_title}.'

    def __init__(self, container_title, item_title, amount_taken):
        self.container_title = container_title
        self.item_title = item_title
        self.amount_taken = amount_taken


class Take_Command_Quantity_Unclear(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.take_command() when the player
    writes an ungrammatical sentence that is ambiguous as to how many of the
    item the player means to take.
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
        return (f"You can't take {self.amount_attempted} {self.item_title}s from the {self.container_title}. Only "
                f'{self.amount_present} is there.')

    def __init__(self, container_title, container_type, item_title, amount_attempted, amount_present):
        self.container_title = container_title
        self.container_type = container_type
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_present = amount_present


class Unequip_Command_Item_Not_Equipped(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.unequip_command() when the player
    tries to unequip an item that is not equipped.
    """
    __slots__ = 'item_asked_title', 'item_asked_type', 'item_present_title'

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_asked_type, gerund=True)
        indirect_article = 'a ' if self.item_asked_type != 'armor' else ''
        if self.item_asked_type and self.item_present_title:
            return f"You're not {item_usage_verb} {indirect_article}{self.item_asked_title}. You're {item_usage_verb} "\
                   f'{indirect_article}{self.item_present_title}.'
        elif self.item_asked_type:
            return f"You're not {item_usage_verb} {indirect_article}{self.item_asked_title}."
        else:
            return f"You don't have a {self.item_asked_title} equipped."

    def __init__(self, item_asked_title, item_asked_type=None, item_present_title=None):
        self.item_asked_title = item_asked_title
        self.item_asked_type = item_asked_type
        self.item_present_title = item_present_title


class Unlock_Command_Dont_Possess_Correct_Key(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.unlock_command() when the player
    tries to unlock a door while not possessing the door key, or unlock a chest
    while not possessing the chest key.
    """
    __slots__ = 'object_to_unlock_title', 'key_needed',

    @property
    def message(self):
        return f'To unlock the {self.object_to_unlock_title} you need a {self.key_needed}.'

    def __init__(self, object_to_unlock_title, key_needed):
        self.object_to_unlock_title = object_to_unlock_title
        self.key_needed = key_needed


class Unlock_Command_Object_Has_Been_Unlocked(Game_State_Message):
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


class Unlock_Command_Object_Is_Already_Unlocked(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.unlock_command() when the player
    tries to unlock a door or chest that is already unlocked.
    """
    __slots__ = 'target',

    @property
    def message(self):
        return f'The {self.target} is already unlocked.'

    def __init__(self, target):
        self.target = target


class Unlock_Command_Object_to_Unlock_Not_Here(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.unlock_command() when the player
    tries to unlock a door or chest that is not present in the current dungeon
    room.
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
    .open_command() and .close_command() when the player has used a specifier
    for a door that matches more than one door in the current dungeon room; for
    example, saying 'unlock wooden door' when there's two wooden doors.
    """
    __slots__ = 'compass_dirs', 'door_or_doorway', 'door_type'

    @property
    def message(self):
        door_type = self.door_type.replace('_', ' ') if self.door_type else None
        message_str = "More than one door in this room matches your command. Do you mean "
        door_str_list = list()
        for compass_dir in self.compass_dirs:
            if door_type is not None:
                door_str_list.append(f'the {compass_dir} {door_type}')
            else:
                door_str_list.append(f'the {compass_dir} {self.door_or_doorway}')
        message_str += join_str_seq_w_commas_and_conjunction(door_str_list, 'or') + '?'
        return message_str

    def __init__(self, compass_dirs, door_or_doorway, door_type):
        self.compass_dirs = compass_dirs
        self.door_or_doorway = door_or_doorway
        self.door_type = door_type


class Various_Commands_Container_Is_Closed(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.put_command() or .take_command()
    when the player tries to access a chest that is closed.
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
        if self.container_present_title is not None:
            return f'There is no {self.container_not_found_title} here. However, there *is* a '\
                   f'{self.container_present_title} here.'
        else:
            return f'There is no {self.container_not_found_title} here.'

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
        return (f'Your ability scores are Strength {self.strength}, Dexterity {self.dexterity}, Constitution '
                f'{self.constitution}, Intelligence {self.intelligence}, Wisdom {self.wisdom}, Charisma {self.charisma}'
                '.\nWould you like to reroll or begin game?')

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
    .lock_command(), .look_at_command(), .open_command(), .pick_lock_command(),
    or .unlock_command() when the player specifies a door that is not present in
    the current dungeon room.
    """
    __slots__ = 'compass_dir', 'portal_type'

    @property
    def message(self):
        if self.compass_dir is not None and self.portal_type is not None:
            return f'This room does not have a {self.compass_dir} {self.portal_type}.'
        elif self.portal_type is not None:
            return f'This room does not have a {self.portal_type}.'
        elif self.compass_dir is not None:
            return f'This room does not have a {compass_dir} door or doorway.'

    def __init__(self, compass_dir, portal_type=None):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class Various_Commands_Entered_Room(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.leave_command() when the player
    leaves a room and enters a new one, or by .begin_command() when the player
    starts the game in the first room. It prints the room description, lists the
    items on the floor if any, mentions any chest or creature, and lists the
    exits to the room by compass direction.
    """
    __slots__ = 'room',

    @property
    def message(self):
        message_list = list()
        message_list.append(self.room.description)
        if self.room.container_here is not None:
            message_list.append(f'You see a {self.room.container_here.title} here.')
        if self.room.creature_here is not None:
            message_list.append(f'There is a {self.room.creature_here.title} in the room.')
        if self.room.items_here is not None:
            room_items = list()
            for item_qty, item in self.room.items_here.values():
                quantifier = 'a' if item_qty == 1 else str(item_qty)
                pluralizer = '' if item_qty == 1 else 's'
                room_items.append(quantifier + ' ' + item.title + pluralizer)
            items_here_str = join_str_seq_w_commas_and_conjunction(room_items, 'and')
            message_list.append(f'You see {items_here_str} on the floor.')
        door_list = list()
        for compass_dir in ('north', 'east', 'south', 'west'):
            dir_attr = compass_dir + '_door'
            door = getattr(self.room, dir_attr, None)
            if door is None:
                continue
            door_ersatz_title = door.door_type.replace('_', ' ')
            door_list.append(f"a {door_ersatz_title} to the {compass_dir}")
        door_str = 'There is ' + join_str_seq_w_commas_and_conjunction(door_list, 'and') + '.'
        message_list.append(door_str)
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
    adventuregame.processor.Command_Processor.begin_game() or .equip_command()
    when the player equips an item. It lists the item equipped and mentions how
    the relevant game parameters have changed as a result.
    """
    __slots__ = ('item_title', 'item_type', 'changed_value_1', 'value_type_1', 'changed_value_2', 'value_type_2',
                'change_text')

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_type, gerund=True)
        indirect_article = 'a ' if self.item_type != 'armor' else ''
        plussign = '+' if self.value_type_1 == 'attack bonus' and self.changed_value_1 >= 0 else ''
        if self.changed_value_1 is None and self.changed_value_2 is None:
            return_str = f"You're now {item_usage_verb} {indirect_article}{self.item_title}."
        elif self.changed_value_2 is None:
            return_str = (f"You're now {item_usage_verb} {indirect_article}{self.item_title}. "
                          f'Your {self.value_type_1} is {plussign}{self.changed_value_1}.')
        else:
            return_str = (f"You're now {item_usage_verb} {indirect_article}{self.item_title}. "
                          f'Your {self.value_type_1} is {plussign}{self.changed_value_1}, '
                          f'and your {self.value_type_2} is {self.changed_value_2}.')
        if self.change_text:
            return_str += ' ' + self.change_text
        return return_str

    def __init__(self, item_title, item_type, changed_value_1=None, value_type_1=None, changed_value_2=None,
                       value_type_2=None, change_text=''):
        self.item_title = item_title
        self.item_type = item_type
        self.changed_value_1 = changed_value_1
        self.value_type_1 = value_type_1
        self.changed_value_2 = changed_value_2
        self.value_type_2 = value_type_2
        self.change_text = change_text


class Various_Commands_Item_Unequipped(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.equip_command(),
    .unequip_command(), or .drop_command(). It's returned by .unequip_command()
    when the player unequips an item; .equip_command() returns it if the player
    already had an item equipped in that slot to convey the previous item's
    removal; and .drop_command() returns it if the item the character dropped
    was equipped and they no longer have any of the item in their inventory.
    """
    __slots__ = ('item_title', 'item_type', 'changed_value_1', 'value_type_1', 'changed_value_2', 'value_type_2',
                'change_text')

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_type, gerund=True)
        indirect_article = 'a ' if self.item_type != 'armor' else ''
        if self.changed_value_1 is None and self.changed_value_2 is None:
            return_str = f"You're no longer {item_usage_verb} {indirect_article}{self.item_title}."
        elif self.changed_value_2 is None:
            return_str = (f"You're no longer {item_usage_verb} {indirect_article}{self.item_title}. "
                          f'Your {self.value_type_1} is {self.changed_value_1}.')
        else:
            return_str = (f"You're no longer {item_usage_verb} {indirect_article}{self.item_title}. "
                          f'Your {self.value_type_1} is {self.changed_value_1}, '
                          f'and your {self.value_type_2} is {self.changed_value_2}.')
        if self.change_text:
            return return_str + ' ' + self.change_text
        else:
            return return_str

    def __init__(self, item_title, item_type, changed_value_1=None, value_type_1=None, changed_value_2=None,
                       value_type_2=None, change_text=''):
        self.item_title = item_title
        self.item_type = item_type
        self.changed_value_1 = changed_value_1
        self.value_type_1 = value_type_1
        self.changed_value_2 = changed_value_2
        self.value_type_2 = value_type_2
        self.change_text = change_text


class Various_Commands_Underwent_Healing_Effect(Game_State_Message):
    """
    This class implements an object that is returned by
    adventuregame.processor.Command_Processor.drink_command() or
    .cast_spell_command(). It's returned by .drink_command() if the player
    drinks a health potion; and it's returned by the .cast_spell_command() if
    the player is a Priest and they successfully cast a healing spell.
    """
    __slots__ = 'amount_healed', 'current_hit_points', 'hit_point_total',

    @property
    def message(self):
        if self.amount_healed and self.current_hit_points == self.hit_point_total:
            return (f"You regained {self.amount_healed} hit points. You're fully healed! Your hit points are "
                    f'{self.current_hit_points}/{self.hit_point_total}.')
        elif self.amount_healed:
            return (f'You regained {self.amount_healed} hit points. Your hit points are '
                    f'{self.current_hit_points}/{self.hit_point_total}.')
        else:
            return (f"You didn't regain any hit points. Your hit points are "
                    f'{self.current_hit_points}/{self.hit_point_total}.')

    def __init__(self, amount_healed, current_hit_points, hit_point_total):
        self.amount_healed = amount_healed
        self.current_hit_points = current_hit_points
        self.hit_point_total = hit_point_total
