import pytest

from configmanager import ConfigManager, ConfigItem


@pytest.fixture
def simple_config_manager():
    return ConfigManager(
        ConfigItem('simple', 'str', default='', type=str),
        ConfigItem('simple', 'int', default=0, type=int),
        ConfigItem('simple', 'float', default=0.0, type=float),
        ConfigItem('random', 'name', default='Bob')
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
