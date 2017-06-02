from .utils import not_set


class BaseItem(object):
    is_item = True
    is_section = False

    def added_to_section(self, alias, section):
        pass


def is_config_item(obj):
    return isinstance(obj, BaseItem)


class BaseSection(object):
    cm__item_cls = BaseItem

    is_item = False
    is_section = True

    def create_item(self, *args, **kwargs):
        """
        Internal factory method used to create an instance of configuration item.
        Should only be used to extend configmanager's functionality.
        """
        return self.cm__item_cls(*args, **kwargs)

    def add_item(self, alias, item):
        raise NotImplementedError()

    def create_section(self, *args, **kwargs):
        """
        Internal factory method used to create an instance of configuration section.
        Should only be used to extend configmanager's functionality.
        """
        return self.__class__(*args, **kwargs)

    def add_section(self, alias, section):
        raise NotImplementedError()

    def added_to_section(self, alias, section):
        pass


def is_config_instance(obj):
    return isinstance(obj, BaseSection)


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


class ConfigRootAttribute(object):
    """
    A descriptor that provides an attribute for Config which if not set is looked up
    in root section.
    Once root section is reached, if the attribute is not present, and factory method is set,
    it is used to initialise the attribute.
    """

    def __init__(self, name, factory):
        self.name = name
        self.attr_name = '_{}'.format(name)
        self.factory = factory

    def _set_config_attr(self, instance, value):
        # Can't use setattr() as Config.__setattr__ is guarding against this.
        instance.__dict__[self.attr_name] = value

    def __set__(self, instance, value):
        self._set_config_attr(instance, value)

    def __get__(self, instance, owner):
        if not hasattr(instance, self.attr_name):
            if instance.section:
                return getattr(instance.section, self.name)
            else:
                # We are at the root, must use factory if available
                if self.factory:
                    attr_value = self.factory(config=instance)
                    self._set_config_attr(instance, attr_value)
                    return attr_value

        return getattr(instance, self.attr_name)
