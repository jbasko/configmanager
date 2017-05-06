configmanager
=============

Welcome to **configmanager**'s documentation!

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

   >>> config.uploads.enabled = True
   >>> config.uploads.enabled.value
   True

Documentation
-------------

.. toctree::
   :maxdepth: 2

   api


