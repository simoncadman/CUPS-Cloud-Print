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
import os
import mimetools
import re
import hashlib
import subprocess
import logging
from auth import Auth
from urlparse import urlparse
from ccputils import Utils


class PrinterManager:
    BOUNDARY = mimetools.choose_boundary()
    CRLF = '\r\n'
    PROTOCOL = 'cloudprint://'
    requestors = None
    requestor = None
    cachedPrinterDetails = {}
    reservedCapabilityWords = set((
        'Duplex', 'Resolution', 'Attribute', 'Choice', 'ColorDevice', 'ColorModel', 'ColorProfile',
        'Copyright', 'CustomMedia', 'Cutter', 'Darkness', 'DriverType', 'FileName', 'Filter',
        'Filter', 'Finishing', 'Font', 'Group', 'HWMargins', 'InputSlot', 'Installable',
        'LocAttribute', 'ManualCopies', 'Manufacturer', 'MaxSize', 'MediaSize', 'MediaType',
        'MinSize', 'ModelName', 'ModelNumber', 'Option', 'PCFileName', 'SimpleColorProfile',
        'Throughput', 'UIConstraints', 'VariablePaperSize', 'Version', 'Color', 'Background',
        'Stamp', 'DestinationColorProfile'
    ))
    URIFormatLatest = 1
    URIFormat20140307 = 2
    URIFormat20140210 = 3

    def __init__(self, requestors):
        """Create an instance of PrinterManager, with authorised requestor

        Args:
          requestors: list or cloudprintrequestor instance, A list of
          requestors, or a single requestor to use for all Cloud Print
          requests.
        """
        if requestors is not None:
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
            if id is not None and requestor is not None:
                if requestor.getAccount() == account:
                    accountPrinters.append(cupsprinters[cupsprinter])
        return accountPrinters, connection

    def getPrinters(self, fulldetails=False, accountName=None):
        """Fetch a list of printers

        Returns:
          list: list of printers for the accounts.
        """
        allprinters = []
        for requestor in self.requestors:
            if accountName is not None and accountName != requestor.getAccount():
                continue

            responseobj = requestor.doRequest(
                'search?connection_status=ALL&client=webui')

            if 'printers' in responseobj and len(responseobj['printers']) > 0:
                for printer in responseobj['printers']:
                    printer['account'] = requestor.getAccount()

                    # fetch all details - search doesnt return all capabilities
                    if fulldetails:
                        self.requestor = requestor
                        details = self.getPrinterDetails(printer['id'])
                        printer['fulldetails'] = details['printers'][0]
                    allprinters.append(printer)
        return allprinters

    def sanitizeText(self, text):
        return text.replace('/', '-').replace(':', '_').replace(';', '_').replace(' ', '_') \
            .encode('utf8', 'ignore')

    def printerNameToUri(self, account, printerid):
        """Generates a URI for the Cloud Print Printer

        Args:
          account: string, account name reference
          printer: string, name of printer from Google Cloud Print

        Returns:
          string: URI for the printer
        """
        account = urllib.quote(account.encode('ascii', 'replace'))
        printer_id = urllib.quote(printerid.encode('ascii', 'replace'))
        return "%s%s/%s" % (self.PROTOCOL, account, printer_id)

    def sanitizePrinterName(self, name):
        """Sanitizes printer name for CUPS

        Args:
          name: string, name of printer from Google Cloud Print

        Returns:
          string: CUPS-friendly name for the printer
        """
        return re.sub('[^a-zA-Z0-9\-_]', '', name.encode('ascii', 'replace').replace(' ', '_'))

    def addPrinter(self, printername, uri, connection, ppd=None):
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
            if ppd is None:
                ppdid = 'MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:' + uri + ';'
                ppds = connection.getPPDs(ppd_device_id=ppdid)
                printerppdname, printerppd = ppds.popitem()
            else:
                printerppdname = ppd
            result = connection.addPrinter(
                name=printername, ppdname=printerppdname, info=printername,
                location='Google Cloud Print', device=uri)
            connection.enablePrinter(printername)
            connection.acceptJobs(printername)
            connection.setPrinterShared(printername, False)
        except Exception as error:
            result = error
        if result is None:
            print "Added " + printername
            return True
        else:
            print "Error adding: " + printername, result
            return False

    def parseURI(self, uristring):
        """Parses a CUPS Cloud Print URI

        Args:
          uristring: string, uri of the Cloud Print device

        Returns:
          string: account name
          string: google cloud print printer id
        """
        uri = urlparse(uristring)
        pathparts = uri.path.split('/')
        printerId = pathparts[1]
        return uri.netloc, printerId

    def parseLegacyURI(self, uristring, requestors):
        """Parses previous CUPS Cloud Print URIs, only used for upgrades

        Args:
          uristring: string, uri of the Cloud Print device

        Returns:
          string: account name
          string: google cloud print printer name
          string: google cloud print printer id
          int: format id
        """
        printerName = None
        accountName = None
        printerId = None
        uri = urlparse(uristring)
        pathparts = uri.path.strip('/').split('/')
        if len(pathparts) == 2:
            formatId = PrinterManager.URIFormat20140307
            printerId = urllib.unquote(pathparts[1])
            accountName = urllib.unquote(pathparts[0])
            printerName = urllib.unquote(uri.netloc)
        else:
            if urllib.unquote(uri.netloc) not in Auth.GetAccountNames(requestors):
                formatId = PrinterManager.URIFormat20140210
                printerName = urllib.unquote(uri.netloc)
                accountName = urllib.unquote(pathparts[0])
            else:
                formatId = PrinterManager.URIFormatLatest
                printerId = urllib.unquote(pathparts[0])
                printerName = None
                accountName = urllib.unquote(uri.netloc)

        return accountName, printerName, printerId, formatId

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
        account, printerid = self.parseURI(uri)
        # find requestor based on account
        requestor = self.findRequestorForAccount(urllib.unquote(account))
        if requestor is None:
            return None, None

        if printerid is not None:
            return printerid, requestor
        else:
            return None, None

    def getPrinterIDByDetails(self, account, printername, printerid):
        """Gets printer id and requestor by printer

        Args:
          uri: string, printer uri
        Return:
          printer id: Single requestor object for the account, or None if no account found
          requestor: Single requestor object for the account
        """
        # find requestor based on account
        requestor = self.findRequestorForAccount(urllib.unquote(account))
        if requestor is None:
            return None, None

        if printerid is not None:
            return printerid, requestor
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
            printerdetails = self.requestor.doRequest(
                'printer?printerid=%s' % (printerid))
            self.cachedPrinterDetails[printerid] = printerdetails
        else:
            printerdetails = self.cachedPrinterDetails[printerid]
        return printerdetails

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

    def getOverrideCapabilities(self, overrideoptionsstring):
        overrideoptions = overrideoptionsstring.split(' ')
        overridecapabilities = {}

        ignorecapabilities = ['Orientation']
        for optiontext in overrideoptions:
            if '=' in optiontext:
                optionparts = optiontext.split('=')
                option = optionparts[0]
                if option in ignorecapabilities:
                    continue

                value = optionparts[1]
                overridecapabilities[option] = value

            # landscape
            if optiontext == 'landscape' or optiontext == 'nolandscape':
                overridecapabilities['Orientation'] = 'Landscape'

        return overridecapabilities

    def getCapabilitiesDict(
            self, attrs, printercapabilities, overridecapabilities):
        capabilities = {"capabilities": []}
        for attr in attrs:
            if attr['name'].startswith('Default'):
                # gcp setting, reverse back to GCP capability
                gcpname = None
                hashname = attr['name'].replace('Default', '')

                # find item name from hashes
                gcpoption = None
                addedCapabilities = []
                for capability in printercapabilities:
                    if hashname == self.getInternalName(capability, 'capability'):
                        gcpname = capability['name']
                        for option in capability['options']:
                            internalCapability = self.getInternalName(
                                option, 'option', gcpname, addedCapabilities)
                            addedCapabilities.append(internalCapability)
                            if attr['value'] == internalCapability:
                                gcpoption = option['name']
                                break
                        addedOptions = []
                        for overridecapability in overridecapabilities:
                            if 'Default' + overridecapability == attr['name']:
                                selectedoption = overridecapabilities[
                                    overridecapability]
                                for option in capability['options']:
                                    internalOption = self.getInternalName(
                                        option, 'option', gcpname, addedOptions)
                                    addedOptions.append(internalOption)
                                    if selectedoption == internalOption:
                                        gcpoption = option['name']
                                        break
                                break
                        break

                # hardcoded to feature type temporarily
                if gcpname is not None and gcpoption is not None:
                    capabilities['capabilities'].append(
                        {'type': 'Feature', 'name': gcpname, 'options': [{'name': gcpoption}]})
        return capabilities

    def attrListToArray(self, attrs):
        attrArray = []
        for attr in attrs:
            attrArray.append({'name': attr.name, 'value': attr.value})
        return attrArray

    def getCapabilities(self, gcpid, cupsprintername, overrideoptionsstring):
        """Gets capabilities of printer and maps them against list

        Args:
          gcpid: printer id from google
          cupsprintername: name of the printer in cups
          overrideoptionsstring: override for print job
        Returns:
          List of capabilities
        """
        import cups
        connection = cups.Connection()
        overridecapabilities = self.getOverrideCapabilities(
            overrideoptionsstring)
        overrideDefaultDefaults = {'Duplex': 'None'}

        details = self.getPrinterDetails(gcpid)
        fulldetails = details['printers'][0]
        for capability in overrideDefaultDefaults:
            if capability not in overridecapabilities:
                overridecapabilities[
                    capability] = overrideDefaultDefaults[capability]

        attrs = cups.PPD(connection.getPPD(cupsprintername)).attributes
        attrArray = self.attrListToArray(attrs)
        return (
            self.getCapabilitiesDict(
                attrArray,
                fulldetails['capabilities'],
                overridecapabilities)
        )

    def submitJob(self, printerid, jobtype, jobfile,
                  jobname, printername, options=""):
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
                print "ERROR: PDF doesnt exist"
                return False
            if rotate > 0:
                p = subprocess.Popen(
                    ['convert', '-density', '300x300', jobfile.lstrip('-'),
                     '-rotate', str(rotate), jobfile.lstrip('-')], stdout=subprocess.PIPE)
                output = p.communicate()[0]
                result = p.returncode
                if result != 0:
                    print "ERROR: Failed to rotate PDF"
                    logging.error("Failed to rotate pdf: " +
                                  str(['convert', '-density', '300x300', jobfile.lstrip('-'), '-rotate', str(rotate), jobfile.lstrip('-')]))
                    logging.error(output)
                    return False
                if not os.path.exists(jobfile):
                    print "ERROR: PDF doesnt exist"
                    return False
            b64file = Utils.Base64Encode(jobfile)
            if b64file is None:
                print "ERROR: Cannot write to file: " + jobfile + ".b64"
                return False
            fdata = Utils.ReadFile(b64file)
            os.unlink(b64file)
        elif jobtype in ['png', 'jpeg']:
            if not os.path.exists(jobfile):
                print "ERROR: File doesnt exist"
                return False
            fdata = Utils.ReadFile(jobfile)
        else:
            print "ERROR: Unknown job type"
            return False

        title = jobname
        if title == "":
            title = "Untitled page"

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
            ('capabilities',
             json.dumps(self.getCapabilities(printerid, printername, options)))
        ]
        logging.info('Capability headers are: %s', headers[4])
        edata = ""
        if jobtype in ['pdf', 'jpeg', 'png']:
            edata = self.encodeMultiPart(
                headers, file_type=content_type[jobtype])

        responseobj = self.requestor.doRequest(
            'submit', None, edata, self.BOUNDARY)
        try:
            if responseobj['success']:
                return True
            else:
                print 'ERROR: Error response from Cloud Print for type %s: %s' % (jobtype, responseobj['message'])
                return False

        except Exception as error_msg:
            print 'ERROR: Print job %s failed with %s' % (jobtype, error_msg)
            return False

    def getInternalName(self, details, internalType,
                        capabilityName=None, existingList=[]):
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
            fixedNameMap[
                'ns1:Colors'] = "ColorModel"
            fixedNameMap[
                'ns1:PrintQualities'] = "OutputMode"
            fixedNameMap[
                'ns1:InputBins'] = "InputSlot"
            fixedNameMap[
                'psk:JobDuplexAllDocumentsContiguously'] = "Duplex"
            fixedNameMap[
                'psk:PageOrientation'] = "Orientation"

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
        if returnValue is None and len(sanitisedName) <= 30 and sanitisedName.decode("utf-8", 'ignore').encode("ascii", "ignore") == sanitisedName:
            returnValue = sanitisedName

        if returnValue is None:
            returnValue = hashlib.sha256(sanitisedName).hexdigest()[:7]

        if returnValue not in existingList:
            return returnValue

        origReturnValue = returnValue

        if "GCP_" + origReturnValue not in existingList:
            return "GCP_" + origReturnValue

        # max 100 rotations, prevent infinite loop
        for i in range(1, 100):
            if returnValue in existingList:
                returnValue = "GCP_" + str(i) + "_" + origReturnValue

        # TODO: need to error if limit hit, or run out of chars allowed etc

        return returnValue

    def getBackendDescription(self):
        return "network cloudprint \"Unknown\" \"Google Cloud Print\""

    def getListDescription(self, foundprinter):
        printerName = foundprinter['name']
        if 'displayName' in foundprinter:
            printerName = foundprinter['displayName']
        return (
            printerName.encode(
                'ascii',
                'replace') + ' - ' + self.printerNameToUri(foundprinter['account'],
                                                           foundprinter['id']) + " - " + foundprinter['account']
        )

    def getBackendDescriptionForPrinter(self, foundprinter):
        return (
            "network " + self.printerNameToUri(foundprinter['account'], foundprinter['id']) + " " + "\"" +
            foundprinter[
                'name'] + "\" \"Google Cloud Print\"" + " \"MFG:Google;MDL:Cloud Print;DES:GoogleCloudPrint;\""
        )