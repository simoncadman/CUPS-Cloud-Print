#! /bin/sh
"true" '''\'
if command -v python2 > /dev/null; then
  exec python2 "$0" "$@"
else
  exec python "$0" "$@"
fi
exit $?
'''

#    CUPS Cloudprint - Print via Google Cloud Print
#    Copyright (C) 2011 Simon Cadman
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from auth import Auth
from ccputils import Utils
from cupshelper import CUPSHelper
from printer import Printer
from printermanager import PrinterManager

import Tkinter
import tkMessageBox
import time
import ttk
import urllib
import webbrowser

class PrinterNameLocationDialog(Tkinter.Toplevel):
    def __init__(self, master, uri, name, location, callback):
        Tkinter.Toplevel.__init__(self, master)
        self.master = master
        self.uri = uri
        self.callback = callback

        self.transient(master) # don't create an icon in the system tray, etc
        self.title('printer name, location')

        ttk.Label(self, text='printer name:').grid(column=0, row=0, sticky='w')
        ttk.Label(self, text='location:').grid(column=0, row=1, sticky='w')
        self.name = ttk.Entry(self)
        self.name.insert(0, name)
        self.name.grid(column=1, row=0)
        self.location = ttk.Entry(self)
        self.location.insert(0, location)
        self.location.grid(column=1, row=1)

        box = ttk.Frame(self)
        ttk.Button(box, text='OK', command=self.ok, default='active').pack(side='left')
        ttk.Button(box, text='Cancel', command=self.cancel).pack(side='left')
        box.grid(column=0, row=2, columnspan=2)

        self.name.focus()
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        self.grab_set()

        self.protocol('WM_DELETE_WINDOW', self.cancel)

        self.wait_window(self)

    def ok(self, *args):
        self.callback(self.uri, self.name.get(), self.location.get())
        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def cancel(self, *args):
        self.master.focus_set()
        self.destroy()

class PrintersTab(ttk.Frame):
    def __init__(self, master, window, **kw):
        ttk.Frame.__init__(self, master, **kw)
        self.window = window

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self,
            columns=('name', 'location'),
            displaycolumns=('name', 'location'),
            height=20,
            selectmode='browse',
            show='headings')

        self.tree.heading('name', text='name', anchor='w')
        self.tree.column('name', width=200, anchor='w')
        self.tree.heading('location', text='location', anchor='w')
        self.tree.column('location', width=300, anchor='w')

        self.tree.grid(column=0, row=0, sticky='nwes', pady=(6,6))

        box = ttk.Frame(self)
        ttk.Button(box, text='rename', command=self._invokeRenameDialog, default='active').pack(
            side='left')
        ttk.Button(box, text='remove', command=self._remove).pack(side='left')
        box.grid(column=0, row=1)

    def _initPrinters(self):
        for printer in self.window.getCUPSHelper().getPrinters().values():
            self.tree.insert('', 'end', printer['device-uri'],
                values=(printer['printer-info'], printer['printer-location']))

    def _clearPrinters(self):
        for child in self.tree.get_children():
            self.tree.delete(child)

    def handleSelected(self):
        self._clearPrinters()
        self._initPrinters()

    def _invokeRenameDialog(self):
        uri = self.tree.focus()
        printer = self.window.getCUPSHelper().getPrinter(uri)
        if printer is not None:
            PrinterNameLocationDialog(self,
                uri, printer['printer-info'], printer['printer-location'], self._rename)

    def _rename(self, uri, name, location):
        self.window.getCUPSHelper().renamePrinter(uri, name, location)
        self.handleSelected() # refresh the UI with new name, location

    def _remove(self):
        uri = self.tree.focus()
        self.window.getCUPSHelper().deletePrinter(uri)
        self.handleSelected() # refresh the UI without the removed printer

class AddPrinterDialogPrinter(object):
    def __init__(self, uri, display_name, location, searchable_str, ccp_printer):
        self.uri = uri
        self.display_name = display_name
        self.location = location
        self.searchable_str = searchable_str
        self.ccp_printer = ccp_printer

    def __cmp__(self, other):
        if self.display_name.lower() < other.display_name.lower():
            return -1
        if self.display_name.lower() > other.display_name.lower():
            return 1
        return cmp(self.location.lower(), other.location.lower())

