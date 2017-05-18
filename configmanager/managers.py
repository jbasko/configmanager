import collections
import configparser
import copy

import six

from .base import BaseSection, is_config_item
from .items import Item
from .parsers import ConfigDeclarationParser
from .persistence import ConfigParserAdapter
from .utils import not_set


class Config(BaseSection):
    """
    Represents a section consisting of config items (instances of :class:`.Item`) and other sections
    (instances of :class:`.Config`).
    
    Notes:
        Members whose name starts with "cm__" are public, but should only be 
        used to customise (extend) the behaviour of Config.
        Members whose name starts with "_cm__" should not be accessed directly.
    
    .. attribute:: Config(config_declaration=None, item_cls=None, configparser_factory=None)
        
        Creates a config section from a declaration, optionally specifies the class used to
        auto-create new config items, and the class used to create ``ConfigParser`` instances
        if needed.
    
    .. attribute:: <config>[name]
    
        Access a config item by its name.
        
        Returns:
            :class:`.Item`
    
    .. attribute:: <config>.<name>
    
        Access a config item by its name.
        
        Returns:
            :class:`.Item`
    """

    cm__item_cls = Item
    cm__configparser_factory = configparser.ConfigParser

    def __new__(cls, config_declaration=None, item_cls=None, configparser_factory=None):
        instance = super(Config, cls).__new__(cls)

        instance._cm__section = None
        instance._cm__configs = collections.OrderedDict()
        instance._cm__configparser_adapter = None

        if item_cls:
            instance.cm__item_cls = item_cls
        if configparser_factory:
            instance.cm__configparser_factory = configparser_factory

        instance.cm__process_config_declaration = ConfigDeclarationParser(section=instance)

        if config_declaration:
            instance.cm__process_config_declaration(config_declaration)

        return instance

    def __repr__(self):
        return '<{cls} at {id}>'.format(cls=self.__class__.__name__, id=id(self))

    def __contains__(self, item):
        return item in self._cm__configs

    def __setitem__(self, name, value):
        if is_config_item(value):
            self.cm__add_item(name, value)
        elif isinstance(value, self.__class__):
            self.cm__add_section(name, value)
        else:
            raise TypeError(
                'Config sections/items can only be replaced with sections/items, '
                'got {type}. To set value use ..[{name}].value = <new_value>'.format(
                    type=type(value),
                    name=name,
                )
            )

    def __getitem__(self, name):
        return self._cm__configs[name]

    def __getattr__(self, name):
        if name in self._cm__configs:
            return self._cm__configs[name]
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith('cm__') or name.startswith('_cm__'):
            return super(Config, self).__setattr__(name, value)
        elif is_config_item(value):
            self.cm__add_item(name, value)
        elif isinstance(value, self.__class__):
            self.cm__add_section(name, value)
        else:
            raise TypeError(
                'Config sections/items can only be replaced with sections/items, '
                'got {type}. To set value use {name}.value = <new_value> notation.'.format(
                    type=type(value),
                    name=name,
                )
            )

    def iter_items(self):
        """
        Iterate over all items contained (recursively).
        
        Returns:
            iterator: iterator over all items contained in this config and its
                sections recursively.
        """
        names_yielded = set()
        for item_name, item in self._cm__configs.items():
            if isinstance(item, self.__class__):
                for sub_item_path, sub_item in item.iter_items():
                    yield (item_name,) + sub_item_path, sub_item
            else:
                # _cm__configs contains duplicates so that we can have multiple aliases point
                # to the same item. We have to de-duplicate here.
                if item.name in names_yielded:
                    continue
                names_yielded.add(item.name)

                yield (item.name,), item

    def iter_sections(self):
        """
        Iterate over sections of this config.
        Does not recurse into sub-sections of sections.
        
        Returns:
            iterator: iterator over direct sub-sections of this section.
        """
        for item_name, item in self._cm__configs.items():
            if isinstance(item, self.__class__):
                yield item_name, item

    def to_dict(self):
        """
        Export values of all items contained in this section to a dictionary.
        
        Returns:
            dict: A dictionary of key-value pairs, where for sections values are dictionaries
            of their contents.
        
        See Also:
            :meth:`.read_dict` does the opposite.
        """
        values = {}
        for item_name, item in self._cm__configs.items():
            if isinstance(item, self.__class__):
                section_values = item.to_dict()
                if section_values:
                    values[item_name] = section_values
            else:
                if item.has_value:
                    values[item.name] = item.value
        return values

    def read_dict(self, dictionary, as_defaults=False):
        """
        Import config values from a dictionary.
        
        When ``as_defaults`` is set to ``True``, the values
        imported will be set as defaults. This can be used to
        declare the sections and items of configuration.
        Values of sections and items in ``dictionary`` can be
        dictionaries as well as instances of :class:`.Item` and
        :class:`.Config`.
        
        Args:
            dictionary: 
            as_defaults: if ``True``, the imported values will be set as defaults.
        
        See Also:
            :meth:`to_dict` does the opposite.
        """
        if as_defaults:
            self.cm__process_config_declaration(dictionary)
        else:
            for name, value in dictionary.items():
                if name not in self:
                    continue
                if is_config_item(self[name]):
                    self[name].value = value
                else:
                    self[name].read_dict(value, as_defaults=as_defaults)

    def reset(self):
        """
        Recursively resets values of all items contained in this section
        and its subsections to their default values.
        """
        for _, item in self.iter_items():
            item.reset()

    @property
    def is_default(self):
        """
        ``True`` if values of all config items in this section and its subsections
        have their values equal to defaults or have no value set.
        """
        for _, item in self.iter_items():
            if not item.is_default:
                return False
        return True

    @property
    def section(self):
        """
        Returns:
            (:class:`.Config`): section to which this section belongs or ``None`` if this
            hasn't been added to any section.
        """
        return self._cm__section

    def added_to_section(self, alias, section):
        """
        A hook that is called when this section is added to another.
        This should only be called when extending functionality of :class:`.Config`.
        
        Args:
            alias (str): alias with which the section as added as a sub-section to another 
            section (:class:`.Config`): section to which this section has been added
        """
        self._cm__section = section

    @property
    def configparser(self):
        """
        Adapter which exposes some of Python standard library's ``configparser.ConfigParser``
        (or ``ConfigParser.ConfigParser`` in Python 2) functionality
        to read and write INI format files. 
        
        Returns:
            :class:`.ConfigParserAdapter`
        """
        if self._cm__configparser_adapter is None:
            self._cm__configparser_adapter = ConfigParserAdapter(
                config=self,
                config_parser_factory=self.cm__configparser_factory,
            )
        return self._cm__configparser_adapter

    def cm__add_item(self, alias, item):
        """
        Internal method used to add a config item to this section.
        Should only be called or overridden when extending *configmanager*'s functionality.
        
        Warnings:
            The name of the method may change.
        """
        if not isinstance(alias, six.string_types):
            raise TypeError('Item name must be a string, got a {!r}'.format(type(alias)))
        item = copy.deepcopy(item)
        if item.name is not_set:
            item.name = alias
        self._cm__configs[item.name] = item
        self._cm__configs[alias] = item
        item.added_to_section(alias, self)

    def cm__add_section(self, alias, section):
        """
        Internal method used to add a sub-section to this section.
        
        Should only be called or overridden when extending *configmanager*'s functionality.

        Warnings:
            The name of the method may change.
        """
        if not isinstance(alias, six.string_types):
            raise TypeError('Section name must be a string, got a {!r}'.format(type(alias)))
        self._cm__configs[alias] = section
        section.added_to_section(alias, self)
