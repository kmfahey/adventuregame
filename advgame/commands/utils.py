#!/usr/bin/python3

from math import nan as NaN
from itertools import chain

import advgame.stmsg as stmsg

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.elements import (
    Chest,
    Corpse,
    Door,
    EquippableItem,
    Potion,
    Wand,
    Weapon,
)
from advgame.utils import (
    join_strs_w_comma_conj,
    lexical_number_in_1_99_re,
    lexical_number_to_digits,
    digit_re,
)


__all__ = (
    "_door_selector",
    "_look_at_item_detail",
    "_matching_door",
    "_pick_up_or_drop_preproc",
    "_preprocessing_for_lock_unlock_open_or_close",
    "_put_or_take_preproc",
)


def _door_selector(game_state, tokens):
    # This is a private workhorse method implementing a flexible
    # door specifier syntax. The methods close_command(),
    # leave_command(), lock_command(), look_at_command(),
    # open_command(), pick_lock_command(), pick_up_command(),
    # unlock_command() all use _door_selector() to apply that
    # syntax. A door can be specified using any combination of its
    # compass direction, title, or portal type.
    #
    # :tokens: The arguments token tuple pased to the calling
    # method.
    #
    # * If the door specifier doesn't match any door in the room, a
    # .stmsg.various.DoorNotPresent object is returned
    #
    # * If the door specifier matches more than one door in the
    # room, a .stmsg.various.AmbiguousDoorSpecifier object is
    # returned.

    # These variables are initialized to None so they can be checked
    # for non-None values later.
    compass_dir = door_type = None

    # If the first token is a compass direction, compass_dir is set
    # to it. This method is always called from a context where the
    # last token has tested equal to 'door' or 'doorway', so I rely
    # on that and compose the door title that the door will be found
    # under in RoomsState.
    if tokens[0] in ("north", "east", "south", "west"):
        compass_dir = tokens[0]
        tokens = tokens[1:]

    # If the first token matches 'iron' or 'wooden' and the last
    # token is 'door' (not 'doorway'), I can match the door_type. I
    # construct the door_type value.
    if (
        (len(tokens) == 2 and tokens[0] in ("iron", "wooden") and tokens[1] == "door")
        or len(tokens) == 1
        and tokens[0] == "doorway"
    ):
        door_type = " ".join(tokens).replace(" ", "_")

    # The tuple of doors in the current room is assigned to a local
    # variable, and I iterate across it trying to match compass_dir,
    # door_type, or both. As a fallback, 'door' vs. 'doorway' in the
    # title is tested. Matches are saved to matching_doors.
    doors = game_state.rooms_state.cursor.doors
    matching_doors = list()
    for door in doors:
        if compass_dir is not None and door_type is not None:
            if not (door.title.startswith(compass_dir) and door.door_type == door_type):
                continue
        elif compass_dir is not None:
            if not door.title.startswith(compass_dir):
                continue
        elif door_type is not None:
            if door.door_type != door_type:
                continue
        else:
            if not door.title.endswith(tokens[-1]):
                continue
        matching_doors.append(door)

    # If no doors matched, a door-not-present error is returned.
    if len(matching_doors) == 0:
        return (stmsg.various.DoorNotPresent(compass_dir, tokens[-1]),)
    elif len(matching_doors) > 1:
        # Otherwise if more than one door matches, a
        # ambiguous-door-specifier error is returned. If possible,
        # it's constructed with a door_type value to give a more
        # useful error message.
        compass_dirs = tuple(door.title.split(" ")[0] for door in matching_doors)
        # Checks that all door_types are the same.
        door_type = (
            matching_doors[0].door_type
            if len(set(door.door_type for door in matching_doors)) == 1
            else None
        )
        return (
            stmsg.various.AmbiguousDoorSpecifier(compass_dirs, tokens[-1], door_type),
        )
    else:
        # Otherwise matching_doors is length 1; I have a match, so I
        # return it.
        return matching_doors


