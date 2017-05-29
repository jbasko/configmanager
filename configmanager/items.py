import copy

import six
from builtins import str

from .exceptions import ConfigValueMissing
from .base import ItemAttribute, BaseItem
from .utils import not_set, parse_bool_str


class Item(BaseItem):
    """
    Represents a config item -- something that has a name, a type, a default value,
    a user- or environment-specific (custom) value, and other attributes.
    """

    #: Name of the config item.
    name = ItemAttribute('name')

    #: Default value of the config item.
    default = ItemAttribute('default')

    #: Type of the config item's value, a callable. Defaults to string.
    type = ItemAttribute('type', default=str)

    raw_str_value = ItemAttribute('raw_str_value')

    #: ``True`` if config item requires a value.
    #: Note that if an item has a default value, marking it as ``required`` will have no effect.
    required = ItemAttribute('required', default=False)

    def __init__(self, name=not_set, **kwargs):
        """
        Creates a config item with its attributes. 
        """

        self._section = None

        if name is not not_set:
            if not isinstance(name, six.string_types):
                raise TypeError('Item name must be a string, got {!r}'.format(type(name)))
            self.name = name

        # Type must be set first because otherwise setting value below may fail.
        if 'type' in kwargs:
            self.type = kwargs.pop('type')
        else:
            #
            # Type guessing
            #
            value = kwargs.get('value', not_set)
            default = kwargs.get('default', not_set)

            # 'str' is from builtins package which means that
            # it is actually a unicode string in Python 2 too.
            type_ = None
            if value is not not_set and value is not None:
                type_ = type(value)
            elif default is not not_set and default is not None:
                type_ = type(default)

            if type_:
                if issubclass(type_, six.string_types):
                    self.type = str
                else:
                    self.type = type_

        self._value = not_set
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        if self._value is not not_set:
            value = self.value
        elif self.default is not not_set:
            value = self.default
        else:
            value = self.default

        return '<{} {} {!r}>'.format(self.__class__.__name__, self.name, value)

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    @property
    def str_value(self):
        if self.raw_str_value is not not_set:
            return self.raw_str_value
        if self._value is not not_set or self.default is not not_set:
            return str(self.value)
        else:
            return repr(self)

    @property
    def value(self):
        """
        The property through which to read and set value of config item.
        """
        return self.get()

    @value.setter
    def value(self, value):
        self.set(value)

    def get(self, fallback=not_set):
        """
        Returns config value.

        See Also:
            :meth:`.set` and :attr:`.value`
        """
        if self.has_value:
            if self._value is not not_set:
                return self._value
            else:
                return copy.deepcopy(self.default)
        elif fallback is not not_set:
            return fallback
        elif self.required:
            raise ConfigValueMissing(self.name)
        return fallback

    def set(self, value):
        """
        Sets config value.
        """
        self._value = self._parse_str_value(value)
        if not issubclass(self.type, six.string_types):
            if isinstance(value, six.string_types):
                self.raw_str_value = value
            else:
                self.raw_str_value = not_set

    def _parse_str_value(self, str_value):
        if str_value is None or str_value is not_set:
            return str_value
        elif self.type is bool:
            return parse_bool_str(str_value)
        else:
            return self.type(str_value)

    def reset(self):
        """
        Resets the value of config item to its default value.
        """
        self._value = not_set
        self.raw_str_value = not_set

    @property
    def is_default(self):
        """
        ``True`` if the item's value is its default value or if no value and no default value are set.
        """
        return self._value is not_set or self._value == self.default

    @property
    def has_value(self):
        """
        ``True`` if item has a default value or custom value set.
        """
        return self.default is not not_set or self._value is not not_set

    @property
    def section(self):
        """
        Config section (an instance of :class:`.Config`) to which the item has been added or ``None`` if
        it hasn't been added to a section yet.
        """
        return self._section

    def added_to_section(self, alias, section):
        """
        Hook to be used when extending *configmanager*. This is called
        when the item has been added to a section.
        """
        self._section = section
