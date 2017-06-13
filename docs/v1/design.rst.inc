******
Design
******

These are internals. Do not use in your application code.

Key, Section, Item, and Item Value Access
=========================================

- get an item or a section: ``config._get_item(*key)``, ``config._get_section(*key)``, or ``config._get_item_or_section(key)``.
- get a key (the meaning of this depends on user settings): ``config._get_by_key(key)``.

