from warnings import warn

from .configparser_imports import NoSectionError

from .base import Config, ConfigManager, not_set, parse_bool_str


class TransitionConfigManager(ConfigManager):
    """
    Represents a :class:`ConfigManager` that tries to be compatible with ``ConfigParser``.
    
    .. warning::
        Use this only if you have a good test coverage of configuration access or if you only
        use the most basic ``ConfigParser`` functionality.
    
        Originally, I thought it might be a good idea to implement ConfigParser interface,
        but it turns out that it is very file- and section- specific and differs between Python 2 and 3.
    
    When replacing ``ConfigParser``, change code like this:
    
    .. code-block:: python
        
        from ConfigParser import ConfigParser 
        
        config = ConfigParser()
    
    to:
    
    .. code-block:: python
    
        from configmanager import TransitionConfigManager
    
        config = TransitionConfigManager()
    
    """

    @property
    def default_section(self):
        return Config.DEFAULT_SECTION

    def defaults(self):
        raise NotImplementedError()

    def sections(self):
        """
        Implementation of ``ConfigParser.sections()``.
        """
        return [k for k in self._sections.keys() if k != self.default_section]

    def add_section(self, section):
        """
        Implementation of ``ConfigParser.add_section()``.
        """
        return self._add_section(section)

    def has_section(self, section):
        """
        Implementation of ``ConfigParser.has_section()``.
        """
        return section != self.default_section and section in self._sections

    def options(self, section):
        """
        Implementation of ``ConfigParser.options()``.
        """
        if section not in self._sections:
            raise NoSectionError(section)
        return list(self._sections[section].keys())

    def has_option(self, section, option):
        return self.has(section, option)

    def read(self, filenames):
        raise NotImplementedError()

    def get(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        A far from perfect implementation of ``ConfigParser.get()``.
        It does not return a raw value, instead returns an instance of :class:`.Config`.
        """
        if not raw:
            warn('{}.get does not support raw=False'.format(self.__class__.__name__))

        config = super(TransitionConfigManager, self).get(section, option)

        if vars and option in vars:
            return vars[option]

        if not config.exists and self.has(self.default_section, option):
            config = self.get(self.default_section, option)

        if not config.exists and fallback is not not_set:
            return fallback

        return config

    def getint(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        .. deprecated:: 0
           Instead, in :class:`.Config` use ``type=int``.
        
        Implementation of ``ConfigParser.getint()``. 
        """
        return int(self.get(section, option, raw=raw, vars=vars, fallback=fallback).value)

    def getfloat(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        .. deprecated:: 0
           Instead, in :class:`.Config` use ``type=float``.

        Implementation of ``ConfigParser.getfloat()``. 
        """
        return float(self.get(section, option, raw=raw, vars=vars, fallback=fallback).value)

    def getboolean(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        .. deprecated:: 0
           Instead, in :class:`.Config` use ``type=bool``.

        Implementation of ``ConfigParser.getboolean()``. 
        """
        return parse_bool_str(self.get(section, option, raw=raw, vars=vars, fallback=fallback).value)

    def set(self, section, option, value):
        """
        Implementation of ``ConfigParser.set()``.
        """
        if not self.has_section(section):
            raise NoSectionError(section)
        self.get(section, option).value = value

    def items(self, section=not_set, raw=True, vars=None):
        """
        A far from perfect implementation of ``ConfigParser.items()``.
        ``raw=False`` and ``vars`` is not supported.
        """
        if not raw:
            warn('raw=False is not supported by {}'.format(self.__class__.__name__))

        if vars:
            warn('vars keyword argument is not supported by {}'.format(self.__class__.__name__))

        if section is not_set:
            return [(s, self._sections[s]) for s in self._sections.keys()]
        elif not self.has_section(section):
            raise NoSectionError(section)
        else:
            return [(option, self._sections[section][option].value) for option in self._sections.keys()]