class AddPrinterTab(ttk.Frame):
    def __init__(self, master, window, **kw):
        ttk.Frame.__init__(self, master, **kw)
        self.window = window

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.tree = ttk.Treeview(self,
            columns=('name', 'location'),
            displaycolumns=('name', 'location'),
            height=20,
            selectmode='browse',
            show='headings')

        self.tree.heading('name', text='name', anchor='w')
        self.tree.column('name', width=200, anchor='w')
        self.tree.heading('location', text='location', anchor='w')
        self.tree.column('location', width=300, anchor='w')

        self.tree.grid(column=0, row=1, columnspan=2, sticky='nwes', pady=(6,6))

        search_label = ttk.Label(self, text='search: ')
        search_label.grid(column=0, row=0, sticky='w')

        self.search = ttk.Entry(self, exportselection=False, validate='key',
            validatecommand=(self.register(self._filterPrinters), '%P'))
        self.search.grid(column=1, row=0, sticky='we')

        self.add_button = ttk.Button(self, text='add this printer', command=self._invokeAddDialog)
        self.add_button.grid(column=1, row=2, sticky='e')

        self.search.bind('<Control-BackSpace>', self._clearQuery)
        self.search.bind('<Return>', self._invokeAddDialog)
        self.tree.bind('<Return>', self._invokeAddDialog)
        self.tree.bind('<Double-1>', self._invokeAddDialog)

        self._initPrinters()

    def _initPrinters(self):
        for p in self.window.getCCPPrinters():
            self.tree.insert('', 'end', p.uri, values=(p.display_name, p.location))
        self._filterPrinters(self.search.get())

    def _clearPrinters(self):
        for child in self.tree.get_children():
            self.tree.delete(child)

    def refreshPrinters(self):
        self._clearPrinters()
        self._initPrinters()

    def _clearQuery(self, *args):
        self.search.delete(0, 'end')

    def _invokeAddDialog(self, *args):
        uri = self.tree.focus()
        for p in self.window.getCCPPrinters():
            if p.uri == uri:
                PrinterNameLocationDialog(self, p.uri, p.display_name, p.location, self._add)
                return

    def _add(self, uri, name, location):
        for p in self.window.getCCPPrinters():
            if p.uri == uri:
                if not self.window.getCUPSHelper().addPrinter(p.ccp_printer, name, location):
                    tkMessageBox.showinfo('failed to add printer', 'failed to add "%s"' % name)
                return

    def _filterPrinters(self, query):
        first_item = None

        if not query:
            for i, p in enumerate(self.window.getCCPPrinters()):
                self.tree.move(p.uri, '', i)
                if i == 0:
                    first_item = p.uri

        else:
            i = 0
            for p in self.window.getCCPPrinters():
                if query in p.searchable_str:
                    self.tree.move(p.uri, '', i)
                    if i == 0:
                        first_item = p.uri
                    i += 1
                else:
                    self.tree.detach(p.uri)

        if first_item:
            self.tree.selection_set((first_item,))
            self.tree.focus(first_item)

        return True

    def handleSelected(self):
        self.search.focus()

class NewAccountDialogStep1(Tkinter.Toplevel):
    def __init__(self, master, callback):
        Tkinter.Toplevel.__init__(self, master)
        self.master = master
        self.callback = callback

        self.transient(master) # don't create an icon in the system tray, etc
        self.title('new account, step 1')

        box = ttk.Frame(self)
        ttk.Label(box, text='account name (eg something@gmail.com): ').pack(side='left')
        self.account_name = ttk.Entry(box)
        self.account_name.pack(side='left')
        box.grid(column=0, row=0)

        box2 = ttk.Frame(self)
        ttk.Button(box2, text='OK', command=self.ok).pack(side='left')
        ttk.Button(box2, text='Cancel', command=self.cancel).pack(side='left')
        box2.grid(column=0, row=1)

        self.account_name.focus()
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        self.grab_set()

        self.protocol('WM_DELETE_WINDOW', self.cancel)

        self.wait_window(self)

    def ok(self, *args):
        self.callback(self.account_name.get())
        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def cancel(self, *args):
        self.master.focus_set()
        self.destroy()

class NewAccountDialogStep2(Tkinter.Toplevel):
    def __init__(self, master, account_name, flow, auth_uri, callback):
        Tkinter.Toplevel.__init__(self, master)
        self.master = master
        self.account_name = account_name
        self.flow = flow
        self.auth_uri = auth_uri
        self.callback = callback

        self.transient(master) # don't create an icon in the system tray, etc
        self.title('new account, step 2')

        message = 'Visit this URL to grant printer access to CUPS Cloud Print'
        ttk.Label(self, text=message).grid(column=0, row=0)
        uri_text = Tkinter.Text(self, width=100, height=3)
        uri_text.insert('insert', auth_uri)
        uri_text.tag_add('sel', '1.0', 'end')
        uri_text.grid(column=0, row=1)
        uri_text.focus()

        box = ttk.Frame(self)
        ttk.Button(box, text='copy URL to clipboard', command=self._copyToClipboard).pack(
            side='left')
        ttk.Button(box, text='open URL in web browser', command=self._openUriInBrowser).pack(
            side='left')
        box.grid(column=0, row=2)

        message2 = 'Google gives you a code, paste it here'
        ttk.Label(self, text=message2).grid(column=0, row=3)

        self.code_entry = ttk.Entry(self, width=60)
        self.code_entry.grid(column=0, row=4)

        box2 = ttk.Frame(self)
        ttk.Button(box2, text='OK', command=self.ok).pack(side='left')
        ttk.Button(box2, text='Cancel', command=self.cancel).pack(side='left')
        box2.grid(column=0, row=5)

        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        self.grab_set()

        self.protocol('WM_DELETE_WINDOW', self.cancel)

        self.wait_window(self)

    def _copyToClipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.auth_uri)

    def _openUriInBrowser(self):
        webbrowser.open_new_tab(self.auth_uri)

    def ok(self, *args):
        code = self.code_entry.get()
        if not code:
            return

        self.callback(self.account_name, self.flow, code)
        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def cancel(self, *args):
        self.master.focus_set()
        self.destroy()

