#!/usr/bin/python3

import abc
import math
import random
import re
import operator
import functools
import operator

import iniconfig

from .utility import *
from .collections import *
from .gameelements import *

__name__ = 'adventuregame.commandreturns'


class game_state_message(abc.ABC):

    @property
    @abc.abstractmethod
    def message(self):
        pass

    @abc.abstractmethod
    def __init__(self, *argl, **argd):
        pass


class command_not_recognized(game_state_message):
    __slots__ = 'command',

    message = property(fget=(lambda self: 'Command not recognized.'))

    def __init__(self, command_str):
        self.command = command_str


class command_bad_syntax(game_state_message):
    __slots__ = 'command', 'proper_syntax'

    @property
    def message(self):
        proper_syntax_options_str = ""
        for option_str in self.proper_syntax_options:
            if proper_syntax_options_str:
                proper_syntax_options_str += ' or '
            proper_syntax_options_str += f"'{option_str}'"
        return f"{self.command.upper()} command: bad syntax. Should be {proper_syntax_options_str}."

    def __init__(self, command_str, *proper_syntax_strs):
        self.command = command_str
        self.proper_syntax_options = proper_syntax_strs


class command_too_many_words(game_state_message):
    __slots__ = 'number_expected',

    message = property(fget=(lambda self: f'Command followed by too many words, needed only {self.number_expected}.'))

    def __init__(self, number_expected_int):
        self.number_expected = number_expected_int


class attack_command_opponent_not_found(game_state_message):
    __slots__ = 'creature_title_given', 'opponent_present'

    @property
    def message(self):
        if self.opponent_present:
            return f"This room doesn't have a {self.creature_title_given}; but there is a {self.opponent_present}."
        else:
            return f"This room doesn't have a {self.creature_title_given}; nobody is here."

    def __init__(self, creature_title_given_str, opponent_present_str=''):
        self.creature_title_given = creature_title_given_str
        self.opponent_present = opponent_present_str


class attack_command_attack_missed(game_state_message):
    __slots__ = 'creature_title',

    message = property(fget=(lambda self: f'Your attack on the {self.creature_title} missed. '
                                                   'It turns to attack!'))

    def __init__(self, creature_title_str):
            self.creature_title = creature_title_str


class attack_command_attack_hit(game_state_message):
    __slots__ = 'creature_title', 'damage_done', 'creature_slain'

    @property
    def message(self):
        if self.creature_slain:
            return f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage.' 
        else:
            return (f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage. ' 
                    f'The {self.creature_title} turns to attack!')

    def __init__(self, creature_title_str, damage_done_int, creature_slain_bool):
        self.creature_title = creature_title_str
        self.damage_done = damage_done_int
        self.creature_slain = creature_slain_bool


class attack_command_foe_death(game_state_message):
    __slots__ = 'creature_title',

    @property
    def message(self):
        return f'The {self.creature_title} is slain.'

    def __init__(self, creature_title_str):
        self.creature_title = creature_title_str


class be_attacked_by_command_attacked_and_not_hit(game_state_message):
    __slots__ = 'creature_title',

    message = property(fget=(lambda self: (f'The {self.creature_title} attacks! Their attack misses.')))

    def __init__(self, creature_title_str):
        self.creature_title = creature_title_str


class be_attacked_by_command_attacked_and_hit(game_state_message):
    __slots__ = 'creature_title', 'damage_done', 'hit_points_left'

    message = property(fget=(lambda self: (f'The {self.creature_title} attacks! Their attack hits. They did '
                                                    f'{self.damage_done} damage! You have {self.hit_points_left} '
                                                    'hit points left.')))

    def __init__(self, creature_title_str, damage_done_int, hit_points_left_int):
        self.creature_title = creature_title_str
        self.damage_done = damage_done_int
        self.hit_points_left = hit_points_left_int


class be_attacked_by_command_character_death(game_state_message):

    message = property(fget=lambda self: f'You have died!')

    def __init__(self):
        pass


