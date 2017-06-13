************
Introduction
************


Objectives
==========

Provide a clean, object-oriented interface to:

1. declare configuration items; organise them into a configuration tree of arbitrary depth
2. parse various configuration sources and initialise configuration items accordingly
3. read values of configuration items
4. change values of configuration items
5. write configuration to various destinations
6. enrich configuration items with additional meta information and more advanced methods of calculating values at run-time.
7. inspect meta information of configuration items

Why not just use ``ConfigParser``?
----------------------------------

``ConfigParser`` does what its name suggests -- it parses configuration files (of one certain
format).

It only starts to appear quite limited if you misuse it as a configuration manager.
By configuration manager we mean a party responsible for things like
managing a list of allowed configuration items and their defaults, loading custom configuration values from
different sources (files, command-line arguments, environment variables etc.), casting values to their right types,
providing interface to retrieve these values consistently.
Just because an instance of ``ConfigParser`` holds the data it has parsed doesn't mean it
should be used in application code to look up configuration values.

If ``ConfigParser`` is used as a configuration manager some of its limitations are:

* a configuration value is just a string which is cast to the right type only if you specifically ask to
  every time when you are looking it up.
* a configuration item (called option in ``ConfigParser``) must belong to a section.
* you can't have configuration trees deeper than one section + one option.
* it only supports INI-format files.


Key Terms and Principles
========================

Configuration of a system is a hierarchical tree of arbitrary depth in which leaf nodes are configuration items,
and non-leaf nodes are configuration sections.

Each sub-tree (section) of the tree can be regarded as a configuration of a sub-system.

Configuration can also be seen as a collection of key-value pairs in which value is a configuration item (including its
name and state), and key is the path of the item in the tree.

All referenced configuration sections and items have to be declared before they are used to stop user from referring to
non-existent, mistyped configuration paths.


Configuration Item
------------------

* has a *name*
* has a *type*
* has a *value* which is determined dynamically when requested
* may have a *default value* which is returned as its value when no custom value is set
* may have a *custom value* which overrides the default value
* may be marked as *required* in which case either a custom value or default value has to be available when item's value
  is requested.
* may have its value requested using :meth:`.Item.get` which accepts a *fallback* which is used when neither
  a default value, nor a custom value is available.
* does NOT know its path in a configuration tree
* knows the section it has been added to
* can be extended with other attributes and to consult other sources to calculate its value

Configuration Section
---------------------

* is an ordered collection of named items and named sections
* has a *name* which is assigned to it when it is added to a parent section. Root section does not have a name
