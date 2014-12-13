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
    helperinstance = CUPSHelper(MockCUPS())

def test_init():
    global helperinstance
    assert isinstance(helperinstance, CUPSHelper)

def test_getPrinters():
    assert isinstance(helperinstance.getPrinters(), dict)
    assert len(helperinstance.getPrinters()) == 0
    
    # add printer
    requestor = CloudPrintRequestor()
    requestor.setAccount("test")
    printerinstance = Printer({'name': 'Testing Printer',
                                        'id': '__test_printer',
                                        'capabilities': [{'name': 'ns1:Colors',
                                                          'type': 'Feature'}]}, requestor)
    helperinstance.addPrinter(printerinstance, "test")
    
    # test count of printers returned has increased by 1
    assert len(helperinstance.getPrinters()) == 1
    
    for printername in helperinstance.getPrinters():
        assert printername == 'TestingPrinter-test'
        printer = helperinstance.getPrinters()[printername]
        assert printer['printer-is-shared'] == False
        assert printer['device-uri'] == 'gcp://test/__test_printer'
    
    # delete printer
    helperinstance.deletePrinter(printerinstance.getURI())
    
    # test count of printers returned is same as original
    assert len(helperinstance.getPrinters()) == 0