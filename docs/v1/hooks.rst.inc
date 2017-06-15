Hooks
=====


``Config.hooks.not_found``
--------------------------

- ``name``, the name that was requested and was not found
- ``section``, the section in which the name was requested


``Config.hooks.item_added_to_section``
--------------------------------------

- ``subject`` - item which was added
- ``section`` - section to which the ``subject`` item was added
- ``alias`` - name under which the ``subject`` item was added


``Config.hooks.section_added_to_section``
-----------------------------------------

- ``subject`` - subject which was added
- ``section`` - parent section to which the ``subject`` section was added
- ``alias`` - name under which the ``subject`` section was added


``Config.hooks.item_value_changed``
-----------------------------------

- ``item``
- ``old_value``
- ``new_value``


How to disable hooks?
---------------------

Hooks are enabled by default whenever a first hook is registered, but can be manually disabled
by passing ``hooks_enabled=False`` when initialising :class:`.Config`.

