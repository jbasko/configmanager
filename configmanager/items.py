import copy

import six

from .base import ItemAttribute
from .exceptions import ConfigValueMissing
from .utils import not_set, resolve_config_path, parse_bool_str


class ConfigItem(object):
    """
    Represents a single configurable thing which has a name (a path), a type, a default value, a value,
    and other things.
    """

    DEFAULT_SECTION = 'DEFAULT'
    strpath_separator = '/'

    #: Default value.
    default = ItemAttribute('default')

    #: Type, defaults to ``str``. Type can be any callable that converts a string to an instance of
    #: the expected type of the config value.
    type = ItemAttribute('type', default=str)

    # Internally, hold on to the raw string value that was used to set value, so that
    # when we persist the value, we use the same notation
    raw_str_value = ItemAttribute('raw_str_value')

    required = ItemAttribute('required', default=False)

    def __init__(self, *path, **kwargs):
        #: a ``tuple`` of config's path segments.
        self.path = None

        resolved = resolve_config_path(*path)
        if len(resolved) == 1:
            self.path = tuple([self.DEFAULT_SECTION]) + resolved
        else:
            self.path = resolved

        # NB! type must be set first because otherwise setting value below may fail.
        if 'type' in kwargs:
            self.type = kwargs.pop('type')

        self._value = not_set
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def strpath(self):
        return self.strpath_separator.join(self.path)

    @property
    def section(self):
        """
        The first segment of :attr:`.path`.
        """
        if len(self.path) != 2:
            raise RuntimeError('section is not defined for items with non-trivial paths')
        return self.path[0]

    @property
    def option(self):
        """
        The second segment of :attr:`.path`.
        """
        if len(self.path) != 2:
            raise RuntimeError('option is not defined for items with non-trivial paths')
        return self.path[-1]

    @property
    def name(self):
        """
        A string, the last segment of :attr:`.path`.
        """
        return self.path[-1]

    @property
    def value(self):
        """
        Value or default value (if no value set) of the :class:`.ConfigItem` instance. 
        """
        if self._value is not not_set:
            return self._value
        if self.default is not_set and self.required:
            raise ConfigValueMissing(self.path)

        # In case default value is a mutable type, you don't want user to accidentally change
        # the defaults!
        return copy.deepcopy(self.default)

    @value.setter
    def value(self, value):
        self._value = self._parse_str_value(value)
        if not issubclass(self.type, six.string_types):
            if isinstance(value, six.string_types):
                self.raw_str_value = value
            else:
                self.raw_str_value = not_set

    @property
    def has_value(self):
        """
        Returns:
            ``True`` if the :class:`.ConfigItem` has a value set.
        """
        return self._value is not not_set

    @property
    def is_default(self):
        """
        Returns:
            ``True`` if item does not have a value set, or its value equals the default value.
                In other words, it returns ``True`` if item's resolved value equals its default value.
                This is NOT the opposite of :attr:`.has_value`!
        """
        return self._value is not_set or self._value == self.default

    @property
    def has_default(self):
        """
        Is ``True`` if the :class:`.ConfigItem` has the default value set.
        """
        return self.default is not not_set

    def __str__(self):
        if self.raw_str_value is not not_set:
            return self.raw_str_value
        if self.has_value or self.has_default:
            return str(self.value)
        else:
            return repr(self)

    def __hash__(self):
        return hash(
            (self.type, self.path, self._value if self.has_value else self.default)
        )

    def __eq__(self, other):
        if isinstance(other, ConfigItem):
            # if self is other:
            #     return True
            return (
                self.type == other.type
                and
                self.path == other.path
                and
                (
                    (
                        # Both have a value that can be compared
                        (self.has_value or self.has_default)
                        and (other.has_value or other.has_default)
                        and (self.value == other.value)
                    )
                    or
                    (
                        # Neither has value that can be compared
                        not (self.has_value or self.has_default)
                        and not (other.has_value or other.has_default)
                    )
                )
            )
        return False

    def reset(self):
        """
        Unsets :attr:`value`. 
        """
        self._value = not_set
        self.raw_str_value = not_set

    def __repr__(self):
        if self.has_value:
            value = str(self.value)
        elif self.default is not not_set:
            value = str(self.default)
        else:
            value = self.default

        return '<{} {} {!r}>'.format(self.__class__.__name__, self.strpath, value)

    def _parse_str_value(self, str_value):
        if str_value is None or str_value is not_set:
            return str_value
        elif self.type is bool:
            return parse_bool_str(str_value)
        else:
            return self.type(str_value)
