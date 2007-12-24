from pyrope.server import Application
from pyrope.model import *

class ChatFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Chat", sizerType="vertical")
        self.chatLog = TextBox(run, self, size=(380, 150), multiline=True, readonly=True)
        self.chatInput = TextBox(run, self, size=(380, -1))
        self.btnSend = Button(run, self, value=u"Send")
        self.btnSend.bind(ButtonEvent, self.onSendButton)

    def onSendButton(self, event):
        def _done(result):
            self.chatLog.value += "\n" + self.run.username + ": " + self.chatInput.value
            self.chatLog.syncWithLocal()
            self.chatInput.value = ""
            self.chatInput.syncWithLocal()
        self.chatInput.syncWithRemote().addCallback(_done)

class ChatApplication(Application):
    def __init__(self):
        Application.__init__(self, "Chat", description="A simple chat application which demonstrates multi-user applications.")
    def start(self, run):
        def _frameDone(result):
            frame.chatLog.value += run.username + " logged in."
            frame.chatLog.syncWithLocal()
            frame.centre()
            frame.show()

        def _gotUsername((result, value)):
            #now we have username, log user in
            run.username = value                
            #create a frame on the client
            frame.createRemote().addCallback(_frameDone)
        frame = ChatFrame(run, None)

        def _tedDone(result):
            ted.showModalAndGetValue().addCallback(_gotUsername)
        ted = TextEntryDialog(run, None, u"Please enter a username", u"Enter username", "guest")
        ted.createRemote().addCallback(_tedDone)
