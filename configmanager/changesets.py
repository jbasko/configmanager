import collections


_Change = collections.namedtuple('Change', field_names=(
    'old_value', 'new_value', 'old_raw_str_value', 'new_raw_str_value'
))


class _ChangesetContext(object):
    def __init__(self, config, auto_reset=False, **unsupported_options):
        self.config = config
        self.hook = None
        self._changes = collections.defaultdict(list)
        self._auto_reset = auto_reset

    def __enter__(self):
        return self.push()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pop()
        if self._auto_reset:
            self.reset()

    def _value_changed(self, item, old_value, new_value, old_raw_str_value, new_raw_str_value):
        if old_value != new_value or old_raw_str_value != new_raw_str_value:
            self._changes[item].append(_Change(old_value, new_value, old_raw_str_value, new_raw_str_value))

    def push(self):
        assert self.hook is None
        self.hook = self.config.hooks.item_value_changed.register_hook(self._value_changed)
        self.config._changeset_contexts.append(self)
        return self

    def pop(self):
        popped = self.config._changeset_contexts.pop()
        assert popped is self
        self.config.hooks.unregister_hook(self.config.hooks.item_value_changed, self._value_changed)
        self.hook = None

    @property
    def values(self):
        """
        Returns a mapping of items to their new values. The mapping includes only items whose value or raw string value
        has changed in the context.
        """
        report = {}
        for k, k_changes in self._changes.items():
            if len(k_changes) == 1:
                report[k] = k_changes[0].new_value
            elif k_changes[0].old_value != k_changes[-1].new_value:
                report[k] = k_changes[-1].new_value
        return report

    @property
    def changes(self):
        """
        Returns a mapping of items to their effective change objects which include the old values
        and the new. The mapping includes only items whose value or raw string value has changed in the context.
        """
        report = {}
        for k, k_changes in self._changes.items():
            if len(k_changes) == 1:
                report[k] = k_changes[0]
            else:
                first = k_changes[0]
                last = k_changes[-1]
                if first.old_value != last.new_value or first.old_raw_str_value != last.new_raw_str_value:
                    report[k] = _Change(
                        first.old_value,
                        last.new_value,
                        first.old_raw_str_value,
                        last.new_raw_str_value,
                    )
        return report

    def reset(self, item=None):
        for k, k_changes in self._changes.items():
            if item is None or k is item:
                k._value = k_changes[0].old_value
                k.raw_str_value = k_changes[0].old_raw_str_value

        if item is None:
            self._changes.clear()
        else:
            del self._changes[item]

    def __len__(self):
        """
        Returns the number of items whose value or raw string value has changed in this context.
        """
        return len(self.changes)
