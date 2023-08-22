#!/usr/bin/python3

"""
All the classes needed to interpret game data in .ini format into an
environment of game element objects, state objects which track game
element object collections, the Character object & its subordinate
objects, which manage the character data and model the limited subset of
Dungeons & Dragons rules that this library implements.
"""

import abc
import collections
import math
import random
import re

import adventuregame.exceptions as excpt
import adventuregame.utility as util


__name__ = "adventuregame.elements"


__all__ = ("AbilityScores", "Armor", "Character", "Chest", "Coin", "Container",
           "ContainersState", "Corpse", "Creature", "CreaturesState", "Door",
           "DoorsState", "Doorway", "Equipment", "EquippableItem", "GameState",
           "IniEntry", "IronDoor", "Item", "ItemsMultiState", "ItemsState",
           "Key", "Oddment", "Potion", "Room", "RoomsState", "Shield", "State",
           "Wand", "Weapon", "WoodenDoor")


class IniEntry(object):
    """
Parent class for classes like Room, Item, and Door that are instantiated
from .ini file entries.
    """

    # This regular expression is used to parse the contents= attributes
    # used by rooms.ini and containers.ini to encode initializing data
    # for an Items_Multi_State object into a single line of text. Used
    # in IniEntry._process_list_value().

    inventory_list_value_re = re.compile(r"""^\[(
                                                    (
                                                        [1-9][0-9]*
                                                        x
                                                        [A-Z][A-Za-z_]+
                                                    )(,
                                                        [1-9][0-9]*
                                                        x
                                                        [A-Z][A-Za-z_]+
                                                    )*
                                                )\]$""", re.X)

    def __init__(self, **argd):
        """
Accept arbitrary keyword arguments and parses them from .ini format.
Casts 'true' and 'false' to boolean, integer strings to int and float
strings to float. Assigns all entries in **argd to object attributes.
        """
        for key, value in argd.items():
            if isinstance(value, str):
                if value.lower() == "false":
                    value = False
                elif value.lower() == "true":
                    value = True
                elif value.isdigit():
                    value = int(value)
                elif util.isfloat(value):
                    value = float(value)
            setattr(self, key, value)

    def __eq__(self, other):
        """
Test two IniEntry objects or objects that subclass IniEntry for equality.
        """
        if not isinstance(other, type(self)):
            return False
        else:
            return all(getattr(self, attr, None) == getattr(other, attr, None)
                       for attr in self.__slots__)

    def _post_init_slots_set_none(self, slots):
        """
Set any attributes listed in __slots__ that haven't been set to None
explicitly.

:slots: The __slots__ value of the class the method is being called
from.
:returns: None.
        """
        for key in slots:
            if not hasattr(self, key):
                setattr(self, key, None)

    def _process_list_value(self, inventory_value):
        r"""
Parse the item inventory stored and returns a list that can be converted
to the contents of a container or corpse.

:inventory_value: A string of the form
\[\d+x[A-Z][A-Za-z_]+(,\d+[A-Z][A-Za-z_]+)*\].
:return: A tuple of pairs of quantity ints and Item subclass objects.
        """
        value_match = self.inventory_list_value_re.match(inventory_value)
        inner_capture = value_match.groups(1)[0]
        capture_split = inner_capture.split(",")
        qty_strval_pairs = tuple((int(item_qty), item_name)
                                 for item_qty, item_name in (
                                     name_x_qty_str.split("x", maxsplit=1)
                                     for name_x_qty_str in capture_split))
        return qty_strval_pairs


class State(abc.ABC):
    """
A generic key-value container object that maintains an internal
dictionary and provides access to it by method.
    """
    __slots__ = "_contents",

    __abstractmethods__ = frozenset(("__init__",))

    def contains(self, item_internal_name):
        """
Test whether an item object with the specified internal name is present
in the private dictionary.

:item_internal_name: The internal name of the Item subclass object.
:return: True or False.
        """
        return any(item_internal_name == contained_item.internal_name
                   for contained_item in self._contents.values())

    def get(self, item_internal_name):
        """
Returns the item object with the given internal name if present,
otherwise raise a KeyError.

:item_internal_name: The internal name of the Item subclass object.
:return: An Item subclass object.
        """
        return self._contents[item_internal_name]

    def set(self, item_internal_name, item):
        """
Add an item to the internal dictionary using the given internal name as
a key.

:item_internal_name: The internal name of the Item subclass object to
use as a key.
:item: The Item subclass object to be set.
        """
        self._contents[item_internal_name] = item

    def delete(self, item_internal_name):
        """
Delete the item object from the internal dictionary referred to by the
given internal name.

:item_internal_name: The internal name of the Item subclass object.
:returns: None.
        """
        del self._contents[item_internal_name]

    def keys(self):
        """Return the internal dictionary's keys iterator."""
        return self._contents.keys()

    def values(self):
        """Return the internal dictionary's values iterator."""
        return self._contents.values()

    def items(self):
        """Return the internal dictionary's items iterator."""
        return self._contents.items()

    def size(self):
        """Return the length of the internal dictionary."""
        return len(self._contents)


class Item(IniEntry):
    """A single item, taken from .ini format."""
    __slots__ = ("internal_name", "title", "description", "weight", "value",
                 "damage", "attack_bonus", "armor_bonus", "item_type",
                 "warrior_can_use", "thief_can_use", "priest_can_use",
                 "mage_can_use", "hit_points_recovered",
                 "mana_points_recovered")

    def __init__(self, **argd):
        """Instance the item for arbitrary key-value pairs."""
        super().__init__(**argd)
        self._post_init_slots_set_none(self.__slots__)

    @classmethod
    def subclassing_factory(cls, **item_dict):
        """
Instance an arbitrary subclass from arguments based on the value of the
item_type key.

:**item_dict: A dictionary of key-value pairs to instantiate the Item
subclass object with.
:return: An Item subclass object.
        """
        if item_dict["item_type"] == "armor":
            item = Armor(**item_dict)
        elif item_dict["item_type"] == "coin":
            item = Coin(**item_dict)
        elif item_dict["item_type"] == "potion":
            item = Potion(**item_dict)
        elif item_dict["item_type"] == "key":
            item = Key(**item_dict)
        elif item_dict["item_type"] == "shield":
            item = Shield(**item_dict)
        elif item_dict["item_type"] == "wand":
            item = Wand(**item_dict)
        elif item_dict["item_type"] == "weapon":
            item = Weapon(**item_dict)
        elif item_dict["item_type"] == "oddment":
            item = Oddment(**item_dict)
        else:
            raise excpt.Internal_Exception(
                "couldn't instance Item subclass, unrecognized item "
                f"type '{item_dict['item_type']}'.")
        return item


class EquippableItem(Item):

    def usable_by(self, character_class):
        """
An item equippable by some classes and not by others, based on the
'warrior_can_use', 'thief_can_use', 'mage_can_use', or 'priest_can_use'
attributes.

:character_class: Either 'Warrior', 'Thief', 'Mage', or 'Priest'.
:return: A boolean.
        """
        if character_class not in ("Warrior", "Thief", "Mage", "Priest"):
            raise excpt.Internal_Exception(
                f"character class {character_class} not recognized")
        return bool(getattr(self, character_class.lower() + "_can_use", None))


# The subclasses don't have much differing functionality but accurately
# typing each Item allows classes that handle items of specific types,
# like Equipment(), to use type testing to determine if a valid Item has
# been supplied as an argument.

class Armor(EquippableItem):
    """A suit of armor, which can be equipped, to raise armor class."""
    pass


class Coin(Item):
    """A coin, i.e. a unit of value."""
    pass


class Potion(Item):
    """A potion, which is drinkable."""
    pass


class Key(Item):
    """A key, which can be used to unlock doors."""
    pass


class Oddment(Item):
    """A miscellaneous good with no in-game purpose."""
    pass


class Shield(EquippableItem):
    """A shield, which can be equipped, to raise armor class."""
    pass


class Wand(EquippableItem):
    """A wand, which can be equipped and used by mages to do damage"""
    pass


class Weapon(EquippableItem):
    """A weapon, which can be equipped, and wielded to do damage."""
    pass


class ItemsState(State):
    """
A container object which stores Item objects (an abstract class).
    """
# <<< HERE
    def __init__(self, **dict_of_dicts):
        """
This __init__ method accepts a **dict-of-dicts -- such as offered by an
IniConfig object's section attribute-- and uses Item.subclassing_factory
to construct Item subclass objects from the internal dicts. Each one has
the attribute internal_name set to the corresponding key from the outer
dict.

:**dict_of_dicts: A structure of internal name keys corresponding to
                  dict values which are key-value pairs to initialize an
                  individual Item subclass object with.
        """
        self._contents = dict()
        for item_internal_name, item_dict in dict_of_dicts.items():
            item = Item.subclassing_factory(
                internal_name=item_internal_name, **item_dict)
            self._contents[item_internal_name] = item


