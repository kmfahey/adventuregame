### ADVISORY

The recommended usage of this code is to run the game `advgame.py` from this
directory and load the package from the current working directory without
installing it. The package is purpose-built for containing the game logic used
by `advgame.py` and has limited potential for reuse. (Although, conceivably, the
D&D object environment defined in `adventuregame.elements` could be reused for
another game that implements Dungeons & Dragons rules.)

*EVEN IF* you install the library however, the `advgame.py` frontend program is
written with the assumption that it will be run from a directory that contains
the `data` directory and its .ini file contents that were distributed with the
game. It can't be used from /usr/local/bin.


#### Background

The author, Kerne M. Fahey, was taking a coding bootcamp course with NuCamp
in python and Devops, and was assigned to write a game of their choosing.
They chose a text-adventure game implementing D&D rules; this package and its
frontend program `advgame.py` was the result.


#### Documentation

docstrings are written into the code and `pydoc` is supported. `pydoc -w` has
been used to generate HTML code documentation; please see `docs` for those
files, as well as Command_Reference.md which replicates the in-game HELP text.


#### Gameplay

The `adventuregame` package implements all the functionality needed to run a
text adventure game, inspired by ADVENT but written to be compatible with basic
Dungeons & Dragons rules. The frontend program `advgame.py` draws on the package
to run the game.

The game takes place in a dungeon. The dungeon features more than a dozen rooms,
where creatures, items and chests can be found. The object of the game is to
find the exit. Some doors and chests are locked; the keys can be found somewhere
in the dungeon.

In play, the player plays one of four classes: Warrior, Thief, Mage or
Priest. The Warrior has the highest hit point total and can use any weapon,
armor or shield in the game. The Thief can pick locks, obviating the need to
find keys in order to advance. The Mage can cast magic missile and use magic
wands, but can't wear armor, use a shield, or use most weapons. The Priest can
cast a healing spell on themself.


#### Implementation Details

The game logic that implements the Dungeons & Dragons rules is found in
`adventuregame.elements`. The ruleset implemented is a simplified version of the
D&D paradigm that draws on both 3rd ed. and 5th ed. conventions. The simplified
rules doesn't use levels, a base attack or proficiency bonus, and a spellcaster
only has one spell to their name.

The adventure game functionality is implemented between `adventuregame.processor`
and `adventuregame.statemsgs`. The processor module is home to a monolithic
`CommandProcessor` class that manages the natural language parsing which
translates the commands entered by a player during the game into game logic.
The `CommandProcessor` class has a method for every command in the game, and a
`process()` method that accepts a natural language string, tokenizes it, strips
off the command prefix, selects the matching method from a dispatch table, and
calls that method with the remainder of the tokens.

A command method always returns a tuple of one or objects that subclass
`Game_State_Message`. That class and its subclasses are found in
`adventuregame.statemsgs`. Every possible outcome from every command is
represented by a separate `Game_State_Message` subclass. Each one has an
`__init__()` method that stores its keyword arguments to attributes, and a
`message` property that contains the logic for translating the semantic content of
the object to a natural language response that can be printed to the UI for the
player to read. There are 95 such subclasses in `adventuregame.statemsgs`.

`CommandProcessor.process()` tail calls the command method. While most outcomes
from a command method can be summarized by a single state message, a tuple is
always returned for uniformity of response from `process()`. Some command methods
need to have several messages printed to the UI in sequence.

The game data is stored in the `data` directory, in .ini format. The 3rd-party
package iniconfig is used to parse the data.

Lastly, `adventuregame.utility` contains a small collection of utility
functions used by the other components of the library, and
`adventuregame.exceptions` defines the Exception subclasses used by the package.

