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
import pytest
sys.path.insert(0, ".")
from printermanager import PrinterManager
from mockrequestor import MockRequestor
from ccputils import Utils

global printers, printerManagerInstance

testCapabilities1 = [{'name': 'ns1:Colors',
                      'displayName' : 'Colors',
                      'type': 'Feature',
                      'options' : 
                      [{'default': True, 'name': 'test', 'displayName' : 'testdisplay'}, {'name': 'test2'}] },
                     {'name': 'ns1:Size',
                      'psk:DisplayName' : 'Size',
                      'type': 'Feature',
                      'options' : 
                      [{'default': True, 'name': 'big', 'psk:DisplayName' : 'testdisplay big'}, {'name': 'small'}] },
                     {'name': 'ns1:Something',
                      'type': 'Feature',
                      'options' : 
                      [{'default': True, 'name': 'one'}, {'name': 'two', 'ppd:value' : 'testval'}] },
                     {'name': 'ns1:TestReservedWord',
                      'type': 'Feature',
                      'options' : 
                      [{'default': True, 'name': 'Resolution'}, {'name': 'two', 'ppd:value' : 'testval'}] },
                     {'name': 'ns1:TestReservedWord',
                      'type': 'Feature',
                      'options' : 
                      [{'default': True, 'name': 'Resolution'}, {'name': 'two', 'ppd:value' : 'testval'}] },
                     {'name': 'ns1:TestReservedWord',
                      'type': 'Feature',
                      'options' : 
                      [{'default': True, 'name': 'Resolution'}, {'name': 'two', 'ppd:value' : 'testval'}] }]

def setup_function(function):
    # setup mock requestors
    global printers, printerManagerInstance

    mockRequestorInstance = MockRequestor()
    mockRequestorInstance.setAccount('testaccount2@gmail.com')
    mockRequestorInstance.printers = [{'name': 'Save to Google Drive',
                                        'id': '__test_save_docs',
                                        'capabilities': testCapabilities1},
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
    correctCapabilities = testCapabilities1
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
                                            'capabilities': testCapabilities1}
    assert printers[1]._fetchDetails() == {'displayName' : 'Save to Google Drive 2 DisplayName', 'id': '__test_save_docs_2', 'name': 'Save to Google Drive 2'}
    
def test_getURI():
    global printers
    assert printers[0].getURI() == Utils._PROTOCOL + "testaccount2%40gmail.com/__test_save_docs"
    assert printers[1].getURI() == Utils._PROTOCOL + "testaccount2%40gmail.com/__test_save_docs_2"
    
def test_getDisplayName():
    global printers
    assert printers[0].getDisplayName() == "Save to Google Drive"
    assert printers[1].getDisplayName() == "Save to Google Drive 2 DisplayName"
    
def test_getListDescription():
    global printers
    assert printers[0].getListDescription() == "Save to Google Drive - " + Utils._PROTOCOL + "testaccount2%40gmail.com/__test_save_docs - testaccount2@gmail.com"
    assert printers[1].getListDescription() == "Save to Google Drive 2 DisplayName - " + Utils._PROTOCOL + "testaccount2%40gmail.com/__test_save_docs_2 - testaccount2@gmail.com"

def test_getLocation():
    global printers
    assert printers[0].getLocation() == ''
    printers[0]._fields['tags'] = ['novalue','name=value','location=test-location']
    assert printers[0].getLocation() == 'test-location'
    
def test_getCUPSBackendDescription():
    global printers
    assert printers[0].getCUPSBackendDescription() == 'network ' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs "Save to Google Drive" "Save to Google Drive" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs"'
    assert printers[1].getCUPSBackendDescription() == 'network ' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs_2 "Save to Google Drive 2 DisplayName" "Save to Google Drive 2 DisplayName" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs_2"'
    printers[0]._fields['tags'] = ['novalue','name=value','location=test-location']
    assert printers[0].getCUPSBackendDescription() == 'network ' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs "Save to Google Drive" "Save to Google Drive @ test-location" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs" "test-location"'
    
def test_getCUPSDriverDescription():
    global printers
    assert printers[0].getCUPSDriverDescription() == '"cupscloudprint:testaccount2%40gmail.com:__test_save_docs.ppd" en "Google" "Save to Google Drive (testaccount2@gmail.com)" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs"'
    assert printers[1].getCUPSDriverDescription() == '"cupscloudprint:testaccount2%40gmail.com:__test_save_docs_2.ppd" en "Google" "Save to Google Drive 2 DisplayName (testaccount2@gmail.com)" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs_2"'
    
