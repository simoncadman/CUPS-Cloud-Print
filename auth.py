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

import urllib, urllib2, mimetools, time
from oauth2client import client
from oauth2client.file import Storage
from oauth2client import multistore_file
from cloudprintrequestor import cloudprintrequestor 

class Auth():
  
  @staticmethod
  def GetUrl(url, data=None, cookies=False, anonymous=False, boundary=None):
    """Get URL, with GET or POST depending data, adds Authorization header.

    Args:
      url: Url to access.
      tokens: dictionary of authentication tokens for specific user.
      data: If a POST request, data to be sent with the request.
      cookies: boolean, True = send authentication tokens in cookie headers.
      anonymous: boolean, True = do not send login credentials.
    Returns:
      String: response to the HTTP request.
    """
    if boundary == None:
      boundary = mimetools.choose_boundary()
    
    request = urllib2.Request(url)
    request.add_header('X-CloudPrint-Proxy', 'api-prober')
    if not anonymous:
      if cookies:
	request.add_header('Cookie', 'SID=%s; HSID=%s; SSID=%s' % (
	    tokens['SID'], tokens['HSID'], tokens['SSID']))
      else:  # Don't add Auth headers when using Cookie header with auth tokens.   
	request.add_header('Authorization', 'GoogleLogin auth=%s' % tokens['Auth'])
    if data:
      request.add_data(data)
      request.add_header('Content-Length', str(len(data)))
      request.add_header('Content-Type', 'multipart/form-data;boundary=%s' % boundary)
    
    # In case the gateway is not responding, we'll retry.
    retry_count = 0
    while retry_count < 5:
      try:
	result = urllib2.urlopen(request).read()
	return result
      except urllib2.HTTPError, e:
	# We see this error if the site goes down. We need to pause and retry.
	err_msg = 'Error accessing %s\n%s' % (url, e)
	time.sleep(60)
	retry_count += 1
	if retry_count == 5:
	  return err_msg

  @staticmethod
  def SetupAuth(interactive=False):
    clientid = '843805314553.apps.googleusercontent.com'
    clientsecret = 'MzTBsY4xlrD_lxkmwFbBrvBv'
    userids = [ "cloudprint" ]
    requestors = []
    for userid in userids:
      storage = multistore_file.get_credential_storage(
	    '/etc/cloudprint.conf',
	    clientid,
	    userid,
	    ['https://www.googleapis.com/auth/cloudprint'])
      credentials = storage.get()

      if not credentials and interactive:
	flow = client.OAuth2WebServerFlow(client_id=clientid,
				  client_secret=clientsecret,
				  scope='https://www.googleapis.com/auth/cloudprint',
				  user_agent=userid)
	auth_uri = flow.step1_get_authorize_url()
	print(userid)
	print("Open this URL and provide the code: " + auth_uri)
	code = raw_input('Code from Google: ')
	credentials = flow.step2_exchange(code)
	storage.put(credentials)
      elif not interactive:
	return False

      requestor = cloudprintrequestor()
      requestor = credentials.authorize(requestor)
      requestor.setAccount(userid)
      requestors.append(requestor)
    return requestors