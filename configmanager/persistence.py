import configparser

import six


class ConfigReaderWriter(object):
    def __init__(self, **options):
        pass

    def dump_config_to_file(self, config, file_obj, with_defaults=False, **kwargs):
        raise NotImplementedError()

    def dump_config_to_string(self, config, with_defaults=False, **kwargs):
        raise NotImplementedError()

    def load_config_from_string(self, config, string, as_defaults=False, **kwargs):
        raise NotImplementedError()

    def load_config_from_file(self, config, file_obj, as_defaults=False, **kwargs):
        raise NotImplementedError()


class ConfigPersistenceAdapter(object):
    def __init__(self, config, reader_writer):
        self._config = config
        self._rw = reader_writer

    def load(self, source, as_defaults=False):
        if isinstance(source, six.string_types):
            with open(source) as f:
                self._rw.load_config_from_file(self._config, f, as_defaults=as_defaults)

        elif isinstance(source, (list, tuple)):
            for s in source:
                with open(s) as f:
                    self._rw.load_config_from_file(self._config, f, as_defaults=as_defaults)

        else:
            self._rw.load_config_from_file(self._config, source, as_defaults=as_defaults)

    def loads(self, config_str, as_defaults=False):
        self._rw.load_config_from_string(self._config, config_str, as_defaults=as_defaults)

    def dump(self, destination, with_defaults=False):
        if isinstance(destination, six.string_types):
            with open(destination, 'w') as f:
                self._rw.dump_config_to_file(self._config, f, with_defaults=with_defaults)
        else:
            self._rw.dump_config_to_file(self._config, destination, with_defaults=with_defaults)

    def dumps(self, with_defaults=False):
        return self._rw.dump_config_to_string(self._config, with_defaults=with_defaults)


class JsonReaderWriter(ConfigReaderWriter):
    def __init__(self, **options):
        super(JsonReaderWriter, self).__init__(**options)

        import json
        self.json = json

    def dump_config_to_file(self, config, file_obj, with_defaults=False, **kwargs):
        self.json.dump(config.to_dict(with_defaults=with_defaults), file_obj, **kwargs)

    def dump_config_to_string(self, config, with_defaults=False, **kwargs):
        return self.json.dumps(config.to_dict(with_defaults=with_defaults), **kwargs)

    def load_config_from_file(self, config, file_obj, as_defaults=False, **kwargs):
        config.read_dict(self.json.load(file_obj, **kwargs), as_defaults=as_defaults)

    def load_config_from_string(self, config, string, as_defaults=False, **kwargs):
        config.read_dict(self.json.loads(string, **kwargs), as_defaults=as_defaults)


class YamlReaderWriter(ConfigReaderWriter):
    def __init__(self, **options):
        super(YamlReaderWriter, self).__init__(**options)

        import yaml
        self.yaml = yaml

    def dump_config_to_file(self, config, file_obj, with_defaults=False, **kwargs):
        self.yaml.dump(config.to_dict(with_defaults=with_defaults), file_obj, **kwargs)

    def dump_config_to_string(self, config, with_defaults=False, **kwargs):
        return self.yaml.dump(config.to_dict(with_defaults=with_defaults), **kwargs)

    def load_config_from_file(self, config, file_obj, as_defaults=False, **kwargs):
        config.read_dict(self.yaml.load(file_obj, **kwargs), as_defaults=as_defaults)

    def load_config_from_string(self, config, string, as_defaults=False, **kwargs):
        config.read_dict(self.yaml.load(string, **kwargs), as_defaults=as_defaults)


class ConfigParserReaderWriter(ConfigReaderWriter):
    def __init__(self, config_parser_factory=None, **options):
        super(ConfigParserReaderWriter, self).__init__(**options)
        self.config_parser_factory = config_parser_factory or configparser.ConfigParser

    def dump_config_to_file(self, config, file_obj, with_defaults=False, **kwargs):
        cp = self.config_parser_factory()
        self._load_config_into_config_parser(config, cp, with_defaults=with_defaults)
        cp.write(file_obj)

    def dump_config_to_string(self, config, with_defaults=False, **kwargs):
        from io import StringIO
        f = StringIO()
        self.dump_config_to_file(config, f, with_defaults=with_defaults)
        return f.getvalue()

    def load_config_from_file(self, config, file_obj, as_defaults=False, **kwargs):
        cp = self.config_parser_factory()
        cp.read_file(file_obj)
        self._load_config_from_config_parser(config, cp, as_defaults=as_defaults)

    def load_config_from_string(self, config, string, as_defaults=False, **kwargs):
        cp = self.config_parser_factory()
        cp.read_string(string)
        self._load_config_from_config_parser(config, cp, as_defaults=as_defaults)

    def _load_config_from_config_parser(self, config, cp, as_defaults=False):
        for section in cp.sections():
            for option in cp.options(section):
                value = cp.get(section, option)
                if as_defaults:
                    if section not in config:
                        config.cm__add_section(section, config.cm__create_section())
                    if option not in config[section]:
                        config[section].cm__add_item(option, config.cm__create_item(option, default=value))
                    else:
                        config[section][option].default = value
                else:
                    if section not in config:
                        continue
                    if option not in config[section]:
                        continue
                    config[section][option].value = value

    def _load_config_into_config_parser(self, config, cp, with_defaults=False):
        for item_path, item in config.iter_items():
            if len(item_path) > 2:
                raise RuntimeError(
                    '{cls} with more than 2 path segments cannot be loaded into ConfigParser'.format(
                        cls=item.__class__.__name__,
                ))
            if not with_defaults and item.is_default:
                continue

            if len(item_path) == 2:
                section, option = item_path
            else:
                section = 'DEFAULT'
                option = item_path[0]

            if not cp.has_section(section):
                cp.add_section(section)
            cp.set(section, option, str(item))
