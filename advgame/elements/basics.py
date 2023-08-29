#!/usr/bin/python3

import re

from abc import ABC


__all__ = "IniEntry", "State"


class IniEntry:
    """
    Parent class for classes like Room, Item, and Door that are instantiated
    from .ini file entries.
    """

    # This regular expression is used to parse the contents= attributes
    # used by rooms.ini and containers.ini to encode initializing data
    # for an ItemsMultiState object into a single line of text. Used
    # in IniEntry._process_list_value().

    inventory_list_value_re = re.compile(
        r"""^\[(
                                                    (
                                                        [1-9][0-9]*
                                                        x
                                                        [A-Z][A-Za-z_]+
                                                    )(,
                                                        [1-9][0-9]*
                                                        x
                                                        [A-Z][A-Za-z_]+
                                                    )*
                                                )\]$""",
        re.X,
    )

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
                elif value.replace(".", "").isdigit():
                    value = float(value)
            setattr(self, key, value)

    def __eq__(self, other):
        """
        Test two IniEntry objects or objects that subclass IniEntry for equality.
        """
        if not isinstance(other, type(self)):
            return False
        else:
            return all(
                getattr(self, attr, None) == getattr(other, attr, None)
                for attr in self.__slots__
            )

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
        qty_strval_pairs = [
            (int(item_qty), item_name)
            for item_qty, item_name in (
                name_x_qty_str.split("x", maxsplit=1)
                for name_x_qty_str in capture_split
            )
        ]
        return qty_strval_pairs


class State(ABC):
    """
    A generic key-value container object that maintains an internal
    dictionary and provides access to it by method.
    """

    __slots__ = ("_contents",)

    __abstractmethods__ = frozenset(("__init__",))

    def contains(self, item_internal_name):
        """
        Test whether an item object with the specified internal name is present
        in the private dictionary.

        :item_internal_name: The internal name of the Item subclass object.
        :return: True or False.
        """
        return any(
            item_internal_name == contained_item.internal_name
            for contained_item in self._contents.values()
        )

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
