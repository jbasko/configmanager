#############
configmanager
#############

- `Documentation <https://jbasko.github.io/configmanager/>`_
- `Source Code and Issue Tracker on github.com <https://github.com/jbasko/configmanager>`_
- `Build Status on travis-ci.org <https://travis-ci.org/jbasko/configmanager>`_


=====================
Questions and Answers
=====================

.. contents::
    :local:


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

How do I write configuration to files?
--------------------------------------

Similarly to reading, you find the appropriate persistence adapter, and use the dump method on it:

.. code-block:: python

    config.json.dump('~/.config/helloworld/config.json', with_defaults=True)

Unless you also pass ``with_defaults=True``, ::dump:: will not include items who don't have a custom value set.

How do I export all configuration values to a dictionary?
---------------------------------------------------------

You can export effective values with :meth:`.Section.dump_values` method:

.. code-block:: python

    >>> config.dump_values()
    {'greeting': 'Hello, world!'}

By default, :meth:`.Section.dump_values` includes values for all items which have a custom value or a default value.
You can also dump just custom values with ``with_defaults=False`` which may result in an empty dictionary
if none of your configuration items have custom values.

How do I read configuration values from a dictionary?
-----------------------------------------------------

.. code-block:: python

    config.load_values({
        'greeting': 'Hey!',
    })

Where is all the richness?
--------------------------

The richness lies in configuration items:

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

How to add a dynamic attribute to all items?
--------------------------------------------

.. code-block:: python

    config = Config({'greeting': 'Hello, world!'})

    @config.item_attribute
    def all_caps_value(item=None, **kwargs):
        return item.value.upper()

    assert config.greeting.all_caps_value == 'HELLO, WORLD!'

How to do something with all configuration items?
-------------------------------------------------

If you need to work with items after the configuration tree has been fully constructed,
you can iterate over all items with ``config.iter_items()`` which can be customised in many
different ways.

.. code-block:: python

    for path, item in config.iter_items(recursive=True):
        print(path, item.is_default)

If you need to process item objects during configuration schema parsing, you can register
an ``item_added_to_section`` hook before adding schemas:

.. code-block:: python

    config = Config()

    @config.hooks.item_added_to_section
    def item_added_to_section(subject=None, section=None, **kwargs):
        print('Item {} was added to a section').format(subject.name)

    # Add schemas afterwards
    config.add_schema({'greeting': 'Hello, world!'})

How to allow item value override through an environment variable?
-----------------------------------------------------------------

If you have meaningful section names and you don't mind *configmanager*'s default naming
schema, then you can just declare the particular items with ``envvar=True``:

.. code-block:: python
    :emphasize-lines: 5,13

    # dictionary notation
    config = Config({
        'greeting': {
            '@default': 'Hello, world!',
            '@envvar': True,
        },
    })

    # same thing with object notation
    config = Config({
        'greeting': Item(
            default='Hello, world!',
            envvar=True,
        ),
    })

Now, to set a value override, your application user would have to set environment variable ``GREETING``.
Had the ``greeting`` item been declared under a section called ``hello_world``, you would have
to override it by setting ``HELLO_WORLD_GREETING``.

If this is not up to your taste, you can specify a custom environment variable name by
replacing ``envvar=True`` with something more likeable:

.. code-block:: python
    :emphasize-lines: 4

    config = Config({
        'greeting': Item(
            default='Hello, world!',
            envvar='MY_APP_GREETING',
        ),
    })

If you want to generate a custom environment variable name dynamically based on item for which
the environment variable name is requested, you can do so by overriding ``envvar_name`` attribute:

.. code-block:: python
    :emphasize-lines: 4,8-10

    config = Config({
        'greeting': {
            '@default': 'Hello, world',
            '@envvar': True,
        }
    })

    @config.item_attribute
    def envvar_name(item=None, **kwargs):
        return 'GGG_{}'.format('_'.join(item.get_path()).upper())

    assert config.greeting.envvar_name == 'GGG_GREETING'

Note that when calculating item value, ``config.greeting.envvar_name`` is only consulted if
``config.greeting.envvar`` is set to ``True``. If it is set to a string, that will be used instead.
Or, if it is set to a falsy value, environment variables won't be consulted at all.

How to handle non-existent configuration items?
-----------------------------------------------

If you request a non-existent configuration item, a :class:`.NotFound` exception is raised.
You could catch these as any other Python exception, or you could register a callback function
to be called when this exception is raised:

.. code-block:: python

    @config.hooks.not_found
    def not_found(name, section):
        print('A section or item called {} was requested, but it does not exist'.format(name))


If this function returns anything other than ``None``, the exception will not be raised.

How can I track changes of config values?
-----------------------------------------

.. code-block:: python

    >>> with config.tracking_context() as ctx:
    ...     config.greeting.value = 'Hey, what is up!'

    >>> len(ctx.changes)
    1

    >>> ctx.changes[config.greeting]
    'Hey, what is up!'
