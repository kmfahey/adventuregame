#!/usr/bin/python3

from advgame.elements.basics import IniEntry, State
from advgame.elements.characters import Character, ItemsState, ItemsMultiState
from advgame.errors import InternalError


__all__ = (
    "Container",
    "ContainersState",
    "Chest",
    "Corpse",
    "Creature",
    "CreaturesState",
)


class Container(IniEntry, ItemsMultiState):
    """
    This class uses multiple inheritance to inherit from both IniEntry and
    ItemsMultiState: it is an object that's instantiated from an entry in
    items.ini, but also can contain Item subclass objects.
    """

    __slots__ = (
        "internal_name",
        "title",
        "description",
        "is_locked",
        "is_closed",
        "container_type",
    )

    def __init__(self, items_state, internal_name, **ini_constr_argd):
        r"""
        This __init__ method calls both parent class's __init__ methods in
        sequence. It draws on the contents attribute of the source ini data,
        which is in the \[\d+x[A-Z][A-Za-z_]+(,\d+x[A-Z][A-Za-z_]+)*\] format,
        and unpacks it. An items_state object is a required argument so that
        it can be used to look up Item subclass objects' internal names and
        populate the container.

        :items_state: An Item_State object.
        :internal_name: The internal name of the container.
        :*item_objs: A tuple of the Item objects contained by the container.
        :**ini_constr_argd: The key-value pairs from containers.ini to
        instantiate the Container object with.
        """
        contents_str = ini_constr_argd.pop("contents", None)
        IniEntry.__init__(self, internal_name=internal_name, **ini_constr_argd)

        # If this Container has a contents attribute, it
        # is a compacted list of Item internal names and
        # quantities. _process_list_value unpacks it and returns
        # quantity-internal_name pairs.
        contents_qtys_item_objs = []

        if contents_str:
            contents_qtys_names = self._process_list_value(contents_str)

            # This list comprehension retrieves the Item subclass
            # objects from items_state.

            contents_qtys_item_objs = [
                (item_qty, items_state.get(item_internal_name))
                for item_qty, item_internal_name in contents_qtys_names
            ]
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

        :items_state: An ItemsState object.
        :**container_dict: A dict of key-value pairs to instantiate the
        Container subclass with.
        """
        container = None

        if container_dict["container_type"] == "chest":
            container = Chest(items_state, **container_dict)
        elif container_dict["container_type"] == "corpse":
            container = Corpse(items_state, **container_dict)
        return container


class ContainersState(ItemsState):
    """
    This ItemsState subclass is instantiated from the sections attribute of
    an IniConfig object instantiated from containers.ini.
    """

    __slots__ = ("_contents",)

    def __init__(self, items_state, **dict_of_dicts):
        """
        This __init__ method accepts an items_state object and a
        **dict-of-dicts, which it iterates down to instantiate the Container
        subclass objects that the container is populated with.

        :items_state: An ItemsState object.
        :**dict_of_dicts: A structure of internal name keys corresponding to
        dict values which are key-value pairs to initialize an individual
        Container subclass object with.
        """
        self._contents = dict()
        for container_internal_name, container_dict in dict_of_dicts.items():
            container = Container.subclassing_factory(
                items_state, internal_name=container_internal_name, **container_dict
            )
            self._contents[container_internal_name] = container


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


class Creature(IniEntry, Character):
    """
    This class uses multiple inheritance to subclass both IniEntry and
    Character. It is instantiated from an .ini file entry, but draws on all
    the game rules entity logic in Character to have access to the same
    mechanics as a character.
    """

    __slots__ = (
        "internal_name",
        "character_name",
        "description",
        "character_class",
        "species",
        "description_dead",
        "title",
        "_strength",
        "_dexterity",
        "_constitution",
        "_intelligence",
        "_wisdom",
        "_charisma",
        "_items_state",
        "_base_hit_points",
        "_weapon_equipped",
        "_armor_equipped",
        "_shield_equipped",
    )

    def __init__(self, items_state, internal_name, **argd):
        """
        This __init__ method initializes the object using super() to call
        __init__ methods from both IniEntry and Character. It sets the ability
        scores, populates its inventory, and sets up its equipment from its ini
        file data.

        :items_state: An ItemsState object.
        :internal_name: A string, the internal name of the creature.
        :**argd: A dict, the key-value pairs to instantiate the Creature object
        from.
        """

        # _separate_argd_into_different_arg_sets() is a utility function
        # that separates all the .ini key-value pairs into args for
        # Character.__init__, args for IniEntry.__init__, attributes
        # that can be used to initialize an Equipment object, and
        # quantity/internal_name pairs that can be used to initialize an
        # Inventory object.

        (
            char_init_argd,
            ini_entry_init_argd,
            equip_argd,
            invent_qty_pairs,
        ) = self._seprt_argd_into_diff_arg_sets(items_state, internal_name, **argd)
        IniEntry.__init__(self, internal_name=internal_name, **ini_entry_init_argd)
        self._post_init_slots_set_none(self.__slots__)
        Character.__init__(self, **char_init_argd)

        # The IniEntry.__init__ and Character.__init__ steps are
        # complete. _init_invent_and_equip handles the other
        # initializations with invent_qty_pairs and equip_argd as
        # arguments.

        self._init_inventory_and_equipment(items_state, invent_qty_pairs, equip_argd)
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

        :items_state: An ItemsState object.
        :intrn_name: A string, the creature's internal name.
        :**argd: The key-value pairs to differentiate into different sets of
        arguments.
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
            "magic_key_stat": argd.pop("magic_key_stat", None),
        }

        # Equipment argd is next, *_equipped key-values are popped from
        # argd and added to equip_argd.

        equip_argd = dict()
        for ini_key in (
            "weapon_equipped",
            "armor_equipped",
            "shield_equipped",
            "wand_equipped",
        ):
            if ini_key not in argd:
                continue
            equip_argd[ini_key] = argd.pop(ini_key)

        # The item quantity/intrn_name pairs are unpacked from
        # 'inventory_items' using _process_list_value, which is
        # inherited from IniEntry and uses the standard item qty/name
        # compact notation.

        invent_qty_name_pairs = self._process_list_value(argd.pop("inventory_items"))

        # If any item internal names don't occur in items_state an
        # exception is raised.

        if any(
            not items_state.contains(invent_intrn_name)
            for _, invent_intrn_name in invent_qty_name_pairs
        ):
            missing_names = tuple(
                item_intrn_name
                for _, item_intrn_name in invent_qty_name_pairs
                if not items_state.contains(item_intrn_name)
            )
            raise InternalError(
                f"bad creatures.ini specification for creature {intrn_name}: "
                + "creature ini config dict `inventory_items` value indicated "
                + "item not present in `ItemsState` argument: "
                + (", ".join(missing_names))
            )

        # The remaining argd is for IniEntry.__init__. And the four
        # argds are returned.

        ini_entry_init_argd = argd
        return (char_init_argd, ini_entry_init_argd, equip_argd, invent_qty_name_pairs)

    def _init_inventory_and_equipment(
        self, items_state, invent_qty_name_pairs, equip_argd
    ):
        """
        This private method accepts an items state, inventory quantity-internal
        name pairs, and the equipment dict, and uses them to initialize the
        creature's inventory and equipped items.

        :items_state: An ItemsState object.
        :invent_qty_name_pairs: A tuple of 2-tuples of item quantity ints and
        internal name strings.
        :equip_argd: A dictionary of equipment assignments.
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
                raise InternalError(
                    "bad creatures.ini specification for creature "
                    + f"{self.internal_name}: items index object does not "
                    + f"contain an item named {item_internal_name}"
                )
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
        corpse = Corpse(
            self._items_state,
            internal_name,
            container_type="corpse",
            description=description,
            title=title,
        )

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

        :items_state: An ItemsState object.
        :**dict_of_dicts: A structure of internal name keys corresponding to
        dict values which are key-value pairs to initialize an individual
        Creature object with.
        """
        self._contents = dict()
        for creature_internal_name, creature_dict in dict_of_dicts.items():
            creature = Creature(
                items_state, internal_name=creature_internal_name, **creature_dict
            )
            self.set(creature.internal_name, creature)
