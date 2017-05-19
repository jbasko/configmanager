configmanager
=============

*Self-conscious items of configuration in Python.*

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager


Interface Status
----------------

This is being actively tested before the public interface gets finalised.
Any code reviewers welcome!

Public methods of ``Config`` and ``Item`` classes that don't start with ``cm__`` aren't expected
to change.


Features
--------

- Manager of configuration items when they have to be more than just key-value pairs.
- Configuration is organised into sections which contain items and other sections.
- Every configuration item is an object which knows its type, default value, custom value,
  the section it has been added to, whether it is required.
- Configuration item and section classes are designed for extension: easy to implement things
  like value override via environment variables, command-line prompt message to ask for a missing value,
  custom type conversions, etc.
- INI format file support through `ConfigParser` integration
- JSON format file support
- Easy to add YAML and any other dictionary-like format support


Quick Tour
----------

More documentation at http://pythonhosted.org/configmanager

.. code-block:: python

    from configmanager import Config, Item

    # Declare defaults (or load from a file)
    config = Config({
        'uploads': {
            'threads': 1,  # type will be set to int
            'tmp_dir': Item(required=True),
        },
    })

    # Load customisation
    config.configparser.read('user-config.ini')


.. code-block:: python

    >>> config.uploads.threads.value = '5'  # attribute-based access to any section or item, type conversion
    >>> config.uploads.threads.value
    5
    >>> config['uploads']['threads'].value  # key-based access is fine too
    5

    >>> config.uploads.tmp_dir.has_value
    False
    >>> config.uploads.tmp_dir.get('/tmp')  # when an item has no default and you want to supply a fallback
    '/tmp'
    >>> config.uploads.tmp_dir.set('/tmp/uploads')  # if there is a get, there must be set!
    >>> config.uploads.tmp_dir.default
    '/tmp'
    >>> config.uploads.tmp_dir.is_default
    False

    >>> config.to_dict()
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
    >>> config.uploads.to_dict(with_defaults=False)
    {'threads': 2}

    >>> config.to_dict(with_defaults=False)
    {
        'uploads': {
            'threads': 2
        }
    }

    >>> config.uploads.db = Config({'user': 'root'})
    >>> config.uploads.db.user.value
    'root'

    >>> new_config = Config({'legacy': config})
    >>> new_config.legacy.uploads.db.user.value
    'root'

