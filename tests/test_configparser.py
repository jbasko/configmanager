from configmanager import ConfigManager, Config


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
        Config('random', 'name', default='Bob')
    )
    config_path = tmpdir.join('config1.ini').strpath
    with open(config_path, 'w') as f:
        m.write(f)

    # default value shouldn't be written
    with open(config_path) as f:
        assert f.read() == '[random]\n\n'

    m.random.name = 'Harry'

    with open(config_path, 'w') as f:
        m.write(f)

    with open(config_path) as f:
        assert f.read() == '[random]\nname = Harry\n\n'
