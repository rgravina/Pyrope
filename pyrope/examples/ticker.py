from pyrope.server import Application
from pyrope.model import *
import datetime
from twisted.internet import task

class TickerFrame(Frame):
    y2k38_problem = datetime.datetime(2038, 1, 19, 3, 14, 7)
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Ticker", sizerType="vertical", size=(300,120))
        Label(run, self, value=u"UNIX system time overflow in:")
        self.labelTime = Label(run, self, value=self._getY2k38DiffStr())
        self.btnOK = Button(run, self, value=u"Oh No!")
        self.btnOK.bind(ButtonEvent, self.onButton)
        self.bind(CloseEvent, self.onClose)
    
    def startClock(self):
        self.loop = task.LoopingCall(self.updateClock)
        self.loop.start(1.0) # call every second

    def stopClock(self):
        self.loop.stop()
        
    def updateClock(self):
        self.labelTime.label=self._getY2k38DiffStr()

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

    def _getY2k38DiffStr(self):
        return self._getDiffStr(self.y2k38_problem)

    def onButton(self, event):
        self.close()

    def onClose(self, event):
        self.stopClock()
        self.destroy()

class TickerApplication(Application):
    def __init__(self):
        Application.__init__(self, "Ticker", description="Counts down to the UNIX system time overflow!")
    def start(self, run):
        def _done(result, frame):
            frame.centre()
            frame.show()
            frame.startClock()

        #create a frame on the client
        frame = TickerFrame(run, None)
        frame.createRemote().addCallback(_done, frame)
