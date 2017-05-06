import pytest

from configmanager import ConfigItem, ConfigManager


def test_get():
    m = ConfigManager(
        ConfigItem('a', '1', value='a1'),
        ConfigItem('a', '2', value='a2'),
        ConfigItem('b', '1', value='b1'),
        ConfigItem('b', '2', value='b2'),
    )

    a1 = m.get('a', '1')
    assert isinstance(a1, ConfigItem)
    assert a1 == 'a1'

    assert m.get('a.1') == 'a1'
    assert m.get('a.2') == 'a2'
    assert m.get('b.1') == 'b1'
    assert m.get('b.2') == 'b2'


def test_duplicate_config_raises_value_error():
    m = ConfigManager()
    m.add(ConfigItem('a', 'b'))

    with pytest.raises(ValueError):
        m.add(ConfigItem('a', 'b'))

    m.add(ConfigItem('a', 'c'))


def test_sets_config():
    m = ConfigManager(
        ConfigItem('c', '1', type=int),
        ConfigItem('c', '2'),
    )

    m.set('c.1', '55')
    m.set('c', '2', '55')

    assert m.get('c', '1') == 55
    assert m.get('c.2') == '55'


def test_config_manager_configs_are_safe_copies():
    c1 = ConfigItem('c', '1', type=int)
    c2 = ConfigItem('c', '2', type=list)

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
        ConfigItem('a', 'b'),
        ConfigItem('a', 'c'),
        ConfigItem('a', 'd'),
        ConfigItem('x', 'y'),
        ConfigItem('x', 'z'),
    )

    assert m.a
    assert m.x
    with pytest.raises(RuntimeError):
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

    m.add(ConfigItem('a', 'b'))

    assert m.has('a', 'b')
    assert m.has('a.b')

    assert not m.has('a', 'c')
    assert not m.has('a.c')

    assert not m.has('b', 'a')
    assert not m.has('b', 'b')


def test_can_retrieve_non_existent_config():
    m = ConfigManager(
        ConfigItem('very', 'real')
    )

    a = m.get('very', 'real')
    assert a.exists

    b = m.get('something', 'nonexistent')
    assert not b.exists


def test_reset():
    m = ConfigManager(
        ConfigItem('forgettable', 'x', type=int),
        ConfigItem('forgettable', 'y', default='YES')
    )

    m.forgettable.x = 23
    m.forgettable.y = 'NO'

    assert m.forgettable.x == 23
    assert m.forgettable.y == 'NO'

    m.reset()

    assert not m.forgettable.x.has_value
    assert m.forgettable.y == 'YES'


def test_items_returns_all_config_items():
    m = ConfigManager(
        ConfigItem('a', 'aa', 'aaa'),
        ConfigItem('b', 'bb'),
        ConfigItem('a', 'aa', 'AAA'),
        ConfigItem('b', 'BB'),
    )

    assert len(m.items()) == 4
    assert m.items()[0].path == ('a', 'aa', 'aaa')
    assert m.items()[-1].path == ('b', 'BB')


def test_items_with_prefix_returns_matching_config_items():
    m = ConfigManager(
        ConfigItem('a', 'aa', 'aaa'),
        ConfigItem('b', 'bb'),
        ConfigItem('a', 'aa', 'AAA'),
        ConfigItem('b', 'BB'),
    )

    a_items = m.items('a')
    assert len(a_items) == 2
    assert a_items[0].path == ('a', 'aa', 'aaa')
    assert a_items[1].path == ('a', 'aa', 'AAA')

    a_aa_items1 = m.items('a.aa')
    a_aa_items2 = m.items('a', 'aa')
    assert a_aa_items1 == a_aa_items2
    assert len(a_aa_items1) == 2
    assert a_aa_items1[0].path == ('a', 'aa', 'aaa')
    assert a_aa_items1[1].path == ('a', 'aa', 'AAA')

    b_bb_items = m.items('b.bb')
    assert len(b_bb_items) == 1

    no_items = m.items('haha.haha')
    assert len(no_items) == 0
