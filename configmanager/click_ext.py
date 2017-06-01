"""
An extension to the click framework to allow declaring
options and arguments (in click lingo) that fall back to
*configmanager*.
"""


def _config_parameter(args, kwargs):
    config_item = args[-1]
    assert config_item.is_item

    original_callback = kwargs.pop('callback', None)

    def callback(ctx, param, value):
        if value is None and config_item.has_value:
            value = config_item.value
        if original_callback:
            original_callback(ctx, param, value)
        return value

    kwargs['callback'] = callback

    if config_item.type.builtin_types:
        kwargs.setdefault('type', config_item.type.builtin_types[0])

    return args[:-1], kwargs


class ClickExtension(object):
    def __init__(self, config):
        self._config = config

        import click
        self._click = click

    def __getattr__(self, item):
        return getattr(self._click, item)

    def option(self, *args, **kwargs):
        """
        Registers a click.option which falls back to a configmanager Item
        if user hasn't provided a value in the command line.

        Item must be the last of ``args``.

        Examples::

            config = Config({'greeting': 'Hello'})

            @click.command()
            @config.click.option('--greeting', config.greeting)
            def say_hello(greeting):
                click.echo(greeting)

        """
        args, kwargs = _config_parameter(args, kwargs)
        return self._click.option(*args, **kwargs)

    def argument(self, *args, **kwargs):
        """
        Registers a click.argument which falls back to a configmanager Item
        if user hasn't provided a value in the command line.

        Item must be the last of ``args``.
        """

        if kwargs.get('required', True):
            raise TypeError(
                'In click framework, arguments are mandatory, unless marked required=False. '
                'Attempt to use configmanager as a fallback provider suggests that this is an optional option, '
                'not a mandatory argument.'
            )

        args, kwargs = _config_parameter(args, kwargs)
        return self._click.argument(*args, **kwargs)
