#!/usr/bin/python3

import os
import unittest

from tests import *


for testing_data_file in ('./testing_data/items.ini', './testing_data/doors.ini', './testing_data/containers.ini',
                          './testing_data/creatures.ini', './testing_data/rooms.ini'):
    if os.path.exists(testing_data_file):
        continue
    else:
        raise advg.InternalError(f"Could not access testing data file '{testing_data_file}'. Please contains the "
                                 + "'testing_data' directory distributed with the game.")


unittest.main()
