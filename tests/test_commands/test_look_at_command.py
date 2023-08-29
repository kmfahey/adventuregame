#!/usr/bin/python3

from unittest import TestCase

from advgame import (
    CommandProcessor,
    ContainersState,
    CreaturesState,
    Door,
    DoorsState,
    GameState,
    InternalError,
    ItemsState,
    RoomsState,
)
from advgame.stmsg.command import BadSyntaxGSM
from advgame.stmsg.lookat import (
    FoundContainerHereGSM,
    FoundCreatureHereGSM,
    FoundDoorOrDoorwayGSM,
    FoundItemOrItemsHereGSM,
    FoundNothingGSM,
)
from advgame.stmsg.various import (
    AmbiguousDoorSpecifierGSM,
    ContainerNotFoundGSM,
    DoorNotPresentGSM,
)

from ..context import (
    containers_ini_config,
    items_ini_config,
    doors_ini_config,
    creatures_ini_config,
    rooms_ini_config,
)


__all__ = (
    "Test_Look_At_1",
    "Test_Look_At_2",
)


class Test_Look_At_1(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        self.doors_state = DoorsState(**doors_ini_config.sections)
        self.containers_state = ContainersState(
            self.items_state, **containers_ini_config.sections
        )
        self.creatures_state = CreaturesState(
            self.items_state, **creatures_ini_config.sections
        )
        self.rooms_state = RoomsState(
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
            **rooms_ini_config.sections,
        )
        self.game_state = GameState(
            self.rooms_state,
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
        )
        self.command_processor = CommandProcessor(self.game_state)
        self.game_state.character_name = "Niath"
        self.game_state.character_class = "Warrior"
        self.game_state.game_has_begun = True
        self.game_state.character.pick_up_item(self.items_state.get("Longsword"))
        self.game_state.character.pick_up_item(self.items_state.get("Studded_Leather"))
        self.game_state.character.pick_up_item(self.items_state.get("Steel_Shield"))
        self.game_state.character.equip_weapon(self.items_state.get("Longsword"))
        self.game_state.character.equip_armor(self.items_state.get("Studded_Leather"))
        self.game_state.character.equip_shield(self.items_state.get("Steel_Shield"))
        (
            _,
            self.gold_coin,
        ) = self.command_processor.game_state.rooms_state.cursor.container_here.get(
            "Gold_Coin"
        )

    def test_look_at_1(self):
        result = self.command_processor.process("look at kobold")
        self.assertIsInstance(result[0], FoundCreatureHereGSM)
        self.assertEqual(
            result[0].creature_description,
            self.game_state.rooms_state.cursor.creature_here.description,
        )
        self.assertEqual(
            result[0].message,
            self.game_state.rooms_state.cursor.creature_here.description,
        )

    def test_look_at_2(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = (
            self.command_processor.game_state.rooms_state.cursor.creature_here.convert_to_corpse()
        )
        result = self.command_processor.process("look at kobold corpse")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(result[0].container_type, "corpse")
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} "
            + "They have 30 gold coins, a health potion, a short sword, and a "
            + "small leather armor on them.",
        )

    def test_look_at_3(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} "
            + "It is closed and locked.",
        )

    def test_look_at_4(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} "
            + "It is closed but unlocked.",
        )

    def test_look_at_5(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} "
            + "It is unlocked and open. It contains 20 gold coins, a health "
            + "potion, a magic wand, a mana potion, a scale mail armor, a "
            + "steel shield, and a warhammer.",
        )

    def test_look_at_6(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        with self.assertRaises(InternalError):
            self.command_processor.process("look at wooden chest")

    def test_look_at_7(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = True
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} It is closed.",
        )

    def test_look_at_8(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = False
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} "
            + "It is open. It contains 20 gold coins, a health potion, a "
            + "magic wand, a mana potion, a scale mail armor, a steel shield, "
            + "and a warhammer.",
        )

    def test_look_at_9(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = True
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} "
            + "It is locked.",
        )

    def test_look_at_10(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = False
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description} "
            + "It is unlocked.",
        )

    def test_look_at_11(self):
        self.game_state.rooms_state.cursor.container_here.is_locked = None
        self.game_state.rooms_state.cursor.container_here.is_closed = None
        result = self.command_processor.process("look at wooden chest")
        self.assertIsInstance(result[0], FoundContainerHereGSM)
        self.assertEqual(
            result[0].container_description,
            self.game_state.rooms_state.cursor.container_here.description,
        )
        self.assertEqual(
            result[0].is_locked,
            self.game_state.rooms_state.cursor.container_here.is_locked,
        )
        self.assertEqual(
            result[0].is_closed,
            self.game_state.rooms_state.cursor.container_here.is_closed,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.container_here.description}",
        )

    def test_look_at_12(self):
        result = self.command_processor.process("look at kobold")
        self.assertIsInstance(result[0], FoundCreatureHereGSM)
        self.assertEqual(
            result[0].creature_description,
            self.game_state.rooms_state.cursor.creature_here.description,
        )
        self.assertEqual(
            result[0].message,
            f"{self.game_state.rooms_state.cursor.creature_here.description}",
        )

    def test_look_at_13(self):
        result = self.command_processor.process("look at north iron door")
        self.assertIsInstance(result[0], FoundDoorOrDoorwayGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertIsInstance(result[0].door, Door)
        self.assertEqual(
            result[0].message,
            "This door is bound in iron plates with a small barred window set "
            + "up high. It is set in the north wall. It is closed but "
            + "unlocked.",
        )


class Test_Look_At_2(TestCase):
    def __init__(self, *argl, **argd):
        super().__init__(*argl, **argd)
        self.maxDiff = None

    def setUp(self):
        self.items_state = ItemsState(**items_ini_config.sections)
        self.doors_state = DoorsState(**doors_ini_config.sections)
        containers_ini_config.sections["Wooden_Chest_1"]["contents"] = (
            "[20xGold_Coin,1xWarhammer,1xMana_Potion,"
            + "1xHealth_Potion,1xSteel_Shield,1xScale_Mail,1xMagic_Wand]"
        )
        self.containers_state = ContainersState(
            self.items_state, **containers_ini_config.sections
        )
        self.creatures_state = CreaturesState(
            self.items_state, **creatures_ini_config.sections
        )
        self.rooms_state = RoomsState(
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
            **rooms_ini_config.sections,
        )
        self.game_state = GameState(
            self.rooms_state,
            self.creatures_state,
            self.containers_state,
            self.doors_state,
            self.items_state,
        )
        self.command_processor = CommandProcessor(self.game_state)
        self.command_processor.game_state.character_name = "Lidda"
        self.command_processor.game_state.character_class = "Thief"
        self.game_state.game_has_begun = True

    def test_look_at_1(self):
        result = self.command_processor.process("look at")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("look at on")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("look at in")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("look at mana potion in")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("look at health potion on")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("look at health potion on wooden chest")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        result = self.command_processor.process("look at mana potion in kobold corpse")
        self.assertIsInstance(result[0], BadSyntaxGSM)
        self.assertEqual(result[0].command, "LOOK AT")
        self.assertEqual(
            result[0].message,
            "LOOK AT command: bad syntax. Should be 'LOOK\u00A0AT\u00A0<item\u00A0name>', "
            + "'LOOK\u00A0AT\u00A0<item\u00A0name>\u00A0IN\u00A0<chest\u00A0name>', "
            + "'LOOK\u00A0AT\u00A0<item\u00A0name>\u00A0IN\u00A0INVENTORY', "
            + "'LOOK\u00A0AT\u00A0<item\u00A0name>\u00A0ON\u00A0<corpse\u00A0name>', "
            + "'LOOK\u00A0AT\u00A0<compass\u00A0direction>\u00A0DOOR', or "
            + "'LOOK\u00A0AT\u00A0<compass\u00A0direction>\u00A0DOORWAY'.",
        )

    def test_look_at_2(self):
        self.command_processor.game_state.rooms_state.cursor.container_here = None
        result = self.command_processor.process("look at mana potion in wooden chest")
        self.assertIsInstance(result[0], ContainerNotFoundGSM)
        self.assertEqual(result[0].container_not_found_title, "wooden chest")
        self.assertEqual(result[0].message, "There is no wooden chest here.")

    def test_look_at_3(self):
        result = self.command_processor.process("look at gold coin in wooden chest")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 20)
        self.assertEqual(
            result[0].item_description,
            "A small shiny gold coin imprinted with an indistinct bust on one "
            + "side and a worn state seal on the other.",
        )
        self.assertEqual(
            result[0].message,
            "A small shiny gold coin imprinted with an indistinct bust on one "
            + "side and a worn state seal on the other. There are 20 in the "
            + "wooden chest.",
        )

    def test_look_at_4(self):
        result = self.command_processor.process("look at warhammer in wooden chest")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A heavy hammer with a heavy iron head with a tapered striking "
            + "point and a long leather-wrapped haft. Its attack bonus is +0 "
            + "and its damage is 1d8. Warriors and priests can use this.",
        )
        self.assertEqual(
            result[0].message,
            "A heavy hammer with a heavy iron head with a tapered striking "
            + "point and a long leather-wrapped haft. Its attack bonus is +0 "
            + "and its damage is 1d8. Warriors and priests can use this. "
            + "There is 1 in the wooden chest.",
        )

    def test_look_at_5(self):
        result = self.command_processor.process("look at steel shield in wooden chest")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A broad panel of leather-bound steel with a metal rim that is "
            + "useful for sheltering behind. Its armor bonus is +2. Warriors "
            + "and priests can use this.",
        )
        self.assertEqual(
            result[0].message,
            "A broad panel of leather-bound steel with a metal rim that is "
            + "useful for sheltering behind. Its armor bonus is +2. Warriors "
            + "and priests can use this. There is 1 in the wooden chest.",
        )

    def test_look_at_6(self):
        result = self.command_processor.process("look at steel shield in wooden chest")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A broad panel of leather-bound steel with a metal rim that is "
            + "useful for sheltering behind. Its armor bonus is +2. Warriors "
            + "and priests can use this.",
        )
        self.assertEqual(
            result[0].message,
            "A broad panel of leather-bound steel with a metal rim that is "
            + "useful for sheltering behind. Its armor bonus is +2. Warriors "
            + "and priests can use this. There is 1 in the wooden chest.",
        )

    def test_look_at_7(self):
        result = self.command_processor.process("look at mana potion in wooden chest")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A small, stoppered bottle that contains a pungeant but drinkable "
            + "blue liquid with a discernable magic aura. It restores 20 mana "
            + "points.",
        )
        self.assertEqual(
            result[0].message,
            "A small, stoppered bottle that contains a pungeant but drinkable "
            + "blue liquid with a discernable magic aura. It restores 20 mana "
            + "points. There is 1 in the wooden chest.",
        )

    def test_look_at_8(self):
        result = self.command_processor.process("look at health potion in wooden chest")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A small, stoppered bottle that contains a pungeant but drinkable "
            + "red liquid with a discernable magic aura. It restores 20 hit "
            + "points.",
        )
        self.assertEqual(
            result[0].message,
            "A small, stoppered bottle that contains a pungeant but drinkable "
            + "red liquid with a discernable magic aura. It restores 20 hit "
            + "points. There is 1 in the wooden chest.",
        )

    def test_look_at_9(self):
        result = self.command_processor.process("look at north door")
        self.assertIsInstance(result[0], FoundDoorOrDoorwayGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertEqual(
            result[0].message,
            "This door is bound in iron plates with a small barred window set "
            + "up high. It is set in the north wall. It is closed but "
            + "unlocked.",
        )

    def test_look_at_10(self):
        result = self.command_processor.process("look at mana potion in inventory")
        self.assertIsInstance(result[0], FoundNothingGSM)
        self.assertEqual(result[0].item_title, "mana potion")
        self.assertEqual(result[0].item_location, "inventory")
        self.assertIs(result[0].location_type, None)
        self.assertEqual(
            result[0].message, "You have no mana potion in your inventory."
        )

    def test_look_at_11(self):
        result = self.command_processor.process("look at longsword on the floor")
        self.assertIsInstance(result[0], FoundNothingGSM)
        self.assertEqual(result[0].item_title, "longsword")
        self.assertEqual(result[0].item_location, "floor")
        self.assertIs(result[0].location_type, None)
        self.assertEqual(result[0].message, "There is no longsword on the floor.")

    def test_look_at_12(self):
        result = self.command_processor.process("pick lock on wooden chest")
        result = self.command_processor.process("open wooden chest")
        result = self.command_processor.process("take mana potion from wooden chest")
        result = self.command_processor.process("look at mana potion in wooden chest")
        self.assertIsInstance(result[0], FoundNothingGSM)
        self.assertEqual(result[0].item_title, "mana potion")
        self.assertEqual(result[0].item_location, "wooden chest")
        self.assertEqual(result[0].location_type, "chest")
        self.assertEqual(
            result[0].message, "The wooden chest has no mana potion in it."
        )

    def test_look_at_13(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_locked = True
        result = self.command_processor.process("look at north door")
        self.assertIsInstance(result[0], FoundDoorOrDoorwayGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertEqual(
            result[0].message,
            "This door is bound in iron plates with a small barred window set "
            + "up high. It is set in the north wall. It is closed and locked.",
        )

    def test_look_at_14(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_closed = (
            False
        )
        result = self.command_processor.process("look at north door")
        self.assertIsInstance(result[0], FoundDoorOrDoorwayGSM)
        self.assertEqual(result[0].compass_dir, "north")
        self.assertEqual(
            result[0].message,
            "This door is bound in iron plates with a small barred window set "
            + "up high. It is set in the north wall. It is open.",
        )

    def test_look_at_15(self):
        self.command_processor.game_state.rooms_state.cursor.north_door.is_closed = (
            False
        )
        result = self.command_processor.process("look at west door")
        self.assertIsInstance(result[0], DoorNotPresentGSM)
        self.assertEqual(result[0].compass_dir, "west")
        self.assertEqual(result[0].message, "This room does not have a west door.")

    def test_look_at_16(self):
        self.command_processor.game_state.rooms_state.move(north=True)
        result = self.command_processor.process("look at east doorway")
        self.assertIsInstance(result[0], FoundDoorOrDoorwayGSM)
        self.assertEqual(result[0].compass_dir, "east")
        self.assertEqual(
            result[0].message,
            "This open doorway is outlined by a stone arch set into the wall. "
            + "It is set in the east wall. It is open.",
        )

        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_closed
        )
        self.assertFalse(
            self.command_processor.game_state.rooms_state.cursor.east_door.is_locked
        )

    def test_look_at_17(self):
        self.command_processor.game_state.character.pick_up_item(
            self.command_processor.game_state.items_state.get("Longsword")
        )
        result = self.command_processor.process("look at longsword in inventory")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A hefty sword with a long blade, a broad hilt and a leathern "
            + "grip. Its attack bonus is +0 and its damage is 1d8. Warriors "
            + "can use this.",
        )
        self.assertEqual(
            result[0].message,
            "A hefty sword with a long blade, a broad hilt and a leathern "
            + "grip. Its attack bonus is +0 and its damage is 1d8. Warriors "
            + "can use this. There is 1 in your inventory.",
        )

    def test_look_at_18(self):
        self.command_processor.game_state.character.pick_up_item(
            self.command_processor.game_state.items_state.get("Magic_Wand")
        )
        result = self.command_processor.process("look at magic wand in inventory")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A palpably magical tapered length of polished ash wood tipped "
            + "with a glowing red carnelian gem. Its attack bonus is +3 and "
            + "its damage is 3d8+5. Mages can use this.",
        )
        self.assertEqual(
            result[0].message,
            "A palpably magical tapered length of polished ash wood tipped "
            + "with a glowing red carnelian gem. Its attack bonus is +3 and "
            + "its damage is 3d8+5. Mages can use this. There is 1 in your "
            + "inventory.",
        )

    def test_look_at_19(self):
        result = self.command_processor.process("look at door")
        self.assertIsInstance(result[0], AmbiguousDoorSpecifierGSM)
        self.assertEqual(set(result[0].compass_dirs), {"north", "east"})
        self.assertEqual(result[0].door_type, "iron_door")
        self.assertEqual(result[0].door_or_doorway, "door")
        self.assertEqual(
            result[0].message,
            "More than one door in this room matches your command. Do you "
            + "mean the north iron door or the east iron door?",
        )

    def test_look_at_20(self):
        result = self.command_processor.process("look at mana potion")
        self.assertIsInstance(result[0], FoundItemOrItemsHereGSM)
        self.assertEqual(result[0].item_qty, 1)
        self.assertEqual(
            result[0].item_description,
            "A small, stoppered bottle that contains a pungeant but drinkable "
            + "blue liquid with a discernable magic aura. It restores 20 mana "
            + "points.",
        )
        self.assertEqual(
            result[0].message,
            "A small, stoppered bottle that contains a pungeant but drinkable "
            + "blue liquid with a discernable magic aura. It restores 20 mana "
            + "points. There is 1 on the floor.",
        )
