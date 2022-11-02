This library implements all the functionality needed to run a fairly complex
text adventure game, inspired by ADVENT but written to be compatible with basic
Dungeons & Dragons rules. The frontend script advgame.py draws on the library to
run the game.

The game takes place in an underground vault. The vault features more than a
dozen rooms, where creatures, items and chests can be found. The object of the
game is to find the exit. Some doors and chests are locked; the keys can be
found somewhere in the vault.

The game logic that implements the Dungeons & Dragons rules is found in
adventuregame.elements. The ruleset implemented is a simplified version of the
D&D paradigm, not specific to any edition, and doesn't use levels, a base attack
or proficiency bonus, or more than one spell per spellcasting class.

The adventure game functionality is implemented between adventuregame.processor
and adventuregame.statemsg. The processor module is home to a monolithic
Command\_Processor class, that manags the natural language parsing which
translates the commands entered by a player during the game into game logic.
The Command\_Processor class has a method for every command in the game, and a
processor() method that accepts a natural language string, tokenizes it, strips
off the command prefix, selects the matching method from a dispatch table, and
calls that method with the remainder of the tokens.

A command method always returns a tuple of one or objects that subclass
Game\_State\_Message. That class and its subclasses are found in
adventuregame.statemsgs. Every possible outcome from every command is
represented by a separate Game\_State\_Message subclass. Each one has an
\_\_init\_\_ method that stores its keyword arguments to attributes, and a
message property that contains the logic for translating the semantic content of
the object to a natural language response that can be printed to the UI for the
player to read. There are 89 such subclasses in adventuregame.statemsgs.

Command\_Processor.process() tail calls the command method. While most outcomes
from a command method can be summarized by a single state message, a tuple is
always returned for uniformity of response from process(). Some command methods
need to have several messages printed to the UI in sequence.

The game data is stored in adventuregame.data. The data-- including collections
of rooms, doors, containers, creatures, items, and chests-- is recorded in
.ini format. The 3rd-party package iniconfig is used to parse the data. The
different data files are stored as multi-line strings in data.py to avoid
keeping non-python files in the module hierarchy. iniconfig has a limitation in
that it only accepts a filesystem path to parse, rather than any iterable \_io
object, so a utility function iniconfig\_obj\_from\_ini\_text() is included that
stores a multiline string of .ini data to a temporary file and then parses it to
an IniConfig object.

Last but not least, adventuregame.utility contains a small collection of utility
functions used by the other components of the library.
