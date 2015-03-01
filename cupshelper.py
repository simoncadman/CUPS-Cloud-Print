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

from ccputils import Utils

import cups


class CUPSHelper(object):
    def __init__(self, connection=None):
        if connection is None:
            self._connection = cups.Connection()
        else:
            self._connection = connection

    def _getCUPSQueueName(self, uri):
        for cups_queue_name, printer in self.getPrinters().items():
            if printer['device-uri'] == uri:
                return cups_queue_name
        return None

    def _getCUPSQueueNameAndPrinter(self, uri):
        for cups_queue_name, printer in self.getPrinters().items():
            if printer['device-uri'] == uri:
                return cups_queue_name, printer
        return None, None

    def getPPDs(self):
        return self._connection.getPPDs()

    def getPPDAttributes(self, name):
        return cups.PPD(self._connection.getPPD(name)).attributes

    def getPrinter(self, uri):
        for cups_queue_name, printer in self.getPrinters().items():
            if printer['device-uri'] == uri:
                return printer
        return None

    def getPrinters(self):
        printers = self._connection.getPrinters()
        return dict((name, printer) for (name, printer) in printers.iteritems()
                    if printer['device-uri'].startswith(Utils.PROTOCOL))

    def deletePrinter(self, uri):
        return self._connection.deletePrinter(uri)

    def renamePrinter(self, uri, name, location):
        cups_queue_name, printer = self._getCUPSQueueNameAndPrinter(uri)
        if cups_queue_name is not None:
            if printer['printer-info'] != name:
                self._connection.setPrinterInfo(cups_queue_name, name)
            if printer['printer-location'] != location:
                self._connection.setPrinterLocation(cups_queue_name, location)

    def addPrinter(self, ccp_printer, name, location=None, ppd=None):
        error = None
        try:
            if ppd:
                ppd_name = ppd
            else:
                ppd_name = ccp_printer.getPPDName()
            if location is None:
                location = 'Google Cloud Print'
            if location.strip() == '':
                location = ccp_printer.getLocation()

            error = self._connection.addPrinter(
                name=name,
                ppdname=ppd_name,
                info=name,
                location=location,
                device=ccp_printer.getURI())
            self._connection.enablePrinter(name)
            self._connection.acceptJobs(name)
            self._connection.setPrinterShared(name, False)

        except Exception as e:
            error = e

        if error is not None:
            print 'Error adding: %s' % name
            print error
            return False

        return True

    def getServerSetting(self, name):
        settings = self._connection.adminGetServerSettings()
        if name in settings:
            return settings[name]
        return None

    @staticmethod
    def generateCUPSQueueName(ccp_printer):
        """Generates a queue name that complies to validate_name() in lpadmin.c"""
        name = ''
        for letter in '%s-%s' % (ccp_printer.getDisplayName(), ccp_printer.getAccount()):
            if letter in ('@', '/', '#') or ord(letter) <= ord(' ') or ord(letter) >= 127:
                continue
            name += letter
        return name[:127]
