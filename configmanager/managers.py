import collections
import configparser
import copy

import six

from .persistence import ConfigPersistenceAdapter, YamlReaderWriter, JsonReaderWriter, ConfigParserReaderWriter
from .base import BaseSection, is_config_item
from .items import Item
from .parsers import ConfigDeclarationParser
from .utils import not_set


class Config(BaseSection):
    """
    Represents a section consisting of config items (instances of :class:`.Item`) and other sections
    (instances of :class:`.Config`).
    
    .. attribute:: Config(config_declaration=None, item_cls=None, configparser_factory=None)
        
        Creates a config section from a declaration, optionally specifies the class used to
        auto-create new config items, and the class used to create ``ConfigParser`` instances
        if needed.
    
    .. attribute:: <config>[name_or_path]
    
        Access a config item or section by its name or path. Name is a string, path is a tuple of strings.
        
        Returns:
            :class:`.Item` or :class:`.Config`
    
    .. attribute:: <config>.<name>
    
        Access a config item or section by its name.
        
        Returns:
            :class:`.Item` or :class:`.Config`
    """

    cm__item_cls = Item
    cm__configparser_factory = configparser.ConfigParser

    def __new__(cls, config_declaration=None, item_cls=None, configparser_factory=None):
        if config_declaration and isinstance(config_declaration, cls):
            return copy.deepcopy(config_declaration)

        instance = super(Config, cls).__new__(cls)
        instance._cm__section = None
        instance._cm__section_alias = None
        instance._cm__configs = collections.OrderedDict()
        instance._cm__configparser_adapter = None
        instance._cm__json_adapter = None
        instance._cm__yaml_adapter = None

        if item_cls:
            instance.cm__item_cls = item_cls
        if configparser_factory:
            instance.cm__configparser_factory = configparser_factory

        instance._cm__process_config_declaration = ConfigDeclarationParser(section=instance)

        if config_declaration:
            instance._cm__process_config_declaration(config_declaration)

        return instance

    def __repr__(self):
        return '<{cls} at {id}>'.format(cls=self.__class__.__name__, id=id(self))

    def _resolve_config_key(self, key):
        if isinstance(key, six.string_types):
            return self._cm__configs[key]
        elif isinstance(key, (tuple, list)) and len(key) > 0:
            if len(key) == 1:
                return self[key[0]]
            else:
                return self[key[0]][key[1:]]
        else:
            raise TypeError('Expected either a string or a tuple as key, got {!r}'.format(key))

    def __contains__(self, key):
        try:
            _ = self._resolve_config_key(key)
            return True
        except KeyError:
            return False

    def __setitem__(self, key, value):
        if isinstance(key, six.string_types):
            name = key
            rest = None
        elif isinstance(key, (tuple, list)) and len(key) > 0:
            name = key[0]
            if len(key) == 1:
                rest = None
            else:
                rest = key[1:]
        else:
            raise TypeError('Expected either a string or a tuple as key, got {!r}'.format(key))

        if rest:
            self[name][rest] = value
            return

        if is_config_item(value):
            self.add_item(name, value)
        elif isinstance(value, self.__class__):
            self.add_section(name, value)
        else:
            raise TypeError(
                'Config sections/items can only be replaced with sections/items, '
                'got {type}. To set value use ..[{name}].value = <new_value>'.format(
                    type=type(value),
                    name=name,
                )
            )

    def __getitem__(self, key):
        return self._resolve_config_key(key)

    def __getattr__(self, name):
        if name in self._cm__configs:
            return self._cm__configs[name]
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith('cm__') or name.startswith('_cm__'):
            return super(Config, self).__setattr__(name, value)
        elif is_config_item(value):
            self.add_item(name, value)
        elif isinstance(value, self.__class__):
            self.add_section(name, value)
        else:
            raise TypeError(
                'Config sections/items can only be replaced with sections/items, '
                'got {type}. To set value use {name}.value = <new_value> notation.'.format(
                    type=type(value),
                    name=name,
                )
            )

    def __len__(self):
        return sum(1 for _ in self.iter_items())

    def __nonzero__(self):
        return True

    def __bool__(self):
        return True

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

    def to_dict(self, with_defaults=True, dict_cls=dict):
        """
        Export values of all items contained in this section to a dictionary.
        
        Returns:
            dict: A dictionary of key-value pairs, where for sections values are dictionaries
            of their contents.
        
        See Also:
            :meth:`.read_dict` does the opposite.
        """
        values = dict_cls()
        for item_name, item in self._cm__configs.items():
            if isinstance(item, self.__class__):
                section_values = item.to_dict(with_defaults=with_defaults, dict_cls=dict_cls)
                if section_values:
                    values[item_name] = section_values
            else:
                if item.has_value:
                    if with_defaults or not item.is_default:
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
        for name, value in dictionary.items():
            if name not in self:
                if as_defaults:
                    if isinstance(value, dict):
                        self[name] = self.create_section()
                        self[name].read_dict(value, as_defaults=as_defaults)
                    else:
                        self[name] = self.create_item(name, default=value)
                else:
                    # Skip unknown names if not interpreting dictionary as defaults
                    continue
            elif is_config_item(self[name]):
                if as_defaults:
                    self[name].default = value
                else:
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

    @property
    def alias(self):
        """
        Returns alias with which this section was added to another or ``None`` if it hasn't been added
        to any.
        
        Returns:
            (str)
        """
        return self._cm__section_alias

    def added_to_section(self, alias, section):
        """
        A hook that is called when this section is added to another.
        This should only be called when extending functionality of :class:`.Config`.
        
        Args:
            alias (str): alias with which the section as added as a sub-section to another 
            section (:class:`.Config`): section to which this section has been added
        """
        self._cm__section = section
        self._cm__section_alias = alias

    @property
    def configparser(self):
        """
        Adapter which exposes some of Python standard library's ``configparser.ConfigParser``
        (or ``ConfigParser.ConfigParser`` in Python 2) functionality
        to load and dump INI format files. 
        
        Returns:
            ConfigPersistenceAdapter
        """
        if self._cm__configparser_adapter is None:
            self._cm__configparser_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=ConfigParserReaderWriter(
                    config_parser_factory=self.cm__configparser_factory,
                ),
            )
        return self._cm__configparser_adapter

    @property
    def json(self):
        """
        Adapter to dump/load JSON format strings and files.
        """
        if self._cm__json_adapter is None:
            self._cm__json_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=JsonReaderWriter(),
            )
        return self._cm__json_adapter

    @property
    def yaml(self):
        """
        Adapter to dump/load YAML format strings and files.
        """
        if self._cm__yaml_adapter is None:
            self._cm__yaml_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=YamlReaderWriter(),
            )
        return self._cm__yaml_adapter

    def add_item(self, alias, item):
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

    def add_section(self, alias, section):
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