def _look_at_item_detail(element):

    # This private utility method handles the task of constructing
    # a detailed description of an item, mentioning everything
    # about it that the game data can show. It doesn't return any
    # GameStateMessage subclass objects; it's a utility method
    # that accomplishes a task that look_command() needs to execute
    # in 3 different places in its code, so it's refactored into its
    # own method.
    #
    # :element: The Item subclass object to derive a detailed
    # description of.

    descr_append_str = ""
    # If the item is equipment, its utility as an equippable item
    # will be detailed.
    if isinstance(element, EquippableItem):
        if isinstance(element, (Wand, Weapon)):
            # If the item can be attacked with, its attack bonus and
            # damage are mentioned.
            descr_append_str = (
                f" Its attack bonus is +{element.attack_bonus} and its damage "
                + f"is {element.damage}. "
            )
        else:
            # isinstance(element, (Armor, Shield))

            # It's a defensive item, so its armor bonus is
            # mentioned.
            descr_append_str = f" Its armor bonus is +{element.armor_bonus}. "
        can_use_list = []
        # All Equippable items have *_can_use attributes expresing
        # class limitations, so I survey those.
        for character_class in ("warrior", "thief", "mage", "priest"):
            if getattr(element, f"{character_class}_can_use", False):
                can_use_list.append(
                    f"{character_class}s" if character_class != "thief" else "thieves"
                )
        # The first class name is titlecased because it's the start
        # of a sentence, and the list of classes is formed into a
        # sentence appended to the working string.
        can_use_list[0] = can_use_list[0].title()
        descr_append_str += join_strs_w_comma_conj(can_use_list, "and")
        descr_append_str += " can use this."
    elif isinstance(element, Potion):
        # If it's a potion, the points recovered are mentioned.
        if element.title == "mana potion":
            descr_append_str = (
                f" It restores {element.mana_points_recovered} mana points."
            )
        elif element.title == "health potion":
            descr_append_str = (
                f" It restores {element.hit_points_recovered} hit points."
            )
    elif isinstance(element, Door):
        # If it's a door, whether it's open or closed is mentioned.
        if element.closeable:
            descr_append_str = " It is closed." if element.is_closed else " It is open."

    # The base element description is returned along with the
    # extended description derived above.
    return element.description + descr_append_str


def _matching_door(game_state, target_door):
    # Fetches the corresponding door object in the room linked to by
    # a door object, so an operation can be performed on both door
    # objects representing the two sides of the same door element.
    # Returns None if the door being tested is the exit door of the
    # dungeon.
    #
    # :target_door: A door object. return: A door object, or None.

    # There's a limitation in the implementations of
    # close_command(), lock_command(), open_command(),
    # pick_lock_command(), and unlock_command(): when targetting
    # a door, the door object that's retrieved to unlock is the
    # one that represents that exit from the current room object;
    # but the other room linked by that door uses a different door
    # object to represent the opposite side of the same notional
    # door game element. In order to operate on the same door in two
    # rooms, both door objects must have their state changed.

    # This dict is used to match opposing door attributes so that
    # the opposite door can be retrieved from the opposite room.
    opposite_compass_door_attrs = {
        "north_door": "south_door",
        "east_door": "west_door",
        "south_door": "north_door",
        "west_door": "east_door",
    }

    # First I iterate across the four possible doors in the current
    # room object to find which door_attr attribute name the door
    # object is stored under.
    door_found_at_attr = None
    for door_attr in ("north_door", "south_door", "east_door", "west_door"):
        found_door = getattr(game_state.rooms_state.cursor, door_attr, None)
        if found_door is target_door:
            door_found_at_attr = door_attr
            break

    # I use the handy method Door.other_room_internal_name(), which
    # returns the internal_name of the linked room when given the
    # internal_name of the room the player is in.
    other_room_internal_name = target_door.other_room_internal_name(
        game_state.rooms_state.cursor.internal_name
    )

    # If the door is the exit to the dungeon, it will have 'Exit' as
    # its other_room_internal_name. There is no far room or far door
    # object, so I return None.
    if other_room_internal_name == "Exit":
        return None

    # Otherwise, I fetch the opposite room, and use the
    # opposite_door_attr to fetch the other door object that
    # represents the other side of the game element door from the
    # door object that I've got, and return it.
    opposite_room = game_state.rooms_state.get(other_room_internal_name)
    opposite_door_attr = opposite_compass_door_attrs[door_found_at_attr]
    opposite_door = getattr(opposite_room, opposite_door_attr)
    return opposite_door


