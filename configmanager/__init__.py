__version__ = '1.0.0'


# The old ones
from .managers import ConfigManager
from .items import ConfigItem
from .exceptions import _UnknownConfigItem, _ConfigValueMissing, _UnsupportedOperation
from .base import ItemAttribute

from .v1 import *
