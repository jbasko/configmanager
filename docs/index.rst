:tocdepth: 5

configmanager
=============

Welcome to **configmanager**'s documentation.

Install it from pypi.org:

.. code-block:: shell

   pip install configmanager

And you are ready to go:

.. code-block:: python

   >>> from configmanager import ConfigItem, ConfigManager

   >>> config = ConfigManager(
   ...    ConfigItem('standard', 'greeting', 'Hello, world!')
   ... )
   >>> config.read('./config.ini')

   >>> config.standard.greeting.has_value
   False
   >>> config.standard.greeting.has_default
   True
   >>> config.standard.greeting.value
   'Hello, world!'

   >>> config.standard.greeting.value = 'Hey!'
   >>> config.standard.greeting.value
   'Hey!'
   >>> config.standard.greeting.default
   'Hello, world!'

   >>> config.standard.write('./config.ini')


.. toctree::
   :maxdepth: 3

   guide


.. toctree::
   :maxdepth: 3

   api
