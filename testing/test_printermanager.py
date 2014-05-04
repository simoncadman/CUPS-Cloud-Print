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

global requestors, printerManagerInstance


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
    mockRequestorInstance2.printers = [{'name': 'Save to Google Drive',
                                        'id': '__test_save_docs',
                                        'capabilities': [{'name': 'ns1:Colors',
                                                          'type': 'Feature'}]},
                                       ]
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
    logging.shutdown()
    reload(logging)

def test_parseURI():
    global printerManagerInstance, requestors
    printerid = printerManagerInstance._getPrinterIdFromURI(
        "cloudprint://testaccount2%40gmail.com/testid")
    assert printerid == "testid"

def test_parseLegacyURI():
    global printerManagerInstance, requestors

    # 20140210 format
    account, printername, printerid, formatid = printerManagerInstance.parseLegacyURI(
        "cloudprint://printername/testaccount2%40gmail.com/", requestors)
    assert formatid == printerManagerInstance.URIFormat20140210
    assert account == "testaccount2@gmail.com"
    assert printername == "printername"
    assert printerid is None

    # 20140307 format
    account, printername, printerid, formatid = printerManagerInstance.parseLegacyURI(
        "cloudprint://printername/testaccount2%40gmail.com/testid", requestors)
    assert formatid == printerManagerInstance.URIFormat20140307
    assert account == "testaccount2@gmail.com"
    assert printername == "printername"
    assert printerid == "testid"

    # 20140308+ format
    account, printername, printerid, formatid = printerManagerInstance.parseLegacyURI(
        "cloudprint://testaccount2%40gmail.com/testid", requestors)
    assert formatid == printerManagerInstance.URIFormatLatest
    assert account == "testaccount2@gmail.com"
    assert printerid == "testid"
    assert printername is None

    printerid, requestor = printerManagerInstance.getPrinterIDByDetails(
        "testaccount2@gmail.com", "printername", "testid")
    assert printerid == "testid"
    assert isinstance(requestor, MockRequestor)
    assert requestor.getAccount() == 'testaccount2@gmail.com'


def test_getCUPSPrintersForAccount():
    global printerManagerInstance, requestors

    foundprinters, connection = printerManagerInstance.getCUPSPrintersForAccount(
        requestors[0].getAccount())
    assert foundprinters == []
    assert isinstance(connection, cups.Connection)

    # total printer
    totalPrinters = 0
    for requestor in requestors:
        totalPrinters += len(requestor.printers)

    fullprintersforaccount = printerManagerInstance.getPrinters(requestors[1].getAccount())
    assert len(fullprintersforaccount) == len(requestors[1].printers)

    fullprinters = printerManagerInstance.getPrinters(True)
    assert len(fullprinters) == totalPrinters

    printers = printerManagerInstance.getPrinters()
    assert len(printers) == totalPrinters
    printer = printers[0]

    # get ppd
    ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()

    # test add printer to cups
    assert printerManagerInstance.addPrinter(
        printer['name'],
        printer.getURI(),
        connection,
        printerppdname) is not None
    foundprinters, newconnection = printerManagerInstance.getCUPSPrintersForAccount(
        requestors[1].getAccount())
    # delete test printer
    connection.deletePrinter(printerManagerInstance.sanitizePrinterName(printer['name']))

    assert isinstance(foundprinters, list)
    assert len(foundprinters) == 1
    assert isinstance(connection, cups.Connection)


def test_instantiate():
    global requestors, printerManagerInstance
    # verify adding single requestor works
    printerManagerInstance = PrinterManager(requestors[0])
    assert printerManagerInstance.requestors[0] == requestors[0]
    assert len(printerManagerInstance.requestors) == 1

    # verify adding whole array of requestors works
    printerManagerInstance = PrinterManager(requestors)
    assert printerManagerInstance.requestors == requestors
    assert len(printerManagerInstance.requestors) == len(requestors)


