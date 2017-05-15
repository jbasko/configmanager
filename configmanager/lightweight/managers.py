import collections

import configparser
import six

from configmanager.persistence import ConfigParserMixin
from configmanager.utils import not_set
from .items import LwItem
from .parsers import parse_config_declaration


class LwConfig(ConfigParserMixin, object):
    """
    Represents a collection of config items or sections of items
    which in turn are instances of Config.
    """
    cm__item_cls = LwItem
    cm__config_parser_factory = configparser.ConfigParser

    def __new__(cls, config_declaration=None):
        if config_declaration:
            return parse_config_declaration(config_declaration, item_cls=cls.cm__item_cls, tree_cls=cls)
        else:
            instance = super(LwConfig, cls).__new__(cls)
            instance.cm__configs = collections.OrderedDict()
            instance.cm__is_config_manager = True
            return instance

    def __repr__(self):
        return '<{cls} at {id}>'.format(cls=self.__class__.__name__, id=id(self))

    def __contains__(self, item):
        return item in self.cm__configs

    def __setitem__(self, name, value):
        if isinstance(value, self.cm__item_cls):
            self._cm__set_item(name, value)
        elif isinstance(value, self.__class__):
            self._cm__set_section(name, value)
        else:
            raise TypeError(
                'Config sections/items can only be replaced with sections/items, '
                'got {type}. To set value use ..[{name}].value = <new_value>'.format(
                    type=type(value),
                    name=name,
                )
            )

    def __getitem__(self, name):
        return self.cm__configs[name]

    def __getattr__(self, name):
        if name in self.cm__configs:
            return self.cm__configs[name]
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith('cm__'):
            return super(LwConfig, self).__setattr__(name, value)
        elif isinstance(value, self.cm__item_cls):
            self._cm__set_item(name, value)
        elif isinstance(value, self.__class__):
            self._cm__set_section(name, value)
        else:
            raise TypeError(
                'Config sections/items can only be replaced with sections/items, '
                'got {type}. To set value use {name}.value = <new_value> notation.'.format(
                    type=type(value),
                    name=name,
                )
            )

    def _cm__set_item(self, alias, item):
        if not isinstance(alias, six.string_types):
            raise TypeError('Item name must be a string, got a {!r}'.format(type(alias)))
        if item.name is not_set:
            item.name = alias
        self.cm__configs[item.name] = item
        self.cm__configs[alias] = item

    def _cm__set_section(self, alias, section):
        if not isinstance(alias, six.string_types):
            raise TypeError('Section name must be a string, got a {!r}'.format(type(alias)))
        self.cm__configs[alias] = section

    def iter_items(self):
        """
        Iterate over all items contained (recursively).
        
        Returns:
            iterator: iterator over all items contained in this config and its
                sections recursively.
        """
        names_yielded = set()
        for item_name, item in self.cm__configs.items():
            if isinstance(item, self.__class__):
                for sub_item_path, sub_item in item.iter_items():
                    yield (item_name,) + sub_item_path, sub_item
            else:
                # cm__configs contains duplicates so that we can have multiple aliases point
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
        for item_name, item in self.cm__configs.items():
            if isinstance(item, self.__class__):
                yield item_name, item

    def to_dict(self, **kwargs):
        values = {}
        for item_name, item in self.cm__configs.items():
            if isinstance(item, self.__class__):
                section_values = item.to_dict(**kwargs)
                if section_values:
                    values[item_name] = section_values
            else:
                if item.has_value:
                    values[item.name] = item.value
        return values

    def reset(self):
        for _, item in self.iter_items():
            item.reset()

    @property
    def is_default(self):
        for _, item in self.iter_items():
            if not item.is_default:
                return False
        return True
