import types

import pytest

from configmanager.items import Item
from configmanager import Config, Types
from configmanager.schema_parser import parse_config_schema
from configmanager.sections import Section


@pytest.fixture
def app_config_dict_example():
    return {
        'uploads': {
            'enabled': True,
            'threads': 1,
            'type_': Item(name='type', default=None),
        },
        'downloads': {
            'content_type': 'text/plain',
            'deep': {
                'question': 'Why would you want a config this deep?',
            },
            'threads': Item(type=int),
        },
        'greeting': 'Hello, world!',
    }


@pytest.fixture
def app_config_module_example():
    uploads = types.ModuleType('uploads')
    uploads.enabled = True
    uploads.threads = 1
    uploads.type_ = Item(name='type', default=None)

    downloads = types.ModuleType('downloads')
    downloads.content_type = 'text/plain'

    deep = types.ModuleType('deep')
    deep.question = 'Why would you want a config this deep?'
    downloads.deep = deep
    downloads.threads = Item(type=int)

    app_config = types.ModuleType('app_config')
    app_config.uploads = uploads
    app_config.downloads = downloads
    app_config.greeting = 'Hello, world!'

    return app_config


def test_primitive_value_is_a_schema_of_an_item():
    config = Config((
        ('enabled', True),
        ('threads', 5),
    ))

    assert config.enabled.is_item
    assert config.enabled.default is True
    assert config.enabled.name == 'enabled'

    assert config.threads.is_item
    assert config.threads.default == 5
    assert config.threads.name == 'threads'


def test_lists_of_tuples_declare_sections():
    config = Config()

    parse_config_schema([
        ('uploads', [
            ('enabled', True),
            ('threads', 5),
            ('db', [
                ('user', 'root'),
                ('password', 'secret'),
            ]),
        ]),
    ], root=config)

    assert config.uploads.is_section
    assert config.uploads.enabled.is_item
    assert config.uploads.enabled.default is True
    assert config.uploads.threads.is_item
    assert config.uploads.db.is_section
    assert config.uploads.db.user.is_item
    assert config.uploads.db.user.default == 'root'
    assert config.uploads.db.password.is_item


def test_non_empty_dictionaries_declare_sections():
    config = Config()
    parse_config_schema({
        'uploads': {
            'enabled': True,
            'threads': 5,
            'db': {
                'user': 'root',
                'password': 'secret',
            },
        },
    }, root=config)

    assert config.uploads.is_section
    assert config.uploads.enabled.is_item
    assert config.uploads.enabled.default is True
    assert config.uploads.threads.is_item
    assert config.uploads.db.is_section
    assert config.uploads.db.user.is_item
    assert config.uploads.db.user.default == 'root'
    assert config.uploads.db.password.is_item


def test_dict_and_module_based_config_schema(app_config_dict_example, app_config_module_example):
    dict_config = Config(app_config_dict_example)
    module_config = Config(app_config_module_example)
    assert dict_config.dump_values(with_defaults=True) == module_config.dump_values(with_defaults=True)


def test_default_value_is_deep_copied():
    things = [1, 2, 3, 4]

    config = Config({'items': things})
    assert config['items'].value == [1, 2, 3, 4]

    things.remove(2)
    assert config['items'].value == [1, 2, 3, 4]


def test_can_use_list_notation_to_declare_ordered_config_tree():
    config = Config([
        ('uploads', [
            ('enabled', False),
            ('db', [
                ('user', 'root'),
            ])
        ])
    ])

    assert config.uploads.enabled.value is False
    assert config.uploads.db.user.value == 'root'


def test_config_root_schema_cannot_be_a_primitive_value(tmpdir):
    #
    with pytest.raises(ValueError):
        Config(5)

    with pytest.raises(ValueError):
        Config(True)

    with pytest.raises(ValueError):
        Config([])

    with pytest.raises(ValueError):
        Config({})

    with pytest.raises(ValueError):
        Config('haha')

    # Also, no more filenames
    json_filename = tmpdir.join('uploads.json').strpath
    with pytest.raises(ValueError):
        Config(json_filename)


def test_dict_with_all_keys_prefixed_with_at_symbol_is_treated_as_item_meta():
    config = Config({
        'enabled': {
            '@default': False,
        },
        'db': {
            'user': 'root',
            'name': {
                '@help': 'Name of the database'
            },
            '@help': 'db configuration',  # This should be ignored for now
        },
    })

    paths = set(path for path, _ in config.iter_items(recursive=True, key='str_path'))
    assert 'enabled' in paths
    assert 'enabled.@default' not in paths
    assert 'db' not in paths
    assert 'db.@help' not in paths
    assert 'db.user' in paths
    assert 'db.name' in paths
    assert 'db.name.@help' not in paths

    assert config.enabled.default is False
    assert config.db.name.help == 'Name of the database'

    # Make sure it still behaves like a bool
    config.enabled.value = 'yes'
    assert config.enabled.value is True

    # Name is excluded because it has no value
    assert config.db.dump_values() == {'user': 'root'}

    config.db.name.value = 'testdb'
    assert config.db.dump_values() == {'user': 'root', 'name': 'testdb'}


