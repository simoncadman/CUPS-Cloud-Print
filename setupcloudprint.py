#! /usr/bin/python

import sys, getpass, mimetools, urllib, urllib2, json, cups
from config import Config
from auth import Auth

CRLF = '\r\n'
BOUNDARY = mimetools.choose_boundary()

# The following are used for authentication functions.
FOLLOWUP_HOST = 'www.google.com/cloudprint'
FOLLOWUP_URI = 'select%2Fgaiaauth'
GAIA_HOST = 'www.google.com'
LOGIN_URI = '/accounts/ServiceLoginAuth'

# The following are used for general backend access.
CLOUDPRINT_URL = 'http://www.google.com/cloudprint'

useConfigDetails = True

try:
  configuration = Config()
except Exception as error:
  useConfigDetails = False
  

def getPrinters(proxy=None):
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

def AddPrinter( printername, uri ) :
  # fix printer name
  printername = printername.replace(' ','_')
  result = None
  try:
    result = connection.addPrinter(name=printername,ppdname='CloudPrint.ppd',info=printername,location='Google Cloud Print',device=uri)
    connection.enablePrinter(printername)
    connection.acceptJobs(printername)
    connection.setPrinterShared(printername, False)
  except Exception as error:
    result = error
  if result == None:
    print "Added",printername
  else:
    print "Error adding:",printername,result
    return None
  
tokens = None
addedCount = 0
success = False
while success == False:
  if useConfigDetails:
    print "Using authentication details from configuration"
    username = configuration.get('Google', 'username')
    password = configuration.get('Google', 'password')
  else:
    print "Please enter your Google Credentials, or CTRL+C to exit: "
    username = raw_input("Username: ")
    password = getpass.getpass()
  
  tokens = Auth.GetAuthTokens(username, password)
  if tokens == None:
    print "Invalid username/password"
    success = False
    useConfigDetails = False
  else:
    print "Successfully connected"
    configuration.save()
    success = True
    
connection = cups.Connection()
cupsprinters = connection.getPrinters()

printers = getPrinters()
if printers == None:
  print "No Printers Found"
  sys.exit(1)
  
printeruris = []

for printer in printers:
  uri = printerNameToUri(printer['name'])
  found = False
  printeruris.append(uri)
  for cupsprinter in cupsprinters:
    if cupsprinters[cupsprinter]['device-uri'] == uri:
      found = True
  if found == False:
    AddPrinter(printer['name'], uri)
    addedCount+=1
    
if addedCount > 0:
  print "Added",addedCount,"new printers to CUPS"
else:
  print "No new printers to add"
  
# check for printers to prune
prunePrinters = []
cupsprinters = connection.getPrinters()

protocolstring = 'cloudprint://'

for cupsprinter in cupsprinters:
  if cupsprinters[cupsprinter]['device-uri'].startswith( protocolstring ):
    if cupsprinters[cupsprinter]['device-uri'] not in printeruris:
      prunePrinters.append(cupsprinter)

if len( prunePrinters ) > 0 :
  print "Found",len( prunePrinters ),"printers with no longer exist on cloud print:"
  for printer in prunePrinters:
    print printer
  answer = raw_input("Remove? ")
  if answer.startswith("Y") or answer.startswith("y"):
    for printer in prunePrinters:
      connection.deletePrinter(printer)
      print "Deleted",printer
  else:
    print "Not removing old printers"