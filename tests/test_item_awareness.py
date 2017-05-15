from configmanager.v1 import Config, Item


def test_item_knows_the_section_it_has_been_added_to():
    enabled = Item(default=False)
    assert enabled.section is None

    uploads = Config({'enabled': enabled})
    assert enabled.section is None  # the original Item is not touched
    assert uploads.enabled.section is uploads

    config = Config({'uploads': uploads})

    assert enabled.section is None
    assert uploads.enabled.section is uploads
    assert config.uploads.enabled is uploads.enabled

    threads = Item(default=5)
    uploads.threads = threads

    assert threads.section is None
    assert uploads.threads.section is uploads

    greeting = Item(default='Hello!')
    uploads['greeting'] = greeting
    assert greeting.section is None
    assert uploads.greeting.section is uploads
