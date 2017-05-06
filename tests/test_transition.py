from configmanager import ConfigItem, TransitionConfigManager


def test_transition_interface():
    m = TransitionConfigManager(
        ConfigItem('a', 'x'),
        ConfigItem('a', 'y'),
        ConfigItem('a', 'z'),
        ConfigItem('b', 'xx'),
        ConfigItem('b', 'yy'),
    )

    assert m.sections() == ['a', 'b']

    # add_section is a no-op
    m.add_section('c')
    assert m.sections() == ['a', 'b']

    assert m.has_section('a')
    assert not m.has_section('c')
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
    assert len(list_of_sections) == 2
    assert list_of_sections[0][0] == 'a'
    assert list_of_sections[1][0] == 'b'
