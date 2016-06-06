"""
Auxiliary functions for the package :mod:`minimongo`, including some generally
handy snippets of code for working with iterables, dictionaries, MongoDB, and
pretty printing. Many of these could eventually be moved to another package,
providing a single repository of generally handy snippets that can be imported
by every other repository.
"""

from datetime import datetime

from copy import deepcopy
from functools import reduce  # Python 3

from operator import xor


# -----------------------------------------------------------------------------
# Dictionaries
# -----------------------------------------------------------------------------

def merge(*args):
    """Merges an arbitrary number of dictionaries sequentially.

    Args:
        *args (dict): arbitrary number of dictionaries

    Returns:
        dict: merged dictionary

    Note that order matters as the dictionaries are merged by updating a new
    dictionary iteratively, and if the dictionary keys are not unique across
    args, then the last dictionary key value pair will be used.
    """

    d = {}
    for arg in args:
        d.update(arg)
    return d


def subset(d, keys, keep=1):
    """Subset a dictionary based on a list of keys.

    Args:
        keys (list): keys
        keep (int): binary flag to keep (1) or remove (0) the keys specified

    Returns:
        dict: subsetted dictionary
    """

    if keep == 0:
        return {key: value for key, value in d.items() if key not in keys}
    else:
        return {key: value for key, value in d.items() if key in keys}


def hasitem_nested(d, keys):
    """Checks a nested dictionary given a list of keys to expand.

    Args:
        keys (list): keys

    Returns:
        bool: if item exists
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

    Args:
        keys (list): ordered list of keys to expand

    Returns:
        object: value to get from key
    """

    return reduce(dict.__getitem__, keys, d)


