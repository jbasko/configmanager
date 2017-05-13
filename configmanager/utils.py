import six


class _NotSet(object):
    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __str__(self):
        return ''

    def __repr__(self):
        return '<NotSet>'

    def __deepcopy__(self, memodict):
        return self

    def __copy__(self):
        return self


not_set = _NotSet()


def resolve_config_path(*path):
    for p in path:
        if not isinstance(p, six.string_types):
            raise TypeError('Config path segments should be strings, got a {}: {}'.format(type(p), p))
        if not p:
            raise ValueError('Config path segments should be non-empty strings, got an empty one')

    if len(path) == 0:
        raise ValueError('Config path must not be empty')

    return tuple(path)


def resolve_config_prefix(*prefix):
    if len(prefix) == 0:
        return tuple()

    return resolve_config_path(*prefix)


def parse_bool_str(bool_str):
    return str(bool_str).lower().strip() in ('yes', 'y', 'yeah', 't', 'true', '1', 'yup', 'on')
