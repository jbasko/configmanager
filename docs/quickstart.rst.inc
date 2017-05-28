
***********
Quick Start
***********

1. Install the latest version from pypi.org ::

    pip install configmanager

2. Import :class:`.Config`. ::

    from configmanager import Config

3. Create your main config section and declare defaults. ::

    config = Config([
        ('greeting', 'Hello, world!'),
    ])

4. Inspect config values. ::

    >>> config.greeting.__dict__
    {'_default': 'Hello, world!',
     '_name': 'greeting',
     '_section': <Config at 4415747688>,
     '_type': str,
     '_value': <NotSet>}

    >>> config.greeting.value
    'Hello, world!'

    >>> config.dump_values()
    {'greeting': 'Hello, world!'}

5. Change config values. ::

    >>> config.greeting.value = 'Hey!'
    >>> config.greeting.__dict__
    {'_default': 'Hello, world!',
     '_name': 'greeting',
     '_section': <Config at 4415747688>,
     '_type': str,
     '_value': 'Hey!'}

    >>> config.load_values({'greeting': 'Good evening!'})
    >>> config.greeting.value
    'Good evening!'

    >>> config.dump_values()
    {'greeting': 'Good evening!'}

6. Persist the configuration. ::

    config.configparser.dump('config.ini')
