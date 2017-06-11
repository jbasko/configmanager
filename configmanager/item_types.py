import six

from builtins import str as text

from .utils import not_set


class _ItemType(object):
    aliases = ()
    builtin_types = ()

    def serialize(self, instance, **kwargs):
        return instance

    def deserialize(self, payload, **kwargs):
        if payload is None or payload is not_set:
            return payload
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

    def set_item_value(self, item, raw_value):
        value = self.deserialize(raw_value)
        if isinstance(raw_value, six.string_types):
            item._raw_str_value = raw_value
        else:
            item._raw_str_value = not_set
        item._value = value

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.aliases)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class _NotSetType(_ItemType):
    def includes(self, obj):
        return obj is None or obj is not_set


class _StrType(_ItemType):
    aliases = ('str', 'string', 'unicode')
    builtin_types = text,

    def includes(self, obj):
        return isinstance(obj, six.string_types)


class _IntType(_ItemType):
    aliases = ('int', 'integer')
    builtin_types = int,

    def accepts(self, obj):
        return self.includes(obj) or isinstance(obj, six.string_types)


class _BoolType(_ItemType):
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


class _FloatType(_ItemType):
    aliases = ('float', 'double')
    builtin_types = float,


class _DictType(_ItemType):
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


class _ListType(_ItemType):
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

    all_types = (
        not_set,
        str,
        int,
        bool,
        float,
        dict,
        list,
    )

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

        for t in self._includes_order:
            if t.includes(obj):
                return t

        raise ValueError(obj)

    def translate(self, type_):
        """
        Given a built-in, an otherwise known type, or a name of known type, return its corresponding wrapper type::

            >>> Types.translate(int)
            <_IntType ('int', 'integer')>

            >>> Types.translate('string')
            <_StrType ('str', 'string', 'unicode')>

        """
        if isinstance(type_, six.string_types):
            for t in self.all_types:
                if type_ in t.aliases:
                    return t
            raise ValueError('Failed to recognise type by name {!r}'.format(type_))

        for t in self.all_types:
            if type_ in t.builtin_types:
                return t

        return type_


Types = _Types()