# Both PUT and TAKE have the same preprocessing challenges, so I
# refactored their logic into a shared private preprocessing method.


def _pick_up_or_drop_preproc(command, tokens):
    # This private workhorse method handles argument processing
    # logic which is common to pick_up_command() and drop_command().
    # It detects the quantity intended and screens for ambiguous
    # command arguments.
    #
    # :command: The command the calling method is executing. tokens:
    # :The tokenized command arguments.
    #
    # * If invalid arguments are sent, returns a
    # .stmsg.command.BadSyntax object.
    #
    # * If the player submitted an ungrammatical
    # sentence which is ambiguous as to the quantity
    # intended, a .stmsg.drop.QuantityUnclear object or a
    # .stmsg.pickup.QuantityUnclear object is returned depending on
    # the value in command.

    # This long boolean checks whether the first token in tokens can
    # indicate quantity.
    if (
        tokens[0] in ("a", "an", "the")
        or tokens[0].isdigit()
        or lexical_number_in_1_99_re.match(tokens[0])
    ):
        # If the quantity indicator is all there is, a syntax error
        # is returned.
        if len(tokens) == 1:
            return (
                stmsg.command.BadSyntax(
                    command.upper(), COMMANDS_SYNTAX[command.upper()]
                ),
            )
        # The item title is formed from the rest of the tokens.
        item_title = " ".join(tokens[1:])

        # If the first token is an indirect article...
        if tokens[0] == "a" or tokens[0] == "an":
            if tokens[-1].endswith("s"):
                # but the end of the last token has a pluralizing
                # 's' on it, I return a quantity-unclear error
                # appropriate to the caller.
                return (
                    (stmsg.drop.QuantityUnclear(),)
                    if command.lower() == "drop"
                    else (stmsg.pickup.QuantityUnclear(),)
                )
            # Otherwise it implies a quantity of 1.
            item_quantity = 1
        elif tokens[0].isdigit():

            # Otherwise if it parses as an int, I save that
            # quantity.
            item_quantity = int(tokens[0])

        # If it's a direct article...
        elif tokens[0] == "the":

            # And the last token ends with a pluralizing 's', the
            # player means to pick up or drop the total quantity
            # possible. I don't know what that is now, so I set the
            # item_quantity to nan as a signal value. When the
            # caller gets as far as identifying the total quantity
            # possible, it will replace this value with that one.
            if tokens[-1].endswith("s"):
                item_quantity = NaN
            else:
                # Otherwise it implies a quantity of 1.
                item_quantity = 1
        else:
            # Based on the enclosing conditional, this else implies
            # lexical_number_in_1_99_re.match(tokens[0]) ==
            # True. So I use lexical_number_to_digits to parse
            # the 1st token to an int.
            item_quantity = lexical_number_to_digits(tokens[0])

            # lexical_number_to_digits also uses NaN as a
            # signal value; it returns that value if the lexical
            # number was outside the range of one to ninety-nine. If
            # so, I return a syntax error.
            if item_quantity is NaN:
                return (
                    stmsg.command.BadSyntax(
                        command.upper(), COMMANDS_SYNTAX[command.upper()]
                    ),
                )
        if item_quantity == 1 and item_title.endswith("s"):
            # Repeating an earlier check on a wider set. If
            # the item_quantity is 1 but the last token ends
            # in a pluralizing 's', I return the appropriate
            # quantity-unclear value.
            return (
                (stmsg.drop.QuantityUnclear(),)
                if command.lower() == "drop"
                else (stmsg.pickup.QuantityUnclear(),)
            )
    else:
        # I form the item title.
        item_title = " ".join(tokens)

        # The first token didn't parse as any kind of number, so I
        # if the item_title ends with a pluralizing 's'.
        if item_title.endswith("s"):
            # If so, the player is implying they want the total
            # quantity possible. As above, I set item_quantity to
            # NaN as a signal value; it'll be replaced by the
            # caller when the total quantity possible is known.
            item_quantity = NaN
        else:

            # Otherwise item_quantity is implied to be 1.
            item_quantity = 1
    item_title = item_title.rstrip("s")

    # Return the item_quantity and item_title parsed from tokens as
    # a 2-tuple.
    return item_quantity, item_title


