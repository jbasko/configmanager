import collections
import copy
import functools
import keyword

import six
from hookery import HookRegistry

from .schema_parser import parse_config_schema
from .meta import ConfigManagerSettings
from .exceptions import NotFound
from .utils import not_set
from .base import BaseSection, is_config_item, is_config_section


_iter_emitters = {
    'path': lambda k, v, _: (k, v),
    'name': lambda k, v, _: (v.alias, v) if v.is_section else (v.name, v),
    'alias': lambda k, v, _: (v.alias, v) if v.is_section else (v.name, v),
    'str_path': lambda k, v, sep: (sep.join(k), v),
    None: lambda k, v, sep: v,
}


class _SectionHooks(HookRegistry):
    def __init__(self, section):
        super(_SectionHooks, self).__init__(section)
        self.not_found = self.register_event('not_found')
        self.item_added_to_section = self.register_event('item_added_to_section')
        self.section_added_to_section = self.register_event('section_added_to_section')
        self.item_value_changed = self.register_event('item_value_changed')


class Section(BaseSection):
    """
    Represents a section consisting of items (instances of :class:`.Item`) and other sections
    (instances of :class:`.Section`).
    """

    # Core section functionality.
    # Keep as light as possible.

    _default_settings = ConfigManagerSettings(immutable=True)

    def __init__(self, schema=None, section=None):
        #: Actual contents of the section
        self._tree = collections.OrderedDict()

        #: Section to which this section belongs (if any at all)
        self._section = section

        #: Alias of this section with which it was added to its parent section
        self._section_alias = None

        # Hooks registry
        self._hooks = _SectionHooks(self)

        # Listen for hook registration so we can enable per-section hooks only when they
        # are actually used.
        self._hooks.hook_registered(self._hook_registered)

        #: Dynamic item attributes registry
        self.__item_attributes = {}

        if schema is not None:
            self.add_schema(schema)

    def __len__(self):
        return len(self._tree)

    def __nonzero__(self):
        return True

    def __bool__(self):
        return True

    def __iter__(self):
        for name in self._tree.keys():
            yield name

    def __repr__(self):
        return '<{cls} {alias} at {id}>'.format(cls=self.__class__.__name__, alias=self.alias, id=id(self))

    def __contains__(self, key):
        try:
            _ = self._get_by_key(key, handle_not_found=False)
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

        self._set_key(name, value)

    def __getitem__(self, key):
        return self._get_by_key(key)

    def __getattr__(self, name):
        if not isinstance(name, six.string_types):
            raise TypeError('Expected a string, got a {!r}'.format(type(name)))

        if name.startswith('_'):
            raise AttributeError(name)

        return self._get_by_key(name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(Section, self).__setattr__(name, value)
        self._set_key(name, value)

    def _default_key_setter(self, name, subject):
        """
        This method is used only when there is a custom key_setter set.

        Do not override this method.
        """
        if is_config_item(subject):
            self.add_item(name, subject)
        elif is_config_section(subject):
            self.add_section(name, subject)
        else:
            raise TypeError(
                'Section items can only be replaced with items, '
                'got {type}. To set item value use ...{name}.value = <new_value>'.format(
                    type=type(subject),
                    name=name,
                )
            )

    def _set_key(self, key, value):
        """
        This method must NOT be called from outside the Section class.

        Do not override this method.
        """

        if is_config_section(value):
            self.add_section(key, value)
            return

        if key not in self._tree or self.settings.key_setter is None:
            if is_config_item(value):
                self.add_item(key, value)
                return

            raise TypeError(
                'Section sections/items can only be replaced with sections/items, '
                'got {type}. To set value use ..[{name}].value = <new_value>'.format(
                    type=type(value),
                    name=key,
                )
            )

        if self.settings.key_setter is None:
            self._default_key_setter(key, value)
        else:
            self.settings.key_setter(subject=self._tree[key], value=value, default_key_setter=self._default_key_setter)

    def _get_by_key(self, key, handle_not_found=True):
        """
        This method must NOT be called from outside the Section class.

        Do not override this method.
        """
        resolution = self._get_item_or_section(key, handle_not_found=handle_not_found)
        if self.settings.key_getter:
            return self.settings.key_getter(parent=self, subject=resolution)
        else:
            return resolution

    def _get_item_or_section(self, key, handle_not_found=True):
        """
        This method must NOT be called from outside the Section class.

        Do not override this method.

        If handle_not_found is set to False, hooks won't be called.
        This is needed when checking key existence -- the whole
        purpose of key existence checking is to avoid errors (and error handling).
        """
        if isinstance(key, six.string_types):
            if self.settings.str_path_separator in key:
                return self._get_item_or_section(key.split(self.settings.str_path_separator))

            if key.endswith('_') and keyword.iskeyword(key[:-1]):
                key = key[:-1]

            if key in self._tree:
                resolution = self._tree[key]
            else:
                if handle_not_found:
                    result = self.dispatch_event(self.hooks.not_found, name=key, section=self)
                    if result is not None:
                        resolution = result
                    else:
                        raise NotFound(key, section=self)
                else:
                    raise NotFound(key, section=self)

        elif isinstance(key, (tuple, list)) and len(key) > 0:
            if len(key) == 1:
                resolution = self._get_item_or_section(key[0], handle_not_found=handle_not_found)
            else:
                resolution = self._get_item_or_section(
                    key[0], handle_not_found=handle_not_found
                )._get_item_or_section(key[1:], handle_not_found=handle_not_found)
        else:
            raise TypeError('Expected either a string or a tuple as key, got {!r}'.format(key))

        return resolution

    def get_item(self, *key):
        """
        The recommended way of retrieving an item by key when extending configmanager's behaviour.
        Attribute and dictionary key access is configurable and may not always return items
        (see PlainConfig for example), whereas this method will always return the corresponding
        Item as long as NOT_FOUND hook callbacks don't break this convention.

        Args:
            *key

        Returns:
            item (:class:`.Item`):
        """
        item = self._get_item_or_section(key)
        if not item.is_item:
            raise RuntimeError('{} is a section, not an item'.format(key))
        return item

    def get_section(self, *key):
        """
        The recommended way of retrieving a section by key when extending configmanager's behaviour.
        """
        section = self._get_item_or_section(key)
        if not section.is_section:
            raise RuntimeError('{} is an item, not a section'.format(key))
        return section

    def get_proxy(self, *key):
        """
        Get hold of a reference to an item or section before it has been declared.
        """
        return PathProxy(self, key)

    @property
    def hooks(self):
        """
        Returns:
            _SectionHooks
        """
        return self._hooks

    @property
    def section(self):
        """
        Returns:
            (:class:`.Config`): section to which this section belongs or ``None`` if this
            hasn't been added to any section.
        """
        return self._section

    @property
    def alias(self):
        """
        Returns alias with which this section was added to another or ``None`` if it hasn't been added
        to any.

        Returns:
            (str)
        """
        return self._section_alias

    def add_item(self, alias, item):
        """
        Add a config item to this section.
        """
        if not isinstance(alias, six.string_types):
            raise TypeError('Item name must be a string, got a {!r}'.format(type(alias)))
        item = copy.deepcopy(item)
        if item.name is not_set:
            item.name = alias

        if self.settings.str_path_separator in item.name:
            raise ValueError(
                'Item name must not contain str_path_separator which is configured for this Config -- {!r} -- '
                'but {!r} does.'.format(self.settings.str_path_separator, item)
            )

        self._tree[item.name] = item

        if item.name != alias:
            if self.settings.str_path_separator in alias:
                raise ValueError(
                    'Item alias must not contain str_path_separator which is configured for this Config -- {!r} --'
                    'but {!r} used for {!r} does.'.format(self.settings.str_path_separator, alias, item)
                )
            self._tree[alias] = item

        item._section = self

        self.dispatch_event(self.hooks.item_added_to_section, alias=alias, section=self, subject=item)

    def add_section(self, alias, section):
        """
        Add a sub-section to this section.
        """
        if not isinstance(alias, six.string_types):
            raise TypeError('Section name must be a string, got a {!r}'.format(type(alias)))

        self._tree[alias] = section

        if self.settings.str_path_separator in alias:
            raise ValueError(
                'Section alias must not contain str_path_separator which is configured for this Config -- {!r} -- '
                'but {!r} does.'.format(self.settings.str_path_separator, alias)
            )

        section._section = self
        section._section_alias = alias

        self.dispatch_event(self.hooks.section_added_to_section, alias=alias, section=self, subject=section)

    def _get_str_path_separator(self, override=None):
        if override is None or override is not_set:
            return self.settings.str_path_separator
        return override

    def _parse_path(self, path=None):
        if not path:
            return ()

        if isinstance(path, six.string_types):
            separator = self.settings.str_path_separator
            clean_path = []
            for part in path.split(separator):
                if part.endswith('_') and keyword.iskeyword(part[:-1]):
                    clean_path.append(part[:-1])
                else:
                    clean_path.append(part)
            clean_path = tuple(clean_path)
        else:
            clean_path = path

        # This is to raise NotFound in case path doesn't exist and to have it
        # handled by not_found hook callbacks.
        self._get_by_key(path)

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

        for obj_alias, obj in self._tree.items():
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
                # _tree contains duplicates so that we can have multiple aliases point
                # to the same item. We have to de-duplicate here.
                if obj.name in names_yielded:
                    continue
                names_yielded.add(obj.name)

                yield (obj.name,), obj

    def _get_path_iterator(self, path=None, recursive=False):
        clean_path = self._parse_path(path=path)

        config = self[clean_path] if clean_path else self

        if clean_path:
            yield clean_path, config

        if config.is_section:
            for p, obj in config._get_recursive_iterator(recursive=recursive):
                yield (clean_path + p), obj

    def iter_all(self, recursive=False, path=None, key='path'):
        """
        Args:
            recursive: if ``True``, recurse into sub-sections

            path (tuple or string): optional path to limit iteration over.

            key: ``path`` (default), ``str_path``, ``name``, ``None``, or a function to calculate the key from
                ``(k, v)`` tuple.

        Returns:
            iterator: iterator over ``(path, obj)`` pairs of all items and
            sections contained in this section.
        """
        if isinstance(key, six.string_types) or key is None:
            if key in _iter_emitters:
                emitter = _iter_emitters[key]
            else:
                raise ValueError('Invalid key {!r}'.format(key))
        else:
            emitter = lambda k, v, _, f=key: (f(k, v), v)

        for p, obj in self._get_path_iterator(recursive=recursive, path=path):
            yield emitter(p, obj, self.settings.str_path_separator)

    def iter_items(self, recursive=False, path=None, key='path'):
        """

        See :meth:`.iter_all` for standard iterator argument descriptions.

        Returns:
            iterator: iterator over ``(key, item)`` pairs of all items
                in this section (and sub-sections if ``recursive=True``).

        """
        for x in self.iter_all(recursive=recursive, path=path, key=key):
            if key is None:
                if x.is_item:
                    yield x
            elif x[1].is_item:
                yield x

    def iter_sections(self, recursive=False, path=None, key='path'):
        """
        See :meth:`.iter_all` for standard iterator argument descriptions.

        Returns:
            iterator: iterator over ``(key, section)`` pairs of all sections
                in this section (and sub-sections if ``recursive=True``).

        """
        for x in self.iter_all(recursive=recursive, path=path, key=key):
            if key is None:
                if x.is_section:
                    yield x
            elif x[1].is_section:
                yield x

    def iter_paths(self, recursive=False, path=None, key='path'):
        """

        See :meth:`.iter_all` for standard iterator argument descriptions.

        Returns:
            iterator: iterator over paths of all items and sections
            contained in this section.

        """
        assert key is not None
        for p, _ in self.iter_all(recursive=recursive, path=path, key=key):
            yield p

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

    def dump_values(self, with_defaults=True, dict_cls=dict, flat=False):
        """
        Export values of all items contained in this section to a dictionary.

        Items with no values set (and no defaults set if ``with_defaults=True``) will be excluded.

        Returns:
            dict: A dictionary of key-value pairs, where for sections values are dictionaries
            of their contents.

        """
        values = dict_cls()

        if flat:
            for str_path, item in self.iter_items(recursive=True, key='str_path'):
                if item.has_value:
                    if with_defaults or not item.is_default:
                        values[str_path] = item.value
        else:
            for item_name, item in self._tree.items():
                if is_config_section(item):
                    section_values = item.dump_values(with_defaults=with_defaults, dict_cls=dict_cls)
                    if section_values:
                        values[item_name] = section_values
                else:
                    if item.has_value:
                        if with_defaults or not item.is_default:
                            values[item.name] = item.value
        return values

    def load_values(self, dictionary, as_defaults=False, flat=False):
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
        """
        if flat:
            # Deflatten the dictionary and then pass on to the normal case.
            separator = self.settings.str_path_separator
            flat_dictionary = dictionary
            dictionary = collections.OrderedDict()
            for k, v in flat_dictionary.items():
                k_parts = k.split(separator)
                c = dictionary
                for i, kp in enumerate(k_parts):
                    if i >= len(k_parts) - 1:
                        c[kp] = v
                    else:
                        if kp not in c:
                            c[kp] = collections.OrderedDict()
                        c = c[kp]

        for name, value in dictionary.items():
            if name not in self:
                if as_defaults:
                    if isinstance(value, dict):
                        self[name] = self.create_section()
                        self[name].load_values(value, as_defaults=as_defaults)
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
                self[name].load_values(value, as_defaults=as_defaults)

    def create_item(self, *args, **kwargs):
        """
        Internal factory method used to create an instance of configuration item.

        Should only be used when extending or modifying configmanager's functionality.
        Under normal circumstances you should let configmanager create sections
        and items when parsing configuration schemas.

        Do not override this method. To customise item creation,
        write your own item factory and pass it to Config through
        item_factory= keyword argument.
        """
        return self.settings.item_factory(*args, **kwargs)

    def create_section(self, *args, **kwargs):
        """
        Internal factory method used to create an instance of configuration section.

        Should only be used when extending or modifying configmanager's functionality.
        Under normal circumstances you should let configmanager create sections
        and items when parsing configuration schemas.

        Do not override this method. To customise section creation,
        write your own section factory and pass it to Config through
        section_factory= keyword argument.
        """
        kwargs.setdefault('section', self)
        return self.settings.section_factory(*args, **kwargs)

    @property
    def settings(self):
        """
        The settings that apply to this section.

        By design, sections can't have their own settings, so normally this would
        point to the settings of manager (an instance of :class:`.Config`) to which this section or one of its parent
        sections has been added to.

        For section objects which haven't been added to a manager yet,
        this points to default settings which are the same for all such free-floating sections.
        """
        if self._section:
            return self._section.settings
        else:
            return self._default_settings

    def add_schema(self, schema):
        """
        Add schema to the configuration tree.

        Adding a schema means declaring additional collection of sections and items that are managed
        by this :class:`.Section` (or :class:`.Config`).

        Examples:

            config = Config()
            config.add_schema({'db': {'user': 'root', 'password': 'secret'}})

        """
        parse_config_schema(schema, root=self)

    def get_path(self):
        """
        Calculate section's path in configuration tree.
        Use this sparingly -- path is calculated by going up the configuration tree.
        For a large number of sections, it is more efficient to use iterators that return paths
        as keys.

        Path value is stable only once the configuration tree is completely initialised.
        """

        if not self.alias:
            return ()

        if self.section:
            return self.section.get_path() + (self.alias,)
        else:
            return self.alias,

    def item_attribute(self, f=None, name=None):
        """
        A decorator to register a dynamic item attribute provider.

        By default, uses function name for attribute name. Override that with ``name=``.
        """
        def decorator(func):
            attr_name = name or func.__name__
            if attr_name.startswith('_'):
                raise RuntimeError('Invalid dynamic item attribute name -- should not start with an underscore')
            self.__item_attributes[attr_name] = func
            return func

        if f is None:
            return decorator
        else:
            return decorator(f)

    def get_item_attribute(self, item, name):
        """
        Method called by item when an attribute is not found.
        """
        if name in self.__item_attributes:
            return self.__item_attributes[name](item)
        elif self.section:
            return self.section.get_item_attribute(item, name)
        else:
            raise AttributeError(name)

    def _hook_registered(self):
        if self.settings.hooks_enabled is None:
            self.settings.hooks_enabled = True

    def dispatch_event(self, event_, **kwargs):
        """
        Dispatch section event.

        Notes:
            You MUST NOT call event.trigger() directly because
            it will circumvent the section settings as well
            as ignore the section tree.

            If hooks are disabled somewhere up in the tree, and enabled
            down below, events will still be dispatched down below because
            that's where they originate.
        """
        if self.settings.hooks_enabled:
            result = self.hooks.dispatch_event(event_, **kwargs)
            if result is not None:
                return result

            # Must also dispatch the event in parent section
            if self.section:
                return self.section.dispatch_event(event_, **kwargs)

        elif self.section:
            # Settings only apply to one section, so must still
            # dispatch the event in parent sections recursively.
            self.section.dispatch_event(event_, **kwargs)


class PathProxy(object):
    def __init__(self, config, path):
        self.__path_getter = functools.partial(config._get_item_or_section, path)
        self.__path_target = not_set

    def _get_real_object(self):
        if self.__path_target is not_set:
            self.__path_target = self.__path_getter()
        return self.__path_target

    def __getattr__(self, name):
        return getattr(self._get_real_object(), name)
