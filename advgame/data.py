#!/usr/bin/python3

import os

from dataclasses import dataclass
from tempfile import mkstemp


__all__ = ("ini_file_texts",)


@dataclass
class IniFileTexts:
    __slots__ = (
        "filenames",
        "_items_text",
        "_doors_text",
        "_containers_text",
        "_creatures_text",
        "_rooms_text",
    )

    ITEMS_INI = 0
    DOORS_INI = 1
    CONTAINERS_INI = 2
    CREATURES_INI = 3
    ROOMS_INI = 4

    def __init__(
        self, _items_text, _doors_text, _containers_text, _creatures_text, _rooms_text
    ):
        self.filenames = dict()
        self._items_text = _items_text
        self._doors_text = _doors_text
        self._containers_text = _containers_text
        self._creatures_text = _creatures_text
        self._rooms_text = _rooms_text

    def _text_to_tempfile_name(self, ini_file_const, ini_file_text):
        file_descr, tempfile_name = mkstemp(".ini.")
        os.close(file_descr)
        with open(tempfile_name, "w") as tmp_fh:
            tmp_fh.write(ini_file_text)
        self.filenames[ini_file_const] = tempfile_name
        return tempfile_name

    def get_ini_tmpfile_name(self, ini_file_const):
        match ini_file_const:
            case self.ITEMS_INI:
                return self._text_to_tempfile_name(self.ITEMS_INI, self._items_text)
            case self.DOORS_INI:
                return self._text_to_tempfile_name(self.DOORS_INI, self._doors_text)
            case self.CONTAINERS_INI:
                return self._text_to_tempfile_name(self.CONTAINERS_INI, self._containers_text)
            case self.CREATURES_INI:
                return self._text_to_tempfile_name(self.CREATURES_INI, self._creatures_text)
            case self.ROOMS_INI:
                return self._text_to_tempfile_name(self.ROOMS_INI, self._rooms_text)

    def remove_tempfile(self, ini_file_const):
        os.remove(self.filenames[ini_file_const])


