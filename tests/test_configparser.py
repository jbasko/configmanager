import collections
import pytest

from configmanager import Config, Item, NotFound


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


def test_reads_empty_config_from_file_obj(simple_config, empty_config_file):
    with open(empty_config_file) as f:
        simple_config.configparser.load(f)

    assert simple_config.dump_values() == {
        'simple': {
            'str': '',
            'int': 0,
            'float': 0.0,
        },
        'random': {
            'name': 'Bob',
        },
    }


def test_reads_simple_config_from_file_obj(simple_config, simple_config_file):
    with open(simple_config_file) as f:
        simple_config.configparser.load(f)

    assert simple_config.dump_values() == {
        'simple': {
            'str': 'hello',
            'int': 5,
            'float': 33.33,
        },
        'random': {
            'name': 'Johnny',
        },
    }


def test_writes_config_to_file(tmpdir):
    m = Config({
        'random': {
            'name': 'Bob',
        },
    })
    config_path = tmpdir.join('config1.ini').strpath
    with open(config_path, 'w') as f:
        m.configparser.dump(f)

    # default value shouldn't be written
    with open(config_path) as f:
        assert f.read() == ''

    m['random']['name'].value = 'Harry'

    with open(config_path, 'w') as f:
        m.configparser.dump(f)

    with open(config_path) as f:
        assert f.read() == '[random]\nname = Harry\n\n'


def test_preserves_bool_notation(tmpdir):
    m = Config({
        'flags': {
            'enabled': False
        }
    })

    assert m.flags.enabled.value is False

    config_path = tmpdir.join('flags.ini').strpath
    with open(config_path, 'w') as f:
        f.write('[flags]\nenabled = Yes\n\n')

    with open(config_path) as f:
        m.configparser.load(f)

    assert m.flags.enabled.value is True

    with open(config_path, 'w') as f:
        m.configparser.dump(f)

    with open(config_path) as f:
        assert f.read() == '[flags]\nenabled = Yes\n\n'


def test_configparser_writer_does_not_accept_three_deep_paths(tmpdir):
    config_path = tmpdir.join('conf.ini').strpath

    m = Config({
        'some': {'deep': {'config': None}}
    })

    m.some.deep.config.value = 'this is fine'
    assert m.some.deep.config.value == 'this is fine'

    with pytest.raises(RuntimeError):
        with open(config_path, 'w') as f:
            m.configparser.dump(f)


def test_read_reads_multiple_files_in_order(tmpdir):
    m = Config({
        'a': {
            'x': Item(type=float),
            'y': 'aye',
        },
        'b': {
            'm': False,
            'n': Item(type=int),
        }
    })

    path1 = tmpdir.join('config1.ini').strpath
    path2 = tmpdir.join('config2.ini').strpath
    path3 = tmpdir.join('config3.ini').strpath

    # Empty file
    m.configparser.dump(path1)

    # Can load from one empty file
    m.configparser.load(path1)
    assert m.is_default

    m.a.x.value = 0.33
    m.b.n.value = 42
    m.configparser.dump(path2)

    # Can load from one non-empty file
    m.reset()
    m.configparser.load(path2)
    assert not m.is_default
    assert m.a.x.value == 0.33

    m.reset()
    m.a.x.value = 0.66
    m.b.m.value = 'YES'
    m.configparser.dump(path3)

    m.reset()
    m.configparser.load([path1, path2, path3])

    assert m.a.x.value == 0.66
    assert m.a.y.is_default
    assert m.b.m.value is True
    assert m.b.m.raw_str_value == 'YES'
    assert m.b.n.value == 42

    m.reset()
    m.configparser.load([path3, path2, path1])

    assert m.a.x.value == 0.33  # this is the only difference with the above order
    assert m.a.y.is_default
    assert m.b.m.value is True
    assert m.b.m.raw_str_value == 'YES'
    assert m.b.n.value == 42

    # Make sure multiple paths not supported in non-list syntax.
    with pytest.raises(TypeError):
        m.configparser.load(path3, path2, path1)


def test_read_string():
    m = Config({
        'a': {
            'x': Item(), 'y': Item(),
        },
        'b': {
            'm': Item(), 'n': Item(),
        },
    })

    m.configparser.loads(u'[a]\nx = haha\ny = yaya\n')
    assert m.a.x.value == 'haha'
    assert m.a.y.value == 'yaya'


def test_read_as_defaults_treats_all_values_as_schemas(tmpdir):
    path = tmpdir.join('conf.ini').strpath
    with open(path, 'w') as f:
        f.write('[uploads]\nthreads = 5\nenabled = no\n')
        f.write('[messages]\ngreeting = Hello, home!\n')

    m = Config()
    m.configparser.load(path, as_defaults=True)

    assert m.uploads
    assert m.uploads.threads.value == '5'
    assert m.uploads.enabled.value == 'no'
    with pytest.raises(NotFound):
        assert m.uploads.something_else
    assert m.messages.greeting.value == 'Hello, home!'

    # Reading again with as_defaults=True should not change the values, only the defaults
    m.uploads.threads.value = '55'
    m.configparser.load(path, as_defaults=True)
    assert m.uploads.threads.value == '55'
    assert m.uploads.threads.default == '5'

    # But reading with as_defaults=False should change the value
    m.configparser.load(path)
    assert m.uploads.threads.value == '5'
    assert m.uploads.threads.default == '5'


def test_write_with_defaults_writes_defaults_too(tmpdir):
    path = tmpdir.join('conf.ini').strpath

    m = Config({'a': {'b': 1, 'c': 'd', 'e': True}})

    m.configparser.dump(path)
    with open(path, 'r') as f:
        assert len(f.read()) == 0

    m.configparser.dump(path, with_defaults=True)
    with open(path, 'r') as f:
        assert len(f.read()) > 0

    n = Config()
    n.configparser.load(path, as_defaults=True)

    assert n.a.b.value == '1'  # it is a string because n has no idea about types
    assert n.a.e.value == 'True'  # same
    assert n.a.c.value == 'd'


def test_write_string_returns_valid_configparser_string():
    config = Config({'db': {'user': 'root'}})
    assert config.configparser.dumps() == ''
    assert config.configparser.dumps(with_defaults=True) == '[db]\nuser = root\n\n'


def test_writes_to_and_reads_from_default_section_transparently(tmpdir):
    config_ini = tmpdir.join('config.ini').strpath

    config1 = Config(collections.OrderedDict([('greeting', 'Hello'), ('name', 'World')]))
    config1.configparser.dump(config_ini, with_defaults=True)

    with open(config_ini) as f:
        assert f.read() == (
            '[NO_SECTION]\n'
            'greeting = Hello\n'
            'name = World\n\n'
        )

    config2 = Config()
    config2.configparser.load(config_ini, as_defaults=True)

    assert config1.dump_values() == config2.dump_values() == {'greeting': 'Hello', 'name': 'World'}
