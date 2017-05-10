configmanager
=============

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager

An attempt to take the best of configparser_ found in Python 3.2+ (and
backported to Python 2.7-3.2 thanks to `configparser package`_) and make each config item
a first class object which knows its type, default value, whether it has a value or not,
knows an environment variable which can override it, and other attributes.

Whereas ``ConfigParser`` is designed to edit config files and work with two-dimensional
config items identified by `section` and `option`, ``ConfigManager`` (the main class provided
by this package) aims at managing access to config values with any `path` and their meta information
regardless of how they are persisted.

I have caught myself using ``ConfigParser`` as a generic config manager even when config
values are not persisted to files. For example, in a command line script setting,
a config value may exist just for the duration of script execution as a merge of default
value and an override supplied via an optional command line argument.


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

    # Basic, ConfigParser-style access
    if not config.get('uploads', 'enabled'):
        config.set('uploads', 'enabled', True)

    # Value access
    if config.v.uploads.enabled:
        config.v.uploads.enabled = False

    # Config item access
    if config.t.uploads.enabled.value is False:
        config.t.uploads.enabled.value = True

    # Section access
    uploads = config.s.uploads
    if uploads.get('enabled'):
        uploads.set('enabled', False)


.. _ConfigParser: https://docs.python.org/3/library/configparser.html
.. _Documentation: http://pythonhosted.org/configmanager
.. _configparser package: https://pypi.python.org/pypi/configparser
