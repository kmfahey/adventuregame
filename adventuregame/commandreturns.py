#!/usr/bin/python3

import abc
import math

from adventuregame.gameelements import *
from adventuregame.utility import *

__name__ = 'adventuregame.commandreturns'


class game_state_message(abc.ABC):

    @property
    @abc.abstractmethod
    def message(self):
        pass

    @abc.abstractmethod
    def __init__(self, *argl, **argd):
        pass

class command_bad_syntax(game_state_message):
    __slots__ = 'command', 'proper_syntax_options'

    @property
    def message(self):
        syntax_options = tuple(f"'{self.command.upper()} {syntax_option}'" if syntax_option else f"'{self.command.upper()}'"
                                   for syntax_option in self.proper_syntax_options)
        if len(syntax_options) == 1:
            proper_syntax_options_str = syntax_options[0]
        elif len(syntax_options) == 2:
            proper_syntax_options_str = ' or '.join(syntax_options)
        else:
            proper_syntax_options_str = syntax_options[0]
            for index in range(1, len(syntax_options)):
                proper_syntax_options_str += ', '
                if index == len(syntax_options) - 1:
                    proper_syntax_options_str += 'or '
                proper_syntax_options_str += syntax_options[index]
        return f'{self.command.upper()} command: bad syntax. Should be {proper_syntax_options_str}.'

    def __init__(self, command, *proper_syntax_options):
        self.command = command
        self.proper_syntax_options = proper_syntax_options


class command_class_restricted(game_state_message):
    __slots__ = 'command', 'classes',

    @property
    def message(self):
        class_str = ''
        classes_plural = [class_str + 's' if class_str != 'thief' else 'thieves' for class_str in self.classes]
        if len(classes_plural) == 1:
            class_str = classes_plural[0]
        elif len(classes_plural) == 2:
            class_str = ' and '.join(classes_plural)
        else:
            class_str = ', '.join(classes_plural[:-1])
            class_str += ', and ' + classes_plural[-1]
        return f'Only {class_str} can use the {self.command.upper()} command.'

    def __init__(self, command, *classes):
        self.command = command
        self.classes = classes


class command_not_recognized(game_state_message):
    __slots__ = 'command',

    message = property(fget=(lambda self: 'Command not recognized.'))

    def __init__(self, command):
        self.command = command


class attack_command_attack_missed(game_state_message):
    __slots__ = 'creature_title',

    message = property(fget=(lambda self: f'Your attack on the {self.creature_title} missed. '
                                                   'It turns to attack!'))

    def __init__(self, creature_title):
        self.creature_title = creature_title


class attack_command_opponent_not_found(game_state_message):
    __slots__ = 'creature_title_given', 'opponent_present'

    @property
    def message(self):
        if self.opponent_present:
            return f"This room doesn't have a {self.creature_title_given}; but there is a {self.opponent_present}."
        else:
            return f"This room doesn't have a {self.creature_title_given}; nobody is here."

    def __init__(self, creature_title_given, opponent_present=''):
        self.creature_title_given = creature_title_given
        self.opponent_present = opponent_present


class attack_command_attack_hit(game_state_message):
    __slots__ = 'creature_title', 'damage_done', 'creature_slain'

    @property
    def message(self):
        if self.creature_slain:
            return f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage.'
        else:
            return (f'Your attack on the {self.creature_title} hit! You did {self.damage_done} damage. '
                    f'The {self.creature_title} turns to attack!')

    def __init__(self, creature_title, damage_done, creature_slain):
        self.creature_title = creature_title
        self.damage_done = damage_done
        self.creature_slain = creature_slain


class attack_command_you_have_no_weapon_or_wand_equipped(game_state_message):
    __slots__ = 'character_class',

    @property
    def message(self):
        if self.character_class == 'Mage':
            return "You have no wand or weapon equipped; you can't attack."
        else:
            return "You have no weapon equipped; you can't attack."

    def __init__(self, character_class):
        self.character_class = character_class


class be_attacked_by_command_attacked_and_hit(game_state_message):
    __slots__ = 'creature_title', 'damage_done', 'hit_points_left'

    message = property(fget=(lambda self: (f'The {self.creature_title} attacks! Their attack hits. They did '
                                                    f'{self.damage_done} damage! You have {self.hit_points_left} '
                                                    'hit points left.')))

    def __init__(self, creature_title, damage_done, hit_points_left):
        self.creature_title = creature_title
        self.damage_done = damage_done
        self.hit_points_left = hit_points_left


class be_attacked_by_command_attacked_and_not_hit(game_state_message):
    __slots__ = 'creature_title',

    message = property(fget=(lambda self: (f'The {self.creature_title} attacks! Their attack misses.')))

    def __init__(self, creature_title):
        self.creature_title = creature_title


