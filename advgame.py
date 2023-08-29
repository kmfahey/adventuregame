#!/usr/bin/python3

from iniconfig import IniConfig

from advgame.data import ini_file_texts
from advgame.elements.characters import GameState
from advgame.elements.characters import ItemsState
from advgame.elements.containers import ContainersState, CreaturesState
from advgame.elements.doors import DoorsState
from advgame.elements.rooms import RoomsState
from advgame.process import CommandProcessor
from advgame.stmsg.be_atkd import CharacterDeathGSM
from advgame.stmsg.leave import WonTheGameGSM
from advgame.stmsg.quit import HaveQuitTheGameGSM
from advgame.utils import textwrapper


# Stage 1: establishing the game data object environment

items_ini_config = IniConfig(
    ini_file_texts.get_ini_tmpfile_name(ini_file_texts.ITEMS_INI)
)
doors_ini_config = IniConfig(
    ini_file_texts.get_ini_tmpfile_name(ini_file_texts.DOORS_INI)
)
containers_ini_config = IniConfig(
    ini_file_texts.get_ini_tmpfile_name(ini_file_texts.CONTAINERS_INI)
)
creatures_ini_config = IniConfig(
    ini_file_texts.get_ini_tmpfile_name(ini_file_texts.CREATURES_INI)
)
rooms_ini_config = IniConfig(
    ini_file_texts.get_ini_tmpfile_name(ini_file_texts.ROOMS_INI)
)

for ini_const in (
    ini_file_texts.ITEMS_INI,
    ini_file_texts.DOORS_INI,
    ini_file_texts.CONTAINERS_INI,
    ini_file_texts.CREATURES_INI,
    ini_file_texts.ROOMS_INI,
):
    ini_file_texts.remove_tempfile(ini_const)


# Stage 2: instancing the state objects.
#
# Each state class can initialize itself from a **dict-of-dicts
# argument, so I initialize the state objects from the parsed .ini
# data files. Some state objects require other ones as arguments to
# initialize properly, so this proceeds in order from simple to complex.

items_state = advg.ItemsState(**items_ini_config.sections)

doors_state = advg.DoorsState(**doors_ini_config.sections)

containers_state = advg.ContainersState(items_state, **containers_ini_config.sections)

creatures_state = advg.CreaturesState(items_state, **creatures_ini_config.sections)

rooms_state = advg.RoomsState(
    creatures_state,
    containers_state,
    doors_state,
    items_state,
    **rooms_ini_config.sections
)

game_state = advg.GameState(
    rooms_state, creatures_state, containers_state, doors_state, items_state
)


# Stage 3: instancing the CommandProcessor object.
#
# The state objects are summarized by a GameState object, which is the
# sole argument to CommandProcessor.__init__. Its methods will consult
# the game_state object to interact with the game's object environment.
command_processor = advg.CommandProcessor(game_state)


### Game data object environment established ###


# The game has a splash page. I didn't author the headline text
# myself, an online generator did it for me. The generator is here:
# <https://www.patorjk.com/software/taag/>.

print(
    """Welcome to...
              _                 _                   _____
    /\\      | |               | |                 / ____|
   /  \\   __| |_   _____ _ __ | |_ _   _ _ __ ___| |  __  __ _ _ __ ___   ___
  / /\\ \\ / _` \\ \\ / / _ \\ '_ \\| __| | | | '__/ _ \\ | |_ |/ _` | '_ ` _ \\ / _ \\
 / ____ \\ (_| |\\ V /  __/ | | | |_| |_| | | |  __/ |__| | (_| | | | | | |  __/
/_/    \\_\\__,_| \\_/ \\___|_| |_|\\__|\\__,_|_|  \\___|\\_____|\\__,_|_| |_| |_|\\___|

This is a text adventure that was inspired by ADVENT but extended to implement
basic Dungeons & Dragons rules. Pick a class, navigate the dungeon, kill people
and take their stuff, and try to find the exit! To start the game use the SET
NAME command to pick a name, and SET CLASS to pick a class. Your class can be
one of Warrior, Thief, Mage or Priest.

Warriors can use any weapon, armor or shield, and have the most hit points.
Thieves can pick locks, so you'll never need to find a key. Mages can cast a
damaging spell and use magic wands, but can't wear armor or use shields. And
Priests can cast a healing spell on themselves.

After your name and class are set, your stats will be rolled. If you're not
satisfied, use the REROLL command to reroll until you like the results. After
that, enter BEGIN GAME and enter the dungeon!

(If you don't know what commands to use, the HELP command can help.)

"""
)

# input() builtin, and CommandProcessor.process() is used to interpret &
# execute them.
#
# process() returns a tuple of advgame.stmsg.GameStateMessage subclass
# objects; they always have a message property which returns a natural
# language response to the command. It is either an error message or it
# describes the results of a successful command.
while True:
    try:
        command = input("Enter command> ")
    except (EOFError, KeyboardInterrupt):
        exit(0)

    print()

    if len(command) == 0:
        continue

    result = command_processor.process(command)

    # GameStateMessage subclass objects' message properties return one
    # or more long lines of text, so advgame.utils.textwrapper is used
    # to wrap the messages to 80 columns.
    for game_state_message in result:
        print(advg.textwrapper(game_state_message.message))

    # Any one of these three GameStateMessage subclass objects signifies
    # the end of the game. If one of them occurs at the end of a list of
    # state messages, the game exits.
    if isinstance(
        result[-1],
        (HaveQuitTheGameGSM, CharacterDeathGSM, WonTheGameGSM),
    ):
        exit(0)

    print()
