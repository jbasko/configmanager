try:
    # Python 2
    from ConfigParser import ConfigParser, NoSectionError, DuplicateSectionError
    ConfigParser.read_file = ConfigParser.readfp
except ImportError:
    from configparser import ConfigParser, NoSectionError, DuplicateSectionError
