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

if __name__ == '__main__': # pragma: no cover
    
    import sys, cups, subprocess, os, json, logging, urllib
    from oauth2client import client
    from oauth2client import multistore_file
    from auth import Auth
    from ccputils import Utils
    from printer import Printer
    Utils.SetupLogging()
    
    # line below is replaced on commit
    CCPVersion = "20140312 225205"
    Utils.ShowVersion(CCPVersion)
    
    if not os.path.exists("/etc/cloudprint.conf"):
        sys.stderr.write("Config is invalid or missing, not running on fresh install\n")
        logging.warning("Upgrade tried to run on fresh install");
        sys.exit(0)
    
    requestors, storage = Auth.SetupAuth(False)
    if requestors == False:
        sys.stderr.write("Config is invalid or missing\n")
        logging.error("Upgrade tried to run with invalid config");
        sys.exit(0)
    printerItem = Printer(requestors)
    
    logging.info("Upgrading to " + CCPVersion)

    try:
        connection = cups.Connection()
    except Exception, e:
        sys.stderr.write("Could not connect to CUPS: " + e.message +"\n")
        sys.exit(0)
    cupsprinters = connection.getPrinters()

    if os.path.exists(Auth.config):
        Utils.FixFilePermissions(Auth.config)

        try:
            content_file = open(Auth.config, 'r')
            content = content_file.read()
            data = json.loads(content)
        except Exception, e:
            sys.stderr.write("Unable to read config file: " + e.message +"\n\n")
            sys.exit(0)

    else:
        sys.stderr.write("\nRun: /usr/share/cloudprint-cups/setupcloudprint.py to setup your Google Credentials and add your printers to CUPS\n\n")
        sys.exit(0)

    from ccputils import Utils
    if Utils.which('lpadmin') == None:
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
                account, printername, printerid, formatid = printerItem.parseLegacyURI(cupsprinters[device]["device-uri"], requestors)
                if formatid != Printer.URIFormatLatest:
                    # not latest format, needs upgrading
                    print "Updating " + cupsprinters[device]["printer-info"], "with new id uri format"
                    printerid, requestor = printerItem.getPrinterIDByDetails(account, printername, printerid)
                    if printerid != None:
                        newDeviceURI = printerItem.printerNameToUri(urllib.unquote(account), printerid)
                        cupsprinters[device]["device-uri"] = newDeviceURI
                        p = subprocess.Popen(["lpadmin", "-p", cupsprinters[device]["printer-info"].lstrip('-'), "-v", newDeviceURI], stdout=subprocess.PIPE)
                        output = p.communicate()[0]
                        result = p.returncode
                        sys.stderr.write(output)
                    else:
                        print cupsprinters[device]["printer-info"], " not found, you should delete and re-add this printer"
                        continue
                else:  
                    print "Updating " + cupsprinters[device]["printer-info"]
                    
                ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:' + cupsprinters[device]["device-uri"] + ';'
                
                # just needs updating
                printerppdname = None
                for ppd in allppds:
                    if allppds[ppd]['ppd-device-id'] == ppdid:
                        printerppdname = ppd
                if printerppdname != None:
                    p = subprocess.Popen(["lpadmin", "-p", cupsprinters[device]["printer-info"].lstrip('-'), "-m", printerppdname.lstrip('-')], stdout=subprocess.PIPE)
                    output = p.communicate()[0]
                    result = p.returncode
                    sys.stderr.write(output)
                else:
                    print cupsprinters[device]["printer-info"], "not found, you should delete and re-add this printer"
        except Exception, e:
            sys.stderr.write("Error connecting to CUPS: " + str(e) + "\n")
