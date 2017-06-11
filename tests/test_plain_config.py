import pytest
import six

from configmanager import NotFound, Item, PlainConfig


@pytest.fixture
def schema():
    return {
        'uploads': {
            'enabled': True,
            'threads': 1,
            'tmp_dir': None,
            'db': {
                'user': 'root',
                'password': 'secret',
            }
        },
    }


def test_items_are_values(schema):
    config = PlainConfig(schema)

    assert config.uploads.is_section
    assert isinstance(config.uploads.enabled, bool)
    assert config.uploads.enabled is True

    assert config.uploads.db.is_section
    assert isinstance(config.uploads.db.user, six.string_types)
    assert config.uploads.db.user == 'root'

    with pytest.raises(AttributeError):
        assert not config.uploads.db.password.value

    with pytest.raises(NotFound):
        assert config.greeting


def test_values_can_be_changed(schema):
    config = PlainConfig(schema)

    assert config.uploads.tmp_dir is None
    assert config.uploads.db.user == 'root'

    config.uploads.enabled = 'no'
    config.uploads.threads = '5'
    config.uploads.tmp_dir = '/tmp'
    config.uploads.db.user = 'admin'

    assert config.uploads.enabled is False
    assert config.uploads.threads == 5
    assert config.uploads.tmp_dir == '/tmp'
    assert config.uploads.db.user == 'admin'

    assert config.dump_values() == {
        'uploads': {
            'enabled': False,
            'threads': 5,
            'tmp_dir': '/tmp',
            'db': {
                'user': 'admin',
                'password': 'secret',
            }
        }
    }


def test_hooks_work(schema):
    config = PlainConfig(schema)

    calls = []

    @config.hooks.item_value_changed
    def item_value_changed(item, old_value, new_value):
        assert isinstance(item, Item)
        assert item.value == new_value
        assert item.value != old_value
        calls.append(item.name)

    assert len(calls) == 0

    config.uploads.enabled = 'no'
    assert calls == ['enabled']

    config.uploads.db.user = 'admin'
    assert calls == ['enabled', 'user']
