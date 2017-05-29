import pytest

import click
from click.testing import CliRunner

from configmanager import Config


def test_click_option_and_click_argument():
    config = Config({
        'uploads': {
            'threads': 5,
            'dir': '/tmp',
        }
    })

    assert config.click

    assert callable(config.click.option)
    assert callable(config.click.argument)

    option = config.click.option('--uploads-threads', config.uploads.threads)
    assert callable(option)

    with pytest.raises(TypeError):
        config.click.argument('uploads_dir', config.uploads.dir)

    argument = config.click.argument('uploads_dir', config.uploads.dir, required=False)
    assert callable(argument)

    @click.command()
    @config.click.argument('uploads_dir', config.uploads.dir, required=False)
    @config.click.option('--uploads-threads', config.uploads.threads)
    def my_command(uploads_dir, uploads_threads):
        assert type(uploads_threads) == int
        print('{} {!r}'.format(uploads_dir, uploads_threads))

    # Use defaults
    result = CliRunner().invoke(my_command)
    assert result.exit_code == 0
    assert result.output == '/tmp 5\n'

    # Use command-line overrides
    result = CliRunner().invoke(my_command, ['/tmp/uploads', '--uploads-threads', '10'])
    assert result.exit_code == 0
    assert result.output == '/tmp/uploads 10\n'
