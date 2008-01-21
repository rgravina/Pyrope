from pyrope.server import Application
from pyrope.model import Frame

class HelloWorldApplication(Application):
    def __init__(self):
        Application.__init__(self, "Hello World", 
                             description="Hello World! in Pyrope")
    def start(self, run):
        def _done(result):
            frame.show()
        #create a frame on the client
        frame = Frame(run, title=u"Hello World!")
        frame.createRemote().addCallback(_done)
