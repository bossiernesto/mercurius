import unittest
from mercurius.config.AppContext import *
from mercurius.useful import singleton
from configparser import DuplicateSectionError

class AppContextTestCase(unittest.TestCase):
    def setUp(self):
        self.app = appContext.getInstance()
        try:
            self.app.build_defaultsettings()
        except DuplicateSectionError:
            pass  # silence it

    def tearDown(self):
        singleton.forgetAllSingletons()

    def test_sectionlen(self):
        self.assertEqual(4, len([section for section in self.app.config_parser.sections()]))

    def test_sectionExists(self):
        self.assertTrue(self.app.sectionExists("Log"))

    def test_getVersion(self):
        self.assertEqual("HTTP/1.1", self.app.getValue(PROTOCOL_VERSION))

    def test_setvalue(self):
        pass

    def test_setObject(self):
        pass

    def test_AppContextSingleton(self):
        appCon = appContext.getInstance()
        self.assertEqual(appCon, self.app)


if __name__ == '__main__':
    unittest.main()
