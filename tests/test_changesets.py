from configmanager import Config
from configmanager.utils import not_set


def test_changeset_context():
    config = Config({
        'greeting': 'Hello, world!',
        'db': {
            'user': 'root',
        },
    })

    ctx1 = config.changeset_context()
    ctx1.push()
    ctx1.pop()

    assert ctx1.values == {}

    with config.changeset_context() as ctx2:
        pass

    assert ctx2.values == {}

    assert ctx1.values == {}
    assert ctx1 is not ctx2

    ctx3 = config.changeset_context()
    ctx3.push()

    config.greeting.value = 'Hey!'
    assert ctx3.values == {config.greeting: 'Hey!'}

    ctx3.pop()
    assert ctx3.values == {config.greeting: 'Hey!'}

    # ctx3 is no longer tracking changes
    config.greeting.value = 'What is up!'
    assert ctx3.values == {config.greeting: 'Hey!'}

    # neither are ctx1 and ctx2
    assert ctx1.values == {}
    assert ctx2.values == {}

    # track in ctx3:
    with ctx3:
        config.db.user.value = 'admin'
        assert ctx3.values == {config.greeting: 'Hey!', config.db.user: 'admin'}
    assert ctx3.values == {config.greeting: 'Hey!', config.db.user: 'admin'}

    # again, ctx3 is no longer tracking
    config.db.user.value = 'Administrator'

    assert ctx3.values == {config.greeting: 'Hey!', config.db.user: 'admin'}

    # neither are ctx1 and ctx2
    assert ctx1.values == {}
    assert ctx2.values == {}

    # nested contexts

    with ctx1:
        config.db.user.value = 'user-in-ctx1'

        with ctx2:
            config.greeting.value = 'greeting-in-ctx2'

        config.greeting.value = 'greeting-in-ctx1'

    assert ctx1.values == {config.db.user: 'user-in-ctx1', config.greeting: 'greeting-in-ctx1'}
    assert ctx2.values == {config.greeting: 'greeting-in-ctx2'}


def test_reset_changes_resets_changes_in_context_and_on_items():
    config = Config({
        'a': 'A1',
        'b': 'B1',
        'c': 'C1',
        'd': 'D1',
    })

    with config.changeset_context() as ctx1:
        config.a.value = 'A2'
        config.c.value = 'C2'

        assert config.a.value == 'A2'
        assert config.c.value == 'C2'

        assert ctx1.values == {
            config.a: 'A2',
            config.c: 'C2',
        }

        ctx1.reset()

        assert ctx1.values == {}

    assert config.a.value == 'A1'
    assert config.b.value == 'B1'
    assert config.c.value == 'C1'
    assert config.d.value == 'D1'

    config.a.value = 'A3'
    config.b.value = 'B3'
    config.c.value = 'C3'

    with config.changeset_context() as ctx2:
        ctx2.reset()

        assert len(ctx2.values) == 0

        assert config.a.value == 'A3'
        assert config.b.value == 'B3'
        assert config.c.value == 'C3'
        assert config.d.value == 'D1'

        config.a.value = 'A4'
        config.b.value = 'B4'

        assert len(ctx2.values) == 2

        assert config.a.value == 'A4'
        assert config.b.value == 'B4'
        assert config.c.value == 'C3'
        assert config.d.value == 'D1'

        # Reset single
        ctx2.reset(config.b)
        assert len(ctx2.values) == 1
        assert config.a.value == 'A4'
        assert config.b.value == 'B3'

        # Reset all
        ctx2.reset()
        assert len(ctx2.values) == 0

    assert config.a.value == 'A3'
    assert config.b.value == 'B3'
    assert config.c.value == 'C3'
    assert config.d.value == 'D1'


def test_tracking_of_tricky_change_and_no_change_situations():
    config = Config({'a': 'aaa'})

    # Set custom value that matches the default. Should be tracked.
    with config.changeset_context() as ctx:
        assert len(ctx.values) == 0

        config.a.value = 'aaa'
        assert len(ctx.values) == 1

        config.reset()
        assert len(ctx.values) == 0

    # No custom value set to start with
    with config.changeset_context() as ctx:
        assert len(ctx.values) == 0

        # Set custom value
        config.a.value = 'bbb'
        assert len(ctx.values) == 1
        assert ctx.values[config.a] == 'bbb'

        # Set custom value which matches default value -- it still is a change.
        config.a.value = 'aaa'
        assert len(ctx.values) == 1
        assert ctx.values[config.a] == 'aaa'

        config.reset()
        assert len(ctx.values) == 0

    # Have a custom value to start with
    config.a.value = 'ccc'
    with config.changeset_context() as ctx:

        # Make one change
        config.a.value = 'ddd'
        assert len(ctx.values) == 1
        assert ctx.values[config.a] == 'ddd'

        # Change back to the original value (within this context), should result in no changes
        config.a.value = 'ccc'
        assert len(ctx.values) == 0

        # Reset still results in a change within this context.
        config.reset()
        assert len(ctx.values) == 1
        assert ctx.values[config.a] == not_set


