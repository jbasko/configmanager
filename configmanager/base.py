import collections
import copy

import six

from .configparser_imports import ConfigParser


class _NotSet(object):
    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __str__(self):
        return ''

    def __repr__(self):
        return '<NotSet>'

    def __deepcopy__(self, memodict):
        return self

    def __copy__(self):
        return self


not_set = _NotSet()


def resolve_config_path(*path):
    for p in path:
        if not isinstance(p, six.string_types):
            raise TypeError('Config path segments should be strings, got a {}: {}'.format(type(p), p))
        if not p:
            raise ValueError('Config path segments should be non-empty strings, got an empty one')

    if len(path) == 0:
        raise ValueError('Config empty must not be empty')

    return tuple(path)


def old_resolve_config_path(*path):
    if len(path) == 0:
        raise ValueError('Expected at least 1 config path segment, got none')

    resolution = []
    for arg in path:
        if isinstance(arg, (list, tuple)):
            resolution.extend(resolve_config_path(*arg))
            continue
        if not isinstance(arg, six.string_types):
            raise TypeError('ConfigItem path segments should be strings, got a {}'.format(type(arg)))
        resolution.extend(arg.split('.'))

    if len(resolution) == 1:
        resolution = [ConfigItem.DEFAULT_SECTION, resolution[0]]

    return tuple(resolution)


def resolve_config_prefix(*prefix):
    if len(prefix) == 0:
        return tuple()

    if len(prefix) == 1 and '.' not in prefix[0]:
        return tuple(prefix)

    return resolve_config_path(*prefix)


def parse_bool_str(bool_str):
    return str(bool_str).lower().strip() in ('yes', 'y', 'yeah', 't', 'true', '1', 'yup')


class ConfigItem(object):
    """
    Represents a single configurable thing which has a name (a path), a type, a default value, a value,
    knows whether it exists or just pretends to, and other things.
    """

    DEFAULT_SECTION = 'DEFAULT'

    class Descriptor(object):
        def __init__(self, name, default=not_set, value=not_set):
            self.name = name
            self.default = default
            self.value = value
            self.attr_name = '_{}'.format(self.name)

        def __set__(self, instance, value):
            setattr(instance, self.attr_name, value)

        def __get__(self, instance, owner):
            return getattr(instance, self.attr_name, self.default)

    #: Default value.
    default = Descriptor('default')

    #: Type, defaults to ``str``. Type can be any callable that converts a string to an instance of
    #: the expected type of the config value.
    type = Descriptor('type', default=str)

    #: Set to ``False`` if the instance was created by :class:`ConfigManager` which
    #: did not recognise it.
    exists = Descriptor('exists', default=True)

    # Internally, hold on to the raw string value that was used to set value, so that
    # when we persist the value, we use the same notation
    raw_str_value = Descriptor('raw_str_value')

    prompt = Descriptor('prompt')
    labels = Descriptor('labels')
    choices = Descriptor('choices')

    def __init__(self, *path, **kwargs):
        #: a ``tuple`` of config's path segments.
        self.path = None

        resolved = resolve_config_path(*path)
        if len(resolved) == 1:
            self.path = tuple([self.DEFAULT_SECTION]) + resolved
        else:
            self.path = resolved

        self._value = not_set
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def section(self):
        """
        The first segment of :attr:`.path`.
        """
        return self.path[0]

    @property
    def option(self):
        """
        The second segment of :attr:`.path`.
        """
        return self.path[-1]

    @property
    def name(self):
        """
        A string, :attr:`.path` joined by dots.
        """
        return '.'.join(self.path)

    @property
    def value(self):
        """
        Value or default value (if no value set) of the :class:`.ConfigItem` instance. 
        """
        if self.exists is False:
            raise RuntimeError('Cannot get value of non-existent config {}'.format(self.name))
        if self._value is not not_set:
            return self._value
        if self.default is not not_set:
            return self.default
        raise RuntimeError('{} has no value or default value set'.format(self.name))

    @value.setter
    def value(self, value):
        if self.exists is False:
            raise RuntimeError('Cannot set non-existent config {}'.format(self.name))
        self._value = self._parse_str_value(value)
        if self.type is not str:
            if isinstance(value, six.string_types):
                self.raw_str_value = value
            else:
                self.raw_str_value = not_set

    @property
    def has_value(self):
        """
        Is ``True`` if the :class:`.ConfigItem` has a value set.
        """
        return self._value is not not_set

    @property
    def has_default(self):
        """
        Is ``True`` if the :class:`.ConfigItem` has the default value set.
        """
        return self.default is not not_set

    def __str__(self):
        if self.raw_str_value is not not_set:
            return self.raw_str_value
        if self.has_value or self.has_default:
            return str(self.value)
        else:
            return repr(self)

    def __eq__(self, other):
        return self.value == other

    def __nonzero__(self):
        return bool(self.value)

    def __bool__(self):
        return bool(self.value)

    def reset(self):
        """
        Unsets :attr:`value`. 
        """
        self._value = not_set
        self.raw_str_value = not_set

    def __repr__(self):
        if not self.exists:
            value = '<NonExistent>'
        elif self.has_value:
            value = str(self.value)
        elif self.default is not not_set:
            value = str(self.default)
        else:
            value = repr(self.default)

        return '<{} {} {}>'.format(self.__class__.__name__, self.name, value)

    def _parse_str_value(self, str_value):
        if str_value is None or str_value is not_set:
            return str_value
        elif self.type is bool:
            return parse_bool_str(str_value)
        else:
            return self.type(str_value)


