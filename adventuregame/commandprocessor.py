#!/usr/bin/python

import math
import re

from .commandreturns import *
from .gameelements import *
from .utility import *

__name__ = 'adventuregame.commandprocessor'


class command_processor(object):
    __slots__ = 'game_state', 'dispatch_table'

    # All return values from *_command methods in this class are
    # tuples. Every *_command method returns one or more *_command_*
    # objects, reflecting a sequence of changes in game state. (For
    # example, an ATTACK action that doesn't kill the foe will prompt
    # the foe to attack. The foe's attack might lead to the character's
    # death. So the return value might be a `attack_command_attack_hit`
    # object, a `be_attacked_by_command_attacked_and_hit` object, and a
    # `be_attacked_by_command_character_death` object, each bearing a message in its
    # `message` property. The code which handles the result of the
    # ATTACK action knows it's receiving a tuple and will iterate through the
    # result objects and display each one's message to the player in turn.

    valid_name_re = re.compile('^[A-Z][a-z]+$')

    valid_class_re = re.compile('^(Warrior|Thief|Mage|Priest)$')

    def __init__(self, game_state_obj):
        self.dispatch_table = {
                                  method_name.rsplit('_', maxsplit=1)[0]: getattr(self, method_name) for method_name in
                                  filter(lambda name: name.endswith('_command'), dir(command_processor))
                              }
        self.game_state = game_state_obj

    def process(self, natural_language_str):
        tokens = natural_language_str.strip().split()
        command = tokens.pop(0).lower()
        if command == 'look' and len(tokens) and tokens[0].lower() == 'at':
            command = command + '_' + tokens.pop(0).lower()
        elif command == 'set' and len(tokens) and (tokens[0].lower() == 'name' or tokens[0].lower() == 'class'):
            command = command + '_' + tokens.pop(0).lower()
            if len(tokens) and tokens[0] == 'to':
                tokens.pop(0)
        elif command == "i'm" and len(tokens) and tokens[0].lower() == 'satisfied':
            command = tokens.pop(0).lower()
        elif command == 'pick' and len(tokens) and tokens[0].lower() == 'up':
            command += '_' + tokens.pop(0).lower()
        if command not in ('set_name', 'set_class'):
            tokens = tuple(map(str.lower, tokens))
        if command not in self.dispatch_table:
            return command_not_recognized(command),
        return self.dispatch_table[command](*tokens)

    def attack_command(self, *tokens):
        creature_title_token = ' '.join(tokens)
        if not self.game_state.rooms_state.cursor.creature_here:
            return attack_command_opponent_not_found(creature_title_token),
        elif self.game_state.rooms_state.cursor.creature_here.title.lower() != creature_title_token:
            return attack_command_opponent_not_found(creature_title_token, self.game_state.rooms_state.cursor.creature_here.title),
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
                return attack_command_attack_hit(creature_obj.title, damage_result, True), attack_command_foe_death(creature_obj.title),
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
                return be_attacked_by_command_attacked_and_hit(creature_obj.title, damage_done, 0), be_attacked_by_command_character_death(),
            else:
                return be_attacked_by_command_attacked_and_hit(creature_obj.title, damage_done, self.game_state.character.hit_points),

    def close_command(self):
        pass

    def drop_command(self, *tokens):
        result = self._parse_item_qty_item_title_natlang('DROP', *tokens)
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
            self.game_state.rooms_state.cursor.items_here.set(item_obj.internal_name, amount_already_here + drop_amount, item_obj)
            amount_had_now = item_had_qty - drop_amount
            return drop_command_dropped_item(item_title, drop_amount, amount_already_here + drop_amount, amount_had_now),

    def equip_command(self):
        pass

    def look_at_command(self, *tokens):
        return self.inspect_command(*tokens)

    def inspect_command(self, *tokens):
        entity_title_token = ' '.join(tokens)
        creature_here_obj = self.game_state.rooms_state.cursor.creature_here
        container_here_obj = self.game_state.rooms_state.cursor.container_here
        if creature_here_obj is not None and creature_here_obj.title == entity_title_token.lower():
            return inspect_command_found_creature_here(creature_here_obj.description),
        elif container_here_obj is not None and container_here_obj.title == entity_title_token.lower():
            return inspect_command_found_container_here(container_here_obj),
        else:
            for item_name, (item_qty, item_obj) in self.game_state.rooms_state.cursor.items_here.items():
                if item_obj.title == entity_title_token:
                    return inspect_command_found_item_or_items_here(item_obj.description, item_qty),
            return inspect_command_found_nothing(entity_title_token),

    def move_command(self):
        pass

    def open_command(self):
        pass

    def _parse_item_qty_item_title_natlang(self, command, *tokens):
        if tokens[0] == 'a' or tokens[0] == 'the' or tokens[0].isdigit() or lexical_number_in_1_99_re.match(tokens[0]):
            if len(tokens) == 1:
                return command_bad_syntax(command.upper(), f'<item name>', f'<number> <item name>'),
            item_title = ' '.join(tokens[1:])
            if tokens[0] == 'a':
                if tokens[-1].endswith('s'):
                    return (drop_command_quantity_unclear(),) if command.lower() == 'drop' else (pick_up_command_quantity_unclear(),)
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
            item_title = ' '.join(tokens[1:])
            if item_title.endswith('s'):
                item_qty = math.nan
            else:
                item_qty = 1
        item_title = item_title.rstrip('s')
        return item_qty, item_title

    def pick_up_command(self, *tokens):
        result = self._parse_item_qty_item_title_natlang('PICK UP', *tokens)
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
                self.game_state.rooms_state.cursor.items_here.set(item_obj.internal_name, item_qty - pick_up_amount, item_obj)
            amount_had_now = amount_already_had + pick_up_amount
            return pick_up_command_item_picked_up(item_title, pick_up_amount, amount_had_now),

    def satisfied_command(self, *tokens):
        if len(tokens):
            return command_bad_syntax('SATISFIED', f''),
        self.game_state.game_has_begun = True
        return satisfied_command_game_begins(),

    def reroll_command(self, *tokens):
        if len(tokens):
            return command_bad_syntax('REROLL', f''),
        self.game_state.character.ability_scores.roll_stats()
        return set_name_or_class_command_display_rolled_stats(
                   strength_int=self.game_state.character.strength,
                   dexterity_int=self.game_state.character.dexterity,
                   constitution_int=self.game_state.character.constitution,
                   intelligence_int=self.game_state.character.intelligence,
                   wisdom_int=self.game_state.character.wisdom,
                   charisma_int=self.game_state.character.charisma),
        

    # Concerning both set_name_command() and set_class_command() below it:
    #
    # The character object isn't instanced in game_state.__init__ because it
    # depends on name and class choice. Its character_name and character_class
    # setters have a side effect where if both have been set the character
    # object is instanced automatically. So after valid input is determined, I
    # check for the state of <both character_name and character_class are now
    # non-None>; if so, the character object was just instanced. That means
    # the ability scores were rolled and assigned. The player may choose to
    # reroll, so the return tuple includes a prompt to do so.

    def set_name_command(self, *tokens):
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
                            strength_int=self.game_state.character.strength,
                            dexterity_int=self.game_state.character.dexterity,
                            constitution_int=self.game_state.character.constitution,
                            intelligence_int=self.game_state.character.intelligence,
                            wisdom_int=self.game_state.character.wisdom,
                            charisma_int=self.game_state.character.charisma
                ))
            else:
                return set_name_command_name_set(self.game_state.character_name),

    def set_class_command(self, *tokens):
        if len(tokens) > 1:
            return command_too_many_words(1),
        elif not self.valid_class_re.match(tokens[0]):
            return set_class_command_invalid_class(tokens[0]),
        class_str = tokens[0]
        class_was_none = self.game_state.character_class is None
        self.game_state.character_class = class_str
        if self.game_state.character_name is not None and class_was_none:
            return (set_class_command_class_set(class_str),
                    set_name_or_class_command_display_rolled_stats(
                        strength_int=self.game_state.character.strength,
                        dexterity_int=self.game_state.character.dexterity,
                        constitution_int=self.game_state.character.constitution,
                        intelligence_int=self.game_state.character.intelligence,
                        wisdom_int=self.game_state.character.wisdom,
                        charisma_int=self.game_state.character.charisma
            ))
        else:
            return set_class_command_class_set(class_str),

    # Both PUT and TAKE have the same preprocessing challenges, so I refactored
    # their logic into a shared private preprocessing method.

    def _parse_item_joinword_container_natlang(self, command, joinword, *tokens):
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
                return command_bad_syntax(command.upper(), f'<item name> IN <chest name>',
                                                           f'<number> <item name> IN <chest name>',
                                                           f'<item name> ON <corpse name>',
                                                           f'<number> <item name> ON <corpse name>'),

        # The first token is a digital number, great.
        if digit_re.match(tokens[0]):
            amount = int(tokens.pop(0))

        # The first token is a lexical number, so I convert it.
        elif lexical_number_in_1_99_re.match(tokens[0]):
            amount = lexical_number_to_digits(tokens.pop(0))

        # The first token is an indirect article, which would mean '1'.
        elif tokens[0] == 'a':
            joinword_index = tokens.index(joinword)

            # The term before the joinword, which is the item title, is
            # plural. The sentence is ungrammatical, so I return an error.
            if tokens[joinword_index - 1].endswith('s'):
                return (take_command_quantity_unclear(),) if command == 'take' else (put_command_quantity_unclear(),)
            amount = 1
            del tokens[0]

        # No other indication was given, so the amount will have to be
        # determined later; either the total amount found in the container
        # (for TAKE) or the total amount in the inventory (for PUT)
        else:
            amount = math.nan

        # I form up the item_title and container_title, but I'm not done testing them.
        joinword_index = tokens.index(joinword)
        item_title = ' '.join(tokens[0:joinword_index])
        container_title = ' '.join(tokens[joinword_index+1:])

        # The item_title begins with a direct article.
        if item_title.startswith('the ') or item_title.startswith('the') and len(item_title) == 3:

            # The title is of the form, 'the gold coins', which means the
            # amount intended is the total amount available-- either the total
            # amount in the container (for TAKE) or the total amount in the
            # character's inventory (for PUT). That will be dertermined later,
            # so NaN is used as a signal value to be replaced when possible.
            if item_title.endswith('s'):
                amount = math.nan
                item_title = item_title[:-1]
            item_title = item_title[4:]

            # `item_title` is *just* 'the'. The sentence is ungrammatical, so
            # I return a syntax error.
            if not item_title:
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

        if item_title.endswith('s'):
            if amount == 1:

                # The `item_title` ends in a plural, but an amount > 1 was
                # specified. That's an ungrammatical sentence, so I return a
                # syntax error.
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

            # The title is plural and `amount` is > 1. I strip the
            # pluralizing 's' off to get the correct item title.
            item_title = item_title[:-1]

        if container_title.startswith('the ') or container_title.startswith('the') and len(container_title) == 3:

            # The container term begins with a direct article and ends with a
            # pluralizing 's'. That's invalid, no container in the dungeon is
            # found in grouping of more than one, so I return a syntax error.
            if container_title.endswith('s'):
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

            container_title = container_title[4:]
            if not container_title:

                # Improbably, the item title is *just* 'the'. That's an
                # ungrammatical sentence, so I return a syntax error.
                return command_bad_syntax(command.upper(), f'<item name> {joinword.upper()} <container name>',
                                                           f'<number> <item name> {joinword.upper()} <container name>'),

        if container_obj is None:

            # There is no container in this room, so no TAKE command can be
            # correct. I return an error.
            return various_commands_container_not_found(container_title),  # tested
        elif not container_title == container_obj.title:

            # The container name specified doesn't match the name of the
            # container in this room, so I return an error.
            return various_commands_container_not_found(container_title, container_obj.title),  # tested

        return amount, item_title, container_title, container_obj

    # This is a very hairy method on account of how much natural language
    # processing it has to do to account for all the permutations on how
    # a user writes TAKE item FROM container.

    def take_command(self, *tokens):
        results = self._parse_item_joinword_container_natlang('TAKE', 'FROM', *tokens)

        # The workhorse private method returns either a game_state_message
        # subclass object (see adventuregame.commandreturns) or a tuple of
        # amount to take, parsed title of item, parsed title of container, and
        # the container object (as a matter of convenience, it's needed by the
        # private method & why fetch it twice).
        if len(results) == 1 and isinstance(results[0], game_state_message):
            return results
        else:
            # len(results) == 4 and isinstance(results[0], int) and isinstance(results[1], str)
            #     and isinstance(results[2], str) and isinstance(results[3], container)
            take_amount, item_title, container_title, container_obj = results

        # The following loop iterates over all the items in the container. I
        # use a while loop so it's possible for the search to fall off the end
        # of the loop. If that code is reached, the specified item isn't in
        # this container.
        container_here_contents = list(container_obj.items())
        index = 0
        while index < len(container_here_contents):
            item_internal_name, (item_qty, item_obj) = container_here_contents[index]

            # This isn't the item specified.
            if item_obj.title != item_title:
                index += 1
                continue

            if take_amount is math.nan:
                # This *is* the item, but the command didn't specify the
                # quantity, so I set `take_amount` to the quantity in the
                # container.
                take_amount = item_qty

            if take_amount > item_qty:

                # The amount specified is more than how much is in the
                # container, so I return an error.
                return take_command_trying_to_take_more_than_is_present(container_title, container_obj.container_type, item_title, take_amount, item_qty),  # tested
            elif take_amount == 1:

                # We have a match. One item is remove from the container and
                # added to the character's inventory; and a success return
                # object is returned.
                container_obj.remove_one(item_internal_name)
                self.game_state.character.pick_up_item(item_obj)
                return take_command_item_or_items_taken(container_title, item_title, take_amount),
            else:

                # We have a match.
                if take_amount == item_qty:

                    # The amount specified is how much is here, so I delete
                    # the item from the container.
                    container_obj.delete(item_internal_name)
                else:

                    # There's more in the container than was specified, so I
                    # set the amount in the container to the amount that was
                    # there minus the amount being taken.
                    container_obj.set(item_internal_name, item_qty - take_amount, item_obj)

                # The character's inventory is updated with the items taken,
                # and a success object is returned.
                self.game_state.character.pick_up_item(item_obj, qty=take_amount)
                return take_command_item_or_items_taken(container_title, item_title, take_amount),

            # The loop didn't find the item on this path, so I increment the
            # index and try again.
            index += 1

        # The loop completed without finding the item, so it isn't present in
        # the container. I return an error.
        return take_command_item_not_found_in_container(container_title, take_amount, container_obj.container_type, item_title),  # tested

    def put_command(self, *tokens):
        results = self._parse_item_joinword_container_natlang('PUT', 'IN|ON', *tokens)

        # The workhorse private method returns either a game_state_message
        # subclass object (see adventuregame.commandreturns) or a tuple of
        # amount to put, parsed title of item, parsed title of container, and
        # the container object (as a matter of convenience, it's needed by the
        # private method & why fetch it twice).
        if len(results) == 1 and isinstance(results[0], game_state_message):
            return results
        else:
            # len(results) == 4 and isinstance(results[0], int) and isinstance(results[1], str)
            #     and isinstance(results[2], str) and isinstance(results[3], container)
            put_amount, item_title, container_title, container_obj = results

        # I read off the player's inventory and filter it for a (qty,obj) pair
        # whose title matches the supplied item name.
        inventory_list = tuple(filter(lambda pair: pair[1].title == item_title, self.game_state.character.list_items()))

        if len(inventory_list) == 1:

            # The player has the item in their inventory, so I save the qty
            # they possess and the item object.
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
        return put_command_amount_put(item_title, container_title, container_obj.container_type, put_amount, amount_possessed),

    def unlock_command(self):
        pass