class be_attacked_by_command_character_death(game_state_message):

    message = property(fget=lambda self: 'You have died!')

    def __init__(self):
        pass


class cast_spell_command_no_creature_to_target(game_state_message):
    __slots__ = ()

    message = property(fget=lambda self: f"You can't cast magic missile here; there is no creature here to target.")

    def __init__(self):
        pass


class cast_spell_command_cast_damaging_spell(game_state_message):
    __slots__ = 'creature_title', 'damage_dealt'

    message = property(fget=lambda self: f"A magic missile springs from your gesturing hand and unerringly strikes "
                                         f"the {self.creature_title}. You have done {self.damage_dealt} points of "
                                          "damage.")

    def __init__(self, creature_title, damage_dealt):
        self.creature_title = creature_title
        self.damage_dealt = damage_dealt


class cast_spell_command_cast_healing_spell(game_state_message):
    __slots__ = ()

    message = property(fget=lambda self: "You cast a healing spell on yourself.")

    def __init__(self):
        pass


class close_command_object_has_been_closed(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'You have closed the {self.target_obj}.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class close_command_object_is_already_closed(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'The {self.target_obj} is already closed.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class close_command_object_to_close_not_here(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f'You found no {self.target_title} here to close.')

    def __init__(self, target_title):
        self.target_title = target_title


class drink_command_drank_mana_potion_when_not_a_spellcaster(game_state_message):
    __slots__ = ()

    message = property(fget=lambda self: f'You feel a little strange, but otherwise nothing happens.')

    def __init__(self):
        pass


class drink_command_tried_to_drink_more_than_possessed(game_state_message):
    __slots__ = 'item_title', 'attempted_qty', 'possessed_qty'

    message = property(fget=lambda self: f"You can't drink {self.attempted_qty} {self.item_title}s. You only have {self.possessed_qty} of them.")

    def __init__(self, item_title, attempted_qty, possessed_qty):
        self.item_title = item_title
        self.attempted_qty = attempted_qty
        self.possessed_qty = possessed_qty


class drink_command_drank_mana_potion(game_state_message):
    __slots__ = 'amount_regained', 'current_mana_points', 'mana_point_total',

    @property
    def message(self):
        if self.amount_regained and self.current_mana_points == self.mana_point_total:
            return (f"You regained {self.amount_regained} mana points. You have full mana points! "
                    f"Your mana points are {self.current_mana_points}/{self.mana_point_total}.")
        elif self.amount_regained:
            return (f"You regained {self.amount_regained} mana points. Your mana points are "
                    f"{self.current_mana_points}/{self.mana_point_total}.")
        else:
            return (f"You didn't regain any mana points. Your mana points are "
                    f"{self.current_mana_points}/{self.mana_point_total}.")

    def __init__(self, amount_regained, current_mana_points, mana_point_total):
        self.amount_regained = amount_regained
        self.current_mana_points = current_mana_points
        self.mana_point_total = mana_point_total

class various_commands_underwent_healing_effect(game_state_message):
    __slots__ = 'amount_healed', 'current_hit_points', 'hit_point_total',

    @property
    def message(self):
        if self.amount_healed and self.current_hit_points == self.hit_point_total:
            return (f"You regained {self.amount_healed} hit points. You're fully healed! Your hit points are "
                    f"{self.current_hit_points}/{self.hit_point_total}.")
        elif self.amount_healed:
            return (f"You regained {self.amount_healed} hit points. Your hit points are "
                    f"{self.current_hit_points}/{self.hit_point_total}.")
        else:
            return (f"You didn't regain any hit points. Your hit points are "
                    f"{self.current_hit_points}/{self.hit_point_total}.")

    def __init__(self, amount_healed, current_hit_points, hit_point_total):
        self.amount_healed = amount_healed
        self.current_hit_points = current_hit_points
        self.hit_point_total = hit_point_total


class drink_command_item_not_drinkable(game_state_message):
    __slots__ = 'item_title',

    message = property(fget=lambda self: f"A {self.item_title} is not drinkable.")

    def __init__(self, item_title):
        self.item_title = item_title


class drink_command_item_not_in_inventory(game_state_message):
    __slots__ = 'item_title',

    message = property(fget=lambda self: f"You don't have a {self.item_title} in your inventory.")

    def __init__(self, item_title):
        self.item_title = item_title


class drop_command_dropped_item(game_state_message):
    __slots__ = 'item_title', 'amount_dropped', 'amount_on_floor', 'amount_left'

    @property
    def message(self):
        # The amount dropped and the amount on the floor both must be nonzero, but the amount left may be zero.
        drop_qty_str, drop_qty_pluralizer = (('a', '') if self.amount_dropped == 1 else (self.amount_dropped, 's'))
        floor_qty_str, floor_qty_pluralizer = (('a', '') if self.amount_on_floor == 1 else (self.amount_on_floor, 's'))
        left_qty_pluralizer = ('' if self.amount_left == 1 else 's' if self.amount_left > 1 else None)
        if left_qty_pluralizer is not None:
            return (f'You dropped {drop_qty_str} {self.item_title}{drop_qty_pluralizer}. You see {floor_qty_str} '
                    f'{self.item_title}{floor_qty_pluralizer} here. You have {self.amount_left} {self.item_title}'
                    f'{left_qty_pluralizer} left.')
        else:
            return (f'You dropped {drop_qty_str} {self.item_title}{drop_qty_pluralizer}. You see {floor_qty_str} '
                    f'{self.item_title}{floor_qty_pluralizer} here. You have no {self.item_title}s left.')

    def __init__(self, item_title, amount_dropped, amount_on_floor, amount_left):
        self.item_title = item_title
        self.amount_dropped = amount_dropped
        self.amount_on_floor = amount_on_floor
        self.amount_left = amount_left


class drop_command_quantity_unclear(game_state_message):

    message = property(fget=lambda self: 'Amount to drop unclear. How many do you mean?')

    def __init__(self):
        pass


class drop_command_trying_to_drop_item_you_dont_have(game_state_message):
    __slots__ = 'item_title', 'amount_attempted'

    @property
    def message(self):
        if self.amount_attempted > 1:
            return f"You don't have any {self.item_title}s in your inventory."
        else:
            return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title, amount_attempted):
        self.item_title = item_title
        self.amount_attempted = amount_attempted


