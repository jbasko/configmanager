from .config_declaration_parser import parse_config_declaration
from .meta import ConfigManagerSettings
from .persistence import ConfigPersistenceAdapter, YamlReaderWriter, JsonReaderWriter, ConfigParserReaderWriter
from .sections import Section


class Config(Section):
    """
    Represents a configuration tree.
    
    .. attribute:: Config(config_declaration=None, **kwargs)
        
        Creates a configuration tree from a declaration.

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

    is_config = True

    def __init__(self, config_declaration=None, **configmanager_settings):
        if 'configmanager_settings' in configmanager_settings:
            if len(configmanager_settings) > 1:
                raise ValueError('Dubious configmanager_settings specification: {}'.format(configmanager_settings))
            configmanager_settings = configmanager_settings['configmanager_settings']

        if not isinstance(configmanager_settings, ConfigManagerSettings):
            configmanager_settings = ConfigManagerSettings(**configmanager_settings)

        super(Config, self).__init__(configmanager_settings=configmanager_settings)

        self._manager = self

        self._configparser_adapter = None
        self._json_adapter = None
        self._yaml_adapter = None
        self._click_extension = None

        if config_declaration is not None:
            parse_config_declaration(config_declaration, root=self)

        self.load_user_app_config()

    def __repr__(self):
        return '<{cls} {alias} at {id}>'.format(cls=self.__class__.__name__, alias=self.alias, id=id(self))

    @property
    def configparser(self):
        """
        Adapter to dump/load INI format strings and files using standard library's
        ``ConfigParser`` (or the backported configparser module in Python 2).
        
        Returns:
            :class:`.ConfigPersistenceAdapter`
        """
        if self._configparser_adapter is None:
            self._configparser_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=ConfigParserReaderWriter(
                    config_parser_factory=self._settings.configparser_factory,
                ),
            )
        return self._configparser_adapter

    @property
    def json(self):
        """
        Adapter to dump/load JSON format strings and files.
        
        Returns:
            :class:`.ConfigPersistenceAdapter`
        """
        if self._json_adapter is None:
            self._json_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=JsonReaderWriter(),
            )
        return self._json_adapter

    @property
    def yaml(self):
        """
        Adapter to dump/load YAML format strings and files.
        
        Returns:
            :class:`.ConfigPersistenceAdapter`
        """
        if self._yaml_adapter is None:
            self._yaml_adapter = ConfigPersistenceAdapter(
                config=self,
                reader_writer=YamlReaderWriter(),
            )
        return self._yaml_adapter

    @property
    def click(self):
        if self._click_extension is None:
            from .click_ext import ClickExtension
            self._click_extension = ClickExtension(
                config=self
            )
        return self._click_extension

    def load_user_app_config(self):
        if not self._settings.app_name:
            return

        import os.path
        if os.path.exists(self._settings.user_app_config):
            self.json.load(self._settings.user_app_config)
