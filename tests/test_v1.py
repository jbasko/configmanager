import pytest

from configmanager import Config, Item, ConfigValueMissing


def test_simple_config():
    # Initialisation of a config manager
    config = Config({
        'greeting': 'Hello, world!',
        'threads': 1,
        'throttling_enabled': False,
    })

    # Attribute-based and key-based access to config items
    assert config.greeting is config['greeting']

    # Every config item is an instance of Item
    assert isinstance(config.greeting, Item)

    # Value and other attribute access on Item
    assert config.greeting.value == 'Hello, world!'
    assert config.threads.value == 1
    assert config.threads.type is int
    assert config.throttling_enabled.value is False
    assert config.throttling_enabled.type is bool

    # If you are working with items which don't have default values, you can use .get() method
    # which accepts fallback value:
    assert config.greeting.get() == 'Hello, world!'
    assert config.greeting.get('Hey!') == 'Hello, world!'

    # Can check if a config item is managed by the manager
    assert 'greeting' in config
    assert 'warning' not in config

    # Can change values
    config.greeting.value = 'Good evening!'
    assert config.greeting.value == 'Good evening!'

    # Can inspect default value
    assert config.greeting.default == 'Hello, world!'

    # Can export all values to a dictionary
    assert config.to_dict() == {
        'greeting': 'Good evening!',
        'threads': 1,
        'throttling_enabled': False,
    }

    # Can iterate over all items
    items = dict(config.iter_items(recursive=True))
    assert len(items) == 3
    assert items[('greeting',)] is config.greeting
    assert items[('threads',)] is config.threads
    assert items[('throttling_enabled',)] is config.throttling_enabled

    # TODO clean up exceptions imports so we can use proper exception name here
    # Requesting unknown config raises Exception (unspecified yet)
    with pytest.raises(Exception):
        assert not config.other_things

    with pytest.raises(Exception):
        assert not config['greeting']

    # TODO Exception type
    # Cannot change item value incorrectly
    with pytest.raises(Exception):
        config.greeting = 'Bye!'

    with pytest.raises(Exception):
        config['greeting'] = 'Bye!'


def test_nested_config():
    """
    This demonstrates how an application config can be created from multiple
    sections (which in turn can be created from others).
    """

    # Declaration of a config section may be a plain dictionary
    db_config = {
        'host': 'localhost',
        'user': 'admin',
        'password': 'secret',
    }

    # Or, it may be an already functional instance of Config
    server_config = Config({
        'port': 8080,
    })

    # Also, it can be a Python module (actual module instance), -- not shown here
    # or a class:
    class ClientConfig:
        timeout = 10

    #
    # All these sections can be combined into one config:
    #
    config = Config({
        'db': db_config,
        'server': server_config,
        'client': ClientConfig,  # a class, not an instance
        'greeting': 'Hello',  # and you can have plain config items next to sections
    })

    # You can load values
    assert config.client.timeout.value == 10
    assert config.greeting.value == 'Hello'

    # You can change values and they will be converted to the right type if possible
    config.client.timeout.value = '20'
    assert config.client.timeout.value == 20

    # Your original declarations are safe -- db_config dictionary won't be changed
    config.db.user.value = 'root'
    assert config.db.user.value == 'root'
    assert db_config['user'] == 'admin'

    # You can also change values by reading them from a dictionary.
    # Unknown names will be ignored unless you pass as_defaults=True
    # but in that case you will overwrite any previously existing items.
    config.read_dict({'greeting': 'Good morning!', 'comments': {'enabled': False}})
    assert config.greeting.value == 'Good morning!'
    assert 'comments' not in config

    # You can check if config value is the default value
    assert not config.db.user.is_default
    assert config.server.port.is_default

    # Or if it has any value at all
    assert config.server.port.has_value

    # Iterate over all items (recursively)
    all = dict(config.iter_items(recursive=True))
    assert all[('db', 'host')] is config.db.host
    assert all[('server', 'port')] is config.server.port

    # Export all values
    config_dict = config.to_dict()
    assert config_dict['db'] == {'host': 'localhost', 'user': 'root', 'password': 'secret'}

    # Each section is a Config instance too, so you can export those separately too:
    assert config.server.to_dict() == config_dict['server']

    # You can reset individual items to their default values
    assert config.db.user.value == 'root'
    config.db.user.reset()
    assert config.db.user.value == 'admin'

    # Or sections
    config.db.user.value = 'root_again'
    assert config.db.user.value == 'root_again'
    config.db.reset()
    assert config.db.user.value == 'admin'

    # Or you can reset all configuration and you can make sure all values match defaults
    assert config.client.timeout.value == 20
    assert not config.is_default
    config.reset()
    assert config.client.timeout.value == 10
    assert config.is_default


def test_exceptions():
    # Items marked as required raise ConfigValueMissing when their value is accessed
    password = Item('password', required=True)
    with pytest.raises(ConfigValueMissing):
        assert not password.value


def test_configparser_integration(tmpdir):
    defaults_ini = tmpdir.join('defaults.ini')
    defaults_ini.write('')
    defaults_ini_path = defaults_ini.strpath

    custom_ini = tmpdir.join('custom.ini')
    custom_ini.write('')
    custom_ini_path = custom_ini.strpath

    # Config sections expose ConfigParser adapter as configparser property:
    config = Config()

    # assuming that defaults.ini exists, this would initialise Config
    # with all values mentioned in defaults.ini set as defaults.
    # Just like with ConfigParser, this won't fail if the file does not exist.
    config.configparser.load(defaults_ini_path, as_defaults=True)

    # if you have already declared defaults, you can load custom
    # configuration without specifying as_defaults=True:
    config.configparser.load(custom_ini_path)

    # other ConfigParser-like methods such as read_dict, loads, read_file are provided too.
    # when you are done setting config values, you can dump them to file too.
    config.configparser.dump(custom_ini_path)

    # Note that default values won't be written unless you explicitly request it
    # by passing with_defaults=True
    config.configparser.dump(custom_ini_path, with_defaults=True)
