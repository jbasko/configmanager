# -*- coding: utf-8 -*-

import pytest
import six
from builtins import str

from configmanager.utils import not_set
from configmanager import Item, RequiredValueMissing, Types


def test_required_value_missing_raised_when_required_value_missing():
    a = Item('a', required=True)

    with pytest.raises(RequiredValueMissing):
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
    assert c.str_value == '25'

    c.value = '23'
    assert c.str_value == '23'

    c.reset()
    assert c.str_value == '25'


def test_raw_str_value_is_reset_on_non_str_value_set():
    c = Item('a', type=int, default=25)
    c.value = '23'
    assert c.str_value == '23'

    c.value = 25
    assert c.str_value == '25'

    c.value = 24
    assert c.str_value == '24'

    c.value = '22'
    assert c.str_value == '22'


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
    assert c.str_value == '<Item a <NotSet>>'
    assert repr(c) == '<Item a <NotSet>>'


def test_bool_str_is_a_str():
    c = Item('a', type=bool)
    assert isinstance(c.str_value, six.string_types)

    c.value = True
    assert isinstance(c.str_value, six.string_types)


def test_bool_config_preserves_raw_str_value_used_to_set_it():
    c = Item('a', type=bool, default=False)
    assert c.value is False

    assert not c.value
    assert c.str_value == 'False'
    assert c.value is False

    c.value = 'False'
    assert not c.value
    assert c.str_value == 'False'
    assert c.value is False

    c.value = 'no'
    assert not c.value
    assert c.str_value == 'no'
    assert c.value is False

    c.value = '0'
    assert not c.value
    assert c.str_value == '0'
    assert c.value is False

    c.value = '1'
    assert c.value
    assert c.str_value == '1'
    assert c.value is True

    c.reset()
    assert not c.value
    assert c.value is False

    c.value = 'yes'
    assert c.str_value == 'yes'
    assert c.value is True


def test_can_set_str_value_to_none():
    c = Item('a', default='haha')
    assert c.value == 'haha'
    assert c.type is Types.str

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


def test_has_value_returns_true_if_value_or_default_is_set():
    c = Item()
    assert not c.has_value
    c.value = '5'
    assert c.has_value
    c.reset()
    assert not c.has_value

    d = Item(default=5)
    assert d.has_value
    d.value = 6
    assert d.has_value
    d.reset()
    assert d.has_value

    e = Item(value=8)
    assert e.has_value
    e.value = 9
    assert e.has_value
    e.reset()
    assert not e.has_value


def test_type_is_guessed_either_from_default_or_value():
    c = Item()
    assert c.type is Types.str

    c = Item(value='haha')
    assert c.type is Types.str

    c = Item(value=u'hāhā')
    assert c.type is Types.str
    assert c.value == u'hāhā'
    assert c.str_value == u'hāhā'

    c = Item(default='haha')
    assert c.type is Types.str

    c = Item(default=u'haha')
    assert c.type is Types.str

    d = Item(default=5)
    assert d.type is Types.int

    e = Item(value=5)
    assert e.type is Types.int

    f = Item(default=None, value=5)
    assert f.type is Types.int


def test_item_default_value_is_deep_copied_on_value_request():
    precious_things = ['a', 'b']
    c = Item(default=precious_things)

    c.value.append('c')  # This has no effect because the value was created on the fly and no-one stored it.

    assert c.value == ['a', 'b']
    assert c.default == ['a', 'b']
    assert precious_things == ['a', 'b']


def test_item_value_is_not_deep_copied_on_value_request():
    precious_things = ['a', 'b']
    c = Item(default=precious_things)

    c.value = ['c', 'd']
    c.value.append('e')

    assert c.value == ['c', 'd', 'e']
    assert c.default == ['a', 'b']


def test_item_value_can_be_unicode_str():
    c = Item(default=u'Jānis Bērziņš')
    assert c.str_value == u'Jānis Bērziņš'

    c.value = u'Pēteris Liepiņš'
    assert c.str_value == u'Pēteris Liepiņš'
    assert c.default == u'Jānis Bērziņš'


def test_item_is_item_and_is_not_section():
    c = Item()
    assert c.is_item
    assert not c.is_section


def test_item_sets_unrecognised_kwargs_as_attributes():
    c = Item(help='This is help', comment='This is comment', default=5, something_random=True)
    c.value = 5

    assert c.is_default
    assert c.help == 'This is help'
    assert c.comment == 'This is comment'
    assert c.something_random

    with pytest.raises(AttributeError):
        assert c.something_too_random


def test_item_treats_kwargs_with_at_symbol_prefix_as_normal_attributes():
    c = Item(**{'@name': 'threads', '@default': 5, '@comment': 'This is comment', 'help': 'This is help'})
    assert c.name == 'threads'
    assert c.default == 5
    assert c.value == 5
    assert c.comment == 'This is comment'
    assert c.help == 'This is help'


def test_items_allows_special_attributes_to_be_prefixed_with_at_symbol_too():
    s = Item(**{'@type': bool, '@value': 'no'})
    assert s.type is Types.bool
    assert s.value is False

    s.value = 'yes'
    assert s.value is True

    t = Item(**{'@default': True})
    assert t.type is Types.bool
    assert t.value is True

    t.value = 'no'
    assert t.value is False


def test_item_attribute_names_should_start_with_a_letter():
    with pytest.raises(ValueError):
        Item(**{'_comment': 'This must fail'})


def test_non_special_default_values_are_converted_to_items_declared_type():
    i = Item(type=int, default='3')
    assert i.default == 3

    b = Item(type=bool, default='yes')
    assert b.default is True

    f = Item(type=float, default='0.23')
    assert f.default == 0.23


def test_item_type_can_be_specified_as_a_string():
    i = Item(type='int', default='3')
    assert i.default == 3

    b = Item(type='boolean', default='yes')
    assert b.default is True

    f = Item(type='float', default='0.23')
    assert f.default == 0.23
