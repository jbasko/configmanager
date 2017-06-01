class _NotSet(object):
    instance = None

    def __init__(self):
        if self.__class__.instance is not None:
            raise RuntimeError('An instance of {} already initialised'.format(self.__class__.__name__))
        self.__class__.instance = self

    def __eq__(self, other):
        return self is other

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
