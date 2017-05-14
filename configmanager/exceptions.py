class _UnknownConfigItem(Exception):
    """
    Exception which is raised when requesting an unknown config item or
    when accessing value of ConfigItem marked as non-existent.
    """


class _ConfigValueMissing(Exception):
    """
    Exception raised when requesting a value of config item with required=True
    that has no value, or default value.
    """


class _UnsupportedOperation(Exception):
    """
    Raised when accessing objects incorrectly, most often when assigning
    values to config items, sections or proxies of such illegally.
    """
