from configmanager import Config
from configmanager.base import ConfigRootAttribute


def hooks_extension(config):
    from configmanager.hooks import Hooks
    return Hooks(config)


def test_tree_attribute_is_attached_to_root():

    def create_special(*args, **kwargs):
        return ['the', 'special']

    class ExtendedConfig(Config):
        special = ConfigRootAttribute('special', factory=create_special)

    config = ExtendedConfig({
        'uploads': {
            'db': {
                'user': 'root',
                'password': 'root',
            }
        }
    })

    assert config.uploads.db.special == ['the', 'special']
    assert config.uploads.db.special is config.special
    assert config.uploads.special is config.special


def test_tree_attribute_factory_is_passed_config():
    calls = []

    def attribute_factory(*args, **kwargs):
        calls.append((args, kwargs))
        return True

    class ExtendedConfig(Config):
        special = ConfigRootAttribute('special', factory=attribute_factory)

    config = ExtendedConfig({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    assert calls == []

    assert config.uploads.db.special is True
    assert calls == [((), {'config': config})]

    assert config.uploads.special is True
    assert calls == [((), {'config': config})]