def test_getPPDName():
    global printers
    assert printers[0].getPPDName() == "cupscloudprint:testaccount2%40gmail.com:__test_save_docs.ppd"
    assert printers[1].getPPDName() == "cupscloudprint:testaccount2%40gmail.com:__test_save_docs_2.ppd"
    
def test_generatePPD():
    global printers
    for printer in printers:
        ppddata = printer.generatePPD()
        assert isinstance(ppddata,basestring)
        
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
    for checkReserved in [False,True]:
        assert printers[0]._sanitizeText("",checkReserved) == ""
        assert printers[0]._sanitizeText("TESTSTRING",checkReserved) == "TESTSTRING"
        assert printers[0]._sanitizeText("TEST:; STRING /2",checkReserved) == "TEST___STRING_-2"
        assert printers[0]._sanitizeText("TEST:; STRING /2",checkReserved) == "TEST___STRING_-2"
    
    assert printers[0]._sanitizeText("Duplex") == "Duplex"
    assert printers[0]._sanitizeText("Duplex",True) == "GCP_Duplex"
    
def test_getInternalName():
    global printers
    printerItem = printers[0]

    internalCapabilityTests = []
    # load test file and try all those
    for filelineno, line in enumerate(open('testing/testfiles/capabilitylist')):
        internalCapabilityTests.append({'name': line.decode("utf-8")})

    for internalTest in internalCapabilityTests:
        assert printerItem._getInternalName(internalTest, 'capability') not in printerItem._RESERVED_CAPABILITY_WORDS
        assert ':' not in printerItem._getInternalName(internalTest, 'capability')
        assert ' ' not in printerItem._getInternalName(internalTest, 'capability')
        assert len(printerItem._getInternalName(internalTest,'capability')) <= 30
        assert len(printerItem._getInternalName(internalTest,'capability')) >= 1

    for internalTest in internalCapabilityTests:
        for capabilityName in ["psk:JobDuplexAllDocumentsContiguously","other", "psk:PageOrientation"]:
            assert printerItem._getInternalName(internalTest,'option',capabilityName) not in printerItem._RESERVED_CAPABILITY_WORDS
            assert ':' not in printerItem._getInternalName(internalTest,'option',capabilityName)
            assert ' ' not in printerItem._getInternalName(internalTest,'option')
            assert len(printerItem._getInternalName(internalTest,'option',capabilityName)) <= 30
            assert len(printerItem._getInternalName(internalTest,'option',capabilityName)) >= 1
            
def test_encodeMultiPart():
    global printers
    assert isinstance(printers[0]._encodeMultiPart([('test','testvalue')]),basestring)
    assert 'testvalue' in printers[0]._encodeMultiPart([('test','testvalue')])
    assert 'Content-Disposition: form-data; name="test"' in printers[0]._encodeMultiPart([('test','testvalue')])

def test_getOverrideCapabilities():
    global printers
    printerItem = printers[0]
    assert printerItem._getOverrideCapabilities("") == {}
    assert printerItem._getOverrideCapabilities("landscape") == {'Orientation': 'Landscape'}
    assert printerItem._getOverrideCapabilities("nolandscape") == {'Orientation': 'Landscape'}
    assert printerItem._getOverrideCapabilities("test=one") == {'test': 'one'}
    assert printerItem._getOverrideCapabilities("test=one anothertest=two") == {'test': 'one','anothertest': 'two'}
    assert printerItem._getOverrideCapabilities("test=one anothertest=two Orientation=yes") == {'test': 'one','anothertest': 'two'}
    
