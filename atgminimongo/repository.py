"""
Classes and methods for interfacing with MongoDB.

Contains a lightweight ORM for interfacing efficiently and easily with MongoDB.
The binding is done using :mod:`pymongo` under the hood, and provides recursive
attribute style indexing using :class:'AttrDictionary'.
"""

from .auxiliary import *

import pymongo
import logging

from inflection import underscore

from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Default config for MongoDB
DEFAULT_CONFIG = {
    'host': '127.0.0.1',
    'port': 27017,
    'username': None,
    'password': None,
    'database': None,
    'collection': None,
    'indexes': []  # List of pymongo IndexModel
}


# -----------------------------------------------------------------------------
# MetaModel (meta)
# -----------------------------------------------------------------------------

class MetaModel(type):
    """Model metaclass for configuring and maintaining connection to Mongo DB.

    Note that the metaclass is used to actually configure the database mapping
    when a model class is defined (or immediately before it is instantiated),
    as the *class* itself represents an ORM. Connection pooling is now handled
    automatically by :mod:`pymongo`, which keeps things straightforward.
    """

    def __str__(cls):
        """String representation for class (containing metaclass binding).
        """
        # Check if class is a subclass of Model (with metaclass MetaModel)
        if not [b for b in cls.__bases__ if isinstance(b, MetaModel)]:
            return super().__repr__()
        else:
            return "<class '{}.{}({})'>".format(cls.__module__, cls.__name__,
                                                cls.__dict__)

    def __new__(cls, name, bases, namespace, **kwargs):
        """Constructor for a new model (configures database mapping)
        """

        _cls = super().__new__(cls, name, bases, namespace)

        # Check if class is a subclass of Model (with metaclass MetaModel)
        if not [b for b in bases if isinstance(b, MetaModel)]:
            return _cls

        # Configure logging
        _cls._logger = logging.getLogger(name)

        # Get model config
        try:
            config = merge(DEFAULT_CONFIG, getattr(_cls, 'config'))
        except AttributeError:
            config = DEFAULT_CONFIG
        setattr(_cls, 'config', config)
        # else:
        #     delattr(cls, 'config')  # delete attribute to avoid key conflicts

        # Default database and collection based on class name if none specified
        config['database'] = config['database'] or 'models'
        config['collection'] = config['collection'] or underscore(name)

        # Connect to MongoDB
        host_uri = get_uri(config)
        try:
            _cls.connection = pymongo.MongoClient(host=host_uri)
            _cls._logger.info('Connection to %s succeeded', host_uri)
        except Exception as e:
            _cls._logger.exception('Error establishing connection to %s: %s',
                                   host_uri, e, e)
            raise

        _cls.database = _cls.connection[config['database']]
        _cls.collection = _cls.database[config['collection']]

        if len(config['indexes']) > 0:
            # Should gracefully create indexes (providing no option conflicts)
            _cls.collection.create_indexes(config['indexes'])

        return _cls


# -----------------------------------------------------------------------------
# AttrDictionary
# -----------------------------------------------------------------------------

