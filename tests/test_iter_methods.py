import pytest


from configmanager import ConfigManager, ConfigItem
from configmanager.utils import not_set


@pytest.fixture
def config():
    return ConfigManager(
        ConfigItem('uploads', 'enabled', type=bool, default=False),
        ConfigItem('downloads', 'enabled', type=bool),
        ConfigItem('downloads', 'threads', type=int, default=0),
        ConfigItem('auth', 'server', 'host'),
        ConfigItem('auth', 'server', 'port', type=int),
        ConfigItem('auth', 'client', 'username'),
        ConfigItem('auth', 'client', 'password')
    )


def test_all_paths(config):
    paths = list(config.iter_paths())
    assert len(paths) == 7
    assert paths[0] == ('uploads', 'enabled')
    assert paths[-1] == ('auth', 'client', 'password')


def test_paths_with_prefix(config):
    upload_paths = list(config.iter_paths('uploads'))
    assert len(upload_paths) == 1
    assert upload_paths[0] == ('uploads', 'enabled')

    auth_paths = list(config.iter_paths('auth'))
    assert len(auth_paths) == 4
    assert auth_paths[0] == ('auth', 'server', 'host')
    assert auth_paths[-1] == ('auth', 'client', 'password')

    server_paths = list(config.iter_paths('auth', 'server'))
    assert len(server_paths) == 2
    assert server_paths[0] == ('auth', 'server', 'host')
    assert server_paths[1] == ('auth', 'server', 'port')


def test_all_prefixes(config):
    prefixes = list(config.iter_prefixes())
    assert len(prefixes) == 5
    assert prefixes[0] == ('uploads',)
    assert prefixes[2] == ('auth',)
    assert prefixes[4] == ('auth', 'client')


def test_prefixes_with_prefix(config):
    assert list(config.iter_prefixes('uploads')) == [('uploads',)]

    auth_prefixes = list(config.iter_prefixes('auth'))
    assert len(auth_prefixes) == 3
    assert auth_prefixes[0] == ('auth',)
    assert auth_prefixes[1] == ('auth', 'server')
    assert auth_prefixes[2] == ('auth', 'client')

    server_prefixes = list(config.iter_prefixes('auth', 'server'))
    assert server_prefixes == [('auth', 'server',)]


def test_all_items(config):
    items = list(config.iter_items())
    assert len(items) == 7
    assert isinstance(items[0], ConfigItem)
    assert items[0] is config.t.uploads.enabled
    assert items[-1] is config.t.auth.client.password


def test_items_with_prefix(config):
    download_items = list(config.iter_items('downloads'))
    assert len(download_items) == 2
    assert download_items[0] is config.t.downloads.enabled
    assert download_items[1] is config.t.downloads.threads

    auth_items = list(config.iter_items('auth'))
    assert len(auth_items) == 4
    assert auth_items[-1] is config.t.auth.client.password

    auth_server_items = list(config.iter_items('auth', 'server'))
    assert len(auth_server_items) == 2
    assert auth_server_items[0] is config.t.auth.server.host


def test_all_values(config):
    values = list(config.iter_values())
    assert len(values) == 7
    assert values[0] is False
    assert values[-1] is not_set


def test_values_with_prefix(config):
    values = list(config.iter_values('downloads'))
    assert len(values) == 2
    assert values[0] == config.get('downloads', 'enabled')
    assert values[1] == config.get('downloads', 'threads')
