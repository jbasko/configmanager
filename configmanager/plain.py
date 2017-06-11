from .managers import Config


class PlainConfig(Config):
    """
    If in your application code you don't need the rich features that configuration
    :class:`.Item` provides as an object, you can use :class:`.PlainConfig` which
    exposes calculated item values instead of items themselves.

    All other features of Config objects are supported. You can still access
    the underlying items through iterators.

    Examples:

        >>> config = PlainConfig({'greeting': 'Hello', 'db': {'user': 'root'}})
        >>> config.greeting
        'Hello'
        >>> config.db.user
        'root'
        >>> config.db.user = 'admin'
        >>> config.db.user
        'admin'
        >>> config.dump_values()
        {'greeting': 'Hello', {'db': {'user': 'admin'}}}

    """

    def __init__(self, *args, **kwargs):
        super(PlainConfig, self).__init__(*args, **kwargs)

        self._settings.item_setter = self.__item_setter
        self._settings.item_getter = self.__item_getter

    def __item_setter(self, item=None, value=None, **kwargs):
        item.value = value

    def __item_getter(self, section=None, item=None, **kwargs):
        return item.value
