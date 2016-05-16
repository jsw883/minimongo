"""
Auxiliary functions for ORM.

Created on Mar 15, 2016

@author: James Williams
"""

from copy import deepcopy
from functools import reduce  # Python 3

from operator import xor


# -----------------------------------------------------------------------------
# Dictionaries
# -----------------------------------------------------------------------------

def merge(*args):
    """Merges an arbitrary number of dictionaries sequentially.

    Note that order matters as the dictionaries are merged by updating a new
    dictionary iteratively, and if the dictionary keys are not unique across
    args, then the last dictionary key value pair will be used.
    """

    # Sequentially merge dictionaries into a new dictionary
    d = {}
    for arg in args:
        d.update(arg)
    return d


def subset(d, keys, keep=1):
    """Subset a dictionary based on a list of keys.
    """

    if keep == 0:
        return {key: value for key, value in d.items() if key not in keys}
    else:
        return {key: value for key, value in d.items() if key in keys}


def hasitem_nested(d, keys):
    """Checks a nested dictionary given a list of keys to expand.
    """

    if len(keys) > 1:
        if keys[0] in d:
            return hasitem_nested(d[keys[0]], keys[1:])
        else:
            return False
    else:
        return keys[0] in d


def getitem_nested(d, keys):
    """Gets a value in a nested dictionary given a list of keys to expand.
    """

    return reduce(dict.__getitem__, keys, d)


def setitem_nested(d, keys, value):
    """Sets a value in a nested dictionary given a list of keys to expand.
    """

    if len(keys) > 1:
        key = keys[0]
        if key in d and isinstance(d[key], dict):
            setitem_nested(d[key], keys[1:], value)
        else:
            d[key] = {}
            setitem_nested(d[key], keys[1:], value)
    else:
        key = keys[0]
        if isinstance(d, dict):
            d[key] = value
        else:
            d[key] = {key: value}

    # reduce(dict.__getitem__, keys[:-1], d).__setitem__(keys[-1], value)


def delitem_nested(d, keys):
    """Deletes a value in a nested dictionary given a list of keys to expand.
    """

    reduce(dict.__getitem__, keys[:-1], d).__delitem__(keys[-1])


def get_dict_from_array(array, conditions):
    """Finds a dictionary in an array based on unqiue pairs of {key: value}.

    The conditions argument is formatted:

        {
            key: value,
            ...
        }
    """

    # if isinstance(key, str):
    #     d = [d for d in array if key in d and d[key] == value]
    # else:
    #     d = [d for d in array
    #          if hasitem_nested(d, key) and getitem_nested(d, key) == value]

    d = []
    for item in array:
        flags = []
        for key, value in conditions.items():
            key = key.split('.')
            if len(key) == 1:
                flag = key[0] in item and item[key[0]] == value
            else:

                flag = (hasitem_nested(item, key) and
                        getitem_nested(item, key) == value)
            flags.append(flag)
        if all(flags):
            d.append(item)

    if d:
        if len(d) == 1:
            return d[0]
        else:
            raise ValueError(
                "Multiple dicts found for key = {}, value = {}".format(
                    keys, value))
    else:
        raise ValueError(
            "Dict not found for key = {}, value = {}".format(key, value))


def dict_from_dict_array(array, pivot_key):
    """Converts an array of dictionaries to a dictionary based on a pivot key.
    """

    return {item[pivot_key]: item for item in array}


def deep_diff(a, b, grab=[], options={'deleted', 'updated', 'created'},
              keep=0):
    """Computes a minimal MongoDB update recursively.

        a = {'a': 0, 'b': 1, 'c': {'d': 2, 'e': 3, 'x': 4}, 'x': '0'}
        b = {'a': 1, 'b': 1, 'c': {'d': 1, 'e': 3, 'y': 4}, 'y': '1'}

        diff = deep_diff(a, b)

    """

    summary = {}

    # Recursive method to obtain minimal update for each nested dictionary
    def diff(a, b, keys):

        a_keys = set(a.keys())
        b_keys = set(b.keys())

        deleted = a_keys - b_keys if 'deleted' in options else set()
        if deleted:
            for key in deleted:
                if xor(keep, key not in grab):
                    setitem_nested(summary, ['deleted'] + keys + [key], a[key])

        matched = a_keys & b_keys
        if matched:
            for key in matched:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    diff(a[key], b[key], keys + [key])
                else:
                    if ('updated' in options and xor(keep, key not in grab) and
                            a[key] != b[key]):
                        setitem_nested(
                            summary, ['updated'] + keys + [key],
                            {
                                'old': a[key],
                                'new': b[key],
                            })

        created = b_keys - a_keys if 'created' in options else set()
        if created:
            for key in created:
                setitem_nested(summary, ['created'] + keys + [key], b[key])

    diff(a, b, [])

    return summary


