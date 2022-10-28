#!/usr/bin/python3


__name__ = "adventuregame.game_data"

containers_ini_config_text = """
[Wooden_Chest_1]
contents=[20xGold_Piece,1xWarhammer,1xMana_Potion]
description=This small, serviceable chest is made of wooden slat bounds within an iron framing, and features a sturdy-looking lock.
is_locked=true
is_closed=true
title=wooden chest
container_type=chest
"""

creatures_ini_config_text = """
[Kobold_Trysk]
# This creature was adapted from the Dungeons & Dragons 3rd edition _Monster Manual_, p.123.
armor_equipped=Small_Leather_Armor
base_hit_points=20
character_class=Thief
character_name=Trysk
charisma=8
constitution=10
description_dead=This diminuitive draconic humanoid is recently slain.
description=This diminuitive draconic humanoid is dressed in leather armor and has a short sword at its hip. It eyes you warily.
dexterity=13
intelligence=10
inventory_items=[1xShort_Sword,1xSmall_Leather_Armor,30xGold_Piece,1xHealth_Potion]
species=Kobold
strength=9
title=kobold
weapon_equipped=Short_Sword
wisdom=9

[Sorcerer_Ardren]
# This creature was adapted from the Dungeons & Dragons 3rd edition _Enemies & Allies_, p.55
base_hit_points=30
character_class=Thief
character_name=Ardren
charisma=18
constitution=15
description_dead=This dead half-elf is dressed in breeches but shirtless. He is recently slain and has the pallor of death.
description=Stripped to the waist and inscribed with dragon chest tattoos, this half-elf is clearly a sorcerer.
dexterity=16
intelligence=10
inventory_items=[2xMana_Potion,1xDagger,10xGold_Piece]
species=human
strength=8
title=sorcerer
weapon_equipped=dagger
wisdom=12
"""

doors_ini_config_text = """
[Room_1,2_x_Room_1,3]
title=doorway
description=This open doorway is outlined by a stone arch set into the wall.
door_type=doorway
is_locked=false
is_closed=false
closeable=false

[Room_1,2_x_Room_2,2]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_1,3_x_Room_2,2]
title=doorway
description=This open doorway is outlined by a stone arch set into the wall.
door_type=doorway
is_locked=false
is_closed=false
closeable=false

[Room_1,3_x_Room_2,3]
title=wooden door
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_1,4_x_Room_1,5]
title=wooden door
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=true
is_closed=true
closeable=true

[Room_1,4_x_Room_2,3]
title=doorway
description=This open doorway is outlined by a stone arch set into the wall.
door_type=doorway
is_locked=false
is_closed=false
closeable=false

[Room_1,5_x_Room_2,4]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_1,5_x_Room_2,5]
title=wooden door
description=This door is made of wooden planks secured together with iron divots.
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
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_2,3_x_Room_2,4]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
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
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_2,5_x_Room_3,5]
title=wooden door
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_3,2_x_Room_3,3]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
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
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_3,3_x_Room_4,2]
title=wooden door
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_3,3_x_Room_4,3]
title=wooden door
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_3,5_x_Room_3,6]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_3,5_x_Room_4,5]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_4,2_x_Room_4,3]
title=wooden door
description=This door is made of wooden planks secured together with iron divots.
door_type=wooden_door
is_locked=false
is_closed=true
closeable=true

[Room_4,3_x_Room_4,4]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true

[Room_4,4_x_Room_4,5]
title=iron door
description=This door is bound in iron plates with a small barred window set up high.
door_type=iron_door
is_locked=true
is_closed=true
closeable=true
"""

