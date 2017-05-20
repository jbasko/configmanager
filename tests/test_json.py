import json

import pytest

from configmanager import Config


@pytest.fixture
def defaults_json_path(tmpdir):
    defaults_path = tmpdir.join('defaults.json').strpath
    with open(defaults_path, 'w') as f:
        json.dump({
            'uploads': {
                'threads': 1,
                'enabled': False,
                'tmp_dir': '/tmp',
            }
        }, f)
    return defaults_path


@pytest.fixture
def user_json_path(tmpdir):
    user_path = tmpdir.join('user.json').strpath
    with open(user_path, 'w') as f:
        json.dump({
            'uploads': {
                'threads': '5',
                'enabled': 'yes',
            }
        }, f)
    return user_path


def test_json_read_and_write(defaults_json_path, user_json_path):
    c1 = Config()
    c1.json.read(defaults_json_path, as_defaults=True)

    c2 = Config()
    c2.json.read([defaults_json_path], as_defaults=True)

    c3 = Config()
    with open(defaults_json_path) as f:
        c3.json.read(f, as_defaults=True)

    assert c1.to_dict(with_defaults=False) == {}
    assert c1.to_dict(with_defaults=True) == {
        'uploads': {
            'threads': 1,
            'enabled': False,
            'tmp_dir': '/tmp',
        }
    }

    assert c1.to_dict() == c2.to_dict() == c3.to_dict()

    c1.json.read(user_json_path)
    c2.json.read([user_json_path])
    with open(user_json_path) as f:
        c3.json.read(f)

    assert c1.to_dict(with_defaults=False) == {
        'uploads': {
            'threads': 5,
            'enabled': True,
        }
    }
    assert c1.to_dict() == c2.to_dict() == c3.to_dict()

    updates = {
        'uploads': {
            'threads': 10,
            'enabled': False,
        }
    }

    c1.read_dict(updates)
    c2.read_dict(updates)
    c3.read_dict(updates)

    assert c1.to_dict() == c2.to_dict() == c3.to_dict()

    c1.json.write(user_json_path)
    c2.json.read(user_json_path)
    assert c1.to_dict() == c2.to_dict() == c3.to_dict()

    assert c1.to_dict() == c2.to_dict() == c3.to_dict()

    with open(user_json_path, 'w') as f:
        c2.json.write(f)
    c1.json.read(user_json_path)

    assert c1.to_dict() == c2.to_dict() == c3.to_dict()


def test_json_writes_with_defaults_false_by_default(user_json_path):
    c = Config({'greeting': 'Hello'})
    c.json.write(user_json_path)

    d = Config()
    d.json.read(user_json_path, as_defaults=True)
    assert len(d) == 0

    c.json.write(user_json_path, with_defaults=True)

    d.json.read(user_json_path, as_defaults=True)
    assert len(d) == 1
    assert d.greeting.value == 'Hello'

    c.greeting.value = 'Hey!'
    c.json.write(user_json_path)

    d.json.read(user_json_path, as_defaults=True)
    assert d.greeting.value == 'Hey!'
