configmanager
=============

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager

An attempt to take the best of configparser_ found in Python 3.2+ (and
backported to Python 2.7-3.2 thanks to `configparser package`_) and make each config item
a first class object which knows its type, default value, whether it has a value or not,
knows an environment variable which can override it, and other attributes.


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
.. _configparser package: https://pypi.python.org/pypi/configparser
