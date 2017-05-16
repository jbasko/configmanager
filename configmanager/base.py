from configmanager.utils import not_set


class BaseItem(object):
    pass


def is_config_item(obj):
    return isinstance(obj, BaseItem)


class BaseSection(object):
    cm__item_cls = BaseItem

    def cm__create_item(self, *args, **kwargs):
        """
        Returns:
            config_item (BaseItem):
        """
        return self.cm__item_cls(*args, **kwargs)

    def cm__create_section(self, *args, **kwargs):
        """
        Returns:
            config (BaseSection):
        """
        return self.__class__(*args, **kwargs)


def is_config_instance(obj):
    return isinstance(obj, BaseSection)


def is_config_section(obj):
    return isinstance(obj, BaseSection)


class ItemAttribute(object):
    def __init__(self, name, default=not_set, value=not_set):
        self.name = name
        self.default = default
        self.value = value
        self.attr_name = '_{}'.format(self.name)

    def __set__(self, instance, value):
        setattr(instance, self.attr_name, value)

    def __get__(self, instance, owner):
        return getattr(instance, self.attr_name, self.default)
