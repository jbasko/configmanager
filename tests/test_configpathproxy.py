import pytest

from configmanager import ConfigManager, ConfigItem, UnknownConfigItem


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


def test_gets_top_level_section_configs(config):
    uploads = config.uploads
    assert uploads.path == ('uploads',)

    assert uploads.has('enabled')
    assert not uploads.has('disabled')

    assert isinstance(uploads.get('enabled'), ConfigItem)
    with pytest.raises(UnknownConfigItem):
        uploads.get_item('disabled')

    assert uploads.get('enabled') is False
    with pytest.raises(UnknownConfigItem):
        uploads.get('disabled')

    uploads.set('enabled', True)
    with pytest.raises(UnknownConfigItem):
        uploads.set('disabled', True)
