import six

from configmanager.utils import not_set


class ConfigParserMixin(object):
    def read(self, *args, **kwargs):
        as_defaults = kwargs.pop('as_defaults', False)

        used_filenames = []
        cp = self.cm__config_parser_factory()

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
        cp = self.cm__config_parser_factory()
        cp.read_file(fileobj)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def read_string(self, string, source=not_set, as_defaults=False):
        cp = self.cm__config_parser_factory()
        if source is not not_set:
            args = (string, source)
        else:
            args = (string,)
        cp.read_string(*args)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def read_dict(self, dictionary, source=not_set, as_defaults=False):
        cp = self.cm__config_parser_factory()
        if source is not not_set:
            args = (dictionary, source)
        else:
            args = (dictionary,)
        cp.read_dict(*args)
        self.load_from_config_parser(cp, as_defaults=as_defaults)

    def write(self, fileobj_or_path):
        """
        Write configuration to a file object or a path.

        This differs from ``ConfigParser.write`` in that it accepts a path too.
        """
        cp = self.cm__config_parser_factory()
        self.load_into_config_parser(cp)

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
                    if section not in self:
                        self[section] = self.__class__()
                    if option not in self[section]:
                        self[section][option] = self.cm__item_cls(option, default=value)
                    else:
                        self[section][option].default = value
                else:
                    if section not in self:
                        continue
                    if option not in self[section]:
                        continue
                    self[section][option].value = value

    def load_into_config_parser(self, cp):
        for item_path, item in self.iter_items():
            if len(item_path) > 2:
                raise RuntimeError(
                    '{cls} with more than 2 path segments cannot be loaded into ConfigParser'.format(
                        cls=item.__class__.__name__,
                ))
            if item.is_default:
                continue

            if len(item_path) == 2:
                section, option = item_path
            else:
                section = 'DEFAULT'
                option = item_path[0]

            if not cp.has_section(section):
                cp.add_section(section)
            cp.set(section, option, str(item))
