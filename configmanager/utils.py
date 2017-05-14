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


def parse_bool_str(bool_str):
    return str(bool_str).lower().strip() in ('yes', 'y', 'yeah', 't', 'true', '1', 'yup', 'on')
