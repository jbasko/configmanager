import collections
import copy

import six

from .configparser_imports import ConfigParser, DuplicateSectionError


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


def resolve_config_path(*args):
    if len(args) == 0:
        raise ValueError('Expected at least 1 config path segment, got none')

    path = []
    for arg in args:
        if not isinstance(arg, six.string_types):
            raise TypeError('Config path segments should be strings, got a {}'.format(type(arg)))
        path.extend(arg.split('.'))

    if len(path) == 1:
        path = [Config.DEFAULT_SECTION, path[0]]

    return path


def parse_bool_str(bool_str):
    return str(bool_str).lower().strip() in ('yes', 'y', 'yeah', 't', 'true', '1', 'yup')


class Config(object):
    """
    Represents a single configurable thing which has a name (a concatenation of its section and option),
    a type, a default value, a value, etc.
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

    #: Set to ``True`` if the config is managed by :class:`ConfigManager`
    #: from which it was retrieved.
    exists = Descriptor('exists', default=None)

    # Internally, hold on to the raw string value that was used to set value, so that
    # when we persist the value, we use the same notation
    raw_str_value = Descriptor('raw_str_value')

    prompt = Descriptor('prompt')
    labels = Descriptor('labels')
    choices = Descriptor('choices')

    def __init__(self, *path, **kwargs):

        #: a ``list`` of config's path segments.
        self.path = resolve_config_path(*path)

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
        return self.path[1]

    @property
    def name(self):
        """
        A string, :attr:`.path` joined by dots.
        """
        return '.'.join(self.path)

    @property
    def value(self):
        """
        Value or default value (if no value set) of the :class:`.Config` instance. 
        """
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
            self.raw_str_value = value

    @property
    def has_value(self):
        """
        Is ``True`` if the :class:`.Config` has a value set.
        """
        return self._value is not not_set

    @property
    def has_default(self):
        """
        Is ``True`` if the :class:`.Config` has the default value set.
        """
        return self.default is not not_set

    def __str__(self):
        if self.raw_str_value is not not_set:
            return self.raw_str_value
        return str(self.value)

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

    def __repr__(self):
        if self.has_value:
            value = str(self.value)
        elif self.default is not not_set:
            value = str(self.default)
        else:
            value = repr(self.default)

        return '<{} {}.{} {}>'.format(self.__class__.__name__, self.section, self.option, value)

    def _parse_str_value(self, str_value):
        if str_value is None or str_value is not_set:
            return str_value
        elif self.type is bool:
            return parse_bool_str(str_value)
        else:
            return self.type(str_value)


class ConfigSection(collections.OrderedDict):
    """
    Represents a collection of :class:`.Config` instances that belong to the same section.
    """
    def __getattr__(self, item):
        if item in self:
            return self[item]
        raise AttributeError(item)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            return super(ConfigSection, self).__setattr__(key, value)
        elif key in self:
            self[key].value = value
        else:
            raise AttributeError(key)


class ConfigManager(object):
    """
    
    A collection and manager of instances of :class:`.Config`.
    
    .. note::
        :class:`.ConfigManager` is not compatible with ``ConfigParser``.
        If you want to use its features in your legacy code which uses ``ConfigParser`` without changing 
        too much of your code, use :class:`TransitionConfigManager` instead.
    
    """

    def __init__(self, *configs):
        """
        
        :param configs: 
        """
        self._sections = collections.OrderedDict()
        self._configs = collections.OrderedDict()
        for config in configs:
            self.add(config)

    def __getattr__(self, item):
        if item in self._sections:
            return self._sections[item]
        raise AttributeError(item)

    def add(self, config):
        """
        Add a new config to manage.
        
        :param config: instance of :class:`.Config`
        """
        if config.name in self._configs:
            raise ValueError('Config {} already present'.format(config.name))

        config = copy.deepcopy(config)
        config.exists = True
        self._configs[config.name] = config

        if config.section not in self._sections:
            self._add_section(config.section)

        current = self._sections[config.section]
        for i, p in enumerate(config.path[1:]):
            is_section = i < len(config.path) - 2
            if is_section:
                if p in current:
                    if not isinstance(current[p], ConfigSection):
                        raise ValueError('Invalid config path {!r}'.format(config.path))
                else:
                    current[p] = ConfigSection()
                current = current[p]
            else:
                current[p] = config

        # self._sections[config.section][config.option] = self._configs[config.name]

    def _add_section(self, section):
        """
        This is not part of the public interface because in configmanager world
        section is an internal implementation detail.
        """
        if section in self._sections:
            raise DuplicateSectionError(section)
        self._sections[section] = ConfigSection()

    def get(self, *path):
        """
        Returns an instance of :class:`.Config` identified by the ``path``.
        
        :param path:
        :return: :class:`.Config`
        """

        path = resolve_config_path(*path)
        section_path = path[:-1]

        current = self
        for p in section_path:
            if isinstance(current, Config):
                raise ValueError('Invalid path {!r}, {!r} is not a section'.format(path, p))
            if p not in current:
                return Config(*path, exists=False)
            else:
                current = current[p]

        if isinstance(current, Config):
            raise ValueError('Invalid path {!r}, {!r} is not a section'.format(path, section_path[-1]))
        if path[-1] in current:
            return current[path[-1]]
        else:
            return Config(*path, exists=False)

    def set(self, *path_and_value):
        """
        Sets value of previously added :class:`.Config` identified by ``section.option`` or ``section`` and ``option``.
        The last argument is the value or string value of the config.
        
        :param path_and_value:
        """
        self.get(*path_and_value[:-1]).value = path_and_value[-1]

    def __contains__(self, section):
        return section in self._sections

    def __getitem__(self, section):
        return self._sections[section]

    def has(self, *path):
        """
        Returns ``True`` if the specified config is managed by this :class:`.ConfigManager`. 
        
        :param path:  
        :return: ``bool``
        """
        current = self
        for p in resolve_config_path(*path):
            if isinstance(current, Config):
                return current.path == path
            if p not in current:
                return False
            current = current[p]
        return True

    def load_from_config_parser(self, cp):
        for section in cp.sections():
            if section not in self._sections:
                raise ValueError('Unknown config section {!r}'.format(section))
            for option in cp.options(section):
                self.get(section, option).value = cp.get(section, option)

    def load_into_config_parser(self, cp):
        for section in self._sections.keys():
            if not cp.has_section(section):
                cp.add_section(section)
            for config in self._sections[section].values():
                if config.has_value:
                    cp.set(section, config.option, str(config))

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
