from pyrope.server import Application
from pyrope.model import *

class HelloWorldApplication(Application):
    def __init__(self):
        Application.__init__(self, "Hello World", description="A simple Hello World application for Pyrope. Displays one frame with the title set to \"Hello World\".")
    def start(self, run):
        def _done(result, frame):
            frame.Show()
        #create a frame on the client
        frame = Frame(run, None, title=u"Hello World!")
        frame.createRemote().addCallback(_done, frame)
