import pytest

from configmanager import Config, Item


@pytest.fixture
def c0():
    return Config()


@pytest.fixture
def c1():
    return Config({
        'greeting': 'Hello!',
    })


@pytest.fixture
def c2():
    return Config({
        'uploads': Config()
    })


@pytest.fixture
def c3():
    return Config({
        'uploads': Config([
            ('enabled', True),
            ('threads', 5),
        ])
    })


@pytest.fixture
def c4():
    return Config([
        ('greeting', 'Hello!'),
        ('uploads', Config([
            ('enabled', True),
            ('db', Config([
                ('host', 'localhost'),
                ('user', 'root')
            ])),
        ])),
        ('downloads', Config([
            ('enabled', True),
            ('threads', 5),
        ])),
    ])


@pytest.fixture
def c5():
    return Config([
        'greeting',
        'tmp_dir',
    ])


@pytest.fixture
def cx():
    return Config([
        ('with_', Item(name='with')),
        ('for', Config([
            ('continue_', Item(name='continue')),
        ])),
    ])


def test_len_config_returns_number_of_children(c0, c1, c2, c3, c4, c5):
    assert len(c0) == 0
    assert len(c1) == 1
    assert len(c2) == 1
    assert len(c3) == 1

    assert len(c4) == 3
    assert len(c4.downloads) == 2
    assert len(c4.uploads) == 2
    assert len(c4.uploads.db) == 2

    assert len(c5) == 2


def test_iter_item_names(c0, c1, c2, c3, c4, c5):
    assert list(c0.iter_item_names()) == []
    assert list(c1.iter_item_names()) == ['greeting']
    assert list(c2.iter_item_names()) == []
    assert list(c3.iter_item_names()) == []

    assert list(c4.iter_item_names()) == ['greeting']
    assert list(c4.uploads.iter_item_names()) == ['enabled']

    assert list(c5.iter_item_names()) == ['greeting', 'tmp_dir']


def test_iter_section_names(c0, c1, c2, c3, c4, c5):
    assert list(c0.iter_section_names()) == []
    assert list(c1.iter_section_names()) == []
    assert list(c2.iter_section_names()) == ['uploads']
    assert list(c3.iter_section_names()) == ['uploads']
    assert list(c4.iter_section_names()) == ['uploads', 'downloads']
    assert list(c5.iter_section_names()) == []


def test_iter_all(c0, c1, c2, c3, c4, c5, cx):
    assert list(c0.iter_all()) == []
    assert list(c0.iter_all(recursive=True)) == []

    all1 = list(c1.iter_all())
    assert len(all1) == 1
    assert all1[0][0] == ('greeting',)
    assert all1[0][1] == c1.greeting

    all2 = list(c2.iter_all())
    assert len(all2) == 1
    assert all2[0][0] == ('uploads',)
    assert all2[0][1] == c2.uploads

    all3 = list(c3.iter_all())
    assert len(all3) == 1
    assert all3[0][0] == ('uploads',)
    assert all3[0][1] == c3.uploads

    rall3 = list(c3.iter_all(recursive=True))
    assert len(rall3) == 3
    assert rall3[1][0] == ('uploads', 'enabled')
    assert rall3[1][1] == c3.uploads.enabled
    assert rall3[2][0] == ('uploads', 'threads')
    assert rall3[2][1] == c3.uploads.threads

    all4 = list(c4.iter_all())
    assert len(all4) == 3

    rall4 = list(c4.iter_all(recursive=True))
    assert len(rall4) == 9
    assert rall4[3][0] == ('uploads', 'db')
    assert rall4[3][1] == c4.uploads.db
    assert rall4[-1][0] == ('downloads', 'threads')
    assert rall4[-1][1] == c4.downloads.threads

    all5 = list(c5.iter_all())
    rall5 = list(c5.iter_all(recursive=True))
    assert all5 == rall5
    assert len(all5) == 2
    assert all5[0][0] == ('greeting',)
    assert all5[0][1] == c5.greeting
    assert all5[1][0] == ('tmp_dir',)
    assert all5[1][1] == c5.tmp_dir

    assert len(list(cx.iter_all())) == 2
    assert len(list(cx.iter_all(recursive=True))) == 3
    assert set(dict(cx.iter_all(recursive=True)).keys()) == {('with',), ('for',), ('for', 'continue')}


@pytest.mark.parametrize('recursive', [False, True])
def test_iter_paths(c0, c1, c2, c3, c4, c5, cx, recursive):
    assert list(cx.iter_paths(recursive=True)) == [('with',), ('for',), ('for', 'continue')]

    for c in [c0, c1, c2, c3, c4, c5, cx]:
        assert len(list(c.iter_all(recursive=recursive))) == len(list(c.iter_paths(recursive=recursive)))
