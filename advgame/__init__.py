#!/usr/bin/python3

"""
This package implements all the functionality needed to run a text-adventure
game in the style of the old BSD UNIX game ADVENT, augmented with support for
tabletop role-playing game conventions drawn from Dungeons & Dragons. The
functionality here is able to model a player playing a specific class (one of
Warrior, Thief, Mage or Priest), exploring a dungeon room to room, fighting
creatures, looting chests and corpses, finding keys and discovering the exit to
the dungeon (which is the win condition).

* advgame.errors comprises the exceptions used by the package.
* advgame.utils comprises a small collection of utility functions used
  by the package.
* advgame.elements comprises the base layer: the game element object
  environment used by the package, featureing OO representations of game
  elements such as rooms, doors, items, creatures, containers and the character
  themself.
* advgame.process comprises a higher-level layer that handles processing
  commands entered by the player and returning semantic return values.
* advgame.stmsg comprises the return values used in
  advgame.process; an abstract base class and a large collection of
  subclasses each of which implements a specific result case of one or more
  specific commands.
"""

from advgame.process import *
from advgame.elements import *
from advgame.stmsg import *
from advgame.utils import *
from advgame.errors import *

__name__ = 'advgame.__init__'
__version__ = "0.9.001"
