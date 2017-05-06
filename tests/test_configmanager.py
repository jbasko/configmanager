import pytest

from configmanager import Config, ConfigManager


def test_get_config():
    m = ConfigManager(
        Config('a', '1', value='a1'),
        Config('a', '2', value='a2'),
        Config('b', '1', value='b1'),
        Config('b', '2', value='b2'),
    )

    a1 = m.get_config('a', '1')
    assert isinstance(a1, Config)
    assert a1 == 'a1'

    assert m.get_config('a.1') == 'a1'
    assert m.get_config('a.2') == 'a2'
    assert m.get_config('b.1') == 'b1'
    assert m.get_config('b.2') == 'b2'


def test_duplicate_config_raises_value_error():
    m = ConfigManager()
    m.add_config(Config('a', 'b'))

    with pytest.raises(ValueError):
        m.add_config(Config('a', 'b'))

    m.add_config(Config('a', 'c'))


def test_set_config():
    m = ConfigManager(
        Config('c', '1', type=int),
        Config('c', '2'),
    )

    m.set_config('c.1', '55')
    m.set_config('c', '2', '55')

    assert m.get_config('c', '1') == 55
    assert m.get_config('c.2') == '55'


def test_config_manager_configs_are_safe_copies():
    c1 = Config('c', '1', type=int)
    c2 = Config('c', '2', type=list)

    m = ConfigManager(c1)

    c1.value = 5
    assert not m.get_config('c', '1').has_value

    m.get_config('c', '1').value = 66
    assert c1.value == 5

    m.add_config(c2)
    c2.value = [1, 2, 3]
    assert not m.get_config('c', '2').has_value

    m.get_config('c', '2').value = [4, 5, 6]
    assert c2.value == [1, 2, 3]


def test_config_section():
    m = ConfigManager(
        Config('a', 'b'),
        Config('a', 'c'),
        Config('a', 'd'),
        Config('x', 'y'),
        Config('x', 'z'),
    )

    assert m.a
    assert m.x
    with pytest.raises(AttributeError):
        assert not m.b

    assert not m.a.b.has_value

    m.a.b = 1
    assert m.a.b == '1'

    with pytest.raises(AttributeError):
        m.a.xx = 23