ITEMS_INI_FILE_TEXT = """
# The weapons in this file are adapted from the Dungeons & Dragons 3rd
# edition weapons. They were accessed online using the _System Reference
# Document_. They can be viewed at <http://dndsrd.net/weapons.html>.
#
# The armor and shields in this file are adapted from the Dungeons &
# Dragons 3rd edition armor and shields. They were accessed online
# using the _System Reference Document_. They can be viewed at
# <http://dndsrd.net/armor.html>.

[Longsword]
attack_bonus=0
damage=1d8
description=A hefty sword with a long blade, a broad hilt and a leathern grip.
item_type=weapon
title=longsword
value=15
warrior_can_use=true
weight=4

[Buckler]
armor_bonus=1
description=A small convex disk made of stiffened leather with an armstrap \
affixed to the inside.
item_type=shield
priest_can_use=true
title=buckler
value=15
warrior_can_use=true
weight=5

[Rapier]
attack_bonus=0
damage=1d6
description=A slender, sharply pointed blade with a basket hilt.
item_type=weapon
thief_can_use=true
title=rapier
value=20
warrior_can_use=true
weight=2

[Magic_Rapier]
attack_bonus=3
damage=1d6+3
description=A slender, sharply pointed blade with a basket hilt.
item_type=weapon
thief_can_use=true
title=magic rapier
value=20
warrior_can_use=true
weight=2

[Magic_Mace]
attack_bonus=3
damage=1d8+3
description=An enchanted mace with a too-shiny weighted metal head and a fine \
leather-wrapped haft.
item_type=weapon
priest_can_use=true
title=magic heavy mace
value=12
warrior_can_use=true
weight=8

[Light_Mace]
attack_bonus=0
damage=1d6
description=A light blunt instrument with a spiked metal head.
item_type=weapon
priest_can_use=true
title=light mace
value=5
warrior_can_use=true
weight=4

[Heavy_Mace]
attack_bonus=0
damage=1d8
description=A hefty, blunt instrument with a dully-spiked weighted metal head.
item_type=weapon
priest_can_use=true
title=mace
value=12
warrior_can_use=true
weight=8

[Staff]
attack_bonus=0
damage=1d6
description=A balanced pole 6 feet in length with metal-shod ends.
item_type=weapon
mage_can_use=true
title=staff
value=0.2
warrior_can_use=true
weight=4

[Steel_Shield]
armor_bonus=2
description=A broad panel of leather-bound steel with a metal rim that is \
useful for sheltering behind.
item_type=shield
priest_can_use=true
title=steel shield
value=10
warrior_can_use=true
weight=6

[Breastplate]
armor_bonus=3
description=A suit of fire-hardened leather plates and padding that provides \
some protection from attack.
item_type=armor
thief_can_use=true
title=studded leather armor
value=45
warrior_can_use=true
weight=15

[Studded_Leather]
armor_bonus=3
description=A suit of fire-hardened leather plates and padding that provides \
some protection from attack.
item_type=armor
thief_can_use=true
title=studded leather armor
value=45
warrior_can_use=true
weight=15

[Scale_Mail]
armor_bonus=4
description=A suit of small steel scales linked together in a flexible \
plating that provides strong protection from attack.
item_type=armor
priest_can_use=true
title=scale mail armor
value=50
warrior_can_use=true
weight=45

[Health_Potion]
description=A small, stoppered bottle that contains a pungeant but drinkable \
red liquid with a discernable magic aura.
hit_points_recovered=20
item_type=potion
mage_can_use=true
priest_can_use=true
thief_can_use=true
title=health potion
value=25
warrior_can_use=true
weight=.1

[Mana_Potion]
description=A small, stoppered bottle that contains a pungeant but drinkable \
blue liquid with a discernable magic aura.
item_type=potion
mage_can_use=true
mana_points_recovered=20
priest_can_use=true
title=mana potion
value=25
weight=.1

[Magic_Sword]
attack_bonus=3
damage=1d8+3
description=A fancy sword with a palpable magic aura and an unnaturally sharp \
blade.
item_type=weapon
title=magic sword
value=100
warrior_can_use=true
weight=3

[Magic_Wand]
attack_bonus=3
damage=2d6+5
description=A palpably magical tapered length of polished ash wood tipped \
with a glowing red carnelian gem.
item_type=wand
mage_can_use=true
title=magic wand
value=100
weight=0.5

[Short_Sword]
attack_bonus=0
damage=1d6
description=A smaller sword with a short blade and a narrower grip.
item_type=weapon
thief_can_use=true
title=short sword
value=10
warrior_can_use=true
weight=2

[Dagger]
attack_bonus=0
damage=1d4
description=A simple bladed weapon with a plain iron hilt and a notched edge.
item_type=weapon
mage_can_use=true
priest_can_use=true
thief_can_use=true
title=dagger
value=2
warrior_can_user=true
weight=1

[Small_Studded_Leather]
armor_bonus=3
description=A suit of leather plates fitted with iron studs designed for a \
humanoid that's 4 feet tall.
item_type=armor
title=small studded leather armor
value=45
weight=15


[Small_Leather_Armor]
armor_bonus=2
description=A suit of leather armor designed for a humanoid of 4 feet in \
height.
item_type=armor
title=small leather armor
value=10
weight=7.5

[Gold_Coin]
description=A small shiny gold coin imprinted with an indistinct bust on one \
side and a worn state seal on the other.
item_type=coin
title=gold coin
value=1
weight=0.02

[Morningstar]
attack_bonus=0
damage=1d8
description=A long-hafted iron cudgel-like weapon with a round, spiked \
striking head.
item_type=weapon
priest_can_use==true
title=morningstar
warrior_can_use=true
weight=5

[Warhammer]
attack_bonus=0
damage=1d8
description=A hammer with a pointed iron head and a long leather-wrapped haft.
item_type=weapon
priest_can_use==true
title=warhammer
warrior_can_use=true
weight=5

[Door_Key]
description=This large ornate brass key can be used to lock or unlock doors.
item_type=key
title=door key
weight=0.16

[Chest_Key]
description=This small workmanlike brass key can be used to lock or unlock \
chests.
item_type=key
title=chest key
weight=0.16

[Magic_Scale_Mail]
armor_bonus=6
description=A shining suit of small mithral scales linked together in fine \
dwarven craftsmanship.
item_type=armor
priest_can_use=true
title=magic scale mail armor
value=50
warrior_can_use=true
weight=45

[Mithral_Chain_Shirt]
armor_bonus=5
description=A suit of chainmail made of tiny, finely-shaped mithral links.
item_type=armor
priest_can_use=true
title=scale mail armor
value=50
warrior_can_use=true
rogue_can_use=true
weight=45

# These miscellaneous goods are inspired by the "Trinkets" 2-page table
# in the 5th ed. D&D Player's Handbook, pp 160-161.

[Music_Box]
description=A figurine of a dancer on a base & under a glass dome, with a \
turnkey on one side of the base.
item_type=oddment
title=music box
value=25
weight=0.5

[Bag_of_Glass_Jewels]
description=A finely-worked leather pouch containing a handful of cut-glass \
false gems.
item_type=oddment
title=bag of glass jewels
value=12.5
weight=0.5

[Conch_Shell]
description=A off-white conch shell with a hole drilled in one end and fitted \
with a loop of leather thong.
item_type=oddment
title=conch
value=0.1
weight=1

[China_Doll]
description=A china doll in a miniature fine dress with jewels for eyes.
item_type=oddment
title=china doll
value=25
weight=1

[Wooden_Flute]
description=A small, delicately-carved wooden flute.
item_type=oddment
title=wooden flute
value=10
weight=1

[Tin_Urn]
description=An urn large enough to hold a spray of flowers, cast of tin and \
inscribed with a scrollwork pattern.
item_type=oddment
title=tin urn
value=10
weight=1

[Dragon_Statuette]
description=A small statuette of dragon in a seated post with its wings \
arched behind it.
item_type=oddment
title=dragon statuette
value=50
weight=5

[Bronze_Pentacle]
description=A weighted bronze disc inscribed with a pentacle on one face; the \
other face is smooth and blank.
item_type=oddment
title=bronze pentacle
value=25
weight=2.5

[Small_Scroll]
description=A small scroll bound with a cord; when unrolled, it proves to be \
draft orders addressed to an unfamiliar name to the army of a nation you've \
never heard of.
item_type=oddment
title=small scroll
value=0.1
weight=1

[Animal_Tusk]
description=A single tusk as long as your hand, taken from the skull of an \
unknown animal.
item_type=oddment
title=animal tusk
value=0.1
weight=1

[Ivory_Silhouette]
description=A silhouette of an elven women impressed upon a convex disk of \
ivory set in a silver setting.
item_type=oddment
title=ivory silhouette
value=25
weight=0.25

[Pack_of_Cards]
description=A pack of playing cards in a tin case, with finely illustrated \
face cards and patterned backs.
item_type=oddment
title=pack of cards
value=25
weight=0.25

[Glass_Orb]
description=A heavy, translucent glass orb shaped from bluish glass.
item_type=oddment
title=glass orb
value=10
weight=1

[Tapestry_Scrap]
description=A hand-sized scrap torn from a larger tapestry, featuring a \
portion of a curlicue pattern.
item_type=oddment
title=tapestry scrap
value=0.1
weight=0.5

# End oddments section inspired by the 5th ed. D&D Player's handbook.
"""

