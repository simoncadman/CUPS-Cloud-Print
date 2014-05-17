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
import cups
import hashlib
import json
import locale
import logging
import mimetools
import os
import re
import urllib
import subprocess

from ccputils import Utils

class Printer(object):
    _PPD_TEMPLATE_HEAD = """*PPD-Adobe: "4.3"
*%%%%%%%% PPD file for Cloud Print with CUPS.
*FormatVersion: "4.3"
*FileVersion: "1.0"
*LanguageVersion: English
*LanguageEncoding: ISOLatin1
*cupsLanguages: \"%(language)s\"
*cupsFilter: "application/vnd.cups-postscript 100 -"
*cupsFilter: "application/vnd.cups-pdf 0 -"
*PCFileName: "ccp.ppd"
*Product: "(Google Cloud Print)"
*Manufacturer: "Google"
*ModelName: "Google Cloud Print"
*ShortNickName: "Google Cloud Print"
*NickName: "Google Cloud Print, 1.0"
*PSVersion: "(3010.000) 550"
*LanguageLevel: "3"
*ColorDevice: True
*DefaultColorSpace: RGB
*FileSystem: False
*Throughput: "1"
*LandscapeOrientation: Minus90
*TTRasterizer: Type42
*%% Driver-defined attributes...
*1284DeviceID: "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:%(uri)s;"
*OpenUI *PageSize/Media Size: PickOne
*%(language)s.Translation PageSize/Media Size: ""
*OrderDependency: 10 AnySetup *PageSize
*DefaultPageSize: %(defaultpapertype)s.Fullbleed
*PageSize Letter.Fullbleed/US Letter: "<</PageSize[612 792]/ImagingBBox null>>setpagedevice"
*%(language)s.PageSize Letter.Fullbleed/US Letter: ""
*PageSize Legal.Fullbleed/US Legal: "<</PageSize[612 1008]/ImagingBBox null>>setpagedevice"
*%(language)s.PageSize Legal.Fullbleed/US Legal: ""
*PageSize A4.Fullbleed/A4: "<</PageSize[595 842]/ImagingBBox null>>setpagedevice"
*%(language)s.PageSize A4.Fullbleed/A4: ""
*CloseUI: *PageSize
*OpenUI *PageRegion/Page Region: PickOne
*%(language)s.Translation PageRegion/Page Region: ""
*OrderDependency: 10 AnySetup *PageRegion
*DefaultPageRegion: %(defaultpapertype)s.Fullbleed
*PageRegion Letter.Fullbleed/US Letter: "<</PageSize[612 792]/ImagingBBox null>>setpagedevice"
*%(language)s.PageRegion Letter.Fullbleed/US Letter: ""
*PageRegion Legal.Fullbleed/US Legal: "<</PageSize[612 1008]/ImagingBBox null>>setpagedevice"
*%(language)s.PageRegion Legal.Fullbleed/US Legal: ""
*PageRegion A4.Fullbleed/A4: "<</PageSize[595 842]/ImagingBBox null>>setpagedevice"
*%(language)s.PageRegion A4.Fullbleed/A4: ""
*CloseUI: *PageRegion
*DefaultImageableArea: %(defaultpapertype)s.Fullbleed
*ImageableArea Letter.Fullbleed/US Letter: "0 0 612 792"
*ImageableArea Legal.Fullbleed/US Legal: "0 0 612 1008"
*ImageableArea A4.Fullbleed/A4: "0 0 595 842"
*DefaultPaperDimension: %(defaultpapertype)s.Fullbleed
*PaperDimension Letter.Fullbleed/US Letter: "612 792"
*PaperDimension Legal.Fullbleed/US Legal: "612 1008"
*PaperDimension A4.Fullbleed/A4: "595 842"
"""

    _PPD_TEMPLATE_FOOT = """*DefaultFont: Courier
*Font AvantGarde-Book: Standard "(1.05)" Standard ROM
*Font AvantGarde-BookOblique: Standard "(1.05)" Standard ROM
*Font AvantGarde-Demi: Standard "(1.05)" Standard ROM
*Font AvantGarde-DemiOblique: Standard "(1.05)" Standard ROM
*Font Bookman-Demi: Standard "(1.05)" Standard ROM
*Font Bookman-DemiItalic: Standard "(1.05)" Standard ROM
*Font Bookman-Light: Standard "(1.05)" Standard ROM
*Font Bookman-LightItalic: Standard "(1.05)" Standard ROM
*Font Courier: Standard "(1.05)" Standard ROM
*Font Courier-Bold: Standard "(1.05)" Standard ROM
*Font Courier-BoldOblique: Standard "(1.05)" Standard ROM
*Font Courier-Oblique: Standard "(1.05)" Standard ROM
*Font Helvetica: Standard "(1.05)" Standard ROM
*Font Helvetica-Bold: Standard "(1.05)" Standard ROM
*Font Helvetica-BoldOblique: Standard "(1.05)" Standard ROM
*Font Helvetica-Narrow: Standard "(1.05)" Standard ROM
*Font Helvetica-Narrow-Bold: Standard "(1.05)" Standard ROM
*Font Helvetica-Narrow-BoldOblique: Standard "(1.05)" Standard ROM
*Font Helvetica-Narrow-Oblique: Standard "(1.05)" Standard ROM
*Font Helvetica-Oblique: Standard "(1.05)" Standard ROM
*Font NewCenturySchlbk-Bold: Standard "(1.05)" Standard ROM
*Font NewCenturySchlbk-BoldItalic: Standard "(1.05)" Standard ROM
*Font NewCenturySchlbk-Italic: Standard "(1.05)" Standard ROM
*Font NewCenturySchlbk-Roman: Standard "(1.05)" Standard ROM
*Font Palatino-Bold: Standard "(1.05)" Standard ROM
*Font Palatino-BoldItalic: Standard "(1.05)" Standard ROM
*Font Palatino-Italic: Standard "(1.05)" Standard ROM
*Font Palatino-Roman: Standard "(1.05)" Standard ROM
*Font Symbol: Special "(001.005)" Special ROM
*Font Times-Bold: Standard "(1.05)" Standard ROM
*Font Times-BoldItalic: Standard "(1.05)" Standard ROM
*Font Times-Italic: Standard "(1.05)" Standard ROM
*Font Times-Roman: Standard "(1.05)" Standard ROM
*Font ZapfChancery-MediumItalic: Standard "(1.05)" Standard ROM
*Font ZapfDingbats: Special "(001.005)" Special ROM
*% End of cloudprint.ppd, 04169 bytes."""

    _PROTOCOL = 'cloudprint://'
    _BACKEND_DESCRIPTION =\
        'network %s "%s" "Google Cloud Print" "MFG:Google;MDL:Cloud Print;DES:GoogleCloudPrint;"'

    _LIST_FORMAT = '"cupscloudprint:%s:%s-%s.ppd" en "Google" "%s (%s)" "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:%s;"'

    _RESERVED_CAPABILITY_WORDS = set((
        'Duplex', 'Resolution', 'Attribute', 'Choice', 'ColorDevice', 'ColorModel', 'ColorProfile',
        'Copyright', 'CustomMedia', 'Cutter', 'Darkness', 'DriverType', 'FileName', 'Filter',
        'Filter', 'Finishing', 'Font', 'Group', 'HWMargins', 'InputSlot', 'Installable',
        'LocAttribute', 'ManualCopies', 'Manufacturer', 'MaxSize', 'MediaSize', 'MediaType',
        'MinSize', 'ModelName', 'ModelNumber', 'Option', 'PCFileName', 'SimpleColorProfile',
        'Throughput', 'UIConstraints', 'VariablePaperSize', 'Version', 'Color', 'Background',
        'Stamp', 'DestinationColorProfile'
    ))

    def __init__(self, fields, requestor):
        self._fields = fields
        self._requestor = requestor

    def getAccount(self):
        return self._requestor.getAccount()

    def getRequestor(self):
        return self._requestor

    def _getMimeBoundary(self):
        if not hasattr(self, '_mime_boundary'):
            self._mime_boundary = mimetools.choose_boundary()
        return self._mime_boundary

    def __getitem__(self, key):
        if key == 'capabilities' and key not in self._fields:
            self._fields = self._fetchDetails()
            if key not in self._fields:
                # Make sure to only fetch details once.
                self._fields[key] = None

        return self._fields[key]

    def __contains__(self, key):
        return key in self._fields

    def _fetchDetails(self):
        responseobj = self._requestor.printer(self['id'])
        return responseobj['printers'][0]

    def getURI(self):
        """Generates a URI for the Cloud Print Printer

        Returns:
          string: URI for the printer
        """
        account = urllib.quote(self.getAccount().encode('ascii', 'replace'))
        printer_id = urllib.quote(self['id'].encode('ascii', 'replace'))
        return "%s%s/%s" % (self._PROTOCOL, account, printer_id)

    def getListDescription(self):
        printerName = self['name']
        if 'displayName' in self:
            printerName = self['displayName']
        return '%s - %s - %s' % (
            printerName.encode('ascii', 'replace'), self.getURI(), self.getAccount())

    def getBackendDescription(self):
        return self._BACKEND_DESCRIPTION % (self.getURI(), self['name'])

    def getCUPSListDescription(self):
        account_no_spaces = self.getAccount().encode('ascii', 'replace').replace(' ', '-')
        name_no_spaces = self['name'].encode('ascii', 'replace').replace(' ', '-')
        id = self['id'].encode('ascii', 'replace').replace(' ', '-')
        name = self['name'].encode('ascii', 'replace')
        return self._LIST_FORMAT %\
            (account_no_spaces, name_no_spaces, id, name, self.getAccount(), self.getURI())

    def getPPDName(self):
        return 'cupscloudprint:%s:%s-%s.ppd' % (
            self.getAccount().encode('ascii', 'replace').replace(' ', '-'),
            self['name'].encode('ascii', 'replace').replace(' ', '-'),
            self['id'].encode('ascii', 'replace').replace(' ', '-'))

    def generatePPD(self):
        """Generates a PPD string for this printer."""
        defaultlocale = locale.getdefaultlocale()
        language = Utils.GetLanguage(defaultlocale)
        defaultpapertype = Utils.GetDefaultPaperType(defaultlocale)
        ppd = self._PPD_TEMPLATE_HEAD % \
            {'language': language, 'defaultpapertype': defaultpapertype, 'uri': self.getURI()}
        if self['capabilities'] is not None:
            addedCapabilities = []
            for capability in self['capabilities']:
                originCapabilityName = None
                internalCapabilityName = \
                    self._getInternalName(capability, 'capability', None, addedCapabilities)
                addedCapabilities.append(internalCapabilityName)
                if 'displayName' in capability and len(capability['displayName']) > 0:
                    originCapabilityName = self._sanitizeText(capability['displayName'])
                elif 'psk:DisplayName' in capability and len(capability['psk:DisplayName']) > 0:
                    originCapabilityName = self._sanitizeText(capability['psk:DisplayName'])
                else:
                    originCapabilityName = self._sanitizeText(capability['name'])
                if capability['type'] == 'Feature':
                    ppd += '*OpenUI *%s/%s: PickOne\n' % \
                        (internalCapabilityName, internalCapabilityName)
                    # translation of capability, allows use of 8
                    # bit chars
                    ppd += '*%s.Translation %s/%s: ""\n' % \
                        (language, internalCapabilityName, originCapabilityName)
                    addedOptions = []
                    for option in capability['options']:
                        originOptionName = None
                        if 'displayName' in option and len(option['displayName']) > 0:
                            originOptionName = self._sanitizeText(option['displayName'])
                        elif 'psk:DisplayName' in option and len(option['psk:DisplayName']) > 0:
                            originOptionName = self._sanitizeText(option['psk:DisplayName'])
                        else:
                            originOptionName = self._sanitizeText(option['name'])
                        internalOptionName = self._getInternalName(option, 'option', capability['name'], addedOptions)
                        addedOptions.append(internalOptionName)
                        if 'default' in option and option['default']:
                            ppd += '*Default%s: %s\n' % (internalCapabilityName, internalOptionName)
                        ppd += '*%s %s:%s\n' % \
                            (internalCapabilityName, internalOptionName, internalOptionName)
                        # translation of option, allows use of 8
                        # bit chars
                        value = ''
                        if 'ppd:value' in option:
                            value = option['ppd:value']
                        ppd += '*%s.%s %s/%s: "%s"\n' % \
                            (language, internalCapabilityName, internalOptionName, originOptionName, value)

                    ppd += '*CloseUI: *%s\n' % internalCapabilityName

        ppd += self._PPD_TEMPLATE_FOOT
        return ppd

    @staticmethod
    def _sanitizeText(text):
        return re.sub(r'(:|;| )', '_', text).replace('/', '-').encode('utf8', 'ignore')

    @staticmethod
    def _getInternalName(details, internalType, capabilityName=None, existingList=[]):
        returnValue = None
        fixedNameMap = {}

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
            fixedNameMap['ns1:Colors'] = "ColorModel"
            fixedNameMap['ns1:PrintQualities'] = "OutputMode"
            fixedNameMap['ns1:InputBins'] = "InputSlot"
            fixedNameMap['psk:JobDuplexAllDocumentsContiguously'] = "Duplex"
            fixedNameMap['psk:PageOrientation'] = "Orientation"

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

        sanitisedName = Printer._sanitizeText(name)

        if sanitisedName in Printer._RESERVED_CAPABILITY_WORDS:
            sanitisedName = 'GCP_' + sanitisedName

        # only sanitise, no hash
        if returnValue is None and\
            len(sanitisedName) <= 30 and\
            sanitisedName.decode("utf-8", 'ignore').encode("ascii", "ignore") == sanitisedName:
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

    def _encodeMultiPart(self, fields, file_type='application/xml'):
        """Encodes list of parameters for HTTP multipart format.

        Args:
          fields: list of tuples containing name and value of parameters.
          file_type: string if file type different than application/xml.
        Returns:
          A string to be sent as data for the HTTP post request.
        """
        lines = []
        for (key, value) in fields:
            lines.append('--' + self._getMimeBoundary())
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append('')  # blank line
            lines.append(str(value))
        lines.append('--%s--' % self._getMimeBoundary())
        lines.append('')  # blank line
        return '\r\n'.join(lines)

    @staticmethod
    def _getOverrideCapabilities(overrideoptionsstring):
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

    @staticmethod
    def _getCapabilitiesDict(attrs, printercapabilities, overridecapabilities):
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
                    if hashname == Printer._getInternalName(capability, 'capability'):
                        gcpname = capability['name']
                        for option in capability['options']:
                            internalCapability = Printer._getInternalName(option, 'option', gcpname, addedCapabilities)
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
                                    internalOption = Printer._getInternalName(option, 'option', gcpname, addedOptions)
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

    @staticmethod
    def _attrListToArray(attrs):
        return ({'name': attr.name, 'value': attr.value} for attr in attrs)

    def _getCapabilities(self, cupsprintername, overrideoptionsstring):
        """Gets capabilities of printer and maps them against list

        Args:
          overrideoptionsstring: override for print job
        Returns:
          List of capabilities
        """
        connection = cups.Connection()
        overridecapabilities = self._getOverrideCapabilities(overrideoptionsstring)
        overrideDefaultDefaults = {'Duplex': 'None'}

        for capability in overrideDefaultDefaults:
            if capability not in overridecapabilities:
                overridecapabilities[capability] = overrideDefaultDefaults[capability]
        attrs = cups.PPD(connection.getPPD(cupsprintername)).attributes
        attrArray = self._attrListToArray(attrs)
        return self._getCapabilitiesDict(attrArray, self['capabilities'], overridecapabilities)

    def submitJob(self, jobtype, jobfile, jobname, cupsprintername, options=""):
        """Submit a job to printerid with content of dataUrl.

        Args:
          jobtype: string, must match the dictionary keys in content and content_type.
          jobfile: string, points to source for job. Could be a pathname or id string.
          jobname: string, name of the print job ( usually page name ).
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

        if jobname == "":
            title = "Untitled page"
        else:
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
            ('printerid', self['id']),
            ('title', title),
            ('content', content[jobtype]),
            ('contentType', content_type[jobtype]),
            ('capabilities', json.dumps(self._getCapabilities(cupsprintername, options)))
        ]
        logging.info('Capability headers are: %s', headers[4])
        data = self._encodeMultiPart(headers, content_type[jobtype])

        responseobj = self.getRequestor().submit(data, self._getMimeBoundary())
        try:
            if responseobj['success']:
                return True
            else:
                print 'ERROR: Error response from Cloud Print for type %s: %s' %\
                    (jobtype, responseobj['message'])
                return False

        except Exception as error_msg:
            print 'ERROR: Print job %s failed with %s' % (jobtype, error_msg)
            return False

