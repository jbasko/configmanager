import json

import pytest

from configmanager import Config


@pytest.fixture
def config():
    return Config(schema={
        'uploads': {
            'enabled': False,
            'threads': 1,
            'db': Config({
                'user': 'root',
                'password': 'secret',
            }),
        },
        'greeting': 'Hello',
    })


def test_load_sources_setting(config, tmpdir):
    json1 = tmpdir.join('config1.json').strpath
    json2 = tmpdir.join('config2.json').strpath
    json3 = tmpdir.join('config3.json').strpath

    config.uploads.db.settings.load_sources.append(json1)
    config.settings.load_sources.append(json2)

    # None of the files exist, shouldn't fail
    config.load()

    assert config.dump_values(with_defaults=False) == {}

    with open(json1, 'w') as f:
        json.dump({'user': 'Administrator', 'password': 'SECRET'}, f)

    config.load()

    assert config.dump_values(with_defaults=False) == {
        'uploads': {'db': {'user': 'Administrator', 'password': 'SECRET'}}
    }

    assert config.uploads.enabled.value is False
    assert config.uploads.db.user.value == 'Administrator'

    with open(json2, 'w') as f:
        json.dump({'uploads': {'db': {'user': 'admin'}, 'enabled': True}}, f)

    config.load()

    assert config.uploads.enabled.value is True
    assert config.uploads.db.user.value == 'admin'  # should override "Administrator"
    assert config.uploads.db.password.value == 'SECRET'

    with open(json3, 'w') as f:
        json.dump({'main': {'greeting': 'Hey!'}}, f)

    wrapper = Config({
        'main': config
    })
    wrapper.settings.load_sources.append(json3)

    wrapper.load()

    assert wrapper.main.uploads.db.user.value == 'admin'
    assert wrapper.main.uploads.db.password.value == 'SECRET'
    assert wrapper.main.greeting.value == 'Hey!'
