import logging
from pyparsing import *

ESC = Literal('\x1b')
integer = Word(nums)
escapeSeq = Combine(ESC + '[' + Optional(delimitedList(integer,';')) +
                    oneOf(list(alphas)))

nonAnsiString = lambda s : Suppress(escapeSeq).transformString(s)

#Mock logger to get messages
class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""


    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        level=nonAnsiString(record.levelname.lower())
        self.messages[level].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': []
        }
