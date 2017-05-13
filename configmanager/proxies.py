from .exceptions import UnsupportedOperation


class PathProxy(object):
    def __init__(self, config, path=None):
        self._config_ = config
        self._path_ = tuple(path) if path else ()

    def _prepend_path_(self, *name):
        return self._path_ + tuple(name)

    def _get_config_item_(self, path, raw):
        return raw

    def _set_config_item_(self, path, raw, value):
        raise UnsupportedOperation(path)

    def _get_proxy_(self, path, raw):
        return raw

    def _set_proxy_(self, path, raw, value):
        raise UnsupportedOperation(path)

    def _get_raw_(self, path):
        if path in self._config_._configs:
            return self._config_._configs[path]
        elif path in self._config_._prefixes:
            return self.__class__(self._config_, path)
        else:
            raise AttributeError(path[-1])

    def _get_(self, path):
        raw = self._get_raw_(path)
        if isinstance(raw, self.__class__):
            return self._get_proxy_(path, raw)
        else:
            return self._get_config_item_(path, raw)

    def __getattr__(self, name):
        return self._get_(self._prepend_path_(name))

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return super(PathProxy, self).__setattr__(name, value)

        path = self._prepend_path_(name)

        raw = self._get_raw_(path)
        if isinstance(raw, self.__class__):
            return self._set_proxy_(path, raw, value)
        else:
            return self._set_config_item_(path, raw, value)

    def __iter__(self):
        raise NotImplementedError()

    def __getitem__(self, item):
        raise NotImplementedError()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (self._path_ == other._path_) and (self._config_ is other._config_)

    def items(self):
        return ((k, self[k]) for k in self)


class ConfigItemProxy(PathProxy):

    def __iter__(self):
        for item in self._config_.iter_items(*self._path_):
            yield item.path

    def __getitem__(self, path):
        return self._config_.get_item(*path)

    def __contains__(self, path):
        return self._config_.has(*path)


class ConfigSectionProxy(PathProxy):
    def _get_config_item_(self, path, raw):
        raise AttributeError(path[-1])

    def _set_config_item_(self, path, raw, value):
        raise AttributeError(path[-1])

    def get_item(self, *path):
        if not self._path_:
            raise AttributeError('get_item')
        return self._config_.get_item(*self._prepend_path_(*path))

    def get(self, *path_and_fallback):
        if not self._path_:
            raise AttributeError('get')
        return self._config_.get(*self._prepend_path_(*path_and_fallback))

    def set(self, *path_and_value):
        if not self._path_:
            raise AttributeError('set')
        return self._config_.set(*self._prepend_path_(*path_and_value))

    def has(self, *path):
        if not self._path_:
            raise AttributeError('has')
        return self._config_.has(*self._prepend_path_(*path))

    def __iter__(self):
        for prefix in self._config_.iter_prefixes(*self._path_):
            yield prefix

    def __getitem__(self, prefix):
        return self._get_(prefix)

    @property
    def is_default(self):
        for item in self._config_.iter_items(*self._path_):
            if not item.is_default:
                return False
        return True

    def reset(self):
        for item in self._config_.iter_items(*self._path_):
            item.reset()


class ConfigValueProxy(PathProxy):
    def _get_config_item_(self, path, raw):
        return raw.value

    def _set_config_item_(self, path, raw, value):
        raw.value = value

    def __iter__(self):
        for item in self._config_.iter_items(*self._path_):
            yield item.path

    def __getitem__(self, path):
        return self._config_.get(*path)
