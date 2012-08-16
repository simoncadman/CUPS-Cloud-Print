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
import httplib2, json

class cloudprintrequestor(httplib2.Http):
  
  CLOUDPRINT_URL = 'http://www.google.com/cloudprint'
  account = None
  
  def setAccount ( self, account ):
    self.account = account
  
  def getAccount ( self ):
    return self.account
  
  def doRequest ( self, path, headers = None, data = None , boundary = None ):
    url = '%s/%s' % (self.CLOUDPRINT_URL, path)
    if data == None:
      headers, response = self.request(url, "GET")
    else:
      headers, response = self.request(url, "GET", body=data, headers=headers)
      print response
    return json.loads(response)