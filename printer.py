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
import json, urllib, os, mimetypes, base64, mimetools, re
from auth import Auth
from urlparse import urlparse

class Printer:
  BOUNDARY = mimetools.choose_boundary()
  CRLF = '\r\n'
  PROTOCOL = 'cloudprint://'
  requestors = None
  requestor = None
  
  def __init__( self, requestors ):
    """Create an instance of Printer, with authorised requestor

    Args:
      requestors: list or cloudprintrequestor instance, A list of requestors, or a single requestor to use for all Cloud Print requests.
    """
    if isinstance(requestors, list):
      self.requestors = requestors
    else:
      self.requestors = [requestors]

  def getPrinters(self):
    """Fetch a list of printers

    Returns:
      list: list of printers for the accounts.
    """
    allprinters = []
    for requestor in self.requestors:
      responseobj = requestor.doRequest('search?connection_status=ALL&client=webui')
      if 'printers' in responseobj and len(responseobj['printers']) > 0:
	for printer in responseobj['printers']:
	  printer['account'] = requestor.getAccount()
	  allprinters.append(printer)
    return allprinters
  
  def printerNameToUri( self, account, printer ) :
    """Generates a URI for the Cloud Print Printer

    Args:
      account: string, account name reference
      printer: string, name of printer from Google Cloud Print
      
    Returns:
      string: URI for the printer
    """
    return self.PROTOCOL + urllib.quote(printer) + "/" + urllib.quote(account)


  def sanitizePrinterName ( self, name ) :
    """Sanitizes printer name for CUPS

    Args:
      name: string, name of printer from Google Cloud Print
      
    Returns:
      string: CUPS-friendly name for the printer
    """
    return re.sub('[^a-zA-Z0-9\-_]', '', name.encode('ascii', 'replace').replace( ' ', '_' ) )

  def addPrinter( self, printername, uri, connection ) :
    """Adds a printer to CUPS

    Args:
      printername: string, name of the printer to add
      uri: string, uri of the Cloud Print device
      connection: connection, CUPS connection
      
    Returns:
      None
    """
    # fix printer name
    printername = self.sanitizePrinterName(printername)
    result = None
    try:
      result = connection.addPrinter(name=printername,ppdname='CloudPrint.ppd',info=printername,location='Google Cloud Print',device=uri)
      connection.enablePrinter(printername)
      connection.acceptJobs(printername)
      connection.setPrinterShared(printername, False)
    except Exception , error:
      result = error
    if result == None:
      print("Added " + printername)
      return True
    else:
      print("Error adding: " + printername,result)
      return False
      
  def parseURI( self, uristring ):
    """Parses a CUPS Cloud Print URI

    Args:
      uristring: string, uri of the Cloud Print device
      
    Returns:
      string: google cloud print printer name
      string: account name
    """
    uri = urlparse(uristring)
    return uri.netloc, uri.path.lstrip('/')
      
  def findRequestorForAccount(self, account):
    """Searches the requestors in the printer object for the requestor for a specific account

    Args:
      account: string, account name
    Return:
      requestor: Single requestor object for the account, or None if no account found
    """
    for requestor in self.requestors:
      if requestor.getAccount() == account:
	return requestor
      
  def getPrinterIDByURI(self, uri):
    """Gets printer id and requestor by printer

    Args:
      uri: string, printer uri
    Return:
      printer id: Single requestor object for the account, or None if no account found
      requestor: Single requestor object for the account
    """
    printername, account = self.parseURI(uri)
    # find requestor based on account
    requestor = self.findRequestorForAccount(urllib.unquote(account))
    if requestor == None:
    	return None, None 
    responseobj = requestor.doRequest('search?connection_status=ALL&client=webui&q=%s' % (printername))
    printername = urllib.unquote(printername)
    if 'printers' in responseobj and len(responseobj['printers']) > 0:
      for printerdetail in responseobj['printers']:
	if printername == printerdetail['name']:
	  return printerdetail['id'], requestor
    else:
      return None, None

  def getPrinterDetails(self, printerid):
    """Gets details about printer from Google

    Args:
      printerid: string, Google printer id
    Return:
      list: data from Google
    """
    return self.requestor.doRequest( 'printer?printerid=%s' % (  printerid) )

  def readFile(self, pathname):
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
	print('ERROR: Error reading %s\n%s', pathname, e)
      f.close()
      return s
    except IOError, e:
      print('ERROR: Error opening %s\n%s', pathname, e)
      return None

  def writeFile(self, file_name, data):
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
	status = False
      f.close()
    except IOError, e:
      status = False

    return status

  def base64Encode(self, pathname):
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
    data = self.readFile(pathname)

    # Convert binary data to base64 encoded data.
    header = 'data:%s;base64,' % file_type
    b64data = header + base64.b64encode(data)

    if self.writeFile(b64_pathname, b64data):
      return b64_pathname
    else:
      return None

  def encodeMultiPart(self, fields, files, file_type='application/xml'):
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
	lines.append('--' + self.BOUNDARY)
	lines.append('Content-Disposition: form-data; name="%s"' % key)
	lines.append('')  # blank line
	lines.append(str(value))
      for (key, filename, value) in files:
	lines.append('--' + self.BOUNDARY)
	lines.append(
	    'Content-Disposition: form-data; name="%s"; filename="%s"'
	    % (key, filename))
	lines.append('Content-Type: %s' % file_type)
	lines.append('')  # blank line
	lines.append(str(value))
      lines.append('--' + self.BOUNDARY + '--')
      lines.append('')  # blank line
      return self.CRLF.join(lines)
  
  def getCapabilities ( self, gcpid, cupsprintername ) :
    """Gets capabilities of printer and maps them against list

    Args:
      gcpid: printer id from google
      cupsprintername: name of the printer in cups
    Returns:
      List of capabilities
    """
    itemmapping = { 
		    'DefaultColorModel' : 'ns1:Colors',
		  }
    
    valuemapping = {		     # CUPS to GCP
		    'ns1:Colors' : {
				     'Gray' : 'Grey_K',
				     'RGB' : 'Color' ,
				     'CMYK' : 'Color' ,
				   }
		  }
    
    import cups
    connection = cups.Connection()
    cupsprinters = connection.getPrinters()
    capabilities = { "capabilities" : [] }
    
    for cupsprinter in cupsprinters:
      if cupsprinters[cupsprinter]['printer-info'] == cupsprintername:
	attrs = cups.PPD(connection.getPPD(cupsprinter)).attributes
	printerdetails = self.getPrinterDetails(gcpid)
	
	for mapping in itemmapping:
	  cupsitem = mapping 
	  gcpitem = itemmapping[mapping]
	  for capability in printerdetails['printers'][0]['capabilities']:
	    if capability['name'] == gcpitem:
	      for attr in attrs:
		if attr.name == cupsitem:
		  if attr.value in valuemapping[gcpitem]:
		    capabilities['capabilities'].append( { 'type' : capability['type'], 'name' : capability['name'], 'options' : [ { 'name' : valuemapping[gcpitem][attr.value] } ] } )
    return capabilities
      
  def submitJob(self, printerid, jobtype, jobfile, jobname, printername ):
    """Submit a job to printerid with content of dataUrl.

    Args:
      printerid: string, the printer id to submit the job to.
      jobtype: string, must match the dictionary keys in content and content_type.
      jobfile: string, points to source for job. Could be a pathname or id string.
      jobname: string, name of the print job ( usually page name ).
      printername: string, Google Cloud Print printer name.
    Returns:
      boolean: True = submitted, False = errors.
    """
    if jobtype == 'pdf':
      
      if not os.path.exists(jobfile):
	print("ERROR: PDF doesnt exist")
	return False
      b64file = self.base64Encode(jobfile)
      fdata = self.readFile(b64file)
      os.unlink(b64file)
      hsid = True
    elif jobtype in ['png', 'jpeg']:
      fdata = self.readFile(jobfile)
      if not os.path.exists(jobfile):
        print("ERROR: File doesnt exist")
        return False
    else:
      return False
    
    title = jobname
    content = {'pdf': fdata,
	      'jpeg': jobfile,
	      'png': jobfile,
	      }
    content_type = {'pdf': 'dataUrl',
		    'jpeg': 'image/jpeg',
		    'png': 'image/png',
		  }
    headers = [
      ('printerid', printerid),
      ('title', title),
      ('content', content[jobtype]),
      ('contentType', content_type[jobtype]),
      ('capabilities', json.dumps( self.getCapabilities(printerid, printername) ) )
    ]
    files = []
    edata = ""
    if jobtype in ['pdf', 'jpeg', 'png']:
      edata = self.encodeMultiPart(headers, files, file_type=content_type[jobtype])
    else:
      edata = self.encodeMultiPart(headers, files)
    
    responseobj = self.requestor.doRequest( 'submit', None, edata, self.BOUNDARY )
    try:
      if responseobj['success'] == True:
	return True
      else:
	print('ERROR: Print job %s failed with %s', jobtype, responseobj['message'])
	return False
	
    except Exception, error_msg:
      print('ERROR: Print job %s failed with %s', jobtype, error_msg)
      return False
