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

    def __init__(self, name, default=not_set, value=not_set, allow_dynamic_override=False):
        self.name = name
        self.default = default
        self.value = value
        self.attr_name = '_{}'.format(self.name)

        # If set to True, this becomes an expensive attribute because now when
        # its value is requested we will check for a registered
        # dynamic attribute with the same name and if available use the dynamic value instead of set value.
        # Attributes that are used in majority of value calculation should avoid this.
        # For example, envvar, which is consulted on every value request, is designed
        # to be a cheap attribute. Users can, however, override envvar_name which is
        # used only if envvar is set to True.
        self.allow_dynamic_override = allow_dynamic_override

    def __set__(self, instance, value):
        setattr(instance, self.attr_name, value)

    def __get__(self, instance, owner):
        if self.allow_dynamic_override:
            if instance.section:
                try:
                    return instance.section.get_item_attribute(instance, self.name)
                except AttributeError:
                    pass
        return getattr(instance, self.attr_name, self.default)
