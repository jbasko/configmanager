import pytest

from configmanager import Config, Item
from configmanager.exceptions import NotFound, RequiredValueMissing
from configmanager.utils import not_set


def test_not_found_raised_for_unknown_items_and_sections_and_paths_in_section():
    config = Config({
        'uploads': {
            'db': {
                'user': 'root',
            }
        },
    })

    with pytest.raises(NotFound):
        _ = config.downloads

    with pytest.raises(NotFound):
        _ = config.uploads.api

    with pytest.raises(NotFound):
        _ = config.uploads.db.password

    with pytest.raises(NotFound):
        _ = config['downloads']

    with pytest.raises(NotFound):
        _ = config['uploads', 'api']

    with pytest.raises(NotFound):
        _ = config['uploads']['db']['password']

    with pytest.raises(NotFound):
        _ = config['downloads',]

    with pytest.raises(NotFound):
        _ = config['uploads', 'api']

    with pytest.raises(NotFound):
        _ = config['uploads', 'db', 'password']


def test_standard_exceptions_raised_for_unknown_attributes_of_item():
    config = Config({'greeting': 'Hello'})

    with pytest.raises(AttributeError):
        _ = config.greeting.something

    with pytest.raises(TypeError):
        _ = config.greeting['something']


def test_not_found_includes_section():
    config = Config({
        'uploads': {
            'db': {}
        }
    })

    with pytest.raises(NotFound) as exc1:
        _ = config.greeting

    assert exc1.value.name == 'greeting'
    assert exc1.value.section is config

    with pytest.raises(NotFound) as exc2:
        _ = config.uploads.threads

    assert exc2.value.name == 'threads'
    assert exc2.value.section is config.uploads


def test_required_value_missing_includes_item():
    item1 = Item(required=True)

    with pytest.raises(RequiredValueMissing) as exc1:
        _ = item1.value

    assert exc1.value.name is not_set
    assert exc1.value.item is item1

    item2 = Item(name='greeting', required=True)

    with pytest.raises(RequiredValueMissing) as exc2:
        _ = item2.value

    assert exc2.value.name == 'greeting'
    assert exc2.value.item is item2


def test_not_found_raised_by_iterators_on_first_not_found_name_in_path():
    config = Config({'uploads': {'db': {'user': 'root'}}})

    with pytest.raises(NotFound) as exc1:
        list(config.iter_all(recursive=True, path=('downloads',)))
    assert exc1.value.name == 'downloads'

    with pytest.raises(NotFound) as exc2:
        _ = config['uploads', 'enabled']
    assert exc2.value.name == 'enabled'

    with pytest.raises(NotFound) as exc3:
        _ = config['uploads', 'something', 'deep']
    assert exc3.value.name == 'something'
