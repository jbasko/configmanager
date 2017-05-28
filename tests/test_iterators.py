import pytest

from configmanager import Config


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