DOORS_INI_FILE_TEXT = """
[Room_1,2_x_Room_1,3]
title=doorway
description=This open doorway is outlined by a stone arch set into the wall.
door_type=doorway
is_locked=false
is_closed=false
closeable=false

[Room_1,2_x_Room_2,2]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=false
is_closed=true
closeable=true

[Room_1,3_x_Room_2,3]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_1,4_x_Room_1,5]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=true
is_closed=true
closeable=true

[Room_1,5_x_Room_2,5]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_2,1_x_Room_2,2]
title=doorway
description=This open doorway is outlined by a stone arch set into the wall.
door_type=doorway
is_locked=false
is_closed=false
closeable=false

[Room_2,2_x_Room_3,2]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=false
is_closed=true
closeable=true

[Room_2,3_x_Room_2,4]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=false
is_closed=true
closeable=true

[Room_2,4_x_Room_2,5]
title=doorway
description=This open doorway is outlined by a stone arch set into the wall.
door_type=doorway
is_locked=false
is_closed=false
closeable=false

[Room_2,4_x_Room_3,4]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_2,5_x_Room_3,5]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_3,2_x_Room_3,3]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_3,2_x_Room_4,2]
title=doorway
description=This open doorway is outlined by a stone arch set into the wall.
door_type=doorway
is_locked=false
is_closed=false
closeable=false

[Room_3,3_x_Room_3,4]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_1,4_x_Room_2,4]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_3,3_x_Room_4,3]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_3,5_x_Room_3,6]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_3,5_x_Room_4,5]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=false
is_closed=true
closeable=true

[Room_4,2_x_Room_4,3]
title=wooden door
description=This door is made of wooden planks secured together with iron \
divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_4,3_x_Room_4,4]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=false
is_closed=true
closeable=true

[Room_4,4_x_Room_4,5]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_locked=false
is_closed=true
closeable=true

[Room_3,6_x_Exit]
title=iron door
description=This door is bound in iron plates with a small barred window set \
up high.
door_type=iron_door
is_exit=true
is_locked=false
is_closed=true
closeable=true
"""

