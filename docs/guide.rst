User Guide
==========

**THIS IS OUT OF DATE**

.. _config-item:

Config Item
-----------

An instance of :class:`.ConfigItem` represents a configurable thing in an application.
It may or may not have a default value, a value, an explicit type and other attributes.

.. code-block:: python

   >>> ConfigItem('upload', 'threads', type=int, default=1)
   <ConfigItem upload.threads 1>

Config items are only created explicitly when instantiating a :ref:`config manager <config-manager>` to declare what items
it will allow. Normally you would have :ref:`config manager <config-manager>` get them for you:

.. code-block:: python

   >>> config = ConfigManager(ConfigItem('upload', 'threads', type=int, default=1))
   >>> config.get_item('upload', 'threads')
   <ConfigItem upload.threads 1>

.. _config-value:

Config Value
------------

The *resolved* value of a :ref:`config item <config-item>`.

It could be a value set by user, or it could be the default value set on the particular :ref:`config item <config-item>`.

Note that an item is not its value.
In application code, where you require configuration value, you must use config item's value,
not the item itself.

An item may also have no value and no default value set in which case accessing
its value will raise an exception.

.. code-block:: python

   >>> item = ConfigItem('upload', 'threads', type=int, default=1)
   >>> item.value
   1
   >>> item.value = 3
   >>> item.value
   3
   >>> item.default
   1

:ref:`Config manager <config-manager>` exposes item's value directly through :meth:`.ConfigManager.get`:

.. code-block:: python

   >>> config.get('upload', 'threads')
   1

.. _config-manager:

Config Manager
--------------

An instance of :class:`.ConfigManager` keeps track of :ref:`config items <config-item>` that it accepts and
provides methods to read and write values from and to these items, as well as to and from config files
(using standard library's ``ConfigParser``).

Config manager can be created with no arguments:

.. code-block:: python

    from configmanager import ConfigManager, ConfigItem

    config = ConfigManager()


In order to let this manager read config values from a file, or to allow user set some, every supported
:ref:`config item <config-item>` must be registered with :meth:`.ConfigManager.add` or
during creation of :class:`.ConfigManager`:

.. code-block:: python

    config = ConfigManager(
        ConfigItem('upload', 'threads', default=1),
        ConfigItem('download', 'greeting'),
    )

This object is now able to parse a file like this:

.. code-block:: ini

    # config.ini

    [upload]
    threads = 5

    [download]
    greeting = Bye!

To parse the file, use :meth:`.ConfigManager.read` or :meth:`.ConfigManager.read_file` methods:

.. code-block:: python

    >>> config.read('./config.ini')


Copying Config Items Between Managers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to copy all config items from one :ref:`config-manager` to another is
to use :meth:`.ConfigManager.iter_items()`::

    config1 = ConfigManager(
         ConfigItem('upload', 'threads', default=1, value=3)
    )

    config2 = ConfigManager(*config1.iter_items())

If you don't want to keep the values (just the defaults), you can call :meth:`.ConfigManager.reset`:

    >>> config2.get('upload', 'threads').value
    3
    >>> config2.reset()
    >>> config2.get('upload', 'threads').value
    1

If the second config manager already exists, you can add config items to it with
:meth:`.ConfigManager.add`::

    map(config2.add, config1.iter_items())
