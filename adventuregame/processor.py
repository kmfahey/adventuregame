#!/usr/bin/python

import math
import operator
import re

import adventuregame.statemsgs as stmsg
import adventuregame.elements as elem
import adventuregame.utility as util


__name__ = 'adventuregame.commandprocessor'


SPELL_DAMAGE = '3d8+5'

SPELL_MANA_COST = 5

STARTER_GEAR = dict(Warrior=dict(weapon='Longsword', armor='Studded_Leather', shield='Buckler'),
                    Thief=dict(weapon='Rapier', armor='Studded_Leather'),
                    Mage=dict(weapon='Staff'),
                    Priest=dict(weapon='Mace', armor='Studded_Leather', shield='Buckler'))

# \u00A0 is a nonbreaking space. I use it in the syntax examples so that the use of text wrapping in advgame.py
# doesn't break individual syntax examples across lines. The longer syntax examples become difficult to read if
# adventuregame.utility.textwrapper() is able to break syntax examples across lines.

COMMANDS_SYNTAX = {
    'ATTACK': ('<creature\u00A0name>',),
    'BEGIN GAME': ('',),
    'CAST SPELL': ('',),
    'CLOSE': ('<door\u00A0name>', '<chest\u00A0name>'),
    'DRINK': ('[THE]\u00A0<potion\u00A0name>',),
    'DROP': ('<item\u00A0name>', '<number>\u00A0<item\u00A0name>'),
    'EQUIP': ('<armor\u00A0name>', '<shield\u00A0name>', '<wand\u00A0name>', '<weapon\u00A0name>'),
    'HELP': ('', '<command\u00A0name>'),
    'INVENTORY': ('',),
    'LOOK AT': ('<item\u00A0name>', '<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
                '<item\u00A0name>\u00A0IN\u00A0INVENTORY', 
                '<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', '<compass\u00A0direction>\u00A0DOOR',
                '<compass\u00A0direction>\u00A0DOORWAY'),
    'LEAVE': ('[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOOR',
              '[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0DOORWAY', 
              '[USING\u00A0or\u00A0VIA]\u00A0<door\u00A0name>',
              '[USING\u00A0or\u00A0VIA]\u00A0<compass\u00A0direction>\u00A0<door\u00A0name>'),
    'LOCK': ('<door\u00A0name>', '<chest\u00A0name>'),
    'OPEN': ('<door\u00A0name>', '<chest\u00A0name>'),
    'PICK LOCK': ('ON\u00A0[THE]\u00A0<chest\u00A0name>', 'ON\u00A0[THE]\u00A0<door\u00A0name>'),
    'PICK UP': ('<item\u00A0name>', '<number>\u00A0<item\u00A0name>'),
    'PUT': ('<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
            '<number>\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>',
            '<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>',
            '<number>\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse name>'),
    'REROLL': ('',),
    'QUIT': ('',),
    'SET CLASS': ('[TO]\u00A0<Warrior, Thief, Mage\u00A0or\u00A0Priest>',),
    'SET NAME': ('[TO]\u00A0<character\u00A0name>',),
    'STATUS': ('',),
    'TAKE': ('<item\u00A0name>\u00A0FROM\u00A0<container\u00A0name>',
             '<number>\u00A0<item\u00A0name>\u00A0FROM\u00A0<container\u00A0name>'),
    'UNEQUIP': ('<armor\u00A0name>', '<shield\u00A0name>', '<wand\u00A0name>', '<weapon\u00A0name>'),
    'UNLOCK': ('<door\u00A0name>', '<chest\u00A0name>')
}

COMMANDS_HELP = {
    'ATTACK': "The ATTACK command is used to attack creatures. Beware: if you attack a creature and don't kill it, it "
              "will attack you in return! After you kill a creature, you can check its corpse for loot using the LOOK "
              "AT command and take loot with the TAKE command.",
    'BEGIN GAME': "The BEGIN GAME command is used to start the game after you have set your name and class and approved"
                  " your ability scores. When you enter this command, you will automatically be equiped with your "
                  "starting gear and started in the antechamber of the dungeon.",
    'CAST SPELL': 'The CAST SPELL command can only be used by Mages and Priests. A Mage can cast an attack spell that '
                  'automatically hits creatures and does damage. A Priest can cast a healing spell on themselves.',
    'CLOSE': 'The CLOSE command can be used to close doors and chests.',
    'DRINK': 'The DRINK command can be used to drink health or mana potions.',
    'DROP': 'The DROP command can be used to remove items from your inventory and leave them on the floor. If you drop '
            'an item you had equipped, it will automatically be unequipped unless you have another on you.',
    'EQUIP': "The EQUIP command can be used to equip a weapon, armor, shield or wand from your inventory. You can't "
             "equip items from the floor.",
    'HELP': 'The HELP command can be used to get help about any game commands.',
    'INVENTORY': 'The INVENTORY command can be used to get a listing of the items in your inventory.',
    'LOOK AT': 'The LOOK at command can be used to get more information about doors, items on the floor or in a chest '
               'or on a corpse, chests, creatures and corpses.',
    'LEAVE': "The LEAVE command is used to exit the room you're in using the door you specify. If the door is locked "
             'you will be unable to leave using it until you can unlock it.',
    'LOCK': 'The LOCK command is used to lock doors and chests. You need a door key to lock doors and a chest key to '
            'lock chests. These keys can be found somewhere in the dungeon.',
    'OPEN': 'The OPEN command is used to open doors and chests.',
    'PICK LOCK': 'Only Thieves can use the pick lock command. The pick lock command enables you to unlock a door or '
                 'chest without needing a key. This saves some searching!',
    'PICK UP': 'The PICK UP command can be used to acquire items from the floor and put them in your inventory. To '
               'acquire items from a chest or corpse, use the take command.',
    'PUT': "The PUT command can be used to remove items from your inventory and place them in a chest or on a corpse's "
           "person. To leave items on the floor, use DROP.",
    'REROLL': 'The REROLL command is used before game start to get a fresh selection of randomly generated ability '
              'scores. You can reroll your ability scores as many times as you want.',
    'QUIT': 'The QUIT command is used to exit the game.',
    'SET CLASS': 'The SET CLASS command is used before game start to pick a class for your character. Your options are '
                 'Warrior, Thief, Mage or Priest.',
    'SET NAME': 'The SET NAME command is used before game start to pick a name for your character. Your name can have '
                'as many parts as you like, but each one must be a capital letter followed by lowercase letters. '
                'Symbols and numbers are not allowed.',
    'STATUS': "The STATUS command is used to see a summary of your hit points and current weapon, armor, shield "
              "choices. Spellcasters also see their mana points; and Mages see their current wand if they're using one.",
    'TAKE': "The TAKE command is used to remove items from a chest or a corpse and place them in your inventory.",
    'UNEQUIP': "The UNEQUIP command is used to unequip a weapon, armor, shield or wand from your inventory.",
    'UNLOCK': "The UNLOCK command is used to unlock a door or chest. You need a door key to unlock doors and a chest "
              "key to unlock chests."
}


