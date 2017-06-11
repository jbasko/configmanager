import os.path


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


_file_ext_to_adapter_name = {
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.ini': 'configparser',
    '.toml': 'toml',  # not really supported yet
    '.xml': 'xml',  # not really supported yet
}


def _get_persistence_adapter_for(filename):
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in _file_ext_to_adapter_name:
        raise ValueError('Unrecognised config file extension for file {!r}'.format(filename))
    return _file_ext_to_adapter_name[ext]
