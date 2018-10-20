import pytest

from configmanager import PlainConfig


def test_read_only_plain_config():
    config = PlainConfig(schema={
        'name': 'foo',
        'db': {
            'username': 'root'
        },
    }, read_only=True)
    assert config.settings.read_only

    assert config.name == 'foo'

    with pytest.raises(RuntimeError) as exc_info:
        config.db = None
    assert 'db is read-only' in str(exc_info.value)

    with pytest.raises(RuntimeError) as exc_info:
        config.name = 'bar'
    assert 'name is read-only' in str(exc_info.value)

    with pytest.raises(RuntimeError) as exc_info:
        config.db.username = 'ha'
    assert 'username is read-only' in str(exc_info.value)

    assert config.db.username == 'root'
