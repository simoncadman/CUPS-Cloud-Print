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
from test_mockrequestor import MockRequestor
import cups, urllib

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
    mockRequestorInstance2.printers = [ { 'name' : 'Save to Google Drive', 'id' : '__google__docs', 'capabilities' : [{ 'name' : 'ns1:Colors', 'type' : 'Feature' }] },  ]
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
    
def test_GetPrinterIDByURIFails (  ):
    global printerItem, requestors
    
    # ensure invalid account returns None/None
    printerIdNoneTest , requestorNoneTest = printerItem.getPrinterIDByURI('cloudprint://testprinter/accountthatdoesntexist')
    assert printerIdNoneTest == None
    assert requestorNoneTest == None
    
    # ensure invalid printer on valid account returns None/None
    printerIdNoneTest , requestorNoneTest = printerItem.getPrinterIDByURI('cloudprint://testprinter/' + urllib.quote(requestors[0].getAccount()) )
    assert printerIdNoneTest == None
    assert requestorNoneTest == None

def test_addPrinterFails ( ) :
    global printerItem
    assert printerItem.addPrinter( '', '', '' ) == False

def test_findPrinterFails ( ) :
    global printerItem
    printerItem.requestor = requestors[0]
    assert printerItem.getPrinterDetails('dsah-sdhjsda-sd') == None

def test_invalidRequest ( ) :
    testMock = MockRequestor()
    assert testMock.doRequest('thisrequestisinvalid') == None

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
        assert printerItem.addPrinter( printername, uri, connection) != None
        testprintername = printerItem.sanitizePrinterName(printername)
        
        # test printer actually added to cups
        cupsPrinters = connection.getPrinters()
        found = False
        for cupsPrinter in cupsPrinters:
            if ( cupsPrinters[cupsPrinter]['printer-info'] == testprintername ):
                found = True
                break
        
        assert found == True
        
        # get details about printer
        printerItem.requestor = requestor
        printerdetails = printerItem.getPrinterDetails(printer['id'])
        assert printerdetails != None
        assert printerdetails['printers'][0] != None
        assert 'capabilities' in printerdetails['printers'][0]
        assert isinstance(printerdetails['printers'][0]['capabilities'], list)
        
        # test submitting job
        assert printerItem.submitJob(printerId, 'pdf', 'testfiles/Test Page.pdf', 'Test Page', testprintername ) == True
        assert printerItem.submitJob(printerId, 'pdf', 'testfiles/Test Page Doesnt Exist.pdf', 'Test Page', testprintername ) == False
        
        # png
        assert printerItem.submitJob(printerId, 'png', 'testfiles/Test Page.png', 'Test Page', testprintername ) == True
        assert printerItem.submitJob(printerId, 'png', 'testfiles/Test Page Doesnt Exist.png', 'Test Page', testprintername ) == False
        
        # ps
        assert printerItem.submitJob(printerId, 'ps', 'testfiles/Test Page.ps', 'Test Page', testprintername ) == False
        assert printerItem.submitJob(printerId, 'ps', 'testfiles/Test Page Doesnt Exist.ps', 'Test Page', testprintername ) == False
        
        # test failure of print job
        assert printerItem.submitJob(printerId, 'pdf', 'testfiles/Test Page.pdf', 'FAIL PAGE', testprintername ) == False
        
        # delete test printer
        connection.deletePrinter( testprintername )