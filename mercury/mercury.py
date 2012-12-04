import sys
from mercury.config.AppContext import *
from mercury.logger.coloredFormater import *
from logging import FileHandler


class Mercury:
    def run(self):
        logname=appContext().getValue(LOG,"LOG_NAME")
        logger=ColoredFormatter(logname)
        logger.addhandler(FileHandler)
        appContext.set_object(logger.__class__,logger)
        #instantiate a mercury Proxy

if __name__ == '__main__':
    sys.exit(Mercury().run())



