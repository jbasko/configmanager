from configmanager.lightweight.items import LwItem


def test_item_default_value_is_deep_copied_on_value_request():
    precious_things = ['a', 'b']
    c = LwItem(default=precious_things)

    c.value.append('c')  # This has no effect because the value was created on the fly and no-one stored it.

    assert c.value == ['a', 'b']
    assert c.default == ['a', 'b']
    assert precious_things == ['a', 'b']


def test_item_value_is_not_deep_copied_on_value_request():
    precious_things = ['a', 'b']
    c = LwItem(default=precious_things)

    c.value = ['c', 'd']
    c.value.append('e')

    assert c.value == ['c', 'd', 'e']
    assert c.default == ['a', 'b']
