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
