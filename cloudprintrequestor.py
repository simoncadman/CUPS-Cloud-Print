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
import httplib2
import json
import logging
import time


class CloudPrintRequestor(httplib2.Http):

    CLOUDPRINT_URL = 'https://www.google.com/cloudprint'
    account = None

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

    def doRequest(self, path, headers=None, data=None, boundary=None, testResponse=None,
                  endpointurl=None):
        """Sends a request to Google Cloud Print

        Args:
          path: string, path part of url
          headers: list, headers to send to GCP
          data: string, body part of request
          boundary: string, boundary part of http forms
        Return:
          list: Decoded json response from Google.
        """

        rpc_name = path.split('?', 1)[0]
        logging.debug('Calling %s RPC', rpc_name)
        start_time = time.time()

        # force useragent to CCP
        if headers is None:
            headers = {}
        headers['user-agent'] = "CUPS Cloud Print"

        url = '%s/%s' % (self.CLOUDPRINT_URL, path)
        if endpointurl is not None:
            url = '%s/%s' % (endpointurl, path)

        # use test response for testing
        if testResponse is None:
            if data is None:
                headers, response = self.request(url, "GET", headers=headers)
            else:
                headers['Content-Length'] = str(len(data))
                contenttype = 'multipart/form-data;boundary=%s' % boundary
                headers['Content-Type'] = contenttype
                headers, response = self.request(
                    url, "POST", body=data, headers=headers)
        else:
            response = testResponse

        try:
            decodedresponse = json.loads(response)
        except ValueError as e:
            print "ERROR: Failed to decode JSON, value was: " + response
            raise e

        logging.debug('%s RPC took %.2f seconds', rpc_name, time.time() - start_time)

        return decodedresponse

    def search(self):
        return self.doRequest('search?connection_status=ALL&client=webui')

    def printer(self, printerid):
        return self.doRequest('printer?printerid=%s' % printerid)

    def submit(self, edata, boundary):
        return self.doRequest('submit', data=edata, boundary=boundary)
