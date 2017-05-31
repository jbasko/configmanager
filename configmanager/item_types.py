import six

from configmanager.utils import not_set


class ItemType(object):
    # Do not declare __init__ here -- this is so that you can have concrete types extend other classes
    # too.

    aliases = ()
    builtin_types = ()

    def serialize(self, instance, **kwargs):
        return instance

    def deserialize(self, payload, **kwargs):
        if self.builtin_types:
            return self.builtin_types[0](payload)
        else:
            return payload

    def includes(self, obj):
        """
        Returns:
            ``True`` if ``obj`` belongs to this type.
        """
        if self.builtin_types:
            return isinstance(obj, self.builtin_types)

    def accepts(self, obj):
        """
        Returns:
            ``True`` if ``obj`` can potentially be deserialized to an instance that belongs to this type.
        """
        return self.includes(obj)

    def __call__(self, *args, **kwargs):
        return self.deserialize(*args, **kwargs)


class _NotSetType(ItemType):
    def includes(self, obj):
        return obj is None or obj is not_set


class _StrType(ItemType):
    aliases = ('str', 'string')

    def includes(self, obj):
        return isinstance(obj, six.string_types)


class _IntType(ItemType):
    aliases = ('int', 'integer')
    builtin_types = int,

    def accepts(self, obj):
        return self.includes(obj) or isinstance(obj, six.string_types)


class _BoolType(ItemType):
    aliases = ('bool', 'boolean')
    builtin_types = bool,

    truthy_values = ('yes', 'true', 'y', 't', 'on', '1')
    falsey_values = ('no', 'false', 'n', 'f', 'off', '0')

    def accepts(self, obj):
        if isinstance(obj, bool):
            return True

        if isinstance(obj, six.string_types):
            str = obj.lower()
            return str in self.truthy_values or str in self.falsey_values

        if isinstance(obj, six.integer_types) and obj == 1 or obj == 0:
            return True

        return False

    def deserialize(self, payload, **kwargs):
        if isinstance(payload, bool):
            return payload

        elif isinstance(payload, six.string_types):
            return payload.lower() in self.truthy_values

        elif isinstance(payload, six.integer_types):
            if payload == 1:
                return True
            elif payload == 0:
                return False

        raise ValueError(payload)


class _FloatType(ItemType):
    aliases = ('float', 'double')
    builtin_types = float,


class _DictType(ItemType):
    aliases = ('dict', 'dictionary')
    builtin_types = dict,

    def serialize(self, instance, **kwargs):
        s = {'@type': 'dict'}
        s.update(instance)
        return s

    def accepts(self, obj):
        return self.includes(obj) or (
            hasattr(obj, '__iter__') and hasattr(obj, '__getitem__') and hasattr(obj, '__len__')
        )


class _ListType(ItemType):
    aliases = ('list',)
    builtin_types = list, tuple


class _Types(object):
    not_set = _NotSetType()
    str = _StrType()
    int = _IntType()
    bool = _BoolType()
    float = _FloatType()
    dict = _DictType()
    list = _ListType()

    def __init__(self):
        self._includes_order = [
            self.not_set,
            self.bool,
            self.int,
            self.float,
            self.dict,
            self.list,
            self.str,
        ]

    def guess(self, obj):
        for type_ in self._includes_order:
            if type_.includes(obj):
                return type_

        raise ValueError(obj)


Types = _Types()