class drop_command_trying_to_drop_more_than_you_have(game_state_message):
    __slots__ = 'item_title', 'amount_attempted', 'amount_had'

    @property
    def message(self):
        if self.amount_attempted > 1 and self.amount_had == 1:
            return f"You can't drop {self.amount_attempted} {self.item_title}s. You only have {self.amount_had} {self.item_title} in your inventory."
        else:   # self.amount_attempted > 1 and self.amount_had > 1
            return f"You can't drop {self.amount_attempted} {self.item_title}s. You only have {self.amount_had} {self.item_title}s in your inventory."

    def __init__(self, item_title, amount_attempted, amount_had):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_had = amount_had


class equip_command_class_cant_use_item(game_state_message):
    __slots__ = 'character_class', 'item_title', 'item_type'

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_type, gerund=False)
        pluralizer = 's' if self.item_type != 'armor' else ''
        return f"{self.character_class}s can't {item_usage_verb} {self.item_title}{pluralizer}."

    def __init__(self, character_class, item_title, item_type):
        self.character_class = character_class
        self.item_title = item_title
        self.item_type = item_type


class equip_command_item_equipped(game_state_message):
    __slots__ = 'item_title', 'item_type', 'changed_value_1', 'value_type_1', 'changed_value_2', 'value_type_2', 'change_text'

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_type, gerund=True)
        indirect_article = 'a ' if self.item_type != 'armor' else ''
        plussign = '+' if self.value_type_1 == 'attack bonus' and self.changed_value_1 >= 0 else ''
        if self.changed_value_1 is None and self.changed_value_2 is None:
            return_str = f"You're now {item_usage_verb} {indirect_article}{self.item_title}."
        elif self.changed_value_2 is None:
            return_str = (f"You're now {item_usage_verb} {indirect_article}{self.item_title}. "
                          f"Your {self.value_type_1} is {plussign}{self.changed_value_1}.")
        else:
            return_str = (f"You're now {item_usage_verb} {indirect_article}{self.item_title}. "
                          f"Your {self.value_type_1} is {plussign}{self.changed_value_1}, "
                          f"and your {self.value_type_2} is {self.changed_value_2}.")
        if self.change_text:
            return_str += ' ' + self.change_text
        return return_str

    def __init__(self, item_title, item_type, changed_value_1=None, value_type_1=None, changed_value_2=None, value_type_2=None, change_text=''):
        self.item_title = item_title
        self.item_type = item_type
        self.changed_value_1 = changed_value_1
        self.value_type_1 = value_type_1
        self.changed_value_2 = changed_value_2
        self.value_type_2 = value_type_2
        self.change_text = change_text


class equip_command_no_such_item_in_inventory(game_state_message):
    __slots__ = 'item_title',

    message = property(fget=lambda self: f"You don't have a {self.item_title} in your inventory.")

    def __init__(self, item_title):
        self.item_title = item_title


