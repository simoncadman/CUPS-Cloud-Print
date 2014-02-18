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
    import sys, logging
    from auth import Auth
    from printer import Printer

    if len(sys.argv) == 2 and sys.argv[1] == 'version':
        # line below is replaced on commit
        CCPVersion = "20140218 222928"
        print "CUPS Cloud Print Printer Drive Lister Version " + CCPVersion
        sys.exit(0)

    logpath = '/var/log/cups/cloudprint_log'
    try:
        logging.basicConfig(filename=logpath,level=logging.INFO)
    except:
        logging.basicConfig(level=logging.INFO)
        logging.error("Unable to write to log file "+ logpath)

    requestors, storage = Auth.SetupAuth(True, permissions=['https://www.googleapis.com/auth/cloudprint', 'https://www.googleapis.com/auth/drive.readonly'])
    printer = Printer(requestors)
    files = printer.getDriveFiles()
    if files == None:
        print "No Files Found"
        sys.exit(1)

    for drivefile in files:
        if len(sys.argv) == 2 and drivefile['title'] == sys.argv[1] + '.pdf':
            print drivefile['fileSize']
            sys.exit(0)
        elif len(sys.argv) != 2:
            print drivefile['title']
