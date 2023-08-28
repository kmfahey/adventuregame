#!/usr/bin/python3

from itertools import chain

from advgame import stmsg as stmsg

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.commands.utils import _door_selector, _matching_door

from advgame.elements import (
    Corpse,
    Doorway,
)


__all__ = ("pick_lock_command",)


def pick_lock_command(game_state, tokens):
    """
    Execute the PICK LOCK command. The return value is always in a tuple
    even when it's of length 1. The PICK LOCK command has the following
    usage:

    PICK LOCK ON [THE] <chest name>
    PICK LOCK ON [THE] <door name>

    * If that syntax is not followed, returns a .stmsg.command.BadSyntaxGSM
    object.

    * If the player tries to use this command while playing a Warrior, Mage
    or Priest, returns a .stmsg.command.ClassRestrictedGSM object.

    * If the arguments specify a door, and that door is not present in the
    current room, returns a .stmsg.various.DoorNotPresentGSM object.

    * If the arguments specify a door, and more than one door matches that
    specification, returns a .stmsg.various.AmbiguousDoorSpecifierGSM object.

    * If the arguments specify a doorway, creature, item, or corpse, returns
    a .stmsg.pklock.ElementNotLockpickableGSM object.

    * If the arguments specify a chest that is not present in the current
    room, returns a .stmsg.pklock.TargetNotFoundGSM object.

    * If the arguments specify a door or chest is that is already unlocked,
    returns a .stmsg.pklock.TargetNotLockedGSM object.

    * Otherwise, the specified door or chest has its is_locked attribute set
    to False, and a .stmsg.pklock.TargetHasBeenUnlockedGSM object is returned.
    """
    # These error booleans are initialized to False so they can be
    # checked for True values later.
    tried_to_operate_on_doorway = False
    tried_to_operate_on_creature = False
    tried_to_operate_on_corpse = False
    tried_to_operate_on_item = False

    # This command is restricted to Thieves; if the player character
    # is of another class, a command-class-restricted error is
    # returned.
    if game_state.character_class != "Thief":
        return (stmsg.command.ClassRestrictedGSM("PICK LOCK", "thief"),)

    # This command requires an argument. If called with no argument
    # or a patently invalid one, a syntax error is returned.
    if (
        not len(tokens)
        or tokens[0] != "on"
        or tokens == ("on",)
        or tokens
        == (
            "on",
            "the",
        )
    ):
        return (stmsg.command.BadSyntaxGSM("PICK LOCK", COMMANDS_SYNTAX["PICK LOCK"]),)
    elif tokens[:2] == ("on", "the"):
        tokens = tokens[2:]
    elif tokens[0] == "on":
        tokens = tokens[1:]

    # I form the target_title from the tokens.
    target_title = " ".join(tokens)

    # container_here and creature_here are assigned to local
    # variables.
    container = game_state.rooms_state.cursor.container_here
    creature = game_state.rooms_state.cursor.creature_here

    # If the target is a door or doorway. the _door_selector() is
    # used.
    if tokens[-1] in ("door", "doorway"):
        result = _door_selector(game_state, tokens)
        # If it returns an error, the error value is returned.
        if isinstance(result[0], stmsg.GameStateMessage):
            return result
        else:
            # Otherwise, the Door object is extracted from its
            # return value.
            (door,) = result

        # If the Door is a doorway, it can't be unlocked; a failure
        # mode boolean is assigned.
        if isinstance(door, Doorway):
            tried_to_operate_on_doorway = True
        elif not door.is_locked:
            # Otherwise if the door isn't locked, a
            # target-not-locked error value is returned.
            return (stmsg.pklock.TargetNotLockedGSM(target_title),)
        else:
            # This is a door object, and it only represents _this
            # side_ of the door game element; I use _matching_door()
            # to fetch the door object representing the opposite
            # side so that the door game element will be unlocked
            # from the perspective of either room.
            opposite_door = _matching_door(game_state, door)
            if opposite_door is not None:
                opposite_door.is_locked = False

            # The door's is_locked attribute is set to False, and a
            # target-has-been-unlocked value is returned.
            door.is_locked = False
            return (stmsg.pklock.TargetHasBeenUnlockedGSM(target_title),)
    # The target isn't a door. If there is a container here and its
    # title matches....
    elif container is not None and container.title == target_title:
        # If it's a Corpse, the failure mode boolean is set.
        if isinstance(container, Corpse):
            tried_to_operate_on_corpse = True
        elif not getattr(container, "is_locked", False):
            # Otherwise if it's not locked, a target-not-locked
            # error value is returned.
            return (stmsg.pklock.TargetNotLockedGSM(target_title),)
        else:
            # Otherwise, its is_locked attribute is set to False,
            # and a target-has-been-unlocked error is returned.
            container.is_locked = False
            return (stmsg.pklock.TargetHasBeenUnlockedGSM(target_title),)

    # The Door and Chest case have been handled and any possible
    # success value has been rejected. Everything from here on down
    # is error handling.
    elif creature is not None and creature.title == target_title:
        # If there's a creature here and its title matches
        # target_title, that failure mode boolean is set.
        tried_to_operate_on_creature = True
    else:
        # I check through items_here (if any) and the player
        # character's inventory looking for an item with a title
        # matching target_title.
        for _, item in chain(
            (
                game_state.rooms_state.cursor.items_here.values()
                if game_state.rooms_state.cursor.items_here is not None
                else ()
            ),
            game_state.character.list_items(),
        ):
            if item.title != target_title:
                continue
            # If one is found, the appropriate failure mode boolean
            # is set, and the loop is broken.
            tried_to_operate_on_item = True
            item_targetted = item
            break

    # If any of the failure mode booleans were set, the appropriate
    # argd is constructed, and a element-not-unlockable error value
    # is instanced with it and returned.
    if any(
        (
            tried_to_operate_on_doorway,
            tried_to_operate_on_corpse,
            tried_to_operate_on_item,
            tried_to_operate_on_creature,
        )
    ):
        argd = {
            "target_type": "doorway"
            if tried_to_operate_on_doorway
            else "corpse"
            if tried_to_operate_on_corpse
            else "creature"
            if tried_to_operate_on_creature
            else item_targetted.__class__.__name__.lower()
        }
        return (stmsg.pklock.ElementNotLockpickableGSM(target_title, **argd),)
    else:
        # The target_title didn't match anything in the current
        # room, so a target-not-found error value is returned.
        return (stmsg.pklock.TargetNotFoundGSM(target_title),)
