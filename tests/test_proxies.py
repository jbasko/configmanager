from configmanager.sections import PathProxy


def test_path_proxy_class(simple_config):
    enabled = PathProxy(simple_config, ('uploads', 'enabled'))
    assert enabled.value is False

    nonexistent_path = ('uploads', 'something', 'nonexistent')
    assert nonexistent_path not in simple_config

    nonexistent = PathProxy(simple_config, nonexistent_path)

    simple_config.uploads.add_schema({'something': {'nonexistent': 42}})
    assert nonexistent.value == 42

    assert nonexistent_path in simple_config

    different = PathProxy(simple_config, 'uploads.different')

    simple_config.uploads.add_schema({'different': 'VERY'})
    assert different.value == 'VERY'

    assert 'uploads.different' in simple_config


def test_get_proxy_handles_both_sections_and_items(simple_config):
    downloads = simple_config.get_proxy('downloads')
    downloads_enabled = simple_config.get_proxy('downloads.enabled')

    assert 'downloads' not in simple_config
    assert ('downloads', 'enabled') not in simple_config

    simple_config.add_schema({
        'downloads': {
            'enabled': True,
            'tmp_dir': '/tmp',
        }
    })

    assert downloads.is_section
    assert downloads.enabled.value is True

    assert downloads_enabled.is_item
    assert downloads_enabled.value is True
