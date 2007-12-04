from pyrope.server import Application
from pyrope.model import *

class TickerApplication(Application):
    def __init__(self):
        Application.__init__(self, "Ticker", description="Counts down to time thesis is due!")
    def start(self, run):
        def _done(result, frame):
            frame.Show()
        #create a frame on the client
        frame = Frame(run, None, title=u"Ticker")
        frame.createRemote().addCallback(_done, frame)
