#!/usr/bin/python3

from collections import defaultdict

from advgame.elements.basics import IniEntry
from advgame.errors import InternalError


__all__ = (
    "Door",
    "IronDoor",
    "WoodenDoor",
    "DoorsState",
    "Doorway",
)


class Door(IniEntry):
    """
    The Item subclass of IniEntry represents a single door. It is
    instantiated from a single section of a doors.ini file as returned by an
    IniConfig's dict-of-dicts sections attribute.
    """

    __slots__ = (
        "internal_name",
        "title",
        "description",
        "door_type",
        "is_locked",
        "is_closed",
        "closeable",
        "_linked_rooms_internal_names",
        "is_exit",
    )

    def __init__(self, **argd):
        """
        The __init__ method uses super() to call IniEntry.__init__ to
        populate the object with attributes from argd. It then sets all unset
        attributes to None and parses the internal name (which has the form
        'Room_#,#_x_Room_#,#') to detect which two rooms are joined by
        this
        door.

        :**argd: The key-value pairs to initialize the Door object with.
        """
        super().__init__(**argd)
        self._post_init_slots_set_none(self.__slots__)
        self._linked_rooms_internal_names = set(self.internal_name.split("_x_"))

    @classmethod
    def subclassing_factory(cls, **door_dict):
        """
        Like Item.subclassing_factory, this factory method accepts an argd and
        detects which Door subclass should be instantiated from the arguments by
        reading the door_type value.

        :**door_dict: The key-value pairs to initialize the Door subclass object
        with.
        """
        if door_dict["door_type"] == "doorway":
            door = Doorway(**door_dict)
        elif door_dict["door_type"] == "wooden_door":
            door = WoodenDoor(**door_dict)
        elif door_dict["door_type"] == "iron_door":
            door = IronDoor(**door_dict)
        else:
            raise InternalError(f'unrecognized door type: {door_dict["door_type"]}')
        return door

    def other_room_internal_name(self, room_internal_name):
        """
        This method accepts the internal name of a room which is one of the two
        rooms linked by this door, and returns the internal name of the other
        room in the linkage.

        :room_internal_name: The internal name of a Room object.
        :return: A Room object.
        """

        if room_internal_name not in self._linked_rooms_internal_names:
            raise InternalError(
                f"room internal name {room_internal_name} not one of the "
                f"two rooms linked by this door object"
            )

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
        return self.__class__(
            **{attr: getattr(self, attr, None) for attr in self.__slots__}
        )


class IronDoor(Door):
    """
    This Door subclass is used to represent doors which are iron. It offers
    no functionality, but is useful for detecting iron doors by type
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


class DoorsState:
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
        dict values which are key-value pairs to initialize an individual Door
        object with.
        """
        self._contents = defaultdict(dict)

        # The entries in doors.ini have internal_names that consist of
        # the internal names for the two rooms they connect, connected
        # by '_x_'. This loop recovers the two room internal names for
        # each .ini entry and stores the Door subclass object in a
        # dict-of-dicts under the two room internal names.

        for door_internal_name, door_argd in dict_of_dicts.items():
            room_1_intrn_name, room_2_intrn_name = door_internal_name.split("_x_")
            self._contents[room_1_intrn_name][
                room_2_intrn_name
            ] = Door.subclassing_factory(internal_name=door_internal_name, **door_argd)
            pass

    def contains(self, room_1_intrn_name, room_2_intrn_name):
        """
        This method tests whether a Door subclass object indexed by the given
        two Room subclass object's internal names is present in the internal
        **dict-of-dicts.

        :room_1_intern_name: The internal name of one of the two linked Room
        objects.
        :room_2_intern_name: The internal name of the other of the two linked
        Room objects.
        :return: A boolean.
        """
        return (
            room_1_intrn_name in self._contents
            and room_2_intrn_name in self._contents[room_1_intrn_name]
        )

    def get(self, room_1_intrn_name, room_2_intrn_name):
        """
        This method returns the Door subclass object indexed by the two given
        Room subclass object internal names, or raises a KeyError if it's not
        present.

        :room_1_intern_name: The internal name of one of the two linked Room
        objects.
        :room_2_intern_name: The internal name of the other of the two linked
        Room objects.
        :return: A Door object.
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
        :room_2_intern_name: The internal name of the other of the two linked
        Room objects.
        :door: A Door object.
        :return: None.
        """
        self._contents[room_1_intrn_name][room_2_intrn_name] = door

    def delete(self, room_1_intrn_name, room_2_intrn_name):
        """
        This method deletes the Door subclass object found in the internal
        **dict-of-dicts under the given two Room subclass object internal name
        keys.

        :room_1_intern_name: The internal name of one of the two linked Room
        objects.
        :room_2_intern_name: The internal name of the other of the two linked
        Room objects.
        :door: A Door object.
        :return: None.
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

        :return: A list of 3-tuples, comprised of a string (the internal name),
        an int (the quantity) and an Item subclass object.
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


class Doorway(Door):
    """
    This Door subclass is used to represent doors which are doorways. It
    offers no functionality, but is useful for detecting doorways by type
    testing.
    """

    pass