def test_getOverrideCapabilities():
    global printerManagerInstance, requestors
    assert printerManagerInstance.getOverrideCapabilities("") == {}
    assert printerManagerInstance.getOverrideCapabilities(
        "landscape") == {'Orientation': 'Landscape'}
    assert printerManagerInstance.getOverrideCapabilities(
        "nolandscape") == {'Orientation': 'Landscape'}
    assert printerManagerInstance.getOverrideCapabilities("test=one") == {'test': 'one'}
    assert printerManagerInstance.getOverrideCapabilities(
        "test=one anothertest=two") == {
        'test': 'one',
        'anothertest': 'two'}
    assert printerManagerInstance.getOverrideCapabilities(
        "test=one anothertest=two Orientation=yes") == {
        'test': 'one',
        'anothertest': 'two'}


def test_getCapabilities():
    global printerManagerInstance, requestors
    foundprinters, connection = printerManagerInstance.getCUPSPrintersForAccount(
        requestors[1].getAccount())

    # total printer
    totalPrinters = 0
    for requestor in requestors:
        totalPrinters += len(requestor.printers)

    fullprinters = printerManagerInstance.getPrinters(True)

    printers = printerManagerInstance.getPrinters()
    printer = printers[0]
    uri = printerManagerInstance.printerNameToUri(
        requestors[1].getAccount(),
        printer['id'])
    account, printerid = printerManagerInstance.parseURI(uri)
    printerId = printerManagerInstance._getPrinterIdFromURI(uri)

    # get ppd
    ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()

    # add test printer to cups
    assert printerManagerInstance.addPrinter(
        printer['name'],
        uri,
        connection,
        printerppdname) is not None
    foundprinters, newconnection = printerManagerInstance.getCUPSPrintersForAccount(
        requestors[1].getAccount())

    emptyoptions = printerManagerInstance.getCapabilities(
        printerId,
        printerManagerInstance.sanitizePrinterName(printer['name']),
        "")
    assert isinstance(emptyoptions, dict)
    assert isinstance(emptyoptions['capabilities'], list)
    assert len(emptyoptions['capabilities']) == 0

    # delete test printer
    connection.deletePrinter(printerManagerInstance.sanitizePrinterName(printer['name']))


def test_GetCapabilitiesDict():
    global printerManagerInstance, requestors
    assert printerManagerInstance.getCapabilitiesDict(
        {},
        {},
        {}) == {"capabilities": []}
    assert printerManagerInstance.getCapabilitiesDict(
        [{'name': 'test'}],
        {},
        {}) == {"capabilities": []}
    assert printerManagerInstance.getCapabilitiesDict(
        [{'name': 'Default' + 'test', 'value': 'test'}],
        [{'name': printerManagerInstance.getInternalName({'name': "test"}, 'capability'),
          'value': printerManagerInstance.getInternalName({'name': "test123"},
                                               'option', printerManagerInstance.getInternalName({'name': "Defaulttest"}, 'capability'), []),
          'options': [{'name': 'test'}, {'name': 'test2'}]}], {}) == {'capabilities': [{'name': 'test', 'options': [{'name': 'test'}], 'type': 'Feature'}]}
    assert printerManagerInstance.getCapabilitiesDict(
        [{'name': 'Default' + 'test', 'value': 'test'}],
        [{'name': printerManagerInstance.getInternalName({'name': "test"}, 'capability'),
          'value': printerManagerInstance.getInternalName({'name': "test123"},
                                               'option', printerManagerInstance.getInternalName({'name': "Defaulttest"}, 'capability'), []),
          'options': [{'name': 'test'}, {'name': 'test2'}]}], {'test': 'test2'}) == {'capabilities': [{'name': 'test', 'options': [{'name': 'test2'}], 'type': 'Feature'}]}


def test_GetPrinterIDByURIFails():
    global printerManagerInstance, requestors

    # ensure invalid account returns None/None
    printerIdNoneTest = printerManagerInstance._getPrinterIdFromURI(
        'cloudprint://testprinter/accountthatdoesntexist')
    assert printerIdNoneTest is None

    # ensure invalid printer on valid account returns None/None
    printerIdNoneTest = printerManagerInstance._getPrinterIdFromURI(
        'cloudprint://testprinter/' + urllib.quote(requestors[0].getAccount()))
    assert printerIdNoneTest is None


