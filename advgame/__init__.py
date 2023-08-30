#!.usr.bin.python3

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

from advgame.commands import (
    COMMANDS_HELP,
    COMMANDS_SYNTAX,
    INGAME_COMMANDS,
    PREGAME_COMMANDS,
    SPELL_DAMAGE,
    SPELL_MANA_COST,
    STARTER_GEAR,
    VALID_NAME_RE,
    attack_command,
    _be_attacked_by_command,
    begin_game_command,
    cast_spell_command,
    close_command,
    drink_command,
    drop_command,
    equip_command,
    help_command,
    inventory_command,
    leave_command,
    lock_command,
    look_at_command,
    open_command,
    pick_up_command,
    pick_lock_command,
    put_command,
    quit_command,
    reroll_command,
    set_class_command,
    set_name_command,
    status_command,
    take_command,
    unequip_command,
    unlock_command,
)
from advgame.data import ini_file_texts
from advgame.elements import AbilityScores, Armor, Character, Chest, Coin, Container, ContainersState, Corpse, Creature, CreaturesState, Door, DoorsState, Doorway, Equipment, EquippableItem, GameState, IniEntry, State, IronDoor, Item, ItemsMultiState, ItemsState, Key, Oddment, Potion, Room, RoomsState, Shield, Wand, Weapon, WoodenDoor
from advgame.errors import BadCommandError, InternalError
from advgame.process import CommandProcessor, Context
from advgame.statemsgs import AmbiguousDoorSpecifierGSM
from advgame.statemsgs import AmountToDrinkUnclearGSM
from advgame.statemsgs import AmountToDropUnclearGSM
from advgame.statemsgs import AmountToPickUpUnclearGSM
from advgame.statemsgs import AmountToPutUnclearGSM
from advgame.statemsgs import AttackHitGSM
from advgame.statemsgs import AttackMissedGSM
from advgame.statemsgs import AttackedAndHitGSM
from advgame.statemsgs import AttackedAndNotHitGSM
from advgame.statemsgs import BadSyntaxGSM
from advgame.statemsgs import CantPickUpChestCorpseCreatureOrDoorGSM
from advgame.statemsgs import CastHealingSpellGSM
from advgame.statemsgs import CharacterDeathGSM
from advgame.statemsgs import ClassCantUseItemGSM
from advgame.statemsgs import ClassRestrictedGSM
from advgame.statemsgs import ContainerIsClosedGSM
from advgame.statemsgs import ContainerNotFoundGSM
from advgame.statemsgs import DisplayHelpForCommandGSM
from advgame.statemsgs import DisplayInventoryGSM
from advgame.statemsgs import DoorIsLockedGSM
from advgame.statemsgs import DisplayRolledStatsGSM
from advgame.statemsgs import DoorNotPresentGSM
from advgame.statemsgs import DrankManaPotionGSM
from advgame.statemsgs import DrankManaPotionWhenNotASpellcasterGSM
from advgame.statemsgs import DroppedItemGSM
from advgame.statemsgs import ElementHasBeenClosedGSM
from advgame.statemsgs import ElementHasBeenLockedGSM
from advgame.statemsgs import ElementHasBeenOpenedGSM
from advgame.statemsgs import ElementHasBeenUnlockedGSM
from advgame.statemsgs import ElementIsAlreadyClosedGSM
from advgame.statemsgs import ElementIsAlreadyLockedGSM
from advgame.statemsgs import ElementIsAlreadyOpenGSM
from advgame.statemsgs import ElementIsAlreadyUnlockedGSM
from advgame.statemsgs import ElementIsLockedGSM
from advgame.statemsgs import ElementNotCloseableGSM
from advgame.statemsgs import ElementNotLockableGSM
from advgame.statemsgs import ElementNotLockpickableGSM
from advgame.statemsgs import ElementNotOpenableGSM
from advgame.statemsgs import ElementNotUnlockableGSM
from advgame.statemsgs import ElementToCloseNotHereGSM
from advgame.statemsgs import ElementToLockNotHereGSM
from advgame.statemsgs import ElementToOpenNotHereGSM
from advgame.statemsgs import ElementToUnlockNotHereGSM
from advgame.statemsgs import EnteredRoomGSM
from advgame.statemsgs import FoeDeathGSM
from advgame.statemsgs import FoundContainerHereGSM
from advgame.statemsgs import FoundCreatureHereGSM
from advgame.statemsgs import FoundDoorOrDoorwayGSM
from advgame.statemsgs import FoundItemOrItemsHereGSM
from advgame.statemsgs import FoundNothingGSM
from advgame.statemsgs import GameBeginsGSM
from advgame.statemsgs import HaveQuitTheGameGSM
from advgame.statemsgs import NameOrClassNotSetGSM
from advgame.statemsgs import ClassSetGSM
from advgame.statemsgs import InsufficientManaGSM
from advgame.statemsgs import InvalidClassGSM
from advgame.statemsgs import InvalidPartGSM
from advgame.statemsgs import ItemEquippedGSM
from advgame.statemsgs import ItemNotDrinkableGSM
from advgame.statemsgs import ItemNotEquippedGSM
from advgame.statemsgs import DontPossessCorrectKeyGSM
from advgame.statemsgs import ItemNotFoundGSM
from advgame.statemsgs import ItemNotFoundInContainerGSM
from advgame.statemsgs import ItemNotInInventoryGSM
from advgame.statemsgs import ItemNotInInventoryGSM
from advgame.statemsgs import ItemOrItemsTakenGSM
from advgame.statemsgs import ItemPickedUpGSM
from advgame.statemsgs import ItemUnequippedGSM
from advgame.statemsgs import LeftRoomGSM
from advgame.statemsgs import NameOrClassNotSetGSM
from advgame.statemsgs import CastDamagingSpellGSM
from advgame.statemsgs import NameSetGSM
from advgame.statemsgs import StatusOutputGSM
from advgame.statemsgs import AmountToTakeUnclearGSM
from advgame.statemsgs import NoCreatureToTargetGSM
from advgame.statemsgs import NoSuchItemInInventoryGSM
from advgame.statemsgs import GameStateMessage, DisplayCommandsGSM
from advgame.statemsgs import NotAllowedNowGSM
from advgame.statemsgs import NotRecognizedGSM
from advgame.statemsgs import NotRecognizedGSM
from advgame.statemsgs import OpponentNotFoundGSM
from advgame.statemsgs import PutAmountOfItemGSM
from advgame.statemsgs import TargetHasBeenUnlockedGSM
from advgame.statemsgs import TargetNotFoundGSM
from advgame.statemsgs import TargetNotLockedGSM
from advgame.statemsgs import TriedToDrinkMoreThanPossessedGSM
from advgame.statemsgs import TryingToDropItemYouDontHaveGSM
from advgame.statemsgs import TryingToDropMoreThanYouHaveGSM
from advgame.statemsgs import TryingToPickUpMoreThanIsPresentGSM
from advgame.statemsgs import TryingToPutMoreThanYouHaveGSM
from advgame.statemsgs import TryingToTakeMoreThanIsPresentGSM
from advgame.statemsgs import UnderwentHealingEffectGSM
from advgame.statemsgs import WonTheGameGSM
from advgame.statemsgs import DontPossessCorrectKeyGSM
from advgame.statemsgs import YouHaveNoWeaponOrWandEquippedGSM

