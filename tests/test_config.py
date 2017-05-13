import pytest
import six

from configmanager import ConfigItem, ConfigValueMissing
from configmanager.utils import not_set


def test_section_and_option_is_only_supported_for_trivial_paths():
    c = ConfigItem('a', 'b')
    assert c.section == 'a'
    assert c.option == 'b'

    d = ConfigItem('d')
    assert d.section == d.DEFAULT_SECTION
    assert d.option == 'd'

    e = ConfigItem('ee', 'ff', 'gg')
    with pytest.raises(RuntimeError):
        assert e.section

    with pytest.raises(RuntimeError):
        assert e.option

    assert e.strpath == 'ee/ff/gg'
    assert e.path == ('ee', 'ff', 'gg')


def test_config_item_name_is_last_segment_of_path():
    c = ConfigItem('c')
    assert c.name == 'c'

    d = ConfigItem('dd', 'ddd')
    assert d.name == 'ddd'

    e = ConfigItem('ee', 'eee', 'eeee')
    assert e.name == 'eeee'


def test_initialisation_with_default_section():
    c = ConfigItem('option1')
    assert c.section == 'DEFAULT'
    assert c.option == 'option1'


@pytest.mark.parametrize('args', [
    (True, True),
    ('section', True),
    (True, 'section'),
    (123, 456),
])
def test_paths_with_non_string_segments_raise_type_error(args):
    with pytest.raises(TypeError):
        ConfigItem(*args)


def test_missing_required_value_raises_config_value_missing():
    c = ConfigItem('a', 'b', required=True)

    with pytest.raises(ConfigValueMissing):
        assert c.value is not_set


def test_required_item_can_still_fall_back_to_default():
    c = ConfigItem('a', 'b', required=True, default=None)
    assert c.value is None

    c.reset()
    assert c.value is None


def test_item_with_no_value_and_no_default_returns_not_set_as_value():
    c = ConfigItem('a', 'b')
    assert c.value is not_set

    c.value = 'hey'
    assert c.value == 'hey'

    c.reset()
    assert c.value is not_set


def test_value_with_default_value():
    c = ConfigItem('a', 'b', default='c')

    assert not c.has_value
    assert c.has_default
    assert c.value == 'c'

    c.value = 'd'

    assert c.has_value
    assert c.has_default
    assert c.value == 'd'

    c.reset()
    assert not c.has_value
    assert c.has_default
    assert c.value == 'c'

    d = ConfigItem('a', 'b', default='c', value='d')
    assert d.value == 'd'

    d.value = 'e'
    assert d.value == 'e'

    d.reset()
    assert d.value == 'c'


def test_value_gets_stringified():
    c = ConfigItem('a', value='23')
    assert c.value == '23'
    assert c.value != 23

    c.value = 24
    assert c.value == '24'
    assert c.value != 24


def test_int_value():
    c = ConfigItem('a', type=int, default=25)
    assert c.value == 25

    c.value = '23'
    assert c.value == 23
    assert c.value != '23'

    c.reset()
    assert c.value == 25


def test_raw_str_value_is_reset_on_reset():
    c = ConfigItem('a', type=int, default=25)
    assert str(c) == '25'

    c.value = '23'
    assert str(c) == '23'

    c.reset()
    assert str(c) == '25'


def test_raw_str_value_is_reset_on_non_str_value_set():
    c = ConfigItem('a', type=int, default=25)
    c.value = '23'
    assert str(c) == '23'

    c.value = 25
    assert str(c) == '25'

    c.value = 24
    assert str(c) == '24'

    c.value = '22'
    assert str(c) == '22'


def test_bool_of_value():
    c = ConfigItem('a')

    # not_set evaluates to False
    assert not c.value

    c.value = 'b'
    assert c.value

    c.value = ''
    assert not c.value

    d = ConfigItem('a', default='b')
    assert d.value

    d.value = ''
    assert not d.value


def test_repr_makes_clear_the_path_and_value():
    c = ConfigItem('a', 'b', 'c', default='hello')
    assert repr(c) == '<ConfigItem a/b/c \'hello\'>'

    c.value = 'bye!'
    assert repr(c) == '<ConfigItem a/b/c \'bye!\'>'


def test_str_and_repr_of_not_set_value_should_not_fail():
    c = ConfigItem('a')
    assert str(c) == '<ConfigItem DEFAULT/a <NotSet>>'
    assert repr(c) == '<ConfigItem DEFAULT/a <NotSet>>'


def test_bool_str_is_a_str():
    c = ConfigItem('a.b', type=bool)
    assert isinstance(str(c), six.string_types)

    c.value = True
    assert isinstance(str(c), six.string_types)


def test_bool_config_preserves_raw_str_value_used_to_set_it():
    c = ConfigItem('a.b', type=bool, default=False)
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


def test_repr():
    assert repr(ConfigItem('this.is', 'me', default='yes')) == '<ConfigItem this.is/me \'yes\'>'
    assert repr(ConfigItem('this.is', 'me')) == '<ConfigItem this.is/me <NotSet>>'


def test_can_set_str_value_to_none():
    c = ConfigItem('a', 'b', default='haha')
    assert c.value == 'haha'

    c.value = None
    assert c.value is None


def test_setting_value_to_not_set_resets_it():
    c = ConfigItem('a', 'b', default='default', value='custom')
    assert c.value == 'custom'

    c.value = not_set
    assert c.value == 'default'


def test_can_set_int_value_to_none():
    c = ConfigItem('a', 'b', type=int, default=0, value=23)
    assert c.value == 23

    c.value = None
    assert c.value is None


def test_equality():
    c = ConfigItem('a', 'b', type=str, value=None)
    cc = ConfigItem('a', 'b', type=str, value=None)
    assert c == cc

    d = ConfigItem('a', 'b', type=int, value=None)
    assert c != d


def test_item_is_equal_to_itself():
    c = ConfigItem('a', 'b')
    assert c == c

    d = ConfigItem('a', 'b', value='d')
    assert d == d

    e = ConfigItem('a', 'b', default='e')
    assert e == e

    f = ConfigItem('a', 'b', default='f', value='g')
    assert f == f


def test_items_are_equal_if_path_and_type_and_effective_value_match():
    x1 = ConfigItem('a', 'b')
    x2 = ConfigItem('a', 'b')
    x3 = ConfigItem('a', 'bb')
    assert x1 == x2
    assert x1 != x3

    y1 = ConfigItem('a', 'b', default='yyy')
    y2 = ConfigItem('a', 'b', value='yyy')
    y3 = ConfigItem('a', 'b', default='yyy', value='YYY')
    y4 = ConfigItem('a', 'bb', value='yyy')
    y5 = ConfigItem('a', 'b', default='YYY', value='yyy')
    assert y1 == y2
    assert y1 != y3
    assert y1 != y4
    assert y1 == y5


def test_is_default():
    c = ConfigItem('a', 'b')
    d = ConfigItem('a', 'b', default=None)
    e = ConfigItem('a', 'b', value=None)

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


def test_strpath_of_config_item():
    c = ConfigItem('a', 'b.com', 'c.d.e')
    d = ConfigItem('d')

    assert c.strpath == 'a/b.com/c.d.e'
    assert d.strpath == '{}/d'.format(d.DEFAULT_SECTION)
