import pytest
import six

from configmanager.utils import not_set
from configmanager.v1 import Item, ConfigValueMissing


def test_missing_required_value_raises_config_value_missing():
    a = Item('a', required=True)

    with pytest.raises(ConfigValueMissing):
        assert a.value is not_set


def test_required_item_falls_back_to_default_when_there_is_one():
    a = Item('a', required=True, default=None)
    assert a.value is None

    a.reset()
    assert a.value is None


def test_item_with_no_value_and_no_default_returns_not_set_as_value():
    c = Item('a')
    assert c.value is not_set

    c.value = 'hey'
    assert c.value == 'hey'

    c.reset()
    assert c.value is not_set


def test_value_gets_stringified():
    c = Item('a', value='23')
    assert c.value == '23'
    assert c.value != 23

    c.value = 24
    assert c.value == '24'
    assert c.value != 24


def test_int_value():
    c = Item('a', type=int, default=25)
    assert c.value == 25

    c.value = '23'
    assert c.value == 23
    assert c.value != '23'

    c.reset()
    assert c.value == 25


def test_raw_str_value_is_reset_on_reset():
    c = Item('a', type=int, default=25)
    assert str(c) == '25'

    c.value = '23'
    assert str(c) == '23'

    c.reset()
    assert str(c) == '25'


def test_raw_str_value_is_reset_on_non_str_value_set():
    c = Item('a', type=int, default=25)
    c.value = '23'
    assert str(c) == '23'

    c.value = 25
    assert str(c) == '25'

    c.value = 24
    assert str(c) == '24'

    c.value = '22'
    assert str(c) == '22'


def test_bool_of_value():
    c = Item('a')

    # not_set evaluates to False
    assert not c.value

    c.value = 'b'
    assert c.value

    c.value = ''
    assert not c.value

    d = Item('a', default='b')
    assert d.value

    d.value = ''
    assert not d.value


def test_repr_makes_clear_name_and_value():
    c = Item('a', default='hello')
    assert repr(c) == '<Item a \'hello\'>'

    c.value = 'bye!'
    assert repr(c) == '<Item a \'bye!\'>'


def test_str_and_repr_of_not_set_value_should_not_fail():
    c = Item('a')
    assert str(c) == '<Item a <NotSet>>'
    assert repr(c) == '<Item a <NotSet>>'


def test_bool_str_is_a_str():
    c = Item('a', type=bool)
    assert isinstance(str(c), six.string_types)

    c.value = True
    assert isinstance(str(c), six.string_types)


def test_bool_config_preserves_raw_str_value_used_to_set_it():
    c = Item('a', type=bool, default=False)
    assert c.value is False

    assert not c.value
    assert str(c) == 'False'
    assert c.value is False

    c.value = 'False'
    assert not c.value
    assert str(c) == 'False'
    assert c.value is False

    c.value = 'no'
    assert not c.value
    assert str(c) == 'no'
    assert c.value is False

    c.value = '0'
    assert not c.value
    assert str(c) == '0'
    assert c.value is False

    c.value = '1'
    assert c.value
    assert str(c) == '1'
    assert c.value is True

    c.reset()
    assert not c.value
    assert c.value is False

    c.value = 'yes'
    assert str(c) == 'yes'
    assert c.value is True


def test_can_set_str_value_to_none():
    c = Item('a', default='haha')
    assert c.value == 'haha'

    c.value = None
    assert c.value is None


def test_setting_value_to_not_set_resets_it():
    c = Item('a', default='default', value='custom')
    assert c.value == 'custom'

    c.value = not_set
    assert c.value == 'default'


def test_can_set_int_value_to_none():
    c = Item('a', type=int, default=0, value=23)
    assert c.value == 23

    c.value = None
    assert c.value is None


def test_equality():
    c = Item('a', type=str, value=None)
    cc = Item('a', type=str, value=None)
    assert c == cc

    d = Item('a', type=int, value=None)
    assert c != d


def test_item_is_equal_to_itself():
    c = Item('a')
    assert c == c

    d = Item('a', value='d')
    assert d == d

    e = Item('a', default='e')
    assert e == e

    f = Item('a', default='f', value='g')
    assert f == f


def test_is_default():
    c = Item('a')
    d = Item('a', default=None)
    e = Item('a', value=None)

    assert c.is_default
    assert d.is_default
    assert not e.is_default

    c.value = 'ccc'
    d.value = 'ddd'
    e.value = 'eee'

    assert not c.is_default
    assert not d.is_default
    assert not e.is_default

    c.value = None
    d.value = None
    e.value = None

    assert not c.is_default
    assert d.is_default  # this is the case when is_default is NOT the opposite of has_value
    assert not e.is_default

    c.reset()
    d.reset()
    e.reset()

    assert c.is_default
    assert d.is_default
    assert e.is_default
