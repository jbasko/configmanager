import collections
import pytest

from configmanager import Config, PlainConfig


@pytest.fixture
def simple_config():
    return Config([
        ('uploads', collections.OrderedDict([
            ('enabled', False),
            ('threads', 1),
            ('db', collections.OrderedDict([
                ('user', 'root'),
                ('password', 'secret'),
            ]))
        ]))
    ])


@pytest.fixture
def plain_config():
    return PlainConfig([
        ('uploads', collections.OrderedDict([
            ('enabled', False),
            ('threads', 1),
            ('db', collections.OrderedDict([
                ('user', 'root'),
                ('password', 'secret'),
            ]))
        ]))
    ])
