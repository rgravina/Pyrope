from pyrope.server import Application
from pyrope.model import *
import datetime
from twisted.internet import task

class TickerFrame(Frame):
    dueDate = datetime.datetime(2008, 1, 24, 18, 00)
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Ticker", sizerType="vertical", size=(300,120))
        Label(run, self, value=u"Thesis is due in:")
        self.labelTime = Label(run, self, value=self._getDiffStr())
        self.btnOK = Button(run, self, value=u"Oh No!")
        self.btnOK.bind(ButtonEvent, self.onButton)
        self.bind(CloseEvent, self.onClose)
    
    def startClock(self):
        self.loop = task.LoopingCall(self.updateClock)
        self.loop.start(1.0) # call every second

    def stopClock(self):
        self.loop.stop()
        
    def updateClock(self):
        self.labelTime.label=self._getDiffStr()
        self.labelTime.syncWithLocal()

    def _getDiffStr(self):
        now = datetime.datetime.now()
        diff = self.dueDate - now
        hours = diff.seconds / 3600 #secs in one hour
        mins = ((diff.seconds % (hours*3600) / 60)) #secs in one min
        secs = ((diff.seconds % (hours*3600+mins*60)))
        diffStr = "%d days, %d hours %d mins %d secs" % (diff.days, hours, mins, secs)
        return diffStr
    
    def onButton(self, event):
        self.callRemote("Close")

    def onClose(self, event):
        self.stopClock()
        self.destroy()

class TickerApplication(Application):
    def __init__(self):
        Application.__init__(self, "Ticker", description="Counts down to time thesis is due!")
    def start(self, run):
        def _done(result, frame):
            frame.centre()
            frame.show()
            frame.startClock()

        #create a frame on the client
        frame = TickerFrame(run, None)
        frame.createRemote().addCallback(_done, frame)
