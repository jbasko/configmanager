import pytest

from configmanager import Config


@pytest.fixture
def yaml_path1(tmpdir):
    return tmpdir.join('path1.yml').strpath


def test_config_written_to_and_read_from_yaml_file(yaml_path1):
    config = Config({
        'uploads': {
            'enabled': True,
            'threads': 5,
            'db': {
                'user': 'root',
            },
        },
    })
    original_values = config.to_dict()

    config.yaml.dump(yaml_path1, with_defaults=True)

    config.yaml.load(yaml_path1)
    assert config.to_dict() == original_values

    config2 = Config()
    config2.yaml.load(yaml_path1, as_defaults=True)
    assert config2.to_dict() == original_values


def test_config_written_to_and_read_from_yaml_string():
    config_str = (
        'uploads:\n'
        '  enabled: True\n'
        '  threads: 5\n'
        '  db:\n'
        '    user: root\n\n'
    )

    config = Config()
    config.yaml.loads(config_str, as_defaults=True)

    assert config.to_dict() == {
        'uploads': {
            'enabled': True,
            'threads': 5,
            'db': {
                'user': 'root',
            }
        }
    }

    config_str2 = config.yaml.dumps(with_defaults=True)

    config2 = Config()
    config2.yaml.loads(config_str2, as_defaults=True)
    assert config2.to_dict() == config.to_dict()
