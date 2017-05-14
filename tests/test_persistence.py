import pytest

from configmanager.v1 import Config, Item


def test_reads_empty_config_from_file_obj(simple_config, empty_config_file):
    with open(empty_config_file) as f:
        simple_config.read_file(f)

    assert simple_config.to_dict() == {
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
        simple_config.read_file(f)

    assert simple_config.to_dict() == {
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
        m.write(f)

    # default value shouldn't be written
    with open(config_path) as f:
        assert f.read() == ''

    m['random']['name'].value = 'Harry'

    with open(config_path, 'w') as f:
        m.write(f)

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
        m.read_file(f)

    assert m.flags.enabled.value is True

    with open(config_path, 'w') as f:
        m.write(f)

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
            m.write(f)


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
    m.write(path1)

    # Can read from one empty file
    m.read(path1)
    assert m.is_default

    m.a.x.value = 0.33
    m.b.n.value = 42
    m.write(path2)

    # Can read from one non-empty file
    m.reset()
    m.read(path2)
    assert not m.is_default
    assert m.a.x.value == 0.33

    m.reset()
    m.a.x.value = 0.66
    m.b.m.value = 'YES'
    m.write(path3)

    m.reset()
    m.read([path1, path2, path3])

    assert m.a.x.value == 0.66
    assert m.a.y.is_default
    assert m.b.m.value is True
    assert m.b.m.raw_str_value == 'YES'
    assert m.b.n.value == 42

    m.reset()
    m.read([path3, path2, path1])

    assert m.a.x.value == 0.33  # this is the only difference with the above order
    assert m.a.y.is_default
    assert m.b.m.value is True
    assert m.b.m.raw_str_value == 'YES'
    assert m.b.n.value == 42

    # Make sure multiple paths supported in non-list syntax.
    m.reset()
    m.read(path3, path2, path1)

    assert m.a.x.value == 0.33
    assert m.b.m.value is True


def test_read_string():
    m = Config({
        'a': {
            'x': Item(), 'y': Item(),
        },
        'b': {
            'm': Item(), 'n': Item(),
        },
    })

    m.read_string(u'[a]\nx = haha\ny = yaya\n')
    assert m.a.x.value == 'haha'
    assert m.a.y.value == 'yaya'


def test_read_dict():
    m = Config({
        'a': {
            'x': Item(), 'y': Item(),
        },
        'b': {
            'm': Item(), 'n': Item(),
        },
    })

    m.read_dict({
        'a': {'x': 'xoxo', 'y': 'yaya'},
        'b': {'m': 'mama', 'n': 'nono'},
    })

    assert m.to_dict() == {
        'a': {'x': 'xoxo', 'y': 'yaya'},
        'b': {'m': 'mama', 'n': 'nono'},
    }


def test_read_as_defaults_treats_all_values_as_declarations(tmpdir):
    path = tmpdir.join('conf.ini').strpath
    with open(path, 'w') as f:
        f.write('[uploads]\nthreads = 5\nenabled = no\n')
        f.write('[messages]\ngreeting = Hello, home!\n')

    m = Config()
    m.read(path, as_defaults=True)

    assert m.uploads
    assert m.uploads.threads.value == '5'
    assert m.uploads.enabled.value == 'no'
    with pytest.raises(AttributeError):
        assert m.uploads.something_else
    assert m.messages.greeting.value == 'Hello, home!'

    # Reading again with as_defaults=True should not change the values, only the defaults
    m.uploads.threads.value = '55'
    m.read(path, as_defaults=True)
    assert m.uploads.threads.value == '55'
    assert m.uploads.threads.default == '5'

    # But reading with as_defaults=False should change the value
    m.read(path)
    assert m.uploads.threads.value == '5'
    assert m.uploads.threads.default == '5'
