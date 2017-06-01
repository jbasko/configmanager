Exceptions
==========

All exception types raised by *configmanager* that program can recover from inherit :class:`.ConfigError`.

``NotFound``
------------

When an unknown configuration item or section is requested, a :class:`.NotFound` exception is raised.


``RequiredValueMissing``
------------------------

When an item with no default value and no custom value set is marked required and has its value requested,
a :class:`.RequiredValueMissing` exception is raised.
