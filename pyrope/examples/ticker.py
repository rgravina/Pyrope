from pyrope.server import Application
from pyrope.model import *

class TickerFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Ticker", sizerType="vertical", size=(200,-1))
        Label(run, self, value=u"Thesis is due in:")
        self.labelTime = Label(run, self, value=u"")
        self.btnOK = Button(run, self, value=u"Oh No!")
        self.btnOK.bind(EventButton, self.onButton)

    def onButton(self, event):
        self.callRemote("Close")

class TickerApplication(Application):
    def __init__(self):
        Application.__init__(self, "Ticker", description="Counts down to time thesis is due!")
    def start(self, run):
        def _done(result, frame):
            frame.centre()
            frame.show()
        #create a frame on the client
        frame = TickerFrame(run, None)
        frame.createRemote().addCallback(_done, frame)
