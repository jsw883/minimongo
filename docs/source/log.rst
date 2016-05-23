Logging
=======

.. automodule:: minimongo.log

Constants
---------

.. data:: COLORS
   
   

   .. exec::
       from minimongo.auxiliary import sphinx_pretty
       from minimongo.log import COLORS
       sphinx_pretty(COLORS, 'COLORS')

.. data:: stderr_formatter

   Preconfigured stderr formatter using :class:`ColoredFormatter`.

.. data:: file_formatter

   Preconfigured file formatter using :class:`logging.Formatter`.

.. data:: logger

   Module logger that can be reconfigured and used globally.

Classes
-------

.. autoclass:: ColoredFormatter
   :show-inheritance:
   :members:
   :private-members:
   :special-members: