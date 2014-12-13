import logging
from .coloredFormater import *
from abc import ABCMeta
from mercury.config.AppContext import *

class AbstractLogger(logging.Logger):

    __metaclass__=ABCMeta

    def __init__(self,name):
        raise NotImplementedError


# Custom logger class with multiple destinations
import logging
from . import coloredFormater as c
from .loggerDecorator import AbstractLogger

FORMAT = "[$BOLD%(name)-s$RESET][%(levelname)-s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d) at %(asctime)-15s"

# Custom logger class with multiple destinations
class ColoredLogger(AbstractLogger):
    COLOR_FORMAT = c.formatter_message(FORMAT, True)

    def __init__(self, name, file_name=None):
        logging.Logger.__init__(self, name, logging.DEBUG)
        self.fileName= file_name if file_name else 'logfile.log'

        color_formatter = c.ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        logging.setLoggerClass(ColoredLogger)
