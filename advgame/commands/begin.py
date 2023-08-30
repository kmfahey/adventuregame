#!/usr/bin/python3

from operator import itemgetter

from advgame.commands.constants import COMMANDS_SYNTAX, STARTER_GEAR
from advgame.statemsgs.begin import GameBeginsGSM, NameOrClassNotSetGSM
from advgame.statemsgs.command import BadSyntaxGSM
from advgame.statemsgs.various import EnteredRoomGSM, ItemEquippedGSM


__all__ = ("begin_game_command",)


def begin_game_command(game_state, tokens):
    """
    Execute the BEGIN GAME command. The return value is always in a tuple
    even when it's of length 1. Returns one or more GameStateMessage
    subclass instances. Takes no arguments.

    * If any arguments are given, returns a BadSyntaxGSM object.

    * If the command is used before the character's name and class have been
    set, returns a NameOrClassNotSetGSM object.

    * Otherwise, returns a GameBeginsGSM object, one or more ItemEquippedGSM
    objects, and a EnteredRoomGSM object.
    """
    # This command begins the game. Most of the work done is devoted to
    # creating the character's starting gear and equipping all of it.

    # This command takes no argument; if any were used, a syntax error
    # is returned.
    if len(tokens):
        return (BadSyntaxGSM("BEGIN GAME", COMMANDS_SYNTAX["BEGIN GAME"]),)

    # The game can't begin if the player hasn't used both SET
    # NAME and SET CLASS yet, so I check for that. If not, a
    # name-or-class-not-set error value is returned.
    character_name = getattr(game_state, "character_name", None)
    character_class = getattr(game_state, "character_class", None)
    if not character_name or not character_class:
        return (NameOrClassNotSetGSM(character_name, character_class),)

    # The error checking is done, so GameState.game_has_begun is set
    # to True, and a game-begins value is used to initialiZe the
    # return_values tuple.
    game_state.game_has_begun = True
    return_values = (GameBeginsGSM(),)

    # A player character receives starting equipment appropriate to
    # their class, as laid out in the STARTER_GEAR dict. The value there
    # is a dict of item types to item internal names. This loop looks
    # up each internal name in the ItemsState object to get an Item
    # subclass object.

    # (This is sorted just to make the results deterministic for ease of
    # testing.)                          vvvvvv
    for item_type, item_internal_name in sorted(
        STARTER_GEAR[character_class].items(), key=itemgetter(0)
    ):
        item = game_state.items_state.get(item_internal_name)
        game_state.character.pick_up_item(item)
        # Character.equip_{item_type} is looked up and called with the
        # Item subclass object to equip the character with this item of
        # equipment.
        getattr(game_state.character, "equip_" + item_type)(item)

        # An appropriate item-equipped return value, complete with
        # either the updated armor_class value or the updated
        # attack_bonus and damage values, is appended to the
        # return_values tuple.
        if item.item_type == "armor":
            return_values += (
                ItemEquippedGSM(
                    item.title,
                    "armor",
                    armor_class=game_state.character.armor_class,
                ),
            )
        elif item.item_type == "shield":
            return_values += (
                ItemEquippedGSM(
                    item.title,
                    "shield",
                    armor_class=game_state.character.armor_class,
                ),
            )
        elif item.item_type == "wand":
            return_values += (
                ItemEquippedGSM(
                    item.title,
                    "wand",
                    attack_bonus=game_state.character.attack_bonus,
                    damage=game_state.character.damage_roll,
                ),
            )
        else:
            return_values += (
                ItemEquippedGSM(
                    item.title,
                    "weapon",
                    attack_bonus=game_state.character.attack_bonus,
                    damage=game_state.character.damage_roll,
                ),
            )

    # Lastly, an entered-room return value is appended to the
    # return_values tuple, so a description of the first room will
    # print.
    return_values += (EnteredRoomGSM(game_state.rooms_state.cursor),)

    # From the player's perspective, the frontend printing out this
    # entire sequence of return values can look like:
    #
    # The game has begun!
    # You're now wearing a suit of studded leather armor. Your armor
    # class is now 11.
    # You're now carrying a buckler. Your armor class is now 12.
    # You're now wielding a mace. Your attack bonus is now +1 and your
    # weapon damage is now 1d6+1.
    # Antechamber of dungeon. There is a doorway to the north.

    return return_values
