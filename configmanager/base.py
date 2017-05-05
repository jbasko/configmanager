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
            section = Configurable.DEFAULT_SECTION
            option = args[0]
    else:
        raise ValueError('Expected 1 or 2 args, got {}'.format(len(args)))

    if not isinstance(section, str):
        raise TypeError('{}.section must be a string'.format(Configurable.__name__))

    if not isinstance(option, str):
        raise TypeError('{}.option must be a string'.format(Configurable.__name__))

    return section, option


class Configurable(object):
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

    default = Descriptor('default')
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
        return '{}.{}'.format(self.section, self.option)

    @property
    def value(self):
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
        return self._value is not not_set

    @property
    def has_default(self):
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
        if config.name in self._configs:
            raise ValueError('Config {} already present'.format(config.name))

        config = copy.deepcopy(config)
        self._configs[config.name] = config

        if config.section not in self._sections:
            self._sections[config.section] = ConfigSection()

        self._sections[config.section][config.option] = self._configs[config.name]

    def get_config(self, *args):
        section, option = resolve_config_name(*args)
        if section not in self._sections:
            raise ValueError('Section {!r} not found'.format(section))
        if option not in self._sections[section]:
            raise ValueError('Option {!r} not found in section {!r}'.format(option, section))
        return self._sections[section][option]

    def set_config(self, *args):
        self.get_config(*args[:-1]).value = args[-1]

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
        cp = ConfigParser()
        cp.read_file(fileobj)
        self.load_from_config_parser(cp)

    def write(self, fileobj):
        cp = ConfigParser()
        self.load_into_config_parser(cp)
        cp.write(fileobj)
