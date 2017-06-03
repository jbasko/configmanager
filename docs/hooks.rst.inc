Hooks
=====

Hooking is a mechanism that allows customisation of a program behaviour by registering callbacks that get called
on certain events.
This is the recommended way to extend *configmanager*, and is much simpler than creating new classes that inherit from
:class:`.Config` or :class:`.Item`.

To hook into *configmanager*, you just have to write a function and register it on a section with the appropriate hook
event by decorating it. Following hook events are defined:

- ``not_found`` -- when a name is not found in a section
- ``added_to_section`` -- *in development*
- ``value_changed`` -- *in development*

Callback functions should accept ``**kwargs`` and should return ``None`` unless they want to cancel
other callback functions.

.. code-block:: python

    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    @config.hooks.not_found
    def callback(**kwargs):
        print('Something happened')

``not_found`` is the bit where you specify which hook you are registering the callback with.

You can register hooks on instances of :class:`.Config` and they will apply to all sub-sections unless a
sub-section has its own hooks registry. *This might change in future.*

.. code-block:: python

    >>> config.hooks is config.uploads.hooks
    True

    >>> config.hooks is config.uploads.db.hooks
    True


``<config>.hooks.not_found``
----------------------------

``not_found`` callbacks are called when user requests a non-existent item or section.

Due to *configmanager*'s design it is impossible to tell whether user is requesting a section or an item.
As a convention, it is fair to assume that user was requesting an item rather than a section.

Callback is passed two **kwargs**:

- ``name=``, the name that was requested and was not found
- ``section=``, the section in which the name was requested

If a ``not_found`` callback returns something that is not ``None``, all sub-sequent ``not_found`` callbacks
will be skipped.

This hook can be used to implement automatic item creation if you are not happy with *configmanager*'s
convention of requiring all configuration items to be declared before referencing them:

.. code-block:: python

    config = Config()

    @config.hooks.not_found
    def auto_create_missing_items(section=None, name=None, **kwargs):
        item = section.create_item(name=name)
        section.add_item(item.name, item)
        return item


This allows you to do the following now:

.. code-block:: python

    >>> config.greeting
    <Item greeting <NotSet>>

    >>> config.greeting.get('Hello')
    'Hello'

    >>> config.greeting.value = 'Good morning!'
    >>> config.greeting.get('Hello')
    'Good morning!
