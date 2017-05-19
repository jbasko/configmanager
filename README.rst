configmanager
=============

*Self-conscious items of configuration in Python.*

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager


Features
--------

- Manager of configuration items when they have to be more than just key-value pairs.
- Configuration is organised into sections which contain items and other sections.
- Each configuration item is an object which knows and respects its type, default value, custom value,
  the section it has been added to, whether it is required.
- Configuration item and section classes are designed for extension: easy to implement things
  like value override via environment variables, command-line prompt message to ask for a missing value,
  custom type conversions, etc.
- `ConfigParser` integration.
- Easy to use with JSON, YAML, and any other format that can be easily converted to and from dictionaries.


Quick Tour
----------

.. code-block:: python

    from configmanager import Config, Item

    # Declare defaults (or load from a file)
    config = Config({
        'uploads': {
            'threads': 1,
            'tmp_dir': Item(required=True),
        },
    })

    # Load customisation
    config.configparser.read('user-config.ini')


.. code-block:: python

    >>> config.uploads.threads.value = '5'  # attribute-based access to any section or item
    >>> config.uploads.threads.value
    5
    >>> config['uploads']['threads'].value  # key-based access is fine too
    5
    >>> config.uploads.tmp_dir.get('/tmp')
    '/tmp'
    >>> config.uploads.tmp_dir.has_value
    False
    >>> config.uploads.tmp_dir.set('/tmp/uploads')
    >>> config.uploads.tmp_dir.default
    '/tmp'
    >>> config.uploads.tmp_dir.is_default
    False
    >>> config.uploads.tmp_dir.to_dict()
    {
        'uploads': {
            'threads': 5,
            'tmp_dir': '/tmp/uploads',
        }
    }
    >>> config.reset()
    >>> config.to_dict()
    {}
    >>> config.uploads.read_dict({'threads': '2'})
    >>> config.uploads.to_dict()
    {'threads': 2}


The depth of config tree is not limited.

.. code-block:: python

    >>> config.uploads.db = Config({'user': 'root'})
    >>> config.uploads.db.user.value
    'root'

    >>> app_config = Config({'legacy': config})
    >>> app_config.legacy.uploads.db.user.value
    'root'


More documentation at http://pythonhosted.org/configmanager
