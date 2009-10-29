import unittest
from eskimoapps.testing.mock import Mock
from pyrope.model.local import *
from pyrope.errors import *
from wx import ImageFromStream, BitmapFromImage
import cStringIO

class PyropeWidgetTest(unittest.TestCase):
    def testRemoteCallFails(self):
        #create a local representation of a frame
        app = Mock()
        app.widgets = []
        frame = Frame(app, Mock(), None)
        self.assertRaises(RemoteResourceNotCreatedException, frame.show)


class ImageTest(unittest.TestCase):
    def testImage(self):
        """Actually no real testing is done here.. just makes sure it doesn't throw any errors on load"""
        run = Mock()
        run.widgets = []
        panel = Mock()
        image = PNGImage(run, panel, "/Users/rgravina/Pyrope/images/pyrope.png")
        
if __name__ == '__main__':
    unittest.main()