def setitem_nested(d, keys, value):
    """Sets a value in a nested dictionary given a list of keys to expand.

    Args:
        keys (list): ordered list of keys to expand
        value (object): value to set at key
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


def delitem_nested(d, keys):
    """Deletes a value in a nested dictionary given a list of keys to expand.

    Args:
        keys (list): ordered list of keys to expand
    """

    reduce(dict.__getitem__, keys[:-1], d).__delitem__(keys[-1])


def deep_diff(old, new, options={'deleted', 'updated', 'created'}, grab=[],
              keep=0):
    """Computes old minimal MongoDB update recursively.

    Args:
        old (dict): old dictionary
        new (dict): new dictionary
        options (set): specifies the categories of difference to find
        grab (list): keys
        keep (int): binary flag to keep (1) or ignore (0) the keys specified

    Returns:
        dict: difference summary

    Example::

        old = {'old': 0, 'new': 1, 'c': {'d': 2, 'e': 3, 'x': 4}, 'x': '0'}
        new = {'old': 1, 'new': 1, 'c': {'d': 1, 'e': 3, 'y': 4}, 'y': '1'}

        diff = deep_diff(old, new)

    """

    summary = {}

    # Recursive method to obtain minimal update for each nested dictionary
    def diff(old, new, keys):

        a_keys = set(old.keys())
        b_keys = set(new.keys())

        deleted = a_keys - b_keys if 'deleted' in options else set()
        if deleted:
            for key in deleted:
                if xor(keep, key not in grab):
                    setitem_nested(
                        summary, ['deleted'] + keys + [key], old[key])

        matched = a_keys & b_keys
        if matched:
            for key in matched:
                if isinstance(old[key], dict) and isinstance(new[key], dict):
                    diff(old[key], new[key], keys + [key])
                else:
                    if ('updated' in options and xor(keep, key not in grab) and
                            old[key] != new[key]):
                        setitem_nested(
                            summary, ['updated'] + keys + [key],
                            {
                                'old': old[key],
                                'new': new[key],
                            })

        created = b_keys - a_keys if 'created' in options else set()
        if created:
            for key in created:
                setitem_nested(summary, ['created'] + keys + [key], new[key])

    diff(old, new, [])

    return summary


# -----------------------------------------------------------------------------
# Other
# -----------------------------------------------------------------------------

def isiterable(iterable, ignorestr=True):
    """Check if an object is iterable, somewhat naively, but sufficiently.

    Args:
        iterable (object): object to check
        ignorestr (bool): boolean flag to ignore strings

    Returns:
        bool: is iterable
    """

    flag = hasattr(iterable, '__getitem__') or hasattr(iterable, '__iter__')
    if ignorestr:
        flag = flag and not hasattr(iterable, 'split')

    return flag


# -----------------------------------------------------------------------------
# MongoDB
# -----------------------------------------------------------------------------

def get_uri(config):
    """Extracts a complete URI from a config dictionary.

    Args:
        config (dict): config dictionary specying URI

    Returns:
        str: complete URI
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
        old, new, options={'deleted', 'updated', 'created'}, grab=['_id'],
        keep=0):
    """Computes a minimal MongoDB update recursively.

    Args:
        old (dict): old dictionary
        new (dict): new dictionary
        options (set): specifies the categories of difference to find
        grab (list): keys
        keep (int): binary flag to keep (1) or ignore (0) the keys specified

    Returns:
        dict: update summary

    Example::

        old = {'a': 0, 'b': 1, 'c': {'d': 2, 'e': 3, 'x': 4}, 'x': '0'}
        new = {'a': 1, 'b': 1, 'c': {'d': 1, 'e': 3, 'y': 4}, 'y': '1'}

        update = get_update(old, new)

    Note that only the '$set' and '$unset' update operators are considered.
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

    Pretty is a pretty printing class that allows output to be cusomtized
    for each object type, custom horizonal tab and line feed strings, and
    indenting. Custom formatters are already specified for :class:`dict`,
    :class:`list`, and :class:`tuple` objects, giving a generic line feed
    scaffold, and a default formatter for :class:`object` is included.
    """

    def __init__(self, htchar='  ', lfchar='\n', indent=0):
        """Return an instance of Pretty.

        Args:
            htchar (str): horizontal tab string
            lfchar (str): line feed string
            indent (int): number of htchar to prepend to output (entirety)
        """
        self.htchar = htchar
        self.lfchar = lfchar
        self.indent = indent
        self.types = {
            object: self.__class__.object_formatter,
            dict: self.__class__.dict_formatter,
            list: self.__class__.list_formatter,
            tuple: self.__class__.tuple_formatter,
        }

    def __call__(self, value, **kwargs):
        """Allows class instance to be invoked as a function for formatting.

        Args:
            value (object): object to be formatted
            **kwargs: named arguments to be assigned as attributes

        Returns:
            str: pretty formatted string ready to be printed
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self.get_formatter(value)(self, value, self.indent)

    def add_formatter(self, obj, formatter):
        """Adds a custom formatter for an arbitrary object type.

        Args:
            obj (type): object type
            formatter (function): custom formatter function with signature
                formatter(value, indent)
        """
        self.types[obj] = formatter

    def get_formatter(self, obj):
        """Retrieves the custom formatter for the object type (or default).
        """
        for type_ in self.types:
            if isinstance(obj, type_):
                return self.types[type_]
        return self.types[object]

    def object_formatter(self, value, indent):
        """Default object formatter.
        """
        return repr(value)

    def dict_formatter(self, value, indent):
        """Dictionary formatter.
        """
        items = []
        for key in sorted(value.keys()):
            s = (self.lfchar + self.htchar * (indent + 1) + repr(key) + ': ' +
                 self.get_formatter(value[key])(self, value[key], indent + 1))
            items.append(s)

        return '{%s}' % (','.join(items) + self.lfchar + self.htchar * indent)

    def list_formatter(self, value, indent):
        """List formatter.
        """
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(item)(self, item, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + self.lfchar + self.htchar * indent)

    def tuple_formatter(self, value, indent):
        """Tuple formatter.
        """
        items = [
            self.lfchar + self.htchar * (indent + 1) +
            self.get_formatter(value)(
                self, item, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + self.lfchar + self.htchar * indent)


def sphinx_pretty(obj, name='obj'):
    """Pretty dict to RST.

    Args:
        obj (object): object to be formatted
        name (str): object name to prepend

    Return:
        str: RST code block, indented and formatted
    """

    pretty = Pretty(indent=2)
    print('.. code-block:: Javascript\n\n    {} = {}\n\n'.format(
        name, pretty(obj)))