class equip_or_unequip_command_item_unequipped(game_state_message):
    __slots__ = 'item_title', 'item_type', 'changed_value_1', 'value_type_1', 'changed_value_2', 'value_type_2', 'change_text',

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_type, gerund=True)
        indirect_article = 'a ' if self.item_type != 'armor' else ''
        if self.changed_value_1 is None and self.changed_value_2 is None:
            return_str = f"You're no longer {item_usage_verb} {indirect_article}{self.item_title}."
        elif self.changed_value_2 is None:
            return_str = (f"You're no longer {item_usage_verb} {indirect_article}{self.item_title}. "
                          f"Your {self.value_type_1} is {self.changed_value_1}.")
        else:
            return_str = (f"You're no longer {item_usage_verb} {indirect_article}{self.item_title}. "
                          f"Your {self.value_type_1} is {self.changed_value_1}, "
                          f"and your {self.value_type_2} is {self.changed_value_2}.")
        if self.change_text:
            return return_str + ' ' + self.change_text
        else:
            return return_str

    def __init__(self, item_title, item_type, changed_value_1=None, value_type_1=None, changed_value_2=None, value_type_2=None, change_text=''):
        self.item_title = item_title
        self.item_type = item_type
        self.changed_value_1 = changed_value_1
        self.value_type_1 = value_type_1
        self.changed_value_2 = changed_value_2
        self.value_type_2 = value_type_2
        self.change_text = change_text


class exit_command_exitted_room(game_state_message):
    __slots__ = 'compass_dir', 'portal_type'

    message = property(fget=lambda self: f'You leave the room via the {self.compass_dir} {self.portal_type}.')

    def __init__(self, compass_dir, portal_type):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class inspect_command_found_door_or_doorway(game_state_message):
    __slots__ = 'compass_dir', 'door_obj'

    @property
    def message(self):
        door_or_doorway = 'doorway' if self.door_obj.door_type == 'doorway' else 'door'
        descr_str = f"This {door_or_doorway} is set into the {self.compass_dir} wall of the room. {self.door_obj.description}"
        if self.door_obj.closeable:
            if self.door_obj.is_closed and self.door_obj.is_locked:
                descr_str += " It is closed and locked."
            elif self.door_obj.is_closed and not self.door_obj.is_locked:
                descr_str += " It is closed but unlocked."
            else:
                descr_str += " It is open."
        return descr_str

    def __init__(self, compass_dir, door_obj):
        self.compass_dir = compass_dir
        self.door_obj = door_obj


class inspect_command_found_container_here(game_state_message):
    __slots__ = 'container_description', 'container_type', 'container', 'is_locked', 'is_closed'

    @property
    def message(self):
        if self.container_type == 'chest':
            if self.is_locked is True and self.is_closed is True:
                return f'{self.container_description} It is closed and locked.'
            elif self.is_locked is False and self.is_closed is True:
                return f'{self.container_description} It is closed but unlocked.'
            elif self.is_locked is False and self.is_closed is False:
                return f'{self.container_description} It is unlocked and open. {self.contents}'
            # `self.is_locked is True and self.is_closed is False` is not a possible outcome of these tests because
            # it's an invalid combination, and is checked for in __init__. If that is the combination of booleans, an
            # exception is raised.
            elif self.is_locked is None and self.is_closed is True:
                return f'{self.container_description} It is closed.'
            elif self.is_locked is None and self.is_closed is False:
                return f'{self.container_description} It is open. {self.contents}'
            elif self.is_locked is True and self.is_closed is None:
                return f'{self.container_description} It is locked.'
            elif self.is_locked is False and self.is_closed is None:
                return f'{self.container_description} It is unlocked.'
            else:  # None and None
                return self.container_description
        elif self.container_type == 'corpse':
            return f'{self.container_description} {self.contents}'

    @property
    def contents(self):
        content_qty_obj_pairs = sorted(self.container.values(), key=lambda arg: arg[1].title)
        contents_str_tuple = tuple('a ' + item_obj.title if qty == 1 else str(qty) + ' ' + item_obj.title + 's'
                                       for qty, item_obj in content_qty_obj_pairs)
        if self.container_type == 'chest':
            if len(contents_str_tuple) == 0:
                return 'It is empty.'
            elif len(contents_str_tuple) == 1:
                return f'It contains {contents_str_tuple[0]}.'
            elif len(contents_str_tuple) == 2:
                return f'It contains {contents_str_tuple[0]} and {contents_str_tuple[1]}.'
            else:
                return 'It contains %s, and %s.' % (', '.join(contents_str_tuple[0:-1]), contents_str_tuple[-1])
        else:
            if len(contents_str_tuple) == 0:
                return 'They have nothing on them.'
            elif len(contents_str_tuple) == 1:
                return f'They have {contents_str_tuple[0]} on them.'
            elif len(contents_str_tuple) == 2:
                return f'They have {contents_str_tuple[0]} and {contents_str_tuple[1]} on them.'
            else:
                return 'They have %s, and %s on them.' % (', '.join(contents_str_tuple[0:-1]), contents_str_tuple[-1])

    def __init__(self, container_obj):
        self.container = container_obj
        self.container_description = container_obj.description
        self.is_locked = container_obj.is_locked
        self.is_closed = container_obj.is_closed
        self.container_type = container_obj.container_type
        if self.is_locked is True and self.is_closed is False:
            raise internal_exception(f'Container {container_obj.internal_name} has is_locked = True and is_open = False, invalid combination of parameters.')


