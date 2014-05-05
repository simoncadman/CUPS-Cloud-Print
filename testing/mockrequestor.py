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
import json
import urllib
import sys
sys.path.insert(0, ".")
from cloudprintrequestor import CloudPrintRequestor

class MockRequestor(CloudPrintRequestor):

    account = None
    printers = []

    def setAccount(self, account):
        """Sets the account name

        Args:
        filename: string, name of the account
        """
        self.account = account

    def getAccount(self):
        """Gets the account name

        Return:
        string: Account name.
        """
        return self.account
    
    def mockSearch(self, path, headers, data, boundary):
        return json.dumps({'printers': self.printers})

    def mockSubmit(self, path, headers, data, boundary):
        if 'FAIL PAGE' in data:
            result = {
                'success': False,
                'message': 'FAIL PAGE was in message'}
        else:
            result = {'success': True}
        return json.dumps(result)

    def mockPrinter(self, path, headers, data, boundary):
        printername = path.split('=')[1]
        foundPrinter = None
        for printer in self.printers:
            if printer['id'] == printername:
                foundPrinter = printer
                break

        if foundPrinter is None:
            return json.dumps(None)

        result = {'printers': [foundPrinter]}
        return json.dumps(result)

    def doRequest(self, path, headers=None, data=None, boundary=None):
        if (path.startswith('search?')):
            return json.loads(self.mockSearch(path, headers, data, boundary))
        if (path.startswith('printer?')):
            return json.loads(self.mockPrinter(path, headers, data, boundary))
        if (path == 'submit'):
            return json.loads(self.mockSubmit(path, headers, data, boundary))
        return None
