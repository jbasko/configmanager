import pytest

from configmanager import Item, ItemAttribute, Config
from configmanager.utils import not_set


def test_custom_item_class_as_item_factory():
    class CustomItem(Item):
        is_custom = ItemAttribute(name='is_custom', default=True)

    config = Config({
        'a': {
            'b': 1,
            'c': True,
        },
        'd': 'e',
        'f': Item(default='this will not be converted'),
    }, item_factory=CustomItem)

    assert isinstance(config.a.b, CustomItem)
    assert isinstance(config.d, CustomItem)

    assert not isinstance(config.f, CustomItem)
    assert config.f.value == 'this will not be converted'
    assert isinstance(config.f, Item)


def test_user_defined_function_as_item_factory():
    calls = []

    def create_item(*args, **kwargs):
        item = Item(*args, **kwargs)
        calls.append(item.name)
        return item

    Config({
        'a': {'b': 1, 'c': True}, 'd': 'efg',
    }, item_factory=create_item)

    assert len(calls) == 3


def test_adding_new_attributes_to_item():
    # This demonstrates two ways of adding new attributes:
    # 1) by declaring ItemAttribute, 2) by creating them in initialiser

    class CustomItem(Item):
        help = ItemAttribute(name='help', default='No help available!')

        def __init__(self, *args, **kwargs):
            description = kwargs.pop('description', None)
            super(CustomItem, self).__init__(*args, **kwargs)
            self.description = description

    config = Config({
        'a': {
            'b': 1,
            'c': True,
        },
        'd': 'efg',
    }, item_factory=CustomItem)

    assert config.a.b.help
    assert config.a.b.description is None

    assert config.d.help
    assert config.d.description is None


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


def test_dynamic_item_attribute_all_caps_name():
    config = Config({
        'uploads': {
            'tmp_dir': '/tmp',
        },
        'greeting': 'Hello',
    })

    with pytest.raises(AttributeError):
        _ = config.greeting.all_caps_name

    with pytest.raises(AttributeError):
        _ = config.uploads.tmp_dir.all_caps_name

    @config.item_attribute
    def all_caps_name(item):
        return '_'.join(item.get_path()).upper()

    assert config.greeting.all_caps_name == 'GREETING'
    assert config.uploads.tmp_dir.all_caps_name == 'UPLOADS_TMP_DIR'
