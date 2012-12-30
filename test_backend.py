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

import backend

def test_fileIsPDFFails():
    assert backend.fileIsPDF('testfiles/NotPdf.txt') == False
    
def test_fileIsPDFSucceeds():
    assert backend.fileIsPDF('testfiles/Test Page.pdf') == True
    
def test_whichFails():
    assert backend.which('dsaph9oaghd9ahdsadsadsadsadasd') == None
    
def test_whichSuceeds():
    assert backend.which('bash') == '/bin/bash'

def test_backendDescription():
    import re
    backendtest = re.compile("^\w+ \w+ \"\w+\" \".+\"$")
    description = backend.getBackendDescription()
    assert isinstance(description, str)
    assert description.startswith('network')
    assert backendtest.match(description) != None