"""
Auxiliary functions for ORM.

Created on Mar 15, 2016

@author: James Williams
"""

from copy import deepcopy
from functools import reduce  # Python 3


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


def getitem_nested(d, keys):
    """Gets a value in a nested dictionary given a list of keys to expand.
    """

    if len(keys) > 1:
        key = keys.pop(0)
        value = getitem_nested(d[key], keys)
    else:
        value = d[keys.pop(0)]

    return value


def setitem_nested(d, keys, value):
    """Sets a value in a nested dictionary given a list of keys to expand.
    """

    if len(keys) > 1:
        key = keys.pop(0)
        if key in d and isinstance(d[key], dict):
            setitem_nested(d[key], keys, value)
        else:
            d[key] = {}
            setitem_nested(d[key], keys, value)
    else:
        key = keys.pop(0)
        if isinstance(d, dict):
            d[key] = value
        else:
            d[key] = {key: value}


def subset(d, keys, keep=1):
    """Subset a dictionary based on a list of keys
    """

    if keep < 1:
        return {key: value for key, value in d.items() if key not in keys}
    else:
        return {key: value for key, value in d.items() if key in keys}


def deep_diff(a, b, ignore=[]):
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

        deleted = a_keys - b_keys
        if deleted:
            for key in deleted:
                if key not in ignore:
                    setitem_nested(summary, ['deleted'] + keys + [key], a[key])

        matched = a_keys & b_keys
        if matched:
            for key in matched:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    diff(a[key], b[key], keys + [key])
                else:
                    if a[key] != b[key]:
                        setitem_nested(
                            summary, ['updated'] + keys + [key],
                            {
                                'old': a[key],
                                'new': b[key],
                            })

        created = b_keys - a_keys
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


def get_update(old, new, ignore=['_id']):
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

        deleted = old_keys - new_keys
        if deleted:
            for key in deleted:
                if key not in ignore:
                    root_key = root + '.' + key if root else key
                    unset[root_key] = ''

        matched = old_keys & new_keys
        if matched:
            for key in matched:
                root_key = root + '.' + key if root else key
                if isinstance(old[key], dict) and isinstance(new[key], dict):
                    diff(old[key], new[key], root_key)
                else:
                    if old[key] != new[key]:
                        upset[root_key] = new[key]

        created = new_keys - old_keys
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