from advgame.utils import (
    join_strs_w_comma_conj,
    lexical_number_to_digits,
    roll_dice,
    textwrapper,
    usage_verb,
)


__all__ = (
    # from advgame.commands.*
    "COMMANDS_HELP",
    "COMMANDS_SYNTAX",
    "INGAME_COMMANDS",
    "PREGAME_COMMANDS",
    "SPELL_DAMAGE",
    "SPELL_MANA_COST",
    "STARTER_GEAR",
    "VALID_NAME_RE",
    "_be_attacked_by_command",
    "attack_command",
    "begin_game_command",
    "cast_spell_command",
    "close_command",
    "drink_command",
    "drop_command",
    "equip_command",
    "help_command",
    "inventory_command",
    "leave_command",
    "lock_command",
    "look_at_command",
    "open_command",
    "pick_lock_command",
    "pick_up_command",
    "put_command",
    "quit_command",
    "reroll_command",
    "set_class_command",
    "set_name_command",
    "status_command",
    "take_command",
    "unequip_command",
    "unlock_command",
    # from advgame.data
    # from advgame.elements.*
    "IniEntry",
    "State",
    "AbilityScores",
    "Character",
    "Equipment",
    "GameState",
    "ItemsMultiState",
    "ItemsState",
    "Chest",
    "Container",
    "ContainersState",
    "Corpse",
    "Creature",
    "CreaturesState",
    "Door",
    "DoorsState",
    "Doorway",
    "IronDoor",
    "WoodenDoor",
    "Armor",
    "Coin",
    "EquippableItem",
    "Item",
    "Key",
    "Oddment",
    "Potion",
    "Shield",
    "Wand",
    "Weapon",
    "Room",
    "RoomsState",
    # from advgame.errors
    "BadCommandError",
    "InternalError",
    # from advgame.process
    "CommandProcessor",
    # from advgame.statemsgs.*
    "AmbiguousDoorSpecifierGSM",
    "AmountToDrinkUnclearGSM",
    "AmountToDropUnclearGSM",
    "AmountToPickUpUnclearGSM",
    "AmountToPutUnclearGSM",
    "AmountToTakeUnclearGSM",
    "AttackHitGSM",
    "AttackMissedGSM",
    "AttackedAndHitGSM",
    "AttackedAndNotHitGSM",
    "BadSyntaxGSM",
    "CantPickUpChestCorpseCreatureOrDoorGSM",
    "CastDamagingSpellGSM",
    "CastHealingSpellGSM",
    "CharacterDeathGSM",
    "ClassCantUseItemGSM",
    "ClassRestrictedGSM",
    "ClassSetGSM",
    "ContainerIsClosedGSM",
    "ContainerNotFoundGSM",
    "DisplayCommandsGSM",
    "DisplayHelpForCommandGSM",
    "DisplayInventoryGSM",
    "DisplayRolledStatsGSM",
    "DontPossessCorrectKeyGSM",
    "DontPossessCorrectKeyGSM",
    "DoorIsLockedGSM",
    "DoorNotPresentGSM",
    "DrankManaPotionGSM",
    "DrankManaPotionWhenNotASpellcasterGSM",
    "DroppedItemGSM",
    "ElementHasBeenClosedGSM",
    "ElementHasBeenLockedGSM",
    "ElementHasBeenOpenedGSM",
    "ElementHasBeenUnlockedGSM",
    "ElementIsAlreadyClosedGSM",
    "ElementIsAlreadyLockedGSM",
    "ElementIsAlreadyOpenGSM",
    "ElementIsAlreadyUnlockedGSM",
    "ElementIsLockedGSM",
    "ElementNotCloseableGSM",
    "ElementNotLockableGSM",
    "ElementNotLockpickableGSM",
    "ElementNotOpenableGSM",
    "ElementNotUnlockableGSM",
    "ElementToCloseNotHereGSM",
    "ElementToLockNotHereGSM",
    "ElementToOpenNotHereGSM",
    "ElementToUnlockNotHereGSM",
    "EnteredRoomGSM",
    "FoeDeathGSM",
    "FoundContainerHereGSM",
    "FoundCreatureHereGSM",
    "FoundDoorOrDoorwayGSM",
    "FoundItemOrItemsHereGSM",
    "FoundNothingGSM",
    "GameBeginsGSM",
    "GameStateMessage",
    "HaveQuitTheGameGSM",
    "InsufficientManaGSM",
    "InvalidClassGSM",
    "InvalidPartGSM",
    "ItemEquippedGSM",
    "ItemNotDrinkableGSM",
    "ItemNotEquippedGSM",
    "ItemNotFoundGSM",
    "ItemNotFoundInContainerGSM",
    "ItemNotInInventoryGSM",
    "ItemNotInInventoryGSM",
    "ItemOrItemsTakenGSM",
    "ItemPickedUpGSM",
    "ItemUnequippedGSM",
    "LeftRoomGSM",
    "NameOrClassNotSetGSM",
    "NameOrClassNotSetGSM",
    "NameSetGSM",
    "NoCreatureToTargetGSM",
    "NoSuchItemInInventoryGSM",
    "NotAllowedNowGSM",
    "NotRecognizedGSM",
    "NotRecognizedGSM",
    "OpponentNotFoundGSM",
    "PutAmountOfItemGSM",
    "StatusOutputGSM",
    "TargetHasBeenUnlockedGSM",
    "TargetNotFoundGSM",
    "TargetNotLockedGSM",
    "TriedToDrinkMoreThanPossessedGSM",
    "TryingToDropItemYouDontHaveGSM",
    "TryingToDropMoreThanYouHaveGSM",
    "TryingToPickUpMoreThanIsPresentGSM",
    "TryingToPutMoreThanYouHaveGSM",
    "TryingToTakeMoreThanIsPresentGSM",
    "UnderwentHealingEffectGSM",
    "WonTheGameGSM",
    "YouHaveNoWeaponOrWandEquippedGSM",
    # from advgame.utils
    "join_strs_w_comma_conj",
    "lexical_number_to_digits",
    "roll_dice",
    "textwrapper",
    "usage_verb",
)
