#! /bin/sh
"true" '''\'
if command -v python2 > /dev/null; then
  exec python2 "$0" "$@"
else
  exec python "$0" "$@"
fi
exit $?
'''

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

if __name__ == '__main__':  # pragma: no cover

    import sys
    import cups
    import subprocess
    import os
    import json
    import logging
    import urllib
    from auth import Auth
    from ccputils import Utils
    from printermanager import PrinterManager
    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140814.2 000000"
    Utils.ShowVersion(CCPVersion)

    if not os.path.exists("/etc/cloudprint.conf"):
        sys.stderr.write(
            "Config is invalid or missing, not running on fresh install\n")
        logging.warning("Upgrade tried to run on fresh install")
        sys.exit(0)

    requestors, storage = Auth.SetupAuth(False)
    if not requestors:
        sys.stderr.write("Config is invalid or missing\n")
        logging.error("Upgrade tried to run with invalid config")
        sys.exit(0)
    printer_manager = PrinterManager(requestors)

    logging.info("Upgrading to " + CCPVersion)

    try:
        connection = cups.Connection()
    except Exception as e:
        sys.stderr.write("Could not connect to CUPS: " + e.message + "\n")
        sys.exit(0)
    cupsprinters = connection.getPrinters()

    if os.path.exists(Auth.config):
        Utils.FixFilePermissions(Auth.config)

        try:
            content_file = open(Auth.config, 'r')
            content = content_file.read()
            data = json.loads(content)
        except Exception as e:
            sys.stderr.write(
                "Unable to read config file: " +
                e.message +
                "\n\n")
            sys.exit(0)

    else:
        errormessage = "\nRun: /usr/share/cloudprint-cups/"
        errormessage += "setupcloudprint.py to"
        errormessage += " setup your Google Credentials"
        errormessage += " and add your printers to CUPS\n\n"
        sys.stderr.write(errormessage)
        sys.exit(0)

    from ccputils import Utils
    if Utils.which('lpadmin') is None:
        errormessage = "lpadmin command not found"
        errormessage += ", you may need to run this script as root\n"
        sys.stderr.write(errormessage)
        sys.exit(1)

    try:
        print "Fetching list of available ppds..."
        allppds = connection.getPPDs()
        print "List retrieved successfully"
    except Exception as e:
        sys.stderr.write("Error connecting to CUPS: " + str(e) + "\n")
        sys.exit(1)

    for device in cupsprinters:
        try:
            if (cupsprinters[device]["device-uri"].find(Utils.OLD_PROTOCOL) == 0)\
                    or (cupsprinters[device]["device-uri"].find(Utils.PROTOCOL) == 0):
                account, printername, printerid, formatid = \
                    printer_manager.parseLegacyURI(
                        cupsprinters[device]["device-uri"],
                        requestors)
                if formatid != PrinterManager.URIFormatLatest:
                    # not latest format, needs upgrading
                    updatingmessage = "Updating "
                    updatingmessage += cupsprinters[device]["printer-info"]
                    updatingmessage += " with new id uri format"
                    print updatingmessage
                    tempprinter = None
                    printerid, requestor = printer_manager.getPrinterIDByDetails(
                        account, printerid)
                    if printerid is not None:
                        tempprinter = printer_manager.getPrinter(
                            printerid,
                            urllib.unquote(account))
                    if tempprinter is not None:
                        cupsprinters[device]["device-uri"] = tempprinter.getURI()
                        p = subprocess.Popen(
                            ["lpadmin",
                             "-p",
                             cupsprinters[device]["printer-info"].lstrip('-'),
                             "-v",
                             tempprinter.getURI()],
                            stdout=subprocess.PIPE)
                        output = p.communicate()[0]
                        result = p.returncode
                        sys.stderr.write(output)
                    else:
                        errormessage = cupsprinters[device]["printer-info"]
                        errormessage += " not found, "
                        errormessage += "you should delete and "
                        errormessage += "re-add this printer"
                        print errormessage
                        continue
                else:
                    print "Updating " + cupsprinters[device]["printer-info"]

                ppdid = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + \
                    cupsprinters[device]["device-uri"]

                # just needs updating
                printerppdname = None
                for ppd in allppds:
                    if allppds[ppd]['ppd-device-id'] == ppdid:
                        printerppdname = ppd
                if printerppdname is not None:
                    p = subprocess.Popen(
                        ["lpadmin",
                         "-p",
                         cupsprinters[device]["printer-info"].lstrip('-'),
                         "-m",
                         printerppdname.lstrip('-')],
                        stdout=subprocess.PIPE)
                    output = p.communicate()[0]
                    result = p.returncode
                    sys.stderr.write(output)
                else:
                    errormessage = cupsprinters[device]["printer-info"]
                    errormessage += " not found, you should delete and"
                    errormessage += " re-add this printer"
                    print errormessage
        except Exception as e:
            sys.stderr.write("Error connecting to CUPS: " + str(e) + "\n")
