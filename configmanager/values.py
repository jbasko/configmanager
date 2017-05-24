import collections


class _ConfigValuesProxy(object):
    def __init__(self, source):
        self._cm_values = source

    def __setitem__(self, key, value):
        raise RuntimeError('{} is read-only'.format(self.__class__.__name__))

    def __len__(self):
        return len(self._cm_values)

    def __contains__(self, item):
        return item in self._cm_values

    def __getitem__(self, item):
        return self._cm_proxy(item)

    def __getattr__(self, item):
        if item not in self._cm_values:
            raise AttributeError(item)
        return self[item]

    def __setattr__(self, key, value):
        if key.startswith('_cm_'):
            return super(_ConfigValuesProxy, self).__setattr__(key, value)
        raise RuntimeError('{} is read-only'.format(self.__class__.__name__))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._cm_values == other._cm_values
        return False

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self._cm_values)

    def _cm_proxy(self, item):
        if item in self._cm_values:
            if isinstance(self._cm_values[item], dict):
                return _ConfigValuesProxy(self._cm_values[item])
            else:
                return self._cm_values[item]
        else:
            raise KeyError(item)

    def keys(self):
        return self._cm_values.keys()

    def values(self):
        return [self._cm_proxy(k) for k in self._cm_values.keys()]

    def get(self, *path_and_fallback):
        if len(path_and_fallback) == 1:
            path = path_and_fallback[0]
            if isinstance(self._cm_values[path], dict):
                raise RuntimeError('Attempting to retrieve a section with get')
            return self._cm_values[path]

        elif len(path_and_fallback) > 2:
            return self[path_and_fallback[0]].get(*path_and_fallback[1:])

        path, fallback = path_and_fallback
        if path not in self._cm_values:
            return fallback

        if path in self._cm_values:
            return self[path].get(fallback)

        raise KeyError(path)


class ConfigValues(_ConfigValuesProxy):
    """
    Represents a tree of configuration **values**.
    
    - is a **read-only**, **ordered** dictionary with few extras
    - does NOT contain any meta information about the configuration items which provide these values.
    - does NOT include values for items with no values (or defaults)
    - Provides ``ConfigParser``-like ``get(section1, section2, name, fallback=)`` method
    - user will not see any ``<NotSet>`` values or `configmanager`-specific exceptions raised;
      instead missing values will be just excluded and accessing values of non-existent sections or items
      will raise ``AttributeError`` or ``KeyError`` if no fallback is provided with the ``get`` access.
    - attribute-like access to any section and item: ``config.<section1>.<section2>``, 
      ``config.<section1>.<section2>.item``.
    - sections accessed via attributes or via ``config_values[section1][section2]`` notation 
      are essentially dictionaries (so can be passed as kwargs to functions) with attribute-like access 
      to contents, but not much more functionality.
    
    Notes:
        ``dict(**config.section)`` won't work if section contains nested sections.
    
    """

    def __init__(self, source):
        if not isinstance(source, collections.OrderedDict):
            source = collections.OrderedDict(source)
        super(ConfigValues, self).__init__(source)
