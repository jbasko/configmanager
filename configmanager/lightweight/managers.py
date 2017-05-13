import collections

from .items import LwItem
from .parsers import parse_config_declaration


class LwConfig(object):
    """
    Represents a collection of config items or sections of items
    which in turn are instances of Config.
    """
    cm__item_cls = LwItem

    @classmethod
    def create(cls, config_declaration=None):
        if config_declaration:
            return parse_config_declaration(config_declaration, item_cls=cls.cm__item_cls, tree_cls=cls)
        else:
            return cls()

    def __init__(self):
        self.cm__configs = collections.OrderedDict()
        self.cm__is_config_manager = True

    def __contains__(self, item):
        return item in self.cm__configs

    def __setitem__(self, name, value):
        if isinstance(value, (self.cm__item_cls, self.__class__)):
            self.cm__configs[name] = value
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
        elif isinstance(value, (self.cm__item_cls, self.__class__)):
            self.cm__configs[name] = value
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
        for item_name, item in self.cm__configs.items():
            if isinstance(item, self.__class__):
                for sub_item_path, sub_item in item.iter_items():
                    yield (item_name,) + sub_item_path, sub_item
            else:
                yield (item_name,), item

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
                values[item_name] = item.to_dict(**kwargs)
            else:
                values[item_name] = item.value
        return values