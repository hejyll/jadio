import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from ._version import __version__
from .platforms import *  # NOQA
from .program import Program  # NOQA
from .search import *  # NOQA
from .station import Station  # NOQA
