configmanager
=============

*Self-conscious items of configuration in Python.*

.. image:: https://travis-ci.org/jbasko/configmanager.svg?branch=master
    :target: https://travis-ci.org/jbasko/configmanager

Features
--------

- Manager of configuration items when they have to be more than just key-value pairs.
- Configuration is organised into sections which contain items and other sections.
- Each configuration item is an object which knows and respects its type, default value, custom value,
  the section it has been added to, whether it is required.
- Configuration item and section classes are designed for extension: easy to implement things
  like value override via environment variables, command-line prompt message to ask for a missing value,
  custom type conversions, etc.
- `ConfigParser` integration.
- Easy to use with JSON, YAML, and any other format that can be easily converted to and from dictionaries.


More documentation at http://pythonhosted.org/configmanager