class ItemsMultiState(ItemsState):
    """
This subclass of Items_State extends its functionality to track the
quantity of each Item subclass object it contains.
    """

    def __init__(self, **argd):
        """
The __init__ method of this class uses super() to call
Items_State.__init__() with the **dict-of-dicts argd. It then resets
each key's value to a tuple of the quantity 1 and the Item subclass
object. Quantities can be altered with subsequent method use but setting
quantities above 1 in Items_Multi_State.__init__ is not supported.
        """
        super().__init__(**argd)

        # I preload the dict's items() sequence outside of the loop
        # because the loop alters the dict and I don't want a concurrent
        # update error.

        contents_items = tuple(self._contents.items())
        for item_internal_name, item in contents_items:
            self._contents[item_internal_name] = (1, item)

    def contains(self, item_internal_name):
        """
This method tests whether an item object with the specified internal
name is present in the private dictionary.

:item_internal_name: The internal name of the Item subclass object.
:return:             A boolean.
        """
        return(any(contained_item.internal_name == item_internal_name
                   for _, contained_item in self._contents.values()))

    def set(self, item_internal_name, item_qty, item):
        """
If an object with the given internal name is present in the internal
dict, this accessor method returns a 2-tuple comprising an int of the
item's quantity and the Item subclass object; otherwise the internal
dict raises a KeyError.

:item_internal_name: The internal name of the Item subclass object.
:item_qty:           An int value of the item quantity.
:item:               The Item subclass object.
:return:             None.
        """
        self._contents[item_internal_name] = item_qty, item

    def add_one(self, item_internal_name, item):
        """
This method increases the quantity stored for the given Item subclass
object by 1, if it's present. Otherwise, the Item is stored under the
given internal name with a quantity of 1.

:item_internal_name: The internal name of the Item subclass object.
:item:               The Item subclass object.
:return:             None.
        """
        if self.contains(item_internal_name):
            self._contents[item_internal_name] = (
                self._contents[item_internal_name][0] + 1,
                self._contents[item_internal_name][1])
        else:
            self._contents[item_internal_name] = 1, item

    def remove_one(self, item_internal_name):
        """
This method decreases the quantity stored for the given Item subclass
object by 1, if it's present. If it's not present, a KeyError is raised.
If the Item subclass object's stored quantity was 1, the object is
deleted from the internal dictionary.

:item_internal_name: The internal name of the Item subclass object.
:return:             None.
        """
        if item_internal_name not in self._contents:
            raise KeyError(item_internal_name)
        elif self._contents[item_internal_name][0] == 1:
            del self._contents[item_internal_name]
        else:
            self._contents[item_internal_name] = (
                self._contents[item_internal_name][0] - 1,
                self._contents[item_internal_name][1])


class Door(IniEntry):
    """
The Item subclass of IniEntry represents a single door. It is
instantiated from a single section of a doors.ini file as returned by an
IniConfig's dict-of-dicts sections attribute.
    """
    __slots__ = ('internal_name', 'title', 'description', 'door_type',
                 'is_locked', 'is_closed', 'closable',
                 '_linked_rooms_internal_names', 'is_exit')

    def __init__(self, **argd):
        """
The __init__ method uses super() to call IniEntry.__init__ to
populate the object with attributes from argd. It then sets all unset
attributes to None and parses the internal name (which has the form
'Room_#,#_x_Room_#,#') to detect which two rooms are joined by this
door.

:**argd: The key-value pairs to initialize the Door object with.
        """
        super().__init__(**argd)
        self._post_init_slots_set_none(self.__slots__)
        self._linked_rooms_internal_names = set(
            self.internal_name.split('_x_'))

    @classmethod
    def subclassing_factory(cls, **door_dict):
        """
Like Item.subclassing_factory, this factory method accepts an argd and
detects which Door subclass should be instantiated from the arguments by
reading the door_type value.

:**door_dict: The key-value pairs to initialize the Door subclass
              object with.
        """
        if door_dict['door_type'] == 'doorway':
            door = Doorway(**door_dict)
        elif door_dict['door_type'] == 'wooden_door':
            door = WoodenDoor(**door_dict)
        elif door_dict['door_type'] == 'iron_door':
            door = IronDoor(**door_dict)
        else:
            raise excpt.Internal_Exception(
                f'unrecognized door type: {door_dict["door_type"]}')
        return door

    def other_room_internal_name(self, room_internal_name):
        """
This method accepts the internal name of a room which is one of the two
rooms linked by this door, and returns the internal name of the other
room in the linkage.

:room_internal_name: The internal name of a Room object.
:return:             A Room object.
        """

        if room_internal_name not in self._linked_rooms_internal_names:
            raise excpt.Internal_Exception(
                f"room internal name {room_internal_name} not one of the "
                f"two rooms linked by this door object")

        # The _linked_rooms_internal_names set is only 2 elements long
        # and by the above one of those elements is the name supplied so
        # this loop returns the other name.

        for found_internal_name in self._linked_rooms_internal_names:
            if found_internal_name == room_internal_name:
                continue
            return found_internal_name

    def copy(self):
        """
This method returns a shallow copy of the object.

:return: A Door object.
        """
        return self.__class__(**{attr: getattr(self, attr, None)
                                 for attr in self.__slots__})


class Doorway(Door):
    """
This Door subclass is used to represent doors which are doorways. It
offers no functionality, but is useful for detecting doorways by type
testing.
    """
    pass


class WoodenDoor(Door):
    """
This Door subclass is used to represent doors which are wooden. It
offers no functionality, but is useful for detecting wooden doors by
type testing.
    """
    pass


class IronDoor(Door):
    """
This Door subclass is used to represent doors which are iron. It offers
no functionality, but is useful for detecting iron doors by type
testing.
    """
    pass


# This class doesn't subclass `State` because it re-implements every
# method.

class DoorsState(object):
    """
This class replicates the functionality of the State object for a
container object which stores Door subclass objects. It's initialized
with a **dict-of-dicts from the items.ini IniConfig object.
    """

    def __init__(self, **dict_of_dicts):
        """
The internal storage dictionary of this object is two-dimensional,
indexed by the internal names of the two rooms connected by the door.
For consistency, the two internal names are sorted and the internal name
that is earlier in the sort order is the outer dict's key, and the one
that's later in the sort order is the inner dict's key.

:**dict_of_dicts: A structure of internal name keys corresponding to
                  dict values which are key-value pairs to initialize an
                  individual Door object with.
        """
        self._contents = collections.defaultdict(dict)

        # The entries in doors.ini have internal_names that consist of
        # the internal names for the two rooms they connect, connected
        # by '_x_'. This loop recovers the two room internal names for
        # each .ini entry and stores the Door subclass object in a
        # dict-of-dicts under the two room internal names.

        for door_internal_name, door_argd in dict_of_dicts.items():
            room_1_intrn_name, room_2_intrn_name = \
                door_internal_name.split("_x_")
            self._contents[room_1_intrn_name][room_2_intrn_name] = \
                Door.subclassing_factory(internal_name=door_internal_name,
                                         **door_argd)
            pass

    def contains(self, room_1_intrn_name, room_2_intrn_name):
        """
This method tests whether a Door subclass object indexed by the given
two Room subclass object's internal names is present in the internal
**dict-of-dicts.

:room_1_intern_name: The internal name of one of the two linked Room
                     objects.
:room_2_intern_name: The internal name of the other of the two linked Room
                     objects.
:return:             A boolean.
        """
        return (room_1_intrn_name in self._contents
                and room_2_intrn_name in self._contents[room_1_intrn_name])

    def get(self, room_1_intrn_name, room_2_intrn_name):
        """
This method returns the Door subclass object indexed by the two given
Room subclass object internal names, or raises a KeyError if it's not
present.

:room_1_intern_name: The internal name of one of the two linked Room
                     objects.
:room_2_intern_name: The internal name of the other of the two linked Room
                     objects.
:return:             A Door object.
        """
        return self._contents[room_1_intrn_name][room_2_intrn_name]

    def set(self, room_1_intrn_name, room_2_intrn_name, door):
        """
This method stores the given Door subclass object in the internal
**dict-of-dicts using the first Room subclass object internal name as
the key to the outer dictionary and the second Room subclass object
internal name as the key to the inner dictionary.

:room_1_intern_name: The internal name of one of the two linked Room
                     objects.
:room_2_intern_name: The internal name of the other of the two linked Room
                     objects.
:door:               A Door object.
:return:             None.
        """
        self._contents[room_1_intrn_name][room_2_intrn_name] = door

    def delete(self, room_1_intrn_name, room_2_intrn_name):
        """
This method deletes the Door subclass object found in the internal
**dict-of-dicts under the given two Room subclass object internal name
keys.

:room_1_intern_name: The internal name of one of the two linked Room
                     objects.
:room_2_intern_name: The internal name of the other of the two linked Room
                     objects.
:door:               A Door object.
:return:             None.
        """
        del self._contents[room_1_intrn_name][room_2_intrn_name]

    def keys(self):
        """
This method returns a list of 2-tuples comprising each valid Room
subclass internal name pairs that can be used as arguments to .get() to
retrieve a Door subclass object.

:return: A list of 2-tuples comprising pairs of Room internal name
         strings.
        """
        keys_list = list()
        for room_1_name in self._contents.keys():
            for second_room_name in self._contents[room_1_name].keys():
                keys_list.append((room_1_name, second_room_name))
        return keys_list

    def values(self):
        """
This method returns a list comprising all the Door subclass objects
stored in the internal **dict-of-dicts.

:return: A list of Door objects.
        """
        values_list = list()
        for room_1_name in self._contents.keys():
            values_list.extend(self._contents[room_1_name].values())
        return values_list

    def items(self):
        """
This method returns a list of 3-tuples, each comprising a pair of Room
subclass object internal names that are a key to the container, coupled
with the Door subclass object that is the value to that key.

:return: A list of 3-tuples, comprised of a string (the internal
         name), an int (the quantity) and an Item subclass object.
        """
        items_list = list()
        for room_1_name in self._contents.keys():
            for second_room_name, door in self._contents[room_1_name].items():
                items_list.append((room_1_name, second_room_name, door))
        return items_list

    def size(self):
        """
This method returns the number of Door subclass objects that is stored
in this container.

:return: An int, the number of Item subclass objects stored.
        """
        return len(self.keys())


