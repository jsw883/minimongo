Repository
==========

.. automodule:: minimongo.repository

Constants
---------

.. data:: DEFAULT_CONFIG
   
   Default config for MongoDB. The ``'indexes'`` field is a list of :class:`pymongo.operations.IndexModel`.

   .. exec::
       from minimongo.auxiliary import sphinx_pretty
       from minimongo.repository import DEFAULT_CONFIG
       sphinx_pretty(DEFAULT_CONFIG, 'DEFAULT_CONFIG')

AttrDictionary
--------------

.. autoclass:: AttrDictionary
   :show-inheritance:
   :members:
   :private-members:
   :special-members:

Models
------

.. autoclass:: MetaModel
   :show-inheritance:
   :members:
   :private-members:
   :special-members:

.. autoclass:: Model
   :show-inheritance:
   :members:
   :private-members:
   :special-members:
