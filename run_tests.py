
import unittest
import glob
import sys

test_file_strings = glob.glob('test/*/test_*.py')
module_strings = [str[0:len(str) - 3] for str in test_file_strings]
modules_paths = [str.replace('/', '.') for str in module_strings]
modules = [__import__(str) for str in modules_paths]
suites = [unittest.defaultTestLoader.loadTestsFromName(str) for str
          in modules_paths]
testSuite = unittest.TestSuite(suites)
text_runner = unittest.TextTestRunner(sys.stdout, verbosity=2).run(testSuite)
exit_result =  1 if len(text_runner.errors) > 0 else 0
sys.exit(exit_result)