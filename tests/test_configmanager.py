import pytest
import six

from configmanager import ConfigItem, ConfigManager, UnknownConfigItem, ConfigValueMissing

from configmanager.v1 import Config, Item


def test_items_are_created_using_the_assigned_cm__item_cls():
    class CustomItem(Item):
        pass

    class CustomConfig(Config):
        cm__item_cls = CustomItem

    config = CustomConfig({
        'a': {'b': {'c': {'d': 1, 'e': '2', 'f': True}}},
        'g': False,
    })

    assert isinstance(config, CustomConfig)
    assert isinstance(config.g, CustomItem)
    assert isinstance(config.a, CustomConfig)
    assert isinstance(config.a.b.c, CustomConfig)
    assert isinstance(config.a.b.c.d, CustomItem)


def test_reset_resets_values_to_defaults():
    config = Config({
        'x': Item(type=int),
        'y': Item(default='YES')
    })

    config.x.value = 23
    config.y.value = 'NO'

    assert config.x.value == 23
    assert config.y.value == 'NO'

    config.reset()

    assert config.x.is_default
    assert config.y.value == 'YES'


def test_can_add_items_to_default_section_and_set_their_value_without_naming_section():
    m = ConfigManager()

    assert not m.has('a')
    with pytest.raises(UnknownConfigItem):
        m.get_item('a')

    m.add('a', default=0, type=int)
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

    n = ConfigManager(*m.iter_items())
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


def test_is_default_returns_true_if_all_values_are_default():
    m = ConfigManager()
    assert m.is_default

    m.add('a', 'b')
    assert m.is_default

    m.set('a', 'b', 'haha')
    assert not m.is_default

    m.reset()
    assert m.is_default

    m.add('x', 'y', default='haha')
    assert m.is_default

    m.set('x', 'y', 'hihi')
    assert not m.is_default

    m.set('x', 'y', 'haha')
    assert m.is_default
