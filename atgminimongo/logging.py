"""
Defines a root logger which can be imported by scripts using this package, and
configurations for color stderr formatting. Currently, modules request loggers
locally, but they could import the root logger directly.

Created on Mar 11, 2016

@author: James Williams
"""

import logging
import sys

import colorama
from colorama import Fore as FG, Back as BG, Style as ST

from log4mongo.handlers import MongoHandler, MongoFormatter

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Initialize colorama to obtain accurate platform specific escape characters
colorama.init()


# -----------------------------------------------------------------------------
# ColoredFormatter
# -----------------------------------------------------------------------------

class ColoredFormatter(logging.Formatter):
    """Logger color formatter for changing color according to level name.
    """

    def format(self, record):  # @ReservedAssignment
        """Format record according to level name (standard).
        """
        colors = {
            'WARNING': FG.YELLOW,
            'INFO': FG.WHITE,
            'DEBUG': FG.BLUE,
            'CRITICAL': FG.CYAN,
            'ERROR': FG.RED}

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

# Configure root logger to be used or inherited
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
