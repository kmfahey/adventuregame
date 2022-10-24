#!/usr/bin/python3

import abc
import re


from .utility import *

__name__ = 'adventuregame.collections'


class ini_entry(object):

    inventory_list_value_re = re.compile(r'^\[(([1-9][0-9]*x[A-Z][A-Za-z_]+)(,[1-9][0-9]*x[A-Z][A-Za-z_]+)*)\]$')

    def __init__(self, **argd):
        for key, value in argd.items():
            if isinstance(value, str):
                if value.lower() == 'false':
                    value = False
                elif value.lower() == 'true':
                    value = True
                elif value.isdigit():
                    value = int(value)
                elif isfloat(value):
                    value = float(value)
            setattr(self, key, value)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in self.__slots__)

    def _post_init_slots_set_none(self, slots):
        for key in slots:
            if not hasattr(self, key):
                setattr(self, key, None)

    def _process_list_value(self, inventory_value):
        value_match = self.inventory_list_value_re.match(inventory_value)
        inner_capture = value_match.groups(1)[0]
        capture_split = inner_capture.split(',')
        qty_strval_pairs = tuple((int(item_qty), item_name) for item_qty, item_name in (
                                    name_x_qty_str.split('x', maxsplit=1) for name_x_qty_str in capture_split)
                                )
        return qty_strval_pairs


class state(abc.ABC):
    __slots__ = '_contents',

    __abstractmethods__ = frozenset(('__init__',))

    def contains(self, item_internal_name):  # check
        return any(item_internal_name == contained_item_obj.internal_name for contained_item_obj in self._contents.values())

    def get(self, item_internal_name):  # check
        return self._contents[item_internal_name]

    def set(self, item_internal_name, item_obj):  # check
        self._contents[item_internal_name] = item_obj

    def delete(self, item_internal_name):  # check
        del self._contents[item_internal_name]

    def keys(self):  # check
        return self._contents.keys()

    def values(self):  # check
        return self._contents.values()

    def items(self):  # check
        return self._contents.items()

    def size(self):  # check
        return len(self._contents)


class items_state(state):  # has been tested

    def __init__(self, **dict_of_dicts):
        self._contents = dict()
        for item_internal_name, item_dict in dict_of_dicts.items():
            item_obj = item.subclassing_factory(internal_name=item_internal_name, **item_dict)
            self._contents[item_internal_name] = item_obj
