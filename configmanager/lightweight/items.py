import copy

import six

from configmanager.exceptions import ConfigValueMissing
from configmanager.base import ItemAttribute
from configmanager.utils import not_set, parse_bool_str


class LwItem(object):
    name = ItemAttribute('name', default=None)
    default = ItemAttribute('default')
    type = ItemAttribute('type', default=str)
    raw_str_value = ItemAttribute('raw_str_value')
    required = ItemAttribute('required', default=False)

    def __init__(self, name=None, **kwargs):
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

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    @property
    def value(self):
        if self._value is not not_set:
            return self._value
        if self.default is not_set and self.required:
            raise ConfigValueMissing(self.name)
        return copy.deepcopy(self.default)

    @value.setter
    def value(self, value):
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
