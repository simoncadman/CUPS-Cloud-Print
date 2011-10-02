#! /usr/bin/python

import mimetools, base64, time, httplib, logging, urllib, urllib2, string, mimetypes

email = "test@test.com"
password = "test"

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

def ConvertJson(json_str):    
  """Convert json string to a python object.

  Args:
    json_str: string, json response.
  Returns:
    dictionary of deserialized json string.
  """
  j = {}
  try:
    j = json.loads(json_str)
    j['json'] = True
  except ValueError, e:
    # This means the format from json_str is probably bad.
    logger.error('Error parsing json string %s\n%s', json_str, e)
    j['json'] = False
    j['error'] = e

  return j

def GetKeyValue(line, sep=':'):
    """Return value from a key value pair string.

    Args:
      line: string containing key value pair.
      sep: separator of key and value.
    Returns:
      string: value from key value string.
    """
    s = line.split(sep)
    return StripPunc(s[1])

def StripPunc(s):
  """Strip puncuation from string, except for - sign.

  Args:
    s: string.
  Returns:
    string with puncuation removed.
  """
  for c in string.punctuation:
    if c == '-' or c == '_':  # Could be negative number, so don't remove '-'.
      continue
    else:
      s = s.replace(c, '')
  return s.strip()

def Validate(response):
  """Determine if JSON response indicated success."""
  if response.find('"success": true') > 0:
    return True
  else:
    return False

def GetMessage(response):
  """Extract the API message from a Cloud Print API json response.

  Args:
    response: json response from API request.
  Returns:
    string: message content in json response.
  """
  lines = response.split('\n')
  for line in lines:
    if '"message":' in line:
      msg = line.split(':')
      return msg[1]

  return None

def ReadFile(pathname):
  """Read contents of a file and return content.

  Args:
    pathname: string, (path)name of file.
  Returns:
    string: contents of file.
  """
  try:
    f = open(pathname, 'rb')
    try:
      s = f.read()
    except IOError, e:
      logger('Error reading %s\n%s', pathname, e)
    finally:
      f.close()
      return s
  except IOError, e:
    logger.error('Error opening %s\n%s', pathname, e)
    return None

def WriteFile(file_name, data):
  """Write contents of data to a file_name.

  Args:
    file_name: string, (path)name of file.
    data: string, contents to write to file.
  Returns:
    boolean: True = success, False = errors.
  """
  status = True

  try:
    f = open(file_name, 'wb')
    try:
      f.write(data)
    except IOError, e:
      logger.error('Error writing %s\n%s', file_name, e)
      status = False
    finally:
      f.close()
  except IOError, e:
    logger.error('Error opening %s\n%s', file_name, e)
    status = False

  return status

def Base64Encode(pathname):
  """Convert a file to a base64 encoded file.

  Args:
    pathname: path name of file to base64 encode..
  Returns:
    string, name of base64 encoded file.
  For more info on data urls, see:
    http://en.wikipedia.org/wiki/Data_URI_scheme
  """
  b64_pathname = pathname + '.b64'
  file_type = mimetypes.guess_type(pathname)[0] or 'application/octet-stream'
  data = ReadFile(pathname)

  # Convert binary data to base64 encoded data.
  header = 'data:%s;base64,' % file_type
  b64data = header + base64.b64encode(data)

  if WriteFile(b64_pathname, b64data):
    return b64_pathname
  else:
    return None



def GetCookie(cookie_key, cookie_string):
    """Extract the cookie value from a set-cookie string.

    Args:
      cookie_key: string, cookie identifier.
      cookie_string: string, from a set-cookie command.
    Returns:
      string, value of cookie.
    """
    logger.debug('Getting cookie from %s', cookie_string)
    id_string = cookie_key + '='
    cookie_crumbs = cookie_string.split(';')
    for c in cookie_crumbs:
      if id_string in c:
        cookie = c.split(id_string)
        return cookie[1]
    return None

def GaiaLogin(email, password):
    """Login to gaia using HTTP post to the gaia login page.

    Args:
      email: string,
      password: string
    Returns:
      dictionary of authentication tokens.
    """
    tokens = {}
    cookie_keys = ['SID', 'LSID', 'HSID', 'SSID']
    email = email.replace('+', '%2B')
    # Needs to be some random string.
    galx_cookie = base64.b64encode('%s%s' % (email, time.time()))

    # Simulate submitting a gaia login form.
    form = ('ltmpl=login&fpui=1&rm=hide&hl=en-US&alwf=true'
            '&continue=https%%3A%%2F%%2F%s%%2F%s'
            '&followup=https%%3A%%2F%%2F%s%%2F%s'
            '&service=%s&Email=%s&Passwd=%s&GALX=%s' % (FOLLOWUP_HOST,
            FOLLOWUP_URI, FOLLOWUP_HOST, FOLLOWUP_URI, SERVICE, email,
            password, galx_cookie))
    login = httplib.HTTPS(GAIA_HOST, 443)
    login.putrequest('POST', LOGIN_URI)
    login.putheader('Host', GAIA_HOST)
    login.putheader('content-type', 'application/x-www-form-urlencoded')
    login.putheader('content-length', str(len(form)))
    login.putheader('Cookie', 'GALX=%s' % galx_cookie)
    logger.debug('Sent POST content: %s', form)
    login.endheaders()
    logger.info('HTTP POST to https://%s%s', GAIA_HOST, LOGIN_URI)
    login.send(form)

    (errcode, errmsg, headers) = login.getreply()
    login_output = login.getfile()
    login_output.close()
    login.close()
    logger.info('Login complete.')

    if errcode != 302:
      logger.error('Gaia HTTP post returned %d, expected 302', errcode)
      logger.error('Message: %s', errmsg)

    for line in str(headers).split('\r\n'):
      if not line: continue
      (name, content) = line.split(':', 1)
      if name.lower() == 'set-cookie':
        for k in cookie_keys:
          if content.strip().startswith(k):
            tokens[k] = GetCookie(k, content)
    if not tokens:
      logger.error('No cookies received, check post parameters.')
      return None
    else:
      logger.debug('Received the following authorization tokens.')
      for t in tokens:
        logger.debug(t)
      return tokens

