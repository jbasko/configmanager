import pytest
import six

from configmanager import ConfigItem, ConfigManager, UnknownConfigItem, ConfigValueNotSet


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
    with pytest.raises(ConfigValueNotSet):
        m.get('b', '1')

    # Provide fallback
    assert m.get('b', '1', 'bbbb') == 'bbbb'

    # Fallback for item with default value should return default value
    assert m.get('a', '2', 'aaaa') == 'a2'


@pytest.mark.parametrize('method', ['get', 'has', 'get_item', 'set'])
def test_basic_accessors_with_no_path_raise_value_error(method):
    m = ConfigManager()

    with pytest.raises(ValueError):
        getattr(m, method)()

    m.add(ConfigItem('a', 'b'))

    with pytest.raises(ValueError):
        getattr(m, method)()


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


def test_cannot_retrieve_non_existent_config():
    m = ConfigManager(
        ConfigItem('very', 'real')
    )

    m.get_item('very', 'real')
    assert m.has('very', 'real')

    with pytest.raises(UnknownConfigItem):
        m.get_item('something', 'nonexistent')

    assert not m.has('something', 'nonexistent')


def test_reset():
    m = ConfigManager(
        ConfigItem('forgettable', 'x', type=int),
        ConfigItem('forgettable', 'y', default='YES')
    )

    m.set('forgettable', 'x', 23)
    m.set('forgettable', 'y', 'NO')

    assert m.get('forgettable', 'x') == 23
    assert m.get('forgettable', 'y') == 'NO'

    m.reset()

    assert not m.get_item('forgettable', 'x').has_value
    assert m.get('forgettable', 'y') == 'YES'


def test_can_add_items_to_default_section_and_set_their_value_without_naming_section():
    m = ConfigManager()

    assert not m.has('a')
    with pytest.raises(UnknownConfigItem):
        m.get_item('a')

    m.add(ConfigItem('a', default=0, type=int))
    assert m.has('a')
    assert m.has(m.default_section, 'a')

    assert m.get_item('a')
    assert m.get('a') == 0

    m.set('a', 5)
    assert m.get('a') == 5


def test_export_empty_config_manager():
    m = ConfigManager()
    assert m.export() == []


def test_export_config_manager_with_no_values():
    m = ConfigManager(ConfigItem('a', 'x'))
    assert m.export() == []


def test_export_config_manager_with_default_section_item():
    m = ConfigManager(
        ConfigItem('a')
    )
    m.set('a', '5')
    assert m.get('a') == '5'
    assert m.export() == [('DEFAULT.a', '5')]

    m.reset()
    assert m.export() == []


def test_export_config_manager_with_multiple_sections_and_defaults():
    m = ConfigManager(
        ConfigItem('a', 'x', default='xoxo'),
        ConfigItem('a', 'y', default='yaya'),
        ConfigItem('b', 'm'),
        ConfigItem('b', 'n', default='nono'),
    )
    assert len(m.export()) == 3
    assert m.export() == [('a.x', 'xoxo'), ('a.y', 'yaya'), ('b.n', 'nono')]

    m.set('a', 'y', 'YEYE')
    assert m.export() == [('a.x', 'xoxo'), ('a.y', 'YEYE'), ('b.n', 'nono')]


def test_exports_configs_with_prefix():
    m = ConfigManager(
        ConfigItem('a', 'x', default='xoxo'),
        ConfigItem('a', 'y', default='yaya'),
        ConfigItem('b', 'm'),
        ConfigItem('b', 'n', default='nono'),
    )
    m.set('a', 'x', 'XIXI')
    assert m.export('a') == [('x', 'XIXI'), ('y', 'yaya')]
    assert m.export('b') == [('n', 'nono')]


def test_exports_configs_with_deep_paths():
    m = ConfigManager(
        ConfigItem('a', 'x', 'i', default='axi'),
        ConfigItem('a', 'x', 'ii', default='axii'),
        ConfigItem('a', 'y', 'i', default='ayi'),
        ConfigItem('a', 'y', 'ii', default='ayii')
    )

    assert len(m.export()) == 4
    assert m.export()[0] == ('a.x.i', 'axi')

    assert m.export('a')[0] == ('x.i', 'axi')

    assert m.export('a', 'y')[1] == ('ii', 'ayii')


def test_copying_items_between_managers():
    m = ConfigManager(
        ConfigItem('a', 'x'),
        ConfigItem('a', 'y'),
        ConfigItem('b', 'bb', 'm'),
        ConfigItem('b', 'bb', 'n'),
        ConfigItem('b', 'bbbb', 'p'),
        ConfigItem('b', 'bbbb', 'q'),
    )

    n = ConfigManager(*m.find_items())
    assert m.export() == n.export()

    m.set('a', 'x', 'xaxa')
    assert m.get('a', 'x') == 'xaxa'
    assert not n.get_item('a', 'x').has_value

    n.set('a', 'x', 'XAXA')
    assert m.get('a', 'x') == 'xaxa'
    assert n.get('a', 'x') == 'XAXA'

    n.reset()
    assert m.get('a', 'x') == 'xaxa'
    assert not n.get_item('a', 'x').has_value


def test_read_as_defaults_treats_all_values_as_declarations(tmpdir):
    path = tmpdir.join('conf.ini').strpath
    with open(path, 'w') as f:
        f.write('[uploads]\nthreads = 5\nenabled = no\n')
        f.write('[messages]\ngreeting = Hello, home!\n')

    m = ConfigManager()
    m.read(path, as_defaults=True)

    assert m.has('uploads', 'threads')
    assert m.has('uploads', 'enabled')
    assert not m.has('uploads', 'something_else')
    assert m.has('messages', 'greeting')

    assert m.get('uploads', 'threads') == '5'
    assert m.get('uploads', 'enabled') == 'no'
    assert m.get('messages', 'greeting') == 'Hello, home!'

    # Reading again with as_defaults=True should not change the values, only the defaults
    m.set('uploads', 'threads', '55')
    m.read(path, as_defaults=True)
    assert m.get('uploads', 'threads') == '55'
    assert m.get_item('uploads', 'threads').default == '5'

    # But reading with as_defaults=False should change the value
    m.read(path)
    assert m.get('uploads', 'threads') == '5'
    assert m.get_item('uploads', 'threads').default == '5'