class AccountsTab(ttk.Frame):
    def __init__(self, master, window, **kw):
        ttk.Frame.__init__(self, master, **kw)
        self.window = window

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self,
            columns=('account',),
            displaycolumns=('account',),
            height=20,
            selectmode='browse',
            show='headings')

        self.tree.heading('account', text='account name', anchor='w')
        self.tree.column('account', width=200, anchor='w')

        self.tree.grid(column=0, row=0, sticky='nwes', pady=(6,6))

        box = ttk.Frame(self)
        self.add_button = ttk.Button(box, text='add an account', command=self._showStep1)
        self.add_button.pack(side='left')
        self.remove_button = ttk.Button(box, text='remove this account', command=self._remove)
        self.remove_button.pack(side='left')
        box.grid(column=0, row=1)

    def _showStep1(self, *args):
        NewAccountDialogStep1(self, self._doStep1)

    def _doStep1(self, account_name):
        flow, auth_uri = Auth.AddAccountStep1(account_name)
        self._showStep2(account_name, flow, auth_uri)

    def _showStep2(self, account_name, flow, auth_uri):
        NewAccountDialogStep2(self, account_name, flow, auth_uri, self._doStep2)

    def _doStep2(self, account_name, flow, code):
        Auth.AddAccountStep2(account_name, flow, code)
        self.handleSelected()
        self.window.resetAccounts()
        self.window.refreshPrinters()

    def _remove(self, *args):
        account_name = self.tree.focus()
        if not account_name:
            return

        #remove printers belonging to the deleted account
        uri_prefix = Utils.PROTOCOL + urllib.quote(account_name.encode('ascii', 'replace')) + '/'
        for cups_printer in self.window.getCUPSHelper().getPrinters().values():
            if cups_printer['device-uri'].startswith(uri_prefix):
                self.window.getCUPSHelper().deletePrinter(cups_printer['device-uri'])

        Auth.DeleteAccount(account_name)
        self.handleSelected()
        self.window.resetAccounts()
        self.window.refreshPrinters()

    def _initAccounts(self):
        self.window.resetAccounts()
        for account_name in Auth.GetAccountNames(self.window.getRequestors()):
            self.tree.insert('', 'end', account_name, values=(account_name,))
        self.add_button.focus()

    def _clearAccounts(self):
        for child in self.tree.get_children():
            self.tree.delete(child)

    def handleSelected(self):
        self._clearAccounts()
        self._initAccounts()

class Window(object):
    def __init__(self):
        self.cups_helper = CUPSHelper()
        self.resetAccounts()

        root = Tkinter.Tk()
        root.title('CUPS Cloud Print')

        notebook = ttk.Notebook(root)
        printers_tab = PrintersTab(notebook, self)
        self._add_printer_tab = AddPrinterTab(notebook, self)
        accounts_tab = AccountsTab(notebook, self)

        self.tabs = (printers_tab, self._add_printer_tab, accounts_tab)
        for tab in self.tabs:
            tab.pack(fill='both', expand=1)

        notebook.add(printers_tab, text='printers')
        notebook.add(self._add_printer_tab, text='add printer')
        notebook.add(accounts_tab, text='accounts')

        notebook.bind_all('<<NotebookTabChanged>>', self._tabChanged)
        notebook.pack(fill='both', expand=1)

        root.mainloop()

    def _tabChanged(self, event):
        self.tabs[event.widget.index('current')].handleSelected()

    def getCUPSHelper(self):
        return self.cups_helper

    def resetAccounts(self):
        self.requestors, self.auth_storage = Auth.SetupAuth(False)
        self._ccp_printers = None

    def refreshPrinters(self):
        self._add_printer_tab.refreshPrinters()

    def getRequestors(self):
        return self.requestors

    def getAuthStorage(self):
        return self.auth_storage

    def getCCPPrinters(self):
        if self._ccp_printers is None:
            td = time.time()
            ccp_printers = []
            for p in PrinterManager(self.getRequestors()).getPrinters():
                ccp_printers.append(AddPrinterDialogPrinter(
                    p.getURI(),
                    p.getDisplayName(),
                    p.getLocation(),
                    '%s %s' % (p.getDisplayName().lower(), p.getLocation().lower()),
                    p))
            td = time.time() - td
            print 'get ccp printers took %.2f seconds' % td
            self._ccp_printers = sorted(ccp_printers)

        return self._ccp_printers

if __name__ == '__main__':
    Utils.SetupLogging()
    Window()

