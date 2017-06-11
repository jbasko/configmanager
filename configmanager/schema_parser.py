import collections
import inspect

import six

from .base import BaseItem, BaseSection


def parse_config_schema(schema, parent_section=None, root=None):
    if root:
        parent_section = root

        is_valid_config_root_schema = (
            inspect.ismodule(schema)
            or
            (
                isinstance(schema, collections.Sequence)
                and len(schema) > 0
                and isinstance(schema[0], tuple)
            )
            or
            (
                isinstance(schema, collections.Mapping)
                and len(schema) > 0
            )
        )
        if not is_valid_config_root_schema:
            raise ValueError(
                'Config root schema has to be a module, a non-empty sequence, or non-empty mapping, '
                'got a {}'.format(type(schema)),
            )

    if isinstance(schema, (BaseItem, BaseSection)):
        # Do not parse existing objects of our hierarchy
        return schema

    elif inspect.ismodule(schema):
        return parse_config_schema(schema.__dict__, parent_section=parent_section, root=root)

    elif isinstance(schema, collections.Mapping):

        if len(schema) == 0:
            # Empty dictionary means an empty item
            return parent_section.create_item(default=schema)

        # Create a list of tuples so we can use the standard schema parser below
        return parse_config_schema([x for x in schema.items()], parent_section=parent_section, root=root)

    if isinstance(schema, collections.Sequence) and not isinstance(schema, six.string_types):

        if len(schema) == 0 or not isinstance(schema[0], tuple):
            # Declaration of an item
            return parent_section.create_item(default=schema)

        # Pre-process all keys and discard private parts and separate out meta parts
        clean_schema = []
        meta = {}

        for k, v in schema:
            if k.startswith('_'):
                continue
            elif k.startswith('@'):
                meta[k[1:]] = v
                continue
            clean_schema.append((k, v))

        if not clean_schema or meta.get('type'):
            # Must be an item
            if not clean_schema:
                return parent_section.create_item(**meta)
            else:
                meta['default'] = dict(clean_schema)
                return parent_section.create_item(**meta)

        # If root is specified it means we are parsing schema for the root,
        # so no need to create a new section.
        section = root or parent_section.create_section()

        for k, v in clean_schema:
            obj = parse_config_schema(v, parent_section=section)
            if obj.is_section:
                section.add_section(k, obj)
            else:
                section.add_item(k, obj)

        return section

    # Declaration of an item
    return parent_section.create_item(default=schema)
