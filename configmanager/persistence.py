import configparser
import json

import six

from .utils import not_set


class ConfigReaderWriter(object):
    def __init__(self, config):
        self.config = config

    def write(self, destination, with_defaults=False):
        raise NotImplementedError()

    def read(self, source, as_defaults=False):
        raise NotImplementedError()

    def write_string(self, with_defaults=False):
        raise NotImplementedError()

    def read_string(self, config_str, as_defaults=False):
        raise NotImplementedError()


class ConfigParserReaderWriter(ConfigReaderWriter):
    def __init__(self, config, config_parser_factory=None):
        super(ConfigParserReaderWriter, self).__init__(config)
        self.config_parser_factory = config_parser_factory or configparser.ConfigParser

    def read(self, source, as_defaults=False):
        cp = self.config_parser_factory()
        if isinstance(source, six.string_types):
            cp.read(source)
        elif isinstance(source, (list, tuple)):
            cp.read(source)
        else:
            cp.read_file(source)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def read_string(self, string, source=not_set, as_defaults=False):
        cp = self.config_parser_factory()
        if source is not not_set:
            args = (string, source)
        else:
            args = (string,)
        cp.read_string(*args)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def write(self, destination, with_defaults=False):
        """
        Write configuration to a file object or a path.

        This differs from ``ConfigParser.write`` in that it accepts a path too.
        """
        cp = self.config_parser_factory()
        self.load_into_config_parser(cp, with_defaults=with_defaults)

        if isinstance(destination, six.string_types):
            with open(destination, 'w') as f:
                cp.write(f)
        else:
            cp.write(destination)

    def write_string(self, with_defaults=False):
        from io import StringIO
        f = StringIO()
        self.write(f, with_defaults=with_defaults)
        return f.getvalue()

    def load_from_config_parser(self, cp, as_defaults=False):
        for section in cp.sections():
            for option in cp.options(section):
                value = cp.get(section, option)
                if as_defaults:
                    if section not in self.config:
                        self.config.cm__add_section(section, self.config.cm__create_section())
                    if option not in self.config[section]:
                        self.config[section].cm__add_item(option, self.config.cm__create_item(option, default=value))
                    else:
                        self.config[section][option].default = value
                else:
                    if section not in self.config:
                        continue
                    if option not in self.config[section]:
                        continue
                    self.config[section][option].value = value

    def load_into_config_parser(self, cp, with_defaults=False):
        for item_path, item in self.config.iter_items():
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


class JsonReaderWriter(ConfigReaderWriter):
    def read(self, source, as_defaults=False):
        if isinstance(source, six.string_types):
            with open(source) as f:
                self.config.read_dict(json.load(f), as_defaults=as_defaults)
        elif isinstance(source, (list, tuple)):
            for s in source:
                with open(s) as f:
                    self.config.read_dict(json.load(f), as_defaults=as_defaults)
        else:
            self.config.read_dict(json.load(source), as_defaults=as_defaults)

    def write(self, destination, with_defaults=False):
        if isinstance(destination, six.string_types):
            with open(destination, 'w') as f:
                json.dump(self.config.to_dict(with_defaults=with_defaults), f)
        else:
            json.dump(self.config.to_dict(with_defaults=with_defaults), destination)

    def read_string(self, config_str, as_defaults=False):
        self.config.read_dict(json.loads(config_str), as_defaults=as_defaults)

    def write_string(self, with_defaults=False):
        return json.dumps(self.config.to_dict(with_defaults=with_defaults))