class Container(IniEntry, ItemsMultiState):
    """
This class uses multiple inheritance to inherit from both IniEntry and
Items_Multi_State: it is an object that's instantiated from an entry in
items.ini, but also can contain Item subclass objects.
    """
    __slots__ = ("internal_name", "title", "description", "is_locked",
                 "is_closed", "container_type")

    def __init__(self, items_state, internal_name,
                 *item_objs, **ini_constr_argd):
        r"""
This __init__ method calls both parent class's __init__ methods in
sequence. It draws on the contents attribute of the source ini data,
which is in the \[\d+x[A-Z][A-Za-z_]+(,\d+x[A-Z][A-Za-z_]+)*\] format,
and unpacks it. An items_state object is a required argument so that
it can be used to look up Item subclass objects' internal names and
populate the container.

:items_state:       An Item_State object.
:internal_name:     The internal name of the container.
:*item_objs:        A tuple of the Item objects contained by the
                    container.
:**ini_constr_argd: The key-value pairs from containers.ini to
                    instantiate the Container object with.
        """
        contents_str = ini_constr_argd.pop("contents", None)
        IniEntry.__init__(self, internal_name=internal_name,
                          **ini_constr_argd)

        # If this Container has a contents attribute, it
        # is a compacted list of Item internal names and
        # quantities. _process_list_value unpacks it and returns
        # quantity-internal_name pairs.

        if contents_str:
            contents_qtys_names = self._process_list_value(contents_str)

            # This list comprehension retrieves the Item subclass
            # objects from items_state.

            contents_qtys_item_objs = tuple(
                (item_qty, items_state.get(item_internal_name))
                for item_qty, item_internal_name in contents_qtys_names)
        ItemsMultiState.__init__(self)
        if contents_str:

            # If the contents attribute was non-None,
            # contents_qtys_item_objs contains the quantities and Item
            # subclass objects to populate this Container object with. I
            # set each internal name to the quantity and Item subclass
            # object values in turn.

            for item_qty, item in contents_qtys_item_objs:
                self.set(item.internal_name, item_qty, item)

        # This cleanup step sets any attributes from __slots__ not yet
        # to None explicitly.

        self._post_init_slots_set_none(self.__slots__)

    @classmethod
    def subclassing_factory(cls, items_state, **container_dict):
        """
This factory accepts an items_state object and a **dict-of-dicts as
featured in an IniConfig object's section attribute, and determines
which Container subclass is appropriate to instantiate from the data.

:items_state:      An Items_State object.
:**container_dict: A dict of key-value pairs to instantiate the
                   Container subclass with.
        """
        if container_dict["container_type"] == "chest":
            container = Chest(items_state, **container_dict)
        elif container_dict["container_type"] == "corpse":
            container = Corpse(items_state, **container_dict)
        return container


class Chest(Container):
    """
This Container subclass is used to represent containers which are
chests. It offers no functionality, but is useful for detecting chest
objects by type testing.
    """
    pass


class Corpse(Container):
    """
This Container subclass is used to represent containers which are
corpses. It offers no functionality, but is useful for detecting corpse
objects by type testing.
    """
    pass


class ContainersState(ItemsState):
    """
This Items_State subclass is instantiated from the sections attribute of
an IniConfig object instantiated from containers.ini.
    """
    __slots__ = "_contents",

    def __init__(self, items_state, **dict_of_dicts):
        """
This __init__ method accepts an items_state object and a
**dict-of-dicts, which it iterates down to instantiate the Container
subclass objects that the container is populated with.

:items_state:     An Items_State object.
:**dict_of_dicts: A structure of internal name keys corresponding to
                  dict values which are key-value pairs to initialize an
                  individual Container subclass object with.
        """
        self._contents = dict()
        for container_internal_name, container_dict in dict_of_dicts.items():
            container = Container.subclassing_factory(
                items_state, internal_name=container_internal_name,
                **container_dict)
            self._contents[container_internal_name] = container


class AbilityScores(object):
    """
This class is one of the dependencies of the Character and Creature
classes and is only used as a subordinate object to them. It abstracts
the six ability scores of a Character or Creature and provides methods
for using them.
    """
    __slots__ = ("strength", "dexterity", "constitution", "intelligence",
                 "wisdom", "charisma", "character_class")

    weightings = {
        "Warrior": ("strength", "constitution", "dexterity", "intelligence",
                    "charisma", "wisdom"),
        "Thief": ("dexterity", "constitution", "charisma", "strength",
                  "wisdom", "intelligence"),
        "Priest": ("wisdom", "strength", "constitution", "charisma",
                   "intelligence", "dexterity"),
        "Mage": ("intelligence", "dexterity", "constitution", "strength",
                 "wisdom", "charisma")
    }

    @property
    def strength_mod(self):
        """
This property computes the Strength modifier from the stored Strength
score.

:return: An int.
        """
        return self._stat_mod("strength")

    @property
    def dexterity_mod(self):
        """
This property computes the Dexterity modifier from the stored Dexterity
score.

:return: An int.
        """
        return self._stat_mod("dexterity")

    @property
    def constitution_mod(self):
        """
This property computes the Constitution modifier from the stored
Constitution score.

:return: An int.
        """
        return self._stat_mod("constitution")

    @property
    def intelligence_mod(self):
        """
This property computes the Intelligence modifier from the stored
Intelligence score.

:return: An int.
        """
        return self._stat_mod("intelligence")

    @property
    def wisdom_mod(self):
        """
This property computes the Wisdom modifier from the stored Wisdom score.

:return: An int.
        """
        return self._stat_mod("wisdom")

    @property
    def charisma_mod(self):
        """
This property computes the Charisma modifier from the stored Charisma score.

:return: An int.
        """
        return self._stat_mod("charisma")

    # In modern D&D, the derived value from an ability score that
    # is relevant to determining outcomes is the 'stat mod' (or
    # 'stat modifier'), which is computed from the ability score
    # by subtracting 10, dividing by 2 and rounding down. That is
    # implemented here.

    def _stat_mod(self, ability_score):
        """
This private method implements the ability score modifier equation for
an arbitrary ability score.

:ability_score: A string, one of 'Strength', 'Dexterity',
                'Constitution', 'Intelligence', 'Wisdom' or 'Charisma'.
:return:        An int.
        """
        if not hasattr(self, ability_score):
            raise excpt.Internal_Exception(
                f"unrecognized ability {ability_score}")
        return math.floor((getattr(self, ability_score) - 10) / 2)

    def __init__(self, character_class_str):
        """
This __init__ method instantiates the Character object from the given
character class. When the ability scores are randomly generated, they
will be assigned by order of priority as determined by the character
class; each class has a different ability priority ordering.

:character_class_str: One of 'Warrior', 'Thief', 'Priest' or 'Mage'.
        """
        if character_class_str not in self.weightings:
            raise excpt.Internal_Exception(
                f"character class {character_class_str} not recognized, "
                "should be one of 'Warrior', 'Thief', 'Priest' or 'Mage'")
        self.character_class = character_class_str

    # Rolling a six-sided die 4 times and then dropping the lowest roll
    # before summing the remaining 3 results to reach a value for an
    # ability score (or 'stat') is the traditional method for generating
    # D&D ability scores. It is reproduced here.

    def roll_stats(self):
        """
This method randomly generates the six ability scores and assigns them
in priority order as dictated by the weightings. For each ability score,
the roll of four 6-sided dice is simulated. The lowest roll is dropped
and the remaining three are summed to yield an ability score value.

:return: None.
        """
        results_list = list()
        for _ in range(0, 6):
            four_rolls = sorted([random.randint(1, 6) for _ in range(0, 4)])
            three_rolls = four_rolls[1:4]
            results_list.append(sum(three_rolls))
        results_list.sort()
        results_list.reverse()
        for index in range(0, 6):
            setattr(self, self.weightings[self.character_class][index],
                    results_list[index])


