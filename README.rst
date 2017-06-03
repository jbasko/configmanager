configmanager
=============

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager

Don't let standard library's configparser drive your configuration value access design. Let it do what it does
best -- parse and write configuration files. And let *configmanager* do the rest.

Main Features
-------------

* Every configuration item is an object with a type, a default value, a custom value and other metadata
* No sections required
* Any depth of sections allowed
* INI (ConfigParser), JSON, YAML formats
* click framework integration
* Designed for humans


Documentation
-------------

https://jbasko.github.io/configmanager/

Source Code and Issue Tracking
------------------------------

https://github.com/jbasko/configmanager


Quick Start
-----------

.. code-block:: shell

    pip install configmanager


.. code-block:: python

    from configmanager import Config

    config = Config({
        'uploads': {
            'threads': 1,
            'enabled': False,
            'db': {
                'user': 'root',
                'password': '',
                'hostname': 'localhost',
                'database': 'uploads',
            },
        },
        'secret': {
            '@required': True,
        }
    })

    config.json.load('defaults.json', as_defaults=True)
    config.configparser.load('env-config.ini')
    config.yaml.load('user-config.yaml')


.. code-block:: python

    >>> config.uploads.threads.type
    <_IntType ('int', 'integer')>

    >>> config.uploads.enabled.type
    <_BoolType ('bool', 'boolean')>

    >>> config.uploads.enabled.value = 'yes'
    >>> config.uploads.enabled
    <Item enabled True>
    >>> config.uploads.enabled.value
    True
    >>> config.uploads.enabled.is_default
    False
    >>> config.uploads.enabled.reset()
    >>> config.uploads.enabled
    <Item enabled False>

    >>> config.secret.value
    # ... stacktrace skipped ...
    RequiredValueMissing: secret

    >>> config.secret.get('f811b8ck-s3cr3t')
    'f811b8ck-s3cr3t'

    >>> config.secret.has_value
    False

    >>> config.dump_values(with_defaults=False)
    {}

    >>> config.dump_values()
    {'uploads': {'db': {'database': 'uploads',
       'hostname': 'localhost',
       'password': '',
       'user': 'root'},
      'enabled': False,
      'threads': 1}}

    >>> config.yaml.dump('all-config.yaml', with_defaults=True)
