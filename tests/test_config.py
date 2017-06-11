# -*- coding: utf-8 -*-

import pytest

from configmanager import Config, Section, Item, Types, NotFound, PlainConfig


def test_reset_resets_values_to_defaults():
    config = Config({
        'x': Item(type=int),
        'y': Item(default='YES')
    })

    config.x.value = 23
    config.y.value = 'NO'

    assert config.x.value == 23
    assert config.y.value == 'NO'

    config.reset()

    assert config.x.is_default
    assert config.y.value == 'YES'


def test_repr_of_config():
    config = Config()
    assert repr(config).startswith('<Config None at ')

    config = Config({'uploads': Config()})
    assert repr(config.uploads).startswith('<Config uploads at ')


def test_assigning_nameless_item_directly_to_config_should_set_its_name():
    config = Config()
    config.dummy = Config()
    config.dummy.x = Item(value=5)
    assert config.dummy.x.name == 'x'

    config.dummy['y'] = Item(default=True)
    assert config.dummy.y.name == 'y'

    assert config.dump_values() == {'dummy': {'x': 5, 'y': True}}


def test_must_not_allow_item_or_section_names_with_str_path_separator_in_them():
    with pytest.raises(ValueError):
        Config({
            'a.b': True,
        })

    Config({
        'a.b': True
    }, str_path_separator='/')

    with pytest.raises(ValueError):
        Config({
            'a/b': True
        }, str_path_separator='/')

    # Sections

    with pytest.raises(ValueError):
        Config({
            'a.b': Section()
        })

    with pytest.raises(ValueError):
        Config({
            'a/b': Section()
        }, str_path_separator='/')

    config = Config({
        'a/b': Section()
    }, str_path_separator='.')

    assert config['a/b'].is_section

    config = Config({
        'a.b': Section()
    }, str_path_separator='/')

    assert config['a.b'].is_section


def test_item_name_and_alias_must_be_a_string():
    config = Config()

    with pytest.raises(TypeError):
        config.x = Item(name=5)

    with pytest.raises(TypeError):
        config[5] = Item()

    with pytest.raises(TypeError):
        config[5] = Item(name='x')


def test_section_name_must_be_a_string():
    config = Config()

    with pytest.raises(TypeError):
        config[5] = Config()


def test_to_dict_should_not_include_items_with_no_usable_value():
    config = Config()
    assert config.dump_values() == {}

    config.a = Item()
    config.b = Item()
    config.dummies = Config({'x': Item(), 'y': Item()})
    assert config.dump_values() == {}

    config.dummies.x.value = 'yes'
    assert config.dump_values() == {'dummies': {'x': 'yes'}}

    config.b.value = 'no'
    assert config.dump_values() == {'dummies': {'x': 'yes'}, 'b': 'no'}


def test_read_dict_recursively_loads_values_from_a_dictionary():
    config = Config({
        'a': {
            'x': 0,
            'y': True,
            'z': 0.0,
        },
        'b': {
            'c': {
                'd': {
                    'x': 'xxx',
                    'y': 'yyy',
                },
            },
        },
    })
    assert config.a.x.value == 0
    assert config.a.y.value is True

    config.load_values({
        'a': {'x': '5', 'y': 'no'},
    })
    assert config.a.x.value == 5
    assert config.a.y.value is False

    config.b.c.load_values({
        'e': 'haha',  # will be ignored
        'd': {'x': 'XXX'},
    })
    assert config.b.c.d.x.value == 'XXX'
    assert 'e' not in config.b.c


def test_read_dict_as_defaults_loads_default_values_from_a_dictionary():
    config = Config()

    # both will be ignored
    config.load_values({
        'a': 5,
        'b': True,
    })

    assert 'a' not in config
    assert 'b' not in config

    # both will be added
    config.load_values({
        'a': 5,
        'b': True,
    }, as_defaults=True)

    assert config.a.value == 5
    assert config.b.value is True


