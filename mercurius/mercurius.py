import sys
from .config.AppContext import *
from .logger.coloredLogger import *
from logging import FileHandler, INFO
from mercurius.core.MercuryProxy import execMercury
from .daemon import *
from mercurius.useful.common import bytedecode

FORMAT = "[%(name)-s][%(levelname)-s]  %(message)s (%(filename)s:%(lineno)d) at %(asctime)-15s"

class Mercurius:
    def run(self):
        appContext.getInstance().build_defaultsettings()
        log_name = bytedecode(appContext.get(LOG, b'log_name'))
        log_file = bytedecode(appContext.get(LOG, b'log_file'))
        logger = ColoredLogger('MERCURY_LOGGER', log_file)

        file_handler = logging.FileHandler(logger.fileName)
        file_handler.setFormatter(logging.Formatter(FORMAT,"%Y-%m-%d %H:%M:%S"))

        logger.addHandler(file_handler)
        logger.setLevel(INFO)
        setMercuryLogger(logger)
        #instantiate a mercurius Proxy
        execMercury()


class MercuriusDaemon(Daemon):
    """Mercury Daemon that uses code from the base class"""
    def run(self):
        mercury = Mercurius()
        mercury.run()


DEFAULT_DAEMON_PATH='/tmp/mercurydaemon.pid'
