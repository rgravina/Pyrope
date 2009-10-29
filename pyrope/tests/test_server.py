import unittest
from pyrope.server import *
from eskimoapps.testing.mock import Mock

class TestServer(unittest.TestCase):
    def testDuplicateRegisterFails(self):
        server = PyropeServer()
        app = Mock
        server.registerApplication(app)
        self.assertRaises(ApplicationAlreadyRegisteredException, server.registerApplication, app)
        
if __name__ == '__main__':
    unittest.main()