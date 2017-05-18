configmanager
=============

*Self-conscious items of configuration in Python.*

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

Interface Status
----------------

This is being actively tested before the public interface gets finalised.

Public methods of classes :class:`.Config` and :class:`.Item` that don't start with ``cm__`` aren't expected
to change much.

Quick Start
-----------

1. Install the latest version from pypi.org ::

    pip install configmanager

2. Import :class:`.Config`. ::

    from configmanager import Config

3. Create your main config section and declare defaults. ::

    config = Config({
        'greeting': 'Hello, world!',
    })

4. Inspect config values. ::

    >>> config.greeting.__dict__
    {'_default': 'Hello, world!',
     '_name': 'greeting',
     '_section': <Config at 4415747688>,
     '_type': str,
     '_value': <NotSet>}

    >>> config.greeting.value
    'Hello, world!'

    >>> config.to_dict()
    {'greeting': 'Hello, world!'}

5. Change config values. ::

    >>> config.greeting.value = 'Hey!'
    >>> config.greeting.__dict__
    {'_default': 'Hello, world!',
     '_name': 'greeting',
     '_section': <Config at 4415747688>,
     '_type': str,
     '_value': 'Hey!'}

    >>> config.read_dict({'greeting': 'Good evening!'})
    >>> config.greeting.value
    'Good evening!'

    >>> config.to_dict()
    {'greeting': 'Good evening!'}

6. Persist the configuration. ::

    config.configparser.write('config.ini')


API Reference
-------------

.. module:: configmanager


Config Object
^^^^^^^^^^^^^

.. autoclass:: Config
   :members:
   :inherited-members:


Item Object
^^^^^^^^^^^

.. autoclass:: Item
   :members:
   :inherited-members:


ConfigValueMissing Object
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ConfigValueMissing
   :members:


ConfigParserAdapter Object
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ConfigParserAdapter
   :members:
   :inherited-members:


ItemAttribute Object
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ItemAttribute
   :members:
