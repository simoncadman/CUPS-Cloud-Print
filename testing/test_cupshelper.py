# -*- coding: utf-8 -*-
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
from cupshelper import CUPSHelper
from printer import Printer
from cloudprintrequestor import CloudPrintRequestor
from mockcups import MockCUPS
import sys
sys.path.insert(0, ".")

global helperinstance


def setup_function(function):
    # setup mock helper
    global helperinstance
    global mockcups
    mockcups = MockCUPS()
    helperinstance = CUPSHelper(mockcups)


def teardown_function(function):
    # setup mock helper
    global mockcups
    global helperinstance
    mockcups = None
    helperinstance = None


def test_init():
    assert isinstance(helperinstance, CUPSHelper)
    testinstance = CUPSHelper()
    assert isinstance(testinstance, CUPSHelper)


def test_getPrinters():
    global mockcups

    assert isinstance(helperinstance.getPrinters(), dict)
    assert len(helperinstance.getPrinters()) == 0

    # add printer
    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    printerinstance = Printer({'name': 'Testing Printer',
                               'id': '__test_printer',
                               'capabilities': [{'name': 'ns1:Colors',
                                                 'type': 'Feature'}]}, requestor, helperinstance)
    helperinstance.addPrinter(printerinstance, "test")

    # also add dummy instance with non-gcp uri
    mockcups._printers["test-dummy-non-gcp-printer"] = {'printer-is-shared': False,
                                                        'printer-info': "test info",
                                                        'printer-state-message': '',
                                                        'printer-type': 1,
                                                        'printer-state-reasons': ['none'],
                                                        'printer-uri-supported':
                                                            'ipp://localhost/printers/test',
                                                        'printer-state': 3,
                                                        'printer-location': "test location",
                                                        'device-uri': "test://test/test"}

    assert len(mockcups._printers) == 2

    # test count of printers returned has increased by 1
    assert len(helperinstance.getPrinters()) == 1

    for printername in helperinstance.getPrinters():
        assert printername == 'test'
        printer = helperinstance.getPrinters()[printername]
        assert printer['printer-is-shared'] is False
        assert printer['device-uri'] == 'gcp://test/__test_printer'

    # delete printer
    helperinstance.deletePrinter(printerinstance.getURI())

    # test count of printers returned is same as original
    assert len(helperinstance.getPrinters()) == 0


def test_addGetPrinter():
    assert len(helperinstance.getPrinters()) == 0
    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    printerinstance = Printer({'name': 'Testing Printer',
                               'id': '__test_printer',
                               'capabilities': [{'name': 'ns1:Colors',
                                                 'type': 'Feature'}]}, requestor, helperinstance)
    helperinstance.addPrinter(printerinstance, "test")

    printerdetails = helperinstance.getPrinter('gcp://test/__test_printer')
    assert printerdetails['device-uri'] == 'gcp://test/__test_printer'

    assert helperinstance.getPrinter('invalid uri') is None

    assert len(helperinstance.getPrinters()) == 1

    printerinstance2 = Printer({'name': 'Testing Printer 2',
                                        'id': '__test_printer_2',
                                        'capabilities': [{'name': 'ns1:Colors',
                                                          'type': 'Feature'}]},
                               requestor, helperinstance)
    helperinstance.addPrinter(
        printerinstance2, "test2", "test-location", printerinstance.getPPDName())
    printerdetails = helperinstance.getPrinter('gcp://test/__test_printer_2')
    assert printerdetails['device-uri'] == 'gcp://test/__test_printer_2'
    assert printerdetails['printer-location'] == 'test-location'

    assert len(helperinstance.getPrinters()) == 2

    printerinstance3 = Printer({'name': 'Testing Printer 3',
                                        'id': '__test_printer_3',
                                        'capabilities': [{'name': 'ns1:Colors',
                                                          'type': 'Feature'}],
                                        'tags': ['location=Test Location']},
                               requestor, helperinstance)
    helperinstance.addPrinter(printerinstance3, "test3", "")
    printerdetails = helperinstance.getPrinter('gcp://test/__test_printer_3')
    assert printerdetails['device-uri'] == 'gcp://test/__test_printer_3'
    assert printerdetails['printer-location'] == 'Test Location'

    assert len(helperinstance.getPrinters()) == 3

    # ensure coverage of errors
    printerinstance4 = Printer({'name': 'Testing Printer 4',
                                        'id': '__test_printer_4',
                                        'capabilities': [{'name': 'ns1:Colors',
                                                          'type': 'Feature'}],
                                        'tags': ['location=Test Location']},
                               requestor, helperinstance)
    helperinstance.addPrinter(printerinstance4, "test4", MockCUPS())
    assert helperinstance.getPrinter('gcp://test/__test_printer_4') is None

    assert len(helperinstance.getPrinters()) == 3


