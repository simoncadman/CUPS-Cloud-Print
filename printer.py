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
import json, urllib, urllib2, os, mimetypes, base64, mimetools
from auth import Auth

class Printer():
  CLOUDPRINT_URL = 'http://www.google.com/cloudprint'
  BOUNDARY = mimetools.choose_boundary()
  CRLF = '\r\n'
  PROTOCOL = 'cloudprint://'
  requestors = None
  
  def __init__( self, requestors ):
    if isinstance(requestors, list):
      self.requestors = requestors
    else:
      self.requestors = [requestors]

  def getPrinters(self, proxy=None):
    allprinters = []
    for requestor in self.requestors:
      responseobj = requestor.doRequest('search?q=')
      if 'printers' in responseobj and len(responseobj['printers']) > 0:
	for printer in responseobj['printers']:
	  printer['account'] = requestor.getAccount()
	  allprinters.append(printer)
    return allprinters
  
  @staticmethod
  def printerNameToUri( account, printer ) :
    return Printer.PROTOCOL + urllib.quote(printer) + "/" + urllib.quote(account)

  @staticmethod
  def AddPrinter( printername, uri, connection ) :
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
      print("Added",printername)
    else:
      print("Error adding:",printername,result)
      return None
      
  @staticmethod
  def GetPrinter(printer, tokens, proxy=None):
      printer_id = None
      response = Auth.GetUrl('%s/search?q=%s' % (Printer.CLOUDPRINT_URL, printer), tokens)
      printer = urllib.unquote(printer)
      responseobj = json.loads(response)
      if 'printers' in responseobj and len(responseobj['printers']) > 0:
	for printerdetail in responseobj['printers']:
	  if printer == printerdetail['name']:
	    return printerdetail['id']
      else:
	return None

  @staticmethod
  def GetPrinterDetails(printerid, tokens, proxy=None):
      printer_id = None
      response = Auth.GetUrl('%s/printer?printerid=%s' % (Printer.CLOUDPRINT_URL, printerid), tokens)
      return json.loads(response)


  @staticmethod
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
	print('ERROR: Error reading %s\n%s', pathname, e)
      finally:
	f.close()
	return s
    except IOError, e:
      print('ERROR: Error opening %s\n%s', pathname, e)
      return None

  @staticmethod
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
	status = False
      finally:
	f.close()
    except IOError, e:
      status = False

    return status

  @staticmethod
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
    data = Printer.ReadFile(pathname)

    # Convert binary data to base64 encoded data.
    header = 'data:%s;base64,' % file_type
    b64data = header + base64.b64encode(data)

    if Printer.WriteFile(b64_pathname, b64data):
      return b64_pathname
    else:
      return None

  @staticmethod
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
	lines.append('--' + Printer.BOUNDARY)
	lines.append('Content-Disposition: form-data; name="%s"' % key)
	lines.append('')  # blank line
	lines.append(str(value))
      for (key, filename, value) in files:
	lines.append('--' + Printer.BOUNDARY)
	lines.append(
	    'Content-Disposition: form-data; name="%s"; filename="%s"'
	    % (key, filename))
	lines.append('Content-Type: %s' % file_type)
	lines.append('')  # blank line
	lines.append(str(value))
      lines.append('--' + Printer.BOUNDARY + '--')
      lines.append('')  # blank line
      return Printer.CRLF.join(lines)
  
  @staticmethod
  def getCapabilities (name, id, tokens) :
    # define mappings
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
      if cupsprinters[cupsprinter]['printer-info'] == name:
	attrs = cups.PPD(connection.getPPD(cupsprinter)).attributes
	printerdetails = Printer.GetPrinterDetails(id, tokens)
	
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
      
  @staticmethod
  def SubmitJob(printerid, jobtype, jobsrc, jobname, tokens, printername):
    """Submit a job to printerid with content of dataUrl.

    Args:
      printerid: string, the printer id to submit the job to.
      jobtype: string, must match the dictionary keys in content and content_type.
      jobsrc: string, points to source for job. Could be a pathname or id string.
    Returns:
      boolean: True = submitted, False = errors.
    """
    if jobtype == 'pdf':
      
      if not os.path.exists(jobsrc):
	print("ERROR: PDF doesnt exist")
	return False
      b64file = Printer.Base64Encode(jobsrc)
      fdata = Printer.ReadFile(b64file)
      os.unlink(b64file)
      hsid = True
    elif jobtype in ['png', 'jpeg']:
      fdata = Printer.ReadFile(jobsrc)
    else:
      fdata = None
    
    title = jobname
    content = {'pdf': fdata,
	      'jpeg': jobsrc,
	      'png': jobsrc,
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
		('capabilities', json.dumps( Printer.getCapabilities(printername, printerid, tokens) ) ) 
	      ]
    files = []
    if jobtype in ['pdf', 'jpeg', 'png']:
      edata = Printer.EncodeMultiPart(headers, files, file_type=content_type[jobtype])
    else:
      edata = Printer.EncodeMultiPart(headers, files)
    
    response = Auth.GetUrl('%s/submit' % Printer.CLOUDPRINT_URL, tokens, data=edata,
		      cookies=False, boundary=Printer.BOUNDARY)
    try:
      responseobj = json.loads(response)
      if responseobj['success'] == True:
	return True
      else:
	print('ERROR: Print job %s failed with %s', jobtype, responseobj['message'])
	return False
	
    except Exception as error_msg:
      print('ERROR: Print job %s failed with %s', jobtype, error_msg)
      return False