CONTAINERS_INI_FILE_TEXT = """
[Wooden_Chest_1]
contents=[1xTapestry_Scrap,20xGold_Coin,1xMagic_Scale_Mail,1xMagic_Mace,\
1xScale_Mail,1xLight_Mace,1xMana_Potion]
description=This small, serviceable chest is made of wooden slats bound \
within an iron frame, and features a sturdy-looking lock.
is_locked=true
is_closed=true
title=wooden chest
container_type=chest

[Wooden_Chest_2]
contents=[1xSmall_Scroll,1xMagic_Wand,40xGold_Coin,1xDagger,1xBreastplate,\
1xRapier,2xMana_Potion,1xHealth_Potion]
description=This small, serviceable chest is made of wooden slats bound \
within an iron frame, and features a sturdy-looking lock.
is_locked=false
is_closed=true
title=wooden chest
container_type=chest

[Wooden_Chest_3]
contents=[1xStudded_Leather,1xMana_Potion,1xShort_Sword,1xWarhammer,\
1xBreastplate,1xTin_Urn,1xMagic_Rapier,21xGold_Coin,1xMana_Potion]
description=This small, serviceable chest is made of wooden slats bound \
within an iron frame, and features a sturdy-looking lock.
is_locked=false
is_closed=true
title=wooden chest
container_type=chest

[Wooden_Chest_4]
contents=[1xBag_of_Glass_Jewels,1xMusic_Box,1xSmall_Scroll,1xLight_Mace,\
1xDagger,1xTin_Urn,15xGold_Coin,1xHealth_Potion]
description=This small, serviceable chest is made of wooden slats bound \
within an iron frame, and features a sturdy-looking lock.
is_locked=true
is_closed=true
title=wooden chest
container_type=chest

[Wooden_Chest_5]
contents=[1xHeavy_Mace,1xConch_Shell,1xSmall_Scroll,20xGold_Coin,1xMana_Potion]
description=This small, serviceable chest is made of wooden slats bound \
within an iron frame, and features a sturdy-looking lock.
is_locked=false
is_closed=true
title=wooden chest
container_type=chest
"""

