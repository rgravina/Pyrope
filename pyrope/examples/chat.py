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
            #update all clients chatlogs
            for app in self.run.app.runningApplications.values():
                app.frame.chatLog.value += self.run.username + ": " + self.chatInput.value + "\n"
                app.frame.chatLog.syncWithLocal()
            #clear input textbox
            self.chatInput.value = ""
            self.chatInput.syncWithLocal()
        self.chatInput.syncWithRemote().addCallback(_done)

class ChatApplication(Application):
    def __init__(self):
        Application.__init__(self, "Chat", description="A simple chat application which demonstrates multi-user applications.")
    def start(self, run):
        def _frameDone(result):
            run.frame.centre()
            run.frame.show()
            username = run.username
            for app in self.runningApplications.values():
                app.frame.chatLog.value += username + " logged in.\n"
                app.frame.chatLog.syncWithLocal()

        def _gotUsername((result, value)):
            #now we have username, log user in
            run.username = value                
            #create a frame on the client
            run.frame.createRemote().addCallback(_frameDone)
        run.frame = ChatFrame(run, None)

        def _tedDone(result):
            ted.showModalAndGetValue().addCallback(_gotUsername)
        ted = TextEntryDialog(run, None, u"Please enter a username", u"Enter username", "guest")
        ted.createRemote().addCallback(_tedDone)
