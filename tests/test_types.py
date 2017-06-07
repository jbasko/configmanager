import collections

from configmanager import Item, Types
from configmanager.item_types import _ItemType


def test_int_type():
    number = Item(type=Types.int, default='55')
    assert number.default == 55
    assert number.value == 55
    assert number.str_value == '55'

    number.value = -55
    assert number.value == -55

    number.value = '-555'
    assert number.value == -555

    assert Types.guess(5) == Types.int
    assert Types.guess(-5) == Types.int
    assert Types.guess(0) == Types.int


def test_type_equality():
    assert Types.int == Types.int
    assert Types.int != _ItemType()
    assert _ItemType() != Types.int
    assert Types.int != Types.float
    assert Types.float != Types.int


def test_bool_type():
    flag = Item(type=Types.bool, default='yes')
    assert flag.default is True
    assert flag.value is True

    flag.value = 'no'
    assert flag.value is False
    assert flag.default is True

    flag.value = True
    assert flag.value is True

    flag.value = '1'
    assert flag.value is True

    flag.value = '0'
    assert flag.value is False

    assert Types.guess(True) == Types.bool
    assert Types.guess(False) == Types.bool
    assert Types.guess(None) == Types.not_set

    assert Types.guess('yes') == Types.str
    assert Types.guess('no') == Types.str
    assert Types.guess('True') == Types.str
    assert Types.guess('False') == Types.str


def test_float_type():
    rate = Item(type=Types.float, default='0.23')
    assert rate.default == 0.23
    assert rate.value == 0.23

    rate.value = '0.01'
    assert rate.value == 0.01

    rate.value = '-0.23'
    assert rate.value == -0.23

    assert Types.guess(0.23) == Types.float
    assert Types.guess(-0.23) == Types.float

    assert Types.guess('-0.23') is not Types.float
    assert Types.guess('0.23') is not Types.float


def test_dict_type():
    db = Item(type=Types.dict, default={
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'db': 'test',
    })

    assert db.default == {'user': 'root', 'password': 'root', 'host': 'localhost', 'db': 'test'}
    assert db.value == {'user': 'root', 'password': 'root', 'host': 'localhost', 'db': 'test'}

    # This has no effect because it is working on a copy of default value
    db.value['password'] = '!!!!!'

    assert db.default == {'user': 'root', 'password': 'root', 'host': 'localhost', 'db': 'test'}
    assert db.value == {'user': 'root', 'password': 'root', 'host': 'localhost', 'db': 'test'}

    # But once we have a real value, then modifications are for real
    db.value = {'user': 'admin', 'password': 'admin', 'host': 'localhost', 'db': 'production'}
    db.value['password'] = '!!!!!'

    assert db.default == {'user': 'root', 'password': 'root', 'host': 'localhost', 'db': 'test'}
    assert db.value == {'user': 'admin', 'password': '!!!!!', 'host': 'localhost', 'db': 'production'}

    assert Types.guess({}) == Types.dict
    assert Types.guess(collections.OrderedDict()) == Types.dict


def test_list_type():
    tags = Item(type=Types.list, default=['untitled', 'new'])

    assert tags.default == ['untitled', 'new']
    assert tags.value == ['untitled', 'new']

    # This should have no effect
    tags.value.append('!!!!')

    assert tags.default == ['untitled', 'new']
    assert tags.value == ['untitled', 'new']

    tags.value = ['real', 'tags', 'now']
    tags.value.append('!!!!')

    assert tags.default == ['untitled', 'new']
    assert tags.value == ['real', 'tags', 'now', '!!!!']

    assert Types.guess([]) == Types.list
    assert Types.guess(()) == Types.list
    assert Types.guess([1, 2, 3]) == Types.list
    assert Types.guess(['1', '2', '3']) == Types.list
