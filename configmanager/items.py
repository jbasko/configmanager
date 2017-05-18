import copy

import six

from .exceptions import ConfigValueMissing
from .base import ItemAttribute, BaseItem
from .utils import not_set, parse_bool_str


class Item(BaseItem):
    name = ItemAttribute('name')
    default = ItemAttribute('default')
    type = ItemAttribute('type', default=str)
    raw_str_value = ItemAttribute('raw_str_value')
    required = ItemAttribute('required', default=False)

    def __init__(self, name=not_set, **kwargs):
        self._section = None

        if name is not not_set:
            if not isinstance(name, six.string_types):
                raise TypeError('Item name must be a string, got {!r}'.format(type(name)))
            self.name = name

        # Type must be set first because otherwise setting value below may fail.
        if 'type' in kwargs:
            self.type = kwargs.pop('type')
        else:
            # Type guessing
            value = kwargs.get('value', not_set)
            default = kwargs.get('default', not_set)
            if value is not not_set and value is not None:
                self.type = type(value)
            elif default is not not_set and default is not None:
                self.type = type(default)

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
        if self.raw_str_value is not not_set:
            return self.raw_str_value
        if self._value is not not_set or self.default is not not_set:
            return str(self.value)
        else:
            return repr(self)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, value):
        self.set(value)

    def get(self, fallback=not_set):
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
        self._value = not_set
        self.raw_str_value = not_set

    @property
    def is_default(self):
        return self._value is not_set or self._value == self.default

    @property
    def has_value(self):
        return self.default is not not_set or self._value is not not_set

    @property
    def section(self):
        return self._section

    def added_to_section(self, alias, section):
        self._section = section
