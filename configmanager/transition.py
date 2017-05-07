from warnings import warn

from .configparser_imports import NoSectionError

from .base import ConfigItem, ConfigManager, not_set, parse_bool_str


class TransitionConfigManager(ConfigManager):
    """
    Represents a :class:`ConfigManager` that tries to be compatible with ``ConfigParser``.
    
    .. warning::
        Use this only if you have a good test coverage of configuration access or if you only
        use the most basic ``ConfigParser`` functionality.
    
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
        return ConfigItem.DEFAULT_SECTION

    def defaults(self):
        raise NotImplementedError()

    def add_section(self, section):
        """
        A no-op because :class:`ConfigManager` has no real sections.
        """
        pass

    def options(self, section):
        """
        Implementation of ``ConfigParser.options()``.
        """
        matches = []
        for path, config in self._configs.items():
            if section == path[0]:
                matches.append(config.path[1])
        return matches

    def has_option(self, section, option):
        return self.has(section, option)

    def read(self, filenames):
        raise NotImplementedError()

    def get(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        A far from perfect implementation of ``ConfigParser.get()``.
        """
        if not raw:
            warn('{}.get does not support raw=False'.format(self.__class__.__name__))

        config = self.get_item(section, option)

        if vars and option in vars:
            return vars[option]

        if not config.exists and self.has(self.default_section, option):
            config = self.get_item(self.default_section, option)

        if not config.exists and fallback is not not_set:
            return fallback

        return config.value

    def getint(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        .. deprecated:: 0
           Instead, in :class:`.ConfigItem` use ``type=int``.
        
        Implementation of ``ConfigParser.getint()``. 
        """
        return int(self.get_item(section, option, raw=raw, vars=vars, fallback=fallback).value)

    def getfloat(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        .. deprecated:: 0
           Instead, in :class:`.ConfigItem` use ``type=float``.

        Implementation of ``ConfigParser.getfloat()``. 
        """
        return float(self.get_item(section, option, raw=raw, vars=vars, fallback=fallback).value)

    def getboolean(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        .. deprecated:: 0
           Instead, in :class:`.ConfigItem` use ``type=bool``.

        Implementation of ``ConfigParser.getboolean()``. 
        """
        return parse_bool_str(self.get_item(section, option, raw=raw, vars=vars, fallback=fallback).value)

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
            return [(s, self.ConfigPathProxy(self, (s,))) for s in self.sections()]
        elif not self.has_section(section):
            raise NoSectionError(section)
        else:
            return [(config.option, config.value) for config in super(TransitionConfigManager, self).items()]
