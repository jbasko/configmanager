from configmanager import Config


def test_tracking_context():
    config = Config({
        'greeting': 'Hello, world!',
        'db': {
            'user': 'root',
        },
    })

    ctx1 = config.tracking_context()
    ctx1.push()
    ctx1.pop()

    assert ctx1.changes == {}

    with config.tracking_context() as ctx2:
        pass

    assert ctx2.changes == {}

    assert ctx1.changes == {}
    assert ctx1 is not ctx2

    ctx3 = config.tracking_context()
    ctx3.push()

    config.greeting.value = 'Hey!'
    assert ctx3.changes == {config.greeting: 'Hey!'}

    ctx3.pop()
    assert ctx3.changes == {config.greeting: 'Hey!'}

    # ctx3 is no longer tracking changes
    config.greeting.value = 'What is up!'
    assert ctx3.changes == {config.greeting: 'Hey!'}

    # neither are ctx1 and ctx2
    assert ctx1.changes == {}
    assert ctx2.changes == {}

    # track in ctx3:
    with ctx3:
        config.db.user.value = 'admin'
        assert ctx3.changes == {config.greeting: 'Hey!', config.db.user: 'admin'}
    assert ctx3.changes == {config.greeting: 'Hey!', config.db.user: 'admin'}

    # again, ctx3 is no longer tracking
    config.db.user.value = 'Administrator'

    assert ctx3.changes == {config.greeting: 'Hey!', config.db.user: 'admin'}

    # neither are ctx1 and ctx2
    assert ctx1.changes == {}
    assert ctx2.changes == {}

    # nested contexts

    with ctx1:
        config.db.user.value = 'user-in-ctx1'

        with ctx2:
            config.greeting.value = 'greeting-in-ctx2'

        config.greeting.value = 'greeting-in-ctx1'

    assert ctx1.changes == {config.db.user: 'user-in-ctx1', config.greeting: 'greeting-in-ctx1'}
    assert ctx2.changes == {config.greeting: 'greeting-in-ctx2'}
