from .items import Item


class ConfigManagerSettings(object):
    def __init__(self, **settings_and_factories):

        # Use _settings when you want to initialise defaults for all Config instances.
        # Use _factories when you want to lazy-load defaults only when requested.
        self._settings = {
            'item_cls': Item,
        }
        self._factories = {
            'configparser_factory': self.create_configparser_factory,
            'section_cls': self.create_section_cls,
        }

        for k, v in settings_and_factories.items():
            if k.startswith('create_'):
                self._factories[k[7:]] = v
            else:
                self._settings[k] = v

    def __repr__(self):
        return '<ConfigManagerSettings {!r}>'.format(self._settings)

    def __str__(self):
        return '<ConfigManagerSettings {!r}>'.format(self._settings)

    def __getattr__(self, item):
        if item in self._settings:
            return self._settings[item]

        elif item in self._factories:
            self._settings[item] = self._factories[item]()
            return self._settings[item]

        raise AttributeError(item)

    def create_configparser_factory(self):
        import configparser
        return configparser.ConfigParser

    def create_section_cls(self):
        from .sections import Section
        return Section
