configmanager
=============

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager

ConfigParser_ in Python standard library is for parsing configuration files, but it doesn't mean it
should drive your configuration access design.

A single item of configuration (a config) doesn't have to be a clueless string value.
It can be a self-aware object that knows its type, its default value, its description and other
things about its real place in the world.

See Documentation_.

::

    pip install configmanager


.. _ConfigParser: https://docs.python.org/3/library/configparser.html
.. _Documentation: http://pythonhosted.org/configmanager
