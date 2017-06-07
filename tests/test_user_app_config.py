import json

from configmanager import Config


def test_config_with_app_name(tmpdir):
    config_path = tmpdir.mkdir('test_config_with_app_name').join('config.json').strpath
    with open(config_path, 'w') as f:
        json.dump({'uploads': {'enabled': True}}, f)

    config = Config({
        'uploads': {
            'enabled': False,
            'threads': 1,
            'db': {
                'user': 'root',
                'password': 'secret',
            }
        }
    }, app_name='test_config_with_app_name', user_config_root=tmpdir.strpath)

    assert config.uploads.threads.value == 1

    assert config.uploads.enabled.value is True
    assert not config.uploads.enabled.is_default
