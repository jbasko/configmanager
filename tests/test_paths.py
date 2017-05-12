import pytest

from configmanager import ConfigItem, ConfigManager, UnknownConfigItem


def test_dots_in_path_segments_dont_create_new_segments():
    assert ConfigItem('www.xyz.com', 'greeting').path == ('www.xyz.com', 'greeting')
    assert ConfigItem('www', 'greeting.com').path == ('www', 'greeting.com')
    assert ConfigItem('www.', '.greeting.com').path == ('www.', '.greeting.com')
    assert ConfigItem('x.y').path == (ConfigItem.DEFAULT_SECTION, 'x.y')
    assert ConfigItem('x').path == (ConfigItem.DEFAULT_SECTION, 'x')


def test_config_with_three_segment_path():
    c = ConfigItem('x', 'y', 'z')
    assert c.name == 'z'
    assert c.path == ('x', 'y', 'z')
    assert c.strpath == 'x/y/z'

    d = ConfigItem('xx', 'yy', 'zz')
    assert d.name == 'zz'
    assert d.path == ('xx', 'yy', 'zz')
    assert d.strpath == 'xx/yy/zz'


def test_config_manager_handles_config_of_three_segment_path():
    m = ConfigManager(
        ConfigItem('x', 'y', 'z', type=float, default=0.33),
        ConfigItem('a', 'a', 'a', default='haha')
    )

    assert m.has('x', 'y', 'z')
    assert not m.has('x.y.z')

    assert m.get('x', 'y', 'z') == 0.33

    m.set('x', 'y', 'z', 0.44)
    assert m.get('x', 'y', 'z') == 0.44

    with pytest.raises(UnknownConfigItem):
        m.set('a.a.a', 'HAHA')

    assert m.get('a', 'a', 'a') == 'haha'

    m.set('a', 'a', 'a', 'HAHA')
    assert m.get('a', 'a', 'a') == 'HAHA'


def test_cannot_treat_config_as_section():
    m = ConfigManager(
        ConfigItem('x', 'y')
    )

    with pytest.raises(UnknownConfigItem):
        m.set('x', 'y', 'z', 'value')

    with pytest.raises(UnknownConfigItem):
        m.get('x', 'y', 'zz', 'default')
