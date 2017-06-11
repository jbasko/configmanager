import collections
import inspect

import six

from configmanager.base import BaseItem, BaseSection


def parse_config_declaration(declaration, parent_section=None, root=None):
    if root:
        parent_section = root

        is_valid_config_root_declaration = (
            inspect.ismodule(declaration)
            or
            (
                isinstance(declaration, collections.Sequence)
                and len(declaration) > 0
                and isinstance(declaration[0], tuple)
            )
            or
            (
                isinstance(declaration, collections.Mapping)
                and len(declaration) > 0
            )
        )
        if not is_valid_config_root_declaration:
            raise ValueError(
                'Config root declaration has to be a module, a non-empty sequence, or non-empty mapping, '
                'got a {}'.format(type(declaration)),
            )

    if isinstance(declaration, (BaseItem, BaseSection)):
        # Do not parse existing objects of our hierarchy
        return declaration

    elif inspect.ismodule(declaration):
        return parse_config_declaration(declaration.__dict__, parent_section=parent_section, root=root)

    elif isinstance(declaration, collections.Mapping):

        if len(declaration) == 0:
            # Empty dictionary means an empty item
            return parent_section.create_item(default=declaration)

        # Create a list of tuples so we can use the standard declaration parser below
        return parse_config_declaration([x for x in declaration.items()], parent_section=parent_section, root=root)

    if isinstance(declaration, collections.Sequence) and not isinstance(declaration, six.string_types):

        if len(declaration) == 0 or not isinstance(declaration[0], tuple):
            # Declaration of an item
            return parent_section.create_item(default=declaration)

        # Pre-process all keys and discard private parts and separate out meta parts
        clean_declaration = []
        meta = {}

        for k, v in declaration:
            if k.startswith('_'):
                continue
            elif k.startswith('@'):
                meta[k[1:]] = v
                continue
            clean_declaration.append((k, v))

        if not clean_declaration or meta.get('type'):
            # Must be an item
            if not clean_declaration:
                return parent_section.create_item(**meta)
            else:
                meta['default'] = dict(clean_declaration)
                return parent_section.create_item(**meta)

        section = root or parent_section.create_section()

        for k, v in clean_declaration:
            obj = parse_config_declaration(v, parent_section=section)
            if obj.is_section:
                section.add_section(k, obj)
            else:
                section.add_item(k, obj)

        return section

    # Declaration of an item
    return parent_section.create_item(default=declaration)