def test_dictionary_with_type_meta_field_marks_an_item():
    config = Config({
        'db': {
            '@type': 'dict',
            'user': 'root',
            'password': 'password',
            'host': 'localhost',
        }
    })

    assert isinstance(config.db, Item)
    assert config.db.type == Types.dict
    assert dict(**config.db.value) == {'user': 'root', 'password': 'password', 'host': 'localhost'}

    config = Config({
        'db': {
            '@something': 'dict',  # intentionally non-sense
            'user': 'root',
            'password': 'password',
            'host': 'localhost',
        }
    })

    assert isinstance(config.db, Section)


def test_subsections_are_instances_of_section_not_config():
    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        }
    })

    assert isinstance(config, Config)
    assert not isinstance(config.uploads, Config)
    assert isinstance(config.uploads, Section)
    assert isinstance(config.uploads.db, Section)


def test_accepts_configmanager_settings_which_are_passed_to_all_subsections():
    configmanager_settings = {
        'message': 'everyone should know this',
    }
    config1 = Config(configmanager_settings=configmanager_settings)
    assert config1.settings.message == 'everyone should know this'

    config2 = Config({'greeting': 'Hello'}, configmanager_settings=configmanager_settings)
    assert config2.settings.message == 'everyone should know this'

    config3 = Config({'db': {'user': 'root'}}, configmanager_settings=configmanager_settings)
    assert config3.settings.message == 'everyone should know this'
    assert config3.db.settings.message == 'everyone should know this'

    assert config3.db.settings is config3.settings


def test_empty_list_is_an_item_with_list_type():
    config = Config({
        'tags': [],
        'uploads': {
            'tmp_dirs': [],
        },
    })

    assert config.tags.is_item
    assert config.tags.type == Types.list
    assert config.tags.default == []

    assert config.uploads.tmp_dirs.is_item
    assert config.uploads.tmp_dirs.type == Types.list
    assert config.uploads.tmp_dirs.default == []


def test_list_of_strings_is_an_item_with_list_type():
    config = Config({
        'tmp_dirs': ['tmp'],
        'target_dirs': ['target1', 'target2'],
        'other_dirs': ['other1', 'other2', 'other3'],
        'uploads': {
            'dirs': ['dir1', 'dir2'],
        }
    })

    assert config.tmp_dirs.default == ['tmp']
    assert config.target_dirs.default == ['target1', 'target2']
    assert config.other_dirs.default == ['other1', 'other2', 'other3']
    assert config.uploads.dirs.default == ['dir1', 'dir2']


def test_empty_dict_is_an_item_with_dict_type():
    config = Config({
        'uploads': {}
    })

    assert config.uploads.is_item
    assert config.uploads.default == {}
    assert config.uploads.type == Types.dict


def test_can_declare_empty_section_and_it_gets_updated_with_references_to_config():
    config = Config({
        'uploads': Section(),
        'api': {
            'db': Section(),
        },
    })

    assert config.uploads.is_section
    assert config.uploads.section is config
    assert config.uploads.settings is config.settings

    assert config.api.db.is_section
    assert config.api.db.section is config.api
    assert config.api.db.settings is config.settings

    assert config.api.section is config
    assert config.api.settings is config.settings


def test_can_reassign_a_section_of_one_config_to_another_and_all_its_subsections_get_updated():
    config1 = Config({
        'uploads': {
            'api': {
                'db': Section()
            },
        },
    })

    config2 = Config({
        'uploads': config1.uploads
    })

    assert config1.settings is not config2.settings

    assert config2.uploads.section is config2
    assert config2.uploads.settings is config2.settings

    assert config2.uploads.api.section is config2.uploads


def test_config_of_configs():
    uploads = Config({
        'threads': 1,
        'db': {
            'user': 'root',
        },
    })

    downloads = Config({
        'enabled': True,
        'tmp_dir': '/tmp',
    })

    uploads.threads.value = 5
    downloads.tmp_dir.value = '/tmp/downloads'

    config = Config({
        'uploads': uploads,
        'downloads': downloads,
    })

    assert config.uploads.threads.value == 5

    config.uploads.threads.value = 3
    assert uploads.threads.value == 3

    assert config.uploads.threads is uploads.threads
    assert config.downloads.enabled is downloads.enabled

    uploads.reset()
    assert config.uploads.threads.value == 1
