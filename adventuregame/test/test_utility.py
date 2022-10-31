#!/usr/bin/python3

import math
import unittest

from .context import *
from .testing_game_data import *

__name__ = 'adventuregame.test_utility'


class Test_Isfloat(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_isfloat(self):
        self.assertTrue(isfloat('+5.6'))
        self.assertTrue(isfloat('-5.6'))
        self.assertTrue(isfloat('5.6'))
        self.assertTrue(isfloat('5.'))
        self.assertTrue(isfloat('.6'))
        self.assertTrue(isfloat('6'))
        self.assertFalse(isfloat('.'))
        self.assertFalse(isfloat('+'))
        self.assertFalse(isfloat('-'))


class Test_Lexical_Number_to_Digits(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_lexical_number_to_digits(self):
        self.assertEqual(lexical_number_to_digits('five'), 5)
        self.assertEqual(lexical_number_to_digits('eighty-one'), 81)
        self.assertEqual(lexical_number_to_digits('nine'), 9)
        self.assertEqual(lexical_number_to_digits('fifty-one'), 51)
        self.assertEqual(lexical_number_to_digits('twenty-one'), 21)
        self.assertEqual(lexical_number_to_digits('ninety-three'), 93)
        self.assertEqual(lexical_number_to_digits('nineteen'), 19)
        self.assertEqual(lexical_number_to_digits('ninety-four'), 94)
        self.assertEqual(lexical_number_to_digits('fourty-three'), 43)
        self.assertEqual(lexical_number_to_digits('six'), 6)
        self.assertIs(lexical_number_to_digits('zero'), math.nan)
        self.assertIs(lexical_number_to_digits('one hundred'), math.nan)
