import configparser

import six

from .utils import not_set


class ConfigParserAdapter(object):
    def __init__(self, config, config_parser_factory=None):
        self.config = config
        self.config_parser_factory = config_parser_factory or configparser.ConfigParser

    def read(self, *args, **kwargs):
        as_defaults = kwargs.pop('as_defaults', False)

        used_filenames = []
        cp = self.config_parser_factory()

        def get_filenames():
            for arg in args:
                if isinstance(arg, six.string_types):
                    yield arg
                else:
                    for filename in arg:
                        yield filename

        # Do it one file after another so that we can tell which file contains invalid configuration
        for filename in get_filenames():
            result = cp.read(filename, **kwargs)
            if result:
                self.load_from_config_parser(cp, as_defaults=as_defaults)
                used_filenames.append(filename)

        return used_filenames

    def read_file(self, fileobj, as_defaults=False):
        cp = self.config_parser_factory()
        cp.read_file(fileobj)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def read_string(self, string, source=not_set, as_defaults=False):
        cp = self.config_parser_factory()
        if source is not not_set:
            args = (string, source)
        else:
            args = (string,)
        cp.read_string(*args)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def read_dict(self, dictionary, source=not_set, as_defaults=False):
        cp = self.config_parser_factory()
        if source is not not_set:
            args = (dictionary, source)
        else:
            args = (dictionary,)
        cp.read_dict(*args)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def write(self, fileobj_or_path, with_defaults=False):
        """
        Write configuration to a file object or a path.

        This differs from ``ConfigParser.write`` in that it accepts a path too.
        """
        cp = self.config_parser_factory()
        self.load_into_config_parser(cp, with_defaults=with_defaults)

        if isinstance(fileobj_or_path, six.string_types):
            with open(fileobj_or_path, 'w') as f:
                cp.write(f)
        else:
            cp.write(fileobj_or_path)

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
