#!/usr/bin/python3

from advgame import stmsg as stmsg

from advgame.commands.constants import COMMANDS_SYNTAX
from advgame.utils import lexical_number_in_1_99_re, lexical_number_to_digits


__all__ = ("drink_command",)


def drink_command(game_state, tokens):
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
            game_state.character.list_items(),
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
        healed_amt = game_state.character.heal_damage(hit_points_recovered)
        game_state.character.drop_item(item)
        return (
            stmsg.various.UnderwentHealingEffect(
                healed_amt,
                game_state.character.hit_points,
                game_state.character.hit_point_total,
            ),
        )
    else:
        # item.title == 'mana potion':

        # If the player character isn't a Mage or
        # a Priest, a mana potion does nothing; a
        # drank-mana-potion-when-not-a-spellcaster error is
        # returned.
        if game_state.character_class not in ("Mage", "Priest"):
            return (stmsg.drink.DrankManaPotionWhenNotASpellcaster(),)

        # The amount of mana recovery done by the potion is
        # granted to the character, and the potion is removed from
        # inventory. A drank-mana-potion value is returned.
        mana_points_recovered = item.mana_points_recovered
        regained_amt = game_state.character.regain_mana(mana_points_recovered)
        game_state.character.drop_item(item)
        return (
            stmsg.drink.DrankManaPotion(
                regained_amt,
                game_state.character.mana_points,
                game_state.character.mana_point_total,
            ),
        )
