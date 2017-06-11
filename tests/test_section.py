"""
Most section tests are in test_config.
Here are tests just to test Section usage outside of Configs.
"""
from configmanager import Section


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

    assert config.uploads.db._settings is config._settings
    assert config.uploads._settings is config._settings

    calls = []

    @config.hooks.item_value_changed
    def value_changed(**kwargs):
        calls.append(1)

    assert len(calls) == 0

    config.uploads.db.user.value = 'admin'

    assert len(calls) == 1
