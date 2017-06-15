from builtins import str
import copy
import os

import six

from .base import ItemAttribute, BaseItem
from .exceptions import RequiredValueMissing
from .item_types import Types
from .utils import not_set


class Item(BaseItem):
    """
    Represents a configuration item -- something that has a name, a type, a default value,
    a user- or environment-specific (custom) value, and other attributes.

    Item attribute name should start with a letter.

    When instantiating an item, you can pass *any* attributes, even ones not declared
    in *configmanager* code::

        >>> threads = Item(default=5, comment='I was here')
        >>> threads.comment
        'I was here'

    If you pass attributes as *kwargs*, names prefixed with ``@`` symbol will have
    ``@`` removed and will be treated like normal attributes::

        >>> t = Item(**{'@name': 'threads', '@default': 5})
        >>> t.name
        'threads'
        >>> t.default
        5
        >>> t.type
        int
    """

    #: Name of the config item.
    name = ItemAttribute('name')

    #: Type of the config item's value, a callable. Defaults to string.
    type = ItemAttribute('type', default=Types.str)

    raw_str_value = ItemAttribute('raw_str_value')

    #: ``True`` if config item requires a value.
    #: Note that if an item has a default value, marking it as ``required`` will have no effect.
    required = ItemAttribute('required', default=False)

    #: If set to a string, will use that as the name of the environment variable and will not consult envvar_name.
    #: If set to True, will use value of envvar_name as the name of environment variable to check for value override.
    #: If set to True and envvar_name is not set, will use auto-generated name based on item's path
    #: in the configuration tree: SECTION1_SECTION2_ITEMNAME.
    envvar = ItemAttribute('envvar', default=None)

    #: See envvar.
    #: Note that you can override this so you don't have to specify name for each enabled envvar individually.
    envvar_name = ItemAttribute('envvar_name', default=None, allow_dynamic_override=True)

    def _get_kwarg(self, name, kwargs):
        """
        Helper to get value of a named attribute irrespective of whether it is passed
        with or without "@" prefix.
        """
        at_name = '@{}'.format(name)

        if name in kwargs:
            if at_name in kwargs:
                raise ValueError('Both {!r} and {!r} specified in kwargs'.format(name, at_name))
            return kwargs[name]

        if at_name in kwargs:
            return kwargs[at_name]

        return not_set

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
        type_ = self._get_kwarg('type', kwargs)
        if type_ is not not_set:
            self.type = Types.translate(type_)

        else:
            #
            # Type guessing
            #
            value = self._get_kwarg('value', kwargs)
            default = self._get_kwarg('default', kwargs)

            if value is not not_set and value is not None:
                self.type = Types.guess(value)
            elif default is not not_set and default is not None:
                self.type = Types.guess(default)

        self._value = not_set
        self._default = not_set

        #
        # Set all attributes except type which has already been set.
        # Unknown extra attributes are OK.
        #
        for k, v in kwargs.items():
            if k in ('type', '@type'):
                continue

            if k.startswith('_'):
                raise ValueError('Item attribute names should start with a letter, got {!r}'.format(k))

            # Allow user to pass meta information with @ prefixes
            if k.startswith('@'):
                setattr(self, k[1:], v)
            else:
                setattr(self, k, v)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError()
        if self.section:
            return self.section.get_item_attribute(self, name)
        raise AttributeError(name)

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

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        if value is not_set or value is None:
            self._default = value
            return
        self._default = self.type.deserialize(value)

    def get(self, fallback=not_set):
        """
        Returns config value.

        See Also:
            :meth:`.set` and :attr:`.value`
        """
        if self.envvar:
            if self.envvar is True:
                envvar_name = self.envvar_name
                if envvar_name is None:
                    envvar_name = '_'.join(self.get_path()).upper()
                if envvar_name in os.environ:
                    return self.type.deserialize(os.environ[envvar_name])
            else:
                if self.envvar in os.environ:
                    return self.type.deserialize(os.environ[self.envvar])

        if self.has_value:
            if self._value is not not_set:
                return self._value
            else:
                return copy.deepcopy(self.default)
        elif fallback is not not_set:
            return fallback
        elif self.required:
            raise RequiredValueMissing(name=self.name, item=self)
        return fallback

    def set(self, value):
        """
        Sets config value.
        """
        old_value = self._value
        self.type.set_item_value(self, value)
        new_value = self._value
        if self.section:
            self.section._trigger_event(self.section.hooks.item_value_changed, item=self, old_value=old_value, new_value=new_value)

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

    def get_path(self):
        """
        Calculate item's path in configuration tree.
        Use this sparingly -- path is calculated by going up the configuration tree.
        For a large number of items, it is more efficient to use iterators that return paths
        as keys.

        Path value is stable only once the configuration tree is completely initialised.
        """
        if self.section:
            return self.section.get_path() + (self.name,)
        else:
            return self.name,
