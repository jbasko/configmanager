"""
Most section tests are in test_config.
Here are tests just to test Section usage outside of Configs.
"""
import pytest

from configmanager import Section, NotFound


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
