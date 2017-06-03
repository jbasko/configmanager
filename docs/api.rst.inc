*************
API Reference
*************

.. module:: configmanager

Public Interface
================

``Config``
----------

.. autoclass:: Config
   :members: iter_items, iter_sections, iter_all, iter_paths,
      load_values, dump_values,
      reset,
      is_default,
      section, alias,
      configparser, json, yaml


``Item``
--------

.. autoclass:: Item
   :members:
   :inherited-members:


``ConfigPersistenceAdapter``
----------------------------

.. autoclass:: ConfigPersistenceAdapter
   :members:
   :inherited-members:

Exceptions
----------

``ConfigError``
^^^^^^^^^^^^^^^

.. autoclass:: ConfigError
   :members:


``NotFound``
^^^^^^^^^^^^

.. autoclass:: NotFound
   :members:


``RequiredValueMissing``
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: RequiredValueMissing
   :members:
