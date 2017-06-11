Schemas
=======

By default, *configmanager* requires user to declare all configuration items that their application code depends on
in schemas. Our view is that if the set of available configuration items varies then it's not
really a configuration anymore.

A schema is basically a listing of what sections and items are there. The simplest way to declare a section
is to pass a dictionary to :class:`.Config` initialiser:

.. code-block:: python

    from configmanager import Config

    config = Config({
        'user': 'admin',
        'password': 'secret',
    })

The code above creates a configuration section that will manage two configuration items, ``user`` and ``password``, with
default values set to ``admin`` and ``secret`` respectively, and both declared as having type ``string`` (guessed
from the default value provided).

If all your configuration values are strings with no default values (an anti-pattern in our view), you can declare
them by passing a list of strings:

.. code-block:: python

    # anti-pattern: lots of configuration items with no defaults
    db_config = Config(['host', 'user', 'password', 'name'])

The first example was better by providing some sensible defaults, but it is not how you want to declare your
configuration. We believe that the order of items and sections in configuration matters, so a better schema
would either pass an ``OrderedDict``, or a list of ``(name, default_value)`` pairs:

.. code-block:: python

    config = Config([
        ('user', 'admin'),
        ('password', 'secret'),
    ])

Default value is not the only thing that can be specified in schema. If we pass a list of :class:`Item` instances
then we allow ourselves to be more specific:

.. code-block:: python

    from configmanager import Config, Item

    config = Config([
        ('hostname', 'localhost'),  # it's ok
        ('port', Item(type=int, required=True)),  # better
        Item('enabled', default=False),  # name can be set directly on Item
    ])

Sections can also contain other sections. In the example below, we use dictionary notation just for clarity --
you are advised to use the list of tuples notation to preserve order of sections and items.

.. code-block:: python

    import logging_config  # module in which you configure logging

    config = Config({
        'uploads': {  # this will become a Config too
            'enabled': True,
            'tmp_dir': '/tmp',
            'db': {  # and this will become a Config
                'user': 'root',
                'password': 'secret',
                'host': 'localhost',
                'name': 'exampledb',
            },
        },
        'logging': logging_config,  # a Python module is also a valid part of schema
    })

This allows to maintain multiple ``Config`` instances, one for each component of your code, which are then combined
into a containing instance only when you have a component that relies on configuration of multiple components.
