API
===

.. module:: configmanager

``ConfigManager``
-----------------

.. autoclass:: ConfigManager
    :members:
    :inherited-members:

..    :var .<section_name>: Access any :class:`.ConfigSection` of the configuration.
..    :var .<section_name>.<option_name>: Access any :class:`.ConfigItem` of the configuration.


``ConfigItem``
--------------

.. autoclass:: ConfigItem
    :members:
    :inherited-members:


``TransitionConfigManager(ConfigManager)``
------------------------------------------

.. autoclass:: TransitionConfigManager
    :inherited-members:
    :members:


``not_set`` Object
------------------

``not_set`` is a special object which is used to represent uninitialised values and
default values.
