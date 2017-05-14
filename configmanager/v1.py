#
# v1
#
# Lw* classes are not part of the public interface.
# Instead, it is the Item and Config classes;
# And they should be imported from here.
#

from .lightweight import LwConfig as _LwConfig
from .lightweight import LwItem as _LwItem
from .exceptions import _ConfigValueMissing as ConfigValueMissing


class Item(_LwItem):
    pass


class Config(_LwConfig):
    cm__item_cls = Item
