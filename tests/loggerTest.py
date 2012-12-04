from mercury.logger.coloredLogger import MercuryLogger,AbstractLogger
from mercury.logger.MockLoggingHandler import MockLoggingHandler
from mercury.config.AppContext import appContext
from unittest import TestCase

class testLogger(TestCase):

    TEST_LOGGER='test'

    appContext().build_defaultsettings()

    def setUp(self):
        self.logger=MercuryLogger(self.TEST_LOGGER)
        self.handler=MockLoggingHandler()
        self.logger.addHandler(self.handler)

    def testCallLogger(self):
        self.assertIsInstance(self.logger,MercuryLogger)

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