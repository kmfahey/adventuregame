#!/usr/bin/python3

"""
Run a text-adventure game in the style of the old BSD UNIX game ADVENT,
augmented with limited Dungeons-&-Dragons-style rules. Can model a
player playing a specific class (one of Warrior, Thief, Mage or Priest),
exploring a dungeon room to room, fighting creatures, looting chests and
corpses, finding keys and discovering the exit to the dungeon (which is
the win condition).

* advgame.errors comprises the exceptions used by the package.

* advgame.utils comprises a small collection of utility functions used
by the package.

* advgame.elements comprises the base layer: the game element object
environment used by the package, featureing OO representations of game
elements such as rooms, doors, items, creatures, containers and the
character themself.

* advgame.process comprises a higher-level layer that handles processing
commands entered by the player and returning semantic return values.

* advgame.statemsgs comprises the return values used in advgame.process;
an abstract base class and a large collection of subclasses each
of which implements a specific result case of one or more specific
commands.
"""

from advgame.elements import (
    AbilityScores,
    Armor,
    Character,
    Chest,
    Coin,
    Container,
    ContainersState,
    Corpse,
    Creature,
    CreaturesState,
    Door,
    DoorsState,
    Doorway,
    Equipment,
    EquippableItem,
    GameState,
    IniEntry,
    IronDoor,
    Item,
    ItemsMultiState,
    ItemsState,
    Key,
    Oddment,
    Potion,
    Room,
    RoomsState,
    Shield,
    State,
    Wand,
    Weapon,
    WoodenDoor,
)
from advgame.errors import BadCommandError, InternalError
from advgame.process import CommandProcessor
from advgame.statemsgs import (
    GameStateMessage,
    attack,
    be_atkd,
    begin,
    castspl,
    close,
    command,
    drink,
    drop,
    equip,
    help_,
    inven,
    leave,
    lock,
    lookat,
    open_,
    pickup,
    pklock,
    put,
    quit,
    reroll,
    setcls,
    setname,
    status,
    take,
    unequip,
    unlock,
    various,
)
from advgame.utils import (
    join_strs_w_comma_conj,
    lexical_number_to_digits,
    roll_dice,
    textwrapper,
    usage_verb,
)


__version__ = "0.9.001"


# From advgame.elements
__all__ = (
    "AbilityScores",
    "Armor",
    "Character",
    "Chest",
    "Coin",
    "Container",
    "ContainersState",
    "Corpse",
    "Creature",
    "CreaturesState",
    "Door",
    "DoorsState",
    "Doorway",
    "Equipment",
    "EquippableItem",
    "GameState",
    "IniEntry",
    "IronDoor",
    "Item",
    "ItemsMultiState",
    "ItemsState",
    "Key",
    "Oddment",
    "Potion",
    "Room",
    "RoomsState",
    "Shield",
    "State",
    "Wand",
    "Weapon",
    "WoodenDoor",
)

# From advgame.errors
__all__ += (
    "BadCommandError",
    "InternalError",
)

# From advgame.process
__all__ += ("CommandProcessor",)

# From advgame.statemsgs
__all__ += (
    "attack",
    "be_atkd",
    "begin",
    "castspl",
    "close",
    "command",
    "drink",
    "drop",
    "equip",
    "help_",
    "inven",
    "leave",
    "lock",
    "lookat",
    "open_",
    "pklock",
    "pickup",
    "put",
    "quit",
    "reroll",
    "setcls",
    "setname",
    "status",
    "take",
    "unequip",
    "unlock",
    "various",
    "GameStateMessage",
)

# From advgame.utils
__all__ = (
    "join_strs_w_comma_conj",
    "lexical_number_to_digits",
    "usage_verb",
    "roll_dice",
    "textwrapper",
)
