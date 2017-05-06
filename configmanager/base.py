import collections

import copy

try:
    # Python 2
    from ConfigParser import ConfigParser
    ConfigParser.read_file = ConfigParser.readfp
except ImportError:
    from configparser import ConfigParser


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


def resolve_config_name(*args):
    if len(args) == 2:
        section, option = args
    elif len(args) == 1:
        if '.' in args[0]:
            section, option = args[0].split('.', 1)
        else:
            section = Config.DEFAULT_SECTION
            option = args[0]
    else:
        raise ValueError('Expected 1 or 2 args, got {}'.format(len(args)))

    if not isinstance(section, str):
        raise TypeError('{}.section must be a string'.format(Config.__name__))

    if not isinstance(option, str):
        raise TypeError('{}.option must be a string'.format(Config.__name__))

    return section, option


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

    prompt = Descriptor('prompt')
    labels = Descriptor('labels')
    choices = Descriptor('choices')

    def __init__(self, *args, **kwargs):
        self.section, self.option = resolve_config_name(*args)

        self._value = not_set
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def name(self):
        """
        Dot-joined concatenation of section and option, i.e. `section.option`
        """
        return '{}.{}'.format(self.section, self.option)

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
        self._value = self.type(value)

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
    A collection of :class:`.Config` instances and methods to manage it.
    """

    def __init__(self, *configs):
        self._sections = collections.OrderedDict()
        self._configs = collections.OrderedDict()
        for config in configs:
            self.add_config(config)

    def __getattr__(self, item):
        if item in self._sections:
            return self._sections[item]
        raise AttributeError(item)

    def add_config(self, config):
        """
        Add a new config to manage.
        
        :param config: instance of :class:`.Config`
        """
        if config.name in self._configs:
            raise ValueError('Config {} already present'.format(config.name))

        config = copy.deepcopy(config)
        self._configs[config.name] = config

        if config.section not in self._sections:
            self._sections[config.section] = ConfigSection()

        self._sections[config.section][config.option] = self._configs[config.name]

    def get_config(self, *args):
        """
        Returns an instance of :class:`.Config` identified by ``section.option``, or ``section`` and ``option``.
        
        :param args:  ``("<section_name>.<option_name>")`` or ``("<section_name>", "<option_name>")``
        :return: :class:`.Config`
        """
        section, option = resolve_config_name(*args)
        if section not in self._sections:
            raise ValueError('Section {!r} not found'.format(section))
        if option not in self._sections[section]:
            raise ValueError('Option {!r} not found in section {!r}'.format(option, section))
        return self._sections[section][option]

    def set_config(self, *args):
        """
        Sets value of previously added :class:`.Config` identified by ``section.option`` or ``section`` and ``option``.
        The last argument is the value or string value of the config.
        
        :param args:  ``("<section_name>.<option_name>"`, value)` or ``("<section_name>", "<option_name>", value)``
        """
        self.get_config(*args[:-1]).value = args[-1]

    def has_config(self, *args):
        """
        Returns ``True`` if the specified config is managed by this :class:`.ConfigManager`. 
        
        :param args:  ``("<section_name>.<option_name>")`` or ``("<section_name>", "<option_name>")``  
        :return: ``bool``
        """
        section, option = resolve_config_name(*args)
        return section in self._sections and option in self._sections[section]

    def load_from_config_parser(self, cp):
        for section in cp.sections():
            if section not in self._sections:
                raise ValueError('Unknown config section {!r}'.format(section))
            for option in cp.options(section):
                self.get_config(section, option).value = cp.get(section, option)

    def load_into_config_parser(self, cp):
        for section in self._sections.keys():
            if not cp.has_section(section):
                cp.add_section(section)
            for config in self._sections[section].values():
                if config.has_value:
                    cp.set(section, config.option, config.value)

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
