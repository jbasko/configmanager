import pytest

from configmanager import ConfigManager, Configurable


@pytest.fixture
def simple_config_manager():
    return ConfigManager(
        Configurable('simple', 'str', default='', type=str),
        Configurable('simple', 'int', default=0, type=int),
        Configurable('simple', 'float', default=0.0, type=float),
        Configurable('random', 'name', default='Bob')
    )


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
