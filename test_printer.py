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

class MockRequestor:
    pass

global requestors

def setup_function(function):
    # setup mock requestors
    global requestors
    requestors = []
    mockRequestorInstance1 = MockRequestor()
    requestors.append(mockRequestorInstance1)
    mockRequestorInstance2 = MockRequestor()
    requestors.append(mockRequestorInstance2)

def teardown_function(function):
    global requestors
    requestors = None

def test_instantiate():
    global requestors
    # verify adding whole array of requestors works
    printerItem = Printer(requestors)
    assert printerItem.requestors == requestors
    assert len(printerItem.requestors) == len(requestors)
    
    # verify adding single requestor works
    printerItem = Printer(requestors[0])
    assert printerItem.requestors[0] == requestors[0]
    assert len(printerItem.requestors) == 1