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
import os
import logging
import sys
import pytest
import struct
sys.path.insert(0, ".")

from ccputils import Utils

def teardown_function(function):
    logging.shutdown()
    reload(logging)

def test_SetupLogging():
    testLogFile = '/tmp/testccp.log'
    assert os.path.exists(testLogFile) == False
    assert Utils.SetupLogging(testLogFile) == True
    logging.error('test_setupLogging error test')
    assert os.path.exists(testLogFile) == True
    os.unlink(testLogFile)

def test_SetupLoggingDefault():
    testLogFile = '/tmp/testccp.log'
    assert os.path.exists(testLogFile) == False
    Utils.logpath = testLogFile
    assert Utils.SetupLogging() == True
    logging.error('test_setupLogging error test')
    assert os.path.exists(testLogFile) == True
    os.unlink(testLogFile)

def test_SetupLoggingFails():
    testLogFile = '/tmp/dirthatdoesntexist/testccp.log'
    assert os.path.exists(testLogFile) == False
    assert Utils.SetupLogging(testLogFile) == False
    assert os.path.exists(testLogFile) == False

def test_fileIsPDFFails():
    assert Utils.fileIsPDF('testing/testfiles/NotPdf.txt') == False

def test_fileIsPDFSucceeds():
    assert Utils.fileIsPDF('testing/testfiles/Test Page.pdf') == True

def test_fileIsPDFErrors():
    assert Utils.fileIsPDF("-dsadsa") == False

def test_whichFails():
    assert Utils.which('dsaph9oaghd9ahdsadsadsadsadasd') is None

def test_whichSucceeds():
    assert Utils.which(
        'bash') in (
        '/bin/bash',
        '/usr/bin/bash',
        '/usr/sbin/bash')

def test_isExeSucceeds():
    if os.path.exists('/usr/bin/sh'):
        assert Utils.is_exe("/usr/bin/sh") == True
    else:
        assert Utils.is_exe("/bin/sh") == True


def test_isExeFails():
    assert Utils.is_exe("/dev/null") == False


def test_getLPID():
    assert int(Utils.GetLPID()) > 0
    assert Utils.GetLPID() is not None

    import grp

    workingPrintGroupName = 'lp'
    try:
        grp.getgrnam(workingPrintGroupName)
    except:
        workingPrintGroupName = 'cups'
        pass

    assert Utils.GetLPID('brokendefault', 'brokenalternative', False) is None
    assert int(
        Utils.GetLPID(
            'brokendefault',
            workingPrintGroupName,
            False)) > 0
    assert Utils.GetLPID(
        'brokendefault',
        workingPrintGroupName,
        False) is not None

    # test blacklist works
    assert Utils.GetLPID(
        workingPrintGroupName,
        'brokenalternative',
        True,
        [workingPrintGroupName,
         'brokendefault',
         'adm',
         'wheel',
         'root'],
        True) is None

def test_showVersion():
    assert Utils.ShowVersion("12345") == False
    sys.argv = ['testfile', 'version']
    with pytest.raises(SystemExit):
        Utils.ShowVersion("12345")

def test_readFile():
    Utils.WriteFile('/tmp/testfile', 'data')
    assert Utils.ReadFile('/tmp/testfile') == 'data'
    assert Utils.ReadFile('/tmp/filethatdoesntexist') is None
    os.unlink('/tmp/testfile')

def test_writeFile():
    Utils.WriteFile('/tmp/testfile', 'data') == True
    Utils.WriteFile('/tmp/testfile/dsadsaasd', 'data') == False
    os.unlink('/tmp/testfile')

def test_base64encode():
    Utils.WriteFile('/tmp/testfile', 'data') == True
    assert Utils.Base64Encode('/tmp/testfile') == 'data:application/octet-stream;base64,ZGF0YQ=='
    assert os.path.exists('/tmp/testfile.b64') == False
    assert Utils.Base64Encode('/tmp/testfile/dsiahdisa') is None

def test_GetLanguage():
    assert Utils.GetLanguage(['en_GB',]) == "en"
    assert Utils.GetLanguage(['en_US',]) == "en"
    assert Utils.GetLanguage(['fr_CA',]) == "fr"
    assert Utils.GetLanguage(['fr_FR',]) == "fr"
    assert Utils.GetLanguage(['it_IT',]) == "it"
    assert Utils.GetLanguage(['en',]) == "en"
    assert Utils.GetLanguage([None,None]) == "en"
    
def test_GetDefaultPaperType():
    assert Utils.GetDefaultPaperType(['en_GB',]) == "A4"
    assert Utils.GetDefaultPaperType(['en_US',]) == "Letter"
    assert Utils.GetDefaultPaperType([None,None]) == "Letter"

def test_GetWindowSize():
    # expect this to fail gracefully if no tty
    assert Utils.GetWindowSize() == None

    # pass in dummy winsize struct
    dummywinsize = struct.pack('HHHH', 800, 600, 0, 0)
    assert Utils.GetWindowSize(dummywinsize) == (800,600)

    # ensure window size of 0x0 returns none
    dummywinsize = struct.pack('HHHH', 0, 0, 0, 0)
    assert Utils.GetWindowSize(dummywinsize) == None
