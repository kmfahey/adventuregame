#!/usr/bin/python3

from .test_attack_command import Test_Attack_1, Test_Attack_2
from .test_begin_game_command import Test_Begin_Game
from .test_cast_spell_command import Test_Cast_Spell
from .test_close_command import Test_Close
from .test_drink_command import Test_Drink
from .test_drop_command import Test_Drop
from .test_equip_command import Test_Equip_1, Test_Equip_2
from .test_help_command import Test_Help_1, Test_Help_2
from .test_inventory_command import Test_Inventory
from .test_leave_command import Test_Leave
from .test_lock_command import Test_Lock
from .test_look_at_command import Test_Look_At_1, Test_Look_At_2
from .test_open_command import Test_Open
from .test_pick_lock_command import Test_Pick_Lock
from .test_pick_up_command import Test_Pick_Up
from .test_processor_class import Test_Processor_Process
from .test_put_command import Test_Put
from .test_quit_command import Test_Quit
from .test_setname_setcls_reroll_begin_commands import (
    Test_Set_Name_Vs_Set_Class_Vs_Reroll_Vs_Begin_Game,
)
from .test_status_command import Test_Status
from .test_take_command import Test_Take
from .test_unequip_command import Test_Unequip_1, Test_Unequip_2
from .test_unlock_command import Test_Unlock


__all__ = (
    "Test_Attack_1",
    "Test_Attack_2",
    "Test_Begin_Game",
    "Test_Cast_Spell",
    "Test_Close",
    "Test_Drink",
    "Test_Drop",
    "Test_Equip_1",
    "Test_Equip_2",
    "Test_Help_1",
    "Test_Help_2",
    "Test_Inventory",
    "Test_Leave",
    "Test_Lock",
    "Test_Look_At_1",
    "Test_Look_At_2",
    "Test_Open",
    "Test_Pick_Lock",
    "Test_Pick_Up",
    "Test_Processor_Process",
    "Test_Put",
    "Test_Quit",
    "Test_Set_Name_Vs_Set_Class_Vs_Reroll_Vs_Begin_Game",
    "Test_Status",
    "Test_Take",
    "Test_Unequip_1",
    "Test_Unequip_2",
    "Test_Unlock",
)
