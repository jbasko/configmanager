import pytest

from configmanager import Config, NotFound
from configmanager.hooks import Hooks


def test_hooks_is_a_config_root_attribute():
    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    assert isinstance(config.uploads.hooks, Hooks)
    assert isinstance(config.hooks, Hooks)
    assert isinstance(config.uploads.db.hooks, Hooks)

    assert config.hooks is config.uploads.hooks
    assert config.hooks is config.uploads.db.hooks

    with pytest.raises(AttributeError):
        _ = config.uploads.db.user.hooks


def test_not_found_hook():
    calls = []

    config = Config({
        'uploads': {}
    })

    @config.hooks.not_found
    def first_hook(*args, **kwargs):
        calls.append(('first', args, kwargs))

    @config.hooks.not_found
    def second_hook(*args, **kwargs):
        calls.append(('second', args, kwargs))

    assert len(calls) == 0

    with pytest.raises(NotFound):
        _ = config.db

    assert len(calls) == 2
    assert calls[0] == ('first', (), {'section': config, 'name': 'db'})
    assert calls[1] == ('second', (), {'section': config, 'name': 'db'})

    with pytest.raises(NotFound):
        _ = config.uploads.threads

    assert len(calls) == 4
    assert calls[2] == ('first', (), {'section': config.uploads, 'name': 'threads'})
    assert calls[3] == ('second', (), {'section': config.uploads, 'name': 'threads'})

    # A hook that creates the missing item so further calls won't trigger
    # the hook handlers again, including any subsequent hook handlers as part of current event.
    @config.hooks.not_found
    def third_hook(*args, **kwargs):
        calls.append(('third', args, kwargs))

        assert kwargs['section']
        assert kwargs['name']

        item = kwargs['section'].create_item(name=kwargs['name'])
        kwargs['section'].add_item(item.name, item)
        return item

    # Fourth hook will never be called because the third hook already resolves the missing name
    @config.hooks.not_found
    def fourth_hook(*args, **kwargs):
        calls.append(('fourth', args, kwargs))

    assert len(calls) == 4

    assert config.uploads.threads

    assert len(calls) == 7

    assert calls[4] == ('first', (), {'section': config.uploads, 'name': 'threads'})
    assert calls[5] == ('second', (), {'section': config.uploads, 'name': 'threads'})
    assert calls[6] == ('third', (), {'section': config.uploads, 'name': 'threads'})

    assert config.uploads.threads

    assert len(calls) == 7
