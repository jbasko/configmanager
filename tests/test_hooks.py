import pytest

from configmanager import Config, NotFound, Section
from configmanager.utils import not_set


def test_hooks_available_on_all_sections():
    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    assert config.uploads.hooks
    assert config.hooks
    assert config.uploads.db.hooks

    with pytest.raises(AttributeError):
        _ = config.uploads.db.user.hooks


def test_not_found_hook():
    calls = []

    config = Config({
        'uploads': Section()
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


def test_item_added_to_section_hook():
    calls = []

    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    @config.hooks.item_added_to_section
    def item_added_to_section(*args, **kwargs):
        calls.append(('first', args, kwargs))

    @config.hooks.item_added_to_section
    def item_added_to_section2(*args, **kwargs):
        calls.append(('second', args, kwargs))

    assert calls == []

    # Adding a section to a section is unrelated
    config.add_section('downloads', config.create_section())

    assert calls == []

    password = config.create_item(name='password')
    threads = config.create_item(name='threads', default=5)
    assert calls == []

    config.uploads.db.add_item(password.name, password)

    # Note that the item added to Config is actually a different instance to the one that was passed to add_item.
    # This is because we do deepcopy in add_item.
    assert calls == [
        ('first', (), {'section': config.uploads.db, 'subject': config.uploads.db.password, 'alias': 'password'}),
        ('second', (), {'section': config.uploads.db, 'subject': config.uploads.db.password, 'alias': 'password'}),
    ]

    config.uploads.add_item('threads_alias', threads)
    assert len(calls) == 4

    assert calls[2:] == [
        ('first', (), {'section': config.uploads, 'subject': config.uploads.threads, 'alias': 'threads_alias'}),
        ('second', (), {'section': config.uploads, 'subject': config.uploads.threads, 'alias': 'threads_alias'}),
    ]


def test_callback_returning_something_cancels_parent_section_hook_handling():
    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    calls = []

    @config.hooks.item_added_to_section
    def root_handler(**kwargs):
        calls.append('root')

    @config.uploads.hooks.item_added_to_section
    def uploads_handler(**kwargs):
        calls.append('uploads')

    @config.uploads.db.hooks.item_added_to_section
    def db_handler(**kwargs):
        calls.append('db')

    assert calls == []

    config.uploads.db.add_item('password', config.create_item(name='password'))

    assert calls == ['db', 'uploads', 'root']

    @config.uploads.hooks.item_added_to_section
    def another_uploads_handler(**kwargs):
        calls.append('uploads2')
        return True

    # Root hooks are not handled because uploads2 returned something
    config.uploads.db.add_item('host', config.create_item(name='host'))
    assert len(calls) == 6
    assert calls[-3:] == ['db', 'uploads', 'uploads2']

    # Root hook is handled because the event happens on root level
    config.add_item('greeting', config.create_item(name='greeting'))
    assert len(calls) == 7
    assert calls[-1:] == ['root']


def test_section_added_to_section_hook():
    calls = []

    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    @config.hooks.section_added_to_section
    def section_added_to_section1(*args, **kwargs):
        calls.append(('on_root', args, kwargs))

    @config.uploads.hooks.section_added_to_section
    def section_added_to_section2(*args, **kwargs):
        calls.append(('on_uploads', args, kwargs))

    assert calls == []

    config.add_section('downloads', config.create_section())
    assert len(calls) == 1
    assert calls[-1:] == [
        ('on_root', (), {'subject': config.downloads, 'alias': 'downloads', 'section': config}),
    ]

    config.uploads.db.add_section('backups', config.create_section())
    assert len(calls) == 3
    assert calls[-2:] == [
        ('on_uploads', (), {'subject': config.uploads.db.backups, 'alias': 'backups', 'section': config.uploads.db}),
        ('on_root', (), {'subject': config.uploads.db.backups, 'alias': 'backups', 'section': config.uploads.db}),
    ]


def test_item_value_changed_hook():
    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    calls = []

    @config.hooks.item_value_changed
    def item_value_changed(old_value=None, new_value=None, item=None, **kwargs):
        calls.append((item, old_value, new_value))

    assert calls == []

    config.reset()

    assert calls == []

    config.uploads.db.user.set('admin')

    assert len(calls) == 1
    assert calls[-1] == (config.uploads.db.user, not_set, 'admin')

    config.uploads.db.user.value = 'Administrator'

    assert len(calls) == 2
    assert calls[-1] == (config.uploads.db.user, 'admin', 'Administrator')

    config.load_values({'uploads': {'something_nonexistent': True}})
    assert len(calls) == 2

    config.load_values({'uploads': {'db': {'user': 'NEW DEFAULT'}}}, as_defaults=True)
    assert len(calls) == 2

    config.load_values({'uploads': {'db': {'user': 'NEW VALUE'}}})
    assert len(calls) == 3
    assert calls[-1] == (config.uploads.db.user, 'Administrator', 'NEW VALUE')


def test_hooks_arent_handled_if_hooks_enabled_setting_is_set_to_falsey_value():
    config = Config({
        'uploads': {
            'db': {
                'user': 'root'
            }
        }
    })

    calls = []

    @config.hooks.item_value_changed
    def item_value_changed(**kwargs):
        calls.append(1)

    config.uploads.db.user.value = 'admin1'
    assert len(calls) == 1

    config.uploads.db.user.value = 'admin2'
    assert len(calls) == 2

    config.settings.hooks_enabled = False
    config.uploads.db.user.value = 'admin3'
    assert len(calls) == 2

    config.settings.hooks_enabled = None
    config.uploads.db.user.value = 'admin4'
    assert len(calls) == 2

    config.settings.hooks_enabled = True
    config.uploads.db.user.value = 'admin5'
    assert len(calls) == 3


def test_hooks_work_across_nested_configs():
    calls = []

    uploads_config = Config({
        'db': Config({
            'user': 'root',
        })
    })

    @uploads_config.hooks.item_value_changed
    def value_changed(**kwargs):
        calls.append(('uploads', kwargs))

    config = Config({
        'uploads': uploads_config,
        'greeting': 'Hello',
    })

    config.greeting.value = 'Hey!'
    assert len(calls) == 0

    config.uploads.db.user.value = 'admin'
    assert len(calls) == 1

    @config.hooks.item_value_changed
    def value_changed(**kwargs):
        calls.append(('main', kwargs))

    uploads_config.db.user.value = 'Administrator'
    assert len(calls) == 3


def test_not_found_hook_not_handled_if_contains_raises_not_found(simple_config):
    calls = []

    @simple_config.hooks.not_found
    def not_found(**kwargs):
        calls.append(kwargs)

    assert len(calls) == 0

    assert 'downloads' not in simple_config

    assert len(calls) == 0


def test_not_found_hook_handled_in_iterators(simple_config):
    calls = []

    @simple_config.hooks.not_found
    def not_found(**kwargs):
        calls.append(kwargs)

    assert len(calls) == 0

    with pytest.raises(NotFound):
        list(simple_config.iter_items(path='uploads.downloads.leftloads.rightloads', recursive=True))

    assert len(calls) == 1

    with pytest.raises(NotFound):
        list(simple_config.iter_paths(path='uploads.downloads.leftloads.rightloads', recursive=True))

    assert len(calls) == 2
