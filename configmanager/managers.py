import collections
import configparser
import copy

import six

from .persistence import ConfigPersistenceAdapter, YamlReaderWriter, JsonReaderWriter, ConfigParserReaderWriter
from .base import BaseSection, is_config_item, is_config_section
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
        return '<{cls} {alias} at {id}>'.format(cls=self.__class__.__name__, alias=self.alias, id=id(self))

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
        return len(self._cm__configs)

    def __nonzero__(self):
        return True

    def __bool__(self):
        return True

    def __iter__(self):
        for name in self._cm__configs.keys():
            yield name

    def iter_items(self, recursive=False, key='path'):
        """

        Args:
            recursive: if ``True``, recurse into sub-sections.
            key: ``path`` (default) or ``name``

        Returns:
            iterator: iterator over ``(path_or_name, item)`` pairs of all items
                in this section (and sub-sections if ``recursive=True``).

        """

        for path, obj in self.iter_all(recursive=recursive):
            if obj.is_item:
                if key == 'path':
                    yield path, obj
                elif key == 'name':
                    yield obj.name, obj
                else:
                    raise ValueError('Invalid iter_items key {!r}'.format(key))

    def iter_sections(self, recursive=False, key='path'):
        """
        Args:
            recursive: if ``True``, recurse into sub-sections.
            key: ``path`` (default) or ``alias``

        Returns:
            iterator: iterator over ``(path_or_alias, section)`` pairs of all sections
                in this section (and sub-sections if ``recursive=True``).
        """
        for path, obj in self.iter_all(recursive=recursive):
            if obj.is_section:
                if key == 'path':
                    yield path, obj
                elif key in ('name', 'alias'):
                    yield obj.alias, obj
                else:
                    raise ValueError('Invalid iter_sections key {!r}'.format(key))

    def iter_all(self, recursive=False):
        """
        Args:
            recursive: if ``True``, recurse into sub-sections

        Returns:
            iterator: iterator over ``(path, obj)`` pairs of all items and
            sections contained in this section.
        """
        names_yielded = set()

        for obj_alias, obj in self._cm__configs.items():
            if obj.is_section:
                if obj.alias in names_yielded:
                    continue
                names_yielded.add(obj.alias)

                yield (obj.alias,), obj

                if not recursive:
                    continue

                for sub_item_path, sub_item in obj.iter_all(recursive=recursive):
                    yield (obj_alias,) + sub_item_path, sub_item

            else:
                # _cm__configs contains duplicates so that we can have multiple aliases point
                # to the same item. We have to de-duplicate here.
                if obj.name in names_yielded:
                    continue
                names_yielded.add(obj.name)

                yield (obj.name,), obj

    def iter_paths(self, recursive=False):
        """

        Args:
            recursive: if ``True``, recurse into sub-sections

        Returns:
            iterator: iterator over paths of all items and sections
            contained in this section.

        """
        for path, _ in self.iter_all(recursive=recursive):
            yield path

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
            if is_config_section(item):
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
        for _, item in self.iter_items(recursive=True):
            item.reset()

    @property
    def is_default(self):
        """
        ``True`` if values of all config items in this section and its subsections
        have their values equal to defaults or have no value set.
        """
        for _, item in self.iter_items(recursive=True):
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
        Adapter to dump/load INI format strings and files using standard library's
        ``ConfigParser`` (or the backported configparser module in Python 2).
        
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
        
        Returns:
            ConfigPersistenceAdapter
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
        
        Returns:
            ConfigPersistenceAdapter
        """
        if self._cm__yaml_adapter is None:
            self._cm__yaml_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=YamlReaderWriter(),
            )
        return self._cm__yaml_adapter

    def add_item(self, alias, item):
        """
        Add a config item to this section.
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
        Add a sub-section to this section.
        """
        if not isinstance(alias, six.string_types):
            raise TypeError('Section name must be a string, got a {!r}'.format(type(alias)))
        self._cm__configs[alias] = section
        section.added_to_section(alias, self)
