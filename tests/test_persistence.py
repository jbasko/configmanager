from configmanager import ConfigManager, ConfigItem


def test_reads_empty_config_from_file_obj(simple_config_manager, empty_config_file):
    with open(empty_config_file) as f:
        simple_config_manager.read_file(f)

    assert simple_config_manager.simple.str == ''
    assert simple_config_manager.simple.int == 0
    assert simple_config_manager.simple.float == 0.0
    assert simple_config_manager.random.name == 'Bob'


def test_reads_simple_config_from_file_obj(simple_config_manager, simple_config_file):
    with open(simple_config_file) as f:
        simple_config_manager.read_file(f)

    assert simple_config_manager.simple.str == 'hello'
    assert simple_config_manager.simple.int == 5
    assert simple_config_manager.simple.float == 33.33
    assert simple_config_manager.random.name == 'Johnny'


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

    m.random.name = 'Harry'

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path) as f:
        assert f.read() == '[random]\nname = Harry\n\n'


def test_preserves_bool_notation(tmpdir):
    m = ConfigManager(
        ConfigItem('flags', 'enabled', type=bool, default=False)
    )

    config_path = tmpdir.join('flags.ini').strpath
    with open(config_path, 'w') as f:
        f.write('[flags]\nenabled = Yes\n\n')

    with open(config_path) as f:
        m.read_file(f)

    assert m.flags.enabled
    assert m.flags.enabled.value is True

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path) as f:
        assert f.read() == '[flags]\nenabled = Yes\n\n'


def test_handles_deep_paths(tmpdir):
    config_path = tmpdir.join('conf.ini').strpath

    m = ConfigManager(
        ConfigItem('some', 'deep', 'config', 'a'),
        ConfigItem('some', 'deep', 'config', 'b'),
    )

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path, 'r') as f:
        assert f.read() == ''

    m.some.deep.config.a = 'AAA'

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path, 'r') as f:
        assert f.read() == '[some]\ndeep.config.a = AAA\n\n'

    m.reset()
    assert not m.some.deep.config.a.has_value

    with open(config_path, 'r') as f:
        m.read_file(f)

    assert m.some.deep.config.a == 'AAA'
