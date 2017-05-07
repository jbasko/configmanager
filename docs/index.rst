configmanager
=============

Welcome to **configmanager**'!

Installation
------------

.. code-block:: shell

   pip install configmanager


Quick Start
-----------

.. code-block:: python

   >>> from configmanager import ConfigManager, ConfigItem

   >>> config = ConfigManager(
   ...     ConfigItem('uploads', 'tmp_dir', default='/tmp/uploads'),
   ...     ConfigItem('uploads', 'threads', default=3, type=int),
   ...     ConfigItem('uploads', 'enabled', default=False, type=bool),
   ... )

   >>> config.uploads.enabled.value
   False
   >>> config.uploads.enabled.has_value
   False

   >>> config.uploads.enabled = True
   >>> config.uploads.enabled.value
   True
   >>> config.uploads.enabled.default
   False
   >>> config.uploads.enabled.has_value
   True

   >>> config.uploads.threads = 5
   >>> config.uploads.threads.value
   5
   >>> config.uploads.threads.reset()
   >>> config.uploads.threads.value
   3

   >> config.uploads.threads.name
   'config.uploads.threads'
   >>> config.uploads.threads.path
   ('config, 'uploads', 'threads')



Documentation
-------------

.. toctree::
   :maxdepth: 2

   api
