class ConfigError(Exception):
    """
    Base class for all exceptions raised by *configmanager* that user may be able to recover from.
    """
    pass


class NotFound(ConfigError):
    """
    Section or item with the requested name or path is not found
    in the section it is being requested from.

    .. attribute:: name

        Name of the section or item which was not found

    .. attribute:: section

        :class:`.Config` instance which does not contain the sought name
    """

    def __init__(self, name, section=None):
        super(NotFound, self).__init__(name)
        self.name = name
        self.section = section

    def __repr__(self):
        return '<{} {!r} in {}>'.format(self.__class__.__name__, self.name, self.section.alias if self.section else None)


class RequiredValueMissing(ConfigError):
    """
    Value was requested from an item which requires a value, but had no
    default or custom value set.

    .. attribute:: name

        Name of the item

    .. attribute:: item

        :class:`.Item` instance
    """
    def __init__(self, name, item=None):
        super(RequiredValueMissing, self).__init__(name)
        self.name = name
        self.item = item

    def __repr__(self):
        return '<{} {!r} in {}>'.format(self.__class__.__name__, self.name, self.item)

