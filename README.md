[`ConfigParser`](https://docs.python.org/3/library/configparser.html) in Python standard library
is for parsing configuration files, but it doesn't mean it  should drive your configuration access design.

**configmanager** wraps each option in a `Config` instance (`c`) which can be inspected to discover:

 * default value (`c.default`)
 * actual value (`c.value`)
 * whether the option has a default value set (`c.has_default`)
 * whether the option has an override set (`c.has_value`)
 * declared type of the config option (`c.type`)

### Usage

Import the tools:
    
    from configmanager import ConfigManager, Config
    

Declare allowed configuration sections and options:

    config = ConfigManager(
        Config('uploader', 'threads', default=3, type=int),
        Config('uploader', 'output_file', default='/tmp/uploader.log'),
    )

Get a string representation of the config value:

    config.uploader.threads == 3

Or:

    config.get_config('uploader.threads') == config.get_config('uploader', 'threads') == '3'

Or, get the exact value in the right type:

    config.uploader.threads.value == config.get_config('uploader.threads').value == 3
    
Set values:

    config.uploader.threads = 4
    
Or:

    config.set_config('uploader', 'threads', 4)
    config.set_config('uploader.threads', 4)
    config.get_config('uploader.threads') = 4

Save non-default configuration to a file:

    with open('./config.ini', 'w') as f:
        config.write(f)
    
After running the code above, contents of `config.ini` are:

    [uploader]
    threads = 4

Parse a configuration file:

    with open('./config.ini') as f:
        config.read_file(f)
    
    assert config.uploader.threads.has_value
    assert config.uploader.threads == 4
    
    assert not config.uploader.has_value
    assert config.uploader.output_file == '/tmp/uploader.log'
