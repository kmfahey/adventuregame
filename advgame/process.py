#!/usr/bin/python3

"""
The CommandProcessor class which processes a natural-language command
and executes it in the game object environment, modifying the game state
and generating a natural-language response.
"""

import itertools
import math
import operator
import re
import types

from functools import partial as curry

import advgame.stmsg as stmsg

from advgame.commands import attack_command, cast_spell_command
from advgame.commands import (
    COMMANDS_HELP,
    COMMANDS_SYNTAX,
    INGAME_COMMANDS,
    PREGAME_COMMANDS,
    SPELL_DAMAGE,
    SPELL_MANA_COST,
    STARTER_GEAR,
    VALID_NAME_RE,
)

from advgame.errors import InternalError
from advgame.elements import (
    Chest,
    Corpse,
    Door,
    Doorway,
    EquippableItem,
    ItemsMultiState,
    Potion,
    Wand,
    Weapon,
)
from advgame.utils import (
    join_strs_w_comma_conj,
    roll_dice,
    lexical_number_in_1_99_re,
    lexical_number_to_digits,
    digit_re,
)


__all__ = ("CommandProcessor",)


# This module consists solely of the CommandProcessor class and
# its supporting data structures. CommandProcessor is a monolithic
# class that has a process() method which accepts a natural language
# command and dispatches it to the appropriate command method. Every
# command in the game corresponds to a method of the CommandProcessor
# class, and each method always returns a tuple of one or more
# advgame.stmsg.GameStateMessage subclass objects. Typically,
# the bulk of the logic in a given command method is devoted to
# detecting player error and handling each error discretely. The
# logic that completes the command task is often a brief coda to a
# sophisticated conditional handling all the cases where the command
# can't complete.


# FIXME
#
# If this class were to be broken up into a processor class and a family
# of command functions one per module, each command function would need
# to be passed a dict containing only the following values:
#
# command_state = {"game_state": # the GameState instance that
#                                # CommandProcessor was instanced with
#                   "character": # None until the game starts, then the
#                                # Character instance
#                   "game_ending_state_msg": # None until the game ends,
#                                            # then the retval of the
#                                            # game-ending command
#
# There'd also need to be a constants module that the COMMANDS_HELP,
# COMMANDS_SYNTAX, INGAME_COMMANDS, PREGAME_COMMANDS, SPELL_DAMAGE,
# SPELL_MANA_COST, and/or STARTER_GEAR constants could be imported from
# for the functions that need them.


