import pytest

from configmanager import ConfigManager, ConfigItem, UnknownConfigItem, UnsupportedOperation


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


def test_values_proxy_exposes_values_for_reading_and_writing(config):
    assert config.v.downloads.threads == 0

    config.v.downloads.threads = 5
    assert config.v.downloads.threads == 5
    assert config.get('downloads', 'threads') == 5
    assert config.get_item('downloads', 'threads').value == 5

    assert config.v.uploads.enabled is False

    config.v.uploads.enabled = 'yes'
    assert config.v.uploads.enabled is True

    config.v.uploads.enabled = 'off'
    assert config.v.uploads.enabled is False

    config.v.auth.client.username = 'admin'
    assert config.v.auth.client.username == 'admin'
    assert config.get_item('auth', 'client', 'username').value == 'admin'

    with pytest.raises(AttributeError):
        config.v.uploads.enabled.really = True


def test_values_proxy_does_not_provide_section_and_item_access(config):
    with pytest.raises(UnsupportedOperation):
        config.v.uploads = {}

    with pytest.raises(AttributeError):
        config.v.uploads.set('enabled', True)

    with pytest.raises(AttributeError):
        config.v.uploads.get('enabled', True)

    with pytest.raises(AttributeError):
        config.v.items()


def test_section_proxy_forbids_access_to_config_items_via_attributes(config):
    with pytest.raises(AttributeError):
        assert config.s.uploads.enabled

    with pytest.raises(AttributeError):
        assert config.s.downloads.enabled

    with pytest.raises(AttributeError):
        assert config.s.auth.server.host

    with pytest.raises(AttributeError):
        config.s.uploads.enabled = True

    with pytest.raises(AttributeError):
        config.s.uploads.enabled.value = True


def test_section_proxy_exposes_sections_and_basic_manager_interface(config):
    assert config.s.downloads
    assert config.s.uploads
    assert config.s.auth
    assert config.s.auth.server
    assert config.s.auth.client

    assert config.s.uploads.get_item('enabled') is config.get_item('uploads', 'enabled')

    assert config.s.uploads.get('enabled') is config.get('uploads', 'enabled')
    assert config.s.auth.get('client', 'password', 'empty1') == 'empty1'
    assert config.s.auth.client.get('password', 'empty2') == 'empty2'

    assert config.s.uploads.has('enabled')
    assert not config.s.uploads.has('nonexistent')

    config.s.auth.client.set('username', 'user1')
    assert config.get('auth', 'client', 'username') == 'user1'

    config.s.auth.set('client', 'username', 'user2')
    assert config.get('auth', 'client', 'username') == 'user2'

    assert config.s.uploads.items()


def test_section_proxy_exposes_has_values_and_reset(config):
    assert not config.has_values
    assert not config.s.uploads.has_values
    assert not config.s.auth.has_values
    assert not config.s.auth.server.has_values

    config.s.uploads.set('enabled', True)
    assert config.s.uploads.has_values
    assert not config.s.auth.has_values
    assert not config.s.auth.server.has_values

    config.s.auth.server.set('host', 'localhost')
    assert config.s.auth.server.has_values
    assert config.s.auth.has_values
    assert not config.s.auth.client.has_values

    config.s.auth.set('client', 'username', 'root')
    assert config.s.auth.client.has_values

    config.s.auth.server.reset()
    assert not config.s.auth.server.has_values
    assert config.s.auth.client.has_values
    assert config.s.auth.has_values


def test_section_proxy_raises_attribute_error_if_section_not_specified(config):
    with pytest.raises(AttributeError):
        config.s.get('auth')

    with pytest.raises(AttributeError):
        config.s.get('auth', 'default')

    with pytest.raises(AttributeError):
        config.s.get('auth', 'client', 'password', 'default')

    with pytest.raises(AttributeError):
        config.s.set('uploads', 'enabled', True)

    with pytest.raises(AttributeError):
        config.s.set('enabled', True)

    with pytest.raises(AttributeError):
        config.s.items()

    with pytest.raises(AttributeError):
        config.s.has('uploads')

    with pytest.raises(AttributeError):
        config.s.has('uploads', 'enabled')


def test_item_proxy(config):
    assert isinstance(config.t.uploads.enabled, ConfigItem)

    with pytest.raises(AttributeError):
        assert config.t.uploads.nonexistent

    config.t.uploads.enabled.value = 'yes'
    assert isinstance(config.t.uploads.enabled, ConfigItem)

    assert config.t.uploads.enabled.value is True

    assert isinstance(config.t.auth.client.username, ConfigItem)
