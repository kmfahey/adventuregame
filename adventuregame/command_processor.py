#!/usr/bin/python

import math
import re

from adventuregame.game_elements import *
from adventuregame.game_state_messages import *
from adventuregame.utility import *

__name__ = 'adventuregame.command_processor'


Spell_Damage = "3d8+5"

Spell_Mana_Cost = 5


class command_processor(object):
    __slots__ = 'game_state', 'dispatch_table',

    # All return values from *_command methods in this class are tuples. Every *_command method returns one or more
    # *_command_* objects, reflecting a sequence of changes in game state. (For example, an ATTACK action that doesn't
    # kill the foe will prompt the foe to attack. The foe's attack might lead to the character's death. So the return
    # value might be a `attack_command_attack_hit` object, a `be_attacked_by_command_attacked_and_hit` object, and a
    # `be_attacked_by_command_character_death` object, each bearing a message in its `message` property. The code which
    # handles the result of the ATTACK action knows it's receiving a tuple and will iterate through the result objects
    # and display each one's message to the player in turn.

    valid_name_re = re.compile('^[A-Z][a-z]+$')

    valid_class_re = re.compile('^(Warrior|Thief|Mage|Priest)$')

    pregame_commands = {'set_name', 'set_class', 'reroll', 'begin_game', 'quit'}

    ingame_commands = {'attack', 'cast_spell', 'close', 'drink', 'drop', 'equip', 'leave', 'inventory', 'look_at', 
                       'lock', 'inspect', 'open', 'pick_lock', 'pick_up', 'quit', 'put', 'quit', 'status', 'take', 
                       'unequip', 'unlock'}

    def __init__(self, game_state_obj):
        self.dispatch_table = dict()
        commands_set = self.pregame_commands | self.ingame_commands
        for method_name in dir(type(self)):
            if not method_name.endswith('_command') or method_name.startswith('_'):
                continue
            command = method_name.rsplit('_', maxsplit=1)[0]
            self.dispatch_table[command] = getattr(self, method_name)
            if command not in commands_set:
                raise internal_exception("Inconsistency between set list of commands and command methods found by "
                                         f"introspection: method {method_name}() does not correspond to a command in "
                                         "pregame_commands or ingame_commands.")
            commands_set.remove(command)
        if len(commands_set):
            raise internal_exception("Inconsistency between set list of commands and command methods found by "
                                     f"introspection: command '{commands_set.pop()} does not correspond to a command "
                                     "in pregame_commands or ingame_commands.")
        self.game_state = game_state_obj

    def process(self, natural_language_str):
        tokens = natural_language_str.strip().split()
        command = tokens.pop(0).lower()
        if command == 'cast' and len(tokens) and tokens[0].lower() == 'spell':
            command += '_' + tokens.pop(0).lower()
        elif command == 'leave' and len(tokens) and (tokens[0].lower() == 'using' or tokens[0].lower() == 'via'):
            tokens.pop(0)
        elif command == "begin":
            if len(tokens) >= 1 and tokens[0] == 'game' or len(tokens) >= 2 and tokens[0:2] == ['the', 'game']:
                if tokens[0] == 'the':
                    tokens.pop(0)
                command += '_' + tokens.pop(0)
            elif not len(tokens):
                command = 'begin_game'
        elif command == 'look' and len(tokens) and tokens[0].lower() == 'at':
            command += '_' + tokens.pop(0).lower()
        elif command == 'pick' and len(tokens) and (tokens[0].lower() == 'up' or tokens[0].lower() == 'lock'):
            command += '_' + tokens.pop(0).lower()
        elif command == "quit":
            if len(tokens) >= 1 and tokens[0] == 'game' or len(tokens) >= 2 and tokens[0:2] == ['the', 'game']:
                if tokens[0] == 'the':
                    tokens.pop(0)
                tokens.pop(0)
        elif command == 'set' and len(tokens) and (tokens[0].lower() == 'name' or tokens[0].lower() == 'class'):
            command += '_' + tokens.pop(0).lower()
            if len(tokens) and tokens[0] == 'to':
                tokens.pop(0)
        elif command == 'show' and len(tokens) and tokens[0].lower() == 'inventory':
            command = tokens.pop(0).lower()
        if command not in ('set_name', 'set_class'):
            tokens = tuple(map(str.lower, tokens))
        if command not in self.dispatch_table and not self.game_state.game_has_begun:
            return command_not_recognized(command, self.pregame_commands, self.game_state.game_has_begun),
        elif command not in self.dispatch_table and self.game_state.game_has_begun:
            return command_not_recognized(command, self.ingame_commands, self.game_state.game_has_begun),
        elif not self.game_state.game_has_begun and command not in self.pregame_commands:
            return command_not_allowed_now(command, self.pregame_commands, self.game_state.game_has_begun),
        elif self.game_state.game_has_begun and command not in self.ingame_commands:
            return command_not_allowed_now(command, self.ingame_commands, self.game_state.game_has_begun),
        return self.dispatch_table[command](*tokens)

    def attack_command(self, *tokens):
        if (not self.game_state.character.weapon_equipped
                and (self.game_state.character_class != "Mage" or not self.game_state.character.wand_equipped)):
            return attack_command_you_have_no_weapon_or_wand_equipped(self.game_state.character_class),
        creature_title_token = ' '.join(tokens)
        if not self.game_state.rooms_state.cursor.creature_here:
            return attack_command_opponent_not_found(creature_title_token),
        elif self.game_state.rooms_state.cursor.creature_here.title.lower() != creature_title_token:
            return attack_command_opponent_not_found(creature_title_token,
                                                     self.game_state.rooms_state.cursor.creature_here.title),
        creature_obj = self.game_state.rooms_state.cursor.creature_here
        attack_roll_dice_expr = self.game_state.character.attack_roll
        damage_roll_dice_expr = self.game_state.character.damage_roll
        attack_result = roll_dice(attack_roll_dice_expr)
        if attack_result < creature_obj.armor_class:
            attack_missed_result = attack_command_attack_missed(creature_obj.title)
            be_attacked_by_result = self._be_attacked_by_command(creature_obj)
            return (attack_missed_result,) + be_attacked_by_result
        else:
            damage_result = roll_dice(damage_roll_dice_expr)
            creature_obj.take_damage(damage_result)
            if creature_obj.hit_points == 0:
                corpse_obj = creature_obj.convert_to_corpse()
                self.game_state.rooms_state.cursor.container_here = corpse_obj
                self.game_state.rooms_state.cursor.creature_here = None
                return (attack_command_attack_hit(creature_obj.title, damage_result, True),
                        various_commands_foe_death(creature_obj.title))
            else:
                attack_hit_result = attack_command_attack_hit(creature_obj.title, damage_result, False)
                be_attacked_by_result = self._be_attacked_by_command(creature_obj)
                return (attack_hit_result,) + be_attacked_by_result

    def _be_attacked_by_command(self, creature_obj):
        attack_roll_dice_expr = creature_obj.attack_roll
        damage_roll_dice_expr = creature_obj.damage_roll
        attack_result = roll_dice(attack_roll_dice_expr)
        if attack_result < self.game_state.character.armor_class:
            return be_attacked_by_command_attacked_and_not_hit(creature_obj.title),
        else:
            damage_done = roll_dice(damage_roll_dice_expr)
            self.game_state.character.take_damage(damage_done)
            if self.game_state.character.is_dead:
                return (be_attacked_by_command_attacked_and_hit(creature_obj.title, damage_done, 0),
                        be_attacked_by_command_character_death())
            else:
                return be_attacked_by_command_attacked_and_hit(creature_obj.title, damage_done,
                                                               self.game_state.character.hit_points)

    def cast_spell_command(self, *tokens):
        if self.game_state.character_class not in ('Mage', 'Priest'):
            return command_class_restricted('CAST SPELL', 'mage', 'priest'),
        elif len(tokens):
            return command_bad_syntax('CAST SPELL', ''),
        elif self.game_state.character.mana_points < Spell_Mana_Cost:
            return cast_spell_command_insuffient_mana(self.game_state.character.mana_points,
                                                      self.game_state.character.mana_point_total, Spell_Mana_Cost),
        elif self.game_state.character_class == 'Mage':
            if self.game_state.rooms_state.cursor.creature_here is None:
                return cast_spell_command_no_creature_to_target(),
            else:
                damage_dealt = roll_dice(Spell_Damage)
                creature_obj = self.game_state.rooms_state.cursor.creature_here
                creature_obj.take_damage(damage_dealt)
                if creature_obj.is_dead:
                    return (cast_spell_command_cast_damaging_spell(creature_obj.title, damage_dealt),
                            various_commands_foe_death(creature_obj.title))
                else:
                    be_attacked_by_result = self._be_attacked_by_command(creature_obj)
                    return ((cast_spell_command_cast_damaging_spell(creature_obj.title, damage_dealt),) + 
                                                                    be_attacked_by_result)
        else:
            damage_rolled = roll_dice(Spell_Damage)
            healed_amt = self.game_state.character.heal_damage(damage_rolled)
            return (cast_spell_command_cast_healing_spell(),
                    various_commands_underwent_healing_effect(healed_amt, self.game_state.character.hit_points,
                                                              self.game_state.character.hit_point_total))

    def close_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('CLOSE', *tokens)
        if isinstance(result[0], game_state_message):
            return result
        else:
            object_to_close, = result
        if object_to_close.is_closed:
            return close_command_object_is_already_closed(object_to_close.title),
        else:
            object_to_close.is_closed = True
            return close_command_object_has_been_closed(object_to_close.title),

    def drink_command(self, *tokens):
        if not len(tokens) or tokens == ('the',):
            return command_bad_syntax('DRINK', '[THE] <potion name>'),
        if tokens[0] == 'the' or tokens[0] == 'a':
            drinking_qty = 1
            tokens = tokens[1:]
        elif tokens[0].isdigit() or lexical_number_in_1_99_re.match(tokens[0]):
            drinking_qty = int(tokens[0]) if tokens[0].isdigit() else lexical_number_to_digits(tokens[0])
            if (drinking_qty > 1 and not tokens[-1].endswith('s')) or (drinking_qty == 1 and tokens[-1].endswith('s')):
                return command_bad_syntax('DRINK', '[THE] <potion name>'),
            tokens = tokens[1:]
        else:
            drinking_qty = 1
            if tokens[-1].endswith('s'):
                return command_bad_syntax('DRINK', '[THE] <potion name>'),
        item_title = ' '.join(tokens).rstrip('s')
        matching_items_qtys_objs = tuple(filter(lambda argl: argl[1].title == item_title,
                                                self.game_state.character.list_items()))
        if not len(matching_items_qtys_objs):
            return drink_command_item_not_in_inventory(item_title),
        item_qty, item_obj = matching_items_qtys_objs[0]
        if not item_obj.title.endswith(' potion'):
            return drink_command_item_not_drinkable(item_title),
        elif drinking_qty > item_qty:
            return drink_command_tried_to_drink_more_than_possessed(item_title, drinking_qty, item_qty),
        elif item_obj.title == 'health potion':
            hit_points_recovered = item_obj.hit_points_recovered
            healed_amt = self.game_state.character.heal_damage(hit_points_recovered)
            self.game_state.character.drop_item(item_obj)
            return various_commands_underwent_healing_effect(healed_amt, self.game_state.character.hit_points,
                                                             self.game_state.character.hit_point_total),
        else:   # item_obj.title == 'mana potion':
            if self.game_state.character_class not in ('Mage', 'Priest'):
                return drink_command_drank_mana_potion_when_not_a_spellcaster(),
            mana_points_recovered = item_obj.mana_points_recovered
            regained_amt = self.game_state.character.regain_mana(mana_points_recovered)
            self.game_state.character.drop_item(item_obj)
            return drink_command_drank_mana_potion(regained_amt, self.game_state.character.mana_points,
                                                   self.game_state.character.mana_point_total),

    def _pick_up_or_drop_preproc(self, command, *tokens):
        if tokens[0] == 'a' or tokens[0] == 'the' or tokens[0].isdigit() or lexical_number_in_1_99_re.match(tokens[0]):
            if len(tokens) == 1:
                return command_bad_syntax(command.upper(), '<item name>', '<number> <item name>'),
            item_title = ' '.join(tokens[1:])
            if tokens[0] == 'a':
                if tokens[-1].endswith('s'):
                    return (drop_command_quantity_unclear(),)
                            if command.lower() == 'drop'
                            else (pick_up_command_quantity_unclear(),)
                item_qty = 1
            elif tokens[0].isdigit():
                item_qty = int(tokens[0])
            elif tokens[0] == 'the':
                if tokens[-1].endswith('s'):
                    item_qty = math.nan
                else:
                    item_qty = 1
            else:  # lexical_number_in_1_99_re.match(tokens[0]) is True
                item_qty = lexical_number_to_digits(tokens[0])
            if item_qty == 1 and item_title.endswith('s'):
                return pick_up_command_quantity_unclear(),
        else:
            item_title = ' '.join(tokens)
            if item_title.endswith('s'):
                item_qty = math.nan
            else:
                item_qty = 1
        item_title = item_title.rstrip('s')
        return item_qty, item_title

    def drop_command(self, *tokens):
        result = self._pick_up_or_drop_preproc('DROP', *tokens)
        if len(result) == 1 and isinstance(result[0], game_state_message):
            return result
        else:
            drop_amount, item_title = result
        if self.game_state.rooms_state.cursor.items_here is not None:
            items_here = tuple(self.game_state.rooms_state.cursor.items_here.values())
        else:
            items_here = ()
        items_had = tuple(self.game_state.character.list_items())
        item_here_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_here))
        items_had_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_had))
        if not len(items_had_pair):
            return drop_command_trying_to_drop_item_you_dont_have(item_title, drop_amount),
        (item_had_qty, item_obj), = items_had_pair
        if drop_amount is math.nan:
            drop_amount = item_had_qty
        amount_already_here = item_here_pair[0][0] if len(item_here_pair) else 0
        if drop_amount > item_had_qty:
            return drop_command_trying_to_drop_more_than_you_have(item_title, drop_amount, item_had_qty),
        else:
            self.game_state.character.drop_item(item_obj, qty=drop_amount)
            if self.game_state.rooms_state.cursor.items_here is None:
                self.game_state.rooms_state.cursor.items_here = items_multi_state()
            self.game_state.rooms_state.cursor.items_here.set(item_obj.internal_name,
                                                              amount_already_here + drop_amount, item_obj)
            amount_had_now = item_had_qty - drop_amount
            return drop_command_dropped_item(item_title, drop_amount,
                                             amount_already_here + drop_amount, amount_had_now),

    def equip_command(self, *tokens):
        if not tokens:
            return command_bad_syntax('EQUIP', '<armor name>', '<shield name>', '<wand name>', '<weapon name>'),
        item_title = ' '.join(tokens)
        matching_item_tuple = tuple(item_obj for _, item_obj in self.game_state.character.list_items()
                                             if item_obj.title == item_title)
        if not len(matching_item_tuple):
            return equip_command_no_such_item_in_inventory(item_title),
        item_obj, = matching_item_tuple[0:1]
        can_use_attr = self.game_state.character_class.lower() + '_can_use'
        if not getattr(item_obj, can_use_attr):
            return equip_command_class_cant_use_item(self.game_state.character_class, item_title, item_obj.item_type),
        retval = tuple()
        if item_obj.item_type == 'armor' and self.game_state.character.armor_equipped:
            old_equipped_obj = self.game_state.character.armor_equipped
            retval = equip_or_unequip_command_item_unequipped(old_equipped_obj.title, old_equipped_obj.item_type,
                                                              self.game_state.character.armor_class, 'armor class'),
        elif item_obj.item_type == 'shield' and self.game_state.character.shield_equipped:
            old_equipped_obj = self.game_state.character.shield_equipped
            retval = equip_or_unequip_command_item_unequipped(old_equipped_obj.title, old_equipped_obj.item_type,
                                                              self.game_state.character.armor_class, 'armor class'),
        elif item_obj.item_type == 'wand' and self.game_state.character.wand_equipped:
            old_equipped_obj = self.game_state.character.wand_equipped
            retval = equip_or_unequip_command_item_unequipped(old_equipped_obj.title, old_equipped_obj.item_type,
                                                              change_text="You now can't attack."),
        elif item_obj.item_type == 'weapon' and self.game_state.character.weapon_equipped:
            old_equipped_obj = self.game_state.character.weapon_equipped
            retval = equip_or_unequip_command_item_unequipped(old_equipped_obj.title, old_equipped_obj.item_type,
                                                              change_text="You now can't attack."),
        if item_obj.item_type == 'armor':
            self.game_state.character.equip_armor(item_obj)
            return retval + (equip_command_item_equipped(item_obj.title, 'armor',
                                                         self.game_state.character.armor_class, 'armor class'),)
        elif item_obj.item_type == 'shield':
            self.game_state.character.equip_shield(item_obj)
            return retval + (equip_command_item_equipped(item_obj.title, 'shield',
                                                         self.game_state.character.armor_class, 'armor class'),)
        elif item_obj.item_type == 'wand':
            self.game_state.character.equip_wand(item_obj)
            return retval + (equip_command_item_equipped(item_obj.title, 'wand',
                                                         self.game_state.character.attack_bonus, 'attack bonus',
                                                         self.game_state.character.damage_roll, 'damage'),)
        else:
            self.game_state.character.equip_weapon(item_obj)
            return retval + (equip_command_item_equipped(item_obj.title, 'weapon',
                                                         self.game_state.character.attack_bonus, 'attack bonus',
                                                         self.game_state.character.damage_roll, 'damage'),)

    def inventory_command(self, *tokens):
        if len(tokens):
            return command_bad_syntax('INVENTORY', ''),
        inventory_contents = sorted(self.game_state.character.list_items(), key=lambda argl: argl[1].title)
        return inventory_command_display_inventory(inventory_contents),

    def leave_command(self, *tokens):
        if (not len(tokens) or len(tokens) != 2 or tokens[0] not in ('north', 'east', 'south', 'west')
            or tokens[1] not in ('door', 'doorway', 'exit')):
            return command_bad_syntax('LEAVE', 'USING <compass direction> DOOR', 'USING <compass direction> DOORWAY'),
        compass_dir = tokens[0]
        portal_type = tokens[1]
        door_attr = f'{compass_dir}_door'
        door_obj = getattr(self.game_state.rooms_state.cursor, door_attr, None)
        if door_obj is None:
            return various_commands_door_not_present(compass_dir, portal_type),
        elif door_obj.is_exit:
            return leave_command_left_room(compass_dir, portal_type), leave_command_won_the_game()
        self.game_state.rooms_state.move(**{compass_dir: True})
        return (leave_command_left_room(compass_dir, portal_type),
                various_commands_entered_room(self.game_state.rooms_state.cursor))

    def look_at_command(self, *tokens):
        return self.inspect_command(*tokens)

    def lock_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('LOCK', *tokens)
        if isinstance(result[0], game_state_message):
            return result
        else:
            object_to_lock, = result
        if object_to_lock.is_locked:
            return lock_command_object_is_already_locked(object_to_lock.title),
        else:
            object_to_lock.is_locked = True
            return lock_command_object_has_been_locked(object_to_lock.title),

    def _inspect_item_detail(self, item_obj):
        descr_append_str = ''
        if getattr(item_obj, 'item_type', '') in ('armor', 'shield', 'wand', 'weapon'):
            if item_obj.item_type == 'wand' or item_obj.item_type == 'weapon':
                descr_append_str = (f" Its attack bonus is +{item_obj.attack_bonus} and its damage is "
                                    f"{item_obj.damage}. ")
            else:  # item_type == 'armor' or item_type == 'shield'
                descr_append_str = f" Its armor bonus is +{item_obj.armor_bonus}. "
            can_use_list = []
            for character_class in ("warrior", "thief", "mage", "priest"):
                if getattr(item_obj, f"{character_class}_can_use", False):
                    can_use_list.append(f"{character_class}s" if character_class != 'thief' else 'thieves')
            can_use_list[0] = can_use_list[0].title()
            if len(can_use_list) == 1:
                descr_append_str += f"{can_use_list[0]} can use this."
            elif len(can_use_list) == 2:
                descr_append_str += f"{can_use_list[0]} and {can_use_list[1]} can use this."
            else:
                can_use_joined = ', '.join(can_use_list[:-1])
                descr_append_str += f"{can_use_joined}, and {can_use_list[-1]} can use this."
        elif getattr(item_obj, 'item_type', '') == 'consumable':
            if item_obj.title == 'mana potion':
                descr_append_str = f' It restores {item_obj.mana_points_recovered} mana points.'
            elif item_obj.title == 'health potion':
                descr_append_str = f' It restores {item_obj.hit_points_recovered} hit points.'
        return item_obj.description + descr_append_str

    def inspect_command(self, *tokens):
        if (not tokens or tokens[0] in ('in', 'on') or tokens[-1] in ('in', 'on')
            or (tokens[-1] in ('door', 'doorway') and (len(tokens) != 2
            or tokens[0] not in ('north', 'south', 'east', 'west')))):
            return command_bad_syntax('INSPECT', '<item name>', '<item name> IN <chest name>',
                                      '<item name> IN INVENTORY', '<item name> ON <corpse name>',
                                      '<compass direction> DOOR', '<compass direction> DOORWAY'),
        item_contained = item_in_inventory = item_in_chest = item_on_corpse = False
        if 'in' in tokens or 'on' in tokens:
            item_contained = True
            if 'in' in tokens:
                joinword_index = tokens.index('in')
                if tokens[joinword_index+1:] == ('inventory',):
                    item_in_inventory = True
                else:
                    item_in_chest = True
            else:
                joinword_index = tokens.index('on')
                item_on_corpse = True
            target_title = ' '.join(tokens[:joinword_index])
            location_title = ' '.join(tokens[joinword_index+1:])
        elif tokens[-1] == 'door' or tokens[-1] == 'doorway':
            compass_direction = tokens[0]
            door_attr = f"{compass_direction}_door"
            door_obj = getattr(self.game_state.rooms_state.cursor, door_attr, None)
            if door_obj is None:
                return various_commands_door_not_present(compass_direction),
            else:
                return inspect_command_found_door_or_doorway(compass_direction, door_obj),
        else:
            target_title = ' '.join(tokens)
        creature_here_obj = self.game_state.rooms_state.cursor.creature_here
        container_here_obj = self.game_state.rooms_state.cursor.container_here
        if (item_in_chest and isinstance(container_here_obj, corpse)
            or item_on_corpse and isinstance(container_here_obj, chest)):
            return command_bad_syntax('INSPECT', '<item name>', '<item name> IN <chest name>',
                                      '<item name> IN INVENTORY', '<item name> ON <corpse name>',
                                      '<compass direction> DOOR', '<compass direction> DOORWAY'),
        if creature_here_obj is not None and creature_here_obj.title == target_title.lower():
            return inspect_command_found_creature_here(creature_here_obj.description),
        elif container_here_obj is not None and container_here_obj.title == target_title.lower():
            return inspect_command_found_container_here(container_here_obj),
        elif item_contained:
            if item_in_inventory:
                for item_qty, item_obj in self.game_state.character.list_items():
                    if item_obj.title != target_title:
                        continue
                    return inspect_command_found_item_or_items_here(self._inspect_item_detail(item_obj), item_qty),
                return inspect_command_found_nothing(target_title, 'inventory', 'inventory')
            else:
                if container_here_obj is None or container_here_obj.title != location_title:
                    return various_commands_container_not_found(location_title),
                elif container_here_obj is not None and container_here_obj.title == location_title:
                    for item_qty, item_obj in container_here_obj.values():
                        if item_obj.title != target_title:
                            continue
                        return inspect_command_found_item_or_items_here(self._inspect_item_detail(item_obj), item_qty),
                    return inspect_command_found_nothing(target_title, location_title,
                                                         'chest' if item_in_chest else 'corpse'),
                else:
                    return various_commands_container_not_found(location_title),
        else:
            for item_name, (item_qty, item_obj) in self.game_state.rooms_state.cursor.items_here.items():
                if item_obj.title != target_title:
                    continue
                return inspect_command_found_item_or_items_here(self._inspect_item_detail(item_obj), item_qty),
            return inspect_command_found_nothing(target_title),

    def open_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('OPEN', *tokens)
        if isinstance(result[0], game_state_message):
            return result
        else:
            object_to_open, = result
        if object_to_open.is_locked:
            return open_command_object_is_locked(object_to_open.title),
        elif object_to_open.is_closed:
            object_to_open.is_closed = False
            return open_command_object_has_been_opened(object_to_open.title),
        else:
            return open_command_object_is_already_open(object_to_open.title),

    def pick_lock_command(self, *tokens):
        if self.game_state.character_class != 'Thief':
            return command_class_restricted('PICK LOCK', 'thief'),
        if not len(tokens) or tokens[0] != 'on' or tokens == ('on',) or tokens == ('on', 'the',):
            return command_bad_syntax('PICK LOCK', 'ON [THE] <chest name>', 'ON [THE] <door name>'),
        elif tokens[1] == 'the':
            tokens = tokens[2:]
        else:
            tokens = tokens[1:]
        target_title = ' '.join(tokens)
        container_obj = self.game_state.rooms_state.cursor.container_here
        door_objs = []
        for compass_dir in ('north', 'east', 'south', 'west'):
            door_obj = getattr(self.game_state.rooms_state.cursor, f'{compass_dir}_door', None)
            if door_obj is None:
                continue
            door_objs.append(door_obj)
        if container_obj is not None and container_obj.title == target_title:
            if not getattr(container_obj, 'is_locked', False):
                return pick_lock_command_target_not_locked(target_title),
            else:
                container_obj.is_locked = False
                return pick_lock_command_target_has_been_unlocked(target_title),
        elif target_title.endswith('door'):
            door_obj_match = tuple(filter(lambda door_obj: door_obj.title == target_title, door_objs))
            if not door_obj_match:
                return pick_lock_command_target_not_found(target_title),
            else:
                door_obj, = door_obj_match[0:1]
                if not door_obj.is_locked:
                    return pick_lock_command_target_not_locked(target_title),
                else:
                    door_obj.is_locked = False
                    return pick_lock_command_target_has_been_unlocked(target_title),
        else:
            return pick_lock_command_target_cant_be_unlocked_or_not_found(target_title),

    def pick_up_command(self, *tokens):
        result = self._pick_up_or_drop_preproc('PICK UP', *tokens)
        if len(result) == 1 and isinstance(result[0], game_state_message):
            return result
        else:
            pick_up_amount, item_title = result
        if self.game_state.rooms_state.cursor.items_here is not None:
            items_here = tuple(self.game_state.rooms_state.cursor.items_here.values())
        else:
            return pick_up_command_item_not_found(item_title, pick_up_amount),
        items_had = tuple(self.game_state.character.list_items())
        item_here_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_here))
        items_had_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_had))
        if not len(item_here_pair):
            items_here_qtys_titles = tuple((item_qty, item_obj.title) for item_qty, item_obj in items_here)
            return pick_up_command_item_not_found(item_title, pick_up_amount, *items_here_qtys_titles),
        (item_qty, item_obj), = item_here_pair
        if pick_up_amount is math.nan:
            pick_up_amount = item_qty
        amount_already_had = items_had_pair[0][0] if len(items_had_pair) else 0
        if item_qty < pick_up_amount:
            return pick_up_command_trying_to_pick_up_more_than_is_present(item_title, pick_up_amount, item_qty),
        else:
            self.game_state.character.pick_up_item(item_obj, qty=pick_up_amount)
            if item_qty == pick_up_amount:
                self.game_state.rooms_state.cursor.items_here.delete(item_obj.internal_name)
            else:
                self.game_state.rooms_state.cursor.items_here.set(item_obj.internal_name,
                                                                  item_qty - pick_up_amount, item_obj)
            amount_had_now = amount_already_had + pick_up_amount
            return pick_up_command_item_picked_up(item_title, pick_up_amount, amount_had_now),

    # Both PUT and TAKE have the same preprocessing challenges, so I refactored their logic into a shared private
    # preprocessing method.

    def _put_or_take_preproc(self, command, joinword, *tokens):
        container_obj = self.game_state.rooms_state.cursor.container_here

        if command.lower() == 'put':
            if container_obj.container_type == 'chest':
                joinword = 'IN'
            else:
                joinword = 'ON'

        command, joinword = command.lower(), joinword.lower()
        tokens = list(tokens)

        # Whatever the user wrote, it doesn't contain the joinword, which is a required token.
        if joinword not in tokens or tokens.index(joinword) == 0 or tokens.index(joinword) == len(tokens) - 1:
            if command == 'take':
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),
            else:
                return command_bad_syntax(command.upper(), '<item name> IN <chest name>',
                                                           '<number> <item name> IN <chest name>',
                                                           '<item name> ON <corpse name>',
                                                           '<number> <item name> ON <corpse name>'),

        # The first token is a digital number, great.
        if digit_re.match(tokens[0]):
            amount = int(tokens.pop(0))

        # The first token is a lexical number, so I convert it.
        elif lexical_number_in_1_99_re.match(tokens[0]):
            amount = lexical_number_to_digits(tokens.pop(0))

        # The first token is an indirect article, which would mean '1'.
        elif tokens[0] == 'a':
            joinword_index = tokens.index(joinword)

            # The term before the joinword, which is the item title, is plural. The sentence is ungrammatical, so I
            # return an error.
            if tokens[joinword_index - 1].endswith('s'):
                return (take_command_quantity_unclear(),) if command == 'take' else (put_command_quantity_unclear(),)
            amount = 1
            del tokens[0]

        # No other indication was given, so the amount will have to be determined later; either the total amount found
        # in the container (for TAKE) or the total amount in the inventory (for PUT)
        else:
            amount = math.nan

        # I form up the item_title and container_title, but I'm not done testing them.
        joinword_index = tokens.index(joinword)
        item_title = ' '.join(tokens[0:joinword_index])
        container_title = ' '.join(tokens[joinword_index+1:])

        # The item_title begins with a direct article.
        if item_title.startswith('the ') or item_title.startswith('the') and len(item_title) == 3:

            # The title is of the form, 'the gold coins', which means the amount intended is the total amount
            # available-- either the total amount in the container (for TAKE) or the total amount in the character's
            # inventory (for PUT). That will be dertermined later, so NaN is used as a signal value to be replaced when
            # possible.
            if item_title.endswith('s'):
                amount = math.nan
                item_title = item_title[:-1]
            item_title = item_title[4:]

            # `item_title` is *just* 'the'. The sentence is ungrammatical, so I return a syntax error.
            if not item_title:
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

        if item_title.endswith('s'):
            if amount == 1:

                # The `item_title` ends in a plural, but an amount > 1 was specified. That's an ungrammatical sentence,
                # so I return a syntax error.
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

            # The title is plural and `amount` is > 1. I strip the pluralizing 's' off to get the correct item title.
            item_title = item_title[:-1]

        if container_title.startswith('the ') or container_title.startswith('the') and len(container_title) == 3:

            # The container term begins with a direct article and ends with a pluralizing 's'. That's invalid, no
            # container in the dungeon is found in grouping of more than one, so I return a syntax error.
            if container_title.endswith('s'):
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

            container_title = container_title[4:]
            if not container_title:

                # Improbably, the item title is *just* 'the'. That's an ungrammatical sentence, so I return a syntax
                # error.
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

        if container_obj is None:

            # There is no container in this room, so no TAKE command can be correct. I return an error.
            return various_commands_container_not_found(container_title),  # tested
        elif not container_title == container_obj.title:

            # The container name specified doesn't match the name of the container in this room, so I return an error.
            return various_commands_container_not_found(container_title, container_obj.title),  # tested

        elif container_obj.is_closed:

            # The container can't be PUT IN to or TAKEn from because it is closed.
            return various_commands_container_is_closed(container_obj.title),

        return amount, item_title, container_title, container_obj

    def put_command(self, *tokens):
        results = self._put_or_take_preproc('PUT', 'IN|ON', *tokens)

        # The workhorse private method returns either a game_state_message subclass object (see
        # adventuregame.game_state_messages) or a tuple of amount to put, parsed title of item, parsed title of
        # container, and the container object (as a matter of convenience, it's needed by the private method & why fetch
        # it twice).
        if len(results) == 1 and isinstance(results[0], game_state_message):
            return results
        else:
            # len(results) == 4 and isinstance(results[0], int) and isinstance(results[1], str)
            #     and isinstance(results[2], str) and isinstance(results[3], container)
            put_amount, item_title, container_title, container_obj = results

        # I read off the player's inventory and filter it for a (qty,obj) pair whose title matches the supplied item
        # name.
        inventory_list = tuple(filter(lambda pair: pair[1].title == item_title, self.game_state.character.list_items()))

        if len(inventory_list) == 1:

            # The player has the item in their inventory, so I save the qty they possess and the item object.
            amount_possessed, item_obj = inventory_list[0]
        else:
            return put_command_item_not_in_inventory(item_title, put_amount),
        if container_obj.contains(item_obj.internal_name):
            amount_in_container, _ = container_obj.get(item_obj.internal_name)
        else:
            amount_in_container = 0
        if put_amount > amount_possessed:
            return put_command_trying_to_put_more_than_you_have(item_title, amount_possessed),
        elif put_amount is math.nan:
            put_amount = amount_possessed
        else:
            amount_possessed -= put_amount
        self.game_state.character.drop_item(item_obj, qty=put_amount)
        container_obj.set(item_obj.internal_name, amount_in_container + put_amount, item_obj)
        return put_command_amount_put(item_title, container_title, container_obj.container_type, put_amount,
                                      amount_possessed),

    def quit_command(self, *tokens):
        if len(tokens):
            return command_bad_syntax('QUIT', ''),
        self.game_state.game_has_ended = True
        return quit_command_have_quit_the_game(),

    def reroll_command(self, *tokens):
        if len(tokens):
            return command_bad_syntax('REROLL', ''),
        character_name = getattr(self.game_state, 'character_name', None)
        character_class = getattr(self.game_state, 'character_class', None)
        if not character_name or not character_class:
            return reroll_command_name_or_class_not_set(character_name, character_class),
        self.game_state.character.ability_scores.roll_stats()
        return set_name_or_class_command_display_rolled_stats(
                   strength=self.game_state.character.strength,
                   dexterity=self.game_state.character.dexterity,
                   constitution=self.game_state.character.constitution,
                   intelligence=self.game_state.character.intelligence,
                   wisdom=self.game_state.character.wisdom,
                   charisma=self.game_state.character.charisma),

    # Concerning both set_name_command() and set_class_command() below it:
    #
    # The character object isn't instanced in game_state.__init__ because it depends on name and class choice. Its
    # character_name and character_class setters have a side effect where if both have been set the character object is
    # instanced automatically. So after valid input is determined, I check for the state of <both character_name and
    # character_class are now non-None>; if so, the character object was just instanced. That means the ability scores
    # were rolled and assigned. The player may choose to reroll, so the return tuple includes a prompt to do so.

    def begin_game_command(self, *tokens):
        if len(tokens):
            return command_bad_syntax('BEGIN GAME', ''),
        character_name = getattr(self.game_state, 'character_name', None)
        character_class = getattr(self.game_state, 'character_class', None)
        if not character_name or not character_class:
            return begin_game_command_name_or_class_not_set(character_name, character_class),
        self.game_state.game_has_begun = True
        return begin_game_command_game_begins(), various_commands_entered_room(self.game_state.rooms_state.cursor)

    def set_name_command(self, *tokens):
        if len(tokens) == 0:
            return command_bad_syntax('SET NAME', '<character name>'),
        name_parts_tests = list(map(bool, map(self.valid_name_re.match, tokens)))
        name_was_none = self.game_state.character_name is None
        if False in name_parts_tests:
            failing_parts = list()
            offset = 0
            for _ in range(0, name_parts_tests.count(False)):
                failing_part_index = name_parts_tests.index(False, offset)
                failing_parts.append(tokens[failing_part_index])
                offset = failing_part_index + 1
            return tuple(map(set_name_command_invalid_part, failing_parts))
        else:
            name_str = ' '.join(tokens)
            self.game_state.character_name = ' '.join(tokens)
            if self.game_state.character_class is not None and name_was_none:
                return (set_name_command_name_set(name_str), set_name_or_class_command_display_rolled_stats(
                            strength=self.game_state.character.strength,
                            dexterity=self.game_state.character.dexterity,
                            constitution=self.game_state.character.constitution,
                            intelligence=self.game_state.character.intelligence,
                            wisdom=self.game_state.character.wisdom,
                            charisma=self.game_state.character.charisma
                ))
            else:
                return set_name_command_name_set(self.game_state.character_name),

    def set_class_command(self, *tokens):
        if len(tokens) == 0 or len(tokens) > 1:
            return command_bad_syntax('SET CLASS', '<Warrior, Thief, Mage or Priest>'),
        elif not self.valid_class_re.match(tokens[0]):
            return set_class_command_invalid_class(tokens[0]),
        class_str = tokens[0]
        class_was_none = self.game_state.character_class is None
        self.game_state.character_class = class_str
        if self.game_state.character_name is not None and class_was_none:
            return (set_class_command_class_set(class_str),
                    set_name_or_class_command_display_rolled_stats(
                        strength=self.game_state.character.strength,
                        dexterity=self.game_state.character.dexterity,
                        constitution=self.game_state.character.constitution,
                        intelligence=self.game_state.character.intelligence,
                        wisdom=self.game_state.character.wisdom,
                        charisma=self.game_state.character.charisma
            ))
        else:
            return set_class_command_class_set(class_str),

    # This is a very hairy method on account of how much natural language processing it has to do to account for all the
    # permutations on how a user writes TAKE item FROM container.

    def status_command(self, *tokens):
        if len(tokens):
            return command_bad_syntax('STATUS', ''),
        character_obj = self.game_state.character
        output_args = dict()
        output_args['hit_points'] = character_obj.hit_points
        output_args['hit_point_total'] = character_obj.hit_point_total
        if character_obj.character_class in ('Mage', 'Priest'):
            output_args['mana_points'] = character_obj.mana_points
            output_args['mana_point_total'] = character_obj.mana_point_total
        else:
            output_args['mana_points'] = None
            output_args['mana_point_total'] = None
        output_args['armor_class'] = character_obj.armor_class
        if character_obj.weapon_equipped or (character_obj.character_class == "Mage" and character_obj.wand_equipped):
            output_args['attack_bonus'] = character_obj.attack_bonus
            output_args['damage'] = character_obj.damage_roll
        else:
            output_args['attack_bonus'] = 0
            output_args['damage'] = ''
        output_args['armor'] = character_obj.armor.title if character_obj.armor_equipped else None
        output_args['shield'] = character_obj.shield.title if character_obj.shield_equipped else None
        output_args['wand'] = character_obj.wand.title if character_obj.wand_equipped else None
        output_args['weapon'] = character_obj.weapon.title if character_obj.weapon_equipped else None
        output_args['is_mage'] = character_obj.character_class == 'Mage'
        return status_command_output(**output_args),

    def take_command(self, *tokens):
        results = self._put_or_take_preproc('TAKE', 'FROM', *tokens)

        # The workhorse private method returns either a game_state_message subclass object (see
        # adventuregame.game_state_messages) or a tuple of amount to take, parsed title of item, parsed title of
        # container, and the container object (as a matter of convenience, it's needed by the private method & why fetch
        # it twice).
        if len(results) == 1 and isinstance(results[0], game_state_message):
            return results
        else:
            # len(results) == 4 and isinstance(results[0], int) and isinstance(results[1], str)
            #     and isinstance(results[2], str) and isinstance(results[3], container)
            take_amount, item_title, container_title, container_obj = results

        # The following loop iterates over all the items in the container. I use a while loop so it's possible for the
        # search to fall off the end of the loop. If that code is reached, the specified item isn't in this container.
        container_here_contents = list(container_obj.items())
        index = 0
        while index < len(container_here_contents):
            item_internal_name, (item_qty, item_obj) = container_here_contents[index]

            # This isn't the item specified.
            if item_obj.title != item_title:
                index += 1
                continue

            if take_amount is math.nan:
                # This *is* the item, but the command didn't specify the quantity, so I set `take_amount` to the
                # quantity in the container.
                take_amount = item_qty

            if take_amount > item_qty:

                # The amount specified is more than how much is in the container, so I return an error.
                return take_command_trying_to_take_more_than_is_present(container_title, container_obj.container_type,
                                                                        item_title, take_amount, item_qty),  # tested
            elif take_amount == 1:

                # We have a match. One item is remove from the container and added to the character's inventory; and a
                # success return object is returned.
                container_obj.remove_one(item_internal_name)
                self.game_state.character.pick_up_item(item_obj)
                return take_command_item_or_items_taken(container_title, item_title, take_amount),
            else:

                # We have a match.
                if take_amount == item_qty:

                    # The amount specified is how much is here, so I delete the item from the container.
                    container_obj.delete(item_internal_name)
                else:

                    # There's more in the container than was specified, so I set the amount in the container to the
                    # amount that was there minus the amount being taken.
                    container_obj.set(item_internal_name, item_qty - take_amount, item_obj)

                # The character's inventory is updated with the items taken, and a success object is returned.
                self.game_state.character.pick_up_item(item_obj, qty=take_amount)
                return take_command_item_or_items_taken(container_title, item_title, take_amount),

            # The loop didn't find the item on this path, so I increment the index and try again.
            index += 1

        # The loop completed without finding the item, so it isn't present in the container. I return an error.
        return take_command_item_not_found_in_container(container_title, take_amount, container_obj.container_type,
                                                        item_title),  # tested

    def _lock_unlock_open_or_close_preproc(self, command, *tokens):
        if not len(tokens):
            return command_bad_syntax(command.upper(), '<door name>', '<chest name>'),
        target_title = ' '.join(tokens)
        container_obj = self.game_state.rooms_state.cursor.container_here
        if lock_unlock_mode := command.lower().endswith('lock'):
            key_objs = [item_obj for _, item_obj in self.game_state.character.list_items()
                        if item_obj.title.endswith(' key')]
        if container_obj is not None and isinstance(container_obj, chest) and container_obj.title == target_title:
            if lock_unlock_mode and (not len(key_objs) or not any(key_obj.title == 'chest key'
                                                                  for key_obj in key_objs)):
                if command.lower() == 'unlock':
                    return unlock_command_dont_possess_correct_key(container_obj.title, 'chest key'),
                else:
                    return lock_command_dont_possess_correct_key(container_obj.title, 'chest key'),
            else:
                return container_obj,
        for door_attr in ('north_door', 'east_door', 'south_door', 'west_door'):
            if getattr(self.game_state.rooms_state.cursor, door_attr, None) is None:
                continue
            door_obj = getattr(self.game_state.rooms_state.cursor, door_attr)
            if isinstance(door_obj, doorway):
                continue
            if door_obj.title == target_title:
                if lock_unlock_mode and (not key_objs or not any(key_obj.title == 'door key' for key_obj in key_objs)):
                    return ((unlock_command_dont_possess_correct_key(door_obj.title, 'door key'),)
                                 if command.lower() == 'unlock'
                                 else (lock_command_dont_possess_correct_key(door_obj.title, 'door key'),))
                else:
                    return door_obj,

        # Control flow fell off the end of the loop, which means none of the doors in the room had a title matching the
        # object title specified in the command, and if there's a chest in the room the chest didn't match either. So
        # whatever the user wanted to lock/unlock, it's not here.
        if command.lower() == 'unlock':
            return unlock_command_object_to_unlock_not_here(target_title),
        elif command.lower() == 'lock':
            return lock_command_object_to_lock_not_here(target_title),
        elif command.lower() == 'open':
            return open_command_object_to_open_not_here(target_title),
        else:
            return close_command_object_to_close_not_here(target_title),

    def unequip_command(self, *tokens):
        if not tokens:
            return command_bad_syntax('UNEQUIP', '<armor name>', '<shield name>', '<wand name>', '<weapon name>'),
        item_title = ' '.join(tokens)
        matching_item_tuple = tuple(item_obj for _, item_obj in self.game_state.character.list_items()
                                    if item_obj.title == item_title)
        if not len(matching_item_tuple):
            matching_item_tuple = tuple(item_obj for item_obj in self.game_state.items_state.values()
                                        if item_obj.title == item_title)
            if matching_item_tuple:
                item_obj, = matching_item_tuple[0:1]
                return unequip_command_item_not_equipped(item_obj.title, item_obj.item_type),
            else:
                return unequip_command_item_not_equipped(item_title),
        item_obj, = matching_item_tuple[0:1]
        if item_obj.item_type == 'armor':
            if self.game_state.character.armor_equipped is not None:
                if self.game_state.character.armor_equipped.title == item_title:
                    self.game_state.character.unequip_armor()
                    return equip_or_unequip_command_item_unequipped(item_title, 'armor',
                                                                    self.game_state.character.armor_class,
                                                                    'armor class'),
                else:
                    return unequip_command_item_not_equipped(item_title, 'armor',
                                                             self.game_state.character.armor_equipped.title),
            else:
                return unequip_command_item_not_equipped(item_title, 'armor'),
        elif item_obj.item_type == 'shield':
            if self.game_state.character.shield_equipped is not None:
                if self.game_state.character.shield_equipped.title == item_title:
                    self.game_state.character.unequip_shield()
                    return equip_or_unequip_command_item_unequipped(item_title, 'shield',
                                                                    self.game_state.character.armor_class,
                                                                    'armor class'),
                else:
                    return unequip_command_item_not_equipped(item_title, 'shield',
                                                             self.game_state.character.shield_equipped.title),
            else:
                return unequip_command_item_not_equipped(item_title, 'shield'),
        elif item_obj.item_type == 'wand':
            if self.game_state.character.wand_equipped is not None:
                if self.game_state.character.wand_equipped.title == item_title:
                    self.game_state.character.unequip_wand()
                    return equip_or_unequip_command_item_unequipped(item_title, 'wand',
                                                                    change_text="You now can't attack."),
                else:
                    return unequip_command_item_not_equipped(item_title, 'wand'),
            else:
                return unequip_command_item_not_equipped(item_title, 'wand'),
        elif item_obj.item_type == 'weapon':
            if self.game_state.character.weapon_equipped is not None:
                if self.game_state.character.weapon_equipped.title == item_title:
                    self.game_state.character.unequip_weapon()
                    return equip_or_unequip_command_item_unequipped(item_title, 'weapon',
                                                                    change_text="You now can't attack."),
                else:
                    return unequip_command_item_not_equipped(item_obj.title, 'weapon'),
            else:
                return unequip_command_item_not_equipped(item_obj.title, 'weapon'),

    def unlock_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('UNLOCK', *tokens)
        if isinstance(result[0], game_state_message):
            return result
        else:
            object_to_unlock, = result
        if object_to_unlock.is_locked is False:
            return unlock_command_object_is_already_unlocked(object_to_unlock.title),
        else:
            object_to_unlock.is_locked = False
            return unlock_command_object_has_been_unlocked(object_to_unlock.title),
