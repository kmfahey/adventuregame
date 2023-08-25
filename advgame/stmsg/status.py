#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = "StatusOutput",


class StatusOutput(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.status_command() when the
player executes it. The status line conveyed by the message property
includes the player's current and total hit points, current and total
mana points if they're a spellcaster, their attack and damage, their
armor class, their armor equipped if not a Mage, their shield equipped
if a Warrior or Priest, their Wand equipped if a Mage, and their Weapon
equipped.
    """

    __slots__ = ('hit_points', 'hit_point_total', 'armor_class', 'attack_bonus', 'damage', 'mana_points',
                 'mana_point_total', 'armor', 'shield', 'weapon', 'wand', 'character_class')

    @property
    def message(self):
        # This long message property assembles a detailed listing of the
        # player character's status, including current & max hit points,
        # current & max mana points (if a spellcaster), armor class,
        # attack & damage, and items equipped.

        # The player character's hit points.
        hp_str = f'Hit Points: {self.hit_points}/{self.hit_point_total}'

        if self.character_class in ('Mage', 'Priest'):
            # The player character's mana points if they're a Mage or a
            # Priest.
            mp_str = f'Mana Points: {self.mana_points}/{self.mana_point_total}'

        # The player character's attack bonus and damage. If they don't
        # have a weapon equipped, or (if they're a Mage) don't have a
        # wand equipped, a message to that effect is shown isntead.
        if self.weapon or self.character_class == 'Mage' and self.wand:
            atk_plussign = '+' if self.attack_bonus >= 0 else ''
            atk_dmg_str = f'Attack: {atk_plussign}{self.attack_bonus} ({self.damage} damage)'
        elif self.character_class == 'Mage':
            atk_dmg_str = 'Attack: no wand or weapon equipped'
        else:
            atk_dmg_str = 'Attack: no weapon equipped'

        # The player character's armor class.
        ac_str = f'Armor Class: {self.armor_class}'

        # The armor, shield, wand and weapon equipped strings are
        # built. If an item is present it's included (since it must be
        # allowed to the class), but a '<item type>: none' value is only
        # included if the player character is of a class that can equip
        # items of that type.
        armor_str = (f'Armor: {self.armor}' if self.armor
                     else 'Armor: none' if self.character_class != 'Mage'
                     else '')
        shield_str = (f'Shield: {self.shield}' if self.shield
                      else 'Shield: none' if self.character_class in ('Warrior', 'Priest')
                      else '')
        wand_str = (f'Wand: {self.wand}' if self.wand
                    else 'Wand: none' if self.character_class == 'Mage'
                    else '')
        weapon_str = (f'Weapon: {self.weapon}' if self.weapon else 'Weapon: none')

        # The previously defined components of the status line are
        # assembled into three hyphen-separated displays.
        points_display = f'{hp_str} - {mp_str}' if self.character_class in ('Mage', 'Priest') else hp_str
        stats_display = f'{atk_dmg_str} - {ac_str}'
        equip_display = weapon_str
        equip_display += f' - {wand_str}' if wand_str else ''
        equip_display += f' - {armor_str}' if armor_str else ''
        equip_display += f' - {shield_str}' if shield_str else ''

        # The three displays are combined in a bar-separated string and
        # returned.
        return f'{points_display} | {stats_display} | {equip_display}'

    def __init__(self, armor_class, attack_bonus, damage, weapon, hit_points, hit_point_total, armor=None, shield=None,
                 wand=None, mana_points=None, mana_point_total=None, character_class=None):
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
        self.character_class = character_class
