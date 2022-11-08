#!/usr/bin/python3

import textwrap
import functools
import iniconfig
import os

import adventuregame as advg


### Establishing the game data object environment ###

# Stage 0: a pertinent error message
#
# The game relies on its game data directory to run. This step checks for
# the data files, so the user gets a helpful error message informing them
# how to resolve the issue, rather than the somewhat opaque exception that
# iniconfig.IniConfig's constructor would raise.

for game_data_file in ('./data/items.ini', './data/doors.ini', 
                       './data/containers.ini', './data/creatures.ini',
                       './data/rooms.ini'):
    if os.path.exists(game_data_file):
        continue
    else:
        raise advg.Internal_Exception(
            f"Could not access game data file '{game_data_file}'. Please "
             "ensure you are running this program from a directory that "
             "contains the 'data' directory distributed with the game.")

# Stage 1: parsing the config files
# 
# The first step oThis stage uses IniConfig to load the game data files from
# ./data/ . Each one becomes an IniConfig object, with a .sections attribute
# that is a dict-of-dicts representation of the .ini file data.

items_ini_config = iniconfig.IniConfig('./data/items.ini')
doors_ini_config = iniconfig.IniConfig('./data/doors.ini')
containers_ini_config = iniconfig.IniConfig('./data/containers.ini')
creatures_ini_config = iniconfig.IniConfig('./data/creatures.ini')
rooms_ini_config = iniconfig.IniConfig('./data/rooms.ini')

# Stage 2: instancing the state objects.
# 
# Each state class can initialize itself from a **dict-of-dicts argument, so
# I initialize the state objects from the parsed .ini data files. Some state
# objects require other ones as arguments to initialize properly, so this
# proceeds in order from simple to complex.

items_state = advg.Items_State(**items_ini_config.sections)
doors_state = advg.Doors_State(**doors_ini_config.sections)
containers_state = advg.Containers_State(items_state, 
                                         **containers_ini_config.sections)
creatures_state = advg.Creatures_State(items_state, 
                                       **creatures_ini_config.sections)
rooms_state = advg.Rooms_State(creatures_state, containers_state, doors_state, 
                              items_state, **rooms_ini_config.sections)
game_state = advg.Game_State(rooms_state, creatures_state, containers_state, 
                             doors_state, items_state)

# Stage 3: instancing the Command_Processor object.
# 
# The state objects are summarized by a Game_State object, which is the
# sole argument to Command_Processor.__init__. Its methods will consult the
# game_state object to interact with the game's object environment.
command_processor = advg.Command_Processor(game_state)


# The game has a splash page. I didn't author the headline text
# myself, an online generator did it for me. The generator is here:
# <https://www.patorjk.com/software/taag/>.

print("""Welcome to...
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

""")

# input() builtin, and Command_Processor.process() is used to interpret &
# execute them.
#
# process() returns a tuple of adventuregame.statemsgs.Game_State_Message
# subclass objects; they always have a message property which returns a natural
# language response to the command. It is either an error message or it
# describes the results of a successful command.
while True:
    try:
        command = input('Enter command> ')
    except (EOFError, KeyboardInterrupt):
        exit(0)

    print()

    result = command_processor.process(command)

    # Game_State_Message subclass objects' message properties return one or more
    # long lines of text, so adventuregame.utility.textwrapper is used to wrap
    # the messages to 80 columns.
    for game_state_message in result:
        print(advg.textwrapper(game_state_message.message))

    # Any one of these three Game_State_Message subclass objects signifies the
    # end of the game. If one of them occurs at the end of a list of state
    # messages, the game exits.
    if isinstance(result[-1], (advg.Quit_Command_Have_Quit_The_Game,
                               advg.Be_Attacked_by_Command_Character_Death,
                               advg.Leave_Command_Won_The_Game)):
        exit(0)

    print()
