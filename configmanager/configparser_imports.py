import six

if six.PY2:
    from ConfigParser import ConfigParser, NoSectionError, DuplicateSectionError
    ConfigParser.read_file = ConfigParser.readfp
else:
    from configparser import ConfigParser, NoSectionError, DuplicateSectionError
