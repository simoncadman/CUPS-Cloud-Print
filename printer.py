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
import json, urllib, os, mimetypes, base64, mimetools, re, hashlib, subprocess
from auth import Auth
from urlparse import urlparse

class Printer:
  BOUNDARY = mimetools.choose_boundary()
  CRLF = '\r\n'
  PROTOCOL = 'cloudprint://'
  requestors = None
  requestor = None
  cachedPrinterDetails = {}
  reservedCapabilityWords = [ 
                             'Duplex', 'Resolution', 'Attribute', 'Choice', 'ColorDevice', 'ColorModel', 'ColorProfile', 
                             'Copyright', 'CustomMedia', 'Cutter', 'Darkness', 'DriverType', 'FileName', 'Filter',
                             'Filter', 'Finishing', 'Font', 'Group', 'HWMargins', 'InputSlot', 'Installable',
                             'LocAttribute', 'ManualCopies', 'Manufacturer', 'MaxSize', 'MediaSize', 'MediaType',
                             'MinSize', 'ModelName', 'ModelNumber', 'Option', 'PCFileName', 'SimpleColorProfile',
                             'Throughput', 'UIConstraints', 'VariablePaperSize', 'Version', 'Color', 'Background', 
                             'Stamp', 'DestinationColorProfile'
                            ]
  
  def __init__( self, requestors ):
    """Create an instance of Printer, with authorised requestor

    Args:
      requestors: list or cloudprintrequestor instance, A list of requestors, or a single requestor to use for all Cloud Print requests.
    """
    if isinstance(requestors, list):
      self.requestors = requestors
    else:
      self.requestors = [requestors]

  def getCUPSPrintersForAccount(self, account):
      import cups
      connection = cups.Connection()
      cupsprinters = connection.getPrinters()
      accountPrinters = []
      for cupsprinter in cupsprinters:
          id, requestor = self.getPrinterIDByURI(cupsprinters[cupsprinter]['device-uri'])
          if id != None and requestor != None:
              if requestor.getAccount() == account:
                  accountPrinters.append(cupsprinters[cupsprinter])
      return accountPrinters, connection

  def getPrinters(self, fulldetails = False):
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
	  
	  # fetch all details - search doesnt return all capabilities
	  if fulldetails:
            self.requestor = requestor
            details = self.getPrinterDetails( printer['id'] )
            printer['fulldetails'] = details['printers'][0]
	  allprinters.append(printer)
    return allprinters
  
  def sanitizeText(self, text):
      return text.replace('/','-').replace(':','_').replace(';','_').replace(' ','_').encode('utf8', 'ignore')
  
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

  def addPrinter( self, printername, uri, connection, ppd=None ) :
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
      if ppd == None: # pragma: no cover
        ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:' + uri + ';'
        ppds = connection.getPPDs(ppd_device_id=ppdid)
        printerppdname, printerppd = ppds.popitem()
      else:
        printerppdname = ppd
      result = connection.addPrinter(name=printername,ppdname=printerppdname,info=printername,location='Google Cloud Print',device=uri)
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
    if printerid not in self.cachedPrinterDetails:
        printerdetails = self.requestor.doRequest( 'printer?printerid=%s' % (  printerid ) )
        self.cachedPrinterDetails[printerid] = printerdetails
    else:
        printerdetails = self.cachedPrinterDetails[printerid]
    return printerdetails

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
      except IOError, e: # pragma: no cover 
	print('ERROR: Error reading %s\n%s', pathname, e)
      f.close()
      return s
    except IOError, e: # pragma: no cover 
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
      except IOError, e: # pragma: no cover 
	status = False
      f.close()
    except IOError, e: # pragma: no cover 
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
      return None # pragma: no cover 

  def encodeMultiPart(self, fields, file_type='application/xml'):
      """Encodes list of parameters for HTTP multipart format.

      Args:
	fields: list of tuples containing name and value of parameters.
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
      lines.append('--' + self.BOUNDARY + '--')
      lines.append('')  # blank line
      return self.CRLF.join(lines)
  
  def getCapabilities ( self, gcpid, cupsprintername, overrideoptionsstring ) :
    """Gets capabilities of printer and maps them against list

    Args:
      gcpid: printer id from google
      cupsprintername: name of the printer in cups
      overrideoptionsstring: override for print job
    Returns:
      List of capabilities
    """
    overrideoptions = overrideoptionsstring.split(' ')
    import cups
    connection = cups.Connection()
    cupsprinters = connection.getPrinters()
    capabilities = { "capabilities" : [] }
    overridecapabilities = {}
    ignorecapabilities = [ 'Orientation' ]
    for optiontext in overrideoptions:
        if '=' in optiontext :
            optionparts = optiontext.split('=')
            option = optionparts[0]
            if option in ignorecapabilities:
                continue
            
            value = optionparts[1]
            overridecapabilities[option] = value
            
        # landscape
        if optiontext == 'landscape' or optiontext == 'nolandscape':
            overridecapabilities['Orientation'] = 'Landscape'
            
    overrideDefaultDefaults = { 'Duplex' : 'None' }
    
    for capability in overrideDefaultDefaults:
        if capability not in overridecapabilities:
            overridecapabilities[capability] = overrideDefaultDefaults[capability]
    
    attrs = cups.PPD(connection.getPPD(cupsprintername)).attributes
    for attr in attrs:
        if attr.name.startswith('Default'):
            # gcp setting, reverse back to GCP capability
            gcpname = None
            hashname = attr.name.replace('Default', '')
            
            # find item name from hashes
            details = self.getPrinterDetails( gcpid )
            fulldetails = details['printers'][0]
            gcpoption = None
            addedCapabilities = []
            for capability in fulldetails['capabilities']:
                if hashname == self.getInternalName(capability, 'capability'):
                    gcpname = capability['name']
                    for option in capability['options']:
                        internalCapability = self.getInternalName(option, 'option', gcpname, addedCapabilities)
                        addedCapabilities.append(internalCapability)
                        if attr.value == internalCapability:
                            gcpoption = option['name']
                            break
                    addedOptions = []
                    for overridecapability in overridecapabilities:
                        if 'Default' + overridecapability == attr.name:
                            selectedoption = overridecapabilities[overridecapability]
                            for option in capability['options']:
                                internalOption = self.getInternalName(option, 'option', gcpname, addedOptions)
                                addedOptions.append(internalOption)
                                if selectedoption == internalOption:
                                    gcpoption = option['name']
                                    break
                            break
                    break
            
            # hardcoded to feature type temporarily
            if gcpname != None and gcpoption != None:
                capabilities['capabilities'].append( { 'type' : 'Feature', 'name' : gcpname, 'options' : [ { 'name' : gcpoption } ] } )
    return capabilities
      
  def submitJob(self, printerid, jobtype, jobfile, jobname, printername, options="" ):
    """Submit a job to printerid with content of dataUrl.

    Args:
      printerid: string, the printer id to submit the job to.
      jobtype: string, must match the dictionary keys in content and content_type.
      jobfile: string, points to source for job. Could be a pathname or id string.
      jobname: string, name of the print job ( usually page name ).
      printername: string, Google Cloud Print printer name.
      options: string, key-value pair of options from print job.
    Returns:
      boolean: True = submitted, False = errors.
    """
    rotate = 0
    
    for optiontext in options.split(' '):
        
        # landscape
        if optiontext == 'landscape':
            # landscape
            rotate = 90
            
        # nolandscape - already rotates
        if optiontext == 'nolandscape':
            # rotate back
            rotate = 270
    
    if jobtype == 'pdf':
      if not os.path.exists(jobfile):
        print("ERROR: PDF doesnt exist")
        return False
      if rotate > 0:
        p = subprocess.Popen(['convert', '-density', '300x300', jobfile, '-rotate', str(rotate), jobfile], stdout=subprocess.PIPE)
        output = p.communicate()[0]
        result = p.returncode
        if result != 0:
            print("ERROR: Failed to rotate PDF")
            return False
        if not os.path.exists(jobfile):
            print("ERROR: PDF doesnt exist")
            return False
      b64file = self.base64Encode(jobfile)
      if b64file == None: # pragma: no cover 
        print("ERROR: Cannot write to file: " + b64file)
        return False
      fdata = self.readFile(b64file)
      os.unlink(b64file)
      hsid = True
    elif jobtype in ['png', 'jpeg']:
      if not os.path.exists(jobfile):
        print("ERROR: File doesnt exist")
        return False
      fdata = self.readFile(jobfile)
    else:
      print("ERROR: Unknown job type")
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
      ('capabilities', json.dumps( self.getCapabilities(printerid, printername, options ) ) )
    ]
    print('DEBUG: Capability headers are: %s', headers[4])
    edata = ""
    if jobtype in ['pdf', 'jpeg', 'png']:
      edata = self.encodeMultiPart(headers, file_type=content_type[jobtype])
    
    responseobj = self.requestor.doRequest( 'submit', None, edata, self.BOUNDARY )
    try:
      if responseobj['success'] == True:
	return True
      else:
	print('ERROR: Error response from Cloud Print for type %s: %s' % ( jobtype, responseobj['message'] ) )
	return False
	
    except Exception, error_msg: # pragma: no cover
      print('ERROR: Print job %s failed with %s' % ( jobtype, error_msg ))
      return False

  def getInternalName ( self, details, internalType, capabilityName = None, existingList = [] ) :
      returnValue = None
      fixedNameMap = {}
      reservedWords = self.reservedCapabilityWords
      
      # use fixed options for options we recognise
      if internalType == "option":
          # option
          if capabilityName == "psk:JobDuplexAllDocumentsContiguously":
            fixedNameMap['psk:OneSided'] = "None"
            fixedNameMap['psk:TwoSidedShortEdge'] = "DuplexTumble"
            fixedNameMap['psk:TwoSidedLongEdge'] = "DuplexNoTumble"
          if capabilityName == "psk:PageOrientation":
            fixedNameMap['psk:Landscape'] = "Landscape"
            fixedNameMap['psk:Portrait'] = "Portrait"
      else:
          # capability
          fixedNameMap['ns1:Colors']                                 = "ColorModel"
          fixedNameMap['ns1:PrintQualities']                         = "OutputMode"
          fixedNameMap['ns1:InputBins']                              = "InputSlot"
          fixedNameMap['psk:JobDuplexAllDocumentsContiguously']      = "Duplex"
          fixedNameMap['psk:PageOrientation']                        = "Orientation"
          
      for itemName in fixedNameMap:
        if details['name'] == itemName:
            returnValue = fixedNameMap[itemName]
            break
        
      if 'displayName' in details and len(details['displayName']) > 0:
        name = details['displayName']
      elif 'psk:DisplayName' in details and len(details['psk:DisplayName']) > 0:
        name = details['psk:DisplayName']
      else:
        name = details['name']
      
      sanitisedName = self.sanitizeText(name)
      
      if sanitisedName in reservedWords:
          sanitisedName = 'GCP_' + sanitisedName
      
      # only sanitise, no hash
      if returnValue == None and len(sanitisedName) <= 30 and sanitisedName.decode("utf-8", 'ignore').encode("ascii","ignore") == sanitisedName:
          returnValue = sanitisedName
      
      if returnValue == None:
        returnValue = hashlib.sha256(sanitisedName).hexdigest()[:7]
      
      if returnValue not in existingList:
        return returnValue
    
      origReturnValue = returnValue
    
      if "GCP_" + origReturnValue not in existingList:
        return "GCP_" + origReturnValue
       
      # max 100 rotations, prevent infinite loop
      for i in range(1,100):
          if returnValue in existingList:
            returnValue = "GCP_" + str(i) + "_" + origReturnValue
      
      # TODO: need to error if limit hit, or run out of chars allowed etc
      
      return returnValue