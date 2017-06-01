import pytest

from configmanager.utils import not_set
from configmanager import Item, RequiredValueMissing


def test_get_returns_value_when_value_is_set():
    assert Item(value=5).get() == 5
    assert Item(value=5).get(10) == 5
    assert Item(value=None).get(20) is None


def test_get_with_no_value_and_no_default_returns_not_set():
    assert Item().get() is not_set


def test_get_returns_fallback_when_no_value_and_no_default_is_set():
    assert Item().get(None) is None
    assert Item(type=int).get(30) == 30


def test_get_required_with_no_value_and_no_default_returns_fallback_if_available():
    assert Item(required=True).get('a') == 'a'

    with pytest.raises(RequiredValueMissing):
        Item(required=True).get()


def test_get_returns_default_value_when_available():
    assert Item(default='a').get() == 'a'
    assert Item(default='b').get('c') == 'b'
    assert Item(default=None).get('d') is None


def test_get_returns_value_when_value_and_default_available():
    assert Item(default='a', value=None).get() is None
    assert Item(default='a', value='b').get() == 'b'
    assert Item(default=None, value=None).get(True) is None
    assert Item(default='a', value='b').get('c') == 'b'


def test_value_calls_get_so_users_can_extend_item_class_by_overriding_just_get():
    class CustomItem(Item):
        def get(self, fallback=not_set):
            return 55

    item = CustomItem(name='a', value=30, default=0)
    assert item.value == 55

    item.reset()
    assert item.value == 55


def test_set_sets_value():
    a = Item(type=int)
    assert not a.has_value

    a.set(5)
    assert a.has_value
    assert a.value == 5

    b = Item(default=55)
    b.set(5)
    assert b.value == 5


def test_value_setting_calls_set_so_users_can_extend_item_class_by_overriding_just_set():
    class CustomItem(Item):
        def set(self, value):
            super(CustomItem, self).set(value * 2)

    item = CustomItem(value=0)
    item.value = 3
    assert item.value == 6
