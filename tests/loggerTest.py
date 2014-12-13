from mercurius.logger.coloredLogger import ColoredLogger,AbstractLogger
from mercurius.logger.MockLoggingHandler import MockLoggingHandler
from mercurius.config.AppContext import appContext
from unittest import TestCase

class testLogger(TestCase):

    TEST_LOGGER='test'

    appContext.getInstance().build_defaultsettings()

    def setUp(self):
        self.logger=ColoredLogger(self.TEST_LOGGER)
        self.handler=MockLoggingHandler()
        self.logger.addHandler(self.handler)

    def testCallLogger(self):
        self.assertIsInstance(self.logger,ColoredLogger)

    def testLogInfo(self):
        self.logger.info('Info Test')
        self.assertTrue('Info Test' in self.handler.messages['info'])

    def testAbstractLogger(self):
        with self.assertRaises(NotImplementedError):
            abstractLogger=AbstractLogger(name='abstract')

    def testMessageQueue(self):
        self.handler.reset() #reset Mock lists
        self.logger.warning('Warning 1')
        self.logger.error('Error 1')
        self.logger.error('Error 2')
        self.assertEqual(len(self.handler.messages['error']),2)
        self.assertEqual(len(self.handler.messages['warning']),1)