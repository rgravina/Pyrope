from pyrope.server import Application
from pyrope.model import *

class ChatApplication(Application):
    def __init__(self):
        Application.__init__(self, "Chat", description="A simple chat application which demonstrates multi-user applications.")
    def start(self, run):
        def _done(result, frame):
            frame.show()
        #create a frame on the client
        frame = Frame(run, None, title=u"Chat")
        frame.createRemote().addCallback(_done, frame)
