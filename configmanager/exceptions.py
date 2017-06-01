class ConfigError(Exception):
    pass


class ItemNotFound(ConfigError):
    pass


class RequiredValueMissing(ConfigError):
    pass