# -----------------------------------------------------------------------------
# Other
# -----------------------------------------------------------------------------

def isiterable(iterable, ignorestr=True):
    """Check if an object is iterable, somewhat naively, but sufficiently.
    """

    flag = hasattr(iterable, '__getitem__') or hasattr(iterable, '__iter__')
    if ignorestr:
        flag = flag and not hasattr(iterable, 'split')

    return flag


# -----------------------------------------------------------------------------
# MongoDB
# -----------------------------------------------------------------------------

def get_uri(config):
    """Extracts a complete URI from a config dictionary..
    """

    # Check if complete URI is already specified
    if 'host_uri' in config:
        host_uri = config['host_uri']
    else:
        host = config['host']
        port = config['port']
        host_uri = 'mongodb://'
        if config['username'] and config['password']:
            host_uri += config['username'] + ':' + config['password'] + '@'
        host_uri += host + ':' + str(port)

    return host_uri


def get_update(
        old, new, grab=['_id'], options={'deleted', 'updated', 'created'},
        keep=0):
    """Computes a minimal MongoDB update recursively.

    Note that only the '$set' and '$unset' update operators are considered.

        old = {'a': 0, 'b': 1, 'c': {'d': 2, 'e': 3, 'x': 4}, 'x': '0'}
        new = {'a': 1, 'b': 1, 'c': {'d': 1, 'e': 3, 'y': 4}, 'y': '1'}

        update = get_update(old, new)

    """

    upset = {}
    unset = {}

    # Recursive method to obtain minimal update for each nested dictionary
    def diff(old, new, root):

        old_keys = set(old.keys())
        new_keys = set(new.keys())

        deleted = old_keys - new_keys if 'deleted' in options else set()
        if deleted:
            for key in deleted:
                if xor(keep, key not in grab):
                    root_key = root + '.' + key if root else key
                    unset[root_key] = ''

        matched = old_keys & new_keys
        if matched:
            for key in matched:
                root_key = root + '.' + key if root else key
                if isinstance(old[key], dict) and isinstance(new[key], dict):
                    diff(old[key], new[key], root_key)
                else:
                    if ('updated' in options and xor(keep, key not in grab) and
                            old[key] != new[key]):
                        upset[root_key] = new[key]

        created = new_keys - old_keys if 'created' in options else set()
        if created:
            for key in created:
                root_key = root + '.' + key if root else key
                upset[root_key] = new[key]

    diff(old, new, '')

    # Check which update operators are needed
    update = {}
    if upset:
        update['$set'] = upset  # Create or update key
    if unset:
        update['$unset'] = unset  # Delete key

    return update


# -----------------------------------------------------------------------------
# Printing
# -----------------------------------------------------------------------------

class Pretty(object):
    """Pretty printer with custom formatting.
    """

    def __init__(self, htchar="  ", lfchar="\n", indent=0):
        self.htchar = htchar
        self.lfchar = lfchar
        self.indent = indent
        self.types = {
            object: self.__class__.object_formatter,
            dict: self.__class__.dict_formatter,
            list: self.__class__.list_formatter,
            tuple: self.__class__.tuple_formatter,
        }

    def add_formatter(self, obj, formatter):
        self.types[obj] = formatter

    def get_formatter(self, obj):
        for type_ in self.types:
            if isinstance(obj, type_):
                return self.types[type_]
        return self.types[object]

    def __call__(self, value, **args):
        for key in args:
            setattr(self, key, args[key])
        return self.get_formatter(value)(self, value, self.indent)

    def object_formatter(self, value, indent):
        return repr(value)

    def dict_formatter(self, value, indent):
        items = []
        for key in sorted(value.keys()):
            s = (self.lfchar + self.htchar * (indent + 1) + repr(key) + ': ' +
                 self.get_formatter(value[key])(self, value[key], indent + 1))
            items.append(s)

        return '{%s}' % (','.join(items) + self.lfchar + self.htchar * indent)

    def list_formatter(self, value, indent):
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(item)(self, item, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + self.lfchar + self.htchar * indent)

    def tuple_formatter(self, value, indent):
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(value)(
                self, item, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + self.lfchar + self.htchar * indent)


def sphinx_pretty(obj, name='obj'):
    """Pretty dict embedding for Spinx (HTML).
    """

    pretty = Pretty(indent=2)
    print('.. code-block:: Javascript\n\n    {} = {}\n\n'.format(
        name, pretty(obj)))