def test_renamePrinter():
    assert len(helperinstance.getPrinters()) == 0
    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    printerinstance = Printer({'name': 'Testing Printer',
                               'id': '__test_printer',
                               'capabilities': [{'name': 'ns1:Colors',
                                                 'type': 'Feature'}]}, requestor, helperinstance)
    helperinstance.addPrinter(printerinstance, "test")

    helperinstance.renamePrinter('gcp://test/__test_printer', 'Testing Printer 2', 'test location')
    printerdetails = helperinstance.getPrinter('gcp://test/__test_printer')
    assert printerdetails['device-uri'] == 'gcp://test/__test_printer'
    assert printerdetails['printer-info'] == 'Testing Printer 2'
    assert printerdetails['printer-location'] == 'test location'

    assert len(helperinstance.getPrinters()) == 1


def test_deletePrinter():
    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    printerinstance = Printer({'name': 'Testing Printer',
                               'id': '__test_printer',
                               'capabilities': [{'name': 'ns1:Colors',
                                                 'type': 'Feature'}]}, requestor, helperinstance)
    helperinstance.addPrinter(printerinstance, "test")
    helperinstance.deletePrinter("printer that doesnt exist")

    assert len(helperinstance.getPrinters()) == 1

    helperinstance.deletePrinter(printerinstance.getURI())

    assert len(helperinstance.getPrinters()) == 0


def test__getCUPSQueueName():
    assert helperinstance._getCUPSQueueName('test') is None
    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    printerinstance = Printer({'name': 'Testing Printer',
                               'id': '__test_printer',
                               'capabilities': [{'name': 'ns1:Colors',
                                                 'type': 'Feature'}]}, requestor, helperinstance)
    helperinstance.addPrinter(printerinstance, "test")

    assert helperinstance._getCUPSQueueName('gcp://test/__test_printer') == "test"


def test__getCUPSQueueNameAndPrinter():
    assert helperinstance._getCUPSQueueNameAndPrinter('test') is None
    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    printerinstance = Printer({'name': 'Testing Printer',
                               'id': '__test_printer',
                               'capabilities': [{'name': 'ns1:Colors',
                                                 'type': 'Feature'}]}, requestor, helperinstance)
    helperinstance.addPrinter(printerinstance, "test")

    assert helperinstance._getCUPSQueueNameAndPrinter('gcp://test/__test_printer') == \
        ("test", {'device-uri': 'gcp://test/__test_printer',
                  'printer-info': 'test',
                  'printer-is-shared': False,
                  'printer-location': 'Google Cloud Print',
                  'printer-state': 3,
                  'printer-state-message': '',
                  'printer-state-reasons': ['none'],
                  'printer-type': 1,
                  'printer-uri-supported': 'ipp://localhost/printers/test'})


def test_generateCUPSQueueName():
    testdata = {
        'test': 'test-test',
        'test1': 'test1-test',
                'test-1': 'test-1-test',
                'testing test': 'testingtest-test',
                'testing£test': 'testingtest-test',
    }

    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    for teststring in testdata:
        printerinstance = Printer({'name': teststring,
                                   'id': '__test_printer',
                                   'capabilities': [{'name': 'ns1:Colors',
                                                     'type': 'Feature'}]},
                                  requestor, helperinstance)
        assert helperinstance.generateCUPSQueueName(printerinstance) == testdata[teststring]


def test_getServerSetting():
    assert helperinstance.getServerSetting('settingthatshouldntexist') == None
    assert helperinstance.getServerSetting('itemthatdoesexist') == 'GeeR2Ieh6Ok5Aep8Ahha'
