from configmanager.v1 import Config, Item


def test_item_knows_the_section_it_has_been_added_to():
    enabled = Item(default=False)
    assert enabled.section is None

    uploads = Config({'enabled': enabled})
    assert enabled.section is uploads

    config = Config({'uploads': uploads})

    assert enabled.section is config.uploads

    threads = Item(default=5)
    uploads.threads = threads

    assert threads.section is config.uploads

    greeting = Item(default='Hello!')
    uploads['greeting'] = greeting
    assert greeting.section is uploads
