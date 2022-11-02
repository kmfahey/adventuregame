#!/usr/bin/python3

import textwrap
import functools
import iniconfig

import adventuregame as advg


items_ini_config = iniconfig.IniConfig('./data/items.ini')
doors_ini_config = iniconfig.IniConfig('./data/doors.ini')
containers_ini_config = iniconfig.IniConfig('./data/containers.ini')
creatures_ini_config = iniconfig.IniConfig('./data/creatures.ini')
rooms_ini_config = iniconfig.IniConfig('./data/rooms.ini')

items_state = advg.Items_State(**items_ini_config.sections)
doors_state = advg.Doors_State(**doors_ini_config.sections)
containers_state = advg.Containers_State(items_state, **containers_ini_config.sections)
creatures_state = advg.Creatures_State(items_state, **creatures_ini_config.sections)
rooms_state = advg.Rooms_State(creatures_state, containers_state, doors_state, items_state,
                              **rooms_ini_config.sections)
game_state = advg.Game_State(rooms_state, creatures_state, containers_state, doors_state,
                            items_state)
command_processor = advg.Command_Processor(game_state)

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

""")

while True:
    command = input('Enter command> ')
    result = command_processor.process(command)

    for game_state_message in result:
        print(advg.textwrapper(game_state_message.message))

    if isinstance(result[-1], (advg.Quit_Command_Have_Quit_The_Game,
                               advg.Be_Attacked_by_Command_Character_Death,
                               advg.Leave_Command_Won_The_Game)):
        break

    print()
