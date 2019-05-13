configmanager
=============

**Update on 2019-05-13**: Version 1.35 and above require Python 3.6+.

**Update on 2018-10-20**: I no longer use this library. It tries to do too many things. It was written in
Python 2.7 and made work with Python 3. With type hints, dataclasses, and many other cool features in Python 3.6+
you can express the same things in a much nicer way than this.

----

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


Documentation
-------------

https://jbasko.github.io/configmanager/

Source Code and Issue Tracking
------------------------------

https://github.com/jbasko/configmanager

Quick Start
-----------

Install from Python Package index with ``pip install configmanager``.

Declare your configuration, the sources, and off you go.
Remember, every configuration item is an object, not just a plain
configuration value.
If you don't need the rich features of configuration items,
use ``configmanager.PlainConfig`` instead.

.. code-block:: python

    import warnings
    from configmanager import Config

    config = Config({
        'uploads': {
            'threads': 1,
            'enabled': False,
            'db': {
                'user': 'root',
                'password': {
                    '@default': 'root',
                    '@envvar': 'MY_UPLOADER_DB_PASSWORD',
                },
            }
        }
    }, load_sources=[
        '/etc/my-uploader/config.ini',
        '~/.config/my-uploader/config.json',
    ], auto_load=True)

    if config.uploads.db.user.is_default:
        warnings.warn('Using default db user!')

    if config.uploads.enabled.get():
        connect_to_database(
            user=config.uploads.db.user.get(),
            password=config.uploads.db.password.get(),
        )
