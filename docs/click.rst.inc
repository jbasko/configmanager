click Integration
=================

click_ is the best framework out there to create usable command-line interfaces with readable code.
If you are a *click* user, you will find it easy to make your options and arguments fall back to
configuration items when user does not specify values for them in the command line.

*configmanager* dependencies don't include *click* package as it is an optional feature. To install *configmanger*
with *click*::

    pip install configmanager[click]

In your *click* command definition, instead of using ``click.option`` and ``click.argument``,
use ``<config>.click.option`` and ``<config>.click.argument`` where ``<config>`` is your instance of
:class:`.Config`.

To specify which configuration item is to be used as a fallback, pass it as the last positional argument to
``<config>.click.option`` or ``<config>.click.argument``.

.. code-block:: python

    import click
    from configmanager import Config


    config = Config({
        'greeting': 'Hello!',
    })


    @click.command()
    @config.click.option('--greeting', config.greeting)
    def say_hello(greeting):
        click.echo(greeting)


    if __name__ == '__main__':
        say_hello()


Note that if you are using :class:`.PlainConfig`, you will have to pass ``config.get_item('greeting')`` to
``@config.click.option`` because ``config.greeting`` would be just the primitive value.

If you now run this simple program it will say ``Hello!`` by default and whatever you supply with ``--greeting``
otherwise.

Note that in *click*, arguments are not meant to be optional (but they can if they are marked with
``required=False``). Since a fallback makes sense only for optional input, you will have to mark your arguments
with ``required=False`` if you want them to fall back to configuration items:

.. code-block:: python

    @click.command()
    @config.click.argument('greeting', config.greeting, required=False)
    def say_hello(greeting):
        click.echo(greeting)


.. _click: http://click.pocoo.org/6/