def test_tracking_with_no_default_and_no_custom_value():
    config = Config({'a': {'@type': 'int'}})

    with config.changeset_context() as ctx:
        config.a.value = 55

    assert ctx.values[config.a] == 55
    assert len(ctx.values) == 1

    ctx.reset()
    assert len(ctx.values) == 0


def test_item_reset_is_tracked():
    config = Config({'a': 'aaa'})
    config.a.value = 'bbb'

    with config.changeset_context() as ctx:
        config.a.value = 'ccc'
        assert len(ctx.values) == 1

        config.reset()
        assert len(ctx.values) == 1

    assert ctx.values[config.a] is not_set


def test_resets_single_item_changes():
    config = Config({'a': 'aaa', 'b': 'bbb', 'c': 'ccc'})

    config.c.value = 'CCC'

    assert config.a.raw_str_value is not_set
    assert config.c.raw_str_value == 'CCC'

    with config.changeset_context() as ctx:

        config.a.value = 'AAA'
        config.b.value = 'BBB'
        config.c.value = 'seeseesee'
        assert config.c.raw_str_value == 'seeseesee'

        assert len(ctx.values) == 3

        ctx.reset(config.a)

        assert len(ctx.values) == 2
        assert ctx.values[config.b] == 'BBB'
        assert ctx.values[config.c] == 'seeseesee'

        assert config.a.value == 'aaa'
        assert config.b.value == 'BBB'
        assert config.c.value == 'seeseesee'

        ctx.reset(config.c)

        assert config.a.value == 'aaa'
        assert config.b.value == 'BBB'
        assert config.c.value == 'CCC'

    assert config.a.raw_str_value is not_set
    assert config.c.raw_str_value == 'CCC'


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

    with config.changeset_context() as ctx:
        config.uploads.a.value = 2
        config.downloads.d.e.value = 'EEE'
        config.downloads.f.value = 'FFF'

    assert len(ctx.values) == 3
    assert ctx.values[config.uploads.a] == 2
    assert ctx.values[config.downloads.d.e] == 'EEE'
    assert ctx.values[config.downloads.f] == 'FFF'

    assert not config.is_default
    assert config.uploads.a.value == 2
    assert config.downloads.d.e.value == 'EEE'
    assert config.downloads.f.value == 'FFF'

    ctx.reset()
    assert config.is_default


def test_change_is_a_merge_of_all_changes_in_context():
    config = Config({
        'a': 1,
    })

    config.a.set('2')

    with config.changeset_context() as ctx:
        config.a.set(3)
        config.a.set(4)
        config.a.set('5')

        assert ctx.changes[config.a].old_value == 2
        assert ctx.changes[config.a].old_raw_str_value == '2'
        assert ctx.changes[config.a].new_value == 5
        assert ctx.changes[config.a].new_raw_str_value == '5'

        config.a.set(6)

        assert ctx.changes[config.a].old_value == 2
        assert ctx.changes[config.a].old_raw_str_value == '2'
        assert ctx.changes[config.a].new_value == 6
        assert ctx.changes[config.a].new_raw_str_value is not_set

        ctx.reset()

        assert config.a not in ctx.changes


def test_changing_raw_str_value_is_still_a_change():
    config = Config({'a': True})
    config.a.set('yes')

    with config.changeset_context() as ctx:
        # The value actually hasn't changed, but the raw string value has, so we are reporting changes.
        config.a.set('on')

        assert config.a in ctx.changes
        assert ctx.changes[config.a].old_raw_str_value == 'yes'
        assert ctx.changes[config.a].new_raw_str_value == 'on'
        assert ctx.values[config.a] is True

        config.a.set('off')
        assert config.a in ctx.changes
        assert ctx.changes[config.a].old_raw_str_value == 'yes'
        assert ctx.changes[config.a].new_raw_str_value == 'off'
        assert ctx.values[config.a] is False

        config.a.set('yes')
        assert config.a not in ctx.changes
        assert config.a not in ctx.values


def test_length_of_changeset_is_the_number_of_changes_and_truth_value_respects_it():
    config = Config({'a': True, 'b': 1})
    config.a.set('yes')

    with config.changeset_context() as ctx:
        assert len(ctx) == 0
        assert not ctx

        config.a.set('on')
        assert len(ctx) == 1
        assert ctx

        config.a.set('yes')
        assert len(ctx) == 0
        assert not ctx

        config.b.set(2)
        assert len(ctx) == 1
        assert ctx

        config.a.set('off')
        assert len(ctx) == 2
        assert ctx
