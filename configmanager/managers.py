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
    Represents a collection of config items or sections of items
    which in turn are instances of Config.
    
    Notes:
        Members whose name starts with "cm__" are public, but should only be 
        used to customise (extend) the behaviour of Config.
        Members whose name starts with "_cm__" should not be accessed directly.
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

    def cm__add_item(self, alias, item):
        if not isinstance(alias, six.string_types):
            raise TypeError('Item name must be a string, got a {!r}'.format(type(alias)))
        item = copy.deepcopy(item)
        if item.name is not_set:
            item.name = alias
        self._cm__configs[item.name] = item
        self._cm__configs[alias] = item
        item.added_to_section(alias, self)

    def cm__add_section(self, alias, section):
        if not isinstance(alias, six.string_types):
            raise TypeError('Section name must be a string, got a {!r}'.format(type(alias)))
        self._cm__configs[alias] = section
        section.added_to_section(alias, self)

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
            iterator: iterator over sections of this config.
        """
        for item_name, item in self._cm__configs.items():
            if isinstance(item, self.__class__):
                yield item_name, item

    def to_dict(self, **kwargs):
        values = {}
        for item_name, item in self._cm__configs.items():
            if isinstance(item, self.__class__):
                section_values = item.to_dict(**kwargs)
                if section_values:
                    values[item_name] = section_values
            else:
                if item.has_value:
                    values[item.name] = item.value
        return values

    def read_dict(self, dictionary, as_defaults=False):
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
        for _, item in self.iter_items():
            item.reset()

    @property
    def is_default(self):
        for _, item in self.iter_items():
            if not item.is_default:
                return False
        return True

    @property
    def section(self):
        return self._cm__section

    def added_to_section(self, alias, section):
        self._cm__section = section

    @property
    def configparser(self):
        """
        Returns:
            ConfigParserAdapter
        """
        if self._cm__configparser_adapter is None:
            self._cm__configparser_adapter = ConfigParserAdapter(
                config=self,
                config_parser_factory=self.cm__configparser_factory,
            )
        return self._cm__configparser_adapter
