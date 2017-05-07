configmanager
=============

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager

ConfigParser_ in Python standard library is for parsing configuration files, but it doesn't mean it
should drive your configuration access design.

A single item of configuration doesn't have to be a clueless string value.
It can be a self-aware object that knows its type, its default value, its description and other
things about its real place in the world.

See Documentation_.

.. code-block:: shell

    pip install configmanager


.. code-block:: python

    from configmanager import ConfigManager, ConfigItem

    config = ConfigManager(
        ConfigItem('uploads', 'tmp_dir', default='/tmp/uploads'),
        ConfigItem('uploads', 'threads', default=3, type=int),
        ConfigItem('uploads', 'enabled', default=False, type=bool),
    )

    # ConfigParser-like access
    if not config.get('uploads', 'enabled'):
        config.set('uploads', 'enabled', True)

    # The self-aware access
    if config.uploads.enabled.has_value:  # True
        config.uploads.enabled.reset()  # forgets value set by user
        print(config.uploads.enabled.value)  # will print default value False


.. _ConfigParser: https://docs.python.org/3/library/configparser.html
.. _Documentation: http://pythonhosted.org/configmanager
