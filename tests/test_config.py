import pytest

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


def test_repr_of_config():
    config = Config()
    assert repr(config).startswith('<Config at ')


def test_assigning_nameless_item_directly_to_config_should_set_its_name():
    config = Config()
    config.dummy = Config()
    config.dummy.x = Item(value=5)
    assert config.dummy.x.name == 'x'

    config.dummy['y'] = Item(default=True)
    assert config.dummy.y.name == 'y'

    assert config.to_dict() == {'dummy': {'x': 5, 'y': True}}


def test_assigning_item_with_name_directly_to_config_should_preserve_its_name():
    # This is debatable, but assuming that user wants to use
    # attribute access as much as possible, this should allow them to.

    config = Config()
    config.dummy = Config()

    config.dummy.a_b = Item(name='a.b', value='AB')
    assert config.dummy.a_b.name == 'a.b'
    assert config.dummy['a_b']
    assert 'a_b' in config.dummy
    assert 'a.b' in config.dummy

    config.dummy['w'] = Item(name='www', value=6)
    assert 'www' in config.dummy
    assert config.dummy.w.name == 'www'
    assert config.dummy.www.name == 'www'

    assert config.to_dict() == {'dummy': {'a.b': 'AB', 'www': 6}}

    all_dummies = list(config.dummy.iter_items())
    assert len(all_dummies) == 2

    items = dict(config.dummy.iter_items())
    assert ('a.b',) in items
    assert ('a_b',) not in items
    assert ('www',) in items
    assert ('w',) not in items


def test_item_name_and_alias_must_be_a_string():
    config = Config()

    with pytest.raises(TypeError):
        config.x = Item(name=5)

    with pytest.raises(TypeError):
        config[5] = Item()

    with pytest.raises(TypeError):
        config[5] = Item(name='x')


def test_section_name_must_be_a_string():
    config = Config()

    with pytest.raises(TypeError):
        config[5] = Config()
