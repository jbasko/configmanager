import pytest

from configmanager import Config


@pytest.fixture
def simple_config():
    return Config({
        'uploads': {
            'threads': 1,
            'enabled': False,
            'db': {
                'user': 'root',
                'password': 'secret',
            }
        }
    })
