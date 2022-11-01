#!/usr/bin/python3

from adventuregame import *


items_ini_config = iniconfig_obj_from_ini_text(items_ini_config_text)
doors_ini_config = iniconfig_obj_from_ini_text(doors_ini_config_text)
containers_ini_config = iniconfig_obj_from_ini_text(containers_ini_config_text)
creatures_ini_config = iniconfig_obj_from_ini_text(creatures_ini_config_text)
rooms_ini_config = iniconfig_obj_from_ini_text(rooms_ini_config_text)

items_state = Items_State(**items_ini_config.sections)
doors_state = Doors_State(**doors_ini_config.sections)
containers_state = Containers_State(items_state, **containers_ini_config.sections)
creatures_state = Creatures_State(items_state, **creatures_ini_config.sections)
rooms_state = Rooms_State(creatures_state, containers_state, doors_state, items_state,
                              **rooms_ini_config.sections)
game_state = Game_State(rooms_state, creatures_state, containers_state, doors_state,
                            items_state)
command_processor = Command_Processor(game_state)

while True:
    command = input('Enter command> ')
    result = command_processor.process(command)
    for message in result:
        print(message.message)
    if isinstance(result[-1], (Quit_Command_Have_Quit_The_Game,
                               Be_Attacked_by_Command_Character_Death,
                               Leave_Command_Won_The_Game)):
        break
    print()
