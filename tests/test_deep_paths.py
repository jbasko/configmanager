import pytest

from configmanager import ConfigItem, ConfigManager


def test_config_with_three_segment_path():
    c = ConfigItem('x', 'y', 'z')
    assert c.name == 'x.y.z'
    assert c.path == ('x', 'y', 'z')

    d = ConfigItem('xx', 'yy.zz')
    assert d.name == 'xx.yy.zz'
    assert d.path == ('xx', 'yy', 'zz')

    e = ConfigItem('xx.yy', 'zz')
    assert e.name == 'xx.yy.zz'
    assert e.path == ('xx', 'yy', 'zz')

    f = ConfigItem('xx.yy.zz')
    assert f.name == 'xx.yy.zz'
    assert f.path == ('xx', 'yy', 'zz')


def test_config_manager_handles_config_of_three_segment_path():
    m = ConfigManager(
        ConfigItem('x.y.z', type=float, default=0.33)
    )

    assert m.has('x.y.z')
    assert m.get('x.y.z').value == 0.33

    m.set('x.y.z', 0.44)
    assert m.get('x.y.z').value == 0.44


def test_cannot_treat_config_as_section():
    m = ConfigManager(
        ConfigItem('x.y')
    )

    with pytest.raises(ValueError):
        assert not m.set('x.y.z')

    zz = m.get('x.yy.zz')
    assert not zz.exists

