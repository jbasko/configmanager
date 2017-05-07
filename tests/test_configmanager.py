import pytest
import six

from configmanager import ConfigItem, ConfigManager, UnknownConfigItem


def test_get_item_returns_config_item():
    m = ConfigManager(
        ConfigItem('a', '1', default='a1'),
        ConfigItem('a', '2', default='a2'),
        ConfigItem('b', '1', default='b1'),
        ConfigItem('b', '2', default='b2'),
    )

    a1 = m.get_item('a', '1')
    assert isinstance(a1, ConfigItem)
    assert a1.value == 'a1'

    assert m.get_item('a', '2').value == 'a2'
    assert m.get_item('b', '1').value == 'b1'
    assert m.get_item('b', '2').value == 'b2'


def test_get_returns_value_not_item():
    m = ConfigManager(
        ConfigItem('a', '1', default='a1'),
        ConfigItem('a', '2', default='a2'),
        ConfigItem('b', '1'),
        ConfigItem('b', '2', default='b2'),
    )

    a1 = m.get('a', '1')
    assert isinstance(a1, six.string_types)
    assert a1 == 'a1'
    assert not hasattr(a1, 'value')

    b2 = m.get('b', '2')
    assert b2 == 'b2'
    m.set('b', '2', 'b22')

    assert b2 == 'b2'  # shouldn't have been touched, it is a primitive type value
    assert m.get('b', '2') == 'b22'

    with pytest.raises(UnknownConfigItem):
        m.get('c', '1')

    with pytest.raises(UnknownConfigItem):
        m.get('c', '1', 'fallback does not matter -- the item does not exist')

    # Good item, no value set though
    with pytest.raises(RuntimeError):
        m.get('b', '1')

    # Provide fallback
    assert m.get('b', '1', 'bbbb') == 'bbbb'

    # Fallback for item with default value should return default value
    assert m.get('a', '2', 'aaaa') == 'a2'


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

    m.set('c', '1', '55')
    m.set('c', '2', '55')

    assert m.get('c', '1') == 55
    assert m.get('c', '2') == '55'


def test_config_manager_configs_are_safe_copies():
    c1 = ConfigItem('c', '1', type=int)
    c2 = ConfigItem('c', '2', type=list)

    m = ConfigManager(c1)

    c1.value = 5
    assert not m.get_item('c', '1').has_value

    m.get_item('c', '1').value = 66
    assert c1.value == 5

    m.add(c2)
    c2.value = [1, 2, 3]
    assert not m.get_item('c', '2').has_value

    m.get_item('c', '2').value = [4, 5, 6]
    assert c2.value == [1, 2, 3]


def test_config_section():
    m = ConfigManager(
        ConfigItem('a', 'b'),
        ConfigItem('a', 'c'),
        ConfigItem('a', 'd'),
        ConfigItem('x', 'y'),
        ConfigItem('x', 'z'),
    )

    assert isinstance(m.a, ConfigManager.ConfigPathProxy)
    assert isinstance(m.x, ConfigManager.ConfigPathProxy)

    with pytest.raises(RuntimeError):
        assert m.b.value

    assert isinstance(m.a.b, ConfigItem)
    assert m.a.b.exists
    assert not m.a.b.has_value

    m.a.b.value = 1
    assert m.a.b.value == '1'

    with pytest.raises(AttributeError):
        m.a.xx = 23


def test_has():
    m = ConfigManager()

    assert not m.has('a', 'b')
    assert not m.has('a.b')

    m.add(ConfigItem('a', 'b'))

    assert m.has('a', 'b')
    assert not m.has('a.b')

    assert not m.has('a', 'c')
    assert not m.has('a.c')

    assert not m.has('b', 'a')
    assert not m.has('b', 'b')


def test_can_retrieve_non_existent_config():
    m = ConfigManager(
        ConfigItem('very', 'real')
    )

    a = m.get_item('very', 'real')
    assert a.exists

    b = m.get_item('something', 'nonexistent')
    assert not b.exists


def test_reset():
    m = ConfigManager(
        ConfigItem('forgettable', 'x', type=int),
        ConfigItem('forgettable', 'y', default='YES')
    )

    m.forgettable.x.value = 23
    m.forgettable.y.value = 'NO'

    assert m.forgettable.x.value == 23
    assert m.forgettable.y.value == 'NO'

    m.reset()

    assert not m.forgettable.x.has_value
    assert m.forgettable.y.value == 'YES'


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
        ConfigItem('a.aa', 'haha'),
        ConfigItem('b', 'bb'),
        ConfigItem('a', 'aa', 'AAA'),
        ConfigItem('b', 'BB'),
    )

    a_items = m.items('a')
    assert len(a_items) == 2
    assert a_items[0].path == ('a', 'aa', 'aaa')
    assert a_items[1].path == ('a', 'aa', 'AAA')

    a_aa_items1 = m.items('a', 'aa')
    a_aa_items2 = m.items('a.aa')
    assert a_aa_items1 != a_aa_items2

    assert len(a_aa_items1) == 2
    assert a_aa_items1[0].path == ('a', 'aa', 'aaa')
    assert a_aa_items1[1].path == ('a', 'aa', 'AAA')

    assert len(a_aa_items2) == 1
    assert a_aa_items2[0].path == ('a.aa', 'haha')

    assert len(m.items('b')) == 2
    assert len(m.items('b', 'bb')) == 1
    assert len(m.items('b.bb')) == 0

    no_items = m.items('haha.haha')
    assert len(no_items) == 0
