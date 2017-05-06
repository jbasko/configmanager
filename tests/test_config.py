import pytest

from configmanager import Config


@pytest.mark.parametrize('args', [
    ('section1', 'option1'),
    ('section1.option1',),
])
def test_initialisation_of_section_and_option(args):
    c = Config(*args)
    assert c.section == 'section1'
    assert c.option == 'option1'


def test_initialisation_with_default_section():
    c = Config('option1')
    assert c.section == 'DEFAULT'
    assert c.option == 'option1'


@pytest.mark.parametrize('args', [
    (True, True),
    ('section', True),
    (['section'], ['option']),
    (True, 'section'),
])
def test_section_and_option_must_be_strings(args):
    with pytest.raises(TypeError):
        Config(*args)


def test_value_with_no_default_value():
    c = Config('a', 'b')

    with pytest.raises(RuntimeError):
        assert c == ''

    assert not c.has_value
    assert not c.has_default

    with pytest.raises(RuntimeError):
        assert not c.value

    c.value = 'c'
    assert c.value == 'c'
    assert c == 'c'

    assert c.has_value

    c.value = 'd'
    assert c.value == 'd'
    assert c == 'd'
    assert c == c.value

    assert not c.has_default


def test_value_with_default_value():
    c = Config('a', 'b', default='c')

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

    d = Config('a', 'b', default='c', value='d')
    assert d.value == 'd'

    d.value = 'e'
    assert d.value == 'e'

    d.reset()
    assert d.value == 'c'


def test_value_gets_stringified():
    c = Config('a', value='23')
    assert c == '23'
    assert c != 23

    c.value = 24
    assert c == '24'
    assert c != 24


def test_int_value():
    c = Config('a', type=int, default=25)
    assert c == 25

    c.value = '23'
    assert c == 23
    assert c != '23'

    c.reset()
    assert c == 25


def test_bool_of_value():
    c = Config('a')

    with pytest.raises(RuntimeError):
        # Cannot evaluate if there is no value and no default value
        assert not c

    c.value = 'b'
    assert c

    c.value = ''
    assert not c

    d = Config('a', default='b')
    assert d

    d.value = ''
    assert not d


def test_str_and_repr_of_not_set_value():
    c = Config('a')

    with pytest.raises(RuntimeError):
        assert not str(c)

    assert repr(c) == '<Config DEFAULT.a <NotSet>>'


def test_creates_config_from_dot_notation():
    c = Config('a.b')
    assert c.section == 'a'
    assert c.option == 'b'