@pytest.fixture
def raw_logging_config():
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'plain': {
                'format': '%(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }


@pytest.fixture
def raw_db_config():
    return {
        'host': 'localhost',
        'username': 'admin',
        'password': 'secret',
        'dbname': 'admindb',
    }


@pytest.fixture
def mixed_app_config(raw_logging_config, raw_db_config):
    """
     A config that contains a previously existing config
     as well as one generated on initialisation.
    """
    return Config({
        'logging': Config(raw_logging_config),
        'db': raw_db_config,
    })


def test_schema_parser_does_not_modify_config(raw_logging_config):
    logging_config = Config(raw_logging_config)
    assert isinstance(logging_config, Config)

    assert logging_config['version']
    assert logging_config['formatters']

    config = Config({'logging': logging_config})
    assert isinstance(config, Config)

    assert config['logging']['version']
    assert config['logging']['formatters']

    assert config['logging']['formatters'] is logging_config['formatters']

    logging_config['version'].value = '2'
    assert config['logging']['version'].value == 2


def test_allows_iteration_over_all_items(mixed_app_config):
    config = mixed_app_config

    all_items = list(config.iter_items(recursive=True))
    assert len(all_items) == 14

    db_items = list(config['db'].iter_items(recursive=True))
    assert len(db_items) == 4

    formatters_items = list(config['logging']['formatters'].iter_items(recursive=True))
    assert len(formatters_items) == 2

    formatters = config['logging']['formatters'].dump_values()
    assert formatters['plain'] == {'format': '%(message)s'}


def test_iter_items_with_recursive_false_iterates_only_over_current_section(mixed_app_config):
    config = mixed_app_config
    assert list(config.iter_items(recursive=False)) == []

    assert len(list(config.logging.iter_items(recursive=False))) == 2
    assert len(list(config.db.iter_items(recursive=False))) == 4


def test_forbids_accidental_item_overwrite_via_setitem(mixed_app_config):
    config = mixed_app_config

    assert config['db']['username'].value == 'admin'

    with pytest.raises(TypeError):
        config['db']['username'] = 'admin2'

    config['db']['username'].value = 'admin2'
    assert config['db']['username'].value == 'admin2'


def test_allows_iteration_over_sections(mixed_app_config):
    config = mixed_app_config

    sections = dict(config.iter_sections())
    assert len(sections) == 2
    assert sections[('db',)] is config.db
    assert sections[('logging',)] is config.logging
    assert 'db' not in sections
    assert 'logging' not in sections

    sections = dict(config.iter_sections(key='alias'))
    assert len(sections) == 2
    assert ('db',) not in sections
    assert ('logging',) not in sections
    assert sections['db'] is config.db
    assert sections['logging'] is config.logging

    assert len(list(sections['db'].iter_sections())) == 0
    assert len(list(sections['logging'].iter_sections())) == 3

    assert len(list(config.iter_sections(recursive=True))) == 9
    assert len(list(config.iter_sections(recursive=True, key='alias'))) == 9


def test_attribute_read_access(mixed_app_config):
    config = mixed_app_config

    assert isinstance(config.db, Section)
    assert isinstance(config.db.username, Item)
    assert isinstance(config.logging.handlers, Section)
    assert isinstance(config.logging.handlers.default, Section)
    assert isinstance(config.logging.loggers[''].handlers, Item)
    assert isinstance(config.logging.loggers[''].level, Item)


def test_attribute_write_access(mixed_app_config):
    config = mixed_app_config

    assert config.db.username.value == 'admin'
    config.db.username.value = 'ADMIN'
    assert config.db.username.value == 'ADMIN'

    config.logging.loggers[''].propagate.value = 'no'
    assert config.logging.loggers[''].propagate.value is False


def test_forbids_accidental_item_overwrite_via_setattr(mixed_app_config):
    config = mixed_app_config

    with pytest.raises(TypeError):
        config.db.username = 'ADMIN'

    assert config.db.username.value == 'admin'

    with pytest.raises(TypeError):
        config.logging.loggers[''].propagate = False

    assert config.logging.loggers[''].propagate.value is True


def test_to_dict(mixed_app_config, raw_db_config, raw_logging_config):
    config = mixed_app_config

    config_dict = config.dump_values()

    assert isinstance(config_dict, dict)

    assert config_dict['db'] is not raw_db_config
    assert config_dict['db'] == raw_db_config
    assert config_dict['logging'] == raw_logging_config


def test_can_inspect_config_contents(mixed_app_config):
    config = mixed_app_config

    assert 'db' in config
    assert 'dbe' not in config

    assert 'logging' in config

    assert 'handlers' in config.logging
    assert '' in config.logging.loggers
    assert 'haha' not in config.logging.loggers


def test_can_have_a_dict_as_a_config_value_if_wrapped_inside_item():
    # You may want to have a dictionary as a config value if you only
    # change it all together or you only pass it all in one piece.

    config = Config({
        'db': {
            'user': 'admin',
            'password': 'secret',
        },
        'aws': Item(default={
            'access_key': '123',
            'secret_key': 'secret',
        })
    })

    assert isinstance(config.aws, Item)
    assert config.aws.name == 'aws'

    with pytest.raises(AttributeError):
        assert config.aws.access_key.value == '123'

    assert config.aws.value['access_key'] == '123'

    # This should have no effect because it is working on a copy of the default
    # value, not the real thing.
    config.aws.value['secret_key'] = 'NEW_SECRET'

    assert config.dump_values()['aws'] == {'access_key': '123', 'secret_key': 'secret'}


def test_len_of_config_returns_number_of_items_and_sections_in_current_level():
    assert len(Config()) == 0

    assert len(Config({'enabled': True})) == 1

    assert len(Config({'uploads': Config()})) == 1
    assert len(Config({'uploads': {}})) == 1

    assert len(Config({'uploads': {'enabled': False}})) == 1
    assert len(Config({'uploads': {'enabled': False, 'threads': 1}})) == 1

    assert len(Config({'uploads': {'enabled': False, 'threads': 0}, 'greeting': 'Hi'})) == 2


def test__getitem__handles_paths_to_sections_and_items_and_so_does__contains__():
    config = Config()
    with pytest.raises(NotFound):
        assert not config['uploads', 'enabled']
    assert ('uploads',) not in config
    assert ('uploads', 'enabled') not in config

    config.uploads = Config({'enabled': True, 'db': {'user': 'root'}})
    assert config['uploads', 'enabled'] is config.uploads.enabled
    assert config['uploads', 'db'] is config.uploads.db

    assert 'uploads' in config
    assert ('uploads',) in config
    assert ('uploads', 'enabled') in config
    assert ('uploads', 'db') in config
    assert ('uploads', 'db', 'user') in config

    assert config.uploads.db.user.value == 'root'

    config['uploads', 'db', 'user'].set('admin')
    assert config.uploads.db.user.value == 'admin'


def test__contains__handles_str_paths(simple_config, plain_config):
    assert 'uploads.db' in simple_config
    assert 'uploads.db' in plain_config
    assert 'uploads.db.user' in simple_config
    assert 'uploads.db.user' in plain_config

    assert 'uploads/db' not in simple_config
    assert 'uploads/db' not in plain_config
    assert 'uploads/db/user' not in simple_config
    assert 'uploads/db/user' not in plain_config


def test_can_use__setitem__to_create_new_deep_paths():
    config = Config()
    config['uploads'] = Config({'enabled': True})

    with pytest.raises(TypeError):
        config['uploads', 'threads'] = 5

    config['uploads', 'threads'] = Item(value=5)
    assert config.uploads.threads.type == Types.int

    config['uploads', 'db'] = Config({'user': 'root'})
    assert config.uploads.db


def test_section_knows_its_alias():
    config = Config()
    config.uploads = Config({
        'enabled': True
    })
    assert config.uploads.alias == 'uploads'

    config.uploads.db = Config({'connection': {'user': 'root'}})
    assert config.uploads.db.alias == 'db'
    assert config.uploads.db.connection.alias == 'connection'


def test_config_item_value_can_be_unicode_str(tmpdir):
    config1 = Config({'greeting': u'Hello, {name}', 'name': u'Anonymous'})
    config1.name.value = u'Jānis Bērziņš'
    assert config1.name.type == Types.str

    path = tmpdir.join('config.ini').strpath
    config1.configparser.dump(path, with_defaults=True)

    config2 = Config({'greeting': '', 'name': ''})
    config2.configparser.load(path)
    assert config2.name.value == u'Jānis Bērziņš'
    assert config1.dump_values(with_defaults=True) == config2.dump_values(with_defaults=True)


def test_config_is_section_and_is_not_item():
    config = Config()
    assert config.is_section
    assert not config.is_item


def test_dump_values_with_flat_true_respects_separator(simple_config):
    assert simple_config.dump_values(with_defaults=True, flat=True) == {
        'uploads.enabled': False,
        'uploads.threads': 1,
        'uploads.db.user': 'root',
        'uploads.db.password': 'secret',
    }

    simple_config.settings.str_path_separator = '/'

    assert simple_config.dump_values(with_defaults=True, flat=True) == {
        'uploads/enabled': False,
        'uploads/threads': 1,
        'uploads/db/user': 'root',
        'uploads/db/password': 'secret',
    }


def test_load_values_with_flat_respects_separator(simple_config):
    new_values = {
        'uploads.enabled': True,
        'uploads.db.user': 'NEW_USER',
        'uploads/threads': 23,
        'uploads/db/password': 'NEW_PASSWORD',
    }

    # default separator is '.' so '/'-separated values are ignored
    simple_config.load_values(new_values, flat=True)

    assert simple_config.uploads.enabled.value is True
    assert simple_config.uploads.db.user.value == 'NEW_USER'
    assert simple_config.uploads.threads.value == 1
    assert simple_config.uploads.db.password.value == 'secret'

    simple_config.reset()

    simple_config.settings.str_path_separator = '/'

    # Now the '.'-separated values are ignored
    simple_config.load_values(new_values, flat=True)

    assert simple_config.uploads.enabled.value is False
    assert simple_config.uploads.db.user.value == 'root'
    assert simple_config.uploads.threads.value == 23
    assert simple_config.uploads.db.password.value == 'NEW_PASSWORD'


def test_config_accepts_and_respects_str_path_separator_setting(simple_config):
    assert list(simple_config.iter_paths(recursive=True, key='str_path')) == [
        'uploads', 'uploads.enabled', 'uploads.threads', 'uploads.db', 'uploads.db.user', 'uploads.db.password',
    ]

    simple_config.settings.str_path_separator = '/'

    assert list(simple_config.iter_paths(recursive=True, key='str_path')) == [
        'uploads', 'uploads/enabled', 'uploads/threads', 'uploads/db', 'uploads/db/user', 'uploads/db/password',
    ]

    assert simple_config.dump_values(with_defaults=True, flat=True) == {
        'uploads/enabled': False,
        'uploads/threads': 1,
        'uploads/db/user': 'root',
        'uploads/db/password': 'secret',
    }


def test_config_of_configs():
    uploads = Config({
        'threads': 1,
        'enabled': True,
        'api': {
            'port': 8000,
        }
    })

    downloads = Config({
        'tmp_dir': '/tmp',
        'db': {
            'user': 'root',
        }
    })

    config = Config({
        'uploads': uploads,
        'downloads': downloads,
        'messages': {
            'greeting': 'Hello',
        }
    })

    assert config.uploads.threads.is_item
    assert config.uploads.api.port.is_item
    assert config.downloads.db.user.is_item
    assert config.messages.greeting.is_item


def test_nested_section_settings_are_the_settings_of_the_nearest_manager_in_tree():
    c = Config({
        'main': Config({
            'a1': Section({
                'a2': Config({
                    'a3': Section({
                        'a4': Section()
                    }),
                }),
            }),
            'b1': Section({
                'b2': Section({
                    'b3': Section({
                        'b4': Config({
                            'b5': Section()
                        }),
                    }),
                }),
            }),
        }),
    })

    assert c.settings
    assert c.main.settings
    assert c.settings is not c.main.settings
    assert c.main.a1.settings is c.main.settings
    assert c.main.a1.a2.settings is not c.main.settings
    assert c.main.a1.a2.a3.settings is c.main.a1.a2.settings
    assert c.main.a1.a2.a3.a4.settings is c.main.a1.a2.settings

    assert c.main.b1.settings is c.main.settings
    assert c.main.b1.b2.settings is c.main.settings
    assert c.main.b1.b2.b3.settings is c.main.settings
    assert c.main.b1.b2.b3.b4.settings is not c.main.settings
    assert c.main.b1.b2.b3.b4.b5.settings is c.main.b1.b2.b3.b4.settings


def test_get_item_and_get_section_for_rich_config():
    config = Config({
        'uploads': Section({
            'db': Section({
                'user': 'root'
            })
        })
    })

    assert config.get_section('uploads').is_section
    assert config.get_section('uploads', 'db').is_section
    assert config.uploads.get_section('db').is_section

    assert config.get_item('uploads', 'db', 'user').is_item
    assert config.uploads.db.get_item('user').is_item

    with pytest.raises(NotFound):
        config.get_item('downloads')

    with pytest.raises(NotFound):
        config.get_section('downloads')

    with pytest.raises(NotFound):
        config.get_item('uploads', 'tmp_dir')

    with pytest.raises(NotFound):
        config.get_section('uploads', 'tmp_dir')


def test_get_item_and_get_section_for_plain_config():
    config = PlainConfig({
        'uploads': Section({
            'db': Section({
                'user': 'root'
            })
        })
    })

    assert config.get_section('uploads').is_section
    assert config.get_section('uploads', 'db').is_section
    assert config.uploads.get_section('db').is_section

    assert config.get_item('uploads', 'db', 'user').is_item
    assert config.uploads.db.get_item('user').is_item

    with pytest.raises(NotFound):
        config.get_item('downloads')

    with pytest.raises(NotFound):
        config.get_section('downloads')

    with pytest.raises(NotFound):
        config.get_item('uploads', 'tmp_dir')

    with pytest.raises(NotFound):
        config.get_section('uploads', 'tmp_dir')


def test_get_item_and_get_section_should_handle_str_paths(simple_config, plain_config):
    assert simple_config.get_item('uploads.db.user') is simple_config.uploads.db.user
    assert simple_config.get_section('uploads.db') is simple_config.uploads.db

    assert plain_config.get_item('uploads.db.user').value == plain_config.uploads.db.user
    assert plain_config.get_section('uploads.db') is plain_config.uploads.db

    custom = Config({'main': simple_config}, str_path_separator='/')

    assert custom.main.uploads.db.user.is_item
    with pytest.raises(NotFound):
        assert custom.get_item('main.uploads.db.user').is_item

    assert custom.get_item('main/uploads/db/user').is_item
