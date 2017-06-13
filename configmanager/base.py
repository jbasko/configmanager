from .utils import not_set


class BaseItem(object):
    is_item = True
    is_section = False
    is_config = False


def is_config_item(obj):
    return isinstance(obj, BaseItem)


class BaseSection(object):
    """
    A base class to allow detection of section classes and instances.
    No other functionality to be added here.
    """

    is_item = False
    is_section = True
    is_config = False


def is_config_section(obj):
    return isinstance(obj, BaseSection)


class ItemAttribute(object):
    """
    Class used in :class:`.Item` class to declare attributes of config items.
    """

    def __init__(self, name, default=not_set, value=not_set):
        self.name = name
        self.default = default
        self.value = value
        self.attr_name = '_{}'.format(self.name)

    def __set__(self, instance, value):
        setattr(instance, self.attr_name, value)

    def __get__(self, instance, owner):
        return getattr(instance, self.attr_name, self.default)
