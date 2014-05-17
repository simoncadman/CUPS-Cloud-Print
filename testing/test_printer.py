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
import cups
import urllib
import logging
import sys
sys.path.insert(0, ".")

from printermanager import PrinterManager
from mockrequestor import MockRequestor

global printers

def setup_function(function):
    # setup mock requestors
    global printers

    mockRequestorInstance = MockRequestor()
    mockRequestorInstance.setAccount('testaccount2@gmail.com')
    mockRequestorInstance.printers = [{'name': 'Save to Google Drive',
                                        'id': '__test_save_docs',
                                        'capabilities': [{'name': 'ns1:Colors',
                                                          'type': 'Feature'}]},
                                       ]
                                        
    printerManagerInstance = PrinterManager(mockRequestorInstance)
    printers = printerManagerInstance.getPrinters()

def teardown_function(function):
    global requestors
    requestors = None
    logging.shutdown()
    reload(logging)

def test_getAccount():
    global printers
    for printer in printers:
        assert printer.getAccount() == "testaccount2@gmail.com"
    
def test_getRequestor():
    global printers
    for printer in printers:
        requestor = printer.getRequestor()
        assert requestor.__class__.__name__ == "MockRequestor"
        assert requestor.getAccount() == 'testaccount2@gmail.com'

def test_getMimeBoundary():
    global printers
    for printer in printers:
        assert printer._getMimeBoundary() != 'test_boundry'
        assert len(printer._getMimeBoundary()) > 30
        assert len(printer._getMimeBoundary()) < 50
        
        printer._mime_boundary = 'test_boundry'
        assert printer._getMimeBoundary() == 'test_boundry'