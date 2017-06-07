from configmanager import Item, ItemAttribute, Config
from configmanager.utils import not_set


def test_allow_passing_item_class_to_config_on_creation():
    class CustomItem(Item):
        is_custom = ItemAttribute(name='is_custom', default=True)

    config = Config({
        'a': {
            'b': 1,
            'c': True,
        },
        'd': 'e',
        'f': Item(default='this will not be converted'),
    }, item_cls=CustomItem)

    assert isinstance(config.a.b, CustomItem)
    assert isinstance(config.d, CustomItem)

    assert not isinstance(config.f, CustomItem)
    assert config.f.value == 'this will not be converted'
    assert isinstance(config.f, Item)


def test_extending_item_class(monkeypatch):
    import os

    class EnvvarBackedItem(Item):
        """
        An item class that allows user to specify overrides via environment variables
        which take precedence over any other sources of config value.
        """

        envvar = ItemAttribute(name='envvar')

        def get(self, fallback=not_set):
            if self.envvar and self.envvar in os.environ:
                return self.type.deserialize(os.environ[self.envvar])
            return super(EnvvarBackedItem, self).get(fallback=fallback)

    config = Config({
        'greeting': EnvvarBackedItem(envvar='GREETING'),
        'threads': EnvvarBackedItem(type=int, envvar='THREADS'),
        'joy_enabled': EnvvarBackedItem(type=bool, envvar='JOY_ENABLED'),
    })

    assert config.greeting.get() is not_set

    monkeypatch.setenv('GREETING', 'Hello')
    assert config.greeting.get() == 'Hello'

    assert config.threads.get() is not_set
    monkeypatch.setenv('THREADS', '5')
    assert config.threads.get() == 5

    assert config.joy_enabled.get() is not_set
    monkeypatch.setenv('JOY_ENABLED', 'yes')
    assert config.joy_enabled.get() is True
