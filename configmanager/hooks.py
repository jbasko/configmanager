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

    def __init__(self, section):
        self._section = section
        self._registry = collections.defaultdict(list)
        self._decorators = {}

    def _get_decorator(self, name):
        if name not in self._decorators:
            def decorator(f):
                self._registry[name].append(f)
                if self._section.settings.hooks_enabled is None:
                    self._section.settings.hooks_enabled = True
                return f
            decorator.__name__ = name
            self._decorators[name] = decorator
        return self._decorators[name]

    def not_found(self, f):
        return self._get_decorator(self.NOT_FOUND)(f)

    def item_added_to_section(self, f):
        return self._get_decorator(self.ITEM_ADDED_TO_SECTION)(f)

    def section_added_to_section(self, f):
        return self._get_decorator(self.SECTION_ADDED_TO_SECTION)(f)

    def item_value_changed(self, f):
        return self._get_decorator(self.ITEM_VALUE_CHANGED)(f)

    def handle(self, hook_name, *args, **kwargs):

        # If hooks are disabled in a high-level Config, and enabled
        # in a low-level Config, they will still be handled within
        # the low-level Config's "jurisdiction".

        if self._section.settings.hooks_enabled:
            for handler in self._registry[hook_name]:
                result = handler(*args, **kwargs)
                if result is not None:
                    return result

            # Must also call callbacks in parent section hook registry
            if self._section.section and self._section.section.hooks != self:
                return self._section.section.hooks.handle(hook_name, *args, **kwargs)

        elif self._section.is_config and self._section.section:
            # Settings only apply to within one Config instance in the tree.
            # Hooks still may need to be called in parent Configs.
            self._section.section.hooks.handle(hook_name, *args, **kwargs)
