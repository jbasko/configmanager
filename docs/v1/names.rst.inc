
Names, Aliases, and Paths
=========================

The examples that follow will rely on this instance of :class:`.Config`:

.. code-block:: python

    config = Config([
        ('uploads', Config([
            ('enabled', True)
        ])),
        ('greeting', 'Hello'),
        ('tmp_dir', '/tmp'),
    ])


*Name* of a configuration item or *alias* of a configuration section is a string which has to be unique in the section
to which the item or the section is added. In the example above, ``'uploads'`` is an alias for a section, ``'enabled'``
is a name, and so are ``'greeting'``, and ``'tmp_dir'``.
Note that the root section -- the configuration tree -- does not have an alias.

*Path* of an item or section is a tuple of names and aliases describing the item's or section's place in a
configuration tree. In the example above, ``('uploads',)``, ``('uploads', 'enabled')``, ``('greeting',)``,
and ``('tmp_dir',)`` are all the existing paths.

Note that the path of an item is relative to where you observe it from. If you were iterating over all paths of
``'uploads'`` section, the path of its only item would be ``('enabled',)``, not ``('uploads', 'enabled')``.

Names of items and aliases of sections have no meaning when traversing the configuration tree recursively, so iterators
that do that yield paths instead.

If you have a name of an item or an alias of a section, for example, ``greeting``, you can retrieve it from its
parent section in two ways:

.. code-block:: python

    >>> config.greeting
    <Item greeting 'Hello'>

    >>> config['greeting']
    <Item greeting 'Hello'>

To retrieve a section or an item using its path, you have to know the root section relative to which the path
was generated and use the ``[]`` notation:

.. code-block:: python

    >>> config[('greeting',)]
    <Item greeting 'Hello'>

    >>> config[('uploads',)]
    <Config uploads at 4436269600>

    >>> config[('uploads', 'enabled')]
    <Item enabled True>
