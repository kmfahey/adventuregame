#!/usr/bin/python

import abc
import math
import random
import re
import operator
import functools
import operator

import iniconfig

__name__ = 'adventuregame.utility'


# Python3's str class doesn't offer a method to test if the string constitutes
# a float value so I rolled my own.
_float_re = re.compile(r'^[+-]?([0-9]+\.|\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+)$')

isfloat = lambda strval: bool(_float_re.match(strval))


digit_re = re.compile('^[0-9]+$')

digit_lexical_number_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
                            'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                            'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
                            'fourty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90, }

lexical_number_in_1_99_re = re.compile('^('
                                           '(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)'
                                       '|'
                                           '(thir|four|fif|six|seven|eigh|nine)teen'
                                       '|'
                                           '(twen|thir|four|fif|six|seven|eigh|nine)ty-'
                                           '(one|two|three|four|five|six|seven|eight|nine)'
                                       ')$')

# The player can use lexical numbers (ie. 'one', 'fourteen', 'thirty') in
# commands and the `command_processor` needs to be able to interpret them, so
# I wrote this utility function.
def lexical_number_to_digits(lexical_number):
    if not lexical_number_in_1_99_re.match(lexical_number):
        return math.nan
    if lexical_number in digit_lexical_number_map:
        return digit_lexical_number_map[lexical_number]
    tens_place, ones_place = lexical_number.split('-')
    base_number = digit_lexical_number_map[tens_place]
    added_number = digit_lexical_number_map[ones_place]
    return base_number + added_number


class internal_exception(Exception):
    pass


class bad_command_exception(Exception):
    __slots__ = 'command', 'message'

    def __init__(self, command_str, message_str):
        self.command = command_str
        self.message = message_str


