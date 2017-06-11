"""
Most section tests are in test_config.
Here are tests just to test Section usage outside of Configs.
"""
import pytest

from configmanager import Section, NotFound


def test_free_floating_sections_share_the_same_default_settings():
    s1 = Section()
    s2 = Section()

    assert s1.settings is s2.settings

    s3 = Section({
        's1': s1,
        's2': s2,
    })

    assert s3.settings is s1.settings
    assert s3.settings is s2.settings
    assert s3.settings is s3.s1.settings
    assert s3.settings is s3.s2.settings


def test_section_default_settings_are_immutable():
    s1 = Section()
    s2 = Section()

    assert s1.settings.load_sources == []

    s1.settings.load_sources.append('config.json')
    assert s1.settings.load_sources == []
    assert s2.settings.load_sources == []


def test_section_created_from_schema():
    uploads = Section({
        'enabled': True,
        'threads': 1,
    })

    assert uploads.is_section

    assert uploads.enabled.is_item
    assert uploads.enabled.value is True

    assert uploads.threads.is_item
    assert uploads.threads.value == 1


def test_nested_section_created_from_schema():
    config = Section({
        'uploads': Section({
            'db': Section({
                'user': 'root'
            })
        })
    })

    assert config.uploads.db.settings is config.settings
    assert config.uploads.settings is config.settings

    calls = []

    @config.hooks.item_value_changed
    def value_changed(**kwargs):
        calls.append(1)

    assert len(calls) == 0

    config.uploads.db.user.value = 'admin'

    assert len(calls) == 1


def test_items_and_sections_with_python_keywords_as_names_can_be_accessed_with_suffixed_attr_names():
    config = Section({
        'for': {
            'if': {
                'assert': 'assert',
                'True': 'True',
            },
            'import': 'import',
            'and': 'and',
        },
        'not_keyword': {
            'really': True,
        }
    })

    assert config['for'].is_section
    assert config.for_.is_section

    assert config['for', 'if', 'assert'].is_item
    assert config['for_', 'if_', 'assert_'].is_item
    assert config.for_.if_.assert_.is_item

    assert config.for_.import_.value == 'import'

    # Make sure non-keywords cannot be accessed with suffixed attribute name
    with pytest.raises(NotFound):
        assert config.not_keyword_.is_section

    assert config.not_keyword.is_section

    with pytest.raises(NotFound):
        assert config.not_keyword.really_.is_item

    assert config.not_keyword.really.is_item

    # Make sure iterators like those paths too
    paths1 = list(config.iter_paths(path='for_', recursive=True))
    paths2 = list(config.iter_paths(path='for', recursive=True))
    assert paths1 == paths2
