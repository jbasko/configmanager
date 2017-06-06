import collections
import copy

import six

from .exceptions import NotFound
from .utils import not_set
from .base import BaseSection, is_config_item


class SimpleSection(BaseSection):
    """
    Core section functionality.

    Keep as light as possible.
    No persistence, hooks or other fancy features here.
    Add those on SimpleSection if at all.

    No customisation (section classes, item classes etc.) allowed here.
    An instance of SimpleSection is used internally to store customisation of configmanager itself.
    """

    def __init__(self):
        self._cm__configs = collections.OrderedDict()
        self._cm__section = None
        self._cm__section_alias = None

    def __len__(self):
        return len(self._cm__configs)

    def __nonzero__(self):
        return True

    def __bool__(self):
        return True

    def __iter__(self):
        for name in self._cm__configs.keys():
            yield name

    def __repr__(self):
        return '<{cls} {alias} at {id}>'.format(cls=self.__class__.__name__, alias=self.alias, id=id(self))

    def _resolve_config_key(self, key):
        if isinstance(key, six.string_types):
            if key in self._cm__configs:
                return self._cm__configs[key]
            else:
                raise NotFound(key, section=self)

        if isinstance(key, (tuple, list)) and len(key) > 0:
            if len(key) == 1:
                return self._resolve_config_key(key[0])
            else:
                return self._resolve_config_key(key[0])[key[1:]]
        else:
            raise TypeError('Expected either a string or a tuple as key, got {!r}'.format(key))

    def __contains__(self, key):
        try:
            _ = self._resolve_config_key(key)
            return True
        except NotFound:
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
                'SimpleSection sections/items can only be replaced with sections/items, '
                'got {type}. To set value use ..[{name}].value = <new_value>'.format(
                    type=type(value),
                    name=name,
                )
            )

    def __getitem__(self, key):
        return self._resolve_config_key(key)

    def __getattr__(self, name):
        if not isinstance(name, six.string_types):
            raise TypeError('Expected a string, got a {!r}'.format(type(name)))

        if name.startswith('_'):
            raise AttributeError(name)

        return self._resolve_config_key(name)

    def __setattr__(self, name, value):
        if name.startswith('cm__') or name.startswith('_cm__'):
            return super(SimpleSection, self).__setattr__(name, value)
        elif is_config_item(value):
            self.add_item(name, value)
        elif isinstance(value, self.__class__):
            self.add_section(name, value)
        else:
            raise TypeError(
                'SimpleSection sections/items can only be replaced with sections/items, '
                'got {type}. To set value use {name}.value = <new_value> notation.'.format(
                    type=type(value),
                    name=name,
                )
            )

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

        item._section = self

    def add_section(self, alias, section):
        """
        Add a sub-section to this section.
        """
        if not isinstance(alias, six.string_types):
            raise TypeError('Section name must be a string, got a {!r}'.format(type(alias)))

        self._cm__configs[alias] = section

        section._cm__section = self
        section._cm__section_alias = alias

    def _parse_path(self, path=None, separator='.'):
        if not path:
            return ()

        if isinstance(path, six.string_types):
            clean_path = tuple(path.split(separator))
        else:
            clean_path = path

        if clean_path not in self:
            for i, part in enumerate(clean_path):
                if clean_path[:i + 1] not in self:
                    raise NotFound(part)
            assert False  # shouldn't reach this line
        return clean_path

    def _get_recursive_iterator(self, recursive=False):
        """
        Basic recursive iterator whose only purpose is to yield all items
        and sections in order, with their full paths as keys.

        Main challenge is to de-duplicate items and sections which
        have aliases.

        Do not add any new features to this iterator, instead
        build others that extend this one.
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

                for sub_item_path, sub_item in obj._get_recursive_iterator(recursive=recursive):
                    yield (obj_alias,) + sub_item_path, sub_item

            else:
                # _cm__configs contains duplicates so that we can have multiple aliases point
                # to the same item. We have to de-duplicate here.
                if obj.name in names_yielded:
                    continue
                names_yielded.add(obj.name)

                yield (obj.name,), obj

    def _get_path_iterator(self, path=None, separator='.', recursive=False):
        clean_path = self._parse_path(path=path, separator=separator)

        config = self[clean_path] if clean_path else self

        if clean_path:
            yield clean_path, config

        if config.is_section:
            for path, obj in config._get_recursive_iterator(recursive=recursive):
                yield (clean_path + path), obj

    def iter_all(self, recursive=False, path=None, key='path', separator='.'):
        """
        Args:
            recursive: if ``True``, recurse into sub-sections

            path (tuple or string): optional path to limit iteration over.

            key: ``path`` (default), ``str_path``, ``name``, or ``None``.

            separator (string): used both to interpret ``path=`` kwarg when it is a string,
                and to generate ``str_path`` as the returned key.

        Returns:
            iterator: iterator over ``(path, obj)`` pairs of all items and
            sections contained in this section.
        """
        for path, obj in self._get_path_iterator(recursive=recursive, path=path, separator=separator):
            if key is None:
                yield obj
            elif key == 'path':
                yield path, obj
            elif key == 'name' or key == 'alias':
                if obj.is_section:
                    yield obj.alias, obj
                else:
                    yield obj.name, obj
            elif key == 'str_path':
                yield separator.join(path), obj
            else:
                raise ValueError('Invalid key {!r}'.format(key))
