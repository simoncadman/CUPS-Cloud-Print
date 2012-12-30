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

from auth import Auth
import json, urllib, cups, os
from test_mockrequestor import MockRequestor
from oauth2client import client
from oauth2client import multistore_file

def setup_function(function):
    # setup mock requestors
    global requestors
    requestors = []
    
    # account without special chars
    mockRequestorInstance1 = MockRequestor()
    mockRequestorInstance1.setAccount('testaccount1')
    mockRequestorInstance1.printers = []
    requestors.append(mockRequestorInstance1)
    
    Auth.config = '/tmp/cloudprint.conf'


def teardown_function(function):
    os.unlink('/tmp/cloudprint.conf')

def test_setupAuth():
    # create initial file
    assert os.path.exists('/tmp/cloudprint.conf') == False
    assert Auth.SetupAuth(False) == False
    assert os.path.exists('/tmp/cloudprint.conf') == True
    
    # add dummy details
    storage = multistore_file.get_credential_storage(
        Auth.config,
        Auth.clientid,
        'testuseraccount',
        ['https://www.googleapis.com/auth/cloudprint'])
    
    credentials = client.OAuth2Credentials('test', Auth.clientid,
                               'testsecret', 'testtoken', 1,
                               'https://www.googleapis.com/auth/cloudprint', 'testaccount1')
    storage.put(credentials)
    
    # re-run to test getting credentials
    requestors, storage = Auth.SetupAuth(False)
    assert requestors != None
    assert storage != None
    