class AttrDictionary(dict):
    """:class:`dict` wrapper allowing `.` access to members of the dictionary.
    """

    # -------------------------------------------------------------------------
    # Core
    # -------------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        """Initializes and populates an :class:`AttrDictionary`.

        Args:
            *args (dict): dictionary objects to apply recursively
            **kwargs: keyword arguments to apply sequentially
        """

        super(AttrDictionary, self).__init__(*args, **kwargs)
        for arg in args:
            # TODO: raise exception if not isinstance(arg, dict)
            for k, v in arg.items():
                self.__setitem__(k, v)

        if kwargs:
            for k, v in kwargs.items():
                self.__setitem__(k, v)

    def __getattr__(self, key):
        """Allow get dictionary values by attribute key.
        """

        try:
            return super(AttrDictionary, self).__getitem__(key)
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, key, value):
        """Allow set dictionary values by attribute key.
        """

        try:
            self.__setitem__(key, value)
        except KeyError as e:
            raise AttributeError(e)

    def __delattr__(self, key):
        """Allow delete dictionary values by attribute key.
        """

        try:
            return super(AttrDictionary, self).__delitem__(key)
        except KeyError as e:
            raise AttributeError(e)

    def __setitem__(self, key, value):
        """Allow nested `.` access by recursive wrapping.
        """

        value = self._ensure_attr_dictionary(value)

        return super(AttrDictionary, self).__setitem__(key, value)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _ensure_attr_dictionary(cls, obj):
        """Ensure object has AttrDictionary functionality recursively.
        """

        if isinstance(obj, AttrDictionary):
            return obj
        elif isinstance(obj, dict):
            return AttrDictionary(obj)
        elif isiterable(obj):
            return [cls._ensure_attr_dictionary(child) for child in obj]

        return obj


# -----------------------------------------------------------------------------
# Model (ORM)
# -----------------------------------------------------------------------------

class Model(AttrDictionary, metaclass=MetaModel):
    """Based model class implementing straightforward ORM.

    :class:`Model` inherits from :class:`AttrDictionary` to allow `.` access
    to members of the dictionary, giving a straightforward ORM. The underlying
    :class:`pymongo.collection.Collection` can also be accessed directly,
    exposing the entirety of :mod:`pymongo` functionality if required.
    """

    # -------------------------------------------------------------------------
    # Core
    # -------------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        """Initialize using :class:`AttrDictionary` (does not update MongoDB).
        """
        super().__init__(*args, **kwargs)
        self._logger.debug('%s initialized.', self)

    def __str__(self):
        """String representation for object (class instance).
        """

        return '{}({})'.format(self.__class__.__name__,
                               super(Model, self).__str__())

    # -------------------------------------------------------------------------
    # Model functionality
    # -------------------------------------------------------------------------

    @classmethod
    def insert_many(self, objects):
        """Create and insert many objects into MongoDB.

        Objects can be a :class:`dict` or :class:`AttrDictionary`, and
        are returned as :class:`Model` instances, with the necessary bindings
        to MongoDB.
        """

        res = self.collection.insert_many(objects)
        objects = [self(obj) for obj in objects]
        for i, inserted_id in enumerate(res.inserted_ids):
            objects[i]._id = inserted_id
            self._logger.debug("%s inserted.", objects[i])

        self._logger.info("%s objects inserted.", len(objects))
        return objects

    @classmethod
    def insert(self, obj):
        """Create and insert one object into MongoDB.

        Objects can be a :class:`dict` or :class:`AttrDictionary`, and
        are returned as :class:`Model` instances, with the necessary bindings
        to MongoDB.
        """

        res = self.collection.insert_one(obj)
        obj = self(obj)
        obj._id = res.inserted_id

        self._logger.debug("%s inserted.", obj)
        self._logger.info("{{'_id': ObjectID('%s')}} inserted.", obj._id)
        return obj

    @classmethod
    def find_many(self, *args, **kwargs):
        """Load many from MongoDB.
        """

        objects = self.collection.find(*args, **kwargs)

        query = args[0] if len(args) != 0 else {}
        if objects is not None:
            self._logger.info("Query %s succeeded.", query)
            for obj in objects:
                yield self(obj)
            objects.close()  # Ensure cursor is closed
        else:
            self._logger.info("Query %s failed.", query)
            return None

    @classmethod
    def find(self, *args, **kwargs):
        """Find one from MongoDB.
        """

        obj = self.collection.find_one(*args, **kwargs)

        if obj is not None:
            self._logger.debug("%s returned.", obj)
            self._logger.info("Query %s succeeded, {{'_id': ObjectID('%s')}} "
                              "returned.", args[0], obj['_id'])
            return self(obj)
        else:
            self._logger.info("Query %s failed, object not found.", args[0])
            return None

    # -------------------------------------------------------------------------
    # Object functionality
    # -------------------------------------------------------------------------

    def save(self):
        """Save to MongoDB, automatically inserting or updating.
        """

        if hasattr(self, '_id'):
            update = get_update(self.find({'_id': self._id}), self)
            res = self.collection.update_one({'_id': self._id}, update)
        else:
            res = self.collection.insert_one(self)
            self._id = res.inserted_id

        self._logger.info("{{'_id': ObjectID('%s')}} saved.", self._id)
        return res

    def update(self, update):
        """Update the MongoDB copy to match local copy.

        Note that this requires the object to be already inserted, and the _id
        key to be specified.

        The update can be a dictionary of 'update operators' which are applied
        to the local and the MongoDB copy directly, or a dictionary containing
        a newer version of the object which is used to replace the local and
        the MongoDB copy with the minimal update required.
        """

        operators = {'$set', '$unset', '$push'}
        if not all(key in operators for key in update.keys()):
            raise UpdateError(
                update, 'Update only works with {} operators.'.format(
                    ' and '.join(operators)))

        if '$set' in update:
            for key in update['$set']:
                setitem_nested(self, key.split('.'), update['$set'][key])

        if '$unset' in update:
            for key in update['$unset']:
                delitem_nested(self, key.split('.'))

        if '$push' in update:
            for key in update['$push']:
                item = getitem_nested(self, key.split('.'))
                setitem_nested(
                    self, key.split('.'), item + [update['$push'][key]])

        res = self.collection.update_one({'_id': self._id}, update)
        self._logger.info("Update %s succeeded {{'_id': ObjectID('%s')}} "
                          "updated.", update, self._id)
        return res

    def delete(self):
        """Remove from MongoDB.

        Note that this requires the object to be already inserted, and the _id
        key to be specified. The local copy will continue to exist but the _id
        key will be removed.
        """

        res = self.collection.delete_one({'_id': self._id})
        self._logger.info(
            "Object {{'_id': ObjectID('%s')}} deleted.", self._id)
        self.__delattr__('_id')
        return res


# -----------------------------------------------------------------------------
# UpdateError
# -----------------------------------------------------------------------------

class UpdateError(Exception):
    """Exception raised for invalid update expressions (with update operators).
    """

    def __init__(self, update, message):
        """Initialize exception with update and message.
        """

        self.update = update
        self.message = message
