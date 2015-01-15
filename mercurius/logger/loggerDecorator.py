"""
.. module:: Mercurius Logger Decorator
   :platform: Linux
   :synopsis: decorator to show up information in a fashioned way
   :copyright: (c) 2013-2015 by Ernesto Bossi.
   :license: BSD.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>
"""

from abc import ABCMeta
import logging
from ..useful.common import get_current_method_name


class AbstractLogger(logging.Logger, metaclass=ABCMeta):
    def __init__(self, name):
        raise NotImplementedError


class DefaultLogger(AbstractLogger):
    """Default logger to build Decorator structure"""

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)
        console = logging.StreamHandler()
        self.addHandler(console)


class DecoratorLogger(AbstractLogger):
    def __init__(self, name, loggers=[], loginstances=[]):
        self.loggers = []
        for log in loggers:
            inst = log()
            self.loggers.append(inst)
        for log in loginstances:
            self.loggers.append(log)
        logging.Logger.__init__(self, name, logging.DEBUG)


    def execLogger(self, func, msg, *args, **kwargs):
        for logger in self.loggers:
            getattr(logger, func)(msg, args, kwargs)

    def critical(self, msg, *args, **kwargs):
        self.execLogger(get_current_method_name(), msg, args, kwargs)

    def error(self, msg, *args, **kwargs):
        self.execLogger(get_current_method_name(), msg, args, kwargs)

    def warning(self, msg, *args, **kwargs):
        self.execLogger(get_current_method_name(), msg, args, kwargs)

    def info(self, msg, *args, **kwargs):
        self.execLogger(get_current_method_name(), msg, args, kwargs)

    def debug(self, msg, *args, **kwargs):
        self.execLogger(get_current_method_name(), msg, args, kwargs)