class inspect_command_found_nothing(game_state_message):
    __slots__ = 'entity_title',

    message = property(fget=lambda self: f'You see no {entity_title} here.')

    def __init__(self, entity_title_str):
        self.entity_title = entity_title_str


class inspect_command_found_item_or_items_here(game_state_message):
    __slots__ = "item_description", "item_qty"

    @property
    def message(self):
        if self.item_qty > 1:
            return f'{self.item_description}. You see {self.item_qty} here.'
        else:
            return self.item_description
    
    def __init__(self, item_description_str, item_qty_int):
        self.item_description = item_description_str
        self.item_qty = item_qty_int


class inspect_command_found_container_here(game_state_message):
    __slots__ = 'container_description', 'container_type', 'container', 'is_locked', 'is_closed'

    @property
    def message(self):
        if self.container_type == 'chest':
            if self.is_locked is True and self.is_closed is True:
                return f'{self.container_description} It is closed and locked.'
            elif self.is_locked is False and self.is_closed is True:
                return f'{self.container_description} It is closed but unlocked.'
            elif self.is_locked is False and self.is_closed is False:
                return f'{self.container_description} It is unlocked and open. {self.contents}'
            # `self.is_locked is True and self.is_closed is False` is not
            # a possible outcome of these tests because it's an invalid
            # combination, and is checked for in __init__. If that is the
            # combination of booleans, an exception is raised.
            elif self.is_locked is None and self.is_closed is True:
                return f'{self.container_description} It is closed.'
            elif self.is_locked is None and self.is_closed is False:
                return f'{self.container_description} It is open. {self.contents}'
            elif self.is_locked is True and self.is_closed is None:
                return f'{self.container_description} It is locked.'
            elif self.is_locked is False and self.is_closed is None:
                return f'{self.container_description} It is unlocked.'
            else: # None and None
                return self.container_description
        elif self.container_type == 'corpse':
            return f'{self.container_description} {self.contents}'

    @property
    def contents(self):
        content_qty_obj_pairs = sorted(self.container.values(), key=lambda arg: arg[1].title)
        contents_str_tuple = tuple('a ' + item_obj.title if qty == 1 else str(qty) + ' ' + item_obj.title + 's'
                                       for qty, item_obj in content_qty_obj_pairs)
        if self.container_type == 'chest':
            if len(contents_str_tuple) == 0:
                return 'It is empty.'
            elif len(contents_str_tuple) == 1:
                return f'It contains {contents_str_tuple[0]}.'
            elif len(contents_str_tuple) == 2:
                return f'It contains {contents_str_tuple[0]} and {contents_str_tuple[1]}.'
            else:
                return 'It contains %s, and %s.' % (', '.join(contents_str_tuple[0:-1]), contents_str_tuple[-1])
        else:
            if len(contents_str_tuple) == 0:
                return 'They have nothing on them.'
            elif len(contents_str_tuple) == 1:
                return f'They have {contents_str_tuple[0]} on them.'
            elif len(contents_str_tuple) == 2:
                return f'They have {contents_str_tuple[0]} and {contents_str_tuple[1]} on them.'
            else:
                return 'They have %s, and %s on them.' % (', '.join(contents_str_tuple[0:-1]), contents_str_tuple[-1])

    def __init__(self, container_obj):
        self.container = container_obj
        self.container_description = container_obj.description
        self.is_locked = container_obj.is_locked
        self.is_closed = container_obj.is_closed
        self.container_type = container_obj.container_type
        if self.is_locked is True and self.is_closed is False:
            raise internal_exception(f'Container {container_obj.internal_name} has is_locked = True and is_open = False, invalid combination of parameters.')


class inspect_command_found_creature_here(game_state_message):
    __slots__ = "creature_description",

    message = property(fget=lambda self: self.creature_description)

    def __init__(self, creature_description_str):
        self.creature_description = creature_description_str


