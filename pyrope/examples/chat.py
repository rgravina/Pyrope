from pyrope.server import Application
from pyrope.model import *

class ChatFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Chat", sizerType="vertical")
        self.chatLog = TextBox(run, self, size=(380, 180), multiline=True, readonly=True)
        self.chatInput = TextBox(run, self, size=(380, -1))
        self.chatInput.bind(TextEnterEvent, self.onTextEnter)

    def onTextEnter(self, event):
        print "enter pressed"

class ChatApplication(Application):
    def __init__(self):
        Application.__init__(self, "Chat", description="A simple chat application which demonstrates multi-user applications.")
    def start(self, run):
        def _done(result):
            frame.centre()
            frame.show()
        #create a frame on the client
        frame = ChatFrame(run, None)
        frame.createRemote().addCallback(_done)
