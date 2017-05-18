class ConfigValueMissing(Exception):
    """
    Exception raised when requesting a value of config item with required=True
    that has no value, or default value.
    """
