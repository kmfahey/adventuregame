#!/usr/bin/python3


from advgame.stmsg.gsm import GameStateMessage
from advgame.utils import join_strs_w_comma_conj, usage_verb


__all__ = (
    "AmbiguousDoorSpecifier",
    "ContainerIsClosed",
    "ContainerNotFound",
    "DisplayRolledStats",
    "DoorNotPresent",
    "EnteredRoom",
    "FoeDeath",
    "ItemEquipped",
    "ItemUnequipped",
    "UnderwentHealingEffect",
)


class AmbiguousDoorSpecifierGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.lock_command(),
    .unlock_command(), .open_command() and .close_command() when the player
    has used a specifier for a door that matches more than one door in the
    current dungeon room; for example, saying 'unlock wooden door' when
    there's two wooden doors.
    """

    __slots__ = "compass_dirs", "door_or_doorway", "door_type"

    @property
    def message(self):
        # This message property assembles a pair of sentences that
        # describe every door in the room that matches the user's
        # ambiguous command and asks them which one they mean.
        door_type = self.door_type.replace("_", " ") if self.door_type else None
        message_str = (
            "More than one door in this room matches your command. Do you mean "
        )
        if door_type is not None:
            door_str_list = [
                f"the {compass_dir} {door_type}" for compass_dir in self.compass_dirs
            ]
        else:
            door_str_list = [
                f"the {compass_dir} {self.door_or_doorway}"
                for compass_dir in self.compass_dirs
            ]
        message_str += join_strs_w_comma_conj(door_str_list, "or") + "?"
        return message_str

    def __init__(self, compass_dirs, door_or_doorway, door_type):
        self.compass_dirs = compass_dirs
        self.door_or_doorway = door_or_doorway
        self.door_type = door_type


class ContainerIsClosedGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.put_command() or
    .take_command() when the player tries to access a chest that is closed.
    """

    __slots__ = ("target",)

    @property
    def message(self):
        return f"The {self.target} is closed."

    def __init__(self, target):
        self.target = target


class ContainerNotFoundGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.put_command(),
    .take_command(), or .look_at_command() when trying to look in a chest
    that isn't present in the current dungeon room, or check a corpse that
    isn't present in the current dungeon room.
    """

    __slots__ = "container_not_found_title", "container_present_title"

    @property
    def message(self):
        return_str = f"There is no {self.container_not_found_title} here."
        if self.container_present_title is not None:
            return_str += f" However, there *is* a {self.container_present_title} here."
        return return_str

    def __init__(self, container_not_found_title, container_present_title=None):
        self.container_not_found_title = container_not_found_title
        self.container_present_title = container_present_title


class DisplayRolledStatsGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.set_name_command() or
    .set_class_command() when both name and class have been set, or by
    .reroll_command(). It displays the character's randomly generated
    ability scores.
    """

    __slots__ = (
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    )

    @property
    def message(self):
        return (
            f"Your ability scores are "
            f"Strength\u00A0{self.strength}, "
            f"Dexterity\u00A0{self.dexterity}, "
            f"Constitution\u00A0{self.constitution}, "
            f"Intelligence\u00A0{self.intelligence}, "
            f"Wisdom\u00A0{self.wisdom}, "
            f"Charisma\u00A0{self.charisma}.\n\n"
            f"Would you like to reroll or begin the game?"
        )

    def __init__(
        self, strength, dexterity, constitution, intelligence, wisdom, charisma
    ):
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma


class DoorNotPresentGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.close_command(),
    .leave_command(), .lock_command(), .look_at_command(), .open_command(),
    .pick_lock_command(), or .unlock_command() when the player specifies a
    door that is not present in the current dungeon room.
    """

    __slots__ = "compass_dir", "portal_type"

    @property
    def message(self):
        # This message property assembles a sentence which informs the
        # player that the door they specified in their command is not
        # present in this room.
        return_str = "This room does not have a"
        if self.compass_dir is not None and self.portal_type is not None:
            # This concatenation varies slightly to turn 'a' into 'an'
            # if the word after it is 'east'.
            return_str += (
                f"n {self.compass_dir} {self.portal_type}."
                if self.compass_dir == "east"
                else f" {self.compass_dir} {self.portal_type}."
            )
        elif self.portal_type is not None:
            return_str += f"a {self.portal_type}."
        elif self.compass_dir is not None:
            # This concatenation varies slightly to turn 'a' into 'an'
            # if the word after it is 'east'.
            return_str += (
                f"n {self.compass_dir} door or doorway."
                if self.compass_dir == "east"
                else f" {self.compass_dir} door or doorway."
            )
        return return_str

    def __init__(self, compass_dir, portal_type=None):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class EnteredRoomGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.leave_command() when the
    player leaves a room and enters a new one, or by .begin_command()
    when the player starts the game in the first room. It prints the room
    description, lists the items on the floor if any, mentions any chest or
    creature, and lists the exits to the room by compass direction.
    """

    __slots__ = ("room",)

    @property
    def message(self):
        # This message property assembles a room description, mentioning
        # any chest, corpse, or creatures, items on the floor, and each
        # of the doors, by building a list of sentences, then joining
        # them and returning the string.
        message_list = list()

        # It starts with the room description.
        message_list.append(self.room.description)

        # If there's a container here, a sentence mentioning it is added
        # to the list.
        if self.room.container_here is not None:
            indirect_article = (
                "an" if self.room.container_here.title[0] in "aeiou" else "a"
            )
            message_list.append(
                f"You see {indirect_article} {self.room.container_here.title} "
                + "here."
            )

        # If there's a creature here, a sentence mentioning them is
        # added to the list.
        if self.room.creature_here is not None:
            indirect_article = (
                "an" if self.room.creature_here.title[0] in "aeiou" else "a"
            )
            message_list.append(
                f"There is {indirect_article} {self.room.creature_here.title} "
                + "in the room."
            )

        # If the items_here attribute is a ItemsMultiState object,
        # its contents are assembled into a list, joined into a
        # comma-separated string, and that string is added to the list.
        if self.room.items_here is not None:
            room_items = list()
            for item_qty, item in self.room.items_here.values():
                quantifier = (
                    str(item_qty)
                    if item_qty > 1
                    else "an"
                    if item.title[0] in "aeiou"
                    else "a"
                )
                pluralizer = "s" if item_qty > 1 else ""
                room_items.append(f"{quantifier} {item.title}{pluralizer}")
            items_here_str = join_strs_w_comma_conj(room_items, "and")
            message_list.append(f"You see {items_here_str} on the floor.")

        # A list of door titles and directions is assembled, joined into
        # a string, and that string is added to the list.
        door_list = list()
        for compass_dir in ("north", "east", "south", "west"):
            dir_attr = compass_dir + "_door"
            door = getattr(self.room, dir_attr, None)
            if door is None:
                continue
            door_ersatz_title = door.door_type.replace("_", " ")
            indirect_article = "an" if door_ersatz_title[0] in "aeiou" else "a"
            door_list.append(
                f"{indirect_article} {door_ersatz_title} to the {compass_dir}"
            )
        door_str = "There is " + join_strs_w_comma_conj(door_list, "and") + "."
        message_list.append(door_str)

        # The list of sentences is joined into a string and returned.
        return "\n".join(message_list)

    def __init__(self, room):
        self.room = room


class FoeDeathGSM(GameStateMessage):
    __slots__ = ("creature_title",)

    @property
    def message(self):
        return (
            f"The {self.creature_title} is slain. You see a "
            + f"{self.creature_title} corpse here."
        )

    def __init__(self, creature_title):
        self.creature_title = creature_title


class ItemEquippedGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.begin_game() or
    .equip_command() when the player equips an item. It lists the item
    equipped and mentions how the relevant game parameters have changed as a
    result.
    """

    __slots__ = (
        "item_title",
        "item_type",
        "attack_bonus",
        "damage",
        "armor_class" "change_text",
    )

    @property
    def message(self):
        # This message property assembles a sentence that informs
        # the user of the new wand, weapon, armor or shield they've
        # equipped. If it's a suit of armor or shield, their new armor
        # class is mentioned. If it's a weapon or wand, their new attack
        # bonus and damage is mentioned.
        item_usage_verb = usage_verb(self.item_type, gerund=True)
        referent = (
            "a suit of"
            if self.item_type == "armor"
            else "an"
            if self.item_title[0] in "aeiou"
            else "a"
        )
        if self.attacking_with is not None:
            item_usage_verb = usage_verb(self.attacking_with.item_type, gerund=True)
            referent = "an" if self.attacking_with.title[0] in "aeiou" else "a"
            return_str = (
                f"You're {item_usage_verb} {referent} "
                + f"{self.attacking_with.title}. "
            )
        else:
            return_str = f"You're now {item_usage_verb} {referent} {self.item_title}. "
        if self.armor_class is not None:
            return_str += f"Your armor class is now {self.armor_class}."
        else:  # attack_bonus is not None and damage != ''
            plussign = "+" if self.attack_bonus >= 0 else ""
            tense = "now " if not self.attacking_with else ""
            return_str += (
                f"Your attack bonus is {tense}{plussign}{self.attack_bonus} "
                + f"and your {self.item_type} damage is {tense}{self.damage}."
            )
        return return_str

    def __init__(
        self,
        item_title,
        item_type,
        attack_bonus=None,
        damage="",
        armor_class=None,
        attacking_with=None,
    ):
        self.item_title = item_title
        self.item_type = item_type
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.armor_class = armor_class
        self.attacking_with = attacking_with


class ItemUnequippedGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.equip_command(),
    .unequip_command(), or .drop_command(). It's returned by
    .unequip_command() when the player unequips an item; .equip_command()
    returns it if the player already had an item equipped in that slot to
    convey the previous item's removal; and .drop_command() returns it if
    the item the character dropped was equipped and they no longer have any
    of the item in their inventory.
    """

    __slots__ = (
        "item_title",
        "item_type",
        "changed_value_1",
        "value_type_1",
        "changed_value_2",
        "value_type_2",
        "change_text",
    )

    @property
    def message(self):
        # This message property constructs a series of sentences that
        # inform the player that they unequipped an item, and what the
        # changes to their stats are and if they can still attack. Nota
        # Bene: if a Mage equips a wand, they will always use it instead
        # of their weapon. If a Mage unequips their wand their attack
        # and damage won't change; and if they unequip their wand their
        # new attack and damage are from the weapon they still have
        # equipped.
        item_usage_verb = usage_verb(self.item_type, gerund=True)
        referent = (
            "a suit of"
            if self.item_type == "armor"
            else "an"
            if self.item_title[0] in "aeiou"
            else "a"
        )
        return_str = f"You're no longer {item_usage_verb} {referent} {self.item_title}."
        if self.armor_class is not None:

            # If the player just unequipped armor or a weapon, their
            # armor class has changed.
            return_str += f" Your armor class is now {self.armor_class}."
        elif self.attack_bonus is not None and self.damage is not None:

            # Only a mage can still have an attack bonus and damage
            # after unequipping something.
            plussign = "+" if self.attack_bonus >= 0 else ""
            if self.now_attacking_with:
                implement = self.now_attacking_with
                return_str += (
                    f" You're now attacking with your "
                    + f"{self.now_attacking_with.title}."
                )
                tense = "now "
            elif self.attacking_with:
                implement = self.attacking_with
                return_str += f" You're attacking with your {implement.title}."
                tense = ""
            return_str += (
                f" Your attack bonus is {tense}{plussign}{self.attack_bonus} "
                + f"and your {implement.title} damage is {tense}{self.damage}."
            )
        elif self.now_cant_attack:

            # Any other class that just unequipped a weapon gets this
            # message.
            return_str += " You now can't attack."
        return return_str

    def __init__(
        self,
        item_title,
        item_type,
        attack_bonus=None,
        damage=None,
        armor_class=None,
        attacking_with=None,
        now_attacking_with=None,
        now_cant_attack=False,
    ):
        self.item_title = item_title
        self.item_type = item_type
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.armor_class = armor_class
        self.attacking_with = attacking_with
        self.now_attacking_with = now_attacking_with
        self.now_cant_attack = now_cant_attack


class UnderwentHealingEffectGSM(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.drink_command() or
    .cast_spell_command(). It's returned by .drink_command() if the player
    drinks a health potion; and it's returned by the .cast_spell_command()
    if the player is a Priest and they successfully cast a healing spell.
    """

    __slots__ = (
        "amount_healed",
        "current_hit_points",
        "hit_point_total",
    )

    @property
    def message(self):
        # This message property handles three cases: * The player
        # regained hit points and now has their maximum hit points. *
        # The player regained hit points but are still short of their
        # maximum. * The player didn't regain any hit points because
        # their hit points were already at maximum.
        return_str = (
            f"You regained {self.amount_healed} hit points."
            if self.amount_healed != 0
            else "You didn't regain any hit points."
        )
        if self.current_hit_points == self.hit_point_total:
            return_str += " You're fully healed!"
        return_str += (
            f" Your hit points are "
            + f"{self.current_hit_points}/{self.hit_point_total}."
        )
        return return_str

    def __init__(self, amount_healed, current_hit_points, hit_point_total):
        self.amount_healed = amount_healed
        self.current_hit_points = current_hit_points
        self.hit_point_total = hit_point_total
