#    CUPS Cloudprint - Print via Google Cloud Print
#    Copyright (C) 2014 Simon Cadman
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

class MockCUPS():
    
    _printers = {}
    
    def __init__(self):
        self._printers = {}
    
    def getPrinters(self):
        return self._printers
    
    def addPrinter(self, name, ppdname, info, location, device):
        self._printers[name] = {'printer-is-shared': False,
                                'printer-info': info,
                                'printer-state-message': '',
                                'printer-type': 1,
                                'printer-state-reasons': ['none'],
                                'printer-uri-supported': 'ipp://localhost/printers/' + name,
                                'printer-state': 3,
                                'printer-location': location,
                                'device-uri': device}
    
    def deletePrinter(self, name):
        del self._printers[name]
    
    def enablePrinter(self, name):
        self._printers[name]['printer-state'] = 3
    
    def acceptJobs(self, name):
        self._printers[name]['printer-state'] = 3
    
    def setPrinterShared(self, name, status):
        self._printers[name]['printer-is-shared'] = status
        
    def setPrinterInfo(self, queue, name):
        if queue in self._printers:
            self._printers[queue]['printer-info'] = name
            return True
        return False
    
    def setPrinterLocation(self, queue, location):
        if queue in self._printers:
            self._printers[queue]['printer-location'] = location
            return True
        return False