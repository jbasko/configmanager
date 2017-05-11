import pytest

from configmanager import ConfigManager, ConfigItem


def test_reads_empty_config_from_file_obj(simple_config_manager, empty_config_file):
    with open(empty_config_file) as f:
        simple_config_manager.read_file(f)

    assert simple_config_manager.get('simple', 'str') == ''
    assert simple_config_manager.get('simple', 'int') == 0
    assert simple_config_manager.get('simple', 'float') == 0.0
    assert simple_config_manager.get('random', 'name') == 'Bob'


def test_reads_simple_config_from_file_obj(simple_config_manager, simple_config_file):
    with open(simple_config_file) as f:
        simple_config_manager.read_file(f)

    assert simple_config_manager.get('simple', 'str') == 'hello'
    assert simple_config_manager.get('simple', 'int') == 5
    assert simple_config_manager.get('simple', 'float') == 33.33
    assert simple_config_manager.get('random', 'name') == 'Johnny'


def test_writes_config_to_file(tmpdir):
    m = ConfigManager(
        ConfigItem('random', 'name', default='Bob')
    )
    config_path = tmpdir.join('config1.ini').strpath
    with open(config_path, 'w') as f:
        m.write(f)

    # default value shouldn't be written
    with open(config_path) as f:
        assert f.read() == ''

    m.set('random', 'name', 'Harry')

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path) as f:
        assert f.read() == '[random]\nname = Harry\n\n'


def test_preserves_bool_notation(tmpdir):
    m = ConfigManager(
        ConfigItem('flags', 'enabled', type=bool, default=False)
    )

    assert m.get('flags', 'enabled') is False

    config_path = tmpdir.join('flags.ini').strpath
    with open(config_path, 'w') as f:
        f.write('[flags]\nenabled = Yes\n\n')

    with open(config_path) as f:
        m.read_file(f)

    assert m.get('flags', 'enabled') is True

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path) as f:
        assert f.read() == '[flags]\nenabled = Yes\n\n'


def test_configparser_writer_does_not_accept_three_deep_paths(tmpdir):
    config_path = tmpdir.join('conf.ini').strpath

    m = ConfigManager(
        ConfigItem('some', 'deep', 'config'),
    )

    m.set('some', 'deep', 'config', 'this is fine')
    assert m.get('some', 'deep', 'config') == 'this is fine'

    with pytest.raises(NotImplementedError):
        with open(config_path, 'w') as f:
            m.write(f)


def test_handles_dotted_sections_and_dotted_options(tmpdir):
    config_path = tmpdir.join('conf.ini').strpath

    m = ConfigManager(
        ConfigItem('some.deep', 'config.a'),
        ConfigItem('some', 'deep.config.a'),
        ConfigItem('some.deep.config', 'a'),
    )

    m.set('some.deep', 'config.a', '2_2')

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path, 'r') as f:
        assert f.read() == '[some.deep]\nconfig.a = 2_2\n\n'

    m.set('some.deep.config', 'a', '3_1')

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path, 'r') as f:
        assert f.read() == '[some.deep]\nconfig.a = 2_2\n\n[some.deep.config]\na = 3_1\n\n'

    m.reset()

    assert not m.get_item('some.deep', 'config.a').has_value
    assert not m.get_item('some.deep.config', 'a').has_value

    with open(config_path, 'r') as f:
        m.read_file(f)

    assert m.get('some.deep', 'config.a') == '2_2'
    assert m.get('some.deep.config', 'a') == '3_1'


def test_read_reads_multiple_files_in_order(tmpdir):
    m = ConfigManager(
        ConfigItem('a', 'x', type=float),
        ConfigItem('a', 'y', default='aye'),
        ConfigItem('b', 'm', default=False, type=bool),
        ConfigItem('b', 'n', type=int),
    )

    path1 = tmpdir.join('config1.ini').strpath
    path2 = tmpdir.join('config2.ini').strpath
    path3 = tmpdir.join('config3.ini').strpath

    # Empty file
    m.write(path1)

    # Can read from one empty file
    m.read(path1)
    assert m.is_default

    m.set('a', 'x', 0.33)
    m.set('b', 'n', 42)
    m.write(path2)

    # Can read from one non-empty file
    m.reset()
    m.read(path2)
    assert not m.is_default
    assert m.get('a', 'x') == 0.33

    m.reset()
    m.set('a', 'x', 0.66)
    m.set('b', 'm', 'YES')
    m.write(path3)

    m.reset()
    m.read([path1, path2, path3])

    assert m.get_item('a', 'x').value == 0.66
    assert not m.get_item('a', 'y').has_value
    assert m.get_item('b', 'm').value is True
    assert m.get_item('b', 'm').raw_str_value == 'YES'
    assert m.get_item('b', 'n').value == 42

    m.reset()
    m.read([path3, path2, path1])

    assert m.get_item('a', 'x').value == 0.33  # this is the only difference with the above order
    assert not m.get_item('a', 'y').has_value
    assert m.get_item('b', 'm').value is True
    assert m.get_item('b', 'm').raw_str_value == 'YES'
    assert m.get_item('b', 'n').value == 42

    # Make sure multiple paths supported in non-list syntax.
    m.reset()
    m.read(path3, path2, path1)

    assert m.get('a', 'x') == 0.33
    assert m.get('b', 'm') is True


def test_read_string():
    m = ConfigManager(
        ConfigItem('a', 'x'),
        ConfigItem('a', 'y'),
        ConfigItem('b', 'm'),
        ConfigItem('b', 'n'),
    )

    m.read_string(u'[a]\nx = haha\ny = yaya\n')
    assert m.get('a', 'x') == 'haha'
    assert m.get('a', 'y') == 'yaya'


def test_read_dict_in_python3():
    m = ConfigManager(
        ConfigItem('a', 'x'),
        ConfigItem('a', 'y'),
        ConfigItem('b', 'm'),
        ConfigItem('b', 'n'),
    )

    m.read_dict({
        'a': {'x': 'xoxo', 'y': 'yaya'},
        'b': {'m': 'mama', 'n': 'nono'},
    })

    assert m.get('a', 'x') == 'xoxo'
    assert m.get('a', 'y') == 'yaya'
    assert m.get('b', 'm') == 'mama'
    assert m.get('b', 'n') == 'nono'

