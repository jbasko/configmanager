import pytest

import collections

from configmanager import ConfigValues


@pytest.fixture
def config():
    source = collections.OrderedDict()
    source['uploads'] = collections.OrderedDict()
    source['uploads']['threads'] = 5
    source['uploads']['enabled'] = True
    source['uploads']['tmp_dir'] = '/tmp'
    source['uploads']['db'] = collections.OrderedDict()
    source['uploads']['db']['user'] = 'root'
    return ConfigValues(source)


def test_config_values_is_an_ordered_dictionary(config):
    assert len(config) == 1
    assert list(config.keys()) == ['uploads']
    assert list(config.values()) == [config['uploads']]

    assert config['uploads']

    assert list(config['uploads'].keys()) == ['threads', 'enabled', 'tmp_dir', 'db']
    assert len(config['uploads']) == 4
    assert len(config['uploads']['db']) == 1
    assert list(config['uploads']['db'].keys()) == ['user']

    assert dict(config['uploads']['db']) == {'user': 'root'}

    d = dict(config['uploads'])
    del d['db']  # unpacking of nested sections doesn't work as smoothly
    assert d == {'threads': 5, 'enabled': True, 'tmp_dir': '/tmp'}


def test_config_values_is_read_only_via_key_access(config):
    with pytest.raises(RuntimeError):
        config['uploads'] = {}

    with pytest.raises(RuntimeError):
        config['downloads'] = 2

    with pytest.raises(RuntimeError):
        config['uploads']['enabled'] = False

    with pytest.raises(RuntimeError):
        config['uploads']['greeting'] = 'Hello'

    with pytest.raises(RuntimeError):
        config['uploads']['db']['user'] = 'admin'

    with pytest.raises(RuntimeError):
        config['uploads']['db']['password'] = 'secret'


def test_get_returns_value_or_fallback(config):
    with pytest.raises(KeyError):
        config.get('downloads')

    assert config.get('downloads', None) is None
    assert config.get('downloads', 5) == 5

    with pytest.raises(KeyError):
        assert config['uploads'].get('greeting')
    assert config['uploads'].get('greeting', 'Hello') == 'Hello'

    with pytest.raises(KeyError):
        # uploads is a section and it doesn't accept a fallback
        assert config.get('uploads', 'greeting')

    with pytest.raises(RuntimeError):
        # get doesn't return sections
        assert config.get('uploads', 'db')

    assert config.get('uploads', 'greeting', 'Hello') == 'Hello'


def test_attribute_like_access_to_sections_and_values(config):
    assert config.uploads

    with pytest.raises(AttributeError):
        assert not config.downloads


def test_attribute_like_access_does_not_allow_changing_values(config):
    # existent attribute
    with pytest.raises(RuntimeError):
        config.uploads = {}

    # non-existent attribute
    with pytest.raises(RuntimeError):
        config.downloads = 2

    # existent attribute
    with pytest.raises(RuntimeError):
        config.uploads.enabled = False

    # non-existent attribute
    with pytest.raises(RuntimeError):
        config.uploads.disabled = False

    # existent attribute
    with pytest.raises(RuntimeError):
        config.uploads.db.user = 'admin'

    # non-existent attribute
    with pytest.raises(RuntimeError):
        config.uploads.db.password = 'secret'