CREATURES_INI_FILE_TEXT = """
[Kobold_1]
# This creature was adapted from the Dungeons & Dragons 3rd edition
# _Monster Manual_, p.123.
armor_equipped=Small_Leather_Armor
base_hit_points=20
character_class=Thief
character_name=Trysk
charisma=8
constitution=10
description_dead=This diminuitive draconic humanoid is recently slain.
description=This diminuitive draconic humanoid is dressed in leather armor \
and has a short sword at its hip. They eye you warily.
dexterity=13
intelligence=10
inventory_items=[1xShort_Sword,1xSmall_Leather_Armor,30xGold_Coin,\
1xHealth_Potion]
species=Kobold
strength=9
title=kobold
weapon_equipped=Short_Sword
wisdom=9

[Kobold_2]
# This creature was adapted from the Dungeons & Dragons 3rd edition
# _Races of the Dragon_, p.144.
armor_equipped=Small_Leather_Armor
base_hit_points=27
character_class=Warrior
character_name=Ner
charisma=8
constitution=10
description_dead=This small scaled draconic humanoid died in combat.
description=This short scaled humanoid wears leather armor and has a light \
mace at the ready. They're on guard at your sudden presence.
dexterity=13
intelligence=10
inventory_items=[1xLight_Mace,1xBuckler,1xSmall_Leather_Armor,100xGold_Coin,\
2xHealth_Potion]
species=Kobold
strength=10
title=kobold
shield_equipped=Buckler
weapon_equipped=Light_Mace
wisdom=9

[Kobold_3]
# This creature was adapted from the Dungeons & Dragons 3rd edition
# _Races of the Dragon_, p.144.
armor_equipped=Small_Leather_Armor
base_hit_points=22
character_class=Thief
character_name=Ner
charisma=9
constitution=10
description_dead=This small scaled draconic humanoid died in combat.
description=This small scaled humanoid wears leather armor and trains a short \
sword on you. They're emitting a low growl.
dexterity=10
intelligence=14
inventory_items=[1xShort_Sword,1xBuckler,1xSmall_Leather_Armor,15xGold_Coin,\
1xMana_Potion]
species=Kobold
strength=6
title=kobold
shield_equipped=Buckler
weapon_equipped=Short_Sword
wisdom=11

[Goblin]
# This creature was adapted from the Dungeons & Dragons
# 3rd ed. _System Reference Document_. It can be found at
# <http://dndsrd.net/monstersG.html>.
armor_equipped=Small_Studded_Leather
base_hit_points=22
character_class=Thief
character_name=Trask
charisma=6
constitution=12
description_dead=This hairy, squat humanoid died in combat.
description=This small scaled humanoid wears leather armor and is training a \
short sword on you. They're emitting a low growl.
dexterity=13
intelligence=10
inventory_items=[1xShort_Sword,1xBuckler,1xSmall_Studded_Leather,15xGold_Coin,\
1xMana_Potion]
species=Goblin
strength=11
title=goblin
shield_equipped=Buckler
weapon_equipped=Short_Sword
wisdom=9

[Bugbear]
# This creature was adapted from the Dungeons & Dragons
# 3rd ed. _System Reference Document_. It can be found at
# <http://dndsrd.net/monstersBtoC.html>.
armor_equipped=Scale_Mail
base_hit_points=22
character_class=Warrior
character_name=Agk
charisma=9
constitution=13
description_dead=This hulking furry humanoid is recently slain.
description=This large furred humanoid has a snoutlike face and a mean \
expression. He hefts his weapon and eyes you warily.
dexterity=12
intelligence=10
inventory_items=[1xMorningstar,1xSteel_Shield,1xScale_Mail,30xGold_Coin,\
1xHealth_Potion]
species=Bugbear
strength=15
title=bugbear
shield_equipped=Steel_Shield
weapon_equipped=Morningstar
wisdom=10
"""

