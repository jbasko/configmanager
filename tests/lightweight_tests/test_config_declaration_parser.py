import types

import pytest

from configmanager.lightweight.items import LwItem
from configmanager.lightweight.parsers import parse_config_declaration


@pytest.fixture
def app_config_cls_example():
    class DeepConfig:
        question = 'Why would you want a config this deep?'

    class UploadsConfig:
        enabled = True
        threads = 1
        type_ = LwItem(name='type', default=None)

    class DownloadsConfig:
        content_type = 'text/plain'
        deep = DeepConfig
        threads = LwItem(type=int)

    class AppConfig:
        uploads = UploadsConfig
        downloads = DownloadsConfig
        greeting = 'Hello, world!'

    return AppConfig


@pytest.fixture
def app_config_example_dict():
    return {
        'uploads': {
            'enabled': True,
            'threads': 1,
            'type_': LwItem(name='type', default=None),
        },
        'downloads': {
            'content_type': 'text/plain',
            'deep': {
                'question': 'Why would you want a config this deep?',
            },
            'threads': LwItem(type=int),
        },
        'greeting': 'Hello, world!',
    }


@pytest.fixture
def app_config_module_example():
    uploads = types.ModuleType('uploads')
    uploads.enabled = True
    uploads.threads = 1
    uploads.type_ = LwItem(name='type', default=None)

    downloads = types.ModuleType('downloads')
    downloads.content_type = 'text/plain'

    deep = types.ModuleType('deep')
    deep.question = 'Why would you want a config this deep?'
    downloads.deep = deep
    downloads.threads = LwItem(type=int)

    app_config = types.ModuleType('app_config')
    app_config.uploads = uploads
    app_config.downloads = downloads
    app_config.greeting = 'Hello, world!'

    return app_config


@pytest.fixture
def app_config_mixed_example():
    class DeepConfig:
        question = 'Why would you want a config this deep?'

    uploads_module = types.ModuleType('uploads')
    uploads_module.enabled = True
    uploads_module.threads = 1
    uploads_module.type_ = LwItem(name='type', default=None)

    downloads_dict = {
        'content_type': 'text/plain',
        'deep': DeepConfig,
        'threads': LwItem(type=int),
    }

    class AppConfig:
        uploads = uploads_module
        downloads = downloads_dict
        greeting = 'Hello, world!'

    return AppConfig


def test_class_based_config_declaration(app_config_cls_example):
    tree = parse_config_declaration(app_config_cls_example)

    assert tree['uploads']
    assert tree['uploads']['enabled'].name == 'enabled'
    assert tree['uploads']['type'].name == 'type'
    assert tree['uploads']['type'].value is None

    assert tree['downloads']
    assert tree['downloads']['deep']
    assert tree['downloads']['deep']['question']
    assert tree['downloads']['deep']['question'].value
    assert tree['downloads']['threads'].name == 'threads'

    assert tree['greeting'].name == 'greeting'

    assert 'deep' not in tree
    assert 'question' not in tree
    assert 'enabled' not in tree


def test_dict_based_config_declaration(app_config_example_dict, app_config_cls_example):
    dict_tree = parse_config_declaration(app_config_example_dict, tree_cls=dict)
    cls_tree = parse_config_declaration(app_config_cls_example, tree_cls=dict)
    assert dict_tree == cls_tree


def test_module_based_config_declaration(app_config_module_example, app_config_cls_example):
    module_tree = parse_config_declaration(app_config_module_example, tree_cls=dict)
    cls_tree = parse_config_declaration(app_config_cls_example, tree_cls=dict)
    assert module_tree == cls_tree


def test_mixed_config_declaration(app_config_mixed_example, app_config_cls_example):
    mixed_tree = parse_config_declaration(app_config_mixed_example, tree_cls=dict)
    cls_tree = parse_config_declaration(app_config_cls_example, tree_cls=dict)
    assert mixed_tree == cls_tree
