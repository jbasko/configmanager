from configmanager import Config
from configmanager.utils import not_set


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


def test_reset_changes_resets_changes_in_context_and_on_items():
    config = Config({
        'a': 'A1',
        'b': 'B1',
        'c': 'C1',
        'd': 'D1',
    })

    with config.tracking_context() as ctx1:
        config.a.value = 'A2'
        config.c.value = 'C2'

        assert config.a.value == 'A2'
        assert config.c.value == 'C2'

        assert ctx1.changes == {
            config.a: 'A2',
            config.c: 'C2',
        }

        ctx1.reset_changes()

        assert ctx1.changes == {}

    assert config.a.value == 'A1'
    assert config.b.value == 'B1'
    assert config.c.value == 'C1'
    assert config.d.value == 'D1'

    config.a.value = 'A3'
    config.b.value = 'B3'
    config.c.value = 'C3'

    with config.tracking_context() as ctx2:
        ctx2.reset_changes()

        assert len(ctx2.changes) == 0

        assert config.a.value == 'A3'
        assert config.b.value == 'B3'
        assert config.c.value == 'C3'
        assert config.d.value == 'D1'

        config.a.value = 'A4'
        config.b.value = 'B4'

        assert len(ctx2.changes) == 2

        assert config.a.value == 'A4'
        assert config.b.value == 'B4'
        assert config.c.value == 'C3'
        assert config.d.value == 'D1'

        # Reset single
        ctx2.reset_changes(config.b)
        assert len(ctx2.changes) == 1
        assert config.a.value == 'A4'
        assert config.b.value == 'B3'

        # Reset all
        ctx2.reset_changes()
        assert len(ctx2.changes) == 0

    assert config.a.value == 'A3'
    assert config.b.value == 'B3'
    assert config.c.value == 'C3'
    assert config.d.value == 'D1'


def test_tracking_of_tricky_change_and_no_change_situations():
    config = Config({'a': 'aaa'})

    # Set custom value that matches the default. Should be tracked.
    with config.tracking_context() as ctx:
        assert len(ctx.changes) == 0

        config.a.value = 'aaa'
        assert len(ctx.changes) == 1

        config.reset()
        assert len(ctx.changes) == 0

    # No custom value set to start with
    with config.tracking_context() as ctx:
        assert len(ctx.changes) == 0

        # Set custom value
        config.a.value = 'bbb'
        assert len(ctx.changes) == 1
        assert ctx.changes[config.a] == 'bbb'

        # Set custom value which matches default value -- it still is a change.
        config.a.value = 'aaa'
        assert len(ctx.changes) == 1
        assert ctx.changes[config.a] == 'aaa'

        config.reset()
        assert len(ctx.changes) == 0

    # Have a custom value to start with
    config.a.value = 'ccc'
    with config.tracking_context() as ctx:

        # Make one change
        config.a.value = 'ddd'
        assert len(ctx.changes) == 1
        assert ctx.changes[config.a] == 'ddd'

        # Change back to the original value (within this context), should result in no changes
        config.a.value = 'ccc'
        assert len(ctx.changes) == 0

        # Reset still results in a change within this context.
        config.reset()
        assert len(ctx.changes) == 1
        assert ctx.changes[config.a] == not_set


def test_tracking_with_no_default_and_no_custom_value():
    config = Config({'a': {'@type': 'int'}})

    with config.tracking_context() as ctx:
        config.a.value = 55

    assert ctx.changes[config.a] == 55
    assert len(ctx.changes) == 1

    ctx.reset_changes()
    assert len(ctx.changes) == 0


def test_item_reset_is_tracked():
    config = Config({'a': 'aaa'})
    config.a.value = 'bbb'

    with config.tracking_context() as ctx:
        config.a.value = 'ccc'
        assert len(ctx.changes) == 1

        config.reset()
        assert len(ctx.changes) == 1

    assert ctx.changes[config.a] is not_set


def test_resets_single_item_changes():
    config = Config({'a': 'aaa', 'b': 'bbb'})

    with config.tracking_context() as ctx:

        config.a.value = 'AAA'
        config.b.value = 'BBB'

        assert len(ctx.changes) == 2

        ctx.reset_changes(config.a)

        assert len(ctx.changes) == 1
        assert ctx.changes[config.b] == 'BBB'

        assert config.a.value == 'aaa'
        assert config.b.value == 'BBB'


def test_config_of_configs():
    config = Config({
        'uploads': Config({
            'a': 1,
            'b': True,
            'c': 'ccc',
        }),
        'downloads': Config({
            'd': {
                'e': 'eee',
            },
            'f': 'fff',
        }),
    })

    with config.tracking_context() as ctx:
        config.uploads.a.value = 2
        config.downloads.d.e.value = 'EEE'
        config.downloads.f.value = 'FFF'

    assert len(ctx.changes) == 3
    assert ctx.changes[config.uploads.a] == 2
    assert ctx.changes[config.downloads.d.e] == 'EEE'
    assert ctx.changes[config.downloads.f] == 'FFF'

    assert not config.is_default
    assert config.uploads.a.value == 2
    assert config.downloads.d.e.value == 'EEE'
    assert config.downloads.f.value == 'FFF'

    ctx.reset_changes()
    assert config.is_default