class CommandProcessor(object):
    """
    A processor that can parse a natural language command, modify the
    game state appropriately, and return a GameStateMessage object that
    stringifies to a natural language reply.
    """

    __slots__ = "context", "dispatch_table"

    # All return values from [a-z_]+_command methods in this class are
    # tuples. Every [a-z_]+_command method returns a tuple of one or
    # more advgame.stmsg.GameStateMessage subclass objects
    # reflecting a change or set of changes in game State.
    #
    # For example, an ATTACK action that doesn't kill the foe
    # will prompt the foe to attack. The foe's attack might lead
    # to the character's death. So the return value might be a
    # `.stmsg.attack.AttackHit` object, a `Stmsg_Batkby_AttackedAndHit`
    # object, and a `Stmsg_Batkby_CharacterDeath` object, each bearing a
    # message in its `message` property. The frontend code will iterate
    # through the tuple printing each message in turn.

    @property
    def game_state(self):
        try:
            return self.context["game_state"]
        except KeyError:
            raise AttributeError(
                "CommandProcessor object has no attribute 'game_state'"
            )

    @game_state.setter
    def game_state(self, value):
        self.context["game_state"] = value

    @property
    def game_ending_state_msg(self):
        try:
            return self.context["game_ending_state_msg"]
        except KeyError:
            raise AttributeError(
                "CommandProcessor object has no attribute 'game_ending_state_msg'"
            )

    @game_ending_state_msg.setter
    def game_ending_state_msg(self, value):
        self.context["game_ending_state_msg"] = value

    def __init__(self, game_state):
        """
        Initialize the CommandProcessor before the beginning of the game.

        :gamestate: A GameState object, which is composited of the game's
        RoomsState, CreaturesState, ContainersState, DoorsState, and ItemsState
        objects. Once the character_name and character_class attributes are set
        on this object, a Character object will be added and the game can begin.
        """
        self.context = dict(game_state=None, game_ending_state_msg=None)

        # This GameState object contains & makes available ItemsState,
        # DoorsState, ContainersState, CreaturesState, and RoomsState
        # objects. It will later furnish a Character object when one
        # can be initialized. These comprise the game data that the
        # player interacts with during the game, and have already been
        # initialized by the frontend script before a CommandProcessor
        # object is instantiated.
        self.game_state = game_state

        # This attribute isn't used until the end of the game. Once
        # the game is over, self.game_state.game_has_ended is set to
        # True, and any further commands just get the GameStateMessage
        # subclass object that indicated end of game. It's saved in this
        # attribute.
        self.game_ending_state_msg = None

        # This introspection associates each method whose name ends with
        # _command with a command whose text (with spaces replaced by
        # underscores) is the beginning of that name.
        self.dispatch_table = dict()
        commands_set = PREGAME_COMMANDS | INGAME_COMMANDS
        for method_name in dir(type(self)):
            attrval = getattr(self, method_name, None)
            if not isinstance(attrval, types.MethodType):
                continue
            if not method_name.endswith("_command") or method_name.startswith("_"):
                continue
            command = method_name.rsplit("_", maxsplit=1)[0]
            self.dispatch_table[command] = attrval
            # This exception catches a programmer error if the
            # pregame_commands or ingame_commands wasn't updated with a
            # new command.
            if command not in commands_set:
                raise InternalError(
                    "Inconsistency between set list of commands and command "
                    + "methods found by introspection: method "
                    + f"{method_name}() does not correspond to a command in "
                    + "pregame_commands or ingame_commands."
                )
            commands_set.remove(command)
        # This exception catches a programmer error if a new command
        # was added to pregame_commands or ingame_commands but the
        # corresponding method hasn't been written or was misnamed.
        if len(commands_set) != 0:
            raise InternalError(
                "Inconsistency between set list of commands and command "
                + "methods found by introspection: command "
                + f"'{commands_set.pop()} does not correspond to a command in "
                + "pregame_commands or ingame_commands."
            )

    def cast_spell_command(self):
        pass

    def attack_command(self):
        pass

    def process(self, natural_language_str):
        """
        Process and dispatch a natural language command string. The return value
        is always a tuple even when it's length 1. If the command is not
        recognized, returns a .stmsg.command.NotRecognized object.

        If a ingame command is used during the pregame (before name and class
        have been set and ability scores have been rolled and accepted)
        or a pregame command is used during the game proper, returns a
        .stmsg.command.NotAllowedNow object.

        If this method is called after the game has ended, the same object that
        was returned when the game ended is returned again. Otherwise, the
        command is processed and a state message object is returned.

        :natural_language_str: The player's command input as a natural language
        string.
        """
        if self.game_state.game_has_ended:
            return (self.game_ending_state_msg,)
        tokens = natural_language_str.strip().split()
        command = tokens.pop(0).lower()

        # This block of conditionals is a set of preprocessing steps
        # that handle multi-token commands and commands which can be
        # said different ways.

        if command == "cast" and len(tokens) and tokens[0].lower() == "spell":
            # A two-word command.
            command += "_" + tokens.pop(0).lower()
        elif (
            command == "leave" and len(tokens) and tokens[0].lower() in ("using", "via")
        ):
            # 'via' or 'using' is dropped.
            tokens.pop(0)
        elif command == "begin":
            if (
                len(tokens) >= 1
                and tokens[0].lower() == "game"
                or len(tokens) >= 2
                and tokens[0].lower() == "the"
                and tokens[1].lower() == "game"
            ):
                if tokens[0].lower() == "the":
                    # 'begin the game' becomes 'begin game'.
                    tokens.pop(0)
                command += "_" + tokens.pop(0).lower()
            elif not len(tokens):
                command = "begin_game"
        elif command == "look" and len(tokens) and tokens[0].lower() == "at":
            # A two-word command.
            command += "_" + tokens.pop(0).lower()
        elif (
            command == "pick"
            and len(tokens)
            and (tokens[0].lower() == "up" or tokens[0].lower() == "lock")
        ):
            # Either 'pick lock' or 'pick up', a two-word command.
            command += "_" + tokens.pop(0).lower()
        elif command == "quit":
            if (
                len(tokens) >= 1
                and tokens[0] == "game"
                or len(tokens) >= 2
                and tokens[0:2] == ["the", "game"]
            ):
                if tokens[0] == "the":
                    # 'quit the game' or 'quit game' becomes 'quit'.
                    tokens.pop(0)
                tokens.pop(0)
        elif (
            command == "set"
            and len(tokens)
            and (tokens[0].lower() == "name" or tokens[0].lower() == "class")
        ):
            command += "_" + tokens.pop(0).lower()
            # 'set name to' becomes 'set name'.
            if len(tokens) and tokens[0].lower() == "to":
                # 'set class to' becomes 'set class'.
                tokens.pop(0)
        elif command == "show" and len(tokens) and tokens[0].lower() == "inventory":
            # 'show inventory' becomes 'inventory'.
            command = tokens.pop(0).lower()
        if command not in ("set_name", "set_class"):
            # 'set name' and 'set class' are case-sensitive; the rest of
            # the commands are not.
            tokens = tuple(map(str.lower, tokens))

        # With the command normalized, I check for it in the dispatch
        # table. If it's not present, a NotRecognized error is
        # returned. The commands allowed in the current game mode are
        # included.
        if command not in self.dispatch_table and not self.game_state.game_has_begun:
            return (
                stmsg.command.NotRecognized(
                    command, PREGAME_COMMANDS, self.game_state.game_has_begun
                ),
            )
        elif command not in self.dispatch_table and self.game_state.game_has_begun:
            return (
                stmsg.command.NotRecognized(
                    command, INGAME_COMMANDS, self.game_state.game_has_begun
                ),
            )

        # If the player used an ingame command during the pregame, or
        # a pregame command during the ingame, a NotAllowedNow
        # error is returned with a list of the currently allowed
        # commands included.
        elif not self.game_state.game_has_begun and command not in PREGAME_COMMANDS:
            return (
                stmsg.command.NotAllowedNow(
                    command, PREGAME_COMMANDS, self.game_state.game_has_begun
                ),
            )
        elif self.game_state.game_has_begun and command not in INGAME_COMMANDS:
            return (
                stmsg.command.NotAllowedNow(
                    command, INGAME_COMMANDS, self.game_state.game_has_begun
                ),
            )

        # Having completed all the checks, I have a valid command and
        # there is a matching command method. The command method is tail
        # called with the remainder of the tokens as an argument.
        match command:
            case "attack":
                return attack_command(self.context, tokens)
            case "cast_spell":
                return cast_spell_command(self.context, tokens)
            case _:
                return self.dispatch_table[command](tokens)

    def begin_game_command(self, tokens):
        """
        Execute the BEGIN GAME command. The return value is always
        in a tuple even when it's of length 1. Returns one or more
        statemsgs.GameStateMessage subclass instances. Takes no arguments.

        * If any arguments are given, returns a .stmsg.command.BadSyntax object.

        * If the command is used before the character's name and class have been
        set, returns a .stmsg.begin.NameOrClassNotSet object.

        * Otherwise, returns a .stmsg.begin.GameBegins object, one or more
        .stmsg.various.ItemEquipped objects, and a .stmsg.various.EnteredRoom
        object.
        """
        # This command begins the game. Most of the work done is devoted
        # to creating the character's starting gear and equipping all of
        # it.

        # This command takes no argument; if any were used, a syntax
        # error is returned.
        if len(tokens):
            return (
                stmsg.command.BadSyntax("BEGIN GAME", COMMANDS_SYNTAX["BEGIN GAME"]),
            )

        # The game can't begin if the player hasn't used both SET
        # NAME and SET CLASS yet, so I check for that. If not, a
        # name-or-class-not-set error value is returned.
        character_name = getattr(self.game_state, "character_name", None)
        character_class = getattr(self.game_state, "character_class", None)
        if not character_name or not character_class:
            return (stmsg.begin.NameOrClassNotSet(character_name, character_class),)

        # The error checking is done, so GameState.game_has_begun is set
        # to True, and a game-begins value is used to initialiZe the
        # return_values tuple.
        self.game_state.game_has_begun = True
        return_values = (stmsg.begin.GameBegins(),)

        # A player character receives starting equipment appropriate to
        # their class, as laid out in the STARTER_GEAR dict. The value
        # there is a dict of item types to item internal names. This
        # loop looks up each internal name in the ItemsState object to
        # get an Item subclass object.

        # (This is sorted just to make the results deterministic for
        # ease of testing.) vvvvvv
        for item_type, item_internal_name in sorted(
            STARTER_GEAR[character_class].items(), key=operator.itemgetter(0)
        ):
            item = self.game_state.items_state.get(item_internal_name)
            self.game_state.character.pick_up_item(item)
            # Character.equip_{item_type} is looked up and called with
            # the Item subclass object to equip the character with this
            # item of equipment.
            getattr(self.game_state.character, "equip_" + item_type)(item)

            # An appropriate item-equipped return value, complete with
            # either the updated armor_class value or the updated
            # attack_bonus and damage values, is appended to the
            # return_values tuple.
            if item.item_type == "armor":
                return_values += (
                    stmsg.various.ItemEquipped(
                        item.title,
                        "armor",
                        armor_class=self.game_state.character.armor_class,
                    ),
                )
            elif item.item_type == "shield":
                return_values += (
                    stmsg.various.ItemEquipped(
                        item.title,
                        "shield",
                        armor_class=self.game_state.character.armor_class,
                    ),
                )
            elif item.item_type == "wand":
                return_values += (
                    stmsg.various.ItemEquipped(
                        item.title,
                        "wand",
                        attack_bonus=self.game_state.character.attack_bonus,
                        damage=self.game_state.character.damage_roll,
                    ),
                )
            else:
                return_values += (
                    stmsg.various.ItemEquipped(
                        item.title,
                        "weapon",
                        attack_bonus=self.game_state.character.attack_bonus,
                        damage=self.game_state.character.damage_roll,
                    ),
                )

        # Lastly, an entered-room return value is appended to the
        # return_values tuple, so a description of the first room will
        # print.
        return_values += (
            stmsg.various.EnteredRoom(self.game_state.rooms_state.cursor),
        )

        # From the player's perspective, the frontend printing out this
        # entire sequence of return values can look like:
        #
        # The game has begun!
        # You're now wearing a suit of studded leather armor. Your armor
        # class is now 11.
        # You're now carrying a buckler. Your armor class is now 12.
        # You're now wielding a mace. Your attack bonus is now +1 and
        # your weapon damage is now 1d6+1.
        # Antechamber of dungeon. There is a doorway to the north.

        return return_values

    def _matching_door(self, target_door):
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
            found_door = getattr(self.game_state.rooms_state.cursor, door_attr, None)
            if found_door is target_door:
                door_found_at_attr = door_attr
                break

        # I use the handy method Door.other_room_internal_name(), which
        # returns the internal_name of the linked room when given the
        # internal_name of the room the player is in.
        other_room_internal_name = target_door.other_room_internal_name(
            self.game_state.rooms_state.cursor.internal_name
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
        opposite_room = self.game_state.rooms_state.get(other_room_internal_name)
        opposite_door_attr = opposite_compass_door_attrs[door_found_at_attr]
        opposite_door = getattr(opposite_room, opposite_door_attr)
        return opposite_door

    def close_command(self, tokens):
        """
        Execute the CLOSE command. The return value is always in a tuple even
        when it's of length 1. The CLOSE command has the following usage:

        CLOSE <door name>
        CLOSE <chest name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If there is no matching chest or door in the room, returns a
        .stmsg.close.ElementToCloseNotHere object.

        * If there is no matching door, returns a .stmsg.various.DoorNotPresent
        object.

        * If more than one door in the room matches, returns a
        .stmsg.various.AmbiguousDoorSpecifier object.

        * If the door or chest specified is already closed, returns a
        .stmsg.close.ElementIsAlreadyClosed object.

        * Otherwise, returns a .stmsg.close.ElementHasBeenClosed object.
        """

        # The self.open_command(), self.close_command(),
        # self.lock_command(), and self.unlock_command() share the
        # majority of their logic in a private workhorse method,
        # self._preprocessing_for_lock_unlock_open_or_close().
        result = self._preprocessing_for_lock_unlock_open_or_close("CLOSE", tokens)

        # As with any workhorse method, it either returns an error value
        # or the object to operate on. So I type test if the result
        # tuple's 1st element is a GameStateMessage subclass object. If
        # so, it's returned.
        if isinstance(result[0], stmsg.GameStateMessage):
            return result
        else:
            # Otherwise I extract the element to close.
            (element_to_close,) = result

        # If the element to close is already closed, a
        if element_to_close.is_closed:
            return (stmsg.close.ElementIsAlreadyClosed(element_to_close.title),)
        elif isinstance(element_to_close, Door):
            # This is a door object, and it only represents _this side_
            # of the door game element; I use _matching_door() to fetch
            # the door object representing the opposite side so that the
            # door game element will be closed from the perspective of
            # either room.
            opposite_door = self._matching_door(element_to_close)
            if opposite_door is not None:
                opposite_door.is_closed = True

        # I set the element's is_closed attribute to True, and return an
        # element-has-been-closed value.
        element_to_close.is_closed = True
        return (stmsg.close.ElementHasBeenClosed(element_to_close.title),)

    def drink_command(self, tokens):
        """
        Execute the DRINK command. The return value is always in a tuple even
        when it's of length 1. The DRINK command has the following usage:

        DRINK [THE] <potion name>
        DRINK <number> <potion name>[s]

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the potion specified is not in the character's inventory, returns a
        .stmsg.drink.ItemNotInInventory object.

        * If the name matches an undrinkable item, or a door, chest, creature,
        or corpse, returns a .stmsg.drink.ItemNotDrinkable object.

        * If the <number> argument is used, and there's not that many of the
        potion, returns a .stmsg.drink.TriedToDrinkMoreThanPossessed object.

        * Otherwise, if it's a health potion, then that potion is
        removed from inventory, the character is healed, and returns a
        .stmsg.various.UnderwentHealingEffect object.

        * If it's a mana potion, and the character is a Warrior or a
        Thief, the potion is removed from inventory, and returns a
        .stmsg.drink.DrankManaPotionWhenNotASpellcaster object.

        * If it's a mana potion, and the character is a Mage or a Preist, then
        the potion is removed from inventory, the character has some mana
        restored, and a .stmsg.drink.DrankManaPotion object is returned.
        """
        # This command requires an argument, which may include a direct
        # or indirect article. If that standard isn't met, a syntax
        # error is returned.
        if not len(tokens) or len(tokens) == 1 and tokens[0] in ("the", "a", "an"):
            return (stmsg.command.BadSyntax("DRINK", COMMANDS_SYNTAX["DRINK"]),)

        # Any leading article is stripped, but it signals that the
        # quantity to drink is 1, so qty_to_drink is set.
        if tokens[0] == "the" or tokens[0] == "a":
            qty_to_drink = 1
            tokens = tokens[1:]

        # Otherwise, I check if the first token is a digital or lexical
        # integer.
        elif tokens[0].isdigit() or lexical_number_in_1_99_re.match(tokens[0]):
            # If the first token parses as an int, I cast it and
            # set qty_to_drink. Otherwise, the utility function
            # advgame.utilsities.lexical_number_to_digits() is used
            # to transform a number word to an int.
            qty_to_drink = (
                int(tokens[0])
                if tokens[0].isdigit()
                else lexical_number_to_digits(tokens[0])
            )
            if (qty_to_drink > 1 and not tokens[-1].endswith("s")) or (
                qty_to_drink == 1 and tokens[-1].endswith("s")
            ):
                return (stmsg.command.BadSyntax("DRINK", COMMANDS_SYNTAX["DRINK"]),)

            # The first token is dropped off the tokens tuple.
            tokens = tokens[1:]
        else:

            # No quantifier was detected at the front of the tokens.
            # That implies qty_to_drink = 1; but if the last token has a
            # plural 's', the arguments are ambiguous as to quantity. So
            # a quantity-unclear error is returned.
            qty_to_drink = 1
            if tokens[-1].endswith("s"):
                return (stmsg.drink.QuantityUnclear(),)

        # The initial error checking is out of the way, so we check the
        # Character's inventory for an item with a title that matches
        # the arguments.
        item_title = " ".join(tokens).rstrip("s")
        matching_items_qtys_objs = tuple(
            filter(
                lambda argl: argl[1].title == item_title,
                self.game_state.character.list_items(),
            )
        )

        # The character has no such item, so an item-not-in-inventory
        # error is returned.
        if not len(matching_items_qtys_objs):
            return (stmsg.drink.ItemNotInInventory(item_title),)

        # An item by the title that the player specified was found, so
        # the object and its quantity are saved.
        item_qty, item = matching_items_qtys_objs[0]

        # If the item isn't a potion, an item-not-drinkable error is
        # returned.
        if not item.title.endswith(" potion"):
            return (stmsg.drink.ItemNotDrinkable(item_title),)

        # If the arguments specify a quantity to drink
        # that's greater than the quantity in inventory, a
        # tried-to-drink-more-than-possessed error is returned.
        elif qty_to_drink > item_qty:
            return (
                stmsg.drink.TriedToDrinkMoreThanPossessed(
                    item_title, qty_to_drink, item_qty
                ),
            )

        # I execute the effect of a health potion or a mana potion,
        # depending. Mana potion first.
        elif item.title == "health potion":

            # The amount of healing done by the potion is healed on the
            # character, and the potion is removed from inventory. A
            # underwent-healing-effect value is returned.
            hit_points_recovered = item.hit_points_recovered
            healed_amt = self.game_state.character.heal_damage(hit_points_recovered)
            self.game_state.character.drop_item(item)
            return (
                stmsg.various.UnderwentHealingEffect(
                    healed_amt,
                    self.game_state.character.hit_points,
                    self.game_state.character.hit_point_total,
                ),
            )
        else:
            # item.title == 'mana potion':

            # If the player character isn't a Mage or
            # a Priest, a mana potion does nothing; a
            # drank-mana-potion-when-not-a-spellcaster error is
            # returned.
            if self.game_state.character_class not in ("Mage", "Priest"):
                return (stmsg.drink.DrankManaPotionWhenNotASpellcaster(),)

            # The amount of mana recovery done by the potion is
            # granted to the character, and the potion is removed from
            # inventory. A drank-mana-potion value is returned.
            mana_points_recovered = item.mana_points_recovered
            regained_amt = self.game_state.character.regain_mana(mana_points_recovered)
            self.game_state.character.drop_item(item)
            return (
                stmsg.drink.DrankManaPotion(
                    regained_amt,
                    self.game_state.character.mana_points,
                    self.game_state.character.mana_point_total,
                ),
            )

    def drop_command(self, tokens):
        """
        Execute the DROP command. The return value is always in a tuple even
        when it's of length 1. The DROP command has the following usage:

        DROP <item name>
        DROP <number> <item name>

        * If the item specified isn't in inventory, returns a
        .stmsg.drop.TryingToDropItemYouDontHave object.

        * If a number is specified, and that's more than how many of the item
        are in inventory, returns a
        .stmsg.drop.TryingToDropMorethanYouHave object.

        * If no number is used and the item is equipped, returns a
        .stmsg.various.ItemUnequipped object and a .stmsg.drop.DroppedItem
        object.

        * Otherwise, the item is removed— or the specified number of the item
        are removed— from inventory and a .stmsg.drop.DroppedItem object is
        returned.
        """
        # self.pick_up_command() and self.drop_command()
        # share a lot of logic in a private workhorse method
        # self._pick_up_or_drop_preproc(). As with all private workhorse
        # methods, the return value is a tuple and might consist of an
        # error value; so the 1st element is type tested to see if its a
        # GameStateMessage subclass object.
        result = self._pick_up_or_drop_preproc("DROP", tokens)
        if len(result) == 1 and isinstance(result[0], stmsg.GameStateMessage):

            # The workhorse method returned an error, so I pass that
            # along.
            return result
        else:

            # The workhorse method succeeded, I extract the item to drop
            # and the quantity from its return tuple.
            drop_quantity, item_title = result

        # The quantity of the item on the floor is reported by some
        # drop_command() return values, so I check the contents of
        # items_here.
        if self.game_state.rooms_state.cursor.items_here is not None:
            items_here = tuple(self.game_state.rooms_state.cursor.items_here.values())
        else:
            items_here = ()

        # items_here's contents are filtered looking for an item by a
        # matching title. If one is found, the quantity already in the
        # room is saved to quantity_already_here.
        item_here_pair = tuple(
            filter(lambda pair: pair[1].title == item_title, items_here)
        )
        quantity_already_here = item_here_pair[0][0] if len(item_here_pair) else 0

        # In the same way, the Character's inventory is listed and
        # filtered looking for an item by a matching title.
        items_had_pair = tuple(
            filter(
                lambda pair: pair[1].title == item_title,
                self.game_state.character.list_items(),
            )
        )

        # The player character's inventory doesn't contain an item by
        # that title, so a trying-to-drop-an-item-you-don't-have error
        # is returned.
        if not len(items_had_pair):
            return (stmsg.drop.TryingToDropItemYouDontHave(item_title, drop_quantity),)

        # The item was found, so its object and quantity are saved.
        ((item_had_qty, item),) = items_had_pair

        if drop_quantity > item_had_qty:

            # If the quantity specified to drop is greater than the
            # quantity in inventory, a trying-to-drop-more-than-you-have
            # error is returned.
            return (
                stmsg.drop.TryingToDropMoreThanYouHave(
                    item_title, drop_quantity, item_had_qty
                ),
            )
        elif drop_quantity is math.nan:

            # The workhorse method returns math.nan as the drop_quantity
            # if the arguments didn't specify a quantity. I now know how
            # many the player character has, so I assume they mean to
            # drop all of them. I set drop_quantity to item_had_qty.
            drop_quantity = item_had_qty

        # If the player drops an item they had equipped, and they have
        # none left, it is unequipped. The return tuple is started
        # with unequip_return, which may be empty at the end of this
        # conditional.
        unequip_return = ()
        if drop_quantity - item_had_qty == 0:

            # This only runs if the player character will have none left
            # after this drop. All four equipment types are separately
            # checked to see if they're the item being dropped. The
            # unequip return value needs to specify which game stats
            # have been changed by the unequipping, so this conditional
            # is involved.
            armor_equipped = self.game_state.character.armor_equipped
            weapon_equipped = self.game_state.character.weapon_equipped
            shield_equipped = self.game_state.character.shield_equipped
            wand_equipped = self.game_state.character.wand_equipped

            # If the character's armor is being dropped, it's unequipped
            # and a item-unequipped error value is generated, noting the
            # decreased armor class.
            if (
                item.item_type == "armor"
                and armor_equipped is not None
                and armor_equipped.internal_name == item.internal_name
            ):
                self.game_state.character.unequip_armor()
                unequip_return = (
                    stmsg.various.ItemUnequipped(
                        item.title,
                        item.item_type,
                        armor_class=self.game_state.character.armor_class,
                    ),
                )
            # If the character's shield is being dropped, it's
            # unequipped and a item-unequipped error value is generated,
            # noting the decreased armor class.
            elif (
                item.item_type == "shield"
                and shield_equipped is not None
                and shield_equipped.internal_name == item.internal_name
            ):
                self.game_state.character.unequip_shield()
                unequip_return = (
                    stmsg.various.ItemUnequipped(
                        item_title,
                        "shield",
                        armor_class=self.game_state.character.armor_class,
                    ),
                )

            # If the character's weapon is being dropped, it's
            # unequipped, and an item-unequipped error value is
            # generated.
            elif (
                item.item_type == "weapon"
                and weapon_equipped is not None
                and weapon_equipped.internal_name == item.internal_name
            ):
                self.game_state.character.unequip_weapon()
                if wand_equipped:
                    # If the player character is a mage and has a wand
                    # equipped, the wand's attack values are included
                    # since they will use the wand to attack. (An
                    # equipped wand always takes precedence over a
                    # weapon for a Mage.)
                    unequip_return = (
                        stmsg.various.ItemUnequipped(
                            item_title,
                            "weapon",
                            attack_bonus=self.game_state.character.attack_bonus,
                            damage=self.game_state.character.damage_roll,
                            attacking_with=wand_equipped,
                        ),
                    )
                else:
                    # Otherwise, the player will be informed that they
                    # now can't attack.
                    unequip_return = (
                        stmsg.various.ItemUnequipped(
                            item_title, "weapon", now_cant_attack=True
                        ),
                    )

            # If the character's wand is being dropped, it's unequipped,
            # and an item-unequipped error value is generated.
            elif (
                item.item_type == "wand"
                and wand_equipped is not None
                and wand_equipped.internal_name == item.internal_name
            ):
                self.game_state.character.unequip_wand()
                if weapon_equipped:
                    # If the player has a weapon equipped, the weapon's
                    # attack values are included since they will fall
                    # back on it.
                    unequip_return = (
                        stmsg.various.ItemUnequipped(
                            item_title,
                            "wand",
                            attack_bonus=self.game_state.character.attack_bonus,
                            damage=self.game_state.character.damage_roll,
                            now_attacking_with=weapon_equipped,
                        ),
                    )
                else:
                    # Otherwise, the player will be informed that they
                    # now can't attack.
                    unequip_return = (
                        stmsg.various.ItemUnequipped(
                            item_title, "wand", now_cant_attack=True
                        ),
                    )

        # Finally, with all other preconditions handled, I actually drop
        # the item.
        self.game_state.character.drop_item(item, qty=drop_quantity)

        # If there wasn't a ItemsMultiState set to items_here, I
        # instantiate one.
        if self.game_state.rooms_state.cursor.items_here is None:
            self.game_state.rooms_state.cursor.items_here = ItemsMultiState()

        # The item is saved to items_here with the combined quantity of
        # what was already there (can be 0) and the quantity dropped.
        self.game_state.rooms_state.cursor.items_here.set(
            item.internal_name, quantity_already_here + drop_quantity, item
        )

        # I calculate the quantity left in the character's inventory,
        # and return a dropped-item value with the quantity dropped,
        # the quantity on the floor, and the quantity remaining in
        # inventory.
        quantity_had_now = item_had_qty - drop_quantity
        return unequip_return + (
            stmsg.drop.DroppedItem(
                item_title,
                item.item_type,
                drop_quantity,
                quantity_already_here + drop_quantity,
                quantity_had_now,
            ),
        )

    def equip_command(self, tokens):
        """
        Execute the EQUIP command. The return value is always in a tuple even
        when it's of length 1. The EQUIP command has the following usage:

        EQUIP <armor name>
        EQUIP <shield name>
        EQUIP <wand name>
        EQUIP <weapon name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the item isn't in inventory, returns a
        .stmsg.equip.NoSuchItemInInventory object.

        * If the item can't be used by the character due to their class, returns
        a .stmsg.equip.ClassCantUseItem object.

        * If an item of the same kind is already equipped (for example trying
        to equip a suit of armor when the character is already wearing armor),
        that item is unequipped, the specified item is equipped, and a
        .stmsg.various.ItemUnequipped object and a .stmsg.various.ItemEquipped
        object are returned.

        * Otherwise, the item is equipped, and a .stmsg.various.ItemEquipped
        object is returned.
        """
        # The equip command requires an argument; if none was given, a
        # syntax error is returned.
        if not tokens or len(tokens) == 1 and tokens[0] == "the":
            return (stmsg.command.BadSyntax("EQUIP", COMMANDS_SYNTAX["EQUIP"]),)
        if tokens[0] == "the":
            tokens = tokens[1:]

        # The title of the item to equip is formed from the arguments.
        item_title = " ".join(tokens)

        # The inventory is filtered looking for an item with a matching
        # title.
        matching_item_tuple = tuple(
            item
            for _, item in self.game_state.character.list_items()
            if item.title == item_title
        )

        # If no such item is found in the inventory, a
        # no-such-item-in-inventory error is returned.
        if not len(matching_item_tuple):
            return (stmsg.equip.NoSuchItemInInventory(item_title),)

        # The Item subclass object was found and is saved.
        (item,) = matching_item_tuple[0:1]

        # I check that the item has a {class}_can_use = True attribute.
        # If not, a class-can't-use-item error is returned.
        can_use_attr = self.game_state.character_class.lower() + "_can_use"
        if not getattr(item, can_use_attr):
            return (
                stmsg.equip.ClassCantUseItem(
                    self.game_state.character_class, item_title, item.item_type
                ),
            )

        # This conditional handles checking, for each type of equippable
        # item, whether the player character already has an item of that
        # type equipped; if so, it's unequipped, and a item-unequipped
        # return value is appended to the return values tuple.
        return_values = tuple()
        if item.item_type == "armor" and self.game_state.character.armor_equipped:
            # The player is trying to equip armor but is already wearing
            # armor, so their existing armor is unequipped.
            old_equipped = self.game_state.character.armor_equipped
            self.game_state.character.unequip_armor()
            return_values += (
                stmsg.various.ItemUnequipped(
                    old_equipped.title,
                    old_equipped.item_type,
                    armor_class=self.game_state.character.armor_class,
                ),
            )
        elif item.item_type == "shield" and self.game_state.character.shield_equipped:
            # The player is trying to equip shield but is already
            # carrying a shield, so their existing shield is unequipped.
            old_equipped = self.game_state.character.shield_equipped
            self.game_state.character.unequip_shield()
            return_values += (
                stmsg.various.ItemUnequipped(
                    old_equipped.title,
                    old_equipped.item_type,
                    armor_class=self.game_state.character.armor_class,
                ),
            )
        elif item.item_type == "wand" and self.game_state.character.wand_equipped:
            # The player is trying to equip wand but is already using a
            # wand, so their existing wand is unequipped.
            old_equipped = self.game_state.character.wand_equipped
            self.game_state.character.unequip_wand()
            if self.game_state.character.weapon_equipped:
                return_values += (
                    stmsg.various.ItemUnequipped(
                        old_equipped.title,
                        old_equipped.item_type,
                        attacking_with=self.game_state.character.weapon_equipped,
                        attack_bonus=self.game_state.character.attack_bonus,
                        damage=self.game_state.character.damage_roll,
                    ),
                )
            else:
                return_values += (
                    stmsg.various.ItemUnequipped(
                        old_equipped.title, old_equipped.item_type, now_cant_attack=True
                    ),
                )
        elif item.item_type == "weapon" and self.game_state.character.weapon_equipped:
            # The player is trying to equip weapon but is already
            # wielding a weapon, so their existing weapon is unequipped.
            old_equipped = self.game_state.character.weapon_equipped
            self.game_state.character.unequip_weapon()
            if self.game_state.character.wand_equipped:
                return_values += (
                    stmsg.various.ItemUnequipped(
                        old_equipped.title,
                        old_equipped.item_type,
                        attacking_with=self.game_state.character.wand_equipped,
                        attack_bonus=self.game_state.character.attack_bonus,
                        damage=self.game_state.character.damage_roll,
                    ),
                )
            else:
                return_values += (
                    stmsg.various.ItemUnequipped(
                        old_equipped.title, old_equipped.item_type, now_cant_attack=True
                    ),
                )

        # Now it's time to equip the new item; a item-equipped return
        # value is appended to return_values.
        if item.item_type == "armor":
            # The player is equipping a suit of armor, so the
            # Character.equip_armor() method is called with the item
            # object.
            self.game_state.character.equip_armor(item)
            return_values += (
                stmsg.various.ItemEquipped(
                    item.title,
                    "armor",
                    armor_class=self.game_state.character.armor_class,
                ),
            )
        elif item.item_type == "shield":
            # The player is equipping a shield, so the
            # Character.equip_shield() method is called with the item
            # object.
            self.game_state.character.equip_shield(item)
            return_values += (
                stmsg.various.ItemEquipped(
                    item.title,
                    "shield",
                    armor_class=self.game_state.character.armor_class,
                ),
            )
        elif item.item_type == "wand":
            # The player is equipping a wand, so the
            # Character.equip_wand() method is called with the item
            # object.
            self.game_state.character.equip_wand(item)
            return_values += (
                stmsg.various.ItemEquipped(
                    item.title,
                    "wand",
                    attack_bonus=self.game_state.character.attack_bonus,
                    damage=self.game_state.character.damage_roll,
                ),
            )
        else:
            # The player is equipping a weapon, so the
            # Character.equip_weapon() method is called with the item
            # object.
            self.game_state.character.equip_weapon(item)

            # Because a wand equipped always supercedes any weapon
            # equipped for a Mage, the item-equipped return value is
            # different if a wand is equipped, so this extra conditional
            # is necessary.
            if self.game_state.character.wand_equipped:
                return_values += (
                    stmsg.various.ItemEquipped(
                        item.title,
                        "weapon",
                        attack_bonus=self.game_state.character.attack_bonus,
                        damage=self.game_state.character.damage_roll,
                        attacking_with=self.game_state.character.wand_equipped,
                    ),
                )
            else:
                return_values += (
                    stmsg.various.ItemEquipped(
                        item.title,
                        "weapon",
                        attack_bonus=self.game_state.character.attack_bonus,
                        damage=self.game_state.character.damage_roll,
                    ),
                )

        # The optional item-unequipped value and the item-equipped value
        # are returned.
        return return_values

    def help_command(self, tokens):
        """
        Execute the HELP command. The return value is always in a tuple even
        when it's of length 1. The HELP command has the following usage:

        HELP
        HELP <command name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the command is used with no arguments, returns a
        .stmsg.help_.DisplayCommands object.

        * If the argument is not a recognized command, returns a
        .stmsg.help_.NotRecognized object.

        * Otherwise, returns a .stmsg.help_.DisplayHelpForCommand object.
        """
        # An ordered tuple of all commands in uppercase is displayed in
        # some return values so it is computed.

        # If called with no arguments, the help command displays a
        # generic help message listing all available commands.
        if len(tokens) == 0:
            commands_set = (
                INGAME_COMMANDS if self.game_state.game_has_begun else PREGAME_COMMANDS
            )
            commands_tuple = tuple(
                sorted(strval.replace("_", " ").upper() for strval in commands_set)
            )
            return (
                stmsg.help_.DisplayCommands(
                    commands_tuple, self.game_state.game_has_begun
                ),
            )

        # A specific command was included as an argument.
        else:
            command_uc = " ".join(tokens).upper()
            command_lc = "_".join(tokens).lower()

            # If the command doesn't occur in commands_tuple, a
            # command-not-recognized error is returned.
            if command_lc not in (INGAME_COMMANDS | PREGAME_COMMANDS):
                commands_tuple = tuple(
                    sorted(
                        strval.replace("_", " ").upper()
                        for strval in INGAME_COMMANDS | PREGAME_COMMANDS
                    )
                )
                return (stmsg.help_.NotRecognized(command_uc, commands_tuple),)
            else:
                # Otherwise, a help message for the command specified is
                # returned.
                return (
                    stmsg.help_.DisplayHelpForCommand(
                        command_uc,
                        COMMANDS_SYNTAX[command_uc],
                        COMMANDS_HELP[command_uc],
                    ),
                )

    def inventory_command(self, tokens):
        """
        Execute the INVENTORY command. The return value is always in a tuple
        even when it's of length 1. The INVENTORY command takes no arguments.

        * If the command is used with any arguments, returns a
        .stmsg.command.BadSyntax object.

        * Otherwise, returns a .stmsg.inven.DisplayInventory object.
        """
        # This command takes no arguments; if any are specified, a
        # syntax error is returned.
        if len(tokens):
            return (stmsg.command.BadSyntax("INVENTORY", COMMANDS_SYNTAX["INVENTORY"]),)

        # There's not really any other error case, for once.
        # The inventory contents are stored in a tuple, and a
        # display-inventory value is returned with the tuple to display.
        inventory_contents = sorted(
            self.game_state.character.list_items(), key=lambda argl: argl[1].title
        )
        return (stmsg.inven.DisplayInventory(inventory_contents),)

    def leave_command(self, tokens):
        """
        Execute the LEAVE command. The return value is always in a tuple even
        when it's of length 1. The LEAVE command has the following usage:

        LEAVE [USING or VIA] <compass direction> DOOR
        LEAVE [USING or VIA] <compass direction> DOORWAY
        LEAVE [USING or VIA] <door name>
        LEAVE [USING or VIA] <compass direction> <door name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the door by that name is not present in the room, returns a
        .stmsg.various.DoorNotPresent object.

        * If the door specifier is ambiguous and matches more than one door in
        the room, returns a .stmsg.various.AmbiguousDoorSpecifier object.

        * If the door is the exit to the dungeon, returns a
        .stmsg.leave.LeftRoom object and a .stmsg.leave.WonTheGame object.

        * Otherwise, a .stmsg.leave.LeftRoom object and a
        .stmsg.various.EnteredRoom object are returned.
        """
        # This method takes arguments of a specific form; if the
        # arguments don't match it, a syntax error is returned.
        if (
            not len(tokens)
            or not 2 <= len(tokens) <= 4
            or tokens[-1] not in ("door", "doorway")
        ):
            return (stmsg.command.BadSyntax("LEAVE", COMMANDS_SYNTAX["LEAVE"]),)

        # The format for specifying doors is flexible, and is
        # implemented by a private workhorse method.
        result = self._door_selector(tokens)

        # Like all workhorse methods, it may return an error. result[0]
        # is type-tested if it inherits from GameStateMessage. If it
        # matches, the result tuple is returned.
        if isinstance(result[0], stmsg.GameStateMessage):
            return result
        else:
            # Otherwise, the matching Door object is extracted from
            # result.
            (door,) = result

        # The compass direction door type are extracted from the Door
        # object.
        compass_dir = door.title.split(" ")[0]
        portal_type = door.door_type.split("_")[-1]

        # If the door is locked, a door-is-locked error is returned.
        if door.is_locked:
            return (stmsg.leave.DoorIsLocked(compass_dir, portal_type),)

        # The exit to the dungeon is a special Door object marked with
        # is_exit=True. I test the Door object to see if this is the
        # one.
        if door.is_exit:

            # If so, a left-room value will be returned along with a
            # won-the-game value.
            return_tuple = (
                stmsg.leave.LeftRoom(compass_dir, portal_type),
                stmsg.leave.WonTheGame(),
            )

            # The game_has_ended boolean is set True, and the
            # game-ending return value is saved so that self.process()
            # can return it if the frontend accidentally tries to submit
            # another command.
            self.game_state.game_has_ended = True
            self.game_ending_state_msg = return_tuple[-1]
            return return_tuple

        # Otherwise, RoomsState.move is called with the compass
        # direction, and a left-room value is returned along with a
        # entered-room value.
        self.game_state.rooms_state.move(**{compass_dir: True})
        return (
            stmsg.leave.LeftRoom(compass_dir, portal_type),
            stmsg.various.EnteredRoom(self.game_state.rooms_state.cursor),
        )

    def lock_command(self, tokens):
        """
        Execute the LOCK command. The return value is always in a tuple even
        when it's of length 1. The LOCK command has the following usage:

        LOCK <door name>
        LOCK <chest name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If no such door is present in the room, returns a
        .stmsg.various.DoorNotPresent object.

        * If the command is ambiguous and matches more than one door in the
        room, returns a .stmsg.various.AmbiguousDoorSpecifier object.

        * If the object to lock is not present, returns a
        .stmsg.lock.ElementToLockNotHere object.

        * If the object to lock is already locked, returns a
        .stmsg.lock.ElementIsAlreadyLocked object.

        * If the object to lock is not present, a .stmsg.lock.ElementNotLockable
        is returned.

        * If the character does not possess the requisite door or
        chest key to lock the specified door or chest, returns a
        .stmsg.lock.DontPossessCorrectKey object.

        * Otherwise, the object has its is_locked attribute set to True, and a
        .stmsg.lock.ElementHasBeenLocked object is returned.
        """
        # This command requires an argument, so if tokens is zero-length
        # a syntax error is returned.
        if not len(tokens):
            return (stmsg.command.BadSyntax("LOCK", COMMANDS_SYNTAX["LOCK"]),)

        # A private workhorse method is used for logic shared
        # with self.unlock_command(), self.open_command(),
        # self.close_command().
        result = self._preprocessing_for_lock_unlock_open_or_close("LOCK", tokens)

        # As always with a workhorse method, the result is checked
        # to see if it's an error value. If so, the result tuple is
        # returned as-is.
        if isinstance(result[0], stmsg.GameStateMessage):
            return result
        else:
            # Otherwise, the element to lock is extracted from the
            # return value.
            (element_to_lock,) = result

        # Locking something requires the matching key in inventory. The
        # key's item title is determined, and the player character's
        # inventory is searched for a matching Key object. The object
        # isn't used for anything (it's not expended), so I don't save
        # it, just check if it's there.
        key_required = "door key" if isinstance(element_to_lock, Door) else "chest key"
        if not any(
            item.title == key_required
            for _, item in self.game_state.character.list_items()
        ):
            # Lacking the key, a don't-possess-correct-key error is
            # returned.
            return (
                stmsg.lock.DontPossessCorrectKey(element_to_lock.title, key_required),
            )

        # If the element_to_lock is already locked, a
        # element-is-already-locked error is returned.
        elif element_to_lock.is_locked:
            return (stmsg.lock.ElementIsAlreadyUnlocked(element_to_lock.title),)
        elif isinstance(element_to_lock, Door):
            # This is a door object, and it only represents _this side_
            # of the door game element; I use _matching_door() to fetch
            # the door object representing the opposite side so that the
            # door game element will be locked from the perspective of
            # either room.
            opposite_door = self._matching_door(element_to_lock)
            if opposite_door is not None:
                opposite_door.is_locked = True

        # The element_to_lock's is_locked attribute is set to rue, and a
        # Telement-has-been-locked value is returned.
        element_to_lock.is_locked = True
        return (stmsg.lock.ElementHasBeenUnlocked(element_to_lock.title),)

    # This private workhorse method handles the shared logic between
    # lock, unlock, open or close:

    def _preprocessing_for_lock_unlock_open_or_close(self, command, tokens):

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
                stmsg.command.BadSyntax(
                    command.upper(), COMMANDS_SYNTAX[command.upper()]
                ),
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
        # workhorse method self._door_selector() is used to implement
        # the flexible door specifier syntax. As always with a private
        # workhorse method, result[0] is type-tested to see if it's a
        # error value. If so, the result tuple is returned.
        if tokens[-1] in ("door", "doorway"):
            result = self._door_selector(tokens)
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
        container = self.game_state.rooms_state.cursor.container_here
        creature = self.game_state.rooms_state.cursor.creature_here

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
            and self.game_state.rooms_state.cursor.items_here is not None
        ):
            # The room's items_here State object and the Character's
            # inventory are both searched through looking for an item
            # whose title matches the target.
            for _, item in itertools.chain(
                self.game_state.rooms_state.cursor.items_here.values(),
                self.game_state.character.list_items(),
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

    def _door_selector(self, tokens):

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
            (
                len(tokens) == 2
                and tokens[0] in ("iron", "wooden")
                and tokens[1] == "door"
            )
            or len(tokens) == 1
            and tokens[0] == "doorway"
        ):
            door_type = " ".join(tokens).replace(" ", "_")

        # The tuple of doors in the current room is assigned to a local
        # variable, and I iterate across it trying to match compass_dir,
        # door_type, or both. As a fallback, 'door' vs. 'doorway' in the
        # title is tested. Matches are saved to matching_doors.
        doors = self.game_state.rooms_state.cursor.doors
        matching_doors = list()
        for door in doors:
            if compass_dir is not None and door_type is not None:
                if not (
                    door.title.startswith(compass_dir) and door.door_type == door_type
                ):
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
                stmsg.various.AmbiguousDoorSpecifier(
                    compass_dirs, tokens[-1], door_type
                ),
            )
        else:
            # Otherwise matching_doors is length 1; I have a match, so I
            # return it.
            return matching_doors

    look_at_door_re = re.compile(
        r"""(
                # For example, this regex
                # matches 'north iron door',
                # 'north door', 'iron door',
                # and 'door'. But it won't
                # match 'iron doorway'.
                (north|east|south|west) \s
            |
                (iron|wooden) \s
            |
                (
                    (north|east|south|west)
                    \s (iron|wooden) \s
                )
            )?
            (door|doorway)
            # Lookbehinds must be fixed-width
            # so I use 2.
            (?<! iron \s doorway)
            (?<! wooden \s doorway)
""",
        re.X,
    )

    def look_at_command(self, tokens):
        """
        Execute the LOOK AT command. The return value is always in a tuple even
        when it's of length 1. The LOOK AT command has the following usage:

        LOOK AT <item name>
        LOOK AT <item name> IN <chest name>
        LOOK AT <item name> IN INVENTORY
        LOOK AT <item name> ON <corpse name>
        LOOK AT <compass direction> DOOR
        LOOK AT <compass direction> DOORWAY

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If looking at a door which is not present in the room, returns a
        .stmsg.various.DoorNotPresent object.

        * If looking at a door, but the arguments are ambiguous
        and match more than one door in the room, returns a
        .stmsg.various.AmbiguousDoorSpecifier object.

        * If looking at a chest or corpse which is not present in the room,
        returns a .stmsg.various.ContainerNotFound object.

        * If looking at an item which isn't present (per the arguments)
        on the floor, in a chest, on a corpse, or in inventory, returns a
        .stmsg.lookat.FoundNothing object.

        * If looking at a chest or corpse which is present, returns a
        .stmsg.lookat.FoundCreatureHere object.

        * If looking at a creature which is present, returns a
        .stmsg.lookat.FoundCreatureHere object.

        * If looking at a door or doorway which is present, returns a
        .stmsg.lookat.FoundDoorOrDoorway object.

        * If looking at an item which is present, returns a
        .stmsg.lookat.FoundItemOrItemsHere object.
        """
        # The LOOK AT command can target an item in a chest or on a
        # corpse, so the presence of either 'in' or 'on' in the tokens
        # tuple indicates that case. The tokens tuple is checked for a
        # consistent container specifier; if it's poorly-constructed, an
        # error value is returned.
        if (
            not tokens
            or tokens[0] in ("in", "on")
            or tokens[-1] in ("in", "on")
            or ("in" in tokens and tokens[-1] == "corpse")
            or ("on" in tokens and tokens[-1] == "chest")
        ):
            return (stmsg.command.BadSyntax("LOOK AT", COMMANDS_SYNTAX["LOOK AT"]),)

        # This conditional is more easily accomplished with a regex
        # than a multi-line boolean chain. `look_at_door_re` is defined
        # above.
        elif tokens[-1] in ("door", "doorway") and not self.look_at_door_re.match(
            " ".join(tokens)
        ):
            return (stmsg.command.BadSyntax("LOOK AT", COMMANDS_SYNTAX["LOOK AT"]),)

        # These four booleans are initialized to False so they can be
        # tested for rue values later.
        item_contained = False
        item_in_inventory = False
        item_in_chest = False
        item_on_corpse = False

        # If 'in' or 'on' is used, the tokens can be divided at the
        # point it occurs into a left-hand value which is the title
        # of an item, and a right-hand value which is the title of a
        # container or is 'inventory'.
        if "in" in tokens or "on" in tokens:
            if "in" in tokens:
                # This signal value will control an upcoming conditional
                # tree.
                item_contained = True
                joinword_index = tokens.index("in")
                # As will one of these two.
                if tokens[joinword_index + 1 :] == ("inventory",):
                    item_in_inventory = True
                else:
                    item_in_chest = True
            else:
                joinword_index = tokens.index("on")
                if tokens[-1] != "floor":
                    # These signal values will control an upcoming
                    # conditional.
                    item_contained = True
                    item_on_corpse = True

            # joinword_index has been set, so target_title and
            # location_title are derived from the tokens before that
            # index, and the tokens after, respectively.
            target_title = " ".join(tokens[:joinword_index])
            location_title = " ".join(tokens[joinword_index + 1 :])

        # If the tokens contain neither 'in' or 'on, and the last token
        # is 'door' or 'dooray', _door_selector is used.
        elif tokens[-1] == "door" or tokens[-1] == "doorway":
            result = self._door_selector(tokens)
            if isinstance(result, tuple) and isinstance(
                result[0], stmsg.GameStateMessage
            ):
                # If it returns an error, that's passed along.
                return result
            else:
                # Otherwise the door it returns is the target, and a
                # found-door-or-doorway value is returned with that door
                # object informing the message.
                (door,) = result
                return (
                    stmsg.lookat.FoundDoorOrDoorway(door.title.split(" ")[0], door),
                )
        else:
            # The tokens don't indicate a door and don't have a
            # location_title to break off the end. The target_title is
            # formed from the tokens.
            target_title = " ".join(tokens)

        # creature_here and container_here are assigned to local
        # variables.
        creature_here = self.game_state.rooms_state.cursor.creature_here
        container_here = self.game_state.rooms_state.cursor.container_here

        # If earlier reasoning concluded the item is meant to be found
        # in a chest, but the container here is None or a corpse, a
        # syntax error is returned.
        if (
            item_in_chest
            and isinstance(container_here, Corpse)
            or item_on_corpse
            and isinstance(container_here, Chest)
        ):
            return (stmsg.command.BadSyntax("look at", COMMANDS_SYNTAX["LOOK AT"]),)

        # If the target_title matches the creature in this room, a
        # found-creature-here value is returned.
        if creature_here is not None and creature_here.title == target_title.lower():
            return (stmsg.lookat.FoundCreatureHere(creature_here.description),)

        # If the container here is not None and matches, a
        # found-container-here value is returned.
        elif (
            container_here is not None and container_here.title == target_title.lower()
        ):
            return (stmsg.lookat.FoundContainerHere(container_here),)

        # Otherwise, if the command specified an item that is contained
        # in something (including the inventory), so I test all the
        # valid states.
        elif item_contained:

            # If the item is supposed to be in the character's
            # inventory, I iterate through the inventory looking for a
            # matching title.
            if item_in_inventory:
                for item_qty, item in self.game_state.character.list_items():
                    if item.title != target_title:
                        continue
                    # If found, a found-item-here value is returned.
                    # _look_at_item_detail() is used to supply a
                    # detailed accounting of the item.
                    return (
                        stmsg.lookat.FoundItemOrItemsHere(
                            self._look_at_item_detail(item), item_qty, "inventory"
                        ),
                    )
                # Otherwise, a found-nothing value is returned.
                return (stmsg.lookat.FoundNothing(target_title, "inventory"),)
            else:
                # Otherwise, the item is in a chest or on a corpse.
                # Either one would need to be the value for
                # container_here, so I test its title against the
                # location_title.
                if container_here is None or container_here.title != location_title:

                    # If it doesn't match, a container-not-found error
                    # is returned.
                    return (stmsg.various.ContainerNotFound(location_title),)

                # Otherwise, if the container is non-None and its title
                # matches, I iterate through the container's contents
                # looking for a matching item title.
                elif (
                    container_here is not None
                    and container_here.title == location_title
                ):
                    for item_qty, item in container_here.values():
                        if item.title != target_title:
                            continue
                        # If I find a match, I return a found-item-here
                        # value. _look_at_item_detail() is used to
                        # supply a detailed accounting of the item.
                        return (
                            stmsg.lookat.FoundItemOrItemsHere(
                                self._look_at_item_detail(item),
                                item_qty,
                                container_here.title,
                                container_here.container_type,
                            ),
                        )
                    # Otherwise, I return a found-nothing value.
                    return (
                        stmsg.lookat.FoundNothing(
                            target_title,
                            location_title,
                            "chest" if item_in_chest else "corpse",
                        ),
                    )
                else:
                    # The container wasn't found, so I return a
                    # container-not-found error.
                    return (stmsg.various.ContainerNotFound(location_title),)
        else:

            # The target isn't a creature, or a container, or in a
            # container, or in the character's inventory, so I check the
            # floor. Again I iterate through items looking for a match.
            for item_name, (
                item_qty,
                item,
            ) in self.game_state.rooms_state.cursor.items_here.items():
                if item.title != target_title:
                    continue
                # If I find a match, I return a found-item-here value.
                # _look_at_item_detail() is used to supply a detailed
                # accounting of the item.
                return (
                    stmsg.lookat.FoundItemOrItemsHere(
                        self._look_at_item_detail(item), item_qty, "floor"
                    ),
                )
            # Otherwise, a found-nothing value is returned.
            return (stmsg.lookat.FoundNothing(target_title, "floor"),)

    def _look_at_item_detail(self, element):

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
                    f" Its attack bonus is +{element.attack_bonus} and its damage is "
                    + f"{element.damage}. "
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
                        f"{character_class}s"
                        if character_class != "thief"
                        else "thieves"
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
                descr_append_str = (
                    " It is closed." if element.is_closed else " It is open."
                )

        # The base element description is returned along with the
        # extended description derived above.
        return element.description + descr_append_str

    def open_command(self, tokens):
        """
        Execute the OPEN command. The return value is always in a tuple even
        when it's of length 1. The OPEN command has the following usage:

        OPEN <door name>
        OPEN <chest name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If trying to open a door which is not present in the room, returns a
        .stmsg.various.DoorNotPresent object.

        * If trying to open a door, but the command is ambiguous and matches
        more than one door, returns a .stmsg.various.AmbiguousDoorSpecifier
        object.

        * If trying to open an item, creature, corpse or doorway, returns a
        .stmsg.open_.ElementNotOpenable object.

        * If trying to open a chest that is not present in the room, returns a
        .stmsg.open_.ElementtoOpenNotHere object.

        * If trying to open a door or chest that is locked, returns a
        .stmsg.open_.ElementIsLocked object.

        * If trying to open a door or chest that is already open, returns a
        .stmsg.open_.ElementIsAlreadyOpen object.

        * Otherwise, the chest or door has its is_closed attribute set to False,
        and returns returns a .stmsg.open_.ElementHasBeenOpened..
        """
        # The shared private workhorse method is called and it handles
        # the majority of the error-checking. If it returns an error
        # that is passed along.
        result = self._preprocessing_for_lock_unlock_open_or_close("OPEN", tokens)
        if isinstance(result[0], stmsg.GameStateMessage):
            return result
        else:
            # Otherwise the element to open is extracted from the return
            # tuple.
            (element_to_open,) = result

        # If the element is locked, a element-is-locked error is
        # returned.
        if element_to_open.is_locked:
            return (stmsg.open_.ElementIsLocked(element_to_open.title),)
        elif not element_to_open.is_closed:
            # Otherwise if it's alreadty open, an
            # element-is-already-open error is returned.
            return (stmsg.open_.ElementIsAlreadyOpen(element_to_open.title),)
        elif isinstance(element_to_open, Door):
            # This is a door object, and it only represents _this side_
            # of the door game element; I use _matching_door() to fetch
            # the door object representing the opposite side so that the
            # door game element will be open from the perspective of
            # either room.
            opposite_door = self._matching_door(element_to_open)
            if opposite_door is not None:
                opposite_door.is_closed = False

        # The element has is_closed set to False and an
        # element-has-been-opened value is returned.
        element_to_open.is_closed = False
        return (stmsg.open_.ElementHasBeenOpened(element_to_open.title),)

    def pick_lock_command(self, tokens):
        """
        Execute the PICK LOCK command. The return value is always in a tuple
        even when it's of length 1. The PICK LOCK command has the following
        usage:

        PICK LOCK ON [THE] <chest name>
        PICK LOCK ON [THE] <door name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the player tries to use this command while playing a Warrior, Mage
        or Priest, returns a .stmsg.command.ClassRestricted object.

        * If the arguments specify a door, and that door is not present in the
        current room, returns a .stmsg.various.DoorNotPresent object.

        * If the arguments specify a door, and more than one door matches that
        specification, returns a .stmsg.various.AmbiguousDoorSpecifier object.

        * If the arguments specify a doorway, creature, item, or corpse, returns
        a .stmsg.pklock.ElementNotUnlockable object.

        * If the arguments specify a chest that is not present in the current
        room, returns a .stmsg.pklock.TargetNotFound object.

        * If the arguments specify a door or chest is that is already unlocked,
        returns a .stmsg.pklock.TargetNotLocked object.

        * Otherwise, the specified door or chest has its is_locked attribute set
        to False, and a .stmsg.pklock.TargetHasBeenUnlocked object is returned.
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
        if self.game_state.character_class != "Thief":
            return (stmsg.command.ClassRestricted("PICK LOCK", "thief"),)

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
            return (stmsg.command.BadSyntax("PICK LOCK", COMMANDS_SYNTAX["PICK LOCK"]),)
        elif tokens[:2] == ("on", "the"):
            tokens = tokens[2:]
        elif tokens[0] == "on":
            tokens = tokens[1:]

        # I form the target_title from the tokens.
        target_title = " ".join(tokens)

        # container_here and creature_here are assigned to local
        # variables.
        container = self.game_state.rooms_state.cursor.container_here
        creature = self.game_state.rooms_state.cursor.creature_here

        # If the target is a door or doorway. the _door_selector() is
        # used.
        if tokens[-1] in ("door", "doorway"):
            result = self._door_selector(tokens)
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
                return (stmsg.pklock.TargetNotLocked(target_title),)
            else:
                # This is a door object, and it only represents _this
                # side_ of the door game element; I use _matching_door()
                # to fetch the door object representing the opposite
                # side so that the door game element will be unlocked
                # from the perspective of either room.
                opposite_door = self._matching_door(door)
                if opposite_door is not None:
                    opposite_door.is_locked = False

                # The door's is_locked attribute is set to False, and a
                # target-has-been-unlocked value is returned.
                door.is_locked = False
                return (stmsg.pklock.TargetHasBeenUnlocked(target_title),)
        # The target isn't a door. If there is a container here and its
        # title matches....
        elif container is not None and container.title == target_title:
            # If it's a Corpse, the failure mode boolean is set.
            if isinstance(container, Corpse):
                tried_to_operate_on_corpse = True
            elif not getattr(container, "is_locked", False):
                # Otherwise if it's not locked, a target-not-locked
                # error value is returned.
                return (stmsg.pklock.TargetNotLocked(target_title),)
            else:
                # Otherwise, its is_locked attribute is set to False,
                # and a target-has-been-unlocked error is returned.
                container.is_locked = False
                return (stmsg.pklock.TargetHasBeenUnlocked(target_title),)

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
            for _, item in itertools.chain(
                (
                    self.game_state.rooms_state.cursor.items_here.values()
                    if self.game_state.rooms_state.cursor.items_here is not None
                    else ()
                ),
                self.game_state.character.list_items(),
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
            return (stmsg.pklock.ElementNotUnlockable(target_title, **argd),)
        else:
            # The target_title didn't match anything in the current
            # room, so a target-not-found error value is returned.
            return (stmsg.pklock.TargetNotFound(target_title),)

    def pick_up_command(self, tokens):
        """
        Execute the PICK UP command. The return value is always in a tuple even
        when it's of length 1. The PICK UP command has the following usage:

        PICK UP <item name>
        PICK UP <number> <item name>),

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the arguments are ungrammatical and are unclear about the quantity
        to pick up, returns a .stmsg.pickup.QuantityUnclear object.

        * If the arguments specify a chest, corpse, creature or door, returns a
        .stmsg.pickup.CantPickUpChestCorpseCreatureOrDoor object.

        * If the arguments specify an item to pick up that is not on the floor
        in the room, returns a .stmsg.pickup.ItemNotFound object.

        * If the arguments specify a quantity of the item to pick up that is
        greater than the quantity present on the floor in the room, returns a
        .stmsg.pickup.TryingToPickUpMoreThanIsPresent object.

        * Otherwise, the item— or the quantity of the item— is removed
        from the floor, and added to the character's inventory, and a
        .stmsg.pickup.ItemPickedUp object is returned.
        """
        # The door var is set to None so later it can be checked for a
        # non-None value.
        door = None
        pick_up_quantity = 0

        # If the contents of tokens is a door specifier,
        # _door_selector() is used.
        if tokens[-1] in ("door", "doorway"):
            result = self._door_selector(tokens)
            # If an error value was returned, it's returned.
            if isinstance(result[0], stmsg.GameStateMessage):
                return result
            else:
                # Otherwise the Door object is extracted from the result
                # tuple. Doors can't be picked up but we at least want
                # to match exactly.
                (door,) = result
                target_title = door.title
        else:
            # Otherwise, a private workhorse method is used to parse the
            # arguments.
            result = self._pick_up_or_drop_preproc("PICK UP", tokens)
            if isinstance(result[0], stmsg.GameStateMessage):
                return result
            else:
                pick_up_quantity, target_title = result

        # unpickupable_item_type is initialized to None so it can be
        # tested for a non-None value later. If it acquires another
        # value, an error value will be returned.
        unpickupable_element_type = None
        if door is not None:

            # The arguments specified a door, so unpickupable_item_type
            # is set to 'door'.
            unpickupable_element_type = "door"

        # Otherwise, if the current room has a creature_here and its
        # title matches, unpickupable_item_type is set to 'creature'.
        elif (
            self.game_state.rooms_state.cursor.creature_here is not None
            and self.game_state.rooms_state.cursor.creature_here.title == target_title
        ):
            unpickupable_element_type = "creature"

        # Otherwise, if the current room has a container_here and
        # its title matches, unpickupable_item_type is set to its
        # container_type.
        elif (
            self.game_state.rooms_state.cursor.container_here is not None
            and self.game_state.rooms_state.cursor.container_here.title == target_title
        ):
            unpickupable_element_type = (
                self.game_state.rooms_state.cursor.container_here.container_type
            )

        # If unpickupable_element_type acquired a value, a
        # cant-pick-up-element error is returned.
        if unpickupable_element_type:
            return (
                stmsg.pickup.CantPickUpChestCorpseCreatureOrDoor(
                    unpickupable_element_type, target_title
                ),
            )

        # If this room has no items_here ItemsMultiState object, nothing
        # can be picked up, and a item-not-found error is returned.
        if self.game_state.rooms_state.cursor.items_here is None:
            return (stmsg.pickup.ItemNotFound(target_title, pick_up_quantity),)

        # The items_here.values() sequence is cast to tuple and assigned
        # to a local variable, and the character's inventory is also so
        # assigned. I iterate through both of them looking for items
        # with titles matching target_title.
        items_here = tuple(self.game_state.rooms_state.cursor.items_here.values())
        items_had = tuple(self.game_state.character.list_items())
        item_here_pair = tuple(
            filter(lambda pair: pair[1].title == target_title, items_here)
        )
        items_had_pair = tuple(
            filter(lambda pair: pair[1].title == target_title, items_had)
        )

        # If no item was found in items_here matching target_title, a
        # tuple of items that *are* here is formed, and a item-not-found
        # error is instanced with it as an argument and returned.
        if not len(item_here_pair):
            items_here_qtys_titles = tuple(
                (item_qty, item.title) for item_qty, item in items_here
            )
            return (
                stmsg.pickup.ItemNotFound(
                    target_title, pick_up_quantity, *items_here_qtys_titles
                ),
            )

        # Otherwise, the item was found here, so its quantity and the
        # Item subclass object are extracted and saved.
        ((quantity_here, item),) = item_here_pair

        # _pick_up_or_drop_preproc() returns math.nan if it couldn't
        # determine a quantity. If it did, I assume the player meant
        # all of the item that's here, and set pick_up_quantity to
        # quantity_here.
        if pick_up_quantity is math.nan:
            pick_up_quantity = quantity_here

        # quantity_in_inventory is needed for the item-picked-up
        # return value constructor. If the item title had a match
        # in the inventory, the quantity there is assigned to
        # quantity_in_inventory, otherwise it's set to 0.
        quantity_in_inventory = items_had_pair[0][0] if len(items_had_pair) else 0

        # If the quantity to pick up specified in the command
        # is greater than the quantity in items_here, a
        # trying-to-pick-up-more-than-is-present error is returned.
        if quantity_here < pick_up_quantity:
            return (
                stmsg.pickup.TryingToPickUpMoreThanIsPresent(
                    target_title, pick_up_quantity, quantity_here
                ),
            )
        else:
            # Otherwise, that quantity of the item is added to the
            # player character's inventory.
            self.game_state.character.pick_up_item(item, qty=pick_up_quantity)

            # If the entire quantity of the item in items_here was
            # picked up, it's deleted from items_here.
            if quantity_here == pick_up_quantity:
                self.game_state.rooms_state.cursor.items_here.delete(item.internal_name)
            else:
                # Otherwise its new quantity is set in items_here.
                self.game_state.rooms_state.cursor.items_here.set(
                    item.internal_name, quantity_here - pick_up_quantity, item
                )
            # The quantity now possessed is computed, and used to
            # construct a item-picked-up return value, which is
            # returned.
            quantity_had_now = quantity_in_inventory + pick_up_quantity
            return (
                stmsg.pickup.ItemPickedUp(
                    target_title, pick_up_quantity, quantity_had_now
                ),
            )

    # Both PUT and TAKE have the same preprocessing challenges, so I
    # refactored their logic into a shared private preprocessing method.

    def _pick_up_or_drop_preproc(self, command, tokens):

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
                # item_quantity to math.nan as a signal value. When the
                # caller gets as far as identifying the total quantity
                # possible, it will replace this value with that one.
                if tokens[-1].endswith("s"):
                    item_quantity = math.nan
                else:
                    # Otherwise it implies a quantity of 1.
                    item_quantity = 1
            else:
                # Based on the enclosing conditional, this else implies
                # lexical_number_in_1_99_re.match(tokens[0]) ==
                # True. So I use lexical_number_to_digits to parse
                # the 1st token to an int.
                item_quantity = lexical_number_to_digits(tokens[0])

                # lexical_number_to_digits also uses math.nan as a
                # signal value; it returns that value if the lexical
                # number was outside the range of one to ninety-nine. If
                # so, I return a syntax error.
                if item_quantity is math.nan:
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
            # check if the item_title ends with a pluralizing 's'.
            if item_title.endswith("s"):
                # If so, the player is implying they want the total
                # quantity possible. As above, I set item_quantity to
                # math.nan as a signal value; it'll be replaced by the
                # caller when the total quantity possible is known.
                item_quantity = math.nan
            else:

                # Otherwise item_quantity is implied to be 1.
                item_quantity = 1
        item_title = item_title.rstrip("s")

        # Return the item_quantity and item_title parsed from tokens as
        # a 2-tuple.
        return item_quantity, item_title

    def put_command(self, tokens):
        """
        Execute the PUT command. The return value is always in a tuple even when
        it's of length 1. The PUT command has the following usage:

        PUT <item name> IN <chest name>
        PUT <number> <item name> IN <chest name>
        PUT <item name> ON <corpse name>
        PUT <number> <item name> ON <corpse name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the arguments specify a chest or corpse that is not present in the
        current room, returns a .stmsg.various.ContainerNotFound object.

        * If the arguments specify a chest that is closed, returns a
        .stmsg.various.ContainerIsClosed object.

        * If the arguments are an ungrammatical sentence and are ambiguous about
        the quantity to put, returns a .stmsg.put.QuantityUnclear object.

        * If the arguments specify an item to put that is not present in the
        character's inventory, returns a .stmsg.put.ItemNotInInventory object.

        * If the arguments specify a quantity of an item to put that is more
        than the character has, returns a .stmsg.put.TryingToPutMorethanYouHave
        object.

        * Otherwise, the item— or the quantity of the item— is removed from
        the character's inventory, placed in the chest or on the corpse, and
        put in the chest or on the corpse, and a .stmsg.put.AmountPut object is
        returned.
        """
        # The shared private workhorse method is called and it handles
        # the majority of the error-checking. If it returns an error
        # that is passed along.
        results = self._put_or_take_preproc("PUT", tokens)

        if len(results) == 1 and isinstance(results[0], stmsg.GameStateMessage):
            # If it returned an error, I return the tuple.
            return results
        else:
            # Otherwise, I recover put_amount (nt), item_title (str),
            # container_title (str) and container (Chest or Corpse) from
            # the results.
            put_amount, item_title, container_title, container = results

        # I read off the player's Inventory and filter it for a
        # (qty,obj) pair whose title matches the supplied Item name.
        inventory_list = tuple(
            filter(
                lambda pair: pair[1].title == item_title,
                self.game_state.character.list_items(),
            )
        )

        if len(inventory_list) == 1:

            # The player has the Item in their Inventory, so I save the
            # qty they possess and the Item object.
            amount_possessed, item = inventory_list[0]
        else:

            # Otherwise I return an item-not-in-inventory error.
            return (stmsg.put.ItemNotInInventory(item_title, put_amount),)

        # I use the Item subclass object to get the internal_name, and
        # look it up in the container to see if any amount is already
        # there. If so I record the amount, otherwise the amount is
        # saved as 0.
        if container.contains(item.internal_name):
            amount_in_container, _ = container.get(item.internal_name)
        else:
            amount_in_container = 0

        if put_amount > amount_possessed:
            # If the amount to put is more than the amount in inventory,
            # I return a trying-to-put-more-than-you-have error.
            return (stmsg.put.TryingToPutMoreThanYouHave(item_title, amount_possessed),)
        elif put_amount is math.nan:
            # Otherwise if _put_or_take_preproc returned math.nan for
            # the put_amount, that means it couldn't be determined from
            # the arguments but is implied, so I set it equal to the
            # total amount possessed, and set the amount_possessed to 0.
            put_amount = amount_possessed
            amount_possessed = 0
        else:

            # Otherwise I decrement the amount_possessed by the put
            # amount.
            amount_possessed -= put_amount

        # I remove the item in the given quantity from the player
        # character's inventory, and add the item in that quantity to
        # the container. Then I return a amount-put value.
        self.game_state.character.drop_item(item, qty=put_amount)
        container.set(item.internal_name, amount_in_container + put_amount, item)
        return (
            stmsg.put.PutAmountOfItem(
                item_title,
                container_title,
                container.container_type,
                put_amount,
                amount_possessed,
            ),
        )

    def _put_or_take_preproc(self, command, tokens):

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
        container = self.game_state.rooms_state.cursor.container_here

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
        if (
            joinword_index == -1
            or joinword_index == 0
            or joinword_index + 1 == len(tokens)
        ):
            return (
                stmsg.command.BadSyntax(
                    command.upper(), COMMANDS_SYNTAX[command.upper()]
                ),
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
            # available', and set quantity to math.nan as a signal
            # value. The caller will replace this with the total amount
            # available when it's known.
            quantity = math.nan

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
                stmsg.command.BadSyntax(
                    command.upper(), COMMANDS_SYNTAX[command.upper()]
                ),
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
                stmsg.command.BadSyntax(
                    command.upper(), COMMANDS_SYNTAX[command.upper()]
                ),
            )

        elif container.is_closed:

            # The container is closed, so I return a container-is-closed
            # error.
            return (stmsg.various.ContainerIsClosed(container.title),)

        # All the error checks passed, so I return the values determined
        # from the tokens argument.
        return quantity, item_title, container_title, container

    def quit_command(self, tokens):
        """
        Execute the QUIT command. The return value is always in a tuple even
        when it's of length 1. The QUIT command takes no arguments.

        * If the command is used with any arguments, returns a
        .stmsg.command.BadSyntax object.

        * Otherwise, the game is ended, and a .stmsg.quit.HaveQuitTheGame object
        is returned.
        """
        # This command takes no arguments, so if any were supplied, I
        # return a syntax error.
        if len(tokens):
            return (stmsg.command.BadSyntax("QUIT", COMMANDS_SYNTAX["QUIT"]),)

        # I devise the quit-the-game return value, set game_has_ended
        # to True, store the return value in game_ending_state_msg so
        # process() can reuse it if needs be, and return the value.
        return_tuple = (stmsg.quit.HaveQuitTheGame(),)
        self.game_state.game_has_ended = True
        self.game_ending_state_msg = return_tuple[-1]
        return return_tuple

    def reroll_command(self, tokens):
        """
        Execute the REROLL command. The return value is always in a tuple even
        when it's of length 1. The REROLL command takes no arguments.

        * If the command is used with any arguments, this method returns a
        .stmsg.command.BadSyntax object.

        * If the character's name or class has not been set yet, returns a
        .stmsg.reroll.NameOrClassNotSet object.

        * Otherwise, ability scores for the character are rolled, and a
        .stmsg.various.DisplayRolledStats is returned.
        """
        # This command takes no arguments, so if any were supplied, I
        # return a syntax error.
        if len(tokens):
            return (stmsg.command.BadSyntax("REROLL", COMMANDS_SYNTAX["REROLL"]),)

        # This command is only valid during the pregame after the
        # character's name and class have been set (and, therefore,
        # their stats have been rolled). If either one is None, I return
        # a name-or-class-not-set error.
        character_name = getattr(self.game_state, "character_name", None)
        character_class = getattr(self.game_state, "character_class", None)
        if not character_name or not character_class:
            return (stmsg.reroll.NameOrClassNotSet(character_name, character_class),)

        # I reroll the player character's stats, and return a
        # display-rolled-stats value.
        self.game_state.character.ability_scores.roll_stats()
        return (
            stmsg.various.DisplayRolledStats(
                strength=self.game_state.character.strength,
                dexterity=self.game_state.character.dexterity,
                constitution=self.game_state.character.constitution,
                intelligence=self.game_state.character.intelligence,
                wisdom=self.game_state.character.wisdom,
                charisma=self.game_state.character.charisma,
            ),
        )

    def set_class_command(self, tokens):
        """
        Execute the SET CLASS command. The return value is always in a tuple
        even when it's of length 1. The SET CLASS command has the following
        usage:

        SET CLASS [TO] <Warrior, Thief, Mage or Priest>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If a class other than Warrior, Thief, Mage or Priest is specified,
        returns a .stmsg.setcls.InvalidClass object.

        * If the name has not yet been set, then the class is set, and a
        .stmsg.setcls.ClassSet object is returned.

        * If the name has been set, then the class is set, ability scores for
        the character are rolled, and a .stmsg.setcls.ClassSet object and a
        Stmsg_Various_DisplayRolledStats object is returned.
        """
        # This command takes exactly one argument, so I return a syntax
        # error if I got 0 or more than 1.
        if len(tokens) == 0 or len(tokens) > 1:
            return (stmsg.command.BadSyntax("SET CLASS", COMMANDS_SYNTAX["SET CLASS"]),)

        # If the user specified something other than one of the four
        # classes, I return an invalid-class error.
        elif tokens[0] not in ("Warrior", "Thief", "Mage", "Priest"):
            return (stmsg.setcls.InvalidClass(tokens[0]),)

        # I assign the chosen classname, record whether this is the
        # first time this command is used, and set the class.
        class_str = tokens[0]
        class_was_none = self.game_state.character_class is None
        self.game_state.character_class = class_str

        # If character name was already set and this is the first
        # setting of character class, the Character object will have
        # been initialized as a side effect, so I return a class-set
        # value and a display-rolled-stats value.
        if self.game_state.character_name is not None and class_was_none:
            return (
                stmsg.setcls.ClassSet(class_str),
                stmsg.various.DisplayRolledStats(
                    strength=self.game_state.character.strength,
                    dexterity=self.game_state.character.dexterity,
                    constitution=self.game_state.character.constitution,
                    intelligence=self.game_state.character.intelligence,
                    wisdom=self.game_state.character.wisdom,
                    charisma=self.game_state.character.charisma,
                ),
            )
        else:
            # Otherwise I return only the class-set value.
            return (stmsg.setcls.ClassSet(class_str),)

    def set_name_command(self, tokens):
        """
        Execute the SET NAME command. The return value is always in a tuple even
        when it's of length 1. The SET NAME command has the following usage:

        SET NAME [TO] <character name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If a name is specified that doesn't match the pattern [A-Z][a-z]+(
        [A-Z][a-z]+)*, returns a .stmsg.setname.InvalidPart object.

        * If the class has not yet been set, then the name is set, and a
        .stmsg.setname.NameSet object is returned.

        * If the class has been set, then the name is set, ability scores for
        the character are rolled, and a .stmsg.setname.NameSet object and a
        .stmsg.various.DisplayRolledStats object are returned.
        """
        # This command requires one or more arguments, so if len(tokens)
        # == 0 I return a syntax error.
        if len(tokens) == 0:
            return (stmsg.command.BadSyntax("SET NAME", COMMANDS_SYNTAX["SET NAME"]),)

        # valid_name_re.pattern == '^[A-Z][a-z]+$'. I test each
        # token for a match, and non-matching name parts are saved.
        # If invalid_name_parts is nonempty afterwards, a separate
        # invalid-name-part error is returned for each failing name
        # part.
        invalid_name_parts = list()
        for name_part in tokens:
            if VALID_NAME_RE.match(name_part):
                continue
            invalid_name_parts.append(name_part)
        if len(invalid_name_parts):
            return tuple(map(stmsg.setname.InvalidPart, invalid_name_parts))

        # If the name wasn't set before this call, I save that fact,
        # then set the character name.
        name_was_none = self.game_state.character_name is None
        name_str = " ".join(tokens)
        self.game_state.character_name = " ".join(tokens)

        # If the character class is set and this command is the
        # first time the name has been set, that means that
        # self.game_state has instantiated a Character object as a
        # side effect, so I return a 2-tuple of a name-set value and a
        # display-rolled-stats value.
        if self.game_state.character_class is not None and name_was_none:
            return (
                stmsg.setname.NameSet(name_str),
                stmsg.various.DisplayRolledStats(
                    strength=self.game_state.character.strength,
                    dexterity=self.game_state.character.dexterity,
                    constitution=self.game_state.character.constitution,
                    intelligence=self.game_state.character.intelligence,
                    wisdom=self.game_state.character.wisdom,
                    charisma=self.game_state.character.charisma,
                ),
            )
        else:
            # Otherwise I just return a name-set value.
            return (stmsg.setname.NameSet(self.game_state.character_name),)

    def status_command(self, tokens):
        """
        Execute the STATUS command. The return value is always in a tuple even
        when it's of length 1. The STATUS command takes no arguments.

        * If the command is used with any arguments, returns a
        .stmsg.command.BadSyntax object.

        * Otherwise, returns a .stmsg.status.StatusOutput object.
        """
        # This command takes no arguments so if any were supplied I
        # return a syntax error.
        if len(tokens):
            return (stmsg.command.BadSyntax("STATUS", COMMANDS_SYNTAX["STATUS"]),)

        # A lot of data goes into a status command so I build the argd
        # to Stmsg_Status_StatusOutput key by key.
        character = self.game_state.character
        status_gsm_argd = dict()
        status_gsm_argd["hit_points"] = character.hit_points
        status_gsm_argd["hit_point_total"] = character.hit_point_total

        # Mana points are only part of a status line if the player
        # character is a Mage or Priest.
        if character.character_class in ("Mage", "Priest"):
            status_gsm_argd["mana_points"] = character.mana_points
            status_gsm_argd["mana_point_total"] = character.mana_point_total
        else:
            status_gsm_argd["mana_points"] = None
            status_gsm_argd["mana_point_total"] = None

        status_gsm_argd["armor_class"] = character.armor_class

        # attack_bonus and damage are only set if a weapon is
        # equipped... or if the player character is a Mage and a wand is
        # equipped.
        if character.weapon_equipped or (
            character.character_class == "Mage" and character.wand_equipped
        ):
            status_gsm_argd["attack_bonus"] = character.attack_bonus
            status_gsm_argd["damage"] = character.damage_roll
        else:
            status_gsm_argd["attack_bonus"] = 0
            status_gsm_argd["damage"] = ""

        # The status line can display the currently equipped armor,
        # shield, weapon and wand, and if an item isn't equipped
        # in a given slot it can display 'none'; but it only shows
        # '<Equipment>: none' if that equipment type is one the player
        # character's class can use. So I use class-tests to determine
        # whether to add each equipment-type argument.
        if character.character_class != "Mage":
            status_gsm_argd["armor"] = (
                character.armor.title if character.armor_equipped else None
            )
        if character.character_class not in ("Thief", "Mage"):
            status_gsm_argd["shield"] = (
                character.shield.title if character.shield_equipped else None
            )
        if character.character_class == "Mage":
            status_gsm_argd["wand"] = (
                character.wand.title if character.wand_equipped else None
            )

        status_gsm_argd["weapon"] = (
            character.weapon.title if character.weapon_equipped else None
        )
        status_gsm_argd["character_class"] = character.character_class

        # The entire argd has been assembled so I return a status-ouput
        # value.
        return (stmsg.status.StatusOutput(**status_gsm_argd),)

    def take_command(self, tokens):
        """
        Execute the TAKE command. The return value is always in a tuple even
        when it's of length 1. The TAKE command has the following usage:

        TAKE <item name> FROM <container name>
        TAKE <number> <item name> FROM <container name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the specified container isn't present in the current room, returns
        a .stmsg.various.ContainerNotFound object.

        * If the specified container is a chest and the chest is closed, returns
        a .stmsg.various.ContainerIsClosed object.

        * If the arguments are an ungrammatical sentence and are
        ambiguous as to what quantity the player means to take, returns a
        .stmsg.take.QuantityUnclear object.

        * If the specified item is not present in the specified chest or on the
        specified corpse, returns a .stmsg.take.ItemNotFoundInContainer object.

        * If the specified quantity of the item is greater than the quantity of
        that item in the chest or on the corpse, returns
        a .stmsg.take.TryingToTakeMoreThanIsPresent object.

        * Otherwise, the item— or the quantity of the item— is removed from
        the chest or the corpse and added to the character's inventory, and a
        .stmsg.take.ItemOrItemsTaken object is returned.
        """
        # take_command() shares logic with put_command() in a private
        # workhorse method _put_or_take_preproc().
        results = self._put_or_take_preproc("TAKE", tokens)

        # As always with private workhorse methods, it may have returned
        # an error value; if so, I return it.
        if len(results) == 1 and isinstance(results[0], stmsg.GameStateMessage):
            return results
        else:
            # Otherwise, I extract the values parsed out of tokens from
            # the results tuple.
            quantity_to_take, item_title, container_title, container = results

        # The following loop iterates over all the items in the
        # Container. I use a while loop so it's possible for the search
        # to fall off the end of the loop. If that code is reached, the
        # specified Item isn't in this Container.
        matching_item = tuple(
            filter(lambda argl: argl[1][1].title == item_title, container.items())
        )
        if len(matching_item) == 0:
            return (
                stmsg.take.ItemNotFoundInContainer(
                    container_title,
                    quantity_to_take,
                    container.container_type,
                    item_title,
                ),
            )

        ((item_internal_name, (item_quantity, item)),) = matching_item

        # The private workhorse method couldn't determine a quantity and
        # returned the signal value math.nan, so I assume the entire
        # amount present is intended, and set quantity_to_take to
        # item_quantity.
        if quantity_to_take is math.nan:
            quantity_to_take = item_quantity
        if quantity_to_take > item_quantity:
            # The amount specified is more than how
            # much is in the Container, so I return a
            # trying-to-take-more-than-is-present error.
            return (
                stmsg.take.TryingToTakeMoreThanIsPresent(
                    container_title,
                    container.container_type,
                    item_title,
                    item.item_type,
                    quantity_to_take,
                    item_quantity,
                ),
            )

        if quantity_to_take == item_quantity:
            # The amount to remove is the total amount present, so I
            # delete it from the container.
            container.delete(item_internal_name)
        else:
            # The quantity to take is less thant the amount present, so
            # I set the item in the container to the new lower quantity.
            container.set(item_internal_name, item_quantity - quantity_to_take, item)

        # I add the item in the given quantity to the player character's
        # inventory and return an item-or-items-taken value.
        self.game_state.character.pick_up_item(item, qty=quantity_to_take)
        return (
            stmsg.take.ItemOrItemsTaken(container_title, item_title, quantity_to_take),
        )

    def unequip_command(self, tokens):
        """
        Execute the UNEQUIP command. The return value is always in a tuple even
        when it's of length 1. The UNEQUIP command has the following usage:

        UNEQUIP <armor name>
        UNEQUIP <shield name>
        UNEQUIP <wand name>
        UNEQUIP <weapon name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the character does not have the item equipped, returns a
        .stmsg.unequip.ItemNotEquipped object.

        * Otherwise, the specified item is unequipped, and a
        .stmsg.various.ItemUnequipped is returned.
        """
        # This command requires an argument so if none was supplied I
        # return a syntax error.
        if not tokens:
            return (stmsg.command.BadSyntax("UNEQUIP", COMMANDS_SYNTAX["UNEQUIP"]),)

        # I construct the item title and search for it in the player
        # character's inventory.
        item_title = " ".join(tokens)
        matching_item_tuple = tuple(
            item
            for _, item in self.game_state.character.list_items()
            if item.title == item_title
        )

        # If the item isn't found in the player character's inventory,
        # I search for it in the items_state just to get the item_type;
        # I return an item-not-equipped error informed by the found
        # item_type if possible.
        if not len(matching_item_tuple):
            matching_item_tuple = tuple(
                item
                for item in self.game_state.items_state.values()
                if item.title == item_title
            )
            if matching_item_tuple:
                (item,) = matching_item_tuple[0:1]
                return (stmsg.unequip.ItemNotEquipped(item.title, item.item_type),)
            else:
                return (stmsg.unequip.ItemNotEquipped(item_title),)

        # I extract the matched item.
        (item,) = matching_item_tuple[0:1]

        # This code is very repetitive but it can't easily be condensed
        # into a loop due to the special case handling in the weapon
        # section vis a vis wands, so I just deal with repetitive code.
        if item.item_type == "armor":
            if self.game_state.character.armor_equipped is None:
                # If I'm unequipping armor but the player character has
                # no armor equipped I return a item-not-equipped error.
                return (stmsg.unequip.ItemNotEquipped(item_title, "armor"),)
            else:
                if self.game_state.character.armor_equipped.title != item_title:
                    # If armor_equipped's title doesn't match the
                    # argument item_title, I return an item-not-equipped
                    # error.
                    return (
                        stmsg.unequip.ItemNotEquipped(
                            item_title,
                            "armor",
                            self.game_state.character.armor_equipped.title,
                        ),
                    )
                else:
                    # Otherwise, the title matches, so I unequip the
                    # armor and return a item-unequipped value.
                    self.game_state.character.unequip_armor()
                    return (
                        stmsg.various.ItemUnequipped(
                            item_title,
                            "armor",
                            armor_class=self.game_state.character.armor_class,
                        ),
                    )
        elif item.item_type == "shield":
            if self.game_state.character.shield_equipped is None:
                # If I'm unequipping a shield but the player character
                # has no shield equipped I return a item-not-equipped
                # error.
                return (stmsg.unequip.ItemNotEquipped(item_title, "shield"),)
            else:
                if self.game_state.character.shield_equipped.title != item_title:
                    # If shield_equipped's title doesn't match the
                    # argument item_title, I return an item-not-equipped
                    # error.
                    return (
                        stmsg.unequip.ItemNotEquipped(
                            item_title,
                            "shield",
                            self.game_state.character.shield_equipped.title,
                        ),
                    )
                else:
                    # Otherwise, the title matches, so I unequip the
                    # shield and return a item-unequipped value.
                    self.game_state.character.unequip_shield()
                    return (
                        stmsg.various.ItemUnequipped(
                            item_title,
                            "shield",
                            armor_class=self.game_state.character.armor_class,
                        ),
                    )
        elif item.item_type == "wand":
            if self.game_state.character.wand_equipped is None:
                # If I'm unequipping a wand but the player character has
                # no wand equipped I return a item-not-equipped error.
                return (stmsg.unequip.ItemNotEquipped(item_title, "wand"),)
            else:
                if self.game_state.character.wand_equipped.title != item_title:
                    # If wand_equipped's title doesn't match the
                    # argument item_title, I return an item-not-equipped
                    # error.
                    return (stmsg.unequip.ItemNotEquipped(item_title, "wand"),)
                else:
                    # Otherwise, the title matches, so I unequip the
                    # wand.
                    self.game_state.character.unequip_wand()
                    weapon_equipped = self.game_state.character.weapon_equipped
                    # If a weapon is equipped, the player character will
                    # still be able to attack with *that*, so I return
                    # an item-unequipped value initialized with the
                    # weapon's info.
                    if weapon_equipped is not None:
                        return (
                            stmsg.various.ItemUnequipped(
                                item_title,
                                "wand",
                                attack_bonus=self.game_state.character.attack_bonus,
                                damage=self.game_state.character.damage_roll,
                                now_attacking_with=weapon_equipped,
                            ),
                        )
                    else:
                        # Otherwise, I return an item-unequipped value
                        # with cant_attack set to True.
                        return (
                            stmsg.various.ItemUnequipped(
                                item_title, "wand", cant_attack=True
                            ),
                        )
        elif item.item_type == "weapon":
            # If I'm unequipping a weapon but the player character has
            # no weapon equipped I return a item-not-equipped error.
            if self.game_state.character.weapon_equipped is None:
                return (stmsg.unequip.ItemNotEquipped(item.title, "weapon"),)
            else:
                if self.game_state.character.weapon_equipped.title != item_title:
                    # If weapon_equipped's title doesn't match the
                    # argument item_title, I return an item-not-equipped
                    # error.
                    return (stmsg.unequip.ItemNotEquipped(item.title, "weapon"),)
                else:
                    # Otherwise, the title matches, so I unequip the
                    # weapon.
                    self.game_state.character.unequip_weapon()
                    wand_equipped = self.game_state.character.wand_equipped
                    # If the player character has a wand equipped,
                    # they'll be attacking with that regardless of their
                    # weapon, so I return an item-unequipped value
                    # initialized with the wand's info.
                    if wand_equipped is not None:
                        return (
                            stmsg.various.ItemUnequipped(
                                item_title,
                                "weapon",
                                attack_bonus=self.game_state.character.attack_bonus,
                                damage=self.game_state.character.damage_roll,
                                attacking_with=wand_equipped,
                            ),
                        )
                    else:
                        # Otherwise I return an item-unequipped value
                        # with now_cant_attack set to True.
                        return (
                            stmsg.various.ItemUnequipped(
                                item_title, "weapon", now_cant_attack=True
                            ),
                        )

    def unlock_command(self, tokens):
        """
        Execute the UNLOCK command. The return value is always in a tuple even
        when it's of length 1. The UNLOCK command has the following usage:

        UNLOCK <door\u00A0name>
        UNLOCK <chest\u00A0name>

        * If that syntax is not followed, returns a .stmsg.command.BadSyntax
        object.

        * If the arguments specify a door that is not present in the room,
        returns a .stmsg.various.DoorNotPresent object.

        * If the arguments given match more than one door in the room, returns a
        .stmsg.various.AmbiguousDoorSpecifier object.

        * If the specified door or chest is not present in the current room,
        returns a .stmsg.unlock.ElementToUnlockNotHere object.

        * If the specified element is a doorway, item, creature or corpse,
        returns a .stmsg.unlock.ElementNotUnlockable object.

        * If the character does not possess the requisite door or
        chest key to lock the specified door or chest, returns an
        .stmsg.unlock.DontPossessCorrectKey object.

        * If the specified door or chest is already unlocked, returns a
        .stmsg.unlock.ElementIsAlreadyUnlocked object.

        * Otherwise, the specified door or chest is unlocked, and a
        .stmsg.unlock.ElementHasBeenUnlocked object is returned.
        """
        # This command requires an argument; so if it was called with no
        # arguments, I return a syntax error.
        if len(tokens) == 0:
            return (stmsg.command.BadSyntax("UNLOCK", COMMANDS_SYNTAX["UNLOCK"]),)

        # unlock_command() shares preprocessing logic with
        # lock_command(), open_command() and close_command(), so a
        # private workhorse method is called.
        result = self._preprocessing_for_lock_unlock_open_or_close("UNLOCK", tokens)
        if isinstance(result[0], stmsg.GameStateMessage):
            # If an error value is returned, I return it in turn.
            return result
        else:
            # Otherwise I extract the element_to_unlock from the result
            # tuple.
            (element_to_unlock,) = result

        # A key is required to unlock something; the chest key for
        # chests and the door key for doors. So I search the player
        # character's inventory for it. The key is not consumed by use,
        # so I only need to know it's there, not retrieve the Key object
        # and operate on it.
        key_required = (
            "door key" if isinstance(element_to_unlock, Door) else "chest key"
        )
        if not any(
            item.title == key_required
            for _, item in self.game_state.character.list_items()
        ):
            # If the required key is not present, I return a
            # don't-possess-correct-key error.
            return (
                stmsg.unlock.DontPossessCorrectKey(
                    element_to_unlock.title, key_required
                ),
            )
        elif element_to_unlock.is_locked is False:
            # Otherwise, if the item is already unlocked, I return an
            # element-is-already-unlocked error.
            return (stmsg.unlock.ElementIsAlreadyLocked(element_to_unlock.title),)
        elif isinstance(element_to_unlock, Door):
            # This is a door object, and it only represents _this side_
            # of the door game element; I use _matching_door() to fetch
            # the door object representing the opposite side so that the
            # door game element will be unlocked from the perspective of
            # either room.
            opposite_door = self._matching_door(element_to_unlock)
            if opposite_door is not None:
                opposite_door.is_locked = False

        # I unlock the element, and return an element-has-been-unlocked
        # value.
        element_to_unlock.is_locked = False
        return (stmsg.unlock.ElementHasBeenLocked(element_to_unlock.title),)
