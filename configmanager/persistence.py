import collections
from io import open
import os.path

from builtins import str
import configparser
import six


class ConfigReaderWriter(object):
    def __init__(self, **options):
        pass

    def store_exists(self, store):
        return os.path.exists(os.path.expanduser(store))

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
        """
        Load configuration values from the specified source.

        Args:
            source:
            as_defaults (bool): if ``True``, contents of ``source`` will be treated as schema of configuration items.

        """
        if isinstance(source, six.string_types):
            source = os.path.expanduser(source)
            with open(source, encoding='utf-8') as f:
                self._rw.load_config_from_file(self._config, f, as_defaults=as_defaults)

        elif isinstance(source, (list, tuple)):
            for s in source:
                with open(s, encoding='utf-8') as f:
                    self._rw.load_config_from_file(self._config, f, as_defaults=as_defaults)

        else:
            self._rw.load_config_from_file(self._config, source, as_defaults=as_defaults)

    def loads(self, config_str, as_defaults=False):
        """
        Load configuration values from the specified source string.

        Args:
            config_str:
            as_defaults (bool): if ``True``, contents of ``source`` will be treated as schema of configuration items.

        """
        self._rw.load_config_from_string(self._config, config_str, as_defaults=as_defaults)

    def dump(self, destination, with_defaults=False):
        """
        Write configuration values to the specified destination.

        Args:
            destination:
            with_defaults (bool): if ``True``, values of items with no custom values will be included in the output
                if they have a default value set.
        """
        if isinstance(destination, six.string_types):
            with open(destination, 'w', encoding='utf-8') as f:
                self._rw.dump_config_to_file(self._config, f, with_defaults=with_defaults)
        else:
            self._rw.dump_config_to_file(self._config, destination, with_defaults=with_defaults)

    def dumps(self, with_defaults=False):
        """
        Generate a string representing all the configuration values.

        Args:
            with_defaults (bool): if ``True``, values of items with no custom values will be included in the output
                if they have a default value set.
        """
        return self._rw.dump_config_to_string(self._config, with_defaults=with_defaults)

    def store_exists(self, store):
        """
        Returns ``True`` if configuration can be loaded from the store.
        """
        return self._rw.store_exists(store)


class JsonReaderWriter(ConfigReaderWriter):
    def __init__(self, **options):
        super(JsonReaderWriter, self).__init__(**options)
        import json
        self.json = json

    def dump_config_to_file(self, config, file_obj, with_defaults=False, **kwargs):
        # See comment in JsonReaderWriter.dump_config_to_string
        file_obj.write(self.dump_config_to_string(config, with_defaults=with_defaults), **kwargs)

    def dump_config_to_string(self, config, with_defaults=False, **kwargs):
        # There is some inconsistent behaviour in Python 2's json.dump as described here:
        # http://stackoverflow.com/a/36008538/38611
        # and io.open which we use for file opening is very strict and fails if
        # the string we are trying to write is not unicode in Python 2
        # because we open files with encoding=utf-8.
        result = self.json.dumps(
            config.dump_values(with_defaults=with_defaults, dict_cls=collections.OrderedDict),
            ensure_ascii=False,
            indent=2,
            **kwargs
        )
        if not isinstance(result, str):
            return str(result)
        else:
            return result

    def load_config_from_file(self, config, file_obj, as_defaults=False, **kwargs):
        config.load_values(
            self.json.load(file_obj, object_pairs_hook=collections.OrderedDict, **kwargs),
            as_defaults=as_defaults,
        )

    def load_config_from_string(self, config, string, as_defaults=False, **kwargs):
        config.load_values(
            self.json.loads(string, object_pairs_hook=collections.OrderedDict, **kwargs),
            as_defaults=as_defaults,
        )


class YamlReaderWriter(ConfigReaderWriter):
    def __init__(self, **options):
        super(YamlReaderWriter, self).__init__(**options)

        try:
            import yaml
            import yaml.resolver
        except ImportError:
            raise RuntimeError('To use YAML, please install PyYAML first')

        #
        # The code to preserve order of items is taken from here:
        # https://stackoverflow.com/a/21048064/38611
        #

        _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

        def dict_representer(dumper, data):
            return dumper.represent_dict(data.items())

        def dict_constructor(loader, node):
            return collections.OrderedDict(loader.construct_pairs(node))

        yaml.add_representer(collections.OrderedDict, dict_representer)
        yaml.add_constructor(_mapping_tag, dict_constructor)

        self.yaml = yaml

        self.default_dump_options = {
            'indent': 2,
            'default_flow_style': False,
        }

    def dump_config_to_file(self, config, file_obj, with_defaults=False, **kwargs):
        for k, v in self.default_dump_options.items():
            kwargs.setdefault(k, v)
        self.yaml.dump(
            config.dump_values(with_defaults=with_defaults, dict_cls=collections.OrderedDict),
            file_obj,
            **kwargs
        )

    def dump_config_to_string(self, config, with_defaults=False, **kwargs):
        for k, v in self.default_dump_options.items():
            kwargs.setdefault(k, v)
        return self.yaml.dump(
            config.dump_values(with_defaults=with_defaults, dict_cls=collections.OrderedDict),
            **kwargs
        )

    def load_config_from_file(self, config, file_obj, as_defaults=False, **kwargs):
        config.load_values(self.yaml.safe_load(file_obj, **kwargs), as_defaults=as_defaults)

    def load_config_from_string(self, config, string, as_defaults=False, **kwargs):
        config.load_values(self.yaml.safe_load(string, **kwargs), as_defaults=as_defaults)


class ConfigParserReaderWriter(ConfigReaderWriter):
    no_section = 'NO_SECTION'

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

        # TODO Clean up the repetition here!

        # TODO Shouldn't really use create_item and create_section methods here,
        # TODO should use load_values(..., as_defaults=True) instead!

        for option, value in cp.defaults().items():
            if as_defaults:
                if option not in config:
                    config.add_item(option, config.create_item(option, default=value))
                else:
                    config[option].default = value
            else:
                if option not in config:
                    continue
                config[option].value = value

        for section in cp.sections():
            if section == self.no_section:
                for option in cp.options(section):
                    value = cp.get(section, option)
                    if as_defaults:
                        if option not in config:
                            config.add_item(option, config.create_item(option, default=value))
                        else:
                            config[option].default = value
                    else:
                        if option not in config:
                            continue
                        config[option].value = value
                continue

            for option in cp.options(section):
                value = cp.get(section, option)
                if as_defaults:
                    if section not in config:
                        config.add_section(section, config.create_section())
                    if option not in config[section]:
                        config[section].add_item(option, config.create_item(option, default=value))
                    else:
                        config[section][option].default = value
                else:
                    if section not in config:
                        continue
                    if option not in config[section]:
                        continue
                    config[section][option].value = value

    def _load_config_into_config_parser(self, config, cp, with_defaults=False):
        for item_path, item in config.iter_items(recursive=True):
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
                section = self.no_section
                option = item_path[0]

            if not cp.has_section(section) and section != cp.default_section:
                cp.add_section(section)
            cp.set(section, option, item.str_value)