class inspect_command_found_creature_here(game_state_message):
    __slots__ = 'creature_description',

    message = property(fget=lambda self: self.creature_description)

    def __init__(self, creature_description):
        self.creature_description = creature_description


class inspect_command_found_item_or_items_here(game_state_message):
    __slots__ = 'item_description', 'item_qty'

    @property
    def message(self):
        if self.item_qty > 1:
            return f'{self.item_description} You see {self.item_qty} here.'
        else:
            return self.item_description

    def __init__(self, item_description, item_qty):
        self.item_description = item_description
        self.item_qty = item_qty


class inspect_command_found_nothing(game_state_message):
    __slots__ = 'item_title', 'item_container', 'container_type'

    @property
    def message(self):
        if self.item_container is not None:
            if self.container_type == 'chest':
                return f'The {self.item_container} has no {self.item_title} in it.'
            elif self.container_type == 'corpse':
                return f'The {self.item_container} has no {self.item_title} on it.'
            else:
                return f'You have no {self.item_title} in your inventory.'
        else:
            return f'You see no {self.item_title} here.'

    def __init__(self, item_title, item_container=None, container_type=None):
        self.item_title = item_title


class inventory_command_display_inventory(game_state_message):
    __slots__ = 'inventory_contents',

    @property
    def message(self):
        display_strs_list = list()
        for item_qty, item_obj in self.inventory_contents:
            if item_obj.item_type == 'armor' and item_qty == 1:
                display_strs_list.append(f"a suit of {item_obj.title}")
            elif item_obj.item_type == 'armor' and item_qty > 1:
                display_strs_list.append(f"{item_qty} suits of {item_obj.title}")
            elif item_qty == 1 and item_obj.title[0] in 'aeiou':
                display_strs_list.append(f"an {item_obj.title}")
            elif item_qty == 1:
                display_strs_list.append(f"a {item_obj.title}")
            else:
                display_strs_list.append(f"{item_qty} {item_obj.title}s")
        if len(display_strs_list) == 1:
            return f"You have {display_strs_list[0]} in your inventory."
        elif len(display_strs_list) == 2:
            return f"You have {display_strs_list[0]} and {display_strs_list[1]} in your inventory."
        else:
            inventory_str = ', '.join(display_strs_list[0:-1])
            inventory_str += f', and {display_strs_list[-1]}'
            return f"You have {inventory_str} in your inventory."

    def __init__(self, inventory_contents_list):
        self.inventory_contents = inventory_contents_list


class lock_command_dont_possess_correct_key(game_state_message):
    __slots__ = 'object_to_lock_title', 'key_needed',

    message = property(fget=lambda self: f'To lock the {self.object_to_lock_title} you need a {self.key_needed}.')

    def __init__(self, object_to_lock_title, key_needed):
        self.object_to_lock_title = object_to_lock_title
        self.key_needed = key_needed


