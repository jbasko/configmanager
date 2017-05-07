User Guide
==========

.. _config-item:

Config Item
-----------

An instance of :class:`.ConfigItem` represents a configurable thing in an application.
It may or may not have a default value, a value, an explicit type and other attributes.

.. code-block:: python

   >>> ConfigItem('upload', 'threads', type=int, default=1)
   <ConfigItem upload.threads 1>

Config items are only created explicitly when instantiating a :ref:`config-manager` to declare what items
it will allow. Normally you would have :ref:`config-manager` get them for you:

.. code-block:: python

   >>> config = ConfigManager(ConfigItem('upload', 'threads', type=int, default=1))
   >>> config.get_item('upload', 'threads')
   <ConfigItem upload.threads 1>

.. _config-value:

Config Value
------------

The *resolved* value of a :ref:`config-item`.

It could be a value set by user, or it could be the default value set on the particular :ref:`config-item`.

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

.. _config-manager:

Config Manager
--------------

The key.
