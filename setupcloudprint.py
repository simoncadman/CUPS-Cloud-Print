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


def getWindowSize():
    """Gets window height and width.

    Gets window (aka terminal, console) height and width using IOCtl Get WINdow SiZe
    method.

    Returns:
        The tuple (height, width) of the window as integers, or None if the
        windows size isn't available.
    """
    try:
        bytes = struct.pack('HHHH', 0, 0, 0, 0)
        winsize = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, bytes)
        height, width = struct.unpack('HHHH', winsize)[:2]
    except:
        return None

    if height > 0 and width > 0:
        return height, width
    return None


def printPrinters(printers):
    """Prints display name of printers.

    Formats as multiple columns if possible. Enumerates each printer name
    with integers starting with 1 (not zero).

    Args:
        printers: List of printers.
    """

    printer_names = ["%d) %s" % (i + 1, printer['displayName'])
                     for i, printer in enumerate(printers)]

    window_size = getWindowSize()
    if window_size is None or window_size[0] > len(printer_names):
        for printer_name in printer_names:
            print printer_name
    else:
        window_width = window_size[1]
        max_name_length = max((len(printer_name)
                              for printer_name in printer_names))
        # How many columns fit in the window, with one space between columns?
        column_quantity = max(1, (window_width + 1) / (max_name_length + 1))
        row_quantity = int(
            math.ceil(len(printer_names) / float(column_quantity)))

        for row_i in xrange(row_quantity):
            row_printers = []
            for printer_name in printer_names[row_i::row_quantity]:
                row_printers.append(printer_name.ljust(max_name_length))
            print ' '.join(row_printers)

if __name__ == '__main__':  # pragma: no cover
    import cups
    import os
    import json
    import sys
    import fcntl
    import termios
    import struct
    import math
    from auth import Auth
    from printer import Printer
    from ccputils import Utils
    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140323 134450"
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
        except:
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
        if not (answer.startswith("Y") or answer.startswith("y")):
            break
        else:
            Auth.AddAccount(storage)

    for requestor in requestors:
        addedCount = 0
        connection = cups.Connection()
        cupsprinters = connection.getPrinters()
        prefix = ""
        printer = Printer(requestor)
        printers = printer.getPrinters()
        if printers is None:
            print "Sorry, no printers were found on your Google Cloud Print account."
            continue

        if unattended:
            answer = "Y"
        else:
            answer = raw_input(
                "Add all Google Cloud Print printers to local CUPS install from " +
                requestor.getAccount(
                ) +
                " (Y/N)? ")

        if not (answer.startswith("Y") or answer.startswith("y")):
            answer = 1
            print "Not adding printers automatically"

            while int(answer) != 0:
                printPrinters(printers)
                maxprinterid = len(printers)
                answer = raw_input(
                    "Add printer (1-%d, 0 to cancel)? " %
                    maxprinterid)
                try:
                    answer = int(answer)
                except ValueError:
                    answer = 0
                if answer != 0:
                    if answer >= 1 and answer <= maxprinterid:
                        ccpprinter = printers[answer - 1]
                        print "Adding " + printers[answer - 1]['displayName']
                        prefixanswer = raw_input(
                            "Use a prefix for name of printer (Y/N)? ")
                        if prefixanswer.startswith("Y") or prefixanswer.startswith("y"):
                            prefix = raw_input("Prefix ( e.g. GCP- )? ")
                            if prefix == "":
                                print "Not using prefix"

                        printername = prefix + \
                            ccpprinter['name'].encode('ascii', 'replace')
                        uri = printer.printerNameToUri(
                            ccpprinter['account'],
                            ccpprinter['id'])
                        found = False
                        for cupsprinter in cupsprinters:
                            if cupsprinters[cupsprinter]['device-uri'] == uri:
                                found = True
                        if found == True:
                            print "\nPrinter with " + printername + " already exists\n"
                        else:
                            printer.addPrinter(printername, uri, connection)
                    else:
                        print "\nPrinter " + str(answer) + " not found\n"
            continue

        prefixanswer = ""
        if unattended:
            prefixanswer = "Y"
        else:
            prefixanswer = raw_input(
                "Use a prefix for names of created printers (Y/N)? ")

        if prefixanswer.startswith("Y") or prefixanswer.startswith("y"):
            prefix = ""
            if unattended:
                prefix = "GCP-"
            else:
                prefix = raw_input("Prefix ( e.g. GCP- )? ")

            if prefix == "":
                print "Not using prefix"

        for ccpprinter in printers:
            uri = printer.printerNameToUri(
                ccpprinter['account'],
                ccpprinter['id'])
            found = False
            for cupsprinter in cupsprinters:
                if cupsprinters[cupsprinter]['device-uri'] == uri:
                    found = True

            if found == False:
                printername = prefix + ccpprinter['name']

                # check if printer name already exists
                foundbyname = False
                for ccpprinter2 in cupsprinters:
                    if printer.sanitizePrinterName(cupsprinters[ccpprinter2]['printer-info']) == printer.sanitizePrinterName(printername):
                        foundbyname = True
                if foundbyname and not unattended:
                    answer = raw_input(
                        "Printer " +
                        printer.sanitizePrinterName(
                            printername) +
                        " already exists, supply another name (Y/N)? ")
                    if answer.startswith("Y") or answer.startswith("y"):
                        printername = raw_input("New printer name? ")
                    else:
                        answer = raw_input(
                            "Overwrite " +
                            printer.sanitizePrinterName(
                                printername) +
                            " with new printer (Y/N)? ")
                        if answer.startswith("N") or answer.startswith("n"):
                            printername = ""
                elif foundbyname and unattended:
                    print "Not adding printer " + printername + ", as already exists"
                    printername = ""

                if printername != "":
                    printer.addPrinter(printername, uri, connection)
                    cupsprinters = connection.getPrinters()
                    addedCount += 1

        if addedCount > 0:
            print "Added " + str(addedCount) + " new printers to CUPS"
        else:
            print "No new printers to add"

    printeruris = []
    printer = Printer(requestors)
    printers = printer.getPrinters()
    for foundprinter in printers:
        printeruris.append(
            printer.printerNameToUri(foundprinter['account'],
                                     foundprinter['id']))

    # check for printers to prune
    prunePrinters = []
    connection = cups.Connection()
    cupsprinters = connection.getPrinters()

    for cupsprinter in cupsprinters:
        if cupsprinters[cupsprinter]['device-uri'].startswith(printer.PROTOCOL):
            if cupsprinters[cupsprinter]['device-uri'] not in printeruris:
                prunePrinters.append(cupsprinter)

    if len(prunePrinters) > 0:
        print "Found " + str(len(prunePrinters)) + " printers which no longer exist on cloud print:"
        for printer in prunePrinters:
            print printer
        answer = raw_input("Remove (Y/N)? ")
        if answer.startswith("Y") or answer.startswith("y"):
            for printer in prunePrinters:
                connection.deletePrinter(printer)
                print "Deleted", printer
        else:
            print "Not removing old printers"
