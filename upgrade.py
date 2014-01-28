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

import sys, cups, subprocess, os, json, logging
from oauth2client import client
from oauth2client import multistore_file
from auth import Auth

logpath = '/var/log/cups/cloudprint_log'

try:
    logging.basicConfig(filename=logpath,level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    logging.error("Unable to write to log file "+ logpath)
    
try:
    # fix ownership of log file
    os.chown(logpath, 0, Auth.GetLPID())
    os.chmod(logpath, 0660)
except:
    logging.warning("Failed to change ownerships and permissions of logfile")

if os.path.exists('/usr/local/share/cloudprint-cups'):
    sys.stderr.write("If you are upgrading from version 20131013 or earlier you should be aware that the scripts have moved from /usr/local/lib/cloudprint-cups to /usr/local/share/cloudprint-cups\n")
else:
    sys.stderr.write("If you are upgrading from version 20131013 or earlier you should be aware that the scripts have moved from /usr/lib/cloudprint-cups to /usr/share/cloudprint-cups\n")

# line below is replaced on commit
CCPVersion = "20140128 231217"

if len(sys.argv) == 2 and sys.argv[1] == 'version':
    print "CUPS Cloud Print Upgrade Script Version " + CCPVersion
    sys.exit(0)

logging.info("Upgrading to " + CCPVersion)

try:
    connection = cups.Connection()
except Exception, e:
    sys.stderr.write("Could not connect to CUPS: " + e.message +"\n")
    sys.exit(0)
cupsprinters = connection.getPrinters()

if os.path.exists(Auth.config):
  try:
    os.chmod(Auth.config, 0660)
  except Exception, e:
    logging.error("Unable to fix config file permissions: %s", str(e))
    
  try:
    content_file = open(Auth.config, 'r')
    content = content_file.read()
    data = json.loads(content)
  except Exception, e:
    sys.stderr.write("Unable to read config file: " + e.message +"\n\n")
    sys.exit(0)
    
else:
  sys.stderr.write("\n\nRun: /usr/share/cloudprint-cups/setupcloudprint.py to setup your Google Credentials and add your printers to CUPS\n\n")
  sys.exit(0)
  
from backend import which
if which('lpadmin') == None:
    sys.stderr.write("lpadmin command not found, you may need to run this script as root\n")
    sys.exit(1)
  
try:
    print "Fetching list of available ppds..."
    allppds = connection.getPPDs()
    print "List retrieved successfully"
except Exception, e:
    sys.stderr.write("Error connecting to CUPS: " + str(e) + "\n")
    sys.exit(1)
    
for device in cupsprinters:
    try:
        if ( cupsprinters[device]["device-uri"].find("cloudprint://") == 0 ):
            print "Updating " + cupsprinters[device]["printer-info"]
            ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:' + cupsprinters[device]["device-uri"] + ';'
            for ppd in allppds:
                if allppds[ppd]['ppd-device-id'] == ppdid:
                    printerppdname = ppd
            p = subprocess.Popen(["lpadmin", "-p", cupsprinters[device]["printer-info"], "-m", printerppdname], stdout=subprocess.PIPE)
            output = p.communicate()[0]
            result = p.returncode
            sys.stderr.write(output)
    except Exception, e:
        sys.stderr.write("Error connecting to CUPS: " + str(e) + "\n")