items_ini_config_text = """
[Longsword]
attack_bonus=0
damage=1d8
description=A hefty sword with a long blade, a broad hilt and a leathern grip.
item_type=weapon
title=longsword
value=15
warrior_can_use=true
weight=3

[Buckler]
armor_bonus=1
description=A small convex disk made of stiffened leather with an armstrap affixed to the inside.
item_type=shield
priest_can_use=true
title=buckler
value=15
warrior_can_use=true
weight=5

[Rapier]
attack_bonus=0
damage=1d8
description=A slender, sharply pointed blade with a basket hilt.
item_type=weapon
thief_can_use=true
title=rapier
value=25
warrior_can_use=true
weight=2

[Mace]
attack_bonus=0
damage=1d6
description=A hefty, blunt instrument with a dully-spiked weighted metal head.
item_type=weapon
priest_can_use=true
title=mace
value=5
warrior_can_use=true
weight=4

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
description=A broad panel of leather-bound steel with a metal rim that is useful for sheltering behind.
item_type=shield
priest_can_use=true
title=steel shield
value=10
warrior_can_use=true
weight=6

[Studded_Leather]
armor_bonus=2
description=A suit of fire-hardened leather plates and padding that provides some protection from attack.
item_type=armor
thief_can_use=true
title=studded leather armor
value=45
warrior_can_use=true
weight=15

[Scale_Mail]
armor_bonus=4
description=A suit of small steel scales linked together in a flexible plating that provides strong protection from attack.
item_type=armor
priest_can_use=true
title=scale mail armor
value=50
warrior_can_use=true
weight=45

[Robe]
armor_bonus=0
description=A long flowing garment that is traditional for mages but provides paltry protection.
item_type=armor
mage_can_use=true
title=robe
value=1
weight=4

[Health_Potion]
description=A small, stoppered bottle that contains a pungeant but drinkable red liquid with a discernable magic aura.
item_type=consumable
mage_can_use=true
priest_can_use=true
thief_can_use=true
hit_points_recovered=20
title=health potion
value=25
warrior_can_use=true
weight=.1

[Mana_Potion]
description=A small, stoppered bottle that contains a pungeant but drinkable blue liquid with a discernable magic aura.
item_type=consumable
mage_can_use=true
priest_can_use=true
title=health potion
mana_points_recovered=20
value=25
weight=.1

[Magic_Sword]
attack_bonus=3
damage=1d12+3
description=A magic sword with a palpable magic aura and an unnaturally sharp blade.
item_type=weapon
title=magic sword
value=100
warrior_can_use=true
weight=3

[Magic_Wand]
attack_bonus=3
damage=3d8+5
description=A palpably magical tapered length of polished ash wood tipped with a glowing red carnelian gem.
item_type=wand
mage_can_use=true
title=magic wand
value=100
weight=0.5

[Short_Sword]
attack_bonus=0
damage=1d8
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

[Small_Leather_Armor]
armor_bonus=2
description=A suit of leather armor designed for a humanoid of 4 feet in height.
item_type=armor
title=small leather armor
value=10
weight=7.5

[Gold_Piece]
description=A small shiny gold coin imprinted with an indistinct bust on one side and a worn state seal on the other.
item_type=coin
title=gold piece
value=1
weight=0.02

[Warhammer]
attack_bonus=0
damage=1d8
description=A heavy hammer with a heavy iron head with a tapered striking point and a long leather-wrapped haft.
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
description=This small workmanlike brass key can be used to lock or unlock chests.
item_type=key
title=door key
weight=0.16
"""

rooms_ini_config_text = """
[Room_2,1]
description=Antechamber of dungeon
entrance=true
north_exit=Room_2,2

[Room_1,2]
description=Dungeon room
east_exit=Room_2,2
north_exit=Room_1,3

[Room_2,2]
description=Dungeon room
east_exit=Room_3,2
south_exit=Room_2,1
west_exit=Room_1,2

[Room_3,2]
description=Dungeon room
east_exit=Room_4,2
north_exit=Room_3,3
west_exit=Room_2,2

[Room_4,2]
description=Dungeon room
north_exit=Room_4,3
west_exit=Room_3,2

[Room_1,3]
description=Dungeon room
east_exit=Room_2,2
south_exit=Room_1,2

[Room_2,3]
description=Dungeon room
north_exit=Room_2,4
west_exit=Room_1,3

[Room_3,3]
description=Dungeon room
east_exit=Room_4,2
north_exit=Room_3,4
south_exit=Room_3,2

[Room_4,3]
description=Dungeon room
north_exit=Room_4,4
south_exit=Room_4,2
west_exit=Room_3,3

[Room_1,4]
description=Dungeon room
east_exit=Room_2,3
north_exit=Room_1,5

[Room_2,4]
description=Dungeon room
east_exit=Room_3,4
north_exit=Room_2,5
south_exit=Room_2,3
west_exit=Room_1,5

[Room_3,4]
description=Dungeon room
south_exit=Room_3,3
west_exit=Room_2,4

[Room_4,4]
description=Dungeon room
north_exit=Room_4,5
south_exit=Room_4,3

[Room_1,5]
description=Dungeon room
east_exit=Room_2,5
south_exit=Room_1,4

[Room_2,5]
description=Dungeon room
east_exit=Room_3,5
south_exit=Room_2,4
west_exit=Room_1,5

[Room_3,5]
description=Dungeon room
east_exit=Room_4,5
north_exit=Room_3,6
west_exit=Room_2,5

[Room_4,5]
description=Dungeon room
south_exit=Room_4,4
west_exit=Room_3,5

[Room_3,6]
description=Dungeon exit
exit=true
south_exit=Room_3,5

"""

