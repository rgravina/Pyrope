from pyrope.server import Application
from pyrope.model import *
from pyrope.model.events import *
from twisted.internet.defer import inlineCallbacks

class DemoFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Widget Demo", sizerType="vertical", minimiseBox=False)
        
        topPanel = Panel(run, self, sizerType="horizontal")
        lhsPanel = Panel(run, topPanel, sizerType="vertical")

        self.text = TextBox(run, lhsPanel, value=u"Enter some text.")
        self.text.bind(TextEvent, self.onText)
        self.label = Label(run, lhsPanel, value=u"Widget Demo")
        self.cancelButton = Button(run, lhsPanel, value=u"Cancel")
        self.cancelButton.bind(ButtonEvent, self.onCancelButton)
        self.okButton = Button(run, lhsPanel, value=u"OK", default=True)
        self.okButton.bind(ButtonEvent, self.onOKButton)
#        self.bind(EventClose, self.onClose)

        checkBox = CheckBox(run, lhsPanel, label=u"two states", alignRight=True)
        checkBoxThree = CheckBox(run, lhsPanel, label=u"three states", threeState=True, userCanSelectThirdState=True)
        self.choice = Choice(run, lhsPanel, choices=["one","two","three"])

        rhsPanel = Panel(run, topPanel, sizerType="vertical")
        
        gauge = Gauge(run, rhsPanel, size=(200,-1), value=30)
        slider = Slider(run, rhsPanel, displayLabels=True)
        self.lb = ListBox(run, rhsPanel, choices=["one","two","three"])
        clb = CheckListBox(run, rhsPanel, choices=["one","two","three"])

        rhsPanel2 = Panel(run, topPanel, sizerType="vertical")
        box = Box(run, rhsPanel2, label=u"A box")
        spinner = Spinner(run, rhsPanel2, wrap=True)
        line = Line(run, rhsPanel2, size=(200,-1))
        radioBox = RadioBox(run, rhsPanel2, label=u"Radio Box!", choices=["one","two","three", "four", "five", "six"], cols=2)

        bottomPanel = Panel(run, self, sizerType="vertical")
        output = TextBox(run, bottomPanel, value=u"Widget ouput...", size=(400,100), readonly=True, multiline=True)

    def onText(self, event):
        def _done(result):
            self.label.label = self.text.value
            self.label.syncWithLocal()
        self.text.syncWithRemote().addCallback(_done)

    def onOKButton(self, event):
        def _done(result):
            self.text.value = u"Clicked OK!"
            self.lb.choices = ["1","2","3"]
            self.text.syncWithLocal()
            self.lb.syncWithLocal()
        self.text.syncWithRemote().addCallback(_done)

    def onCancelButton(self, event):
        self.text.value = u"Clicked Cancel!"
        self.lb.choices = ["one","two","three"]
        self.text.syncWithLocal()
        self.lb.syncWithLocal()

#    def onClose(self, event):
#        def _done(result):
#            def _done(result):
#                dlg.destroy()
#                if result == wx.ID_OK:
#                    self.destroy()
#            dlg.showModal().addCallback(_done)
#        dlg = MessageDialog(self.run, self, u"Are you sure you want to quit Widget Demo?", caption=u"Quit Widget Demo?")
#        dlg.createRemote().addCallback(_done)
    
class WidgetsApplication(Application):
    def __init__(self):
        Application.__init__(self, "Widget Demo", description="Demonstrates Pyrope widgets, event handling etc..")
    def start(self, run):
        def _done(result):
            #although Centre and Show return Deferred's, their order of execution is not important, so we can ignore them.
            #GetBackgroundColour returns the localally cached value
            frame.centre()
            #note: frame.callRemote("Show") also works
            frame.show()
            
        #create a local representation of a frame
        frame = DemoFrame(run, None)
        #create the resource on client (to show it, call frame.show())
        frame.createRemote().addCallback(_done)
