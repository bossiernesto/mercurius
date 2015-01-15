import threading
from .config.AppContext import *
from .logger.coloredLogger import *
from logging import INFO
from mercurius.core.MercuriusProxy import buildMercuryServer
from .daemon import *
from mercurius.useful.common import bytedecode

FORMAT = "[%(name)-s][%(levelname)-s]  %(message)s (%(filename)s:%(lineno)d) at %(asctime)-15s"

class Mercurius:
    def __init__(self):
        self.server = buildMercuryServer()
        self.cycle = 0.1

    def run(self):
        appContext.getInstance().build_defaultsettings()
        log_name = bytedecode(appContext.get(LOG, b'log_name'))
        log_file = bytedecode(appContext.get(LOG, b'log_file'))
        logger = ColoredLogger(log_name, log_file)

        file_handler = logging.FileHandler(logger.fileName)
        file_handler.setFormatter(logging.Formatter(FORMAT,"%Y-%m-%d %H:%M:%S"))

        logger.addHandler(file_handler)
        logger.setLevel(INFO)
        setMercuryLogger(logger)
        #instantiate a mercurius Proxy
        self.start_serving()

    def start_serving(self, daemon=False):
        server_thread = threading.Thread(target = self.server.serve_forever)
        if daemon:
            server_thread.setDaemon(daemon)
        server_thread.start()

        while True:
            time.sleep(self.cycle)

    def stop_serving(self):
        self.server.shutdown()

class MercuriusDaemon(Daemon):
    """Mercury Daemon that uses code from the base class"""
    def run(self):
        mercury = Mercurius()
        mercury.run()


DEFAULT_DAEMON_PATH='/tmp/mercurydaemon.pid'
