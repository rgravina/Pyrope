# runs all tests
# works from Twisted Trial:
# >trial runtests.py
# or simply python:
# >python runtests.py
import unittest
from pyrope.tests.test_server import *
from pyrope.tests.test_local import *

if __name__ == '__main__':
    unittest.main()
