import wx
import wxaddons.sized_controls as sc

class AddressBookEntry(object):
    def __init__(self, name="", email="", phone="", address=""):
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        
entries=[AddressBookEntry("Robert Gravina", "robert@gravina.com", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"), 
         AddressBookEntry("Guido van Rossum", "guido@python.org", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Robert Gravina", "robert@gravina.com", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"), 
         AddressBookEntry("Guido van Rossum", "guido@python.org", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Robert Gravina", "robert@gravina.com", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"), 
         AddressBookEntry("Guido van Rossum", "guido@python.org", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org", "090 1234 5678", "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Robert Gravina", "robert@gravina.com", "090 1234 5678", "123 Sample St.\nSample City\nSample Country")]

class AddressBookFrame(sc.SizedFrame):
    def __init__(self, parent, entries):
        sc.SizedFrame.__init__(self, parent,  wx.ID_ANY, "Address Book")
        self.entries = entries

        #required by SizedControls - add controls to this panel, not the frame itself
        mainPanel = self.GetContentsPane()

        #left panel - list of address book entries
        listPanel = sc.SizedPanel(mainPanel)
        listPanel.SetSizerType("horizontal")
        self.list = wx.ListBox(listPanel, choices=[entry.name for entry in entries], size=(170, 180))
        self.list.Bind(wx.EVT_LISTBOX, self.onListBoxSelect)

        #right panel - address book entry form
        rightPanel = sc.SizedPanel(listPanel)
        rightPanel.SetSizerType("form")
        
        wx.StaticText(rightPanel, label="Name")
        self.name = wx.TextCtrl(rightPanel, size=(160,-1))
        wx.StaticText(rightPanel, label="Email")
        self.email = wx.TextCtrl(rightPanel, size=(160,-1))
        wx.StaticText(rightPanel, label="Phone")
        self.phone =  wx.TextCtrl(rightPanel, size=(160,-1))
        wx.StaticText(rightPanel, label="Address")
        self.address =  wx.TextCtrl(rightPanel, size=(160,-1), style=wx.TE_MULTILINE)

        #buttons
        buttonPanel = sc.SizedPanel(mainPanel)
        buttonPanel.SetSizerType("horizontal")

        self.addButton = wx.Button(buttonPanel, label="+")
        self.addButton.Bind(wx.EVT_BUTTON, self.onAddButton)
        self.deleteButton = wx.Button(buttonPanel, label="-")
        self.deleteButton.Bind(wx.EVT_BUTTON, self.onDeleteButton)
        self.saveButton = wx.Button(buttonPanel, label="Save")
        self.saveButton.SetDefault()
        self.saveButton.Bind(wx.EVT_BUTTON, self.onSave)
        
        self.statusBar = wx.StatusBar(self)
        self.statusBar.SetFieldsCount(1)
        self.statusBar.SetStatusText("%d entries" % len(entries), 0)
        self.SetStatusBar(self.statusBar)

        self.Fit()
        self.Show(True)

    def onListBoxSelect(self, event):
        index = event.GetSelection()
        self.name.SetValue(self.entries[index].name)
        self.email.SetValue(self.entries[index].email)
        self.phone.SetValue(self.entries[index].phone)
        self.address.SetValue(self.entries[index].address)
    
    def onSave(self, event):
        index = self.list.GetSelection()
        self.entries[index].name = self.name.GetValue()
        self.entries[index].email = self.email.GetValue()
        self.entries[index].phone = self.phone.GetValue()
        self.entries[index].address = self.address.GetValue()
        self.list.SetString(index, self.name.GetValue())
    
    def onAddButton(self, event):
        entries.append(AddressBookEntry("", ""))
        self.list.Append("")
        self.list.Select(len(entries)-1)
        self.clearControls()
    
    def onDeleteButton(self, event):
        index = self.list.GetSelection()
        del self.entries[index]
        self.list.Delete(index)
        self.clearControls()
    
    def clearControls(self):
        self.name.SetValue("")
        self.email.SetValue("")
        self.phone.SetValue("")
        self.address.SetValue("")

if __name__ == '__main__':
    app = wx.PySimpleApp()
    addressBook = AddressBookFrame(None, entries)
    app.MainLoop()
