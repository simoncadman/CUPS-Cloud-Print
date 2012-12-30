#! /usr/bin/env python2
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

from printer import Printer
import json, urllib, cups

class MockRequestor:
    
    account = None
    printers = []
    
    def setAccount ( self, account ):
        """Sets the account name

        Args:
        filename: string, name of the account
        """
        self.account = account
    
    def getAccount ( self ):
        """Gets the account name

        Return:
        string: Account name.
        """
        return self.account
    
    def mockSearch ( self, path, headers, data , boundary ) :
        result = { 'printers' : self.printers }
        return json.dumps( result )
        
    def doRequest ( self, path, headers = None, data = None , boundary = None ):
        if ( path.startswith('search?') ) :
            return json.loads(self.mockSearch(path, headers, data, boundary))
        return None

global requestors, printerItem

def setup_function(function):
    # setup mock requestors
    global requestors
    requestors = []
    
    # account without special chars
    mockRequestorInstance1 = MockRequestor()
    mockRequestorInstance1.setAccount('testaccount1')
    mockRequestorInstance1.printers = []
    requestors.append(mockRequestorInstance1)
    
    # with @ symbol
    mockRequestorInstance2 = MockRequestor()
    mockRequestorInstance2.setAccount('testaccount2@gmail.com')
    mockRequestorInstance2.printers = [ { 'name' : 'Save to Google Drive', 'id' : '__google__docs' },  ]
    requestors.append(mockRequestorInstance2)
    
    # 1 letter
    mockRequestorInstance3 = MockRequestor()
    mockRequestorInstance3.setAccount('t')
    mockRequestorInstance3.printers = []
    requestors.append(mockRequestorInstance3)
    
    # instantiate printer item
    if function != test_instantiate:
        test_instantiate()

def teardown_function(function):
    global requestors
    requestors = None

def test_instantiate():
    global requestors, printerItem
    # verify adding single requestor works
    printerItem = Printer(requestors[0])
    assert printerItem.requestors[0] == requestors[0]
    assert len(printerItem.requestors) == 1
    
    # verify adding whole array of requestors works
    printerItem = Printer(requestors)
    assert printerItem.requestors == requestors
    assert len(printerItem.requestors) == len(requestors)
    
def test_printers():
    global printerItem, requestors
    
    # test cups connection
    connection = cups.Connection()
    cupsprinters = connection.getPrinters()
    
    # total printer
    totalPrinters = 0
    for requestor in requestors:
        totalPrinters+=len(requestor.printers)
    
    printers = printerItem.getPrinters()
    import re
    assert len(printers) == totalPrinters
    for printer in printers:
        
        # name
        assert isinstance(printer['name'], unicode)
        assert len(printer['name']) > 0
        
        # account
        assert isinstance(printer['account'], str)
        assert len(printer['account']) > 0
        
        # id
        assert isinstance(printer['id'], unicode)
        assert len(printer['id']) > 0
        
        # test encoding and decoding printer details to/from uri
        uritest = re.compile("cloudprint://(.*)/" + urllib.quote( printer['account'] ))
        uri = printerItem.printerNameToUri(printer['account'], printer['name'])
        assert isinstance(uri, str)
        assert len(uri) > 0
        assert uritest.match(uri) != None
        
        printername, account = printerItem.parseURI(uri)
        assert isinstance(printername, str)
        assert urllib.unquote(printername) == printer['name']
        assert isinstance(account, str)
        assert urllib.unquote(account) == printer['account']
        
        printerId, requestor = printerItem.getPrinterIDByURI(uri)
        assert isinstance(printerId, unicode)
        assert isinstance(requestor, MockRequestor)
        
        # test add printer to cups
        testprintername = 'Test-' + urllib.unquote(printername).encode('ascii', 'replace').replace(' ', '_')
        assert printerItem.addPrinter( testprintername, uri, connection) != None
        
        # delete test printer
        connection.deletePrinter( testprintername )