class Equipment(object):
    """
This object represents the equipment held by a Character or Creature. It
stores what items are equipped as the armor, shield, weapon or wand, and
computes the derived values armor class, attack bonus and damage.
    """
    __slots__ = 'character_class', 'armor', 'shield', 'weapon', 'wand'

    @property
    def armor_equipped(self):
        """
This property returns the armor that is equipped, or None if none is
equipped.

:return: An Armor object, or None.
        """
        return getattr(self, "armor", None)

    @property
    def shield_equipped(self):
        """
This property returns the shield that is equipped, or None if none is
equipped.

:return: A Shield object, or None.
        """
        return getattr(self, "shield", None)

    @property
    def weapon_equipped(self):
        """
This property returns the weapon that is equipped, or None if none is
equipped.

:return: A Weapon object, or None.
        """
        return getattr(self, "weapon", None)

    @property
    def wand_equipped(self):
        """
This property returns the wand that is equipped, or None if none is
equipped.

:return: A Wand object, or None.
        """
        return getattr(self, "wand", None)

    def __init__(self, character_class, armor_item=None, shield_item=None,
                 weapon_item=None, wand_item=None):
        """
This __init__ method instantiates the object with the given character
class, and (optionally) armor, shield, weapon or wand items to equip.
        """
        self.character_class = character_class
        self.armor = armor_item
        self.shield = shield_item
        self.wand = wand_item
        self.weapon = weapon_item

    def equip_armor(self, item):
        """
This method equips the given Armor object.

:item:    An Armor object.
:returns: None.
        """
        if not isinstance(item, Armor):
            raise excpt.Internal_Exception(
                "the method 'equip_armor()' only accepts 'armor' objects "
                "for its argument")
        self._equip("armor", item)

    def equip_shield(self, item):
        """
This method equips the given Shield object.

:item:    A Shield object.
:returns: None.
        """
        if not isinstance(item, Shield):
            raise excpt.Internal_Exception(
                "the method 'equip_shield()' only accepts 'shield' "
                "objects for its argument")
        self._equip("shield", item)

    def equip_weapon(self, item):
        """
This method equips the given Weapon object.

:item:    A Weapon object.
:returns: None.
        """
        if not isinstance(item, Weapon):
            raise excpt.Internal_Exception(
                "the method 'equip_weapon()' only accepts 'weapon' "
                "objects for its argument")
        self._equip("weapon", item)

    def equip_wand(self, item):
        """
This method equips the given Wand object.

:item:    A Wand object.
:returns: None.
        """
        if not isinstance(item, Wand):
            raise excpt.Internal_Exception(
                "the method 'equip_wand()' only accepts 'wand' objects "
                "for its argument")
        self._equip("wand", item)

    def unequip_armor(self):
        """
This method unequips the armor that is equipped.

:return: None.
        """
        self._unequip("armor")

    def unequip_shield(self):
        """
This method unequips the shield that is equipped.

:return: None.
        """
        self._unequip("shield")

    def unequip_weapon(self):
        """
This method unequips the weapon that is equipped.

:return: None.
        """
        self._unequip("weapon")

    def unequip_wand(self):
        """
This method unequips the wand that is equipped.

:return: None.
        """
        self._unequip("wand")

    def _equip(self, equipment_slot, item):
        """
This private method equips the given EquippableItem subclass object in
the given slot.

:equipment_slot: A string, one of 'armor', 'shield', 'weapon', or
                 'wand'.
:return:         None.
        """
        if equipment_slot not in ("armor", "shield", "weapon", "wand"):
            raise excpt.Internal_Exception(
                f"equipment slot {equipment_slot} not recognized")
        if equipment_slot == "armor":
            self.armor = item
        elif equipment_slot == "shield":
            self.shield = item
        elif equipment_slot == "weapon":
            self.weapon = item
        elif equipment_slot == "wand":
            self.wand = item

    def _unequip(self, equipment_slot):
        """
This private method unequips the given EquippableItem subclass object.

:equipment_slot: A string, one of 'armor', 'shield', 'weapon', or
                 'wand'.
:return:         None.
        """
        if equipment_slot not in ("armor", "shield", "weapon", "wand"):
            raise excpt.Internal_Exception(
                f"equipment slot {equipment_slot} not recognized")
        if equipment_slot == "armor":
            self.armor = None
        elif equipment_slot == "shield":
            self.shield = None
        elif equipment_slot == "weapon":
            self.weapon = None
        elif equipment_slot == "wand":
            self.wand = None

    @property
    def armor_class(self):
        """
This method computes the armor class from the equipped Armor and Shield
objects' armor bonuses if any.

:return: An int.
        """
        ac = 10
        if self.armor_equipped:
            ac += self.armor.armor_bonus
        if self.shield_equipped:
            ac += self.shield.armor_bonus
        return ac

    @property
    def attack_bonus(self):
        """
This method returns the attack bonus associated with any equipped weapon
or wand.

:return: An int.
        """
        if self.wand_equipped:
            return self.wand.attack_bonus
        elif self.weapon_equipped:
            return self.weapon.attack_bonus
        else:
            return None

    @property
    def damage(self):
        r"""
This method returns the damage associated with any equipped weapon or
wand.

:return: A string of the form '\d+d\d+([+-]\d+)?'.
        """
        if self.wand_equipped:
            return self.wand.damage
        if self.weapon_equipped:
            return self.weapon.damage
        else:
            return None