class Command_Processor(object):
    __slots__ = 'game_state', 'dispatch_table',

    # All return values from *_command methods in this class are tuples. Every *_command method returns one or more
    # *_command_* objects, reflecting a sequence of changes in game State. (For example, an ATTACK action that doesn't
    # kill the foe will prompt the foe to attack. The foe's attack might lead to the character's death. So the return
    # value might be a `Attack_Command_Attack_Hit` object, a `Be_Attacked_by_Command_Attacked_and_Hit` object, and a
    # `Be_Attacked_by_Command_Character_Death` object, each bearing a message in its `message` property. The code which
    # handles the result of the ATTACK action knows it's receiving a tuple and will iterate through the result objects
    # and display each one's message to the player in turn.

    valid_name_re = re.compile('^[A-Z][a-z]+$')

    valid_class_re = re.compile('^(Warrior|Thief|Mage|Priest)$')

    pregame_commands = {'set_name', 'set_class', 'help', 'reroll', 'begin_game', 'quit'}

    ingame_commands = {'attack', 'cast_spell', 'close', 'help', 'drink', 'drop', 'equip', 'leave', 'inventory',
                       'look_at', 'lock', 'open', 'pick_lock', 'pick_up', 'quit', 'put', 'quit', 'status', 'take',
                       'unequip', 'unlock'}

    def __init__(self, game_state):
        self.dispatch_table = dict()
        commands_set = self.pregame_commands | self.ingame_commands
        for method_name in dir(type(self)):
            if not method_name.endswith('_command') or method_name.startswith('_'):
                continue
            command = method_name.rsplit('_', maxsplit=1)[0]
            self.dispatch_table[command] = getattr(self, method_name)
            if command not in commands_set:
                raise Internal_Exception('Inconsistency between set list of commands and command methods found by '
                                         f'introspection: method {method_name}() does not correspond to a command in '
                                         'pregame_commands or ingame_commands.')
            commands_set.remove(command)
        if len(commands_set):
            raise Internal_Exception('Inconsistency between set list of commands and command methods found by '
                                     f"introspection: command '{commands_set.pop()} does not correspond to a command "
                                     'in pregame_commands or ingame_commands.')
        self.game_state = game_state

    def process(self, natural_language_str):
        tokens = natural_language_str.strip().split()
        command = tokens.pop(0).lower()
        if command == 'cast' and len(tokens) and tokens[0].lower() == 'spell':
            command += '_' + tokens.pop(0).lower()
        elif command == 'leave' and len(tokens) and (tokens[0].lower() == 'using' or tokens[0].lower() == 'via'):
            tokens.pop(0)
        elif command == 'begin':
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
        elif command == 'quit':
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
            return stmsg.Command_Not_Recognized(command, self.pregame_commands, self.game_state.game_has_begun),
        elif command not in self.dispatch_table and self.game_state.game_has_begun:
            return stmsg.Command_Not_Recognized(command, self.ingame_commands, self.game_state.game_has_begun),
        elif not self.game_state.game_has_begun and command not in self.pregame_commands:
            return stmsg.Command_Not_Allowed_Now(command, self.pregame_commands, self.game_state.game_has_begun),
        elif self.game_state.game_has_begun and command not in self.ingame_commands:
            return stmsg.Command_Not_Allowed_Now(command, self.ingame_commands, self.game_state.game_has_begun),
        return self.dispatch_table[command](*tokens)

    def attack_command(self, *tokens):
        if (not self.game_state.character.weapon_equipped
                and (self.game_state.character_class != 'Mage' or not self.game_state.character.wand_equipped)):
            return stmsg.Attack_Command_You_Have_No_Weapon_or_Wand_Equipped(self.game_state.character_class),
        elif not tokens:
            return stmsg.Command_Bad_Syntax('ATTACK', *COMMANDS_SYNTAX['ATTACK']),
        weapon_type = 'wand' if self.game_state.character.wand_equipped else 'weapon'
        creature_title_token = ' '.join(tokens)
        if not self.game_state.rooms_state.cursor.creature_here:
            return stmsg.Attack_Command_Opponent_Not_Found(creature_title_token),
        elif self.game_state.rooms_state.cursor.creature_here.title.lower() != creature_title_token:
            return stmsg.Attack_Command_Opponent_Not_Found(creature_title_token,
                                                           self.game_state.rooms_state.cursor.creature_here.title),
        creature = self.game_state.rooms_state.cursor.creature_here
        attack_roll_dice_expr = self.game_state.character.attack_roll
        damage_roll_dice_expr = self.game_state.character.damage_roll
        attack_result = util.roll_dice(attack_roll_dice_expr)
        if attack_result < creature.armor_class:
            attack_missed_result = stmsg.Attack_Command_Attack_Missed(creature.title, weapon_type)
            be_attacked_by_result = self._be_attacked_by_command(creature)
            return (attack_missed_result,) + be_attacked_by_result
        else:
            damage_result = util.roll_dice(damage_roll_dice_expr)
            creature.take_damage(damage_result)
            if creature.hit_points == 0:
                corpse = creature.convert_to_corpse()
                self.game_state.rooms_state.cursor.container_here = corpse
                self.game_state.rooms_state.cursor.creature_here = None
                return (stmsg.Attack_Command_Attack_Hit(creature.title, damage_result, True, weapon_type),
                        stmsg.Various_Commands_Foe_Death(creature.title))
            else:
                attack_hit_result = stmsg.Attack_Command_Attack_Hit(creature.title, damage_result, False, weapon_type)
                be_attacked_by_result = self._be_attacked_by_command(creature)
                return (attack_hit_result,) + be_attacked_by_result

    def _be_attacked_by_command(self, creature):
        attack_roll_dice_expr = creature.attack_roll
        damage_roll_dice_expr = creature.damage_roll
        attack_result = util.roll_dice(attack_roll_dice_expr)
        if attack_result < self.game_state.character.armor_class:
            return stmsg.Be_Attacked_by_Command_Attacked_and_Not_Hit(creature.title),
        else:
            damage_done = util.roll_dice(damage_roll_dice_expr)
            self.game_state.character.take_damage(damage_done)
            if self.game_state.character.is_dead:
                return (stmsg.Be_Attacked_by_Command_Attacked_and_Hit(creature.title, damage_done, 0),
                        stmsg.Be_Attacked_by_Command_Character_Death())
            else:
                return (stmsg.Be_Attacked_by_Command_Attacked_and_Hit(creature.title, damage_done,
                                                                      self.game_state.character.hit_points),)

    def begin_game_command(self, *tokens):
        if len(tokens):
            return stmsg.Command_Bad_Syntax('BEGIN GAME', *COMMANDS_SYNTAX['BEGIN GAME']),
        character_name = getattr(self.game_state, 'character_name', None)
        character_class = getattr(self.game_state, 'character_class', None)
        if not character_name or not character_class:
            return stmsg.Begin_Game_Command_Name_or_Class_Not_Set(character_name, character_class),
        self.game_state.game_has_begun = True
        result = stmsg.Begin_Game_Command_Game_Begins(),      # v-- This is sorted just to make the tests deterministic.
        for item_type, item_internal_name in sorted(STARTER_GEAR[character_class].items(), key=operator.itemgetter(0)):
            item = self.game_state.items_state.get(item_internal_name)
            self.game_state.character.pick_up_item(item)
            getattr(self.game_state.character, 'equip_' + item_type)(item)
            if item.item_type == 'armor':
                result += (stmsg.Various_Commands_Item_Equipped(item.title, 'armor', self.game_state.character.armor_class,
                                                                'armor class'),)
            elif item.item_type == 'shield':
                result += (stmsg.Various_Commands_Item_Equipped(item.title, 'shield', self.game_state.character.armor_class,
                                                                'armor class'),)
            elif item.item_type == 'wand':
                result += (stmsg.Various_Commands_Item_Equipped(item.title, 'wand', self.game_state.character.attack_bonus,
                                                                'attack bonus', self.game_state.character.damage_roll,
                                                                'damage'),)
            else:
                result += (stmsg.Various_Commands_Item_Equipped(item.title, 'weapon', self.game_state.character.attack_bonus,
                                                                'attack bonus', self.game_state.character.damage_roll,
                                                                'damage'),)
        return result + (stmsg.Various_Commands_Entered_Room(self.game_state.rooms_state.cursor),)

    def cast_spell_command(self, *tokens):
        if self.game_state.character_class not in ('Mage', 'Priest'):
            return stmsg.Command_Class_Restricted('CAST SPELL', 'mage', 'priest'),
        elif len(tokens):
            return stmsg.Command_Bad_Syntax('CAST SPELL', *COMMANDS_SYNTAX['CAST SPELL']),
        elif self.game_state.character.mana_points < SPELL_MANA_COST:
            return stmsg.Cast_Spell_Command_Insuffient_Mana(self.game_state.character.mana_points,
                                                            self.game_state.character.mana_point_total,
                                                            SPELL_MANA_COST),
        elif self.game_state.character_class == 'Mage':
            if self.game_state.rooms_state.cursor.creature_here is None:
                return stmsg.Cast_Spell_Command_No_Creature_to_Target(),
            else:
                damage_dealt = util.roll_dice(SPELL_DAMAGE)
                creature = self.game_state.rooms_state.cursor.creature_here
                creature.take_damage(damage_dealt)
                if creature.is_dead:
                    return (stmsg.Cast_Spell_Command_Cast_Damaging_Spell(creature.title, damage_dealt),
                            stmsg.Various_Commands_Foe_Death(creature.title))
                else:
                    be_attacked_by_result = self._be_attacked_by_command(creature)
                    return ((stmsg.Cast_Spell_Command_Cast_Damaging_Spell(creature.title, damage_dealt),) +
                                                                    be_attacked_by_result)
        else:
            damage_rolled = util.roll_dice(SPELL_DAMAGE)
            healed_amt = self.game_state.character.heal_damage(damage_rolled)
            return (stmsg.Cast_Spell_Command_Cast_Healing_Spell(),
                    stmsg.Various_Commands_Underwent_Healing_Effect(healed_amt, self.game_state.character.hit_points,
                                                                    self.game_state.character.hit_point_total))

    def close_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('CLOSE', *tokens)
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            object_to_close, = result
        if object_to_close.is_closed:
            return stmsg.Close_Command_Object_Is_Already_Closed(object_to_close.title),
        else:
            object_to_close.is_closed = True
            return stmsg.Close_Command_Object_Has_Been_Closed(object_to_close.title),

    def drink_command(self, *tokens):
        if not len(tokens) or tokens == ('the',):
            return stmsg.Command_Bad_Syntax('DRINK', *COMMANDS_SYNTAX['DRINK']),
        if tokens[0] == 'the' or tokens[0] == 'a':
            drinking_qty = 1
            tokens = tokens[1:]
        elif tokens[0].isdigit() or util.lexical_number_in_1_99_re.match(tokens[0]):
            drinking_qty = int(tokens[0]) if tokens[0].isdigit() else util.lexical_number_to_digits(tokens[0])
            if (drinking_qty > 1 and not tokens[-1].endswith('s')) or (drinking_qty == 1 and tokens[-1].endswith('s')):
                return stmsg.Command_Bad_Syntax('DRINK', *COMMANDS_SYNTAX['DRINK']),
            tokens = tokens[1:]
        else:
            drinking_qty = 1
            if tokens[-1].endswith('s'):
                return stmsg.Command_Bad_Syntax('DRINK', *COMMANDS_SYNTAX['DRINK']),
        item_title = ' '.join(tokens).rstrip('s')
        matching_items_qtys_objs = tuple(filter(lambda argl: argl[1].title == item_title,
                                                self.game_state.character.list_items()))
        if not len(matching_items_qtys_objs):
            return stmsg.Drink_Command_Item_Not_in_Inventory(item_title),
        item_qty, item = matching_items_qtys_objs[0]
        if not item.title.endswith(' potion'):
            return stmsg.Drink_Command_Item_Not_Drinkable(item_title),
        elif drinking_qty > item_qty:
            return stmsg.Drink_Command_Tried_to_Drink_More_than_Possessed(item_title, drinking_qty, item_qty),
        elif item.title == 'health potion':
            hit_points_recovered = item.hit_points_recovered
            healed_amt = self.game_state.character.heal_damage(hit_points_recovered)
            self.game_state.character.drop_item(item)
            return stmsg.Various_Commands_Underwent_Healing_Effect(healed_amt, self.game_state.character.hit_points,
                                                                   self.game_state.character.hit_point_total),
        else:   # item.title == 'mana potion':
            if self.game_state.character_class not in ('Mage', 'Priest'):
                return stmsg.Drink_Command_Drank_Mana_Potion_when_Not_A_Spellcaster(),
            mana_points_recovered = item.mana_points_recovered
            regained_amt = self.game_state.character.regain_mana(mana_points_recovered)
            self.game_state.character.drop_item(item)
            return stmsg.Drink_Command_Drank_Mana_Potion(regained_amt, self.game_state.character.mana_points,
                                                         self.game_state.character.mana_point_total),

    def drop_command(self, *tokens):
        result = self._pick_up_or_drop_preproc('DROP', *tokens)
        if len(result) == 1 and isinstance(result[0], stmsg.Game_State_Message):
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
            return stmsg.Drop_Command_Trying_to_Drop_Item_You_Dont_Have(item_title, drop_amount),
        (item_had_qty, item), = items_had_pair
        if drop_amount is math.nan:
            drop_amount = item_had_qty
        amount_already_here = item_here_pair[0][0] if len(item_here_pair) else 0
        if drop_amount > item_had_qty:
            return stmsg.Drop_Command_Trying_to_Drop_More_than_You_Have(item_title, drop_amount, item_had_qty),
        else:
            unequip_return = ()
            if drop_amount - item_had_qty == 0:
                armor_equipped = self.game_state.character.armor_equipped
                weapon_equipped = self.game_state.character.weapon_equipped
                shield_equipped = self.game_state.character.shield_equipped
                wand_equipped = self.game_state.character.wand_equipped
                if item.item_type == 'armor' and armor_equipped is not None and armor_equipped.internal_name == item.internal_name:
                    self.game_state.character.unequip_armor()
                    unequip_return = stmsg.Various_Commands_Item_Unequipped(item.title, item.item_type,
                                                                            self.game_state.character.armor_class,
                                                                      'armor class'),
                elif item.item_type == 'weapon' and weapon_equipped is not None and weapon_equipped.internal_name == item.internal_name:
                    self.game_state.character.unequip_weapon()
                    if wand_equipped:
                        unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon',
                                                                                change_text="You're still attacking with your wand."),
                    else:
                        unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon',
                                                                                change_text="You now can't attack."),
                elif item.item_type == 'shield' and shield_equipped is not None and shield_equipped.internal_name == item.internal_name:
                    self.game_state.character.unequip_shield()
                    unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'shield',
                                                                            self.game_state.character.armor_class,
                                                                            'armor class'),
                elif item.item_type == 'wand' and wand_equipped is not None and wand_equipped.internal_name == item.internal_name:
                    self.game_state.character.unequip_wand()
                    if weapon_equipped:
                        unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'wand',
                                                                                change_text=f"You're now attacking with your {weapon_equipped.title}."),
                    else:
                        unequip_return = stmsg.Various_Commands_Item_Unequipped(item_title, 'wand',
                                                                                change_text="You now can't attack."),
            self.game_state.character.drop_item(item, qty=drop_amount)
            if self.game_state.rooms_state.cursor.items_here is None:
                self.game_state.rooms_state.cursor.items_here = Items_Multi_State()
            self.game_state.rooms_state.cursor.items_here.set(item.internal_name,
                                                              amount_already_here + drop_amount, item)
            amount_had_now = item_had_qty - drop_amount
            return unequip_return + (stmsg.Drop_Command_Dropped_Item(item_title, item.item_type, drop_amount,
                                                                     amount_already_here + drop_amount, amount_had_now),)

    def equip_command(self, *tokens):
        if not tokens:
            return stmsg.Command_Bad_Syntax('EQUIP', *COMMANDS_SYNTAX['EQUIP']),
        item_title = ' '.join(tokens)
        matching_item_tuple = tuple(item for _, item in self.game_state.character.list_items()
                                             if item.title == item_title)
        if not len(matching_item_tuple):
            return stmsg.Equip_Command_No_Such_Item_in_Inventory(item_title),
        item, = matching_item_tuple[0:1]
        can_use_attr = self.game_state.character_class.lower() + '_can_use'
        if not getattr(item, can_use_attr):
            return stmsg.Equip_Command_Class_Cant_Use_Item(self.game_state.character_class, item_title, item.item_type),
        retval = tuple()
        if item.item_type == 'armor' and self.game_state.character.armor_equipped:
            old_equipped = self.game_state.character.armor_equipped
            retval = stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                            self.game_state.character.armor_class, 'armor class'),
        elif item.item_type == 'shield' and self.game_state.character.shield_equipped:
            old_equipped = self.game_state.character.shield_equipped
            retval = stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                            self.game_state.character.armor_class, 'armor class'),
        elif item.item_type == 'wand' and self.game_state.character.wand_equipped:
            old_equipped = self.game_state.character.wand_equipped
            retval = stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                            change_text="You now can't attack."),
        elif item.item_type == 'weapon' and self.game_state.character.weapon_equipped:
            old_equipped = self.game_state.character.weapon_equipped
            retval = stmsg.Various_Commands_Item_Unequipped(old_equipped.title, old_equipped.item_type,
                                                            change_text="You now can't attack."),
        if item.item_type == 'armor':
            self.game_state.character.equip_armor(item)
            return retval + (stmsg.Various_Commands_Item_Equipped(item.title, 'armor',
                                                                  self.game_state.character.armor_class, 'armor class'),)
        elif item.item_type == 'shield':
            self.game_state.character.equip_shield(item)
            return retval + (stmsg.Various_Commands_Item_Equipped(item.title, 'shield',
                                                                  self.game_state.character.armor_class, 'armor class'),)
        elif item.item_type == 'wand':
            self.game_state.character.equip_wand(item)
            return retval + (stmsg.Various_Commands_Item_Equipped(item.title, 'wand',
                                                                  self.game_state.character.attack_bonus, 'attack bonus',
                                                                  self.game_state.character.damage_roll, 'damage'),)
        else:
            self.game_state.character.equip_weapon(item)
            return retval + (stmsg.Various_Commands_Item_Equipped(item.title, 'weapon',
                                                                  self.game_state.character.attack_bonus, 'attack bonus',
                                                                  self.game_state.character.damage_roll, 'damage'),)


    def help_command(self, *tokens):
        commands_tuple = tuple(sorted(map(lambda strval: strval.replace('_', ' ').upper(),
                                          self.pregame_commands | self.ingame_commands)))
        if len(tokens) == 0:
            return stmsg.Help_Command_Display_Commands(commands_tuple),
        else:
            command = ' '.join(tokens)
            command_upper = command.upper()
            command_uscores = command.replace(' ', '_')
            if command_uscores not in self.pregame_commands and command_uscores not in self.ingame_commands:
                return stmsg.Help_Command_Command_Not_Recognized(command_upper, commands_tuple),
            else:
                return stmsg.Help_Command_Display_Help_for_Command(command_upper, COMMANDS_SYNTAX[command_upper],
                                                                   COMMANDS_HELP[command_upper]),

    def inventory_command(self, *tokens):
        if len(tokens):
            return stmsg.Command_Bad_Syntax('INVENTORY', *COMMANDS_SYNTAX['INVENTORY']),
        inventory_contents = sorted(self.game_state.character.list_items(), key=lambda argl: argl[1].title)
        return stmsg.Inventory_Command_Display_Inventory(inventory_contents),

    def leave_command(self, *tokens):
        if (not len(tokens) or len(tokens) != 2 or tokens[0] not in ('north', 'east', 'south', 'west')
            or tokens[1] not in ('door', 'doorway', 'exit')):
            return stmsg.Command_Bad_Syntax('LEAVE', *COMMANDS_SYNTAX['LEAVE']),
        compass_dir = tokens[0]
        portal_type = tokens[1]
        door_attr = f'{compass_dir}_door'
        door = getattr(self.game_state.rooms_state.cursor, door_attr, None)
        if door is None:
            return stmsg.Various_Commands_Door_Not_Present(compass_dir, portal_type),
        elif door.is_exit:
            return stmsg.Leave_Command_Left_Room(compass_dir, portal_type), stmsg.Leave_Command_Won_The_Game()
        self.game_state.rooms_state.move(**{compass_dir: True})
        return (stmsg.Leave_Command_Left_Room(compass_dir, portal_type),
                stmsg.Various_Commands_Entered_Room(self.game_state.rooms_state.cursor))

    def lock_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('LOCK', *tokens)
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            object_to_lock, = result
        if object_to_lock.is_locked:
            return stmsg.Lock_Command_Object_Is_Already_Locked(object_to_lock.title),
        else:
            object_to_lock.is_locked = True
            return stmsg.Lock_Command_Object_Has_Been_Locked(object_to_lock.title),

    def _lock_unlock_open_or_close_preproc(self, command, *tokens):
        door = None
        if not len(tokens):
            return stmsg.Command_Bad_Syntax(command.upper(), *COMMANDS_SYNTAX[command.upper()]),
        if tokens[-1] in ('door', 'doorway'):
            result = self._look_at_open_close_lock_unlock_door_selector(*tokens)
            if isinstance(result[0], stmsg.Game_State_Message):
                return result
            else:
                door, = result
        target_title = ' '.join(tokens) if door is None else None
        container = self.game_state.rooms_state.cursor.container_here
        if lock_unlock_mode := command.lower().endswith('lock'):
            key_objs = [item for _, item in self.game_state.character.list_items()
                        if item.title.endswith(' key')]
        if (door is None and container is not None and isinstance(container, elem.Chest)
                and container.title == target_title):
            if lock_unlock_mode and (not len(key_objs) or not any(key.title == 'chest key'
                                                                  for key in key_objs)):
                if command.lower() == 'unlock':
                    return stmsg.Unlock_Command_Dont_Possess_Correct_Key(container.title, 'chest key'),
                else:
                    return stmsg.Lock_Command_Dont_Possess_Correct_Key(container.title, 'chest key'),
            else:
                return container,
        if lock_unlock_mode and (not key_objs or not any(key.title == 'door key' for key in key_objs)):
            return ((stmsg.Unlock_Command_Dont_Possess_Correct_Key(door.title, 'door key'),)
                         if command.lower() == 'unlock'
                         else (stmsg.Lock_Command_Dont_Possess_Correct_Key(door.title, 'door key'),))
        else:
            return door,

        # Control flow fell off the end of the loop, which means none of the doors in the room had a title matching the
        # object title specified in the command, and if there's a chest in the room the chest didn't match either. So
        # whatever the user wanted to lock/unlock, it's not here.
        if command.lower() == 'unlock':
            return stmsg.Unlock_Command_Object_to_Unlock_Not_Here(target_title),
        elif command.lower() == 'lock':
            return stmsg.Lock_Command_Object_to_Lock_Not_Here(target_title),
        elif command.lower() == 'open':
            return stmsg.Open_Command_Object_to_Open_Not_Here(target_title),
        else:
            return stmsg.Close_Command_Object_to_Close_Not_Here(target_title),

    def _look_at_open_close_lock_unlock_door_selector(self, *tokens):
        compass_dir = door_type = None
        if tokens[0] in ('north', 'east', 'south', 'west'):
            compass_dir = tokens[0]
            door_title = f'{compass_dir} {tokens[-1]}'
            tokens = tokens[1:]
        if ((len(tokens) == 2 and tokens[0] in ('iron', 'wooden') and tokens[1] == 'door')
                or len(tokens) == 1 and tokens[0] == 'doorway'):
            door_type = ' '.join(tokens).replace(' ', '_')
        doors = self.game_state.rooms_state.cursor.doors
        matching_doors = list()
        for door in doors:
            if ((door_type and door.door_type == door_type and compass_dir and door.title == door_title)
                    or (door_type and door.door_type == door_type) or (compass_dir and door.title == door_title)
                    or (not door_type and not compass_dir and door.door_type.endswith(tokens[-1]))):
                matching_doors.append(door)
        if len(matching_doors) == 0:
            return stmsg.Various_Commands_Door_Not_Present(compass_dir, tokens[-1]),
        elif len(matching_doors) > 1:
            compass_dirs = tuple(door.title.split(' ')[0] for door in matching_doors)
            # Checks that all door_types are the same.
            door_type = matching_doors[0].door_type if len(set(door.door_type for door in matching_doors)) == 1 else None
            return stmsg.Various_Commands_Ambiguous_Door_Specifier(compass_dirs, tokens[-1], door_type),
        else:
            return tuple(matching_doors)

    look_at_door_re = re.compile("""(                                                                                   
                                        (north|east|south|west) \s  # For example, this regex matches 'north iron door',
                                    |                               # 'north door', 'iron door', and 'door'. But it won't 
                                        (iron|wooden) \s            # match 'iron doorway'.
                                    |
                                        (
                                            (north|east|south|west) \s (iron|wooden) \s
                                        )
                                    )?
                                    (door|doorway)
                                    (?<! iron \s doorway)           # Lookbehinds must be fixed-width so I use 2.
                                    (?<! wooden \s doorway)
                                    """, re.X)

    def look_at_command(self, *tokens):
        if (not tokens or tokens[0] in ('in', 'on') or tokens[-1] in ('in', 'on')
                or ('in' in tokens and tokens[-1] == 'corpse')
                or ('on' in tokens and tokens[-1] == 'chest')):
            return stmsg.Command_Bad_Syntax('LOOK AT', *COMMANDS_SYNTAX['LOOK AT']),
        # This conditional is more easily accomplished with a simple regex than a multi-line boolean chain.
        # `look_at_door_re` is defined above.
        elif tokens[-1] in ('door', 'doorway') and not self.look_at_door_re.match(' '.join(tokens)):
            return stmsg.Command_Bad_Syntax('LOOK AT', *COMMANDS_SYNTAX['LOOK AT']),
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
            result = self._look_at_open_close_lock_unlock_door_selector(*tokens)
            if isinstance(result, tuple) and isinstance(result[0], stmsg.Game_State_Message):
                return result
            else:
                door, = result
                return stmsg.Look_At_Command_Found_Door_or_Doorway(door.title.split(' ')[0], door),
        else:
            target_title = ' '.join(tokens)
        creature_here = self.game_state.rooms_state.cursor.creature_here
        container_here = self.game_state.rooms_state.cursor.container_here
        if (item_in_chest and isinstance(container_here, elem.Corpse)
            or item_on_corpse and isinstance(container_here, elem.Chest)):
            return stmsg.Command_Bad_Syntax('look at', *commands_syntax['look at']),
        if creature_here is not None and creature_here.title == target_title.lower():
            return stmsg.Look_At_Command_Found_Creature_Here(creature_here.description),
        elif container_here is not None and container_here.title == target_title.lower():
            return stmsg.Look_At_Command_Found_Container_Here(container_here),
        elif item_contained:
            if item_in_inventory:
                for item_qty, item in self.game_state.character.list_items():
                    if item.title != target_title:
                        continue
                    return stmsg.Look_At_Command_Found_Item_or_Items_Here(self._look_at_item_detail(item), item_qty),
                return stmsg.Look_At_Command_Found_Nothing(target_title, 'inventory', 'inventory'),
            else:
                if container_here is None or container_here.title != location_title:
                    return stmsg.Various_Commands_Container_Not_Found(location_title),
                elif container_here is not None and container_here.title == location_title:
                    for item_qty, item in container_here.values():
                        if item.title != target_title:
                            continue
                        return stmsg.Look_At_Command_Found_Item_or_Items_Here(self._look_at_item_detail(item), item_qty),
                    return stmsg.Look_At_Command_Found_Nothing(target_title, location_title,
                                                               'chest' if item_in_chest else 'corpse'),
                else:
                    return stmsg.Various_Commands_Container_Not_Found(location_title),
        else:
            for item_name, (item_qty, item) in self.game_state.rooms_state.cursor.items_here.items():
                if item.title != target_title:
                    continue
                return stmsg.Look_At_Command_Found_Item_or_Items_Here(self._look_at_item_detail(item), item_qty),
            return stmsg.Look_At_Command_Found_Nothing(target_title),

    def _look_at_item_detail(self, element):
        descr_append_str = ''
        if getattr(element, 'item_type', '') in ('armor', 'shield', 'wand', 'weapon'):
            if element.item_type == 'wand' or element.item_type == 'weapon':
                descr_append_str = (f' Its attack bonus is +{element.attack_bonus} and its damage is '
                                    f'{element.damage}. ')
            else:  # item_type == 'armor' or item_type == 'shield'
                descr_append_str = f' Its armor bonus is +{element.armor_bonus}. '
            can_use_list = []
            for character_class in ('warrior', 'thief', 'mage', 'priest'):
                if getattr(element, f'{character_class}_can_use', False):
                    can_use_list.append(f"{character_class}s" if character_class != 'thief' else 'thieves')
            can_use_list[0] = can_use_list[0].title()
            if len(can_use_list) == 1:
                descr_append_str += f'{can_use_list[0]} can use this.'
            elif len(can_use_list) == 2:
                descr_append_str += f'{can_use_list[0]} and {can_use_list[1]} can use this.'
            else:
                can_use_joined = ', '.join(can_use_list[:-1])
                descr_append_str += f'{can_use_joined}, and {can_use_list[-1]} can use this.'
        elif getattr(element, 'item_type', '') == 'potion':
            if element.title == 'mana potion':
                descr_append_str = f' It restores {element.mana_points_recovered} mana points.'
            elif element.title == 'health potion':
                descr_append_str = f' It restores {element.hit_points_recovered} hit points.'
        elif 'door' in getattr(element, 'door_type', ''):
            if element.closeable:
                descr_append_str = ' It is closed.' if element.is_closed else ' It is open.'
        return element.description + descr_append_str

    def open_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('OPEN', *tokens)
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            object_to_open, = result
        if object_to_open.is_locked:
            return stmsg.Open_Command_Object_Is_Locked(object_to_open.title),
        elif object_to_open.is_closed:
            object_to_open.is_closed = False
            return stmsg.Open_Command_Object_Has_Been_Opened(object_to_open.title),
        else:
            return stmsg.Open_Command_Object_Is_Already_Open(object_to_open.title),

    def pick_lock_command(self, *tokens):
        if self.game_state.character_class != 'Thief':
            return stmsg.Command_Class_Restricted('PICK LOCK', 'thief'),
        if not len(tokens) or tokens[0] != 'on' or tokens == ('on',) or tokens == ('on', 'the',):
            return stmsg.Command_Bad_Syntax('PICK LOCK', *COMMANDS_SYNTAX['PICK LOCK']),
        elif tokens[1] == 'the':
            tokens = tokens[2:]
        else:
            tokens = tokens[1:]
        target_title = ' '.join(tokens)
        container = self.game_state.rooms_state.cursor.container_here
        door_objs = []
        for compass_dir in ('north', 'east', 'south', 'west'):
            door = getattr(self.game_state.rooms_state.cursor, f'{compass_dir}_door', None)
            if door is None:
                continue
            door_objs.append(door)
        if container is not None and container.title == target_title:
            if not getattr(container, 'is_locked', False):
                return stmsg.Pick_Lock_Command_Target_Not_Locked(target_title),
            else:
                container.is_locked = False
                return stmsg.Pick_Lock_Command_Target_Has_Been_Unlocked(target_title),
        elif target_title.endswith('door'):
            door_obj_match = tuple(filter(lambda door: door.title == target_title, door_objs))
            if not door_obj_match:
                return stmsg.Pick_Lock_Command_Target_Not_Found(target_title),
            else:
                door, = door_obj_match[0:1]
                if not door.is_locked:
                    return stmsg.Pick_Lock_Command_Target_Not_Locked(target_title),
                else:
                    door.is_locked = False
                    return stmsg.Pick_Lock_Command_Target_Has_Been_Unlocked(target_title),
        else:
            return stmsg.Pick_Lock_Command_Target_Cant_Be_Unlocked_or_Not_Found(target_title),

    def pick_up_command(self, *tokens):
        door = None
        result = self._pick_up_or_drop_preproc('PICK UP', *tokens)
        if len(result) == 1 and isinstance(result[0], stmsg.Game_State_Message):
            return result
        elif tokens[-1] not in ('door', 'doorway'):
            pick_up_amount, element_title = result
        else:
            result = _look_at_open_close_lock_unlock_door_selector(*tokens)
            if isinstance(result[0], stmsg.Game_State_Message):
                element_title = tokens[-1]
            else:
                door, = result
                element_title = door.title
        unpickupable_item_type = ''
        if door is not None:
            unpickupable_item_type = 'door'
        elif self.game_state.rooms_state.cursor.creature_here is not None and self.game_state.rooms_state.cursor.creature_here.title == element_title:
            unpickupable_item_type = 'creature'
        elif self.game_state.rooms_state.cursor.container_here is not None and self.game_state.rooms_state.cursor.container_here.title == element_title:
            unpickupable_item_type = self.game_state.rooms_state.cursor.container_here.container_type
        if unpickupable_item_type:
            return stmsg.Pick_Up_Command_Cant_Pick_Up_Creature_Chest_or_Door(unpickupable_item_type, element_title),
        item_title = element_title
        if self.game_state.rooms_state.cursor.items_here is not None:
            items_here = tuple(self.game_state.rooms_state.cursor.items_here.values())
        else:
            return stmsg.Pick_Up_Command_Item_Not_Found(item_title, pick_up_amount),
        items_had = tuple(self.game_state.character.list_items())
        item_here_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_here))
        items_had_pair = tuple(filter(lambda pair: pair[1].title == item_title, items_had))
        if not len(item_here_pair):
            items_here_qtys_titles = tuple((item_qty, item.title) for item_qty, item in items_here)
            return stmsg.Pick_Up_Command_Item_Not_Found(item_title, pick_up_amount, *items_here_qtys_titles),
        (item_qty, item), = item_here_pair
        if pick_up_amount is math.nan:
            pick_up_amount = item_qty
        amount_already_had = items_had_pair[0][0] if len(items_had_pair) else 0
        if item_qty < pick_up_amount:
            return stmsg.Pick_Up_Command_Trying_to_Pick_Up_More_than_Is_Present(item_title, pick_up_amount, item_qty),
        else:
            self.game_state.character.pick_up_item(item, qty=pick_up_amount)
            if item_qty == pick_up_amount:
                self.game_state.rooms_state.cursor.items_here.delete(item.internal_name)
            else:
                self.game_state.rooms_state.cursor.items_here.set(item.internal_name,
                                                                  item_qty - pick_up_amount, item)
            amount_had_now = amount_already_had + pick_up_amount
            return stmsg.Pick_Up_Command_Item_Picked_Up(item_title, pick_up_amount, amount_had_now),

    # Both PUT and TAKE have the same preprocessing challenges, so I refactored their logic into a shared private
    # preprocessing method.

    def _pick_up_or_drop_preproc(self, command, *tokens):
        if tokens[0] == 'a' or tokens[0] == 'the' or tokens[0].isdigit() or util.lexical_number_in_1_99_re.match(tokens[0]):
            if len(tokens) == 1:
                return stmsg.Command_Bad_Syntax(command.upper(), *COMMANDS_SYNTAX[command.upper()]),
            item_title = ' '.join(tokens[1:])
            if tokens[0] == 'a':
                if tokens[-1].endswith('s'):
                    return (stmsg.Drop_Command_Quantity_Unclear(),) if command.lower() == 'drop' else (stmsg.Pick_Up_Command_Quantity_Unclear(),)
                item_qty = 1
            elif tokens[0].isdigit():
                item_qty = int(tokens[0])
            elif tokens[0] == 'the':
                if tokens[-1].endswith('s'):
                    item_qty = math.nan
                else:
                    item_qty = 1
            else:  # util.lexical_number_in_1_99_re.match(tokens[0]) is True
                item_qty = util.lexical_number_to_digits(tokens[0])
            if item_qty == 1 and item_title.endswith('s'):
                return stmsg.Pick_Up_Command_Quantity_Unclear(),
        else:
            item_title = ' '.join(tokens)
            if item_title.endswith('s'):
                item_qty = math.nan
            else:
                item_qty = 1
        item_title = item_title.rstrip('s')
        return item_qty, item_title

    def put_command(self, *tokens):
        results = self._put_or_take_preproc('PUT', 'IN|ON', *tokens)

        # The workhorse private method returns either a stmsg.Game_State_Message subclass object (see
        # adventuregame.game_state_messages) or a tuple of amount to put, parsed title of Item, parsed title of
        # Container, and the Container object (as a matter of convenience, it's needed by the private method & why fetch
        # it twice).
        if len(results) == 1 and isinstance(results[0], stmsg.Game_State_Message):
            return results
        else:
            # len(results) == 4 and isinstance(results[0], int) and isinstance(results[1], str)
            #     and isinstance(results[2], str) and isinstance(results[3], Container)
            put_amount, item_title, container_title, container = results

        # I read off the player's Inventory and filter it for a (qty,obj) pair whose title matches the supplied Item
        # name.
        inventory_list = tuple(filter(lambda pair: pair[1].title == item_title, self.game_state.character.list_items()))

        if len(inventory_list) == 1:

            # The player has the Item in their Inventory, so I save the qty they possess and the Item object.
            amount_possessed, item = inventory_list[0]
        else:
            return stmsg.Put_Command_Item_Not_in_Inventory(item_title, put_amount),
        if container.contains(item.internal_name):
            amount_in_container, _ = container.get(item.internal_name)
        else:
            amount_in_container = 0
        if put_amount > amount_possessed:
            return stmsg.Put_Command_Trying_to_Put_More_than_You_Have(item_title, amount_possessed),
        elif put_amount is math.nan:
            put_amount = amount_possessed
        else:
            amount_possessed -= put_amount
        self.game_state.character.drop_item(item, qty=put_amount)
        container.set(item.internal_name, amount_in_container + put_amount, item)
        return stmsg.Put_Command_Amount_Put(item_title, container_title, container.container_type, put_amount,
                                            amount_possessed),

    def _put_or_take_preproc(self, command, joinword, *tokens):
        container = self.game_state.rooms_state.cursor.container_here

        if command.lower() == 'put':
            if container.container_type == 'chest':
                joinword = 'IN'
            else:
                joinword = 'ON'

        command, joinword = command.lower(), joinword.lower()
        tokens = list(tokens)

        # Whatever the user wrote, it doesn't contain the joinword, which is a required token.
        if joinword not in tokens or tokens.index(joinword) == 0 or tokens.index(joinword) == len(tokens) - 1:
            return stmsg.Command_Bad_Syntax(command.upper(), *COMMANDS_SYNTAX[command.upper()]),

        # The first token is a digital number, great.
        if util.digit_re.match(tokens[0]):
            amount = int(tokens.pop(0))

        # The first token is a lexical number, so I convert it.
        elif util.lexical_number_in_1_99_re.match(tokens[0]):
            amount = util.lexical_number_to_digits(tokens.pop(0))

        # The first token is an indirect article, which would mean '1'.
        elif tokens[0] == 'a':
            joinword_index = tokens.index(joinword)

            # The term before the joinword, which is the Item title, is plural. The sentence is ungrammatical, so I
            # return an error.
            if tokens[joinword_index - 1].endswith('s'):
                return (stmsg.Take_Command_Quantity_Unclear(),) if command == 'take' else (stmsg.Put_Command_Quantity_Unclear(),)
            amount = 1
            del tokens[0]

        # No other indication was given, so the amount will have to be determined later; either the total amount found
        # in the Container (for TAKE) or the total amount in the Inventory (for PUT)
        else:
            amount = math.nan

        # I form up the item_title and container_title, but I'm not done testing them.
        joinword_index = tokens.index(joinword)
        item_title = ' '.join(tokens[0:joinword_index])
        container_title = ' '.join(tokens[joinword_index+1:])

        # The item_title begins with a direct article.
        if item_title.startswith('the ') or item_title.startswith('the') and len(item_title) == 3:

            # The title is of the form, 'the gold coins', which means the amount intended is the total amount
            # available-- either the total amount in the Container (for TAKE) or the total amount in the Character's
            # Inventory (for PUT). That will be dertermined later, so NaN is used as a signal value to be replaced when
            # possible.
            if item_title.endswith('s'):
                amount = math.nan
                item_title = item_title[:-1]
            item_title = item_title[4:]

            # `item_title` is *just* 'the'. The sentence is ungrammatical, so I return a syntax error.
            if not item_title:
                return stmsg.Command_Bad_Syntax(command.upper(), *COMMANDS_SYNTAX[command.upper()]),

        if item_title.endswith('s'):
            if amount == 1:

                # The `item_title` ends in a plural, but an amount > 1 was specified. That's an ungrammatical sentence,
                # so I return a syntax error.
                return stmsg.Command_Bad_Syntax(command.upper(), *COMMANDS_SYNTAX[command.upper()]),

            # The title is plural and `amount` is > 1. I strip the pluralizing 's' off to get the correct Item title.
            item_title = item_title[:-1]

        if container_title.startswith('the ') or container_title.startswith('the') and len(container_title) == 3:

            # The Container term begins with a direct article and ends with a pluralizing 's'. That's invalid, no
            # Container in the dungeon is found in grouping of more than one, so I return a syntax error.
            if container_title.endswith('s'):
                return stmsg.Command_Bad_Syntax(command.upper(), *COMMANDS_SYNTAX[command.upper()]),

            container_title = container_title[4:]
            if not container_title:

                # Improbably, the Item title is *just* 'the'. That's an ungrammatical sentence, so I return a syntax
                # error.
                return stmsg.Command_Bad_Syntax(command.upper(), *COMMANDS_SYNTAX[command.upper()]),

        if container is None:

            # There is no Container in this Room, so no TAKE command can be correct. I return an error.
            return stmsg.Various_Commands_Container_Not_Found(container_title),  # tested
        elif not container_title == container.title:

            # The Container name specified doesn't match the name of the Container in this Room, so I return an error.
            return stmsg.Various_Commands_Container_Not_Found(container_title, container.title),  # tested

        elif container.is_closed:

            # The Container can't be PUT IN to or TAKEn from because it is closed.
            return stmsg.Various_Commands_Container_Is_Closed(container.title),

        return amount, item_title, container_title, container

    def quit_command(self, *tokens):
        if len(tokens):
            return stmsg.Command_Bad_Syntax('QUIT', *COMMANDS_SYNTAX['QUIT']),
        self.game_state.game_has_ended = True
        return stmsg.Quit_Command_Have_Quit_The_Game(),

    def reroll_command(self, *tokens):
        if len(tokens):
            return stmsg.Command_Bad_Syntax('REROLL', *COMMANDS_SYNTAX['REROLL']),
        character_name = getattr(self.game_state, 'character_name', None)
        character_class = getattr(self.game_state, 'character_class', None)
        if not character_name or not character_class:
            return stmsg.Reroll_Command_Name_or_Class_Not_Set(character_name, character_class),
        self.game_state.character.ability_scores.roll_stats()
        return stmsg.Set_Name_or_Class_Command_Display_Rolled_Stats(
                   strength=self.game_state.character.strength,
                   dexterity=self.game_state.character.dexterity,
                   constitution=self.game_state.character.constitution,
                   intelligence=self.game_state.character.intelligence,
                   wisdom=self.game_state.character.wisdom,
                   charisma=self.game_state.character.charisma),

    # Concerning both set_name_command() and set_class_command() below it:
    #
    # The Character object isn't instanced in Game_State.__init__ because it depends on name and class choice. Its
    # character_name and character_class setters have a side effect where if both have been set the Character object is
    # instanced automatically. So after valid input is determined, I check for the State of <both character_name and
    # character_class are now non-None>; if so, the Character object was just instanced. That means the ability scores
    # were rolled and assigned. The player may choose to reroll, so the return tuple includes a prompt to do so.

    def set_class_command(self, *tokens):
        if len(tokens) == 0 or len(tokens) > 1:
            return stmsg.Command_Bad_Syntax('SET CLASS', *COMMANDS_SYNTAX['SET CLASS']),
        elif not self.valid_class_re.match(tokens[0]):
            return stmsg.Set_Class_Command_Invalid_Class(tokens[0]),
        class_str = tokens[0]
        class_was_none = self.game_state.character_class is None
        self.game_state.character_class = class_str
        if self.game_state.character_name is not None and class_was_none:
            return (stmsg.Set_Class_Command_Class_Set(class_str),
                    stmsg.Set_Name_or_Class_Command_Display_Rolled_Stats(
                        strength=self.game_state.character.strength,
                        dexterity=self.game_state.character.dexterity,
                        constitution=self.game_state.character.constitution,
                        intelligence=self.game_state.character.intelligence,
                        wisdom=self.game_state.character.wisdom,
                        charisma=self.game_state.character.charisma
            ))
        else:
            return stmsg.Set_Class_Command_Class_Set(class_str),

    # This is a very hairy method on account of how much natural language processing it has to do to account for all the
    # permutations on how a user writes TAKE Item FROM Container.

    def set_name_command(self, *tokens):
        if len(tokens) == 0:
            return stmsg.Command_Bad_Syntax('SET NAME', *COMMANDS_SYNTAX['SET NAME']),
        name_parts_tests = list(map(bool, map(self.valid_name_re.match, tokens)))
        name_was_none = self.game_state.character_name is None
        if False in name_parts_tests:
            failing_parts = list()
            offset = 0
            for _ in range(0, name_parts_tests.count(False)):
                failing_part_index = name_parts_tests.index(False, offset)
                failing_parts.append(tokens[failing_part_index])
                offset = failing_part_index + 1
            return tuple(map(stmsg.Set_Name_Command_Invalid_Part, failing_parts))
        else:
            name_str = ' '.join(tokens)
            self.game_state.character_name = ' '.join(tokens)
            if self.game_state.character_class is not None and name_was_none:
                return (stmsg.Set_Name_Command_Name_Set(name_str), stmsg.Set_Name_or_Class_Command_Display_Rolled_Stats(
                            strength=self.game_state.character.strength,
                            dexterity=self.game_state.character.dexterity,
                            constitution=self.game_state.character.constitution,
                            intelligence=self.game_state.character.intelligence,
                            wisdom=self.game_state.character.wisdom,
                            charisma=self.game_state.character.charisma
                ))
            else:
                return stmsg.Set_Name_Command_Name_Set(self.game_state.character_name),

    def status_command(self, *tokens):
        if len(tokens):
            return stmsg.Command_Bad_Syntax('STATUS', *COMMANDS_SYNTAX['STATUS']),
        character = self.game_state.character
        output_args = dict()
        output_args['hit_points'] = character.hit_points
        output_args['hit_point_total'] = character.hit_point_total
        if character.character_class in ('Mage', 'Priest'):
            output_args['mana_points'] = character.mana_points
            output_args['mana_point_total'] = character.mana_point_total
        else:
            output_args['mana_points'] = None
            output_args['mana_point_total'] = None
        output_args['armor_class'] = character.armor_class
        if character.weapon_equipped or (character.character_class == 'Mage' and character.wand_equipped):
            output_args['attack_bonus'] = character.attack_bonus
            output_args['damage'] = character.damage_roll
        else:
            output_args['attack_bonus'] = 0
            output_args['damage'] = ''
        output_args['armor'] = character.armor.title if character.armor_equipped else None
        output_args['shield'] = character.shield.title if character.shield_equipped else None
        output_args['wand'] = character.wand.title if character.wand_equipped else None
        output_args['weapon'] = character.weapon.title if character.weapon_equipped else None
        output_args['is_mage'] = character.character_class == 'Mage'
        return stmsg.Status_Command_Output(**output_args),

    def take_command(self, *tokens):
        results = self._put_or_take_preproc('TAKE', 'FROM', *tokens)

        # The workhorse private method returns either a stmsg.Game_State_Message subclass object (see
        # adventuregame.game_state_messages) or a tuple of amount to take, parsed title of Item, parsed title of
        # Container, and the Container object (as a matter of convenience, it's needed by the private method & why fetch
        # it twice).
        if len(results) == 1 and isinstance(results[0], stmsg.Game_State_Message):
            return results
        else:
            # len(results) == 4 and isinstance(results[0], int) and isinstance(results[1], str)
            #     and isinstance(results[2], str) and isinstance(results[3], Container)
            take_amount, item_title, container_title, container = results

        # The following loop iterates over all the items in the Container. I use a while loop so it's possible for the
        # search to fall off the end of the loop. If that code is reached, the specified Item isn't in this Container.
        container_here_contents = list(container.items())
        index = 0
        while index < len(container_here_contents):
            item_internal_name, (item_qty, item) = container_here_contents[index]

            # This isn't the Item specified.
            if item.title != item_title:
                index += 1
                continue

            if take_amount is math.nan:
                # This *is* the Item, but the command didn't specify the quantity, so I set `take_amount` to the
                # quantity in the Container.
                take_amount = item_qty

            if take_amount > item_qty:

                # The amount specified is more than how much is in the Container, so I return an error.
                return stmsg.Take_Command_Trying_to_Take_More_than_Is_Present(container_title, container.container_type,
                                                                              item_title, take_amount, item_qty),  # tested
            elif take_amount == 1:

                # We have a match. One Item is remove from the Container and added to the Character's Inventory; and a
                # success return object is returned.
                container.remove_one(item_internal_name)
                self.game_state.character.pick_up_item(item)
                return stmsg.Take_Command_Item_or_Items_Taken(container_title, item_title, take_amount),
            else:

                # We have a match.
                if take_amount == item_qty:

                    # The amount specified is how much is here, so I delete the Item from the Container.
                    container.delete(item_internal_name)
                else:

                    # There's more in the Container than was specified, so I set the amount in the Container to the
                    # amount that was there minus the amount being taken.
                    container.set(item_internal_name, item_qty - take_amount, item)

                # The Character's Inventory is updated with the items taken, and a success object is returned.
                self.game_state.character.pick_up_item(item, qty=take_amount)
                return stmsg.Take_Command_Item_or_Items_Taken(container_title, item_title, take_amount),

            # The loop didn't find the Item on this path, so I increment the index and try again.
            index += 1

        # The loop completed without finding the Item, so it isn't present in the Container. I return an error.
        return stmsg.Take_Command_Item_Not_Found_in_Container(container_title, take_amount, container.container_type,
                                                              item_title),  # tested

    def unequip_command(self, *tokens):
        if not tokens:
            return stmsg.Command_Bad_Syntax('UNEQUIP', *COMMANDS_SYNTAX['UNEQUIP']),
        item_title = ' '.join(tokens)
        matching_item_tuple = tuple(item for _, item in self.game_state.character.list_items()
                                    if item.title == item_title)
        if not len(matching_item_tuple):
            matching_item_tuple = tuple(item for item in self.game_state.items_state.values()
                                        if item.title == item_title)
            if matching_item_tuple:
                item, = matching_item_tuple[0:1]
                return stmsg.Unequip_Command_Item_Not_Equipped(item.title, item.item_type),
            else:
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title),
        item, = matching_item_tuple[0:1]
        if item.item_type == 'armor':
            if self.game_state.character.armor_equipped is not None:
                if self.game_state.character.armor_equipped.title == item_title:
                    self.game_state.character.unequip_armor()
                    return stmsg.Various_Commands_Item_Unequipped(item_title, 'armor',
                                                                  self.game_state.character.armor_class,
                                                                  'armor class'),
                else:
                    return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'armor',
                                                                   self.game_state.character.armor_equipped.title),
            else:
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'armor'),
        elif item.item_type == 'shield':
            if self.game_state.character.shield_equipped is not None:
                if self.game_state.character.shield_equipped.title == item_title:
                    self.game_state.character.unequip_shield()
                    return stmsg.Various_Commands_Item_Unequipped(item_title, 'shield',
                                                                  self.game_state.character.armor_class,
                                                                  'armor class'),
                else:
                    return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'shield',
                                                                   self.game_state.character.shield_equipped.title),
            else:
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'shield'),
        elif item.item_type == 'wand':
            if self.game_state.character.wand_equipped is not None:
                if self.game_state.character.wand_equipped.title == item_title:
                    self.game_state.character.unequip_wand()
                    weapon_equipped = self.game_state.character.weapon_equipped
                    if weapon_equipped is not None:
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'wand',
                                                                      change_text=f"You're now attacking with your "
                                                                            f'{weapon_equipped.title}'),
                    else:
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'wand',
                                                                      change_text="You now can't attack."),
                else:
                    return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'wand'),
            else:
                return stmsg.Unequip_Command_Item_Not_Equipped(item_title, 'wand'),
        elif item.item_type == 'weapon':
            if self.game_state.character.weapon_equipped is not None:
                if self.game_state.character.weapon_equipped.title == item_title:
                    self.game_state.character.unequip_weapon()
                    if self.game_state.character.wand_equipped is not None:
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon',
                                                                      change_text="You're attacking with your wand."),
                    else:
                        return stmsg.Various_Commands_Item_Unequipped(item_title, 'weapon',
                                                                      change_text="You now can't attack."),
                else:
                    return stmsg.Unequip_Command_Item_Not_Equipped(item.title, 'weapon'),
            else:
                return stmsg.Unequip_Command_Item_Not_Equipped(item.title, 'weapon'),

    def unlock_command(self, *tokens):
        result = self._lock_unlock_open_or_close_preproc('UNLOCK', *tokens)
        if isinstance(result[0], stmsg.Game_State_Message):
            return result
        else:
            object_to_unlock, = result
        if object_to_unlock.is_locked is False:
            return stmsg.Unlock_Command_Object_Is_Already_Unlocked(object_to_unlock.title),
        else:
            object_to_unlock.is_locked = False
            return stmsg.Unlock_Command_Object_Has_Been_Unlocked(object_to_unlock.title),

