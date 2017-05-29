import copy
import inspect
import os.path
import types

import collections
import six

from .base import is_config_item, is_config_section


def is_config_declaration(obj):
    return (
        isinstance(obj, (dict, types.ModuleType))
        or
        inspect.isclass(obj)
    )


def get_file_adapter_name(filename):
    adapter_lookup = {
        '.json': 'json',
        '.js': 'json',
        '.ini': 'configparser',
        '.yaml': 'yaml',
        '.yml': 'yaml',
    }

    _, ext = os.path.splitext(filename)
    return adapter_lookup.get(ext.lower(), 'configparser')


class ConfigDeclarationParser(object):
    def __init__(self, section):
        assert section
        assert hasattr(section, 'create_item')
        assert hasattr(section, 'create_section')
        self.section = section

    def __call__(self, config_decl, section=None):
        if section is None:
            section = self.section

        if isinstance(config_decl, dict):
            keys_and_values = config_decl.items()
        elif isinstance(config_decl, types.ModuleType):
            keys_and_values = config_decl.__dict__.items()
        elif inspect.isclass(config_decl):
            keys_and_values = config_decl.__dict__.items()
        elif isinstance(config_decl, (tuple, list)):
            items = collections.OrderedDict()
            for x in config_decl:
                if is_config_item(x):
                    items[x.name] = x
                elif isinstance(x, tuple):
                    items[x[0]] = x[1]
                elif isinstance(x, six.string_types):
                    items[x] = section.cm__item_cls()
                else:
                    raise TypeError('Unexpected {!r} {!r} in list of items for config declaration'.format(type(x), x))
            keys_and_values = items.items()
        elif isinstance(config_decl, six.string_types):
            getattr(section, get_file_adapter_name(config_decl)).load(config_decl, as_defaults=True)
            keys_and_values = ()
        else:
            raise TypeError('Unsupported config declaration type {!r}'.format(type(config_decl)))

        for k, v in keys_and_values:
            if not isinstance(k, six.string_types):
                raise TypeError('Config section and item names must be strings, got {}: {!r}'.format(type(k), k))
            if k.startswith('_'):
                continue
            elif is_config_section(v):
                section.add_section(k, v)
            elif is_config_declaration(v):
                section.add_section(k, self.__call__(v, section=self.section.create_section()))
            elif is_config_item(v):
                section.add_item(k, copy.deepcopy(v))
            else:
                section.add_item(k, self.section.create_item(default=copy.deepcopy(v)))

        return section
