from pyrope.server import Application
from pyrope.model import *
from pyrope.model.events import *
from twisted.internet.defer import inlineCallbacks
from time import sleep

class DemoFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Widget Demo", sizerType="vertical", minimiseBox=False)
        self.toolBar = ToolBar(run, self)
        self.toolBar.addTool(u"Tool", Image(run, self, "images/dot-red.png"))
        self.toolBar.addTool(u"Tool", Image(run, self, "images/dot-blue.png"))
        self.toolBar.addTool(u"Tool", Image(run, self, "images/dot-green.png"))
        self.toolBar.addTool(u"Tool", Image(run, self, "images/dot-orange.png"))
        self.toolBar.addTool(u"Tool", Image(run, self, "images/dot-purple.png"))

        #setup menu
        menuBar = MenuBar(run, self)
        menuFile = Menu(u"Menu1")
        item1 = MenuItem(u"Item1")
        item2 = MenuItem(u"Item2")
        menuFile.addItem(item1)
        menuFile.addItem(item2)
        menuHelp = Menu(u"Menu2")
        menuHelp.addItem(MenuItem(u"Item1"))
        menuHelp.addItem(MenuItem(u"Item2"))

        menuBar.addMenu(menuFile)
        menuBar.addMenu(menuHelp)

        menuBar.bind(item1, self.onItem1)
        menuBar.bind(item2, self.onItem2)
        self.menuBar = menuBar
        
        topPanel = Panel(run, self, sizerType="horizontal")
        lhsPanel = Panel(run, topPanel, sizerType="vertical")

        self.text = TextBox(run, lhsPanel, value=u"Enter some text.")
        self.text.bind(TextEvent, self.onText)
        self.label = Label(run, lhsPanel, value=u"Widget Demo")
        self.cancelButton = Button(run, lhsPanel, value=u"Cancel")
        self.cancelButton.bind(ButtonEvent, self.onCancelButton)
        self.okButton = Button(run, lhsPanel, value=u"OK", default=True)
        self.okButton.bind(ButtonEvent, self.onOKButtonPrebind)
        self.okButton.bind(ButtonEvent, self.onOKButton)
#        self.bind(CloseEvent, self.onClose)

        checkBox = CheckBox(run, lhsPanel, label=u"two states", alignRight=True)
        checkBoxThree = CheckBox(run, lhsPanel, label=u"three states", threeState=True, userCanSelectThirdState=True)
        self.choice = Choice(run, lhsPanel, choices=["one","two","three"])

        rhsPanel = Panel(run, topPanel, sizerType="vertical")
        
        self.gauge = Gauge(run, rhsPanel, size=(200,-1))
        self.slider = Slider(run, rhsPanel, displayLabels=True)
        self.slider.bind(ScrollEvent, self.onScroll)
        self.lb = ListBox(run, rhsPanel, choices=["one","two","three"])
        clb = CheckListBox(run, rhsPanel, choices=["one","two","three"])

        rhsPanel2 = Panel(run, topPanel, sizerType="vertical")
        box = Box(run, rhsPanel2, label=u"A box")
        spinner = Spinner(run, rhsPanel2, wrap=True)
        line = Line(run, rhsPanel2, size=(200,-1))
        radioBox = RadioBox(run, rhsPanel2, label=u"Radio Box!", choices=["one","two","three", "four", "five", "six"], cols=2)
        image = Image(run, rhsPanel2, "images/pyrope.png")
        
        bottomPanel = Panel(run, self, sizerType="vertical")
        self.output = TextBox(run, bottomPanel, value=u"Widget ouput...\n", size=(400,100), readonly=True, multiline=True)

        self.statusBar = StatusBar(run, self, fields=[u"demo online"])

        splitter = Splitter(run, self, minimumPaneSize=20, liveUpdate=True)
        splitterPanel1 = Panel(run, splitter, sizerType="vertical")
        label = Label(run, splitterPanel1, value=u"Left side of splitter panel")
        splitterPanel2 = Panel(run, splitter, sizerType="vertical")
        label = Label(run, splitterPanel2, value=u"Right side of splitter panel")
        bitmapButton = BitmapButton(run, splitterPanel2, Image(run, self, "images/dot-red.png"))

        rhsPanel3 = Panel(run, topPanel, sizerType="vertical")
        notebook = Notebook(run, topPanel)
        notePanel1 = Panel(run, notebook, sizerType="horizontal")
        notebook.addPage(u"Page 1", notePanel1)
        Label(run, notePanel1, value=u"Page 1")
        Label(run, notePanel1, value=u"Page 1")
        Label(run, notePanel1, value=u"Page 1")
        notePanel2 = Panel(run, notebook, sizerType="horizontal")
        notebook.addPage(u"Page 2", notePanel2)
        Label(run, notePanel2, value=u"Page 2")
        Label(run, notePanel2, value=u"Page 2")
        Label(run, notePanel2, value=u"Page 2")
        notebook.bind(NotebookPageChangingEvent, self.onNotebookChanging)
#        notebook.bind(NotebookPageChangedEvent, self.onNotebookChanged)

    def onNotebookChanging(self, event):
        
        self.label.label = u"Notebook changing from %d to %d" % (event.data["oldSelection"], event.data["selection"])
        
    def onNotebookChanged(self, event):
        self.label.label = u"Notebook changed from %d to %d" % (event.data["oldSelection"], event.data["selection"])
        
    def onItem1(self):
        self.label.label = u"Item 1 selected"
        self.output.value += u"Dropdown selection: %s\n" % self.choice.choices[self.choice.selectedIndex]

    def onItem2(self):
        self.label.label = u"Item 2 selected"
    
    def onText(self, event):
        self.label.label = self.text.value
        
    def onOKButtonPrebind(self, event):
        #demonstrates passing the event on to the next handler
        self.output.value += u"Dropdown selection: %s\n" % self.choice.choices[self.choice.selectedIndex]
        return True

    def onOKButton(self, event):
#        self.output.value += u"waitig 5 secs...\n"
#        sleep(5)
        self.text.value = u"Clicked OK!"
        self.lb.setChoice(0, "1")
        
    def onCancelButton(self, event):
        self.text.value = u"Clicked Cancel!"
        self.lb.choices = ["one","two","three"]
 
    def onScroll(self, event):
        self.gauge.value = self.slider.value
        print self.slider.value

    def onClose(self, event):
        def _done(result):
            def _done(result):
                dlg.destroy()
                if result == wx.ID_OK:
                    self.destroy()
            dlg.showModal().addCallback(_done)
        dlg = MessageDialog(self.run, self, u"Are you sure you want to quit Widget Demo?", caption=u"Quit Widget Demo?")
        dlg.createRemote().addCallback(_done)
    
class WidgetsApplication(Application):
    def __init__(self):
        Application.__init__(self, "Widget Demo", description="Demonstrates Pyrope widgets, event handling etc..")
    def start(self, run):
        def _done(result):
            #although Centre and Show return Deferred's, their order of execution is not important, so we can ignore them.
            frame.centre()
            #note: frame.callRemote("Show") also works
            frame.show()
            #test setting a wxWindow attribute
            frame.label.backgroundColour = (255, 125, 27)
            
        #create a local representation of a frame
        frame = DemoFrame(run, None)
        #create the resource on client (to show it, call frame.show())
        frame.createRemote().addCallback(_done)