class ConfigManager(object):
    """
    
    A collection and manager of instances of :class:`.ConfigItem`.
    
    .. note::
        :class:`.ConfigManager` is not compatible with ``ConfigParser``.
        If you want to use its features in your legacy code which uses ``ConfigParser`` without changing 
        too much of your code, use :class:`TransitionConfigManager` instead.
    
    """

    class ConfigPathProxy(object):
        def __init__(self, config_manager, path):
            assert isinstance(path, tuple)
            self._config_manager_ = config_manager
            self._path_ = path

        def __repr__(self):
            return '<{} {}>'.format(self.__class__.__name__, '.'.join(self._path_))

        @property
        def exists(self):
            return self._config_manager_.has(self._path_)

        def __setattr__(self, key, value):
            if key.startswith('_'):
                return super(ConfigManager.ConfigPathProxy, self).__setattr__(key, value)

            full_path = self._path_ + (key,)
            if self._config_manager_.has(*full_path):
                args = full_path + (value,)
                self._config_manager_.set(*args)
            else:
                raise AttributeError(key)

        def __getattr__(self, path):
            full_path = self._path_ + (path,)
            if self._config_manager_.has(*full_path):
                return self._config_manager_.get(*full_path)
            else:
                return self.__class__(self._config_manager_, full_path)

    def __init__(self, *configs):
        """
        :param configs:  a ``list`` of :class:`.ConfigItem` instances representing items of configuration
                         that this manager accepts.
        """
        self._configs = collections.OrderedDict()
        self._prefixes = collections.OrderedDict()  # Ordered set basically

        for config in configs:
            self.add(config)

    def __getattr__(self, path_segment):
        if (path_segment,) in self._prefixes:
            return self.ConfigPathProxy(self, (path_segment,))
        else:
            return self.get(path_segment)

    def add(self, config):
        """Register a new config to manage.
        
        Args:
            config (ConfigItem): item to add
        
        Examples:
            >>> cm = ConfigManager()
            >>> cm.add(ConfigItem('some.path', default='/tmp/something.txt'))
            >>> cm.some.path
            '/tmp/something.txt'
        
        .. note::
            :class:`.ConfigItem` instances are deep-copied when they are registered with the manager.
        """
        if config.path in self._configs:
            raise ValueError('ConfigItem {} already present'.format(config.name))

        config = copy.deepcopy(config)
        config.exists = True
        self._configs[config.path] = config

        prefix = []
        for p in config.path[:-1]:
            prefix.append(p)
            temp_prefix = tuple(prefix)
            if temp_prefix not in self._prefixes:
                self._prefixes[temp_prefix] = []

    def get(self, *path):
        """Get a config item by path.
        
        By design, there is no way to supply a fallback value. The idea is that a fallback
        value can be set as :attr:`ConfigItem.default`.
            
        :attr:`ConfigItem.value` returns the default value (fallback value) if actual value
        is not set.
        
        Args:
            *path:
        
        Returns:
            ConfigItem: an existing or newly created :class:`.ConfigItem` matching the ``path``.
            
            If this manager does not contain an item with ``path``, the returned item's ``exists``
            attribute will be set to ``False`` and accessing its value will raise ``RuntimeError``.
        
        Examples:
            >>> cm = ConfigManager(ConfigItem('very', 'real', default=0.0, type=float))
            >>> cm.get('very', 'real')
            <ConfigItem very.real 0.0>
            
            >>> cm.get('quite', 'surreal')
            <ConfigItem quite.surreal <NonExistent>>
            >>> cm.get('quite', 'surreal').exists
            False
        
        Note:
            For constant paths, you can use attribute access:
        
            >>> cm.very.real
            <ConfigItem very.real 0.0>
            
            >>> cm.quite.surreal
            <ConfigItem quite.surreal <NonExistent>>
        
        """
        path = resolve_config_path(*path)

        if path in self._configs:
            return self._configs[path]
        else:
            return ConfigItem(*path, exists=False)

    def set(self, *path_and_value):
        """
        Sets ``value`` of previously added :class:`.ConfigItem` identified by ``path``.
        
        :param path_and_value:
        """
        self.get(*path_and_value[:-1]).value = path_and_value[-1]

    def has(self, *path):
        """
        Returns ``True`` if the specified config is managed by this :class:`.ConfigManager`. 

        :param path:  
        :return: ``bool``
        """
        path = resolve_config_path(*path)
        return path in self._configs

    def items(self, *prefix):
        """
        Returns a ``list`` of :class:`.ConfigItem` instances managed by this manager.
        If ``prefix`` is specified, only items with matching path prefix are included.
        """
        prefix = resolve_config_prefix(*prefix)
        if not prefix:
            return list(self._configs.values())
        else:
            return [c for c in self._configs.values() if c.path[:len(prefix)] == prefix[:]]

    def read_file(self, fileobj):
        """
        Read configuration from a file descriptor like in standard library's ``ConfigParser.read_file``
        (``ConfigParser.readfp`` in Python 2).
        """
        cp = ConfigParser()
        cp.read_file(fileobj)
        self.load_from_config_parser(cp)

    def write(self, fileobj):
        """
        Write configuration to a file descriptor like in standard library's ``ConfigParser.write``.
        """
        cp = ConfigParser()
        self.load_into_config_parser(cp)
        cp.write(fileobj)

    def sections(self):
        """
        Returns a list of all sections.
        """
        return list(prefix[0] for prefix in self._prefixes.keys() if len(prefix) == 1)

    def has_section(self, section):
        """
        Returns ``True`` if section called ``section`` exists.
        """
        return tuple([section]) in self._prefixes

    def reset(self):
        """
        Resets values of config items.
        """
        for config in self._configs.values():
            config.reset()

    def load_from_config_parser(self, cp):
        """
        Updates config items from data in `ConfigParser`
        
        Args:
            cp (ConfigParser):

        Returns:

        """
        for section in cp.sections():
            for option in cp.options(section):
                self.get(section, option).value = cp.get(section, option)

    def load_into_config_parser(self, cp):
        for config in self._configs.values():
            if len(config.path) > 2:
                raise NotImplementedError('{} with more than 2 path segments cannot be loaded into {}'.format(
                    config.__class__.__name__, self.__class__.__name__
                ))
            if not config.has_value:
                continue
            if not cp.has_section(config.section):
                cp.add_section(config.section)
            cp.set(config.section, config.option, str(config))
