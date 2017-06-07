import configparser

import six

from .base import is_config_item, is_config_section
from .exceptions import NotFound
from .hooks import Hooks
from .items import Item
from .parsers import ConfigDeclarationParser
from .persistence import ConfigPersistenceAdapter, YamlReaderWriter, JsonReaderWriter, ConfigParserReaderWriter
from .sections import Section


class Config(Section):
    """
    Represents a section consisting of items (instances of :class:`.Item`) and other sections
    (instances of :class:`.Config`).
    
    .. attribute:: Config(config_declaration=None, **kwargs)
        
        Creates a section from a declaration.

        Args:
            ``config_declaration``: can be a dictionary, a list, a simple class, a module, another :class:`.Config`
            instance, and a combination of these.

        Keyword Args:

            ``config_parser_factory``:

        Examples::

            config = Config([
                ('greeting', 'Hello!'),
                ('uploads', Config({
                    'enabled': True,
                    'tmp_dir': '/tmp',
                })),
                ('db', {
                    'host': 'localhost',
                    'user': 'root',
                    'password': 'secret',
                    'name': 'test',
                }),
                ('api', Config([
                    'host',
                    'port',
                    'default_user',
                    ('enabled', Item(type=bool)),
                ])),
            ])
    
    .. attribute:: <config>[<name_or_path>]
    
        Access item by its name, section by its alias, or either by its path.

        Args:
            ``name`` (str): name of an item or alias of a section

        Args:
            ``path`` (tuple): path of an item or a section
        
        Returns:
            :class:`.Item` or :class:`.Config`

        Examples::

            >>> config['greeting']
            <Item greeting 'Hello!'>

            >>> config['uploads']
            <Config uploads at 4436269600>

            >>> config['uploads', 'enabled'].value
            True
    
    .. attribute:: <config>.<name>
    
        Access an item by its name or a section by its alias.

        For names and aliases that break Python grammar rules, use ``config[name]`` notation instead.
        
        Returns:
            :class:`.Item` or :class:`.Config`

    .. attribute:: <name_or_path> in <Config>

        Returns ``True`` if an item or section with the specified name or path is to be found in this section.

    .. attribute:: len(<Config>)

        Returns the number of items and sections in this section (does not include sections and items in
        sub-sections).

    .. attribute:: __iter__()

        Returns an iterator over all item names and section aliases in this section.

    """

    def __init__(self, config_declaration=None, **configmanager_settings):
        if 'configmanager_settings' in configmanager_settings:
            if len(configmanager_settings) > 1:
                raise ValueError('Dubious configmanager_settings specification: {}'.format(configmanager_settings))
            configmanager_settings = configmanager_settings['configmanager_settings']
        super(Config, self).__init__(configmanager_settings=configmanager_settings)
        self._cm__configparser_adapter = None
        self._cm__json_adapter = None
        self._cm__yaml_adapter = None
        self._cm__click_extension = None

        self.__dict__['hooks'] = Hooks(config=self)
        self._cm__process_config_declaration = ConfigDeclarationParser(section=self)

        if config_declaration:
            self._cm__process_config_declaration(config_declaration)

    def __repr__(self):
        return '<{cls} {alias} at {id}>'.format(cls=self.__class__.__name__, alias=self.alias, id=id(self))

    def _resolve_config_key(self, key):
        if isinstance(key, six.string_types):
            if key in self._cm__configs:
                return self._cm__configs[key]
            else:
                result = self.hooks.handle(Hooks.NOT_FOUND, name=key, section=self)
                if result is not None:
                    return result
                raise NotFound(key, section=self)

        if isinstance(key, (tuple, list)) and len(key) > 0:
            if len(key) == 1:
                return self._resolve_config_key(key[0])
            else:
                return self._resolve_config_key(key[0])[key[1:]]
        else:
            raise TypeError('Expected either a string or a tuple as key, got {!r}'.format(key))

    @property
    def configparser(self):
        """
        Adapter to dump/load INI format strings and files using standard library's
        ``ConfigParser`` (or the backported configparser module in Python 2).
        
        Returns:
            :class:`.ConfigPersistenceAdapter`
        """
        if self._cm__configparser_adapter is None:
            self._cm__configparser_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=ConfigParserReaderWriter(
                    config_parser_factory=self.configmanager_settings.configparser_factory,
                ),
            )
        return self._cm__configparser_adapter

    @property
    def json(self):
        """
        Adapter to dump/load JSON format strings and files.
        
        Returns:
            :class:`.ConfigPersistenceAdapter`
        """
        if self._cm__json_adapter is None:
            self._cm__json_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=JsonReaderWriter(),
            )
        return self._cm__json_adapter

    @property
    def yaml(self):
        """
        Adapter to dump/load YAML format strings and files.
        
        Returns:
            :class:`.ConfigPersistenceAdapter`
        """
        if self._cm__yaml_adapter is None:
            self._cm__yaml_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=YamlReaderWriter(),
            )
        return self._cm__yaml_adapter

    @property
    def click(self):
        if self._cm__click_extension is None:
            from .click_ext import ClickExtension
            self._cm__click_extension = ClickExtension(
                config=self
            )
        return self._cm__click_extension

    def add_item(self, alias, item):
        """
        Add a config item to this section.
        """
        super(Config, self).add_item(alias, item)

        # Since we are actually deep-copying the supplied item,
        # the actual item to pass to callbacks needs to be fetched from the section.
        item = self[alias]

        self.hooks.handle(Hooks.ITEM_ADDED_TO_SECTION, alias=alias, section=self, subject=item)

    def add_section(self, alias, section):
        """
        Add a sub-section to this section.
        """
        super(Config, self).add_section(alias, section)
        self.hooks.handle(Hooks.SECTION_ADDED_TO_SECTION, alias=alias, section=self, subject=section)
