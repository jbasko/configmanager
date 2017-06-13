#############
configmanager
#############

- `Documentation <https://jbasko.github.io/configmanager/>`_
- `Source Code and Issue Tracker on github.com <https://github.com/jbasko/configmanager>`_
- `Build Status on travis-ci.org <https://travis-ci.org/jbasko/configmanager>`_

=====================
Questions and Answers
=====================


What is it?
-----------

- If you come from the world of Django, it is the ``settings`` object you import from ``django.conf``.

- If you have built one before, you probably built it around standard library's ``ConfigParser``,
  or perhaps just a plain dictionary.

- It is the party responsible for loading the configuration from different sources and for making it accessible
  to the rest of your application through uniform interface.


How is it different from others?
--------------------------------

- It requires you to declare your configuration schema beforehand.

- Every configuration item is a rich object with a type, a name, a default value, a custom value,
  and other attributes. All these and other, easy-to-add attributes can be used to calculate configuration item's
  effective value when application requests it.

- It allows you to choose how you will access values of configuration items: through dictionary-like access,
  through attributes, or through method calls.

- It does not limit you to a specific configuration file format, or to a specific limit of configuration tree depth.

- It can be easily composed of other configuration managers.

- It does not support value interpolation.


How do I install it?
--------------------

.. code-block:: shell

    pip install configmanager


How do I use it?
----------------

It depends on what you are after. If you are just looking for something to parse different files and put the
values in one object, then you want to use ``PlainConfig`` interface:

.. code-block:: python

    >>> from configmanager import PlainConfig

    >>> config = PlainConfig(schema={'greeting': 'Hello, world!'})

    >>> config.greeting
    'Hello, world!'

If you are after the rich configuration item functionality which *configmanager* was designed for, then you
want to use ``Config`` interface:

.. code-block:: python

    >>> from configmanager import Config

    >>> config = Config(schema={'greeting': 'Hello, world!'})

    >>> config.greeting.value
    'Hello, world!'

Further answers will assume that you are using the rich ``Config`` interface.

How do I read configuration from files?
---------------------------------------

If there is a list of locations that you want to always inspect when initialising the configuration manager, you
can pass them using the ``load_sources=`` setting of *configmanager*. Make sure you also enable auto-loading:

.. code-block:: python
    :emphasize-lines: 3-4

    config = Config(
        schema={'greeting': 'Hello, world'},
        load_sources=['/etc/helloworld/config.ini', '~/.config/helloworld/config.json'],
        auto_load=True,
    )

If you want to reload these same sources later, or load them for the first time because you didn't specify
``auto_load=True``, you can do so with ``config.load()``.

To load configuration from a specific file at a later point in manager's lifetime, you can use
``load(source)`` method on the appropriate persistence adapter:

.. code-block:: python

    config.configparser.load('/etc/helloworld/config.ini')
    config.yaml.load('~/.config/helloworld/config.yaml')
    config.json.load('~/.config/helloworld/config.json')

How do I get all configuration values?
--------------------------------------

.. code-block:: python

    >>> config.dump_values()
    {'greeting': 'Hello, world!'}

Where is all the power?
-----------------------

Don't look for power in the configuration values because the power lies in configuration items
which in *configmanager* are rich objects:

.. code-block:: python

    >>> greeting = config.greeting

    >>> greeting
    <Item greeting 'Hello, world!'>

    >>> greeting.has_value
    True

    >>> greeting.default
    'Hello, world!'

    >>> greeting.is_default
    True

    >>> greeting.value = 'Hey!'
    >>> greeting.value
    'Hey!'

    >>> greeting.is_default
    False

    >>> greeting.reset()
    >>> greeting.value
    'Hello, world!'

How to create an item with no default value?
--------------------------------------------

In normal circumstances, we consider a configuration item with no default value an anti-pattern.
However, if you want to force your application user to provide a value for an item for which no default value would
be acceptable, for example, it can be done either by using an explicit ``Item`` instance in configuration schema,
or by using dictionary notation with meta keys:

.. code-block:: python

    # Option 1
    from configmanager import Item
    config.add_schema({'enabled': Item(required=True)})

    # Option 2
    config.add_schema({'enabled': {'@required': True}})

How to provide a fallback value for an item with no default value?
------------------------------------------------------------------

Once you have a reference to the item, you can call its ``.get(fallback)`` method:

    >>> config.enabled.get(False)
    False

    >>> config.enabled.value
    # .. stack-trace skipped ..
    configmanager.exceptions.RequiredValueMissing: enabled

