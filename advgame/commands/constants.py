#!/usr/bin/python3

import re


__all__ = (
    "COMMANDS_HELP",
    "COMMANDS_SYNTAX",
    "INGAME_COMMANDS",
    "PREGAME_COMMANDS",
    "SPELL_DAMAGE",
    "SPELL_MANA_COST",
    "STARTER_GEAR",
    "VALID_NAME_RE",
)


SPELL_DAMAGE = "3d8+5"

SPELL_MANA_COST = 5

STARTER_GEAR = {
    "Mage": {"weapon": "Staff"},
    "Priest": {"armor": "Studded_Leather", "shield": "Buckler", "weapon": "Heavy_Mace"},
    "Thief": {"armor": "Studded_Leather", "weapon": "Rapier"},
    "Warrior": {"armor": "Studded_Leather", "shield": "Buckler", "weapon": "Longsword"},
}


# The COMMAND_SYNTAX dict is a compendium of usage examples for
# every command in the game. When a command method needs to return
# BadSyntaxGSM object, it consults this dict for the second argument to
# its constructor.
#
# \u00A0 is a unicode nonbreaking space. I use it in the syntax examples
# so that the use of advgame.utils.textwrapper() in advgame.py doesn't
# break individual syntax examples across lines. The longer syntax
# examples become difficult to read if wrapped across a line.

COMMANDS_SYNTAX = {
    "ATTACK": ("<creature\xa0name>",),
    "BEGIN GAME": ("",),
    "CAST SPELL": ("",),
    "CLOSE": ("<door\xa0name>", "<chest\xa0name>"),
    "DRINK": ("[THE]\xa0<potion\xa0name>", "<number>\xa0<potion\xa0name>(s)"),
    "DROP": ("<item\xa0name>", "<number>\xa0<item\xa0name>"),
    "EQUIP": (
        "<armor\xa0name>",
        "<shield\xa0name>",
        "<wand\xa0name>",
        "<weapon\xa0name>",
    ),
    "HELP": ("", "<command\xa0name>"),
    "INVENTORY": ("",),
    "LEAVE": (
        "[USING\xa0or\xa0VIA]\xa0<compass\xa0direction>\xa0DOOR",
        "[USING\xa0or\xa0VIA]\xa0<compass\xa0direction>\xa0DOORWAY",
        "[USING\xa0or\xa0VIA]\xa0<door\xa0name>",
        "[USING\xa0or\xa0VIA]\xa0<compass\xa0direction>\xa0<door\xa0name>",
    ),
    "LOCK": ("<door\xa0name>", "<chest\xa0name>"),
    "LOOK AT": (
        "<item\xa0name>",
        "<item\xa0name>\xa0IN\xa0<chest\xa0name>",
        "<item\xa0name>\xa0IN\xa0INVENTORY",
        "<item\xa0name>\xa0ON\xa0<corpse\xa0name>",
        "<compass\xa0direction>\xa0DOOR",
        "<compass\xa0direction>\xa0DOORWAY",
    ),
    "OPEN": ("<door\xa0name>", "<chest\xa0name>"),
    "PICK LOCK": ("ON\xa0[THE]\xa0<chest\xa0name>", "ON\xa0[THE]\xa0<door\xa0name>"),
    "PICK UP": ("<item\xa0name>", "<number>\xa0<item\xa0name>"),
    "PUT": (
        "<item\xa0name>\xa0IN\xa0<chest\xa0name>",
        "<number>\xa0<item\xa0name>\xa0IN\xa0<chest\xa0name>",
        "<item\xa0name>\xa0ON\xa0<corpse\xa0name>",
        "<number>\xa0<item\xa0name>\xa0ON\xa0<corpse\xa0name>",
    ),
    "QUIT": ("",),
    "REROLL": ("",),
    "SET CLASS": ("[TO]\xa0<Warrior,\xa0Thief,\xa0Mage\xa0or\xa0Priest>",),
    "SET NAME": ("[TO]\xa0<character\xa0name>",),
    "STATUS": ("",),
    "TAKE": (
        "<item\xa0name>\xa0FROM\xa0<container\xa0name>",
        "<number>\xa0<item\xa0name>\xa0FROM\xa0<container\xa0name>",
    ),
    "UNEQUIP": (
        "<armor\xa0name>",
        "<shield\xa0name>",
        "<wand\xa0name>",
        "<weapon\xa0name>",
    ),
    "UNLOCK": ("<door\xa0name>", "<chest\xa0name>"),
}

# The COMMANDS_HELP dict is a compendium of help blurbs for use by
# CommandProcessor.help_command(). Where the blurb explicitly suggests
# another command, a nonbreaking space is used again to ensure the
# command doesn't get wrapped and is readable.

