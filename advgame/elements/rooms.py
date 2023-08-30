#!/usr/bin/python3

from advgame.elements.basics import IniEntry
from advgame.elements.characters import ItemsMultiState
from advgame.errors import InternalError, BadCommandError


__all__ = "Room", "RoomsState"


class Room(IniEntry):
    """
    This IniEntry subclass represents a single room. It is instantiated
    from a single section of a doors.ini file as returned by an IniConfig's
    dict-of-dicts sections attribute.
    """

    __slots__ = (
        "internal_name",
        "title",
        "description",
        "north_door",
        "west_door",
        "south_door",
        "east_door",
        "occupant",
        "item",
        "is_entrance",
        "is_exit",
        "_containers_state",
        "_creatures_state",
        "_doors_state",
        "_items_state",
        "creature_here",
        "container_here",
        "items_here",
    )

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

    def __init__(
        self, creatures_state, containers_state, doors_state, items_state, **argd
    ):
        """
        This __init__ method defines a room object as given in a single section
        of rooms.ini. It needs a creatures_state object, a containers_state
        object, a doors_state object and an items_state object. It initializes
        the object from its argd, drawing on the state objects to set the
        creature_here, container_here, items_here and the {compass_dir}_door
        attributes.

        :creatures_state: A CreaturesState object.
        :containers_state: A ContainersState object.
        :doors_state: A DoorsState object.
        :items_state: An ItemsState object.
        :**argd: A dict of key-value pairs to instantiate the Room object with.
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
                raise InternalError(
                    f"room obj `{self.internal_name}` creature_here value "
                    + f"'{self.creature_here}' doesn't correspond to any "
                    + "creatures in creatures_state store"
                )
            self.creature_here = self._creatures_state.get(self.creature_here)

        # If a container_here attribute is set, that value is taken
        # as an internal_name, looked up in containers_state, and the
        # matching container is saved to container_here.

        if self.container_here:
            if not self._containers_state.contains(self.container_here):
                raise InternalError(
                    f"room obj `{self.internal_name}` container_here value "
                    + f"'{self.container_here}' doesn't correspond to any "
                    + "creatures in creatures_state store"
                )
            self.container_here = self._containers_state.get(self.container_here)

        # If an items_here attribute is set, it's parsed as the
        # compact item quantity/internal_name as interpretable
        # by IniEntry._process_list_value(), and the resultant
        # ItemsMultiState object is assigned to items_here.

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
            sorted_pair = tuple(sorted((self.internal_name, getattr(self, door_attr))))
            if sorted_pair[0].lower() == "exit":
                sorted_pair = tuple(reversed(sorted_pair))

            # The Door objects stored in each Room object are not
            # identical with the Door objects in self._doors_state
            # because each Door gets a new title based on its compass
            # direction; the same Door can be titled "north door" in the
            # southern of the two rooms it connects and "south door" in
            # the northern one.

            door = self._doors_state.get(*sorted_pair).copy()
            door.title = (
                f"{compass_dir} doorway"
                if door.title == "doorway"
                else f"{compass_dir} door"
            )
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
            doors_tuple += (getattr(self, f"{compass_dir}_door"),)
        return doors_tuple


class RoomsState:
    """
    This class implements a state object that tracks the entire dungeon's
    layout.
    """

    __slots__ = (
        "_creatures_state",
        "_containers_state",
        "_items_state",
        "_doors_state",
        "_rooms_objs",
        "_room_cursor",
    )

    @property
    def cursor(self):
        """
        This property returns the Room object that the RoomsState object
        considers the player to currently be occupying.

        :return: A Room object.
        """
        return self._rooms_objs[self._room_cursor]

    def __init__(
        self,
        creatures_state,
        containers_state,
        doors_state,
        items_state,
        **dict_of_dicts,
    ):
        """
        This __init__method instantiates every room object, given a
        creatures_state object, a containers_state object, a doors_state object
        and an items_state object to initialize them with, and a **dict-of-dicts
        from rooms.ini as furnished by an IniConfig's sections attribute.

        :creatures_state: A CreaturesState object.
        :containers_state: A ContainersState object.
        :doors_state: A DoorsState object.
        :items_state: A ItemsState object.
        :**dict_of_dicts: A structure of internal name keys corresponding to
        dict values which are key-value pairs to initialize an individual
        Creature object with.
        """
        self._rooms_objs = dict()
        self._creatures_state = creatures_state
        self._containers_state = containers_state
        self._doors_state = doors_state
        self._items_state = items_state

        # The Room objects contained by this object are initialized from
        # **dict_of_dicts.

        for room_internal_name, room_dict in dict_of_dicts.items():
            room = Room(
                creatures_state,
                containers_state,
                doors_state,
                items_state,
                internal_name=room_internal_name,
                **room_dict,
            )

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
        :return: A Room object.
        """
        return self._rooms_objs[internal_name]

    def set(self, internal_name, room):
        """
        This method is used to store a Room object to internal storage by the
        given internal name.

        :room_internal_name: A string, the internal name of the Room object.
        :room: A Room object.
        :return: None.
        """
        self._rooms_objs[internal_name] = room

    def move(self, north=False, west=False, south=False, east=False):
        """
        This method directs the RoomsState object to move the cursor from the
        current room to an adjacent room by the given compass direction.

        :north: A boolean, True if movement to the north is intended, False
        otherwise.
        :east: A boolean, True if movement to the east is intended, False
        otherwise.
        :south: A boolean, True if movement to the south is intended, False
        otherwise.
        :west: A boolean, True if movement to the west is intended, False
        otherwise.
        :return: None.
        """

        # If more than one of north, east, south and west are True,
        # raise an exception.
        exit_name = None
        exit_key = None

        if (
            (north and west)
            or (north and south)
            or (north and east)
            or (west and south)
            or (west and east)
            or (south and east)
        ):
            raise InternalError(
                "move() must receive only *one* True argument of the four "
                + "keys `north`, `south`, `east` and `west`"
            )
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
            raise BadCommandError("MOVE", f"This room has no <{exit_key}> exit.")
        door = getattr(self.cursor, exit_name)

        # If the Door object has is_locked=True, an exception is raised.

        if door.is_locked:
            raise InternalError(
                f"exiting {self.cursor.internal_name} via the "
                + "{exit_name.replace('_',' ')}: door is locked"
            )

        # The Door object returns the other Room object it connects to;
        # the value for cursor is updated by setting _room_cursor to
        # that Room object's internal_name.

        other_room_internal_name = door.other_room_internal_name(
            self.cursor.internal_name
        )
        new_room_dest = self._rooms_objs[other_room_internal_name]
        self._room_cursor = new_room_dest.internal_name