# This private workhorse method handles the shared logic between
# lock, unlock, open or close:


def _preprocessing_for_lock_unlock_open_or_close(game_state, command, tokens):
    # This private workhorse method handles the shared logic
    # for lock_command(), unlock_command(), open_command() and
    # close_command(). All four commands have the same type of game
    # elements as their targets, and a player specifying such an
    # element has the same failure modes.
    #
    # :command: The command that the calling method was executing.
    # One of LOCK, UNLOCK, OPEN, or CLOSE.
    # :tokens: The arguments that the calling method was called
    # with. Must be non-null.
    #
    # * If the calling command received a zero-length tokens
    # argument, a syntax error is returned. The COMMANDS_SYNTAX used
    # for the error uses the command argument iso t matches the
    # calling method's context
    #
    # * If the specified game element is not present in the
    # current room, one of .stmsg.unlock.ElementToUnlockNotHere,
    # .stmsg.lock.ElementToLockNotHere,
    # .stmsg.open_.ElementtoOpenNotHere, or
    # .stmsg.close.ElementToCloseNotHere is returned, depending on
    # the command argument
    #
    # * If the specified game element is a corpse, creature,
    # doorway or item, it's an invalid element for any of the
    # calling methods; one of .stmsg.lock.ElementNotLockable,
    # .stmsg.unlock.ElementNotUnlockable,
    # .stmsg.open_.ElementNotOpenable, or
    # .stmsg.close.ElementNotClosable is returned, depending on the
    # command argument.

    # If the command was used with no arguments, a syntax error is
    # returned.
    if not len(tokens):
        return (
            stmsg.command.BadSyntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),
        )

    # door is initialized to None so whether it's non-None later can
    # be a signal.
    door = None

    # These booleans are initialized to False; later if any one of
    # them is true, an error value will be returned.
    tried_to_operate_on_doorway = False
    tried_to_operate_on_creature = False
    tried_to_operate_on_corpse = False
    tried_to_operate_on_item = False

    # If the arguments indicate a door(way), a further private
    # workhorse method _door_selector() is used to implement
    # the flexible door specifier syntax. As always with a private
    # workhorse method, result[0] is type-tested to see if it's a
    # error value. If so, the result tuple is returned.
    if tokens[-1] in ("door", "doorway"):
        result = _door_selector(game_state, tokens)
        if isinstance(result[0], stmsg.GameStateMessage):
            return result
        else:
            # Otherwise, the Door object is extracted. But it may be
            # a doorway, that's tested later.
            (door,) = result

    # The target title is formed, and container_here & creature_here
    # are assigned to local variables as they're referenced
    # frequently.
    target_title = " ".join(tokens) if door is None else door.title
    container = game_state.rooms_state.cursor.container_here
    creature = game_state.rooms_state.cursor.creature_here

    if door is not None:
        # If the Door object is a Doorway, that failure mode boolean
        # is set.
        if door.door_type == "doorway":
            tried_to_operate_on_doorway = True
        else:
            # Otherwise, it's a valid target for the calling method,
            # and it's returned.
            return (door,)
    elif creature is not None and creature.title == target_title:
        # If the target matches the title for the creature in this
        # room, that failure mode boolean is set.
        tried_to_operate_on_creature = True
    elif container is not None and container.title == target_title:
        # If the target matches the title for a container here...
        if isinstance(container, Corpse):
            # If the container is a corpse, that failure mode
            # boolean is set.
            tried_to_operate_on_corpse = True
        else:
            # Otherwise, it's a valid target for the calling method,
            # and it's returned.
            return (container,)

    # If I reach this point, the method is in a failure mode. If a
    # door or chest matched it would already have been returned. If
    # the other three failure modes don't obtain, the fourth-- an
    # item-- is checked for.
    if (
        not any((tried_to_operate_on_doorway, tried_to_operate_on_corpse))
        and game_state.rooms_state.cursor.items_here is not None
    ):
        # The room's items_here State object and the Character's
        # inventory are both searched through looking for an item
        # whose title matches the target.
        for _, item in chain(
            game_state.rooms_state.cursor.items_here.values(),
            game_state.character.list_items(),
        ):
            if item.title != target_title:
                continue
            # If a match is found, that failure mode boolean is set
            # and the loop is broken.
            tried_to_operate_on_item = True
            item_targetted = item
            break

    # If any of the four failure modes occurred, then the
    # player specified an existing element that is not
    # openable/closeable/lockable/unlockable. An appropriate argd
    # is constructed and an appropriate error value is returned
    # identifying the mistargeted element.
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
        if command.lower() == "unlock":
            return (stmsg.unlock.ElementNotLockable(target_title, **argd),)
        elif command.lower() == "lock":
            return (stmsg.lock.ElementNotUnlockable(target_title, **argd),)
        elif command.lower() == "open":
            return (stmsg.open_.ElementNotOpenable(target_title, **argd),)
        else:
            return (stmsg.close.ElementNotCloseable(target_title, **argd),)
    else:
        # Otherwise, the target didn't match *any* game element
        # within the player's reach, so the appropriate error value
        # is returned indicating the target isn't present.
        if command.lower() == "unlock":
            return (stmsg.unlock.ElementToLockNotHere(target_title),)
        elif command.lower() == "lock":
            return (stmsg.lock.ElementToUnlockNotHere(target_title),)
        elif command.lower() == "open":
            return (stmsg.open_.ElementToOpenNotHere(target_title),)
        else:
            return (stmsg.close.ElementToCloseNotHere(target_title),)