COMMANDS_HELP = {
    "ATTACK": "The ATTACK command is used to attack creatures. Beware: if you "
    + "attack a creature and don't kill it, it will attack you in "
    + "return! After you kill a creature, you can check its corpse "
    + "for loot using the LOOK AT command and take loot with the "
    + "TAKE command.",
    "BEGIN GAME": "The BEGIN GAME command is used to start the game after you "
    + "have set your name and class and approved your ability "
    + "scores. When you enter this command, you will "
    + "automatically be equiped with your starting gear and "
    + "started in the antechamber of the dungeon.",
    "CAST SPELL": "The CAST SPELL command can only be used by Mages and "
    + "Priests. A Mage can cast an attack spell that "
    + "automatically hits creatures and does damage. A Priest "
    + "can cast a healing spell on themselves.",
    "CLOSE": "The CLOSE command can be used to close doors and chests.",
    "DRINK": "The DRINK command can be used to drink health or mana potions.",
    "DROP": "The DROP command can be used to remove items from your inventory "
    + "and leave them on the floor. If you drop an item you had "
    + "equipped, it will automatically be unequipped unless you have "
    + "another on you.",
    "EQUIP": "The EQUIP command can be used to equip a weapon, armor, shield "
    + "or wand from your inventory. You can't equip items from the "
    + "floor.",
    "HELP": "The HELP command can be used to get help about any game commands.",
    "INVENTORY": "The INVENTORY command can be used to get a listing of the "
    + "items in your inventory. If you want more information "
    + "about an item, say 'LOOK\xa0AT\xa0<item\xa0title>\xa0IN\xa0"
    "INVENTORY'.",
    "LEAVE": "The LEAVE command is used to exit the room you're in using the "
    + "door you specify. If the door is locked you will be unable to "
    + "leave using it until you can unlock it.",
    "LOCK": "The LOCK command is used to lock doors and chests. You need a "
    + "door key to lock doors and a chest key to lock chests. These "
    + "keys can be found somewhere in the dungeon.",
    "LOOK AT": "The LOOK at command can be used to get more information about "
    + "doors, items on the floor or in a chest or on a corpse, "
    + "chests, creatures and corpses.",
    "OPEN": "The OPEN command is used to open doors and chests.",
    "PICK LOCK": "Only Thieves can use the pick lock command. The pick lock "
    + "command enables you to unlock a door or chest without "
    + "needing a key. This saves some searching!",
    "PICK UP": "The PICK UP command can be used to acquire items from the "
    + "floor and put them in your inventory. To acquire items "
    + "from a chest, say "
    + "'<item\xa0name>\xa0FROM\xa0<chest\xa0name>'. For a corpse, "
    + "say '<item\xa0name>\xa0FROM\xa0<chest\xa0name>'.",
    "PUT": "The PUT command can be used to remove items from your inventory "
    + "and place them in a chest or on a corpse's person. To leave "
    + "items on the floor, use DROP.",
    "QUIT": "The QUIT command is used to exit the game.",
    "REROLL": "The REROLL command is used before game start to get a fresh "
    + "selection of randomly generated ability scores. You can "
    + "reroll your ability scores as many times as you want.",
    "SET CLASS": "The SET CLASS command is used before game start to pick a "
    + "class for your character. Your options are Warrior, "
    + "Thief, Mage or Priest.",
    "SET NAME": "The SET NAME command is used before game start to pick a "
    + "name for your character. Your name can have as many parts "
    + "as you like, but each one must be a capital letter "
    + "followed by lowercase letters. Symbols and numbers are not "
    + "allowed.",
    "STATUS": "The STATUS command is used to see a summary of your hit points "
    + "and current weapon, armor, shield choices. Spellcasters also "
    + "see their mana points; and Mages see their current wand if "
    + "they're using one.",
    "TAKE": "The TAKE command is used to remove items from a chest or a "
    + "corpse and place them in your inventory.",
    "UNEQUIP": "The UNEQUIP command is used to unequip a weapon, armor, "
    + "shield or wand from your inventory.",
    "UNLOCK": "The UNLOCK command is used to unlock a door or chest. You need "
    + "a door key to unlock doors and a chest key to unlock chests.",
}


VALID_NAME_RE = re.compile("^[A-Z][a-z]+$")

PREGAME_COMMANDS = {"set_name", "set_class", "help", "reroll", "begin_game", "quit"}

INGAME_COMMANDS = {
    "attack",
    "cast_spell",
    "close",
    "help",
    "drink",
    "drop",
    "equip",
    "leave",
    "inventory",
    "look_at",
    "lock",
    "open",
    "pick_lock",
    "pick_up",
    "quit",
    "put",
    "quit",
    "status",
    "take",
    "unequip",
    "unlock",
}
