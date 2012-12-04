import logging
import coloredFormater as c
from abc import ABCMeta
from mercury.config.AppContext import *

class AbstractLogger(logging.Logger):

    __metaclass__=ABCMeta

    def __init__(self,name):
        raise NotImplementedError


# Custom logger class with multiple destinations
class MercuryLogger(AbstractLogger):
    FORMAT = "[$BOLD%(name)-s$RESET] at [%(threadName)s][%(levelname)-s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d) at %(asctime)-15s.%(msecs)03d]"
    COLOR_FORMAT = c.formatter_message(FORMAT, True)
    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)

        color_formatter = c.ColoredFormatter(self.COLOR_FORMAT)

        logfile=appContext().get(LOG,"LOG_FILE")

        filehandler = logging.RotatingFileHandler(logfile,maxBytes=(log_size*(1<<20)),backupCount=5)
        filehandler.setFormatter(color_formatter)

        self.addHandler(filehandler)
        logging.setLoggerClass(MercuryLogger)
        return