"""
Tests classes and methods for interfacing with MongoDB.

Prior to testing, add the following user to MongoDB:

    db.createUser({
        'user': 'minimongoTester',
        'pwd': 'minimongoTester',
        'roles':[
            {'role': 'readWrite', 'db': 'minimongo_testing'}
        ]
    })

Created on Mar 21, 2015

@author: Williams, James S.
"""

import pytest

from minimongo.repository import MetaModel, AttrDictionary, Model, \
    UpdateError


# ----------------------------------------------------------------------------
# AttrDictionary
# ----------------------------------------------------------------------------

class TestAttrDictionary(object):

    def setup(self):
        self.dictionary = AttrDictionary({
            'a': 0,
            'b': 'string',
            'c': {
                'x': 1,
            },
            'd': [{
                'x': 1,
            }]
        })

    def test_init(self):
        # Test class inheritance and recusive __init__ and __setitem__ method
        assert isinstance(self.dictionary.c, dict)
        assert isinstance(self.dictionary.c, AttrDictionary)
        # Test getkey
        assert self.dictionary['a'] == 0
        # Test setkey
        self.dictionary['e'] = 1
        assert self.dictionary['e'] == 1

    def test_attr(self):
        # Test getattr
        assert self.dictionary.a == 0
        assert self.dictionary.b == 'string'
        # Test setattr
        self.dictionary.e = 1
        assert self.dictionary.e == 1

    def test_attr_nested(self):
        # Test getattr
        assert self.dictionary.c.x == 1
        assert self.dictionary.d[0].x == 1
        # Test setattr
        self.dictionary.c.y = 3
        assert self.dictionary.c.y == 3
        # Test setattr recursively
        self.dictionary.e = {'x': {'i': 1}, 'y': [{'i': 1}]}
        assert self.dictionary.e.x.i == 1
        assert self.dictionary.e.y[0].i == 1


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------

class TestModel(object):

    class Dummy(Model):
        # Set config attr to configure binding by metaclass constructor
        config = {
            'host': '127.0.0.1',
            'port': 27017,
            'username': 'minimongoTester',
            'password': 'minimongoTester',
            'database': 'minimongo_testing',
            'collection': 'dummies',
            'indices': (),
            'auto_index': True,
        }

    def setup(self):
        self.Dummy.connection.drop_database(self.Dummy.database)
        self.dummy = self.Dummy({
            'a': 0,
            'b': 1,
            'c': {
                'd': 2,
                'e': 3,
            },
            'f': [
                0
            ]
        })

    def teardown(self):
        self.Dummy.connection.drop_database(self.Dummy.database)

    def test_init(self):
        # Test connection config
        assert self.Dummy.connection.address == ('127.0.0.1', 27017)
        assert self.Dummy.database.name == 'minimongo_testing'
        assert self.Dummy.collection.name == 'dummies'
        assert self.Dummy.connection.server_info()['ok'] == 1
        # Test class
        assert self.dummy.__class__ == self.Dummy
        # Test getattr
        assert self.dummy.b == 1
        assert self.dummy.c.e == 3

    def test_insert_many(self):
        # Insert many
        dummies = self.Dummy.insert_many([{'a': 0}, {'a': 1}])
        # Find
        dummy = self.Dummy.find({'a': 0})
        assert dummy.__class__ == self.Dummy
        assert dummy == dummies[0]
        dummy.delete()
        dummy = self.Dummy.find({'a': 1})
        assert dummy.__class__ == self.Dummy
        assert dummy == dummies[1]
        dummy.delete()
        assert not list(self.Dummy.find_many())

    def test_insert(self):
        # Insert one
        dummy = self.Dummy.insert({'a': 0})
        # Find
        res = self.Dummy.find({'a': 0})
        assert res.__class__ == self.Dummy
        assert res == dummy
        res.delete()
        assert not self.Dummy.find({'a': 0})

    def test_save_and_find(self):
        # Save
        res = self.dummy.save()
        assert res.acknowledged
        # Find
        dummy = self.Dummy.find({'a': 0})
        assert dummy.__class__ == self.Dummy
        assert dummy == self.dummy
        # Modify, save, and find
        self.dummy.b = 4
        self.dummy.c.e = 5
        assert self.Dummy.find({'a': 0}) != self.dummy
        res = self.dummy.save()
        assert res.acknowledged
        assert self.Dummy.find({'a': 0}) == self.dummy

    def test_update(self):
        # Save
        res = self.dummy.save()
        assert res.acknowledged
        # Update (set)
        self.dummy.update({'$set': {'b': 4, 'c.e': 5}})
        assert self.dummy.b == 4
        assert self.dummy.c.e == 5
        assert self.Dummy.find({'a': 0}) == self.dummy
        # Update (unset)
        self.dummy.update({'$unset': {'b': '', 'c.e': ''}})
        assert 'b' not in self.dummy
        assert 'e' not in self.dummy.c
        assert self.Dummy.find({'a': 0}) == self.dummy
        # Update (push)
        self.dummy.update({'$push': {'f': 1}})
        assert self.dummy.f[1] == 1
        assert self.Dummy.find({'a': 0}) == self.dummy
        # Error
        with pytest.raises(UpdateError):
            self.dummy.update({'$set': {'b': 6}, 'f': 7})

    def test_delete(self):
        # Save
        res = self.dummy.save()
        # Delete
        res = self.dummy.delete()
        assert res.acknowledged
        assert not self.Dummy.find({'a': 0})

    def test_find_many(self):
        # Insert many
        dummies = self.Dummy.insert_many([{'a': 0}, {'a': 1}])
        # Find many
        dummies = list(self.Dummy.find_many())
        assert dummies[0] == self.Dummy.find({'a': 0})
        assert dummies[1] == self.Dummy.find({'a': 1})
