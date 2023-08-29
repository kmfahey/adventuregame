#!/usr/bin/python3

import os
import sys

from iniconfig import IniConfig

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import advgame


__all__ = ("containers_ini_config", "items_ini_config", "doors_ini_config", "creatures_ini_config", "rooms_ini_config",)


containers_ini_config = IniConfig("./testing_data/containers.ini")
items_ini_config = IniConfig("./testing_data/items.ini")
doors_ini_config = IniConfig("./testing_data/doors.ini")
creatures_ini_config = IniConfig("./testing_data/creatures.ini")
rooms_ini_config = IniConfig("./testing_data/rooms.ini")

