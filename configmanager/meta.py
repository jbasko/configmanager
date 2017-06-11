import copy
import os.path

from .items import Item


class ConfigManagerSettings(object):
    def __init__(self, immutable=False, **settings_and_factories):

        #: set to True for default settings which means deep copies are returned as values
        #: and new settings cannot be set.
        self._is_immutable = immutable

        # Some settings are declared as @properties and look
        # into settings or _factories just for overrides.

        # Use settings when you want to initialise defaults for all Config instances.
        # Use _factories when you want to lazy-load defaults only when requested.
        self._settings = {
            'item_factory': Item,
            'app_name': None,
            'hooks_enabled': None,  # None means that when a hook is registered, hooks will be enabled automatically
            'str_path_separator': '.',
            'key_getter': None,
            'key_setter': None,
            'auto_load': False,
            'load_sources': [],
        }
        self._factories = {
            'configparser_factory': self.create_configparser_factory,
            'section_factory': self.create_section_factory,
        }

        for k, v in settings_and_factories.items():
            if k.startswith('create_'):
                self._factories[k[7:]] = v
            else:
                self._settings[k] = v

        if self.app_name:
            self.load_sources.append(self.user_app_config)

    def __repr__(self):
        return '<ConfigManagerSettings {!r}>'.format(self._settings)

    def __str__(self):
        return '<ConfigManagerSettings {!r}>'.format(self._settings)

    def __getattr__(self, item):
        if item not in self._settings and item in self._factories:
            self._settings[item] = self._factories[item]()

        if item in self._settings:
            if self._is_immutable:
                return copy.deepcopy(self._settings[item])
            else:
                return self._settings[item]

        raise AttributeError(item)

    def create_configparser_factory(self):
        import configparser
        return configparser.ConfigParser

    def create_section_factory(self):
        from .sections import Section
        return Section

    @property
    def user_config_root(self):
        if 'user_config_root' in self._settings:
            return self._settings['user_config_root']
        return os.path.expanduser('~/.config')

    @property
    def user_app_config(self):
        if 'user_app_config' in self._settings:
            return self._settings['user_app_config']
        return os.path.join(self.user_config_root, self.app_name, 'config.json')
