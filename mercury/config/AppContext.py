import ConfigParser,io,inspect
from mercury.useful.singleton import Singleton
from mercury.exceptions import ConfigError
import os

path = os.getcwd()
MERCURY_ROOT= os.sep.join(path.split(os.sep)[:-1])

DEFAULT_NAME="SETTINGS.conf"
DEFAULT_FILENAME=MERCURY_ROOT+DEFAULT_NAME
OBJECTSECTION="OBJECTS"

#Convention MasterCatalog
MASTER_CATALOG="MasterCatalog"
DOCUMENTAL_DB="DocumentalDB"
LOG="Log"
MERCURY="MERCURY"

setting_template=[(LOG,[("LOG_FILE",MERCURY_ROOT+"/logfile.log"),("LOG_NAME","mercury_log"),("OUTPUT_STDOUT",False)]),
                  ('DocumentalDB',[("COUCH_DB_NAME",'http://localhost:5984')]),
                  ('General',[("SHOW_DEBUG_INFO",0),("MERCURY_ROOT_DIR",MERCURY_ROOT),("SECTION_DESCRIPTOR",MASTER_CATALOG)]),
                  (MASTER_CATALOG,[(LOG,LOG),(DOCUMENTAL_DB,"Document"),(MERCURY,MERCURY)]) #Do not modify this like
]

class appContext():
    """Simple wrapper for the ConfigParser module used in this proyect. It also stores reference to objects"""

    __metaclass__=Singleton

    def __init__(self,filename=DEFAULT_FILENAME):
        self.config_parser=ConfigParser.RawConfigParser()
        self.get_settings(filename)

    @staticmethod
    def build_defaultsettings(save=False):
        appC=appContext()
        for section in setting_template:
            appC.config_parser.add_section(section[0])
            for value in  section[1]:
                appC.set_property(section[0],value[0],value[1])
        if save:
            with open(DEFAULT_FILENAME,'wb+') as file:
                appC.config_parser.write(file)

    def get_settings(self,filename=DEFAULT_FILENAME,flow=False):
        if flow:
            f=io.BytesIO(filename)
        else:
            f=open(filename,'w+')
        self.config_parser.readfp(f)

    @staticmethod
    def sectionExists(section):
        try:
            appContext().get(section,"a")
            return True
        except ConfigParser.NoOptionError:
            return True
        except ConfigParser.NoSectionError,Exception:
            return False

    def sanitizeKeyValue(self,key,value):
        try:
            return key.encode('ascii','xmlcharrefreplace'),value.encode('ascii','xmlcharrefreplace')
        except AttributeError:
            return key,value

    #Setters
    @staticmethod
    def set_object(klass,object):
        appC=appContext()
        if inspect.isclass(klass) and isinstance(object,klass):
            if not appC.sectionExists(OBJECTSECTION):
                appC.config_parser.add_section(OBJECTSECTION)
            appC.set_property(OBJECTSECTION,klass,object)

    @staticmethod
    def set_property(section,key,value):
        appC=appContext()
        lkey,lvalue=appC.sanitizeKeyValue(key,value)
        appC.config_parser.set(section,lkey,lvalue)

    #getters
    @staticmethod
    def getObject(klass):
        return appContext().get(OBJECTSECTION,klass)

    @staticmethod
    def getValue(key):
        for section in appContext().config_parser.sections():
            try:
                return appContext().get(section,key)
            except ConfigParser.NoOptionError:
                pass #keep iterating
        raise ConfigError("No value with key {1} on AppContext".format(key))

    @staticmethod
    def get(section,key):
        """staticmethod that returns value from section and option from default file"""
        return appContext().get_value(section,key)


    def get_value(self,section,key):
        try:
            return self.config_parser.get(section,key)
        except ConfigParser.NoOptionError,ConfigParser.NoSectionError:
            raise ConfigError()

    #delete objects
    def remove(self,section,option):
        appContext().config_parser.remove_option(section,option)

    @staticmethod
    def remove_object(section,option):
        if appContext().sectionExists(section):
            appContext().remove(section,option)

    @staticmethod
    def clear_section(section):
        if appContext().sectionExists(section):
            for option in appContext().config_parser.options(section):
                appContext().remove(section,option)