class take_command_quantity_unclear(game_state_message):

    message = property(fget=lambda self: f"Amount to take unclear. How many do you want?")

    def __init__(self):
        pass


class take_command_trying_to_take_more_than_is_present(game_state_message):
    __slots__ = 'container_title', 'container_type', 'item_title', 'amount_attempted', 'amount_present'

    message = property(fget=lambda self: f"You can't take {self.amount_attempted} {self.item_title}s from the {self.container_title}. Only {self.amount_present} is there.")

    def __init__(self, container_title_str, container_type_str, item_title_str, amount_attempted_int, amount_present_int):
        self.container_title = container_title_str
        self.container_type = container_type_str
        self.item_title = item_title_str
        self.amount_attempted = amount_attempted_int
        self.amount_present = amount_present_int

class put_command_amount_put(game_state_message):
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
            return (f"You put {self.amount_put} {self.item_title}{amount_put_pluralizer} on the {self.container_title}'s person."
                    f' You have {self.amount_left} {self.item_title}{amount_left_pluralizer} left.')
        else:  # not self.amount_left and self.container_type == 'corpse':
            return (f"You put {self.amount_put} {self.item_title}{amount_put_pluralizer} on the {self.container_title}'s person."
                    f' You have no more {self.item_title}{amount_left_pluralizer}.')

    def __init__(self, item_title_str, container_title_str, container_type_str, amount_put_int, amount_left_int):
        self.item_title = item_title_str
        self.container_title = container_title_str
        self.container_type = container_type_str
        self.amount_put = amount_put_int
        self.amount_left = amount_left_int


class put_command_trying_to_put_more_than_you_have(game_state_message):
    __slots__ = 'item_title', 'amount_present'

    @property
    def message(self):
        pluralizer = 's' if self.amount_present > 1 else ''
        return f"You only have {self.amount_present} {self.item_title}{pluralizer} in your inventory."

    def __init__(self, item_title_str, amount_present_int):
        self.item_title = item_title_str
        self.amount_present = amount_present_int


class put_command_quantity_unclear(game_state_message):

    message = property(fget=lambda self: f"Amount to put unclear. How many do you mean?")

    def __init__(self):
        pass


class put_command_item_not_in_inventory(game_state_message):
    __slots__ = 'amount_attempted', 'item_title'

    @property
    def message(self):
        if self.amount_attempted > 1:
            return f"You don't have any {self.item_title}s in your inventory."
        else:
            return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title_str, amount_attempted_int):
        self.amount_attempted =  amount_attempted_int
        self.item_title =  item_title_str


class take_command_item_not_found_in_container(game_state_message):
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

    def __init__(self, container_title_str, amount_attempted_int, container_type_str, item_title_str):
        self.container_title =  container_title_str
        self.amount_attempted =  amount_attempted_int
        self.container_type =  container_type_str
        self.item_title =  item_title_str

class various_commands_container_not_found(game_state_message):
    __slots__ = 'container_not_found_title', 'container_present_title'

    @property
    def message(self):
        if self.container_present_title is not None:
            return f"There is no {self.container_not_found_title} here. However, there *is* a {self.container_present_title} here."
        else:
            return f"There is no {self.container_not_found_title} here."

    def __init__(self, container_not_found_title_str, container_present_title_str=None):
        self.container_not_found_title = container_not_found_title_str
        self.container_present_title = container_present_title_str


class take_command_item_or_items_taken(game_state_message):
    __slots__ = 'container_title', 'item_title', 'amount_taken'

    @property
    def message(self):
        if self.amount_taken > 1:
            return f'You took {self.amount_taken} {self.item_title}s from the {self.container_title}.'
        else:
            return f'You took a {self.item_title} from the {self.container_title}.'

    def __init__(self, container_title_str, item_title_str, amount_taken_int):
        self.container_title = container_title_str
        self.item_title = item_title_str
        self.amount_taken = amount_taken_int


