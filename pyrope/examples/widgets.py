from pyrope.server import Application
from pyrope.model import *
from twisted.internet.defer import inlineCallbacks

class DemoFrame(SizedFrame):
    def __init__(self, run, parent):
        SizedFrame.__init__(self, run, parent, title=u"Widget Demo", sizerType="vertical")
        self.text = TextBox(run, self, size=(250,-1), value=u"Enter some text.")
        self.text.bind(EventText, self.onText)
        self.label = Label(run, self, value=u"Widget Demo")
        self.button = Button(run, self, value=u"Click Me!")
        self.button.bind(EventButton, self.onButton)
        self.bind(EventClose, self.onClose)

    def onText(self, event):
        self.label.SetValue(event.widget.value)

    def onButton(self, event):
        self.label.SetValue("Clicked button!")

    def onClose(self, event):
        def _done(result):
            def _done(result):
                dlg.Destroy()
                if result == wx.ID_OK:
                    self.Destroy()
            dlg.ShowModal().addCallback(_done)
        dlg = MessageDialog(self.run, self, u"Are you sure you want to quit Widget Demo?", caption=u"Quit Widget Demo?", style=wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        dlg.createRemote().addCallback(_done)

class WidgetsApplication(Application):
    def __init__(self):
        Application.__init__(self, "Widget Demo", description="Demonstrates Pyrope widgets, event handling etc..")
    def start(self, run):
        def _done(result):
            #although Centre and Show return Deferred's, their order of execution is not important, so we can ignore them.
            #GetBackgroundColour returns the localally cached value
            frame.Centre()
            frame.Show()
            
        #create a local representation of a frame
        frame = DemoFrame(run, None)
        #create the resource on client (to show it, call frame.show())
        frame.createRemote().addCallback(_done)
