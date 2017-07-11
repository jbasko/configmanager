import pytest

from configmanager import Config, Item, RequiredValueMissing


def test_validate_raises_required_value_missing():
    config = Config({
        'a': Item(required=True),
        'b': Item(),
    })

    with pytest.raises(RequiredValueMissing):
        config.validate()

    config.a.set('value')
    config.validate()

    config.a.reset()
    with pytest.raises(RequiredValueMissing):
        config.validate()