def test_GetCapabilitiesDict():
    global printers
    printerItem = printers[0]
    assert printerItem._getCapabilitiesDict({},{},{}) == {"capabilities": []}
    assert printerItem._getCapabilitiesDict([{'name': 'test'}],{},{}) == {"capabilities": []}
    assert printerItem._getCapabilitiesDict([{'name': 'Default' + 'test', 'value': 'test'}],[{'name': printerItem._getInternalName({'name': "test"}, 'capability'),'value': printerItem._getInternalName({'name': "test123"},
                                              'option', printerItem._getInternalName({'name': "Defaulttest"}, 'capability'), []),
                                              'options': [{'name': 'test'}, {'name': 'test2'}]}], {}) == {'capabilities': [{'name': 'test', 'options': [{'name': 'test'}], 'type': 'Feature'}]}
    assert printerItem._getCapabilitiesDict([{'name': 'Default' + 'test', 'value': 'test'}],
                                            [{'name': printerItem._getInternalName({'name': "test"}, 'capability'),
                                             'value': printerItem._getInternalName({'name': "test123"},
                                             'option', printerItem._getInternalName({'name': "Defaulttest"}, 'capability'), []),
                                             'options': [{'name': 'test'}, {'name': 'test2'}]}], {'test': 'test2'}) == {'capabilities': [{'name': 'test', 'options': [{'name': 'test2'}], 'type': 'Feature'}]}

def test_attrListToArray():
    global printers
    assert len(list(printers[0]._attrListToArray({}))) == 0

def test_getCapabilities():
    global printers, printerManagerInstance
    printer = printers[0]
    connection = cups.Connection()
    
    # get test ppd
    ppdid = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()
    
    assert printerManagerInstance.addPrinter(
        printer['name'],
        printer,
        connection,
        printerppdname) is not None
    emptyoptions = printer._getCapabilities(printerManagerInstance.sanitizePrinterName(printer['name']),"landscape")
    assert isinstance(emptyoptions, dict)
    assert isinstance(emptyoptions['capabilities'], list)
    assert len(emptyoptions['capabilities']) == 0
    connection.deletePrinter(printerManagerInstance.sanitizePrinterName(printer['name']))
    
def test_submitJob():
    global printers, printerManagerInstance
    printer = printers[0]
    connection = cups.Connection()
    testprintername = printerManagerInstance.sanitizePrinterName(printer['name'])
    
    # get test ppd
    ppdid = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()
    
    assert printerManagerInstance.addPrinter(
        printer['name'],
        printer,
        connection,
        printerppdname) is not None
    
    # test submitting job
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        'Test Page',
        testprintername) == True
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page Doesnt Exist.pdf',
        'Test Page',
        testprintername) == False
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page Corrupt.pdf',
        'Test Page',
        testprintername, 'landscape') == False

    # test submitting job with rotate
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        'Test Page',
        testprintername,
        "landscape") == True
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        'Test Page',
        testprintername,
        "nolandscape") == True

    # test submitting job with no name
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        '',
        testprintername) == True
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page Doesnt Exist.pdf',
        '',
        testprintername) == False

    # png
    assert printer.submitJob(
        'png',
        'testing/testfiles/Test Page.png',
        'Test Page',
        testprintername) == True
    assert printer.submitJob(
        'png',
        'testing/testfiles/Test Page Doesnt Exist.png',
        'Test Page',
        testprintername) == False

    # ps
    assert printer.submitJob(
        'ps',
        'testing/testfiles/Test Page.ps',
        'Test Page',
        testprintername) == False
    assert printer.submitJob(
        'ps',
        'testing/testfiles/Test Page Doesnt Exist.ps',
        'Test Page',
        testprintername) == False

    # test failure of print job
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        'FAIL PAGE',
        testprintername) == False

    # test failure of print job with exception
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        'TEST PAGE WITH EXCEPTION',
        testprintername) == False

    # delete test printer
    connection.deletePrinter(testprintername)
    
@pytest.mark.skipif(
    os.getuid() == 0,
    reason="will only pass if running tests as non-root user")
def test_submitJobFileCreationFails():
    global printers, printerManagerInstance
    printer = printers[0]
    connection = cups.Connection()
    testprintername = printerManagerInstance.sanitizePrinterName(printer['name'])
    
    # get test ppd
    ppdid = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()
    
    assert printerManagerInstance.addPrinter(
        printer['name'],
        printer,
        connection,
        printerppdname) is not None
    
    # test failure of print job because b64 version of file exists
    Utils.WriteFile('testing/testfiles/Test Page.pdf.b64', 'test')
    os.chmod('testing/testfiles/Test Page.pdf.b64',0)
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        'Test Page',
        testprintername) == False
    os.unlink('testing/testfiles/Test Page.pdf.b64')
    
    # delete test printer
    connection.deletePrinter(testprintername)
