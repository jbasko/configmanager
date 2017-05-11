class UnknownConfigItem(Exception):
    """
    Exception which is raised when requesting an unknown config item or
    when accessing value of ConfigItem marked as non-existent.
    """


class ConfigValueMissing(Exception):
    """
    Exception which is raised when requesting a value of config item that
    has no value, or default value, or any other fallback.
    """


class UnsupportedOperation(Exception):
    """
    Raised when accessing objects incorrectly, most often when assigning
    values to config items, sections or proxies of such illegally.
    """
