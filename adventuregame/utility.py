#!/usr/bin/python

import functools
import math
import os
import random
import re
import tempfile
import textwrap

import iniconfig


__name__ = 'adventuregame.utility'

# Python3's str class doesn't offer a method to test if the string constitutes a
# float value so I rolled my own.

_float_re = re.compile(r'^[+-]?([0-9]+\.|\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+)$')

isfloat = lambda strval: bool(_float_re.match(strval))


# The player can use lexical numbers (ie. 'one', 'fourteen', 'thirty') in
# commands and the `Command_Processor` needs to be able to interpret them, so
# I wrote this utility function. The regular expressions it uses are defined
# outside the function so they're only compiled once.

digit_re = re.compile('^[0-9]+$')

lexical_number_in_1_99_re = re.compile("""^(
                                           (one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)
                                       |
                                           (thir|four|fif|six|seven|eigh|nine)teen
                                       |
                                           (twen|thir|for|fif|six|seven|eigh|nine)ty-
                                           (one|two|three|four|five|six|seven|eight|nine)
                                       )$""", re.X)

digit_lexical_number_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
                            'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
                            'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
                            'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
                            'eighty': 80, 'ninety': 90, }

# This argument uses a regex to verify the argument is between one and
# ninety-nine. If not, math.nan is returned as a signal value. If the string is
# found in digit_lexical_number_map, the digit value for that key is returned.
# Otherwise, it's a hyphenate lexical number above twenty. It's broken at the
# hyphen and the two components are looked up in digit_lexical_number_map and
# the values summed to arrive at the digital equivelant of the lexical number.

def lexical_number_to_digits(lexical_number):
    if not lexical_number_in_1_99_re.match(lexical_number):
        return math.nan
    if lexical_number in digit_lexical_number_map:
        return digit_lexical_number_map[lexical_number]
    tens_place, ones_place = lexical_number.split('-')
    base_number = digit_lexical_number_map[tens_place]
    added_number = digit_lexical_number_map[ones_place]
    return base_number + added_number


class Internal_Exception(Exception):
    pass


class Bad_Command_Exception(Exception):
    __slots__ = 'command', 'message'

    def __init__(self, command_str, message_str):
        self.command = command_str
        self.message = message_str


# A simple convenience function used in adventuregame.statemsgs to form natural
# language messages around types of equippable items.

def usage_verb(item_type, gerund=True):
    if item_type == 'armor':
        return 'wearing' if gerund else 'wear'
    elif item_type == 'shield':
        return 'carrying' if gerund else 'carry'
    elif item_type == 'weapon':
        return 'wielding' if gerund else 'wield'
    else:
        return 'using' if gerund else 'use'

# In D&D, the standard notation for dice rolling is of the form
# [1-9][0-9]*d[1-9]+[0-9]*([+-][1-9][0-9]*)?, where the first number indicates
# how many dice to roll, the second number is the number of sides of the die to
# roll, and the optional third number is a positive or negative value to add
# to the result of the roll to reach the final outcome. As an example, 1d20+3
# indicates a roll of one 20-sided die to which 3 should be added.
#
# I have used this notation in the items.ini file since it's the simplest way
# to compactly express Weapon damage, and in the attack roll methods to call
# for a d20 roll (the standard D&D conflict resolution roll). This function
# parses those expressions and returns a closure that executes random.randint
# appropriately to simulate dice rolls of the dice indicated by the expression.

dice_expression_re = re.compile(r'([1-9]+)d([1-9][0-9]*)([-+][1-9][0-9]*)?')

def roll_dice(dice_expr):
    match = dice_expression_re.match(dice_expr)
    if not match:
        raise Internal_Exception('invalid dice expression: ' + dice_expr)
    number_of_dice, sidedness_of_dice, modifier_to_roll = match.groups()
    number_of_dice = int(number_of_dice)
    sidedness_of_dice = int(sidedness_of_dice)
    modifier_to_roll = int(modifier_to_roll) if modifier_to_roll is not None else 0
    return sum(random.randint(1, sidedness_of_dice) for _ in range(0, number_of_dice)) + modifier_to_roll



# The game data is stored in .ini format; however, to avoid having non-python
# files residing in the module hierarchy, the .ini data is kept inline in
# adventuregame.data as multi-line strings.
#
# Unfortunately, iniconfig.IniConfig has a limitation: it takes as its argument
# the path to the .ini file to parse, rather than accepting an open _io.*
# iterable file object.
#
# As a workaround, iniconfig_obj_from_ini_text() takes a multi-line string of
# .ini data, stores it to a temp file, initializes the IniConfig object from
# that file, then deletes the file.
#
# Memoization is used to avoid repeating the string-to-tempfile storage
# operation when a valid IniConfig object for the multi-line string has already
# been generated.
#
# Without memoization, during testing it's possible to open so many tempfiles
# with this function that the OS gives us a `OSError: [Errno 24] Too many open
# files` error. Using entire config file texts as keys to a dictionary is
# uncommon but it works. IniConfig objects are simple data vectors that don't
# undergo state changes when we use them, so they can be reused.

memoized_iniconfig_objs = dict()

def iniconfig_obj_from_ini_text(ini_config_text):
    if ini_config_text in memoized_iniconfig_objs:
        return memoized_iniconfig_objs[ini_config_text]
    _, temp_ini_config_file = tempfile.mkstemp(suffix='.ini')
    temp_ini_config_fh = open(temp_ini_config_file, 'w')
    temp_ini_config_fh.write(ini_config_text)
    temp_ini_config_fh.close()
    del temp_ini_config_fh
    ini_config = iniconfig.IniConfig(temp_ini_config_file)
    os.remove(temp_ini_config_file)
    memoized_iniconfig_objs[ini_config_text] = ini_config
    return ini_config



# The return values from adventuregame.processor.Command_Processor.process() are
# not wrapped; the wrapping is done at the UI level in advgame.py. Python comes
# with a text wrapping library, textwrap, but it has a limitation: if it's fed a
# multi-paragraph string, the paragraphs are run together and a single wrapped
# paragraph is returned.
#
# This lambda breaks the multi-paragraph st4ring into separate strings, maps a
# curried textwrap.wrap() over them, joins wrap()'s list results with newlines,
# and joins the wrapped paragraphs with newlines to a multi-paragraph string.

_wrapper = functools.partial(textwrap.wrap, width=80)

textwrapper = lambda multiline_str: "\n".join("\n".join(paragraph)
                                              for paragraph in map(_wrapper, multiline_str.split("\n")))