class Character(object):
    """
This class represents a character. The player's interaction with the
game rules environment during play is mediated by an instance of this
class, which tracks their ability scores, equipment, hit points, mana
points if a spellcaster, and inventory.
    """
    __slots__ = ("character_name", "character_class", "magic_key_stat",
                 "_hit_point_maximum", "_current_hit_points",
                 "_mana_point_maximum", "_current_mana_points",
                 "ability_scores", "inventory", "_equipment")

    # The rules for "mana" points I use in this class are drawn
    # from Dungeons & Dragons 3rd edition rules. In those rules
    # they"re called "spell points". These two dicts are drawn from
    # the variant Spell Points rules, which are available online at
    # <http://dndsrd.net/unearthedSpellPoints.html>

    _base_mana_points = {"Priest": 16, "Mage": 19}

    _bonus_mana_points = {
        -4: 0, -3: 0, -2: 0, -1: 0, 0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
    # End data from that page.

    # These defaults are adapted from D&D 3rd edition rules. This info
    # is generic and doesn't have a citation.

    _magic_key_stats = {"Priest": "wisdom", "Mage": "intelligence"}

    # End rules drawn from D&D.

    # These are arbitrary.

    _hitpoint_base = {"Warrior": 40, "Priest": 30, "Thief": 30, "Mage": 20}

    def __init__(self, character_name_str, character_class_str,
                 base_hit_points=0, base_mana_points=0,
                 magic_key_stat=None, strength=0, dexterity=0, constitution=0,
                 intelligence=0, wisdom=0, charisma=0):
        """
This __init__ method sets the character's name and class. It
instantiates a subordinate Ability_Scores object, and initialized
it with the ability scores arguments (which does nothing if they
are the default of zero). It instantiates the subordinate inventory
Items_Multi_State() object and the subordinate Equipment object, and
sets up the hit point and (optionally) mana point values. It also sets
the magic key stat if any.
                                                                       |
:character_name_str:  A string, the name for the character.
:character_class_str: A string one of 'Warrior', 'Thief', 'Priest', or
                      'Mage'.
:base_hit_points:     An int, the character's base hit points
                      (optional).
:base_mana_points:    An int, the character's base mana points
                      (optional).
:magic_key_stat:      A string, the character's magic key stat (one of
                      'Intelligence', 'Wisdom', or 'Charisma').
:strength:            An int, the set value for the character's
                      Strength score (optional).
:dexterity:           An int, the set value for the character's
                      Dexterity score (optional).
:constitution:        An int, the set value for the character's
                      Constitution score (optional).
:intelligence:        An int, the set value for the character's
                      Intelligence score (optional).
:wisdom:              An int, the set value for the character's Wisdom
                      score (optional).
:charisma:            An int, the set value for the character's
                      Charisma score (optional).
        """
        if character_class_str not in {"Warrior", "Thief", "Priest", "Mage"}:
            raise excpt.Internal_Exception(
                f"character class argument {character_class_str} not one "
                "of Warrior, Thief, Priest or Mage")
        self.character_name = character_name_str
        self.character_class = character_class_str
        self.ability_scores = AbilityScores(character_class_str)

        # This step is refactored into a private method for readability.
        # All it does is set the ability scores if they're all nonzero.

        self._set_up_ability_scores(strength, dexterity, constitution,
                                    intelligence, wisdom, charisma)
        self.inventory = ItemsMultiState()
        self._equipment = Equipment(character_class_str)

        # This step is refactored into a private method for readability.
        # Its logic is fairly complex, q.v.

        self._set_up_hit_points_and_mana_points(base_hit_points,
                                                base_mana_points,
                                                magic_key_stat)

    def _set_up_ability_scores(self, strength=0, dexterity=0, constitution=0,
                               intelligence=0, wisdom=0, charisma=0):
        """
This private method sets the ability scores from its arguments if they
are nonzero. It is used by __init__ to set ability scores from its
arguments if furnished.

:strength:     An int, the set value for the character's Strength
               score (optional).
:dexterity:    An int, the set value for the character's Dexterity
               score (optional).
:constitution: An int, the set value for the character's Constitution
               score (optional).
:intelligence: An int, the set value for the character's Intelligence
               score (optional).
:wisdom:       An int, the set value for the character's Wisdom score
               (optional).
:charisma:     An int, the set value for the character's Charisma
               score (optional).
        """
        if all((strength, dexterity, constitution,
                intelligence, wisdom, charisma)):
            self.ability_scores.strength = strength
            self.ability_scores.dexterity = dexterity
            self.ability_scores.constitution = constitution
            self.ability_scores.intelligence = intelligence
            self.ability_scores.wisdom = wisdom
            self.ability_scores.charisma = charisma
        elif any((strength, dexterity, constitution,
                  intelligence, wisdom, charisma)):
            raise excpt.Internal_Exception(
                "The constructor for 'character' must be supplied with "
                "either all of the arguments 'strength', 'dexterity', "
                "'constitution', 'intelligence', 'wisdom', and 'charisma' "
                "or none of them.")
        else:
            self.ability_scores.roll_stats()

    def _set_up_hit_points_and_mana_points(self, base_hit_points,
                                           base_mana_points, magic_key_stat):
        """
This private method sets up the Character object's hit points, and
mana points if they're playing a spellcaster. Bonus hit points are
calculated from the character's Constitution modifier. Bonus mana points
are calculated from the specified magic key ability score (Intelligence
for Mages, and Wisdom for Priests).

:base_hit_points:  An int, the character's base hit points.
:base_mana_points: An int, the character's base mana points.
:magic_key_stat:   A string, the character's magic key stat (one of
                   'Intelligence', 'Wisdom', or 'Charisma').
:return:           None.
        """

        # When the Character is instanced by a Game_State object, none
        # of these values are supplied to __init__. But the Creature
        # object that subclasses Character draws its values from an .ini
        # entry, and it does have all these values supplied to __init__.
        #
        # Base hit points are taken either from an argument to __init__
        # or from the class's default in the _hitpoint_base dict.

        if base_hit_points:
            self._hit_point_maximum = self._current_hit_points = (
                (base_hit_points +
                 self.ability_scores.constitution_mod * 3))
        else:
            self._hit_point_maximum = self._current_hit_points = (
                self._hitpoint_base[self.character_class]
                + self.ability_scores.constitution_mod * 3)

        # Magic key stat can be set from the arguments to __init__ or
        # drawn from class defaults.

        if magic_key_stat:
            if magic_key_stat not in ("intelligence", "wisdom", "charisma"):
                raise excpt.Internal_Exception(
                    f"`magic_key_stat` argument '{magic_key_stat}' not "
                    "recognized")
            self.magic_key_stat = magic_key_stat
        else:
            if self.character_class == "Priest":
                self.magic_key_stat = "wisdom"
            elif self.character_class == "Mage":
                self.magic_key_stat = "intelligence"
            else:
                self.magic_key_stat = ""
                self._mana_point_maximum = self._current_mana_points = 0
                return
        magic_key_stat_mod = getattr(self, self.magic_key_stat + "_mod", None)

        # These assignments add bonus mana points from the
        # _bonus_mana_points dict. A spellcaster with a high
        # spellcasting stat (16-18) can gain a lot of extra mana points.

        if base_mana_points:
            self._mana_point_maximum = self._current_mana_points = (
                base_mana_points
                + self._bonus_mana_points[magic_key_stat_mod])
        elif self.character_class in self._base_mana_points:
            self._mana_point_maximum = self._current_mana_points = (
                self._base_mana_points[self.character_class]
                + self._bonus_mana_points[magic_key_stat_mod])
        else:
            self._mana_point_maximum = self._current_mana_points = 0

    def _attack_or_damage_stat_dependency(self):
        """
This private method is used by attack_roll(), attack_bonus() and
damage() to determine which ability score modifier to add to attack
and damage. It's Strength for Warriors, Priests, and Mages wielding a
weapon; it's Dexterity for Thieves, and it's Intelligence for Mages
wielding a wand.

:return: A string, one of 'strength', 'dexterity', or 'intelligence'.
        """

        # The convention that a Mage using a spell add Intelligence
        # to their attack & damage is drawn from Dungeons & Dragons
        # 5th edition rules as laid out in the 5th edition _Player's
        # Handbook_.

        if (self.character_class in ("Warrior", "Priest")
                or (self.character_class == "Mage"
                    and self._equipment.weapon_equipped)):
            return "strength"
        elif self.character_class == "Thief":
            return "dexterity"
        else:
            # By exclusion, (`character_class` == "Mage" and
            # self._equipment.wand_equipped)
            return "intelligence"

    @property
    def _item_attacking_with(self):
        """
This private property returns the wand object equipped if there is one,
otherwise the weapon object equipped if there is one, otherwise None.

:return: A Wand object, a Weapon object, or None.
        """
        if self._equipment.wand_equipped:
            return self._equipment.wand
        elif self._equipment.weapon_equipped:
            return self._equipment.weapon
        else:
            return None

    @property
    def hit_point_total(self):
        """
This property returns the character's maximum hit points.

:return: An int.
        """
        return self._hit_point_maximum

    @property
    def hit_points(self):
        """
This property returns the character's current hit points.

:return: An int.
        """
        return self._current_hit_points

    @property
    def mana_points(self):
        """
This property returns the character's current mana points if any.

:return: An int.
        """
        return self._current_mana_points

    @property
    def mana_point_total(self):
        """
This property returns the character's maximum mana points if any.

:return: An int.
        """
        return self._mana_point_maximum

    def take_damage(self, damage_value):
        """
This method applies the given damage to the character's hit points.
If the hit points would be reduced to less than 0, they are set to 0
instead. The method returns the amount of damage assessed.

:damage_value: An int, the number of hit points to lose.
:return:       An int.
        """
        if self._current_hit_points - damage_value < 0:
            taken_amount = self._current_hit_points
            self._current_hit_points = 0
            return taken_amount
        else:
            self._current_hit_points -= damage_value
            return damage_value

    def heal_damage(self, healing_value):
        """
This method applies an amount of healing to the character's hit
points. If the healing would increase the hit points to more than the
character's maximum hit points, their hit point value is set to their
hit point maximum instead. The method returns the amount of healing
done.

:healing_value: An int, the number of hit points to recover.
:return:        An int.
        """
        if self._current_hit_points + healing_value > self._hit_point_maximum:
            amount_healed = self._hit_point_maximum - self._current_hit_points
            self._current_hit_points = self._hit_point_maximum
            return amount_healed
        else:
            self._current_hit_points += healing_value
            return healing_value

    def spend_mana(self, spent_amount):
        """
This method attempts to spend an amount of mana points from the
character's mana points, returning the amount spent if successful. If
the amount spent would reduce the character's mana points to less than
zero, no spending takes place, and 0 is returned to indicate failure.

:spent_amount: An int, the number of mana points to spend.
:return:       An int.
        """
        if self._current_mana_points < spent_amount:
            return 0
        else:
            self._current_mana_points -= spent_amount
            return spent_amount

    def regain_mana(self, regaining_value):
        """
This method regains mana points by the given value. If the amount
regained would increase the character's mana points to greater than
their maximum mana point total, their current mana point value is set
equal to their maximum mana point value instead. The method returns the
amount of mana points regained.

:regaining_value: An int, the number of mana points to regain.
:return:          An int.
        """
        if (self._current_mana_points + regaining_value
                > self._mana_point_maximum):
            amount_regained = self._mana_point_maximum - \
                self._current_mana_points
            self._current_mana_points = self._mana_point_maximum
            return amount_regained
        else:
            self._current_mana_points += regaining_value
            return regaining_value

    @property
    def is_alive(self):
        """
This property returns True if the character's hit point total is greater
than 0.

:return: A boolean.
        """
        return self._current_hit_points > 0

    @property
    def is_dead(self):
        """
This property returns True if the character's hit point total equals 0.

:return: A boolean.
        """
        return self._current_hit_points == 0

    @property
    def attack_roll(self):
        r"""
This property returns a dice expression usable by
adventuregame.utilities.roll_dice() to execute an attack roll during an
ATTACK command. It calculates the attack bonus from the equipped item
and the relevant ability score modifier.

:return: A string of the form '\d+d\d+([+-]\d+)?'.
        """

        # This standard for formulating attack rolls is drawn from
        # Dungeons & Dragon 3rd edition. Those rules can be found at
        # <https://dndsrd.net/>.
        #
        # If no weapon or wand is equipped, None is returned.

        if not (self._equipment.weapon_equipped
                or self._equipment.wand_equipped):
            return None

        # The ability score can be strength, dexterity or intelligence,
        # depending on class. Its modifier is added to the attack roll.

        stat_dependency = self._attack_or_damage_stat_dependency()

        # The item attacking with can have a bonus to attack. That is
        # added to the attack roll.

        item_attacking_with = self._item_attacking_with
        stat_mod = getattr(self.ability_scores, stat_dependency+"_mod")
        total_mod = item_attacking_with.attack_bonus + stat_mod
        mod_str = ("+" + str(total_mod) if total_mod > 0
                   else str(total_mod) if total_mod < 0
                   else "")

        # Attack rolls are resolved with a roll of a twenty-sided die.
        # .utility.roll_dice can interpret this return value into a
        # random number generation and execute it.

        return "1d20" + mod_str

    @property
    def damage_roll(self):
        r"""
This property returns a dice expression usable by
adventuregame.utilities.roll_dice() to execute a damage roll during an
ATTACK command. It calculates the damage dice value from the equipped
wand or weapon, and the relevant ability score modifier.

:return: A string of the form '\d+d\d+([+-]\d+)?'.
        """

        # This standard for formulating damage rolls is drawn from
        # Dungeons & Dragon 3rd edition. Those rules can be found at
        # <https://dndsrd.net/>.

        if not (self._equipment.weapon_equipped
                or self._equipment.wand_equipped):
            return None
        stat_dependency = self._attack_or_damage_stat_dependency()
        item_attacking_with = self._item_attacking_with
        item_dmg = item_attacking_with.damage

        # The item's damage is a die roll and an optional modifier. This
        # step splits that into the dice and the modifier.

        dmg_base_dice, dmg_mod = (item_dmg.split("+") if "+" in item_dmg
                                  else item_dmg.split("-") if "-" in item_dmg
                                  else (item_dmg, "0"))
        dmg_mod = int(dmg_mod)

        # The damage modifier needs to be adjusted by the stat mod from
        # above.

        total_dmg_mod = dmg_mod + getattr(self.ability_scores,
                                          stat_dependency+"_mod")
        dmg_str = dmg_base_dice + ("+" + str(total_dmg_mod)
                                   if total_dmg_mod > 0
                                   else str(total_dmg_mod)
                                   if total_dmg_mod < 0
                                   else "")

        # The dice expression is reassembled with the changed modifier,
        # and returned.

        return dmg_str

    # This class keeps its `Ability_Scores`, `Equipment` and
    # `Items_Multi_State` (Inventory) objects in private attributes,
    # just as a matter of good OOP design. In the cases of the
    # `Ability_Scores` and `Equipment` objects, these passthrough
    # methods are necessary so the concealed objects' functionality can
    # be accessed from code that only has the `Character` object.
    #
    # The `Items_Multi_State` inventory object presents a customized
    # mapping interface that Character action management code doesn't
    # need to access, so only a few methods are offered.

    def pick_up_item(self, item, qty=1):
        """
This method adds the given Item subclass object to the character's
inventory in the quantity specified, default 1.

:item:   An Item subclass object.
:qty:    An int, the quantity to add to the container, default 1.
:return: None.
        """
        have_qty = self.item_have_qty(item)
        if qty == 1:
            self.inventory.add_one(item.internal_name, item)
        else:
            self.inventory.set(item.internal_name, qty + have_qty, item)

    def drop_item(self, item, qty=1):
        """
This method removes the specified quantity (default 1) of the given Item
subclass object from the character's inventory.

:item:   An Item subclass object.
:qty:    An int, the quantity to remove from the container, default 1.
:return: None.
        """
        have_qty = self.item_have_qty(item)
        if have_qty == 0:
            raise KeyError(item.internal_name)
        if have_qty == qty:
            self.inventory.delete(item.internal_name)
        else:
            self.inventory.set(item.internal_name, have_qty - qty, item)

    def item_have_qty(self, item):
        """
This method checks whether the given Item subclass object is present in
the character's inventory. If so, it returns the quantity possessed. If
not, it returns 0.

:item:   An Item subclass object.
:return: An int.
        """
        if not self.inventory.contains(item.internal_name):
            return 0
        else:
            have_qty, _ = self.inventory.get(item.internal_name)
            return have_qty

    def have_item(self, item):
        """
This method checks whether the given Item subclass object is present in
the character's inventory. It returns True or False.

:item:   An Item subclass object.
:return: A boolean.
        """
        return self.inventory.contains(item.internal_name)

    def list_items(self):
        """
This method returns a sorted list of 2-tuples comprising an integer item
quantity and an Item subclass object. The list is ordered alphabetically
by the Item subclass object's title attributes.

:return: A list of 2-tuples.
        """
        return list(sorted(self.inventory.values(),
                           key=lambda *argl: argl[0][1].title))

    # BEGIN passthrough methods for private Ability_Scores
    @property
    def strength(self):
        """
This property returns the value for the Strength score stored in the
subordinate Ability_Scores object.

:return: An int.
        """
        return getattr(self.ability_scores, "strength")

    @property
    def dexterity(self):
        """
This property returns the value for the Dexterity score stored in the
subordinate Ability_Scores object.

:return: An int.
        """
        return getattr(self.ability_scores, "dexterity")

    @property
    def constitution(self):
        """
This property returns the value for the Constitution score stored in the
subordinate Ability_Scores object.

:return: An int.
        """
        return getattr(self.ability_scores, "constitution")

    @property
    def intelligence(self):
        """
This property returns the value for the Intelligence score stored in the
subordinate Ability_Scores object.

:return: An int.
        """
        return getattr(self.ability_scores, "intelligence")

    @property
    def wisdom(self):
        """
This property returns the value for the Wisdom score stored in the
subordinate Ability_Scores object.

:return: An int.
        """
        return getattr(self.ability_scores, "wisdom")

    @property
    def charisma(self):
        """
This property returns the value for the Charisma score stored in the
subordinate Ability_Scores object.

:return: An int.
        """
        return getattr(self.ability_scores, "charisma")

    @property
    def strength_mod(self):
        """
This property returns the Strength ability score modifier from the
subordinate Ability_Scores object.

:return: An int.
        """
        return self.ability_scores._stat_mod("strength")

    @property
    def dexterity_mod(self):
        """
This property returns the Dexterity ability score modifier from the
subordinate Ability_Scores object.

:return: An int.
        """
        return self.ability_scores._stat_mod("dexterity")

    @property
    def constitution_mod(self):
        """
This property returns the Constitution ability score modifier from the
subordinate Ability_Scores object.

:return: An int.
        """
        return self.ability_scores._stat_mod("constitution")

    @property
    def intelligence_mod(self):
        """
This property returns the Intelligence ability score modifier from the
subordinate Ability_Scores object.

:return: An int.
        """
        return self.ability_scores._stat_mod("intelligence")

    @property
    def wisdom_mod(self):
        """
This property returns the Wisdom ability score modifier from the
subordinate Ability_Scores object.

:return: An int.
        """
        return self.ability_scores._stat_mod("wisdom")

    @property
    def charisma_mod(self):
        """
This property returns the Charisma ability score modifier from the
subordinate Ability_Scores object.

:return: An int.
        """
        return self.ability_scores._stat_mod("charisma")
    # END passthrough methods for private Ability_Scores

    # BEGIN passthrough methods for private _equipment
    @property
    def armor_equipped(self):
        """
This property returns the armor_equipped property from the subordinate
Equipment object.

:return: An Armor object, or None.
        """
        return self._equipment.armor_equipped

    @property
    def shield_equipped(self):
        """
This property returns the shield_equipped property from the subordinate
Equipment object.

:return: A Shield object, or None.
        """
        return self._equipment.shield_equipped

    @property
    def weapon_equipped(self):
        """
This property returns the weapon_equipped property from the subordinate
Equipment object.

:return: A Weapon object, or None.
        """
        return self._equipment.weapon_equipped

    @property
    def wand_equipped(self):
        """
This property returns the wand_equipped property from the subordinate
Equipment object.

:return: A Wand object, or None.
        """
        return self._equipment.wand_equipped

    @property
    def armor(self):
        """
This property returns the armor property from the subordinate Equipment
object.

:return: An Armor object, or None.
        """
        return self._equipment.armor

    @property
    def shield(self):
        """
This property returns the shield property from the subordinate Equipment
object.

:return: A Shield object, or None.
        """
        return self._equipment.shield

    @property
    def weapon(self):
        """
This property returns the weapon property from the subordinate Equipment
object.

:return: A Weapon object, or None.
        """
        return self._equipment.weapon

    @property
    def wand(self):
        """
This property returns the wand property from the subordinate Equipment
object.

:return: A Wand object, or None.
        """
        return self._equipment.wand

    def equip_armor(self, item):
        """
This method calls the equip_armor method on the subordinate Equipment
object with the given argument.

:item:   An Armor object.
:return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise excpt.Internal_Exception(
                "equipping an `item` object that is not in the "
                "character's `inventory` object is not allowed")
        return self._equipment.equip_armor(item)

    def equip_shield(self, item):
        """
This method calls the equip_shield method on the subordinate Equipment
object with the given argument.

:item:   A Shield object.
:return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise excpt.Internal_Exception(
                "equipping an `item` object that is not in the "
                "character's `inventory` object is not allowed")
        return self._equipment.equip_shield(item)

    def equip_weapon(self, item):
        """
This method calls the equip_weapon method on the subordinate Equipment
object with the given argument.

:item:   A Weapon object.
:return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise excpt.Internal_Exception(
                "equipping an `item` object that is not in the "
                "character's `inventory` object is not allowed")
        return self._equipment.equip_weapon(item)

    def equip_wand(self, item):
        """
This method calls the equip_wand method on the subordinate Equipment
object with the given argument.

:item:   A Wand object.
:return: None.
        """
        if not self.inventory.contains(item.internal_name):
            raise excpt.Internal_Exception(
                "equipping an `item` object that is not in the "
                "character's `inventory` object is not allowed")
        return self._equipment.equip_wand(item)

    def unequip_armor(self):
        """
This method calls the unequip_armor method on the subordinate Equipment
object.

:return: None.
        """
        return self._equipment.unequip_armor()

    def unequip_shield(self):
        """
This method calls the unequip_shield method on the subordinate Equipment
object.

:return: None.
        """
        return self._equipment.unequip_shield()

    def unequip_weapon(self):
        """
This method calls the unequip_weapon method on the subordinate Equipment
object.

:return: None.
        """
        return self._equipment.unequip_weapon()

    def unequip_wand(self):
        """
This method calls the unequip_wand method on the subordinate Equipment
object.

:return: None.
        """
        return self._equipment.unequip_wand()
    # END passthrough methods for private _equipment

    # These aren't passthrough methods because the `_equipment` returns
    # values for these Character parameters that are informed only by
    # the Equipment it stores. At the level of the `Character` object,
    # these values should also be informed by the character's ability
    # scores stores in the `Ability_Scores`. A character's armor class
    # is modified by their dexterity modifier; and their attack & damage
    # values are modified by either their strength score (for Warriors,
    # Priests, and Mages using a Weapon), or Dexterity (for Thieves), or
    # Intelligence (for Mages using a Wand).

    @property
    def armor_class(self):
        """
This property returns the character's ability score as computed from
their equipments' armor bonuses and their Dexterity modifier.

:return: An int.
        """
        armor_class = self._equipment.armor_class
        dexterity_mod = self.ability_scores.dexterity_mod
        return armor_class + dexterity_mod

    @property
    def attack_bonus(self):
        """
This property returns the character's attack bonus as computed from
their weapon or wand's attack bonus and their relevant ability score
modifier (Strength for Warriors, Priests and Mages wielding a weapon;
Dexterity for Thieves; and Intelligence for Mages wielding a wand).

:return: An int.
        """

        # A character with no weapon or wand has no attack bonus.

        if (not (self._equipment.weapon_equipped
                 or self.character_class == "Mage"
                 and self._equipment.wand_equipped)):
            raise excpt.Internal_Exception(
                "The character does not have a weapon equipped; no valid "
                "value for `attack_bonus` can be computed.")
        stat_dependency = self._attack_or_damage_stat_dependency()

        # By the shield statement above, I know that the control flow
        # getting here means that if no weapon is equipped a wand must
        # be.

        if self.character_class == "Mage":
            base_attack_bonus = (self._equipment.wand.attack_bonus
                                 if self._equipment.wand_equipped
                                 else self._equipment.weapon.attack_bonus)
        else:
            base_attack_bonus = self._equipment.weapon.attack_bonus

        # The attack bonus is drawn from the weapon or wand's attack
        # bonus plus the relevant stat mod.

        return base_attack_bonus + getattr(self.ability_scores,
                                           stat_dependency + '_mod')


class Creature(IniEntry, Character):
    """
This class uses multiple inheritance to subclass both IniEntry and
Character. It is instantiated from an .ini file entry, but draws on all
the game rules entity logic in Character to have access to the same
mechanics as a character.
    """
    __slots__ = ("internal_name", "character_name", "description",
                 "character_class", "species", "_strength", "_dexterity",
                 "_constitution", "_intelligence", "_wisdom", "_charisma",
                 "_items_state", "_base_hit_points", "_weapon_equipped",
                 "_armor_equipped", "_shield_equipped")

    def __init__(self, items_state, internal_name, **argd):
        """
This __init__ method initializes the object using super() to call
__init__ methods from both IniEntry and Character. It sets the ability
scores, populates its inventory, and sets up its equipment from its ini
file data.

:items_state:   An Items_State object.
:internal_name: A string, the internal name of the creature.
:**argd:        A dict, the key-value pairs to instantiate the
                Creature object from.
        """

        # _separate_argd_into_different_arg_sets() is a utility function
        # that separates all the .ini key-value pairs into args for
        # Character.__init__, args for IniEntry.__init__, attributes
        # that can be used to initialize an Equipment object, and
        # quantity/internal_name pairs that can be used to initialize an
        # Inventory object.

        char_init_argd, ini_entry_init_argd, equip_argd, invent_qty_pairs = \
            self._seprt_argd_into_diff_arg_sets(
                items_state, internal_name, **argd)
        IniEntry.__init__(self, internal_name=internal_name,
                          **ini_entry_init_argd)
        self._post_init_slots_set_none(self.__slots__)
        Character.__init__(self, **char_init_argd)

        # The IniEntry.__init__ and Character.__init__ steps
        # are complete. _init_invent_and_equip handles the other
        # initializations with invent_qty_pairs and equip_argd as
        # arguments.

        self._init_inventory_and_equipment(items_state, invent_qty_pairs,
                                           equip_argd)
        self._items_state = items_state

    # Divides the argd passed to __init__ into arguments for
    # Character.__init__, arguments for IniEntry.__init__, arguments to
    # Character.equip_*, and arguments to Character.pick_up_item.
    #
    # argd is accepted as a ** argument, so it's passed by copy rather
    # than by reference.

    def _seprt_argd_into_diff_arg_sets(self, items_state, intrn_name, **argd):
        """
This private method takes the argd supplied to __init__ and separates
it into Character.__init__() arguments, IniEntry.__init__() arguments,
inventory quantity-internal name pairs, and an equipment dict.

:items_state:   An Items_State object.
:intrn_name: A string, the creature's internal name.
:**argd:        The key-value pairs to differentiate into different
                sets of arguments.
        """

        # Character's __init__ args are formed first. dict.pop is used
        # so this step removes those values from argd as they're added
        # to char_init_argd.

        char_init_argd = {
            "strength": int(argd.pop("strength")),
            "dexterity": int(argd.pop("dexterity")),
            "constitution": int(argd.pop("constitution")),
            "intelligence": int(argd.pop("intelligence")),
            "wisdom": int(argd.pop("wisdom")),
            "charisma": int(argd.pop("charisma")),
            "base_hit_points": int(argd.pop("base_hit_points")),
            "character_name_str": argd.pop("character_name"),
            "character_class_str": argd.pop("character_class"),
            "base_mana_points": int(argd.pop("base_mana_points", 0)),
            "magic_key_stat": argd.pop("magic_key_stat", None)
        }

        # Equipment argd is next, *_equipped key-values are popped from
        # argd and added to equip_argd.

        equip_argd = dict()
        for ini_key in ("weapon_equipped", "armor_equipped",
                        "shield_equipped", "wand_equipped"):
            if ini_key not in argd:
                continue
            equip_argd[ini_key] = argd.pop(ini_key)

        # The item quantity/intrn_name pairs are unpacked from
        # 'inventory_items' using _process_list_value, which is
        # inherited from IniEntry and uses the standard item qty/name
        # compact notation.

        invent_qty_name_pairs = self._process_list_value(
            argd.pop("inventory_items"))

        # If any item internal names don't occur in items_state an
        # exception is raised.

        if any(not items_state.contains(invent_intrn_name)
               for _, invent_intrn_name in invent_qty_name_pairs):
            missing_names = tuple(item_intrn_name
                                  for _, item_intrn_name
                                  in invent_qty_name_pairs
                                  if not items_state.contains(item_intrn_name))
            pluralizer = "s" if len(missing_names) > 1 else ""
            raise excpt.Internal_Exception(
                f"bad creatures.ini specification for creature "
                f"{intrn_name}: creature ini config dict "
                f"`inventory_items` value indicated item{pluralizer} not "
                "present in `Items_State` argument: "
                + (", ".join(missing_names)))

        # The remaining argd is for IniEntry.__init__. And the four
        # argds are returned.

        ini_entry_init_argd = argd
        return (char_init_argd, ini_entry_init_argd,
                equip_argd, invent_qty_name_pairs)

    def _init_inventory_and_equipment(self, items_state, invent_qty_name_pairs,
                                      equip_argd):
        """
This private method accepts an items state, inventory quantity-internal
name pairs, and the equipment dict, and uses them to initialize the
creature's inventory and equipped items.

:items_state:              An Items_State object.
:invent_qty_name_pairs: A tuple of 2-tuples of item quantity ints
                           and internal name strings.
:equip_argd:           A dictionary of equipment assignments.
        """

        # The internal_name pairs in invent_qty_name_pairs are used to
        # look up Item subclass objects and those objects are saved to
        # the Character object's inventory.

        for item_qty, item_internal_name in invent_qty_name_pairs:
            item = items_state.get(item_internal_name)
            self.pick_up_item(item, qty=item_qty)

        # The *_equipped key-values are used to equip items from the
        # inventory, if they're there. If any points to an object not in
        # inventory an exception is raised.

        for equip_key, item_internal_name in equip_argd.items():
            if not items_state.contains(item_internal_name):
                raise excpt.Internal_Exception(
                    "bad creatures.ini specification for creature "
                    f"{self.internal_name}: items index object does not "
                    f"contain an item named {item_internal_name}")
            item = items_state.get(item_internal_name)
            if equip_key == "weapon_equipped":
                self.equip_weapon(item)
            elif equip_key == "armor_equipped":
                self.equip_armor(item)
            elif equip_key == "shield_equipped":
                self.equip_shield(item)
            else:  # by exclusion, the value must be "wand_equipped"
                self.equip_wand(item)

    def convert_to_corpse(self):
        """
This method is used when a creature has been defeated in combat and its
presence in a Room object needs to be converted from a creature to a
container (subclass corpse).

:return: A Corpse object.
        """
        internal_name = self.internal_name
        description = self.description_dead
        title = f"{self.title} corpse"
        corpse = Corpse(self._items_state, internal_name,
                        container_type="corpse",
                        description=description, title=title)

        # The items in inventory are saved to the new Corpse object's
        # contents.

        for item_internal_name, (item_qty, item) in self.inventory.items():
            corpse.set(item_internal_name, item_qty, item)
        return corpse


class CreaturesState(State):
    """
This State subclass is instantiated from the sections attribute of an
IniConfig object instantiated from creatures.ini.
    """

    def __init__(self, items_state, **dict_of_dicts):
        """
This __init__ method accepts an items_state object and a **dict-of-dicts
as offered by an IniConfig object's sections attribute. It instantiates
and stores a Creature object for each section of the **dict-of-dicts.
Unlike other *_State classes it doesn't use a subclassing_factory
because the Creature class is not subclassed to delineate different
types of creature.

:items_state:     An Items_State object.
:**dict_of_dicts: A structure of internal name keys corresponding to
                  dict values which are key-value pairs to initialize an
                  individual Creature object with.
        """
        self._contents = dict()
        for creature_internal_name, creature_dict in dict_of_dicts.items():
            creature = Creature(items_state,
                                internal_name=creature_internal_name,
                                **creature_dict)
            self.set(creature.internal_name, creature)


class Room(IniEntry):
    """
This IniEntry subclass represents a single room. It is instantiated
from a single section of a doors.ini file as returned by an IniConfig's
dict-of-dicts sections attribute.
    """
    __slots__ = ('internal_name', 'title', 'description', 'north_door',
                 'west_door', 'south_door', 'east_door', 'occupant', 'item',
                 'is_entrance', 'is_exit', '_containers_state',
                 '_creatures_state', '_doors_state', '_items_state',
                 'creature_here', 'container_here', 'items_here')

    @property
    def has_north_door(self):
        """
This property returns True if the object has a nonempty north_door
value, False otherwise.

:return: A boolean.
        """
        return bool(getattr(self, "north_door", False))

    @property
    def has_east_door(self):
        """
This property returns True if the object has a nonempty east_door value,
False otherwise.

:return: A boolean.
        """
        return bool(getattr(self, "east_door", False))

    @property
    def has_south_door(self):
        """
This property returns True if the object has a nonempty south_door
value, False otherwise.

:return: A boolean.
        """
        return bool(getattr(self, "south_door", False))

    @property
    def has_west_door(self):
        """
This property returns True if the object has a nonempty west_door value,
False otherwise.

:return: A boolean.
        """
        return bool(getattr(self, "west_door", False))

    def __init__(self, creatures_state, containers_state, doors_state,
                 items_state, **argd):
        """
This __init__ method defines a room object as given in a single section
of rooms.ini. It needs a creatures_state object, a containers_state
object, a doors_state object and an items_state object. It initializes
the object from its argd, drawing on the state objects to set the
creature_here, container_here, items_here and the {compass_dir}_door
attributes.

:creatures_state:  A Creatures_State object.
:containers_state: A Containers_State object.
:doors_state:      A Doors_State object.
:items_state:      An Items_State object.
:**argd:           A dict of key-value pairs to instantiate the Room
                   object with.
        """
        super().__init__(**argd)
        self._containers_state = containers_state
        self._creatures_state = creatures_state
        self._items_state = items_state
        self._doors_state = doors_state
        self._post_init_slots_set_none(self.__slots__)

        # If a creature_here attribute is set, that value is taken as an
        # internal_name, looked up in creatures_state, and the matching
        # creature is saved to creature_here.

        if self.creature_here:
            if not self._creatures_state.contains(self.creature_here):
                raise excpt.Internal_Exception(
                    f"room obj `{self.internal_name}` creature_here value "
                    f"'{self.creature_here}' doesn't correspond to any "
                    "creatures in creatures_state store")
            self.creature_here = self._creatures_state.get(self.creature_here)

        # If a container_here attribute is set, that value is taken
        # as an internal_name, looked up in containers_state, and the
        # matching container is saved to container_here.

        if self.container_here:
            if not self._containers_state.contains(self.container_here):
                raise excpt.Internal_Exception(
                    f"room obj `{self.internal_name}` container_here "
                    f"value '{self.container_here}' doesn't correspond to "
                    "any creatures in creatures_state store")
            self.container_here = self._containers_state.get(
                self.container_here)

        # If an items_here attribute is set, it's parsed as the
        # compact item quantity/internal_name as interpretable
        # by IniEntry._process_list_value(), and the resultant
        # Items_Multi_State object is assigned to items_here.

        if self.items_here:
            items_here_names_list = self._process_list_value(self.items_here)
            items_state = ItemsMultiState()
            for item_qty, item_internal_name in items_here_names_list:
                item = self._items_state.get(item_internal_name)
                items_state.set(item_internal_name, item_qty, item)
            self.items_here = items_state
        for compass_dir in ("north", "east", "south", "west"):
            door_attr = f"{compass_dir}_door"
            if not getattr(self, door_attr, False):
                continue
            sorted_pair = tuple(sorted((self.internal_name,
                                        getattr(self, door_attr))))
            if sorted_pair[0].lower() == "exit":
                sorted_pair = tuple(reversed(sorted_pair))

            # The Door objects stored in each Room object are not
            # identical with the Door objects in self._doors_state
            # because each Door gets a new title based on its compass
            # direction; the same Door can be titled "north door" in the
            # southern of the two rooms it connects and "south door" in
            # the northern one.

            door = self._doors_state.get(*sorted_pair).copy()
            door.title = (f"{compass_dir} doorway" if door.title == "doorway"
                          else f"{compass_dir} door")
            setattr(self, door_attr, door)

    @property
    def doors(self):
        """
This property returns a tuple comprising the Door subclass objects
attached to this Room object.

:return: A tuple of Door objects.
        """
        doors_tuple = ()

        # This method is just a shorthand for accessing the
        # has_(north|south|east|west)_door attributes.

        for compass_dir in ("north", "east", "south", "west"):
            has_door_property = f"has_{compass_dir}_door"
            if not getattr(self, has_door_property):
                continue
            doors_tuple += getattr(self, f"{compass_dir}_door"),
        return doors_tuple


class RoomsState(object):
    """
This class implements a state object that tracks the entire dungeon's
layout.
    """
    __slots__ = ("_creatures_state", "_containers_state", "_items_state",
                 "_doors_state", "_rooms_objs", "_room_cursor")

    @property
    def cursor(self):
        """
This property returns the Room object that the Rooms_State object
considers the player to currently be occupying.

:return: A Room object.
        """
        return self._rooms_objs[self._room_cursor]

    def __init__(self, creatures_state, containers_state, doors_state,
                 items_state, **dict_of_dicts):
        """
This __init__method instantiates every room object, given a
creatures_state object, a containers_state object, a doors_state object
and an items_state object to initialize them with, and a **dict-of-dicts
from rooms.ini as furnished by an IniConfig's sections attribute.

:creatures_state:  A Creatures_State object.
:containers_state: A Containers_State object.
:doors_state:      A Doors_State object.
:items_state:      A Items_State object.
:**dict_of_dicts:  A structure of internal name keys corresponding to
                   dict values which are key-value pairs to initialize
                   an individual Creature object with.
        """
        self._rooms_objs = dict()
        self._creatures_state = creatures_state
        self._containers_state = containers_state
        self._doors_state = doors_state
        self._items_state = items_state

        # The Room objects contained by this object are initialized from
        # **dict_of_dicts.

        for room_internal_name, room_dict in dict_of_dicts.items():
            room = Room(creatures_state, containers_state, doors_state,
                        items_state, internal_name=room_internal_name,
                        **room_dict)

            # The cursor is set to the room identifies by
            # is_entrance=True

            if room.is_entrance:
                self._room_cursor = room.internal_name
            self.set(room.internal_name, room)

    def get(self, internal_name):
        """
This method is used to retrieve a Room object from internal storage with
the given internal name.

:room_internal_name: A string, the internal name of the Room object.
:return:             A Room object.
        """
        return self._rooms_objs[internal_name]

    def set(self, internal_name, room):
        """
This method is used to store a Room object to internal storage by the
given internal name.

:room_internal_name: A string, the internal name of the Room object.
:room:               A Room object.
:return:             None.
        """
        self._rooms_objs[internal_name] = room

    def move(self, north=False, west=False, south=False, east=False):
        """
This method directs the Rooms_State object to move the cursor from the
current room to an adjacent room by the given compass direction.

:north:  A boolean, True if movement to the north is intended, False
         otherwise.
:east:   A boolean, True if movement to the east is intended, False
         otherwise.
:south:  A boolean, True if movement to the south is intended, False
         otherwise.
:west:   A boolean, True if movement to the west is intended, False
         otherwise.
:return: None.
        """

        # If more than one of north, east, south and west are True,
        # raise an exception.

        if ((north and west) or (north and south) or (north and east)
                or (west and south) or (west and east) or (south and east)):
            raise excpt.Internal_Exception(
                "move() must receive only *one* True argument of the four "
                "keys `north`, `south`, `east` and `west`")
        if north:
            exit_name = "north_door"
            exit_key = "NORTH"
        elif west:
            exit_name = "west_door"
            exit_key = "WEST"
        elif south:
            exit_name = "south_door"
            exit_key = "SOUTH"
        elif east:
            exit_name = "east_door"
            exit_key = "EAST"

        # If the Room doesn't have a matching exit, an exception is
        # raised.

        if not getattr(self.cursor, exit_name):
            raise excpt.Bad_Command_Exception(
                "MOVE", f"This room has no <{exit_key}> exit.")
        door = getattr(self.cursor, exit_name)

        # If the Door object has is_locked=True, an exception is raised.

        if door.is_locked:
            raise excpt.Internal_Exception(
                f"exiting {self.cursor.internal_name} via the "
                f"{exit_name.replace('_',' ')}: door is locked")

        # The Door object returns the other Room object it connects to;
        # the value for cursor is updated by setting _room_cursor to
        # that Room object's internal_name.

        other_room_internal_name = door.other_room_internal_name(
            self.cursor.internal_name)
        new_room_dest = self._rooms_objs[other_room_internal_name]
        self._room_cursor = new_room_dest.internal_name


class GameState(object):
    """
This class represents the entire Game_State needed to run a
session of AdventureGame. It is the top-level object, and stores an
items_state object, a doors_state object, a containers_state object,
a creatures_state object, a rooms_state object, and (once it can be
instantiated) a character object.
    """
    __slots__ = ("_character_name", "_character_class", "character",
                 "rooms_state", "containers_state", "doors_state",
                 "items_state", "creatures_state", "game_has_begun",
                 "game_has_ended")

    @property
    def character_name(self):
        """
This property returns the character name.

:return: A string.
        """
        return self._character_name

    @character_name.setter
    def character_name(self, name_str):
        """
This property sets the character name, and contains a hook to attempt to
instantiate the character object if both the name and class have been
set.

:name_str: A string, the character name.
:return:   None.
        """
        setattr(self, "_character_name", name_str)
        self._incept_character_obj_if_possible()

    @property
    def character_class(self):
        """
This property returns the character class.

:return: A string, one of 'Warrior', 'Thief', 'Mage', or 'Priest'.
        """
        return self._character_class

    @character_class.setter
    def character_class(self, class_str):
        """
This property sets the character class, and contains a hook to attempt
to instantiate the character object if both the name and class have been
set.

:name_str: A string, the character class.
:return:   None.
        """
        setattr(self, "_character_class", class_str)
        self._incept_character_obj_if_possible()

    def __init__(self, rooms_state, creatures_state, containers_state,
                 doors_state, items_state):
        """
This __init__ method stores an items_state object, a doors_state object,
a containers_state object, a creatures_state object, and a rooms_state
object from its arguments.

:rooms_state:      A Rooms_State object.
:creatures_state:  A Creatures_State object.
:containers_state: A Containers_State object.
:doors_state:      A Doors_State object.
:items_state:      An Items_State object.
        """
        self.items_state = items_state
        self.doors_state = doors_state
        self.containers_state = containers_state
        self.creatures_state = creatures_state
        self.rooms_state = rooms_state
        self._character_name = None
        self._character_class = None
        self.game_has_begun = False
        self.game_has_ended = False
        self.character = None

    # The Character object can't be instantiated until the
    # `character_name` and `character_class` attributes are set, but
    # that happens after initialization; so the `character_name` and
    # `character_class` setters call this method prospectively each time
    # either is called to check if both have been set and `Character`
    # object instantiation can proceed.

    def _incept_character_obj_if_possible(self):
        """
This private method is called by the character_name and character_class
property setters, and it instantiates the Character object if both the
character name and the character class have been set.

:return: None.
        """
        if (self.character is None and getattr(self, "character_name", None)
                and getattr(self, "character_class", None)):
            self.character = Character(self.character_name,
                                       self.character_class)
