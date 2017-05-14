from configmanager.utils import not_set


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