def _put_or_take_preproc(game_state, command, tokens):
    # This private workhorse method handles logic that is common to
    # put_command() and take_command(). It determines the quantity,
    # item title, container (and container title) from the tokens
    # argument.
    #
    # :command: The command being executed by the calling method.
    # Either 'PUT' or 'TAKE'.
    # :tokens: The tokens argument the calling method was called
    # with.
    #
    # * If the tokens argument is zero-length or doesn't container
    # the appropriate joinword ('FROM' for TAKE, 'IN' for PUT with
    # chests, or 'ON' for put with corpses), returns a BadSyntax
    # object.
    #
    # * If the arguments are an ungrammatical sentence
    # and are ambiguous about the quantity of the item,
    # returns a .stmsg.put.QuantityUnclear object or a
    # .stmsg.take.QuantityUnclear object.
    #
    # * If the arguments specify a container title that doesn't
    # match the title of the container in the current room, returns
    # a .stmsg.various.ContainerNotFound object.
    #
    # * If the arguments targeted a chest and the chest is closed,
    # returns a .stmsg.various.ContainerIsClosed object.

    # The current room's container_here value is assigned to a local
    # variable.
    container = game_state.rooms_state.cursor.container_here

    command = command.lower()

    # I seek the joinword in the tokens tuple and record its
    # index so I can use it to break the tokens tuple into an
    # item-title-part and a container-title-part.
    if command == "take":
        try:
            joinword_index = tokens.index("from")
        except ValueError:
            joinword_index = -1
        else:
            joinword = "from"
    else:
        # The PUT command uses joinword IN for chests and ON for
        # corpses so I seek either one.
        try:
            joinword_index = tokens.index("on")
        except ValueError:
            joinword_index = -1
        else:
            joinword = "on"
        if joinword_index == -1:
            try:
                joinword_index = tokens.index("in")
            except ValueError:
                joinword_index = -1
            else:
                joinword = "in"

    # If the joinword wasn't found, or if it's at the beginning or
    # end of the tokens tuple, I return a syntax error.
    if joinword_index == -1 or joinword_index == 0 or joinword_index + 1 == len(tokens):
        return (
            stmsg.command.BadSyntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),
        )

    # I use the joinword_index to break the tokens tuple into an
    # item_tokens tuple and a container_tokens tuple.
    item_tokens = tokens[:joinword_index]
    container_tokens = tokens[joinword_index + 1 :]

    # The first token is a digital number, so I cast it to int and
    # set quantity.
    if digit_re.match(item_tokens[0]):
        quantity = int(item_tokens[0])
        item_tokens = item_tokens[1:]

    # The first token is a lexical number, so I convert it and set
    # quantity.
    elif lexical_number_in_1_99_re.match(tokens[0]):
        quantity = lexical_number_to_digits(item_tokens[0])
        item_tokens = item_tokens[1:]

    # The first token is an indirect article, which would mean '1'.
    elif item_tokens[0] == "a" or item_tokens[0] == "an" or item_tokens[0] == "the":
        if len(item_tokens) == 1:
            # item_tokens is *just* ('a',) or ('an',) or ('the',)
            # which is a syntax error.
            return (
                stmsg.command.BadSyntax(
                    command.upper(), COMMANDS_SYNTAX[command.upper()]
                ),
            )
        else:
            # Otherwise quantity is 1.
            quantity = 1
        item_tokens = item_tokens[1:]

    else:
        # I wasn't able to determine quantity which means it's
        # implied; I assume the player means 'the total amount
        # available', and set quantity to NaN as a signal
        # value. The caller will replace this with the total amount
        # available when it's known.
        quantity = NaN

    if item_tokens[-1].endswith("s"):
        if quantity == 1:
            # quantity is 1 but the item title is plural, so I
            # return a syntax error.
            return (
                (stmsg.take.QuantityUnclear(),)
                if command == "take"
                else (stmsg.put.QuantityUnclear(),)
            )

        # I strip the plural s.
        item_tokens = item_tokens[:-1] + (item_tokens[-1].rstrip("s"),)

    if container_tokens[-1].endswith("s"):
        # The container title is plural, which is a syntax error.
        return (
            stmsg.command.BadSyntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),
        )

    if (
        container_tokens[0] == "a"
        or container_tokens[0] == "an"
        or container_tokens[0] == "the"
    ):
        if len(container_tokens) == 1:
            # The container title is *just* ('a',) or ('an',) or
            # ('the',), so I return a syntax error.
            return (
                stmsg.command.BadSyntax(
                    command.upper(), COMMANDS_SYNTAX[command.upper()]
                ),
            )

        # I strip the article from the container tokens.
        container_tokens = container_tokens[1:]

    # I construct the item_title and the container_title.
    item_title = " ".join(item_tokens)
    container_title = " ".join(container_tokens)

    if container is None:

        # There is no container in this room, so I return a
        # container-not-found error.
        return (stmsg.various.ContainerNotFound(container_title),)
    elif not container_title == container.title:

        # The container name specified doesn't match the name of the
        # container in this Room, so I return a container-not-found
        # error.
        return (stmsg.various.ContainerNotFound(container_title, container.title),)

    elif (
        isinstance(container, Chest)
        and joinword == "on"
        or isinstance(container, Corpse)
        and joinword == "in"
    ):

        # The joinword used doesn't match the one appropriate to the
        # type of container here, so I return a syntax error.
        return (
            stmsg.command.BadSyntax(command.upper(), COMMANDS_SYNTAX[command.upper()]),
        )

    elif container.is_closed:

        # The container is closed, so I return a container-is-closed
        # error.
        return (stmsg.various.ContainerIsClosed(container.title),)

    # All the error checks passed, so I return the values determined
    # from the tokens argument.
    return quantity, item_title, container_title, container
