import pytest

from configmanager import ConfigManager, ConfigItem, UnsupportedOperation, ConfigValueMissing
from configmanager.proxies import ConfigSectionProxy
from configmanager.utils import not_set


@pytest.fixture
def config():
    return ConfigManager(
        ConfigItem('uploads', 'enabled', type=bool, default=False),
        ConfigItem('downloads', 'enabled', type=bool),
        ConfigItem('downloads', 'threads', type=int, default=0),
        ConfigItem('auth', 'server', 'host'),
        ConfigItem('auth', 'server', 'port', type=int),
        ConfigItem('auth', 'client', 'username', required=True),
        ConfigItem('auth', 'client', 'password')
    )


def test_value_proxy_exposes_values_for_reading_and_writing(config):
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


def test_value_proxy_does_not_provide_section_and_item_access(config):
    with pytest.raises(UnsupportedOperation):
        config.v.uploads = {}

    with pytest.raises(AttributeError):
        config.v.uploads.set('enabled', True)

    with pytest.raises(AttributeError):
        config.v.uploads.get('enabled', True)

    # This is different, "items" don't refer to config items here, it's part of Python's dictionary interface.
    assert config.v.items()


def test_iteration_over_value_proxy_returns_values_of_all_irrespective_of_status(config):
    with pytest.raises(ConfigValueMissing):
        dict(config.v.items())

    # set the only required value
    config.set('auth', 'client', 'username', 'admin')

    values = dict(config.v.items())
    assert len(values) == 7

    assert values[('uploads', 'enabled')] is False
    assert values[('downloads', 'enabled')] is not_set


def test_value_proxy_is_iterable(config):
    paths = list(config.v)
    assert len(paths) == 7
    assert config.v[paths[0]] is False
    assert config.v[paths[1]] is not_set

    config.set('auth', 'server', 'port', 3333)
    config.set('uploads', 'enabled', 'yes')
    paths = list(config.v)
    assert len(paths) == 7

    assert paths[0] == ('uploads', 'enabled')
    assert paths[-1] == ('auth', 'client', 'password')


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


def test_section_proxy_exposes_is_default_and_reset(config):
    assert config.is_default
    assert config.s.uploads.is_default
    assert config.s.auth.is_default
    assert config.s.auth.server.is_default

    config.s.uploads.set('enabled', True)
    assert not config.s.uploads.is_default
    assert config.s.auth.is_default
    assert config.s.auth.server.is_default

    config.s.auth.server.set('host', 'localhost')
    assert not config.s.auth.server.is_default
    assert not config.s.auth.is_default
    assert config.s.auth.client.is_default

    config.s.auth.set('client', 'username', 'root')
    assert not config.s.auth.client.is_default

    config.s.auth.server.reset()
    assert config.s.auth.server.is_default
    assert not config.s.auth.client.is_default
    assert not config.s.auth.is_default


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

    # This is different now, items() is part of Python's dictionary interface, nothing to do with config items.
    assert config.s.items()

    with pytest.raises(AttributeError):
        config.s.has('uploads')

    with pytest.raises(AttributeError):
        config.s.has('uploads', 'enabled')


def test_section_proxy_is_iterable(config):
    prefixes = list(config.s)
    assert len(prefixes) == 5

    assert prefixes[0] == ('uploads',)
    assert prefixes[-1] == ('auth', 'client')

    assert isinstance(config.s[prefixes[0]], ConfigSectionProxy)


def test_item_proxy_provides_access_to_items(config):
    assert isinstance(config.t.uploads.enabled, ConfigItem)

    with pytest.raises(AttributeError):
        assert config.t.uploads.nonexistent

    config.t.uploads.enabled.value = 'yes'
    assert isinstance(config.t.uploads.enabled, ConfigItem)

    assert config.t.uploads.enabled.value is True

    assert isinstance(config.t.auth.client.username, ConfigItem)


def test_item_proxy_is_iterable(config):
    paths = list(config.t)
    assert len(paths) == 7

    assert config.t[paths[0]] is config.t.uploads.enabled

    assert ('auth', 'server', 'port') in paths
    assert ('uploads', 'something_else') not in paths


def test_proxies_support_items_transparently(config):
    items = dict(config.t.items())
    assert len(items) == 7
    assert isinstance(items[('uploads', 'enabled')], ConfigItem)

    sections = dict(config.s.items())
    assert len(sections) == 5
    assert isinstance(sections[('auth', 'server')], ConfigSectionProxy)

    with pytest.raises(ConfigValueMissing):
        dict(config.v.items())

    config.v.auth.client.username = 'admin'
    values = dict(config.v.items())
    assert len(values) == 7
    assert values[('uploads', 'enabled')] is False
    assert values[('downloads', 'threads')] == 0
