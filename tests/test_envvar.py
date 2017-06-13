from configmanager import Section


def test_envvar_attribute_enables_value_override_via_envvars(monkeypatch):
    config = Section({
        'uploads': {
            'threads': 1
        }
    })

    assert config.uploads.threads.envvar is None
    assert config.uploads.threads.envvar_name is None
    assert config.uploads.threads.value == 1

    config.uploads.threads.envvar = True
    assert config.uploads.threads.value == 1

    monkeypatch.setenv('UPLOADS_THREADS', '23')
    assert config.uploads.threads.value == 23

    config.uploads.threads.envvar_name = 'OTHER_UPLOADS_THREADS'
    assert config.uploads.threads.value == 1

    monkeypatch.setenv('OTHER_UPLOADS_THREADS', '42')
    assert config.uploads.threads.value == 42

    config.uploads.threads.envvar = False
    assert config.uploads.threads.value == 1

    config.uploads.threads.envvar = 'UPLOADS_THREADS'
    assert config.uploads.threads.value == 23

    config.uploads.threads.envvar = 'OTHER_UPLOADS_THREADS'
    assert config.uploads.threads.value == 42

    config.uploads.threads.envvar = 'SOMETHING_NONEXISTENT'
    assert config.uploads.threads.value == 1


def test_dynamic_override_of_envvar_name(monkeypatch):
    config = Section({
        'uploads': {
            'threads': 1
        }
    })

    assert config.uploads.threads.envvar_name is None

    @config.item_attribute
    def envvar_name(item=None, **kwargs):
        return 'TEST_{}'.format('_'.join(item.get_path()).upper())

    assert config.uploads.threads.envvar_name == 'TEST_UPLOADS_THREADS'

    assert config.uploads.threads.value == 1

    # This has no immediate effect because envvar is still None
    monkeypatch.setenv('TEST_UPLOADS_THREADS', '23')
    assert config.uploads.threads.value == 1

    # This changes everything
    config.uploads.threads.envvar = True
    assert config.uploads.threads.value == 23

    # But, if envvar is set to a name, envvar_name doesn't matter again
    config.uploads.threads.envvar = 'OTHER_UPLOADS_THREADS'
    assert config.uploads.threads.value == 1

    monkeypatch.setenv('OTHER_UPLOADS_THREADS', '42')
    assert config.uploads.threads.value == 42
