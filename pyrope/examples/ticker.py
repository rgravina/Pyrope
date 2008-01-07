from pyrope.server import Application
from pyrope.model import *
import datetime
from twisted.internet import task

class TickerFrame(Frame):
    draftDueDate = datetime.datetime(2008, 1, 16, 17, 00)
    thesisDueDate = datetime.datetime(2008, 1, 30, 17, 00)
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Ticker", sizerType="vertical", size=(300,210))
        Label(run, self, value=u"Thesis DRAFT is due in:")
        self.labelDraftTime = Label(run, self, value=self._getDraftDiffStr())
        Line(run, self, size=(300,-1))
        Label(run, self, value=u"Thesis FINAL is due in:")
        self.labelThesisTime = Label(run, self, value=self._getThesisDiffStr())
        self.btnOK = Button(run, self, value=u"Oh No!")
        self.btnOK.bind(ButtonEvent, self.onButton)
        self.bind(CloseEvent, self.onClose)
    
    def startClock(self):
        self.loop = task.LoopingCall(self.updateClock)
        self.loop.start(1.0) # call every second

    def stopClock(self):
        self.loop.stop()
        
    def updateClock(self):
        self.labelDraftTime.label=self._getDraftDiffStr()
        self.labelThesisTime.label=self._getThesisDiffStr()
        syncWithLocal(self.labelDraftTime, self.labelThesisTime)

    def _getDiffStr(self, dueDate):
        now = datetime.datetime.now()
        diff = dueDate - now
        hours = diff.seconds / 3600 #secs in one hour
        if hours:
            mins = ((diff.seconds % (hours*3600) / 60)) #secs in one min
        else:
            mins = diff.seconds / 60 #secs in one min
        if hours or mins:
            secs = ((diff.seconds % (hours*3600+mins*60)))
        else:
            secs = diff.seconds
        diffStr = "%d days, %d hours %d mins %d secs" % (diff.days, hours, mins, secs)
        return diffStr

    def _getDraftDiffStr(self):
        return self._getDiffStr(self.draftDueDate)
    def _getThesisDiffStr(self):
        return self._getDiffStr(self.thesisDueDate)

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
