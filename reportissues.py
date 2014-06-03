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

if __name__ == '__main__':  # pragma: no cover

    import sys
    import os
    import subprocess
    libpath = "/usr/local/share/cloudprint-cups/"
    if not os.path.exists(libpath):
        libpath = "/usr/share/cloudprint-cups"
    sys.path.insert(0, libpath)

    from auth import Auth
    from printermanager import PrinterManager
    from ccputils import Utils
    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140530 214732"
    Utils.ShowVersion(CCPVersion)

    requestors, storage = Auth.SetupAuth(True)
    printer_manager = PrinterManager(requestors)
    printers = printer_manager.getPrinters()
    if printers is None:
        print "ERROR: No Printers Found"
        sys.exit(1)

    for printer in printers:
        print printer.getCUPSDriverDescription()
        print ""
        print printer._fields
        print printer['capabilities']
        print "\n"
        ppdname = printer.getPPDName()
        p = subprocess.Popen(
            (os.path.join(libpath, 'dynamicppd.py'), 'cat', ppdname.lstrip('-')),
            stdout=subprocess.PIPE)
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
