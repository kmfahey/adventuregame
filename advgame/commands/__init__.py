#!/usr/bin/python3

from advgame.commands.attack import attack_command
from advgame.commands.castspl import cast_spell_command
from advgame.commands.constants import (
    COMMANDS_HELP,
    COMMANDS_SYNTAX,
    INGAME_COMMANDS,
    PREGAME_COMMANDS,
    SPELL_DAMAGE,
    SPELL_MANA_COST,
    STARTER_GEAR,
    VALID_NAME_RE,
)


__all__ = "attack_command", "cast_spell_command"

__all__ += (
    "COMMANDS_HELP",
    "COMMANDS_SYNTAX",
    "INGAME_COMMANDS",
    "PREGAME_COMMANDS",
    "SPELL_DAMAGE",
    "SPELL_MANA_COST",
    "STARTER_GEAR",
    "VALID_NAME_RE",
)
