from warnings import warn

from .configparser_imports import NoSectionError

from .base import Config, ConfigManager, not_set


class TransitionConfigManager(ConfigManager):
    """
    Represents a :class:`ConfigManager` that tries to be compatible with ``ConfigParser``.
    
    Use this only if you have a good test coverage of configuration access or if you only
    use the most basic ``ConfigParser`` functionality.
    
    Originally, I thought it might be a good idea to implement ConfigParser interface,
    but it turns out that it is very file- and section- specific and differs between Python 2 and 3.
    """

    @property
    def default_section(self):
        return Config.DEFAULT_SECTION

    def get(self, section, option, raw=True, vars=None, fallback=not_set):
        """
        Implementation of ``ConfigParser.get()``.
        """
        if not raw:
            warn('{}.get does not support raw=False'.format(self.__class__.__name__))

        config = super(TransitionConfigManager, self).get_config(section, option)

        if vars and option in vars:
            return vars[option]

        if not config.exists and self.has_config(self.default_section, option):
            config = super(TransitionConfigManager, self).get_config(self.default_section, option)

        if not config.exists and fallback is not not_set:
            return fallback

        return config.value

    def set(self, section, option, value):
        """
        Implementation of ``ConfigParser.set()``.
        """
        if not self.has_section(section):
            raise NoSectionError(section)
        super(TransitionConfigManager, self).set_config(section, option, value)

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

    def sections(self):
        """
        Implementation of ``ConfigParser.sections()``.
        """
        return [k for k in self._sections.keys() if k != self.default_section]

    def options(self, section):
        """
        Implementation of ``ConfigParser.options()``.
        """
        if section not in self._sections:
            raise NoSectionError(section)
        return list(self._sections[section].keys())

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
