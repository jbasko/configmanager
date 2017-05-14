import pytest

from configmanager.lightweight.managers import LwConfig
from configmanager.lightweight.items import LwItem


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
    return LwConfig({
        'logging': LwConfig(raw_logging_config),
        'db': raw_db_config,
    })


def test_declaration_parser_does_not_modify_config(raw_logging_config):
    logging_config = LwConfig(raw_logging_config)
    assert isinstance(logging_config, LwConfig)

    assert logging_config['version']
    assert logging_config['formatters']

    config = LwConfig({'logging': logging_config})
    assert isinstance(config, LwConfig)

    assert config['logging']['version']
    assert config['logging']['formatters']

    assert config['logging']['formatters'] is logging_config['formatters']

    logging_config['version'].value = '2'
    assert config['logging']['version'].value == 2


def test_allows_iteration_over_all_items(mixed_app_config):
    config = mixed_app_config

    all_items = list(config.iter_items())
    assert len(all_items) == 14

    db_items = list(config['db'].iter_items())
    assert len(db_items) == 4

    formatters_items = list(config['logging']['formatters'].iter_items())
    assert len(formatters_items) == 2

    formatters = config['logging']['formatters'].to_dict()
    assert formatters['plain'] == {'format': '%(message)s'}


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

    assert len(dict(sections['db'].iter_sections())) == 0

    logging_sections = dict(sections['logging'].iter_sections())
    assert len(logging_sections) == 3


def test_attribute_read_access(mixed_app_config):
    config = mixed_app_config

    assert isinstance(config.db, LwConfig)
    assert isinstance(config.db.username, LwItem)
    assert isinstance(config.logging.handlers, LwConfig)
    assert isinstance(config.logging.handlers.default, LwConfig)
    assert isinstance(config.logging.loggers[''].handlers, LwItem)
    assert isinstance(config.logging.loggers[''].level, LwItem)


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

    config_dict = config.to_dict()

    assert isinstance(config_dict, dict)

    assert config_dict['db'] is not raw_db_config
    assert config_dict['db'] == raw_db_config
    assert config_dict['logging'] == raw_logging_config


def test_can_inspect_config_contents(mixed_app_config):
    config = mixed_app_config

    assert 'db' in config
    assert 'dbe' not in config
    assert ('db',) not in config

    assert 'logging' in config

    assert 'handlers' in config.logging
    assert '' in config.logging.loggers
    assert 'haha' not in config.logging.loggers


def test_can_have_a_dict_as_a_config_value_if_wrapped_inside_item():
    # You may want to have a dictionary as a config value if you only
    # change it all together or you only pass it all in one piece.

    config = LwConfig({
        'db': {
            'user': 'admin',
            'password': 'secret',
        },
        'aws': LwItem(default={
            'access_key': '123',
            'secret_key': 'secret',
        })
    })

    assert isinstance(config.aws, LwItem)
    assert config.aws.name == 'aws'

    with pytest.raises(AttributeError):
        assert config.aws.access_key.value == '123'

    assert config.aws.value['access_key'] == '123'

    # This should have no effect because it is working on a copy of the default
    # value, not the real thing.
    config.aws.value['secret_key'] = 'NEW_SECRET'

    assert config.to_dict()['aws'] == {'access_key': '123', 'secret_key': 'secret'}