def test_addPrinterFails():
    global printerManagerInstance
    assert printerManagerInstance.addPrinter('', '', '') == False


def test_findPrinterFails():
    global printerManagerInstance
    printerManagerInstance.requestor = requestors[0]
    assert printerManagerInstance.getPrinterDetails('dsah-sdhjsda-sd') is None


def test_invalidRequest():
    testMock = MockRequestor()
    assert testMock.doRequest('thisrequestisinvalid') is None


def test_internalName():
    global printerManagerInstance

    internalCapabilityTests = []

    # generate test cases for each reserved word
    # for word in printerManagerInstance.reservedCapabilityWords:
    #    internalCapabilityTests.append( { 'name' : word } )

    # load test file and try all those
    for filelineno, line in enumerate(open('testing/testfiles/capabilitylist')):
        internalCapabilityTests.append({'name': line.decode("utf-8")})

    for internalTest in internalCapabilityTests:
        assert printerManagerInstance.getInternalName(
            internalTest,
            'capability') not in printerManagerInstance.reservedCapabilityWords
        assert ':' not in printerManagerInstance.getInternalName(
            internalTest,
            'capability')
        assert ' ' not in printerManagerInstance.getInternalName(
            internalTest,
            'capability')
        assert len(
            printerManagerInstance.getInternalName(
                internalTest,
                'capability')) <= 30
        assert len(
            printerManagerInstance.getInternalName(
                internalTest,
                'capability')) >= 1

    for internalTest in internalCapabilityTests:
        for capabilityName in ["psk:JobDuplexAllDocumentsContiguously", "other", "psk:PageOrientation"]:
            assert printerManagerInstance.getInternalName(
                internalTest,
                'option',
                capabilityName) not in printerManagerInstance.reservedCapabilityWords
            assert ':' not in printerManagerInstance.getInternalName(
                internalTest,
                'option',
                capabilityName)
            assert ' ' not in printerManagerInstance.getInternalName(
                internalTest,
                'option')
            assert len(
                printerManagerInstance.getInternalName(
                    internalTest,
                    'option',
                    capabilityName)) <= 30
            assert len(
                printerManagerInstance.getInternalName(
                    internalTest,
                    'option',
                    capabilityName)) >= 1


