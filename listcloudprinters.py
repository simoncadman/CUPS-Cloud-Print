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
    from ccputils import Utils
    Utils.SetupLogging()
    
    # line below is replaced on commit
    CCPVersion = "20140313 235824"
    Utils.ShowVersion(CCPVersion)

    requestors, storage = Auth.SetupAuth(True)
    printer = Printer(requestors)
    printers = printer.getPrinters()
    if printers == None:
        print "No Printers Found"
        sys.exit(1)

    for foundprinter in printers:
        print printer.getListDescription(foundprinter)
