#!/usr/bin/python3

import math
import unittest

from .context import adventuregame as advg

__name__ = 'tests.test_utility'


LOREM_IPSUM_UNWRAPPED = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas malesuada mi vel \
elementum facilisis. Nulla ac felis in diam dictum dignissim in eget neque. Sed ultrices, mauris sed pellentesque \
rutrum, dui augue elementum ante, vel ultricies diam metus nec risus. Cras finibus, orci ac pellentesque finibus, \
orci lorem tempus justo, eget mollis nibh justo et dolor. Sed commodo magna erat, sed elementum nulla feugiat a. Ut \
faucibus gravida felis ut mollis. In in ante metus. Pellentesque habitant morbi tristique senectus et netus et \
malesuada fames ac turpis egestas. Aenean est nibh, ultrices in lacinia vel, feugiat eu nibh. Pellentesque ac aliquet \
risus. Aliquam erat volutpat. Aliquam bibendum felis sit amet vulputate molestie. Vivamus scelerisque lacinia mauris \
non rutrum. Nunc tempor quis turpis eget tincidunt.

Vivamus ac ultricies dolor, vel condimentum sapien. Sed semper facilisis pulvinar. Fusce sit amet vulputate nibh. \
Donec consequat scelerisque odio non facilisis. Ut nibh elit, iaculis at justo id, iaculis efficitur turpis. Donec \
fringilla volutpat ligula at blandit. Vestibulum congue cursus tellus, id commodo ex fringilla ut. Nullam eu leo \
pellentesque, consectetur felis nec, ultricies enim. Nunc sit amet elementum orci. Aenean quis dolor in nisl posuere \
finibus gravida eu urna. Ut tempor, neque id ornare porta, risus turpis rhoncus justo, in dapibus lacus nunc vel \
elit. Pellentesque vulputate pellentesque purus, ac imperdiet urna sagittis sodales. Donec varius orci \
sapien.

Fusce tristique blandit ex, vel interdum libero dignissim non. Sed ut libero rutrum, efficitur diam ullamcorper, \
pellentesque tortor. Sed vitae nisi eget est luctus volutpat sit.
"""

LOREM_IPSUM_WRAPPED = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas malesuada mi
vel elementum facilisis. Nulla ac felis in diam dictum dignissim in eget neque.
Sed ultrices, mauris sed pellentesque rutrum, dui augue elementum ante, vel
ultricies diam metus nec risus. Cras finibus, orci ac pellentesque finibus, orci
lorem tempus justo, eget mollis nibh justo et dolor. Sed commodo magna erat, sed
elementum nulla feugiat a. Ut faucibus gravida felis ut mollis. In in ante
metus. Pellentesque habitant morbi tristique senectus et netus et malesuada
fames ac turpis egestas. Aenean est nibh, ultrices in lacinia vel, feugiat eu
nibh. Pellentesque ac aliquet risus. Aliquam erat volutpat. Aliquam bibendum
felis sit amet vulputate molestie. Vivamus scelerisque lacinia mauris non
rutrum. Nunc tempor quis turpis eget tincidunt.

Vivamus ac ultricies dolor, vel condimentum sapien. Sed semper facilisis
pulvinar. Fusce sit amet vulputate nibh. Donec consequat scelerisque odio non
facilisis. Ut nibh elit, iaculis at justo id, iaculis efficitur turpis. Donec
fringilla volutpat ligula at blandit. Vestibulum congue cursus tellus, id
commodo ex fringilla ut. Nullam eu leo pellentesque, consectetur felis nec,
ultricies enim. Nunc sit amet elementum orci. Aenean quis dolor in nisl posuere
finibus gravida eu urna. Ut tempor, neque id ornare porta, risus turpis rhoncus
justo, in dapibus lacus nunc vel elit. Pellentesque vulputate pellentesque
purus, ac imperdiet urna sagittis sodales. Donec varius orci sapien.

Fusce tristique blandit ex, vel interdum libero dignissim non. Sed ut libero
rutrum, efficitur diam ullamcorper, pellentesque tortor. Sed vitae nisi eget est
luctus volutpat sit.
"""


class Test_Textwrapper(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_textwrapper(self):
        wrapped_text = advg.textwrapper(LOREM_IPSUM_UNWRAPPED)
        self.assertEqual(wrapped_text, LOREM_IPSUM_WRAPPED)


class Test_Isfloat(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_isfloat(self):
        self.assertTrue(advg.isfloat('+5.6'))
        self.assertTrue(advg.isfloat('-5.6'))
        self.assertTrue(advg.isfloat('5.6'))
        self.assertTrue(advg.isfloat('5.'))
        self.assertTrue(advg.isfloat('.6'))
        self.assertTrue(advg.isfloat('6'))
        self.assertFalse(advg.isfloat('.'))
        self.assertFalse(advg.isfloat('+'))
        self.assertFalse(advg.isfloat('-'))


class Test_Lexical_Number_to_Digits(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_lexical_number_to_digits(self):
        self.assertEqual(advg.lexical_number_to_digits('five'), 5)
        self.assertEqual(advg.lexical_number_to_digits('eighty-one'), 81)
        self.assertEqual(advg.lexical_number_to_digits('nine'), 9)
        self.assertEqual(advg.lexical_number_to_digits('fifty-one'), 51)
        self.assertEqual(advg.lexical_number_to_digits('twenty-one'), 21)
        self.assertEqual(advg.lexical_number_to_digits('ninety-three'), 93)
        self.assertEqual(advg.lexical_number_to_digits('nineteen'), 19)
        self.assertEqual(advg.lexical_number_to_digits('ninety-four'), 94)
        self.assertEqual(advg.lexical_number_to_digits('forty-three'), 43)
        self.assertEqual(advg.lexical_number_to_digits('six'), 6)
        self.assertIs(advg.lexical_number_to_digits('zero'), math.nan)
        self.assertIs(advg.lexical_number_to_digits('one hundred'), math.nan)

class Test_Lexical_Number_to_Digits(unittest.TestCase):

    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def test_join_str_seq_w_commas_and_conjunction_1(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction((), 'and')
        self.assertEqual(joined_str, '')
        
    def test_join_str_seq_w_commas_and_conjunction_2(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction(('foo',), 'and')
        self.assertEqual(joined_str, 'foo')
        
    def test_join_str_seq_w_commas_and_conjunction_3(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction(('foo', 'bar'), 'and')
        self.assertEqual(joined_str, 'foo and bar')
        
    def test_join_str_seq_w_commas_and_conjunction_4(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction(('foo', 'bar', 'baz'), 'and')
        self.assertEqual(joined_str, 'foo, bar, and baz')

    def test_join_str_seq_w_commas_and_conjunction_1(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction((), 'or')
        self.assertEqual(joined_str, '')
        
    def test_join_str_seq_w_commas_and_conjunction_2(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction(('foo',), 'or')
        self.assertEqual(joined_str, 'foo')
        
    def test_join_str_seq_w_commas_and_conjunction_3(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction(('foo', 'bar'), 'or')
        self.assertEqual(joined_str, 'foo or bar')
        
    def test_join_str_seq_w_commas_and_conjunction_4(self):
        joined_str = advg.join_str_seq_w_commas_and_conjunction(('foo', 'bar', 'baz'), 'or')
        self.assertEqual(joined_str, 'foo, bar, or baz')
