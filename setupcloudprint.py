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


def printPrinters(printers):
    """Prints display name of printers.

    Formats as multiple columns if possible. Enumerates each printer name
    with integers starting with 1 (not zero).

    Args:
        printers: List of printers.

    Returns:
        number of printers printed
    """

    printer_names = \
        ["%d) %s" % (i + 1, printer['displayName']) for i, printer in enumerate(printers)]

    window_size = Utils.GetWindowSize()
    if window_size is None or window_size[0] > len(printer_names):
        for printer_name in printer_names:
            print printer_name
    else:
        window_width = window_size[1]
        max_name_length = max((len(printer_name) for printer_name in printer_names))
        # How many columns fit in the window, with one space between columns?
        column_quantity = max(1, (window_width + 1) / (max_name_length + 1))
        row_quantity = int(math.ceil(len(printer_names) / float(column_quantity)))

        for row_i in xrange(row_quantity):
            row_printers = []
            for printer_name in printer_names[row_i::row_quantity]:
                row_printers.append(printer_name.ljust(max_name_length))
            print ' '.join(row_printers)
    return len(printers)

if __name__ == '__main__':  # pragma: no cover
    import cups
    import os
    import json
    import sys
    import math
    from auth import Auth
    from printermanager import PrinterManager
    from ccputils import Utils
    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140705 163713"
    Utils.ShowVersion(CCPVersion)

    unattended = False
    answer = ""

    if len(sys.argv) == 2 and sys.argv[1] == 'unattended':
        print "Running unattended, setting up all printers"
        unattended = True

    if os.path.exists(Auth.config):
        try:
            content_file = open(Auth.config, 'r')
            content = content_file.read()
            data = json.loads(content)
        except Exception:
            # remove old config file
            print "Deleting old configuration file: " + Auth.config
            os.remove(Auth.config)

    while True:
        requestors, storage = Auth.SetupAuth(True)
        print "You currently have these accounts configured: "
        for requestor in requestors:
            print requestor.getAccount()
        if unattended:
            break
        answer = raw_input("Add more accounts (Y/N)? ")
        if not answer.lower().startswith("y"):
            break
        else:
            Auth.AddAccount(storage)

    for requestor in requestors:
        addedCount = 0
        connection = cups.Connection()
        cupsprinters = connection.getPrinters()
        prefix = ""
        printer_manager = PrinterManager(requestor)
        printers = printer_manager.getPrinters()
        if printers is None:
            print "Sorry, no printers were found on your Google Cloud Print account."
            continue

        if unattended:
            answer = "y"
        else:
            answer = raw_input("Add all Google Cloud Print printers from %s to CUPS (Y/N)? " %
                               requestor.getAccount())

        if not answer.lower().startswith("y"):
            answer = 1
            print "Not adding printers automatically"

            while int(answer) != 0:
                maxprinterid = printPrinters(printers)
                answer = raw_input("Add printer (1-%d, 0 to cancel)? " % maxprinterid)
                try:
                    answer = int(answer)
                except ValueError:
                    answer = 0
                if answer == 0:
                    continue
                if answer < 1 or answer > maxprinterid:
                    print "\nPrinter %d not found\n" % answer
                    continue

                ccpprinter = printers[answer - 1]
                print "Adding " + printers[answer - 1]['displayName']
                prefixanswer = raw_input("Use a prefix for name of printer (Y/N)? ")
                if prefixanswer.lower().startswith("y"):
                    prefix = raw_input("Prefix ( e.g. GCP- )? ")
                    if prefix == "":
                        print "Not using prefix"

                printername = prefix + ccpprinter.getDisplayName().encode('ascii', 'replace')
                found = False
                for cupsprinter in cupsprinters:
                    if cupsprinters[cupsprinter]['device-uri'] == ccpprinter.getURI():
                        found = True
                if found:
                    print "\nPrinter with %s already exists\n" % printername
                else:
                    printer_manager.addPrinter(printername, ccpprinter, connection)

            continue

        prefixanswer = ""
        if unattended:
            prefixanswer = "Y"
        else:
            prefixanswer = raw_input("Use a prefix for names of created printers (Y/N)? ")

        if prefixanswer.lower().startswith("y"):
            prefix = ""
            if unattended:
                prefix = "GCP-"
            else:
                prefix = raw_input("Prefix ( e.g. GCP- )? ")

            if prefix == "":
                print "Not using prefix"

        for ccpprinter in printers:
            found = False
            for cupsprinter in cupsprinters:
                if cupsprinters[cupsprinter]['device-uri'] == ccpprinter.getURI():
                    found = True

            if found:
                continue

            printername = prefix + ccpprinter.getDisplayName()

            # check if printer name already exists
            foundbyname = False
            for ccpprinter2 in cupsprinters:
                printerinfo = cupsprinters[ccpprinter2]['printer-info']
                if printer_manager.sanitizePrinterName(printerinfo) == \
                        printer_manager.sanitizePrinterName(printername):
                    foundbyname = True
            if foundbyname and not unattended:
                answer = raw_input('Printer %s already exists, supply another name (Y/N)? ' %
                                   printer_manager.sanitizePrinterName(printername))
                if answer.startswith("Y") or answer.startswith("y"):
                    printername = raw_input("New printer name? ")
                else:
                    answer = raw_input("Overwrite %s with new printer (Y/N)? " %
                                       printer_manager.sanitizePrinterName(printername))
                    if answer.lower().startswith("n"):
                        printername = ""
            elif foundbyname and unattended:
                print "Not adding printer %s, as already exists" % printername
                printername = ""

            if printername != "":
                printer_manager.addPrinter(printername, ccpprinter, connection)
                cupsprinters = connection.getPrinters()
                addedCount += 1

        if addedCount > 0:
            print "Added %d new printers to CUPS" % addedCount
        else:
            print "No new printers to add"

    printer_uris = []
    printer_manager = PrinterManager(requestors)
    printers = printer_manager.getPrinters()
    for printer in printers:
        printer_uris.append(printer.getURI())

    # check for printers to prune
    prunePrinters = []
    connection = cups.Connection()
    cupsprinters = connection.getPrinters()

    for cupsprinter in cupsprinters:
        if cupsprinters[cupsprinter]['device-uri'].startswith(Utils.PROTOCOL) \
                and cupsprinters[cupsprinter]['device-uri'] not in printer_uris:
            prunePrinters.append(cupsprinter)

    if len(prunePrinters) > 0:
        print "Found %d printers which no longer exist on cloud print:" % len(prunePrinters)
        for printer in prunePrinters:
            print printer
        answer = raw_input("Remove (Y/N)? ")
        if answer.lower().startswith("y"):
            for printer in prunePrinters:
                connection.deletePrinter(printer)
                print "Deleted", printer
        else:
            print "Not removing old printers"
