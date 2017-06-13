Iterators
=========

*configmanager* provides several handy iterators to walk through items and sections of a configuration tree (which
itself is a section).

The examples that follow will rely on this instance of :class:`.Config`:

.. code-block:: python

    config = Config([
        ('uploads', Config([
            ('enabled', True)
        ])),
        ('greeting', 'Hello'),
        ('tmp_dir', '/tmp'),
    ])


Iterable Sections
-----------------

An instance of :class:`.Config` (which is used to represent both sections and the whole configuration tree) is an
iterable, and iterating over it will yield names of sections and items contained directly in it.
Note that sub-sections aren't inspected.

.. code-block:: python

    >>> for name in config:
    ...     print(name)
    ...
    uploads
    greeting
    tmp_dir

    >>> for name in config.uploads:
    ...     print(name)
    enabled


``len()`` of a section will return number of items and sections it contains.

.. code-block:: python

    >>> len(config)
    3

    >>> len(config.uploads)
    1


``iter_all`` and ``iter_paths``
-------------------------------

:meth:`.Config.iter_all` is the main iterator that is used by all others. It yields key-value pairs where keys
are paths and values are sections or items. It accepts an optional ``recursive=`` kwarg which if set to ``True``
will make the iterator yield contents of sub-sections too.

.. code-block:: python

    >>> for path, obj in config.iter_all(recursive=True):
    ...     print(path, obj)
    ...
    ('uploads',) <Config uploads at 4436269600>
    ('uploads', 'enabled') <Item enabled True>
    ('greeting',) <Item greeting 'Hello'>
    ('tmp_dir',) <Item tmp_dir '/tmp'>

If you wish to just iterate over all available paths, you can do so with :meth:`.Config.iter_paths`:

    >>> list(config.iter_paths(recursive=True))
    [('uploads',), ('uploads', 'enabled'), ('greeting',), ('tmp_dir',)]


``.is_section`` and ``.is_item`` helpers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When traversing a configuration tree with :meth:`.Config.iter_all`, you may want to easily detect whether you are
looking at a section or an item. You can do that by inspecting ``.is_section`` and ``.is_item`` which are defined
on :class:`.Config` as well as on :class:`.Item`.

.. code-block:: python

    >>> config.is_section
    True
    >>> config.is_item
    False

    >>> config.greeting.is_section
    False
    >>> config.greeting.is_item
    True


``iter_items`` and ``iter_sections``
------------------------------------

If you know that you only care about items or only about sections, you can use
:meth:`.Config.iter_items` and :meth:`.Config.iter_sections` which accept not only ``recursive=`` kwarg,
but also ``key=`` which determines what is returned as key in key-value pairs.

By default, path of the returned item or section is used as the key:

.. code-block:: python

    >>> for path, item in config.iter_items(recursive=True):
    ...  print(path, item)
    ...
    ('uploads', 'enabled') <Item enabled True>
    ('greeting',) <Item greeting 'Hello'>
    ('tmp_dir',) <Item tmp_dir '/tmp'>

To get item names or section aliases (plain strings) as keys, use ``key='alias'`` for sections and ``key='name'``
for items.

    >>> for name, item in config.iter_items(key='name'):
    ...  print(name, item)
    ...
    greeting <Item greeting 'Hello'>
    tmp_dir <Item tmp_dir '/tmp'>

    >>> for alias, section in config.iter_sections(key='alias'):
    ...     print(alias, section)
    ...
    uploads <Config uploads at 4436269600>


Note that using ``alias`` or ``name`` as key doesn't make much sense in recursive context
(``recursive=True``) as keys yielded from one section may clash with those from another.
For example, ``('uploads', 'tmp_dir')`` would have the same key as ``('downloads', 'tmp_dir')``.
