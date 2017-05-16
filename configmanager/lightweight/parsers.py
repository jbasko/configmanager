import copy
import inspect
import types

import six

from configmanager.base import is_config_instance, is_config_item


def is_config_declaration(obj):
    return (
        isinstance(obj, (dict, types.ModuleType))
        or
        inspect.isclass(obj)
    )


class ConfigDeclarationParser(object):
    def __init__(self, section):
        assert section
        assert hasattr(section, 'cm__create_item')
        assert hasattr(section, 'cm__create_section')
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
        else:
            raise TypeError('Unsupported config declaration type {!r}'.format(type(config_decl)))

        for k, v in keys_and_values:
            if not isinstance(k, six.string_types):
                raise TypeError('Config section and item names must be strings, got {}: {!r}'.format(type(k), k))
            if k.startswith('_'):
                continue
            elif is_config_instance(v):
                section[k] = v
            elif is_config_declaration(v):
                section[k] = self.__call__(v, section=self.section.cm__create_section())
            elif is_config_item(v):
                section[k] = copy.deepcopy(v)
            else:
                section[k] = self.section.cm__create_item(default=copy.deepcopy(v))

        return section