class lock_command_object_has_been_locked(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'You have locked the {self.target_obj}.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class lock_command_object_is_already_locked(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'The {self.target_obj} is already locked.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class lock_command_object_to_lock_not_here(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f'You found no {self.target_title} here to lock.')

    def __init__(self, target_title):
        self.target_title = target_title


class open_command_object_has_been_opened(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'You have opened the {self.target_obj}.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class open_command_object_is_already_open(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'The {self.target_obj} is already open.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class open_command_object_is_locked(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'The {self.target_obj} is locked.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class open_command_object_to_open_not_here(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f'You found no {self.target_title} here to open.')

    def __init__(self, target_title):
        self.target_title = target_title


class pick_lock_command_target_not_locked(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f'The {self.target_title} is not locked.')

    def __init__(self, target_title):
        self.target_title = target_title


class pick_lock_command_target_has_been_unlocked(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f'You have unlocked the {self.target_title}.')

    def __init__(self, target_title):
        self.target_title = target_title


class pick_lock_command_target_not_found(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f'This room has no {self.target_title}.')

    def __init__(self, target_title):
        self.target_title = target_title


class pick_lock_command_target_cant_be_unlocked_or_not_found(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f"The {self.target_title} is not found or can't be unlocked.")

    def __init__(self, target_title):
        self.target_title = target_title


class pick_up_command_item_not_found(game_state_message):
    __slots__ = 'item_title', 'amount_attempted', 'items_here'

    @property
    def message(self):
        item_pluralizer = 's' if self.amount_attempted > 1 else ''
        if self.items_here:
            items_here_str_tuple = tuple(f'a {item_title}' if item_count == 1 else f'{item_count} {item_title}s' for item_count, item_title in self.items_here)
            if len(items_here_str_tuple) == 1:
                items_here_str = items_here_str_tuple[0]
            elif len(items_here_str_tuple) == 2:
                items_here_str = ' and '.join(items_here_str_tuple)
            else:
                items_here_str = ', '.join(items_here_str_tuple[:-1]) + ', and ' + items_here_str_tuple[-1]
            return f'You see no {self.item_title}{item_pluralizer} here. However, there is {items_here_str} here.'
        else:
            return f'You see no {self.item_title}{item_pluralizer} here.'

    def __init__(self, item_title, amount_attempted, *items_here):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.items_here = tuple(sorted(items_here, key=operator.itemgetter(1)))


class pick_up_command_item_picked_up(game_state_message):
    __slots__ = 'item_title', 'pick_up_amount', 'amount_had'

    @property
    def message(self):
        if self.pick_up_amount == 1 and self.amount_had == 1:
            return f'You picked up a {self.item_title}. You have 1 {self.item_title}.'
        elif self.pick_up_amount == 1 and self.amount_had > 1:
            return f'You picked up a {self.item_title}. You have {self.amount_had} {self.item_title}s.'
        else:
            return f'You picked up {self.pick_up_amount} {self.item_title}s. You have {self.amount_had} {self.item_title}s.'

    def __init__(self, item_title, pick_up_amount, amount_had):
        self.item_title = item_title
        self.pick_up_amount = pick_up_amount
        self.amount_had = amount_had


class pick_up_command_quantity_unclear(game_state_message):

    message = property(fget=lambda self: 'Amount to pick up unclear. How many do you mean?')

    def __init__(self):
        pass


class pick_up_command_trying_to_pick_up_more_than_is_present(game_state_message):
    __slots__ = 'item_title', 'amount_attempted', 'amount_present'

    message = property(fget=lambda self: f"You can't pick up {self.amount_attempted} {self.item_title}s. Only {self.amount_present} is here.")

    def __init__(self, item_title, amount_attempted, amount_present):
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_present = amount_present


class put_command_amount_put(game_state_message):
    __slots__ = 'item_title', 'container_title', 'container_type', 'amount_put', 'amount_left'

    @property
    def message(self):
        amount_put_pluralizer = 's' if self.amount_put > 1 else ''
        amount_left_pluralizer = 's' if self.amount_left > 1 or not self.amount_left else ''
        if self.amount_left and self.container_type == 'chest':
            return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} in the {self.container_title}.'
                    f' You have {self.amount_left} {self.item_title}{amount_left_pluralizer} left.')
        elif not self.amount_left and self.container_type == 'chest':
            return (f'You put {self.amount_put} {self.item_title}{amount_put_pluralizer} in the {self.container_title}.'
                    f' You have no more {self.item_title}{amount_left_pluralizer}.')
        elif self.amount_left and self.container_type == 'corpse':
            return (f"You put {self.amount_put} {self.item_title}{amount_put_pluralizer} on the {self.container_title}'s person."
                    f' You have {self.amount_left} {self.item_title}{amount_left_pluralizer} left.')
        else:  # not self.amount_left and self.container_type == 'corpse':
            return (f"You put {self.amount_put} {self.item_title}{amount_put_pluralizer} on the {self.container_title}'s person."
                    f' You have no more {self.item_title}{amount_left_pluralizer}.')

    def __init__(self, item_title, container_title, container_type, amount_put, amount_left):
        self.item_title = item_title
        self.container_title = container_title
        self.container_type = container_type
        self.amount_put = amount_put
        self.amount_left = amount_left


class put_command_item_not_in_inventory(game_state_message):
    __slots__ = 'amount_attempted', 'item_title'

    @property
    def message(self):
        if self.amount_attempted > 1:
            return f"You don't have any {self.item_title}s in your inventory."
        else:
            return f"You don't have a {self.item_title} in your inventory."

    def __init__(self, item_title, amount_attempted):
        self.amount_attempted = amount_attempted
        self.item_title = item_title


class put_command_quantity_unclear(game_state_message):

    message = property(fget=lambda self: 'Amount to put unclear. How many do you mean?')

    def __init__(self):
        pass


class put_command_trying_to_put_more_than_you_have(game_state_message):
    __slots__ = 'item_title', 'amount_present'

    @property
    def message(self):
        pluralizer = 's' if self.amount_present > 1 else ''
        return f'You only have {self.amount_present} {self.item_title}{pluralizer} in your inventory.'

    def __init__(self, item_title, amount_present):
        self.item_title = item_title
        self.amount_present = amount_present


class satisfied_command_game_begins(game_state_message):

    message = property(fget=lambda self: 'The game has begun!')

    def __init__(self):
        pass


class set_class_command_class_set(game_state_message):
    __slots__ = 'class_str',

    message = property(fget=lambda self: f'Your class, {self.class_str}, has been set.')

    def __init__(self, class_str):
        self.class_str = class_str


class set_class_command_invalid_class(game_state_message):
    __slots__ = 'bad_class',

    message = property(fget=lambda self: f"'{self.bad_class}' is not a valid class choice. Please choose Warrior, "
                                          'Thief, Mage, or Priest.')

    def __init__(self, bad_class):
        self.bad_class = bad_class


class set_name_command_invalid_part(game_state_message):
    __slots__ = 'name_part',

    message = property(fget=lambda self: f'The name {self.name_part} is invalid; must be a capital letter followed by'
                                          ' lowercase letters.')

    def __init__(self, name_part):
        self.name_part = name_part


class set_name_command_name_set(game_state_message):
    __slots__ = 'name',

    message = property(fget=lambda self: f"Your name, '{self.name}', has been set.")

    def __init__(self, name):
        self.name = name


class set_name_or_class_command_display_rolled_stats(game_state_message):
    __slots__ = 'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'

    @property
    def message(self):
        return (f'Your ability scores are Strength {self.strength}, Dexterity {self.dexterity}, Constitution '
                f'{self.constitution}, Intelligence {self.intelligence}, Wisdom {self.wisdom}, Charisma {self.charisma}'
                '.\nAre you satisfied with these scores or would you like to reroll?')

    def __init__(self, strength, dexterity, constitution, intelligence, wisdom, charisma):
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma


class take_command_item_not_found_in_container(game_state_message):
    __slots__ = 'container_title', 'amount_attempted', 'container_type', 'item_title'

    @property
    def message(self):
        if self.container_type == 'chest' and (self.amount_attempted == 1 or self.amount_attempted is math.nan):
            return f"The {self.container_title} doesn't have a {self.item_title} in it."
        elif self.container_type == 'chest' and self.amount_attempted > 1:
            return f"The {self.container_title} doesn't have any {self.item_title}s in it."
        elif self.container_type == 'corpse' and (self.amount_attempted == 1 or self.amount_attempted is math.nan):
            return f"The {self.container_title} doesn't have a {self.item_title} on them."
        else:  # self.container_type == 'corpse' and self.amount_attempted > 1:
            return f"The {self.container_title} doesn't have any {self.item_title}s on them."

    def __init__(self, container_title, amount_attempted, container_type, item_title):
        self.container_title = container_title
        self.amount_attempted = amount_attempted
        self.container_type = container_type
        self.item_title = item_title


class status_command_output(game_state_message):
    __slots__ = 'hit_points', 'hit_point_total', 'armor_class', 'attack_bonus', 'damage','mana_points', 'mana_point_total', 'armor', 'shield', 'weapon', 'wand', 'is_mage'

    @property
    def message(self):
        hp_str = f'Hit Points: {self.hit_points}/{self.hit_point_total}'
        if self.mana_points:
            mp_str = f'Mana Points: {self.mana_points}/{self.mana_point_total}'
        armor_str = f'Armor: {self.armor}' if self.armor else 'Armor: none'
        shield_str = f'Shield: {self.shield}' if self.shield else 'Shield: none'
        if self.weapon or (self.is_mage and self.wand):
            atk_plussign = '+' if self.attack_bonus >= 0 else ''
            atk_dmg_str = f'Attack: {atk_plussign}{self.attack_bonus} ({self.damage} damage)'
        elif self.is_mage:
            atk_dmg_str = f'Attack: no wand or weapon equipped'
        else:
            atk_dmg_str = f'Attack: no weapon equipped'
        wand_str = f'Wand: {self.wand}' if self.wand else 'Wand: none' if self.is_mage else ''
        weapon_str = f'Weapon: {self.weapon}' if self.weapon else 'Weapon: none'
        ac_str = f'Armor Class: {self.armor_class}'
        points_display = f'{hp_str} - {mp_str}' if self.mana_points else hp_str
        stats_display = f'{atk_dmg_str} - {ac_str}'
        equip_display = f'{wand_str} - ' if wand_str else ''
        equip_display += f'{weapon_str} - {armor_str} - {shield_str}'
        return f'{points_display} | {stats_display} | {equip_display}'

    def __init__(self, armor_class, attack_bonus, damage, armor, shield, weapon, wand, hit_points, hit_point_total,
                       mana_points=None, mana_point_total=None, is_mage=False):
        self.armor_class = armor_class
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.armor = armor
        self.shield = shield
        self.weapon = weapon
        self.wand = wand
        self.hit_points = hit_points
        self.hit_point_total = hit_point_total
        self.mana_points = mana_points
        self.mana_point_total = mana_point_total
        self.is_mage = is_mage


class take_command_item_or_items_taken(game_state_message):
    __slots__ = 'container_title', 'item_title', 'amount_taken'

    @property
    def message(self):
        if self.amount_taken > 1:
            return f'You took {self.amount_taken} {self.item_title}s from the {self.container_title}.'
        else:
            return f'You took a {self.item_title} from the {self.container_title}.'

    def __init__(self, container_title, item_title, amount_taken):
        self.container_title = container_title
        self.item_title = item_title
        self.amount_taken = amount_taken


class take_command_quantity_unclear(game_state_message):

    message = property(fget=lambda self: 'Amount to take unclear. How many do you want?')

    def __init__(self):
        pass


class take_command_trying_to_take_more_than_is_present(game_state_message):
    __slots__ = 'container_title', 'container_type', 'item_title', 'amount_attempted', 'amount_present'

    message = property(fget=lambda self: f"You can't take {self.amount_attempted} {self.item_title}s from the {self.container_title}. Only {self.amount_present} is there.")

    def __init__(self, container_title, container_type, item_title, amount_attempted, amount_present):
        self.container_title = container_title
        self.container_type = container_type
        self.item_title = item_title
        self.amount_attempted = amount_attempted
        self.amount_present = amount_present


class unequip_command_item_not_equipped(game_state_message):
    __slots__ = 'item_asked_title', 'item_asked_type', 'item_present_title'

    @property
    def message(self):
        item_usage_verb = usage_verb(self.item_asked_type, gerund=True)
        indirect_article = 'a ' if self.item_asked_type != 'armor' else ''
        if self.item_asked_type and self.item_present_title:
            return f"You're not {item_usage_verb} {indirect_article}{self.item_asked_title}. You're {item_usage_verb} {indirect_article}{self.item_present_title}."
        elif self.item_asked_type:
            return f"You're not {item_usage_verb} {indirect_article}{self.item_asked_title}."
        else:
            return f"You don't have a {self.item_asked_title} equipped."

    def __init__(self, item_asked_title, item_asked_type=None, item_present_title=None):
        self.item_asked_title = item_asked_title
        self.item_asked_type = item_asked_type
        self.item_present_title = item_present_title


class unlock_command_dont_possess_correct_key(game_state_message):
    __slots__ = 'object_to_unlock_title', 'key_needed',

    message = property(fget=lambda self: f'To unlock the {self.object_to_unlock_title} you need a {self.key_needed}.')

    def __init__(self, object_to_unlock_title, key_needed):
        self.object_to_unlock_title = object_to_unlock_title
        self.key_needed = key_needed


class unlock_command_object_has_been_unlocked(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'You have unlocked the {self.target_obj}.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class unlock_command_object_is_already_unlocked(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'The {self.target_obj} is already unlocked.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class unlock_command_object_to_unlock_not_here(game_state_message):
    __slots__ = 'target_title',

    message = property(fget=lambda self: f'You found no {self.target_title} here to unlock.')

    def __init__(self, target_title):
        self.target_title = target_title


class various_commands_container_is_closed(game_state_message):
    __slots__ = 'target_obj',

    message = property(fget=lambda self: f'The {self.target_obj} is closed.')

    def __init__(self, target_obj):
        self.target_obj = target_obj


class various_commands_container_not_found(game_state_message):
    __slots__ = 'container_not_found_title', 'container_present_title'

    @property
    def message(self):
        if self.container_present_title is not None:
            return f'There is no {self.container_not_found_title} here. However, there *is* a {self.container_present_title} here.'
        else:
            return f'There is no {self.container_not_found_title} here.'

    def __init__(self, container_not_found_title, container_present_title=None):
        self.container_not_found_title = container_not_found_title
        self.container_present_title = container_present_title


class various_commands_door_not_present(game_state_message):
    __slots__ = 'compass_dir', 'portal_type'

    @property
    def message(self):
        if self.portal_type is not None:
            return f'This room does not have a {self.compass_dir} {self.portal_type}.'
        else:
            return f'This room does not have a {self.compass_dir} exit.'

    def __init__(self, compass_dir, portal_type=None):
        self.compass_dir = compass_dir
        self.portal_type = portal_type


class various_commands_foe_death(game_state_message):
    __slots__ = 'creature_title',

    @property
    def message(self):
        return f'The {self.creature_title} is slain.'

    def __init__(self, creature_title):
        self.creature_title = creature_title




