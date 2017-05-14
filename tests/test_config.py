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
