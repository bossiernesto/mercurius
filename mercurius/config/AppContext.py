"""
.. module:: AppContext
   :platform: Linux
   :synopsis: AppContext using configParser
   :copyright: (c) 2012 by Ernesto Bossi.
   :license: BSD.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""
__version__ = '0.0.1'
import configparser
import io
import inspect
from mercurius.useful.singleton import Singleton
from mercurius.exceptions import ConfigError
from mercurius.logger.loggerDecorator import AbstractLogger
import os

path = os.getcwd()
MERCURY_ROOT = os.sep.join(path.split(os.sep)[:-1])

DEFAULT_NAME = 'SETTINGS.conf'
DEFAULT_FILENAME = MERCURY_ROOT + DEFAULT_NAME
OBJECTSECTION = "OBJECTS"

# Convention MasterCatalog
MASTER_CATALOG = "MasterCatalog"
DOCUMENTAL_DB = "DocumentalDB"
LOG = 'Log'
MERCURY = 'MERCURY'

#Mercurius Server Settings
PROTOCOL_VERSION = 'Protocol_Version'

setting_template = [
    (LOG, [('log_file', MERCURY_ROOT + '/logfile.log'), ('log_name', 'mercury_log'), ('output_stdout', False)]),
    ('DocumentalDB', [('couch_db_name', 'http://localhost:5984')]),
    (MERCURY, [('SHOW_DEBUG_INFO', 0), ('mercury_root_dir', MERCURY_ROOT), ('section_descriptor', MASTER_CATALOG),
               ('verbose', True), ('port', 9090),
               ('version', 'Mercury' + __version__), (PROTOCOL_VERSION, 'HTTP/1.1')]),
    (MASTER_CATALOG, [(LOG, LOG), (DOCUMENTAL_DB, 'Document'), (MERCURY, MERCURY)])  #Do not modify this like
]


class appContext(Singleton):
    """Simple wrapper for the ConfigParser module used in this proyect. It also stores reference to objects"""

    def __init__(self, filename=DEFAULT_FILENAME):
        self.config_parser = configparser.RawConfigParser()
        self.get_settings(filename)

    #Builders
    def build_defaultsettings(self, save=False):
        for section in setting_template:
            self.config_parser.add_section(section[0])
            for value in section[1]:
                self.set_property(section[0], value[0], value[1])
        if save:
            with open(DEFAULT_FILENAME, 'wb+') as file:
                self.config_parser.write(file)

    def get_settings(self, filename=DEFAULT_FILENAME, flow=False):
        if flow:
            f = io.BytesIO(filename)
        else:
            f = open(filename, 'w+')
        self.config_parser.readfp(f)

    def sectionExists(self, section):
        return section in self.config_parser.sections()

    def sanitizeKeyValue(self, key, value):
        try:
            return key.encode('ascii', 'xmlcharrefreplace'), value.encode('ascii', 'xmlcharrefreplace')
        except AttributeError:
            return key, value

    #Setters
    def set_object(self, klass, object):
        if inspect.isclass(klass) and isinstance(object, klass):
            if not self.sectionExists(OBJECTSECTION):
                self.config_parser.add_section(OBJECTSECTION)
            self.set_property(OBJECTSECTION, klass.__name__, object)

    def set_property(self, section, key, value):
        lkey, lvalue = self.sanitizeKeyValue(key, value)
        self.config_parser.set(section, lkey, lvalue)

    #getters
    def getObject(self, klass):
        return self.get(OBJECTSECTION, klass)

    def getValue(self, key):
        for section in self.config_parser.sections():
            try:
                return self.get(section, key)
            except ConfigError:
                pass #keep iterating
        raise ConfigError("No value with key {0} on AppContext".format(key))

    @staticmethod
    def get(section, key):
        """staticmethod that returns value from section and option from default file"""
        return appContext.getInstance()._get_value(section, key)

    def _get_value(self, section, key):
        try:
            return self.config_parser.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            raise ConfigError()

    def _get_section(self, key):
        for section in self.config_parser.sections():
            try:
                self._get_value(section, key)
                return section
            except ConfigError:
                pass    #Keep iterating
        raise ConfigError("No section found for  key {1} on AppContext".format(key))

    #delete objects
    def remove(self, section, option):
        self.config_parser.remove_option(section, option)

    def remove_object(self, option):
        try:
            section = self._get_section(option)
            self.remove(section, option)
        except ConfigError:
            pass    #Because it's a delete method if it can't find the option in the AppContext then it doesn't exists

    def clear_section(self, section):
        if self.sectionExists(section):
            for option in self.config_parser.options(section):
                self.remove(section, option)

    def removeSection(self, section):
        self.config_parser.remove_section(section)

    #Helper function
    def getDebugPrint(self):
        for section in self.config_parser.sections():
            print(section)


def getAppContext():
    return appContext.getInstance()


MERCURIUSLOGGER = 'MERCURIUS_LOGGER'


def getMercuryLogger():
    try:
        return getAppContext().getValue(MERCURIUSLOGGER)
    except ConfigError:
        return None


def setMercuryLogger(logger):
    try:
        if not isinstance(logger, AbstractLogger):
            raise ConfigError('{0} is not an AbstractLogger to Register in AppContext'.format(logger))
        getAppContext().set_property(LOG, MERCURIUSLOGGER, logger)
    except configparser.NoSectionError:
        getAppContext().build_defaultsettings()
        setMercuryLogger(logger)