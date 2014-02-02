#! /usr/bin/env python2
#    CUPS Cloudprint - Print via Google Cloud Print                          
#    Copyright (C) 2013 Simon Cadman
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

import sys, os, subprocess, logging

if len(sys.argv) == 2 and sys.argv[1] == 'version':
    # line below is replaced on commit
    CCPVersion = "20140202 222011"
    print "CUPS Cloud Print Issue Reporting Script Version " + CCPVersion
    sys.exit(0)

logpath = '/var/log/cups/cloudprint_log'
try:
    logging.basicConfig(filename=logpath,level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    logging.error("Unable to write to log file "+ logpath)

libpath = "/usr/local/share/cloudprint-cups/"
if not os.path.exists( libpath  ):
    libpath = "/usr/share/cloudprint-cups"
sys.path.insert(0, libpath)

from auth import Auth
from printer import Printer

requestors, storage = Auth.SetupAuth(False)
printer = Printer(requestors)
printers = printer.getPrinters(True)
if printers == None:
    print "ERROR: No Printers Found"
    sys.exit(1)

for foundprinter in printers:
    print '"cupscloudprint:' + foundprinter['account'].encode('ascii', 'replace').replace(' ', '-') +':' + foundprinter['name'].encode('ascii', 'replace').replace(' ', '-') + '.ppd" en "Google" "' + foundprinter['name'].encode('ascii', 'replace') + ' (' + foundprinter['account'] + ')" "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:' + printer.printerNameToUri( foundprinter['account'], foundprinter['name'] ) +';"'
    print ""
    print foundprinter['fulldetails']
    print "\n"
    p = subprocess.Popen([os.path.join(libpath,'dynamicppd.py'), 'cat', 'cupscloudprint:' + foundprinter['account'].encode('ascii', 'replace').replace(' ', '-') +':' + foundprinter['name'].encode('ascii', 'replace').replace(' ', '-') + '.ppd'], stdout=subprocess.PIPE)
    ppddata = p.communicate()[0]
    result = p.returncode
    tempfile = open('/tmp/.ppdfile', 'w')
    tempfile.write(ppddata)
    tempfile.close()
    
    p = subprocess.Popen(['cupstestppd', '/tmp/.ppdfile'], stdout=subprocess.PIPE)
    testdata = p.communicate()[0]
    result = p.returncode
    print "Result of cupstestppd was " + str(result)
    print "".join(testdata)
    if result != 0:
        print "cupstestppd errored: "
        print ppddata
        print "\n"
    
    os.unlink('/tmp/.ppdfile')
    
