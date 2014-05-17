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
import subprocess
import os
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
                                                          'DisplayName' : 'Colors',
                                                          'type': 'Feature',
                                                          'options' : 
                                                           [{'default': True, 'name': 'test'}, {'name': 'test2'}] }]},
                                      {'name': 'Save to Google Drive 2',
                                       'displayName' : 'Save to Google Drive 2 DisplayName',
                                        'id': '__test_save_docs_2' },
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
        
def test_getCapabilitiesItems():
    global printers
    printer = printers[0]
    correctCapabilities = [{'name': 'ns1:Colors', 'DisplayName' : 'Colors', 'type': 'Feature', 'options' : [{'default': True, 'name': 'test'}, {'name': 'test2'}] }]
    assert printer._fields['capabilities'] == correctCapabilities
    assert printer._fields['capabilities'] == printer['capabilities']
    del printer._fields['capabilities']
    assert 'capabilities' not in printer._fields
    assert printer['capabilities'] == correctCapabilities
    assert printer._fields['capabilities'] == printer['capabilities']
    
def test_getCapabilitiesItemsMissing():
    global printers
    printer = printers[1]
    assert 'capabilities' not in printer._fields
    assert printer['capabilities'] == None
    
def test_contains():
    global printers
    for printer in printers:
        assert 'testvalue' not in printer
        printer._fields['testvalue'] = 'test'
        assert 'testvalue' in printer
        del printer._fields['testvalue']
        assert 'testvalue' not in printer

def test_fetchDetails():
    global printers
    assert printers[0]._fetchDetails() == {'name': 'Save to Google Drive', 
                                           'id': '__test_save_docs',
                                            'capabilities': [{'name': 'ns1:Colors',
                                                          'DisplayName' : 'Colors',
                                                          'type': 'Feature',
                                                          'options' : 
                                                           [{'default': True, 'name': 'test'}, {'name': 'test2'}] }]}
    assert printers[1]._fetchDetails() == {'displayName' : 'Save to Google Drive 2 DisplayName', 'id': '__test_save_docs_2', 'name': 'Save to Google Drive 2'}
    
def test_getURI():
    global printers
    assert printers[0].getURI() == "cloudprint://testaccount2%40gmail.com/__test_save_docs"
    assert printers[1].getURI() == "cloudprint://testaccount2%40gmail.com/__test_save_docs_2"
    
def test_getListDescription():
    global printers
    assert printers[0].getListDescription() == "Save to Google Drive - cloudprint://testaccount2%40gmail.com/__test_save_docs - testaccount2@gmail.com"
    assert printers[1].getListDescription() == "Save to Google Drive 2 DisplayName - cloudprint://testaccount2%40gmail.com/__test_save_docs_2 - testaccount2@gmail.com"
    
def test_getBackendDescription():
    global printers
    assert printers[0].getBackendDescription() == 'network cloudprint://testaccount2%40gmail.com/__test_save_docs "Save to Google Drive" "Google Cloud Print" "MFG:Google;MDL:Cloud Print;DES:GoogleCloudPrint;"'
    assert printers[1].getBackendDescription() == 'network cloudprint://testaccount2%40gmail.com/__test_save_docs_2 "Save to Google Drive 2" "Google Cloud Print" "MFG:Google;MDL:Cloud Print;DES:GoogleCloudPrint;"'
    
def test_getCUPSListDescription():
    global printers
    assert printers[0].getCUPSListDescription() == '"cupscloudprint:testaccount2@gmail.com:Save-to-Google-Drive-__test_save_docs.ppd" en "Google" "Save to Google Drive (testaccount2@gmail.com)" "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:cloudprint://testaccount2%40gmail.com/__test_save_docs;"'
    assert printers[1].getCUPSListDescription() == '"cupscloudprint:testaccount2@gmail.com:Save-to-Google-Drive-2-__test_save_docs_2.ppd" en "Google" "Save to Google Drive 2 (testaccount2@gmail.com)" "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:cloudprint://testaccount2%40gmail.com/__test_save_docs_2;"'
    
def test_getPPDName():
    global printers
    assert printers[0].getPPDName() == "cupscloudprint:testaccount2@gmail.com:Save-to-Google-Drive-__test_save_docs.ppd"
    assert printers[1].getPPDName() == "cupscloudprint:testaccount2@gmail.com:Save-to-Google-Drive-2-__test_save_docs_2.ppd"
    
def test_generatePPD():
    global printers
    for printer in printers:
        ppddata = printer.generatePPD()
        assert isinstance(ppddata,str)
        
        # test ppd data is valid
        tempfile = open('/tmp/.ppdfile', 'w')
        tempfile.write(ppddata)
        tempfile.close()
        
        p = subprocess.Popen(['cupstestppd', '/tmp/.ppdfile'], stdout=subprocess.PIPE)
        testdata = p.communicate()[0]
        os.unlink('/tmp/.ppdfile')
        assert p.returncode == 0
    
def test_sanitizeText():
    global printers
    assert printers[0]._sanitizeText("") == ""
    assert printers[0]._sanitizeText("TESTSTRING") == "TESTSTRING"
    assert printers[0]._sanitizeText("TEST:; STRING /2") == "TEST___STRING_-2"
    assert printers[0]._sanitizeText("TEST:; STRING /2") == "TEST___STRING_-2"