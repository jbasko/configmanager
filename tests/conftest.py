import pytest

from configmanager.v1 import Config


@pytest.fixture
def simple_config():
    return Config({
        'simple': {
            'str': '',
            'int': 0,
            'float': 0.0,
        },
        'random': {
            'name': 'Bob',
        },
    })


@pytest.fixture
def empty_config_file(tmpdir):
    path = tmpdir.join('empty.ini')
    with open(path.strpath, 'w') as f:
        f.write('')
    return path.strpath


@pytest.fixture
def simple_config_file(tmpdir):
    path = tmpdir.join('simple.ini')
    with open(path.strpath, 'w') as f:
        f.write('[simple]\n')
        f.write('str = hello\n')
        f.write('int = 5\n')
        f.write('float = 33.33\n')
        f.write('\n')
        f.write('[random]\n')
        f.write('name = Johnny')
    return path.strpath
