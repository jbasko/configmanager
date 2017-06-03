import collections


class Hooks(object):

    NOT_FOUND = 'not_found'
    ADDED_TO_SECTION = 'added_to_section'
    VALUE_CHANGED = 'value_changed'

    _names = (
        NOT_FOUND,
        ADDED_TO_SECTION,
        VALUE_CHANGED,
    )

    def __init__(self, config):
        self._config = config
        self._registry = collections.defaultdict(list)
        self._decorators = {}

    def _get_decorator(self, name):
        if name not in self._decorators:
            def decorator(f):
                self._registry[name].append(f)
                return f
            decorator.__name__ = name
            self._decorators[name] = decorator
        return self._decorators[name]

    def __getattr__(self, name):
        if name in self._names:
            return self._get_decorator(name)
        else:
            raise AttributeError('Hook {} does not exist; valid hook names are {}'.format(
                name, ', '.join(self._names),
            ))

    def handle(self, hook_name, *args, **kwargs):
        for handler in self._registry[hook_name]:
            result = handler(*args, **kwargs)
            if result is not None:
                return result
