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

import sys, cups, subprocess, os, json
from oauth2client import client
from oauth2client import multistore_file
from auth import Auth

if len(sys.argv) == 2 and sys.argv[1] == 'version':
    # line below is replaced on commit
    CCPVersion = "20130914 133422"
    print "CUPS Cloud Print Upgrade Script Version " + CCPVersion
    sys.exit(0)
    
connection = cups.Connection()
cupsprinters = connection.getPrinters()

if os.path.exists(Auth.config):
  try:
    content_file = open(Auth.config, 'r')
    content = content_file.read()
    data = json.loads(content)
  except Exception, e:
    sys.stderr.write("Unable to read config file: " + e.message +"\n\n")
    sys.exit(0)
    
else:
  sys.stderr.write("\n\nRun: /usr/lib/cloudprint-cups/setupcloudprint.py to setup your Google Credentials and add your printers to CUPS\n\n")
  sys.exit(0)
  
for device in cupsprinters:
    try:
        if ( cupsprinters[device]["device-uri"].find("cloudprint://") == 0 ):
            print "Updating " + cupsprinters[device]["printer-info"]
            ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:' + cupsprinters[device]["device-uri"] + ';'
            ppds = connection.getPPDs(ppd_device_id=ppdid)
            printerppdname, printerppd = ppds.popitem()
            p = subprocess.Popen(["lpadmin", "-p", cupsprinters[device]["printer-info"], "-m", printerppdname], stdout=subprocess.PIPE)
            output = p.communicate()[0]
            result = p.returncode
            sys.stderr.write(output)
    except Exception, e:
        sys.stderr.write("Error connecting to CUPS: " + str(e) + "\n")
