import pytest

from configmanager import Config, ConfigManager


def test_get():
    m = ConfigManager(
        Config('a', '1', value='a1'),
        Config('a', '2', value='a2'),
        Config('b', '1', value='b1'),
        Config('b', '2', value='b2'),
    )

    a1 = m.get('a', '1')
    assert isinstance(a1, Config)
    assert a1 == 'a1'

    assert m.get('a.1') == 'a1'
    assert m.get('a.2') == 'a2'
    assert m.get('b.1') == 'b1'
    assert m.get('b.2') == 'b2'


def test_duplicate_config_raises_value_error():
    m = ConfigManager()
    m.add(Config('a', 'b'))

    with pytest.raises(ValueError):
        m.add(Config('a', 'b'))

    m.add(Config('a', 'c'))


def test_sets_config():
    m = ConfigManager(
        Config('c', '1', type=int),
        Config('c', '2'),
    )

    m.set('c.1', '55')
    m.set('c', '2', '55')

    assert m.get('c', '1') == 55
    assert m.get('c.2') == '55'


def test_config_manager_configs_are_safe_copies():
    c1 = Config('c', '1', type=int)
    c2 = Config('c', '2', type=list)

    m = ConfigManager(c1)

    c1.value = 5
    assert not m.get('c', '1').has_value

    m.get('c', '1').value = 66
    assert c1.value == 5

    m.add(c2)
    c2.value = [1, 2, 3]
    assert not m.get('c', '2').has_value

    m.get('c', '2').value = [4, 5, 6]
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


def test_has():
    m = ConfigManager()

    assert not m.has('a', 'b')
    assert not m.has('a.b')

    m.add(Config('a', 'b'))

    assert m.has('a', 'b')
    assert m.has('a.b')

    assert not m.has('a', 'c')
    assert not m.has('a.c')

    assert not m.has('b', 'a')
    assert not m.has('b', 'b')


def test_can_retrieve_non_existent_config():
    m = ConfigManager(
        Config('very', 'real')
    )

    a = m.get('very', 'real')
    assert a.exists

    b = m.get('something', 'nonexistent')
    assert not b.exists


def test_cannot_set_nonexistent_config():
    c = Config('not', 'managed')
    c.value = '23'
    assert c.value == '23'

    d = Config('actually', 'managed', exists=False)
    with pytest.raises(RuntimeError):
        d.value = '23'
