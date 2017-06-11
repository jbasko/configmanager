from configmanager import Item, ItemAttribute, Config, Section
from configmanager.meta import ConfigManagerSettings
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
    }, item_factory=CustomItem)

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


def test_make_section_attributes_point_to_values_instead_of_items():
    uploads = Section({
        'enabled': True,
        'threads': 1,
        'tmp_dir': '/tmp',
    }, configmanager_settings=ConfigManagerSettings(item_getter=lambda item, section: item.value))

    assert uploads.enabled is True
    assert uploads.threads == 1
    assert uploads.tmp_dir == '/tmp'

    # This won't work, the settings must be on the managing Config object
    config = Config({
        'uploads': uploads
    })

    assert config.uploads.enabled.is_item
    assert config.uploads.threads.is_item
    assert config.uploads.tmp_dir.is_item

    # This will work:
    config = Config({
        'uploads': uploads
    }, item_getter=lambda item, section: item.value)

    assert config.uploads.enabled is True
    assert config.uploads.threads == 1
    assert config.uploads.tmp_dir == '/tmp'

    assert config.dump_values() == {'uploads': {'enabled': True, 'threads': 1, 'tmp_dir': '/tmp'}}


def test_make_setting_section_attributes_sets_item_values_instead_of_items():
    def set_item(item=None, value=None, **kwargs):
        item.value = value

    uploads = Section({
        'enabled': True,
        'threads': 1,
        'tmp_dir': '/tmp',
    }, configmanager_settings=ConfigManagerSettings(item_setter=set_item))

    assert uploads.enabled.value is True

    uploads.enabled = 'no'
    assert uploads.enabled.value is False

