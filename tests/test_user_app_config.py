import json

from configmanager import Config


def test_config_with_app_name(tmpdir):
    config_path = tmpdir.mkdir('test_config_with_app_name').join('config.json').strpath
    with open(config_path, 'w') as f:
        json.dump({'uploads': {'enabled': True}}, f)

    schema = {
        'uploads': {
            'enabled': False,
            'threads': 1,
            'db': {
                'user': 'root',
                'password': 'secret',
            }
        }
    }

    # Auto-load enabled
    config1 = Config(schema, app_name='test_config_with_app_name', user_config_root=tmpdir.strpath, auto_load=True)

    assert config1.uploads.threads.value == 1

    assert config1.uploads.enabled.value is True
    assert not config1.uploads.enabled.is_default

    # Auto-load not enabled by default
    config2 = Config(schema, app_name='test_config_with_app_name', user_config_root=tmpdir.strpath)
    assert config2.uploads.enabled.value is False

    config2.load()
    assert config2.uploads.enabled.value is True
