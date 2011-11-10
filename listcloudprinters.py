#! /usr/bin/python
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

import mimetools, base64, time, httplib, logging, urllib, urllib2, string, mimetypes, sys, os, json



import ConfigParser, os, pickle

class Config():
  
  configfile = "/etc/cloudprint.conf"
  
  def __init__( self ):
    self.config = ConfigParser.ConfigParser()
    self.config.readfp( open(self.configfile) )
    # verify we have needed params
    self.config.get("Google", "Username")
    self.config.get("Google", "Password")
    
  def get ( self, section, key ):
    return self.config.get(section, key)

  def save (self ):
    with open(self.configfile, 'wb') as configdetail:
      self.config.write(configdetail)

try:
  configuration = Config()
except IOError:
  print "ERROR: Unable to load configuration from", Config.configfile,", create one from cloudprint.conf.example"
  sys.exit(1)
except Exception as error:
  print "ERROR: Unknown error when reading configuration file - ", error
  sys.exit(1)

email = configuration.get("Google", "Username")
password = configuration.get("Google", "Password")

CRLF = '\r\n'
BOUNDARY = mimetools.choose_boundary()

# The following are used for authentication functions.
FOLLOWUP_HOST = 'www.google.com/cloudprint'
FOLLOWUP_URI = 'select%2Fgaiaauth'
GAIA_HOST = 'www.google.com'
LOGIN_URI = '/accounts/ServiceLoginAuth'
LOGIN_URL = 'https://www.google.com/accounts/ClientLogin'
SERVICE = 'cloudprint'
OAUTH = 'This_should_contain_oauth_string_for_your_username'

# The following are used for general backend access.
CLOUDPRINT_URL = 'http://www.google.com/cloudprint'
# CLIENT_NAME should be some string identifier for the client you are writing.
CLIENT_NAME = 'CUPS Cloud Print'

logger = logging



def GetAuthTokens(email, password):
    """Assign login credentials from GAIA accounts service.

    Args:
      email: Email address of the Google account to use.
      password: Cleartext password of the email account.
    Returns:
      dictionary containing Auth token.
    """
    tokens = {}

    # We still need to get the Auth token.    
    params = {'accountType': 'GOOGLE',
              'Email': email,
              'Passwd': password,
              'service': SERVICE,
              'source': CLIENT_NAME}
    stream = urllib.urlopen(LOGIN_URL, urllib.urlencode(params))

    success = False
    for line in stream:
      if line.strip().startswith('Auth='):
        tokens['Auth'] = line.strip().replace('Auth=', '')
        success = True
    
    if not success:
      return None
    
    return tokens


tokens = GetAuthTokens(email, password)
if tokens == None:
  print "ERROR: Invalid username/password"
  sys.exit(1)

    
def getPrinters(proxy=None):
    printer_id = None
    response = GetUrl('%s/search?q=' % (CLOUDPRINT_URL), tokens)
    responseobj = json.loads(response)
    if 'printers' in responseobj and len(responseobj['printers']) > 0:
      return responseobj['printers']
    else:
      return None

def GetUrl(url, tokens, data=None, cookies=False, anonymous=False):
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
  request = urllib2.Request(url)
  request.add_header('X-CloudPrint-Proxy', 'api-prober')
  if not anonymous:
    if cookies:
      logger.debug('Adding authentication credentials to cookie header')
      request.add_header('Cookie', 'SID=%s; HSID=%s; SSID=%s' % (
          tokens['SID'], tokens['HSID'], tokens['SSID']))
    else:  # Don't add Auth headers when using Cookie header with auth tokens.   
      request.add_header('Authorization', 'GoogleLogin auth=%s' % tokens['Auth'])
  if data:
    request.add_data(data)
    request.add_header('Content-Length', str(len(data)))
    request.add_header('Content-Type', 'multipart/form-data;boundary=%s' % BOUNDARY)

  # In case the gateway is not responding, we'll retry.
  retry_count = 0
  while retry_count < 5:
    try:
      result = urllib2.urlopen(request).read()
      return result
    except urllib2.HTTPError, e:
      # We see this error if the site goes down. We need to pause and retry.
      err_msg = 'Error accessing %s\n%s' % (url, e)
      logger.error(err_msg)
      logger.info('Pausing %d seconds', 60)
      time.sleep(60)
      retry_count += 1
      if retry_count == 5:
        return err_msg

def printerNameToUri( printer ) :
  printer = urllib.quote(printer)
  return 'cloudprint://' + printer

printers = getPrinters()
if printers == None:
  print "No Printers Found"
  sys.exit(1)

for printer in printers:
  print printer['name'] + ' - ' + printerNameToUri(printer['name'])
