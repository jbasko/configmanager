import pytest

from configmanager import Config, TransitionConfigManager
from configmanager.configparser_imports import DuplicateSectionError


def test_transition_interface():
    m = TransitionConfigManager(
        Config('a', 'x'),
        Config('a', 'y'),
        Config('a', 'z'),
        Config('b', 'xx'),
        Config('b', 'yy'),
    )

    assert m.sections() == ['a', 'b']

    m.add_section('c')
    with pytest.raises(DuplicateSectionError):
        m.add_section('c')

    assert m.has_section('a')
    assert m.has_section('c')
    assert not m.has_section('d')
    assert not m.has_section(m.default_section)

    assert m.options('a') == ['x', 'y', 'z']
    assert m.options('b') == ['xx', 'yy']

    assert m.has_option('a', 'x')
    assert not m.has_option('x', 'a')
    assert not m.has_option('b', 'x')

    assert m.get('a', 'x', vars={'x': None}) is None

    m.set('a', 'x', '23')
    assert m.a.x == '23'

    assert m.get('a', 'x') == '23'
    assert m.get('a', 'x', vars={'x': None}) is None

    assert m.get('a', 'x', fallback='ZZZ') == '23'
    assert m.get('a', 'zzz', fallback='ZZZ') == 'ZZZ'

    list_of_sections = m.items()
    assert len(list_of_sections) == 3
    assert list_of_sections[0][0] == 'a'
    assert len(list_of_sections[0][1]) == 3
    assert list_of_sections[1][0] == 'b'
    assert len(list_of_sections[1][1]) == 2
    assert list_of_sections[2][0] == 'c'

