"""
Defines a root logger which can be imported by scripts using this package, and
configurations for color stderr formatting. Currently, modules request loggers
locally, but they could import the root logger directly.
"""

import logging
import sys

import colorama
from colorama import Fore as FG, Back as BG, Style as ST

# from log4mongo.handlers import MongoHandler, MongoFormatter

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Initialize colorama to obtain accurate platform specific escape characters
colorama.init()

#: Default colors for :class:`ColoredFormatter` (using :mod:`colorama`)
COLORS = {
    'WARNING': FG.YELLOW,
    'INFO': FG.WHITE,
    'DEBUG': FG.BLUE,
    'CRITICAL': FG.CYAN,
    'ERROR': FG.RED
}


# -----------------------------------------------------------------------------
# ColoredFormatter
# -----------------------------------------------------------------------------

class ColoredFormatter(logging.Formatter):
    """Color formatter for logging.
    """

    def __init__(self, *args, **kwargs):
        """Initializes a new :class:`ColoredFormatter` with colors specified.

        Args:
            colors (dict): dictionary mapping logging level to color
                (default: :data:`COLORS`)
        """

        # Allows non keyword arguments to be passed
        colors = kwargs.pop('colors', COLORS)

        super().__init__(*args, **kwargs)

        self.colors = colors

    def format(self, record):
        """Format record according to level name (standard).
        """

        name = record.levelname
        if name in colors:
            record.levelname = colors[name] + name
        return logging.Formatter.format(self, record)


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

# Configure formatters
stderr_formatter = ColoredFormatter(
    fmt=FG.LIGHTBLACK_EX + '%(asctime)s' + FG.LIGHTBLUE_EX +
    ' - %(module)s.%(name)s.%(funcName)s:%(lineno)d' +
    ' - %(levelname)s: ' + ST.RESET_ALL + '%(message)s',
    datefmt='%m-%d-%Y %H:%M:%S')
file_formatter = logging.Formatter(
    fmt='%(asctime)s' +
    ' - %(module)s.%(funcName)s:%(lineno)d' +
    ' - %(levelname)s: %(message)s',
    datefmt='%m-%d-%Y %H:%M:%S')

# Module logger that can be reconfigured and used globally
logger = logging.getLogger()

# Configure root logger to be used or inherited
logger.setLevel(logging.DEBUG)
