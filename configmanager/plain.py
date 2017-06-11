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

        self.settings.key_setter = self.__key_setter
        self.settings.key_getter = self.__key_getter

    def __key_setter(self, subject=None, value=None, default_key_setter=None, **kwargs):
        if subject.is_item:
            subject.value = value
        else:
            default_key_setter()

    def __key_getter(self, parent=None, subject=None, **kwargs):
        if subject.is_item:
            return subject.value
        else:
            return subject
