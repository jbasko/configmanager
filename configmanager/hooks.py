import collections


class Hooks(object):

    NOT_FOUND = 'not_found'
    ITEM_ADDED_TO_SECTION = 'item_added_to_section'
    SECTION_ADDED_TO_SECTION = 'section_added_to_section'
    ITEM_VALUE_CHANGED = 'item_value_changed'

    _names = (
        NOT_FOUND,
        ITEM_ADDED_TO_SECTION,
        SECTION_ADDED_TO_SECTION,
        ITEM_VALUE_CHANGED,
    )

    def __init__(self, config):
        self._config = config
        self._registry = collections.defaultdict(list)
        self._decorators = {}

    def _get_decorator(self, name):
        if name not in self._decorators:
            def decorator(f):
                self._registry[name].append(f)
                if self._config._configmanager_settings.hooks_enabled is None:
                    self._config._configmanager_settings.hooks_enabled = True
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
        if not self._config._configmanager_settings.hooks_enabled:
            return

        for handler in self._registry[hook_name]:
            result = handler(*args, **kwargs)
            if result is not None:
                return result

        # Must also call callbacks in parent section hook registry
        if self._config.section and self._config.section.hooks != self:
            return self._config.section.hooks.handle(hook_name, *args, **kwargs)
