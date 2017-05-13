import pytest

from configmanager.utils import resolve_config_path, resolve_config_prefix


def test_path_is_a_tuple():
    p = resolve_config_path('a', 'b')
    assert isinstance(p, tuple)
    assert p == ('a', 'b')

    assert resolve_config_path('a', 'b', 'c') == ('a', 'b', 'c')
    assert resolve_config_path('A.B', 'cd.ef.gh', 'iJ') == ('A.B', 'cd.ef.gh', 'iJ')


def test_empty_path_raises_value_error():
    with pytest.raises(ValueError):
        resolve_config_path()


@pytest.mark.parametrize('path', [
    (['section', 'option'], 'suboption'),
    (('section',), ('subsection', 'option',)),
    (('section',), ('option',)),
])
def test_lists_and_tuples_as_path_segment_raise_type_error(path):
    with pytest.raises(TypeError):
        resolve_config_path(*path)


@pytest.mark.parametrize('path', [
    ('valid1', {}, 'valid2'),
    (True, 'valid'),
    (None,),
    ('valid1', None,),
    ('valid1', 'valid2', 'valid3', False),
])
def test_non_string_segments_raise_type_error(path):
    with pytest.raises(TypeError):
        resolve_config_path(*path)


@pytest.mark.parametrize('path', [
    ('',),
    ('', 'valid'),
    ('valid1', '', 'valid2'),
    ('valid1', 'valid2', ''),
    ('valid1', 'valid2', 'valid3', ''),
])
def test_empty_segments_raise_value_error(path):
    with pytest.raises(ValueError):
        resolve_config_path(*path)


def test_config_prefix_can_be_empty():
    assert resolve_config_prefix() == tuple()


def test_config_prefix_is_really_just_a_config_path_that_can_be_empty():
    assert resolve_config_prefix('a', 'b', 'c') == ('a', 'b', 'c')
