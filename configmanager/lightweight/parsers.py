import collections
import copy
import inspect
import types

from .items import LwItem


def is_config_declaration(obj):
    return (
        isinstance(obj, (dict, types.ModuleType))
        or
        inspect.isclass(obj)
    )


def is_config_instance(obj):
    return getattr(obj, 'cm__is_config_manager', False)


def parse_config_declaration(config_decl, item_cls=LwItem, tree_cls=collections.OrderedDict):
    """
    Args:
        config_decl: 
        tree_cls=collections.OrderedDict: change to ``dict`` in tests for comparisons because
            the iteration over items in declaration may be unordered.

    Returns:
        config_tree (collections.OrderedDict): an instance of ``tree_cls``
    """
    if isinstance(config_decl, dict):
        keys_and_values = config_decl.items()
    elif isinstance(config_decl, types.ModuleType):
        keys_and_values = config_decl.__dict__.items()
    elif inspect.isclass(config_decl):
        keys_and_values = config_decl.__dict__.items()
    else:
        raise TypeError('Unsupported config declaration type {!r}'.format(type(config_decl)))

    config_tree = tree_cls()

    for k, v in keys_and_values:
        if k.startswith('_'):
            continue
        elif is_config_declaration(v):
            config_tree[k] = parse_config_declaration(v, item_cls=item_cls, tree_cls=tree_cls)
        elif is_config_instance(v):
            config_tree[k] = v
        else:
            if isinstance(v, item_cls):
                item = copy.deepcopy(v)
                if not item.name:
                    item.name = k
            else:
                item = item_cls(name=k, default=v)
            config_tree[item.name] = item

    return config_tree