def GetAuthTokens(email, password):
    """Assign login credentials from GAIA accounts service.

    Args:
      email: Email address of the Google account to use.
      password: Cleartext password of the email account.
    Returns:
      dictionary containing Auth token.
    """
    # First get GAIA login credentials using our GaiaLogin method.
    tokens = GaiaLogin(email, password)

    # We still need to get the Auth token.    
    params = {'accountType': 'GOOGLE',
              'Email': email,
              'Passwd': password,
              'service': SERVICE,
              'source': CLIENT_NAME}
    stream = urllib.urlopen(LOGIN_URL, urllib.urlencode(params))

    for line in stream:
      if line.strip().startswith('Auth='):
        tokens['Auth'] = line.strip().replace('Auth=', '')
    
    return tokens


tokens = GetAuthTokens(email, password)


def EncodeMultiPart(fields, files, file_type='application/xml'):
    """Encodes list of parameters and files for HTTP multipart format.

    Args:
      fields: list of tuples containing name and value of parameters.
      files: list of tuples containing param name, filename, and file contents.
      file_type: string if file type different than application/xml.
    Returns:
      A string to be sent as data for the HTTP post request.
    """
    lines = []
    for (key, value) in fields:
      lines.append('--' + BOUNDARY)
      lines.append('Content-Disposition: form-data; name="%s"' % key)
      lines.append('')  # blank line
      lines.append(value)
    for (key, filename, value) in files:
      lines.append('--' + BOUNDARY)
      lines.append(
          'Content-Disposition: form-data; name="%s"; filename="%s"'
          % (key, filename))
      lines.append('Content-Type: %s' % file_type)
      lines.append('')  # blank line
      lines.append(value)
    lines.append('--' + BOUNDARY + '--')
    lines.append('')  # blank line
    return CRLF.join(lines)
    
    
def SubmitJob(printerid, jobtype, jobsrc):
  """Submit a job to printerid with content of dataUrl.

  Args:
    printerid: string, the printer id to submit the job to.
    jobtype: string, must match the dictionary keys in content and content_type.
    jobsrc: string, points to source for job. Could be a pathname or id string.
  Returns:
    boolean: True = submitted, False = errors.
  """
  if jobtype == 'pdf':
    b64file = Base64Encode(jobsrc)
    fdata = ReadFile(b64file)
    hsid = True
  elif jobtype in ['png', 'jpeg']:
    fdata = ReadFile(jobsrc)
  else:
    fdata = None

  # Make the title unique for each job, since the printer by default will name
  # the print job file the same as the title.

  datehour = time.strftime('%b%d%H%M', time.localtime())
  title = '%s%s' % (datehour, jobsrc)
  content = {'pdf': fdata,
             'jpeg': jobsrc,
             'png': jobsrc,
            }
  content_type = {'pdf': 'dataUrl',
                  'jpeg': 'image/jpeg',
                  'png': 'image/png',
                 }
  headers = [('printerid', printerid),
             ('title', title),
             ('content', content[jobtype]),
             ('contentType', content_type[jobtype])]
  files = [('capabilities', 'capabilities', '{"capabilities":[]}')]
  if jobtype in ['pdf', 'jpeg', 'png']:
    files.append(('content', jobsrc, fdata))
    edata = EncodeMultiPart(headers, files, file_type=content_type[jobtype])
  else:
    edata = EncodeMultiPart(headers, files)

  response = GetUrl('%s/submit' % CLOUDPRINT_URL, tokens, data=edata,
                    cookies=False)
  status = Validate(response)
  if not status:
    error_msg = GetMessage(response)
    logger.error('Print job %s failed with %s', jobtype, error_msg)

  return status
  
  
def getPrinter(printer, proxy=None):
    printer_id = None
    response = GetUrl('%s/search?q=%s' % (CLOUDPRINT_URL, printer), tokens)
    printer = urllib.unquote(printer)
    sections = response.split('"printers": [')
    lines = sections[1].split(',')
    for line in lines:
      if '"id"' in line:
        printer_id = GetKeyValue(line)
      elif '"name"' in line:
        printer_name = GetKeyValue(line)
        if printer_name == printer:
          logger.debug('Printer %s is registered', printer)
          if printer_id:
            return printer_id
          else:
            logger.error('Malformed api response.')
            return None

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
    

printerid = getPrinter("Print%20to%20Google%20Docs")
print SubmitJob(printerid, 'pdf', '/tmp/testpdf.pdf')