ROOMS_INI_FILE_TEXT = """
[Room_2,1]
description=You're in a debris-strewn old room, at the bottom of a long shaft \
down which you fell. There's no climbing back up there.
is_entrance=true
north_door=Room_2,2

[Room_1,2]
description=The path corners here. This room has the same vaulted ceiling as \
the last. The floors are clear of dust.
east_door=Room_2,2
items_here=[1xChest_Key]
north_door=Room_1,3

[Room_2,2]
description=The vault branches here, doors leading away in both directions. \
The room's ceiling is arched and the stonework looks ancient.
east_door=Room_3,2
south_door=Room_2,1
west_door=Room_1,2
items_here=[1xAnimal_Tusk]

[Room_3,2]
description=This room has three exits. You think you hear activity in the \
distance.
east_door=Room_4,2
items_here=[1xMagic_Rapier]
north_door=Room_3,3
west_door=Room_2,2

[Room_4,2]
creature_here=Kobold_1
description=This room has seen recent use. An empty weapon rack stands in the \
corner.
items_here=[1xChina_Doll,1xLight_Mace,1xMagic_Sword]
north_door=Room_4,3
west_door=Room_3,2

[Room_1,3]
container_here=Wooden_Chest_1
description=The path turns another corner here. A nest of discarded fabrics \
in the corner suggests some creature recently bedded down in this room.
east_door=Room_2,3
south_door=Room_1,2

[Room_2,3]
creature_here=Kobold_3
description=This room has three more nests in each of three corners of the \
room, and the remains of someone's cooking in the fourth.
items_here=[1xMana_Potion,1xSteel_Shield,1xTin_Urn]
north_door=Room_2,4
west_door=Room_1,3

[Room_3,3]
container_here=Wooden_Chest_2
description=A few of the panels of masonry from this room's arched ceiling \
have fallen in, but the ceiling still seems sound.
east_door=Room_4,3
items_here=[1xTin_Urn,1xSmall_Scroll,1xMana_Potion]
north_door=Room_3,4
south_door=Room_3,2

[Room_4,3]
description=Three doors lead away from this room. A heap of disused garments \
lies in the corner.
items_here=[1xDoor_Key]
north_door=Room_4,4
south_door=Room_4,2
west_door=Room_3,3

[Room_1,4]
description=This room has a heap of bones in the corner-- many of them look \
recetly chewed.
east_door=Room_2,4
items_here=[1xChest_Key]
north_door=Room_1,5

[Room_2,4]
description=Two creatures with different handwritings had a conversation in \
chalk on the wall of this room, but you can't read the language.
east_door=Room_3,4
items_here=[1xDoor_Key,1xMithral_Chain_Shirt]
north_door=Room_2,5
south_door=Room_2,3
west_door=Room_1,4

[Room_3,4]
container_here=Wooden_Chest_3
description=The remains of a cookfire linger in the corner, and the roof is \
stained with soot. Several chewed bones sit by it.
south_door=Room_3,3
west_door=Room_2,4

[Room_4,4]
creature_here=Kobold_2
description=Several battle-damaged suits of chainmail and plate armor are \
lying about in this room, along with a few different pairs of pliers and \
awls, as though someone was trying to repair them.
north_door=Room_4,5
south_door=Room_4,3

[Room_1,5]
container_here=Wooden_Chest_4
description=Two recently-used sleeping pallets are set up on opposite sides \
of this room: a small one and one sized for someone taller than you.
east_door=Room_2,5
items_here=[1xScale_Mail,1xTapestry_Scrap,1xHealth_Potion]
south_door=Room_1,4

[Room_2,5]
creature_here=Goblin
description=Several different hands have drawn chalk graffiti on the north \
wall of this room, in a language you can't read.
east_door=Room_3,5
south_door=Room_2,4
west_door=Room_1,5

[Room_3,5]
creature_here=Bugbear
description=This room has fresher air than the others; a draft is blowing \
through the window of the door in the north wall.
east_door=Room_4,5
items_here=[1xSmall_Leather_Armor]
north_door=Room_3,6
west_door=Room_2,5

[Room_4,5]
container_here=Wooden_Chest_5
description=This room's east and north walls feature several long, arcing \
scratches, as though someone was swinging a sword around recklessly at some \
point.
south_door=Room_4,4
west_door=Room_3,5

[Room_3,6]
description=This room has fresh air. You can see sunlight through the window \
in the north door.
is_exit=true
items_here=[1xChina_Doll,1xBronze_Pentacle]
south_door=Room_3,5
north_door=Exit
"""


ini_file_texts = IniFileTexts(
    ITEMS_INI_FILE_TEXT,
    DOORS_INI_FILE_TEXT,
    CONTAINERS_INI_FILE_TEXT,
    CREATURES_INI_FILE_TEXT,
    ROOMS_INI_FILE_TEXT,
)
