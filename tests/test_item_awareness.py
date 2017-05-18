from configmanager import Config, Item


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


def test_section_knows_the_section_it_has_been_added_to():
    uploads_config = Config({'enabled': True})
    downloads_config = Config({'enabled': False})

    assert not uploads_config.section
    assert not downloads_config.section

    main_config = Config({
        'uploads': uploads_config,
        'downloads': downloads_config,
    })
    assert uploads_config.section is main_config
    assert downloads_config.section is main_config

    # Adding to another section updates the state
    app_config = Config({
        'up': uploads_config,
    })

    assert uploads_config.section is app_config
    assert downloads_config.section is main_config
