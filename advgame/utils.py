#!/usr/bin/python3

"""
The advgame.utils module comprises a small collection of utility
functions used by other modules in the package to expedite common tasks in the
codebase.
"""

import math
import random
import re
import textwrap

import advgame.errors as excpt

__name__ = 'advgame.utils'


# The task of joining a list that may be 1, 2, or more elements with commas and
# a conjunction is a common one in advgame.stmsg, so I wrote this
# function to automate that task.

def join_strs_w_comma_conj(str_list, conjunction='and'):
    """
This function automates the task of joining a sequence of strings with commas
and a conjunction.

>>> join_strs_w_comma_conj(['foo'], 'and')
'foo'
>>> join_strs_w_comma_conj(['foo', 'bar'], 'and')
'foo and bar'
>>> join_strs_w_comma_conj(['foo', 'bar', 'baz'], 'and')
'foo, bar, and baz'

:str_list:    The sequence of strings to join.
:conjunction: The conjunction to use with sequences longer than 1 element.
              Typical values include 'and' or 'or'.
:return:      Returns a grammatical comma-separated list string.
    """
    if len(str_list) == 0:
        return ''
    elif len(str_list) == 1:
        return str_list[0]
    elif len(str_list) == 2:
        return f'{str_list[0]} {conjunction} {str_list[1]}'
    else:
        return ', '.join(str_list[:-1]) + f', {conjunction} ' + str_list[-1]


# This regular expression matches a string representation of a floating-point
# value.

_float_re = re.compile(r'^[+-]?([0-9]+\.|\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+)$')


def isfloat(strval):
    try:
        f = float(strval)
    except ValueError:
        return False
    else:
        return True


# The player can use lexical numbers (ie. 'one', 'fourteen', 'thirty') in
# commands and the `CommandProcessor` needs to be able to interpret them, so
# I wrote this utility function. The regular expressions it uses are defined
# outside the function so they're only compiled once.

digit_re = re.compile('^[0-9]+$')

# This regular expression matches any lexical number from one to ninety-nine.

lexical_number_in_1_99_re = re.compile("""^(
                                           (one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)
                                       |
                                           (thir|four|fif|six|seven|eigh|nine)teen
                                       |
                                           (twen|thir|for|fif|six|seven|eigh|nine)ty-
                                           (one|two|three|four|five|six|seven|eight|nine)
                                       )$""", re.X)

# This dictionary is a lookup table that's used to interpret the ones place and
# (optionally) tens place of a lexical number.

_digit_lexical_number_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
                            'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
                            'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
                            'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
                            'eighty': 80, 'ninety': 90, }


def lexical_number_to_digits(lexical_number):
    """
This function parses a lexical representation of a number between one and
ninety-nine, and returns an int that is equivalent to that number. For lexical
numbers outside of one to ninety-nine, math.nan is returned.

>>> lexical_number_to_digits('one')
1
>>> lexical_number_to_digits('ninety-nine')
99
>>> lexical_number_to_digits('one hundred and sixty')
nan

:lexical_number: The textual representation of a number to parse. Must be
between one and ninety-nine inclusive. :return: Returns an int, or math.nan
(which is a float).
    """

    # The lexical number is not in the range this function can parse, so
    # math.nan is returned as a signal value.
    if not lexical_number_in_1_99_re.match(lexical_number):
        return math.nan

    # The lexical number is not hyphenate, so I can use
    # _digit_lexical_number_map and return the matching int value.
    if lexical_number in _digit_lexical_number_map:
        return _digit_lexical_number_map[lexical_number]

    # The lexical number is hyphenate, so I break it into a tens place and a
    # ones place, look them up separately in _digit_lexical_number_map, and
    # return the sum of the int values.
    tens_place, ones_place = lexical_number.split('-')
    base_number = _digit_lexical_number_map[tens_place]
    added_number = _digit_lexical_number_map[ones_place]
    return base_number + added_number


# A simple convenience function used in advgame.stmsg to form natural
# language messages around types of equippable items.

def usage_verb(item_type, gerund=True):
    """
This convenience function returns the appropriate verb to use when referring to
how a character is described as using an equippable type of item.

>>> usage_verb('armor', gerund=True)
'wearing'
>>> usage_verb('shield', gerund=False)
'carry'
>>> usage_verb('weapon', gerund=True)
'wielding'

:item_type: Either 'armor', 'shield', 'weapon', or 'wand'. :gerund: Either True
(to receive the gerund) or False (to receive the present indicative). :return:
The verb string matching how the item is used.
    """
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
# for a d20 roll (the standard D&D conflict resolution roll).

_dice_expression_re = re.compile(r'([1-9]+)d([1-9][0-9]*)([-+][1-9][0-9]*)?')


def roll_dice(dice_expr):
    """
This function accepts a standard Dungeons & Dragons dice expression (such as
1d20+5, 1d8+2, or 3d10-3), uses random.randint() to simulate a dice roll or
rolls with the given modifier, and returns the computed random value>

:dice_expr: A dice expression of the form #d#[±#]. return: A random number
:value, as an int.
    """
    match = _dice_expression_re.match(dice_expr)
    if not match:
        raise excpt.InternalError('invalid dice expression: ' + dice_expr)
    number_of_dice, sidedness_of_dice, modifier_to_roll = match.groups()
    number_of_dice = int(number_of_dice)
    sidedness_of_dice = int(sidedness_of_dice)
    modifier_to_roll = int(modifier_to_roll) if modifier_to_roll is not None else 0
    return sum(random.randint(1, sidedness_of_dice) for _ in range(0, number_of_dice)) + modifier_to_roll


# The return values from advgame.process.CommandProcessor.process() are
# not wrapped; the wrapping is done at the UI level in advgame.py. Python comes
# with a text wrapping library, textwrap, but it has a limitation: if it's fed a
# multi-paragraph string, the paragraphs are run together and a single wrapped
# paragraph is returned. This function extends it to handle multiple paragraphs.

def textwrapper(paragraphs, width=80):
    """
This function accepts a multiline string comprising paragraphs of unwrapped
text, separately wraps each one to 80 columns, and returns the wrapped
paragraphs as a string.

:paragraphs: A multi-line string of text. return: The text input wrapped to 80
:columns paragraph-by-paragraph.
    """
    # The text is broken into separate paragraph strings and applies
    # textwrap.wrap to each one.
    wrapped_lines = map(lambda para: textwrap.wrap(para, width=width), paragraphs.split('\n'))

    # textwrap.wrap returns a list of lines, so I reassemble the paragraphs with
    # '\n'.join()
    wrapped_paragraphs = ['\n'.join(paragraph) for paragraph in wrapped_lines]

    # The full multi-paragraph text is reassembled with a second use of
    # '\n'.join() and returned.
    wrapped = '\n'.join(wrapped_paragraphs)
    return wrapped
