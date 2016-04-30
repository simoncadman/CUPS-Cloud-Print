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
import re
import urllib
import subprocess
import unicodedata
import sys

from ccputils import Utils


class Printer(object):
    _PPD_TEMPLATE_HEAD = """*PPD-Adobe: "4.3"
*%%%%%%%% PPD file for Cloud Print with CUPS.
*FormatVersion: "4.3"
*FileVersion: "1.0"
*LanguageVersion: English
*LanguageEncoding: ISOLatin1
*cupsLanguages: "%(language)s"
*cupsFilter: "application/vnd.cups-postscript 100 -"
*cupsFilter: "application/vnd.cups-pdf 0 -"
*PCFileName: "%(ppdname)s"
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
*1284DeviceID: "%(ieee1284)s;"
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

    _BACKEND_DESCRIPTION = 'network %s "%s" "%s" "%s"'
    _BACKEND_DESCRIPTION_PLUS_LOCATION = 'network %s "%s" "%s @ %s" "%s" "%s"'

    _IEEE_1284 = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:%s'

    _DRIVER_DESCRIPTION = '"%s" en "Google" "%s (%s)" "%s"'

    _PPD_NAME = 'cupscloudprint:%s:%s.ppd'

    _RESERVED_CAPABILITY_WORDS = set((
        'Duplex', 'Resolution', 'Attribute', 'Choice', 'ColorDevice', 'ColorModel', 'ColorProfile',
        'Copyright', 'CustomMedia', 'Cutter', 'Darkness', 'DriverType', 'FileName', 'Filter',
        'Filter', 'Finishing', 'Font', 'Group', 'HWMargins', 'InputSlot', 'Installable',
        'LocAttribute', 'ManualCopies', 'Manufacturer', 'MaxSize', 'MediaSize', 'MediaType',
        'MinSize', 'ModelName', 'ModelNumber', 'Option', 'PCFileName', 'SimpleColorProfile',
        'Throughput', 'UIConstraints', 'VariablePaperSize', 'Version', 'Color', 'Background',
        'Stamp', 'DestinationColorProfile', 'JCLToPDFInterpreter', 'APAutoSetupTool',
        'APDialogExtension', 'APHelpBook', 'APICADriver', 'APPrinterIconPath',
        'APPrinterLowInkTool', 'APPrinterPreset', 'APPrinterUtilityPath', 'APScannerOnly',
        'APScanAppBundleID'
    ))

    _RESERVED_CAPABILITY_PREFIXES = (
        'cups'
    )

    _FIXED_OPTION_MAPPINGS = {"psk:JobDuplexAllDocumentsContiguously":
                              {'psk:OneSided': "None",
                                  'psk:TwoSidedShortEdge': "DuplexTumble",
                                  'psk:TwoSidedLongEdge': "DuplexNoTumble"},
                              "psk:PageOrientation":
                              {'psk:Landscape': "Landscape",
                               'psk:Portrait': "Portrait"}
                              }

    _FIXED_CAPABILITY_MAPPINGS = {'ns1:Colors': "ColorModel",
                                  'ns1:PrintQualities': "OutputMode",
                                  'ns1:InputBins': "InputSlot",
                                  'psk:JobDuplexAllDocumentsContiguously': "Duplex",
                                  'psk:PageOrientation': "Orientation"}

    _CONVERTCOMMAND = 'convert'

    _IGNORED_CAPABILITIES = [
        'supported_content_type',
        'vendor_capability'
    ]

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
        """Generates a URI for the Cloud Print Printer.

        Returns:
          URI for the printer
        """
        account = urllib.quote(self.getAccount().encode('ascii', 'replace'))
        printer_id = urllib.quote(self['id'].encode('ascii', 'replace'))
        return "%s%s/%s" % (Utils._PROTOCOL, account, printer_id)

    def getListDescription(self):
        return '%s - %s - %s' % (
            self.getDisplayName().encode('ascii', 'replace'), self.getURI(), self.getAccount())

    def getLocation(self):
        """Gets the location of the printer, or '' if location not available."""

        # Look for hints of a location tag.
        if 'tags' in self:
            for tag in self['tags']:
                if '=' not in tag:
                    continue
                key, value = tag.split('=', 1)
                if 'location' in key:
                    return value

        return ''

    def getCUPSBackendDescription(self):
        display_name = self.getDisplayName()

        location = self.getLocation()
        if location:
            return self._BACKEND_DESCRIPTION_PLUS_LOCATION % (
                self.getURI(), display_name, display_name, location, self.getIEEE1284(), location)
        else:
            return self._BACKEND_DESCRIPTION % (
                self.getURI(), display_name, display_name, self.getIEEE1284())

    def getCUPSDriverDescription(self):
        name = self.getDisplayName().encode('ascii', 'replace')
        return self._DRIVER_DESCRIPTION % (
            self.getPPDName(), name, self.getAccount(), self.getIEEE1284())

    def getIEEE1284(self):
        return self._IEEE_1284 % self.getURI()

    def getDisplayName(self):
        """Gets a name that carbon-based lifeforms can read.

        For example, "HP LaserJet 2000", not "HP_LaserJet-2000".

        Returns:
          A name that makes sense when displayed to a non-technical user
        """

        if 'displayName' in self and self['displayName']:
            return self['displayName']
        else:
            return self['name']

    def getPPDName(self):
        return self._PPD_NAME % (
            urllib.quote(self.getAccount().encode('ascii', 'replace').replace(' ', '-')),
            self['id'].encode('ascii', 'replace').replace(' ', '-'))

    def generatePPD(self):
        """Generates a PPD string for this printer."""
        defaultlocale = locale.getdefaultlocale()
        language = Utils.GetLanguage(defaultlocale)
        defaultpapertype = Utils.GetDefaultPaperType(defaultlocale)
        ppd = self._PPD_TEMPLATE_HEAD % {
            'language': language, 'defaultpapertype': defaultpapertype,
            'ieee1284': self.getIEEE1284(), 'ppdname': self.getPPDName()}
        if self['capabilities'] is not None:
            addedCapabilities = []
            for capabilityname in self['capabilities']['printer']:
                if capabilityname not in self._IGNORED_CAPABILITIES:
                    capability = {}
                    capability['options'] = self['capabilities']['printer'][capabilityname]
                    capability['name'] = capabilityname
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

                    newppddata = '*OpenUI *%s/%s: PickOne\n' % \
                        (internalCapabilityName, internalCapabilityName)
                    # translation of capability, allows use of 8
                    # bit chars
                    newppddata += '*%s.Translation %s/%s: ""\n' % \
                        (language, internalCapabilityName, originCapabilityName)
                    addedOptions = []

                    if 'options' in capability and 'option' in capability['options']:
                        for option in capability['options']['option']:
                            originOptionName = None
                            if 'display_name' in option and len(option['display_name']) > 0:
                                originOptionName = self._sanitizeText(option['display_name'])
                            elif 'custom_display_name' in option \
                                    and len(option['custom_display_name']) > 0:
                                originOptionName = self._sanitizeText(option['custom_display_name'])
                            elif 'name' in option and len(option['name']) > 0:
                                originOptionName = self._sanitizeText(option['name'])
                            elif 'type' in option and len(option['type']) > 0:
                                originOptionName = self._sanitizeText(option['type'])
                            else:
                                continue
                            internalOptionName = self._getInternalName(
                                option, 'option', capability['name'], addedOptions)
                            addedOptions.append(internalOptionName)
                            if 'is_default' in option and option['is_default']:
                                newppddata += '*Default%s: %s\n' % (
                                    internalCapabilityName, internalOptionName)
                            newppddata += '*%s %s:%s\n' % \
                                (internalCapabilityName, internalOptionName, internalOptionName)
                            # translation of option, allows use of 8
                            # bit chars
                            value = ''
                            if 'ppd:value' in option:
                                value = option['ppd:value']
                            newppddata += '*%s.%s %s/%s: "%s"\n' % (
                                language,
                                internalCapabilityName,
                                internalOptionName,
                                originOptionName,
                                value)

                        newppddata += '*CloseUI: *%s\n' % internalCapabilityName
                    if len(addedOptions) > 0:
                        ppd += newppddata

        ppd += self._PPD_TEMPLATE_FOOT
        return ppd

    @staticmethod
    def _sanitizeText(text, checkReserved=False):
        sanitisedName = re.sub(r'(:|;| )', '_', text).replace('/', '-').encode('utf8', 'ignore')
        sanitisedName = "".join(ch for ch in unicode(sanitisedName, errors='ignore')
                                if unicodedata.category(ch)[0] != "C")
        if checkReserved and (sanitisedName in Printer._RESERVED_CAPABILITY_WORDS or
                              sanitisedName.startswith(Printer._RESERVED_CAPABILITY_PREFIXES)):
            sanitisedName = 'GCP_' + sanitisedName
        return sanitisedName

    @staticmethod
    def _getInternalName(details, internalType, capabilityName=None, existingList=None):
        returnValue = None
        if existingList is None:
            existingList = []

        fixedNameMap = {}
        # use fixed options for options we recognise
        if internalType == "option":
            # option
            if capabilityName in Printer._FIXED_OPTION_MAPPINGS:
                fixedNameMap = Printer._FIXED_OPTION_MAPPINGS[capabilityName]
        else:
            # capability
            fixedNameMap = Printer._FIXED_CAPABILITY_MAPPINGS

        for itemName in fixedNameMap:
            if details['name'] == itemName:
                returnValue = fixedNameMap[itemName]
                break

        if 'display_name' in details and len(details['display_name']) > 0:
            name = details['display_name']
        elif 'custom_display_name' in details and len(details['custom_display_name']) > 0:
            name = details['custom_display_name']
        elif 'name' in details and len(details['name']) > 0:
            name = details['name']
        elif 'type' in details and len(details['type']) > 0:
            name = details['type']
        else:
            return None

        sanitisedName = Printer._sanitizeText(name, True)

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
        # example:
        # {"version":"1.0","print":{"media_size":{"width_microns":215000,"height_microns":275000,"vendor_id":"15"}}}
        capabilities = {"version": "1.0", "print": {}}
        for attr in attrs:
            if attr['name'].startswith('Default'):
                # gcp setting, reverse back to GCP capability
                gcpname = None
                hashname = attr['name'].replace('Default', '')
                parammap = {}
                valuemap = {}
                deleteparams = ['name', 'custom_name', 'is_default',
                                'display_name', 'custom_display_name']

                # find item name from hashes
                gcpoption = None
                addedCapabilities = []
                for capabilityname in printercapabilities:
                    capability = {}
                    capability['options'] = printercapabilities[capabilityname]
                    capability['name'] = capabilityname
                    if hashname == Printer._getInternalName(capability, 'capability'):
                        gcpname = capability['name']
                        for option in capability['options']['option']:
                            paramname = 'type'
                            if 'type' not in option:
                                if 'vendor_id' in option:
                                    paramname = 'vendor_id'
                            if paramname in option:
                                internalCapability = Printer._getInternalName(
                                    option, 'option', gcpname, addedCapabilities)
                                addedCapabilities.append(internalCapability)
                                if attr['value'] == internalCapability:
                                    gcpoption = option[paramname]
                                    parammap[gcpoption] = paramname

                                    for deleteparam in deleteparams:
                                        if deleteparam in option:
                                            del option[deleteparam]

                                    valuemap[gcpoption] = option
                                    break
                        addedOptions = []
                        for overridecapability in overridecapabilities:
                            if 'Default' + overridecapability == attr['name']:
                                selectedoption = overridecapabilities[
                                    overridecapability]
                                for option in capability['options']['option']:
                                    paramname = 'type'
                                    if 'type' not in option:
                                        if 'vendor_id' in option:
                                            paramname = 'vendor_id'
                                    if paramname in option:
                                        internalOption = Printer._getInternalName(
                                            option, 'option', gcpname, addedOptions)
                                        addedOptions.append(internalOption)
                                        if selectedoption == internalOption:
                                            gcpoption = option[paramname]
                                            parammap[gcpoption] = paramname

                                            for deleteparam in deleteparams:
                                                if deleteparam in option:
                                                    del option[deleteparam]

                                            valuemap[gcpoption] = option
                                            break
                                break
                        break

                if gcpname is not None and gcpoption is not None:
                    if parammap[gcpoption] == 'vendor_id':
                        capabilities['print'][gcpname] = valuemap[gcpoption]
                    else:
                        capabilities['print'][gcpname] = {parammap[gcpoption]: gcpoption}
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
        return self._getCapabilitiesDict(attrArray,
                                         self['capabilities']['printer'],
                                         overridecapabilities)

    def submitJob(self, jobtype, jobfile, jobdata, jobname, cupsprintername, options=""):
        """Submits a job to printerid with content of dataUrl.

        Args:
          jobtype: string, must match the dictionary keys in content and content_type.
          jobfile: string, points to source for job. Could be a pathname or id string.
          jobdata: string, data for print job
          jobname: string, name of the print job ( usually page name ).
          options: string, key-value pair of options from print job.

        Returns:
          True if submitted, False otherwise
        """
        rotate = 0

        # refuse to submit empty jobdata
        if len(jobdata) == 0:
            sys.stderr.write("ERROR: Job data is empty\n")
            return False

        if jobfile is None or jobfile == "":
            jobfile = "Unknown"

        for optiontext in options.split(' '):

            # landscape
            if optiontext == 'landscape':
                # landscape
                rotate = 90

            # nolandscape - already rotates
            if optiontext == 'nolandscape':
                # rotate back
                rotate = 270

        if jobtype not in ['png', 'jpeg', 'pdf']:
            sys.stderr.write("ERROR: Unknown job type: %s\n" % jobtype)
            return False
        else:
            if rotate != 0:
                try:
                    command = [self._CONVERTCOMMAND, '-density', '300x300', '-',
                               '-rotate', str(rotate), '-']
                    p = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                    newjobdata = p.communicate(jobdata)[0]
                    if p.returncode == 0:
                        jobdata = newjobdata
                    else:
                        logging.error("Failed to rotate")
                        return False
                except Exception as error_msg:
                    logging.error("Convert command errored when rotating: %s" % str(error_msg))
                    return False

        if jobname == "":
            title = "Untitled page"
        else:
            title = jobname
        headers = [
            ('printerid', self['id']),
            ('title', title),
            ('content', Utils.Base64Encode(jobdata, jobtype)),
            ('contentType', 'dataUrl'),
            ('ticket', json.dumps(self._getCapabilities(cupsprintername, options)))
        ]
        logging.info('Capability headers are: %s', headers[4])
        data = self._encodeMultiPart(headers, 'dataUrl')

        try:
            responseobj = self.getRequestor().submit(data, self._getMimeBoundary())
            if responseobj['success']:
                return True
            else:
                sys.stderr.write("ERROR: Error response from Cloud Print for type %s: %s\n" %
                                 (jobtype, responseobj['message']))
                return False

        except Exception as error_msg:
            sys.stderr.write("ERROR: Print job %s failed with %s\n" % (jobtype, error_msg))
            return False