def test_printers():
    global printerManagerInstance, requestors

    # test cups connection
    connection = cups.Connection()
    cupsprinters = connection.getPrinters()

    # total printer
    totalPrinters = 0
    for requestor in requestors:
        totalPrinters += len(requestor.printers)

    fullprinters = printerManagerInstance.getPrinters(True)
    assert 'fulldetails' in fullprinters[0]

    printers = printerManagerInstance.getPrinters()
    assert 'fulldetails' not in printers[0]
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
        uritest = re.compile(
            "cloudprint://(.*)/" + urllib.quote(printer['id']))
        uri = printerManagerInstance.printerNameToUri(printer['account'], printer['id'])
        assert isinstance(uri, str) or isinstance(uri, unicode)
        assert len(uri) > 0
        assert uritest.match(uri) is not None

        account, printerid = printerManagerInstance.parseURI(uri)
        assert isinstance(account, str)
        assert urllib.unquote(account) == printer['account']

        printerId = printerManagerInstance._getPrinterIdFromURI(uri)
        assert isinstance(printerId, str)

        # get ppd
        ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:'
        ppds = connection.getPPDs(ppd_device_id=ppdid)
        printerppdname, printerppd = ppds.popitem()

        # test add printer to cups
        assert printerManagerInstance.addPrinter(
            printer['name'],
            uri,
            connection,
            printerppdname) is not None
        testprintername = printerManagerInstance.sanitizePrinterName(printer['name'])

        # test printer actually added to cups
        cupsPrinters = connection.getPrinters()
        found = False
        for cupsPrinter in cupsPrinters:
            if (cupsPrinters[cupsPrinter]['printer-info'] == testprintername):
                found = True
                break

        assert found == True

        # get details about printer
        printerdetails = printerManagerInstance.getPrinterDetails(printer['id'])
        assert printerdetails is not None
        assert printerdetails['printers'][0] is not None
        assert 'capabilities' in printerdetails['printers'][0]
        assert isinstance(printerdetails['printers'][0]['capabilities'], list)

        # test submitting job
        assert printerManagerInstance.submitJob(
            printerId,
            'pdf',
            'testing/testfiles/Test Page.pdf',
            'Test Page',
            testprintername) == True
        assert printerManagerInstance.submitJob(
            printerId,
            'pdf',
            'testing/testfiles/Test Page Doesnt Exist.pdf',
            'Test Page',
            testprintername) == False

        # test submitting job with rotate
        assert printerManagerInstance.submitJob(
            printerId,
            'pdf',
            'testing/testfiles/Test Page.pdf',
            'Test Page',
            testprintername,
            "landscape") == True
        assert printerManagerInstance.submitJob(
            printerId,
            'pdf',
            'testing/testfiles/Test Page.pdf',
            'Test Page',
            testprintername,
            "nolandscape") == True

        # test submitting job with no name
        assert printerManagerInstance.submitJob(
            printerId,
            'pdf',
            'testing/testfiles/Test Page.pdf',
            '',
            testprintername) == True
        assert printerManagerInstance.submitJob(
            printerId,
            'pdf',
            'testing/testfiles/Test Page Doesnt Exist.pdf',
            '',
            testprintername) == False

        # png
        assert printerManagerInstance.submitJob(
            printerId,
            'png',
            'testing/testfiles/Test Page.png',
            'Test Page',
            testprintername) == True
        assert printerManagerInstance.submitJob(
            printerId,
            'png',
            'testing/testfiles/Test Page Doesnt Exist.png',
            'Test Page',
            testprintername) == False

        # ps
        assert printerManagerInstance.submitJob(
            printerId,
            'ps',
            'testing/testfiles/Test Page.ps',
            'Test Page',
            testprintername) == False
        assert printerManagerInstance.submitJob(
            printerId,
            'ps',
            'testing/testfiles/Test Page Doesnt Exist.ps',
            'Test Page',
            testprintername) == False

        # test failure of print job
        assert printerManagerInstance.submitJob(
            printerId,
            'pdf',
            'testing/testfiles/Test Page.pdf',
            'FAIL PAGE',
            testprintername) == False

        # delete test printer
        connection.deletePrinter(testprintername)


def test_backendDescription():
    global printerManagerInstance
    import re
    backendtest = re.compile("^\w+ \w+ \"\w+\" \".+\"$")
    description = printerManagerInstance.getBackendDescription()
    assert isinstance(description, str)
    assert description.startswith('network')
    assert backendtest.match(description) is not None


def test_getListDescription():
    global printerManagerInstance
    assert printerManagerInstance.getListDescription(
        {'name': 'Save to Google Drive',
         'account': 'test',
         'id': '__test_save_docs'}) == 'Save to Google Drive - cloudprint://test/__test_save_docs - test'
    assert printerManagerInstance.getListDescription(
        {'name': 'Save to Google Drive',
         'displayName': 'Save to Google Drive 2',
         'account': 'test',
         'id': '__test_save_docs'}) == 'Save to Google Drive 2 - cloudprint://test/__test_save_docs - test'


def test_getBackendDescriptionForPrinter():
    global printerManagerInstance
    assert printerManagerInstance.getBackendDescriptionForPrinter(
        {'name': 'Save to Google Docs',
         'account': 'test',
         'id': '__test_save_docs'}) == 'network cloudprint://test/__test_save_docs "Save to Google Docs" "Google Cloud Print" "MFG:Google;MDL:Cloud Print;DES:GoogleCloudPrint;"'
