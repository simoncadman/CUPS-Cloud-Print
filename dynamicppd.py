#! /usr/bin/env python2
#    CUPS Cloudprint - Print via Google Cloud Print
#    Copyright (C) 2013 Simon Cadman
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

import os
import sys

__list_format = '"cupscloudprint:%s:%s-%s.ppd" en "Google" "%s (%s)" "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:%s;"'

# Countries where letter sized paper is used, according to:
# http://en.wikipedia.org/wiki/Letter_(paper_size)
__letter_countries = set(('US', 'CA', 'MX', 'BO', 'CO', 'VE', 'PH', 'CL'))

__ppd_template_head = """*PPD-Adobe: "4.3"
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

__ppd_template_foot = """*DefaultFont: Courier
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


def doList(sys, printer):
    """Lists Google Cloud Print printers."""
    printers = printer.getPrinters()
    if printers is None:
        sys.stderr.write("ERROR: No Printers Found\n")
        sys.exit(1)
    for foundprinter in printers:
        account_no_spaces = foundprinter['account'].encode('ascii', 'replace').replace(' ', '-')
        name_no_spaces = foundprinter['name'].encode('ascii', 'replace').replace(' ', '-')
        id = foundprinter['id'].encode('ascii', 'replace').replace(' ', '-')
        name = foundprinter['name'].encode('ascii', 'replace')
        account = foundprinter['account']
        uri = printer.printerNameToUri(foundprinter['account'], foundprinter['id'])
        print __list_format % \
            (account_no_spaces, name_no_spaces, id, name, account, uri)
    sys.exit(0)


def generatePPD(accountName, foundprinter):
    """Generates a PPD string for foundprinter."""
    language = "en"
    defaultpapertype = "Letter"
    defaultlocale = locale.getdefaultlocale()[0]
    if defaultlocale is not None:
        language = defaultlocale
        if len(language.split('_')) > 1 and language.split('_')[1] not in __letter_countries:
            defaultpapertype = "A4"
    if '_' in language and language.split("_")[0] != "en":
        language = language.split("_")[0]
    uri = printer.printerNameToUri(foundprinter['account'], foundprinter['id'])
    ppd = __ppd_template_head % \
        {'language': language, 'defaultpapertype': defaultpapertype, 'uri': uri}
    if len(sys.argv) > 3 and sys.argv[3] == "testmode" and os.path.exists('test-capabilities.serial'):
        with file("test-capabilities.serial") as f:
            import ast
            foundprinter['fulldetails'] = ast.literal_eval(f.read())
    else:
        printer.requestor = printer.findRequestorForAccount(accountName)
        details = printer.getPrinterDetails(foundprinter['id'])
        foundprinter['fulldetails'] = details['printers'][0]
    if 'capabilities' in foundprinter['fulldetails']:
        addedCapabilities = []
        for capability in foundprinter['fulldetails']['capabilities']:
            originCapabilityName = None
            internalCapabilityName = \
                printer.getInternalName(capability, 'capability', None, addedCapabilities)
            addedCapabilities.append(internalCapabilityName)
            if 'displayName' in capability and len(capability['displayName']) > 0:
                originCapabilityName = printer.sanitizeText(capability['displayName'])
            elif 'psk:DisplayName' in capability and len(capability['psk:DisplayName']) > 0:
                originCapabilityName = printer.sanitizeText(capability['psk:DisplayName'])
            else:
                originCapabilityName = printer.sanitizeText(capability['name'])
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
                        originOptionName = printer.sanitizeText(
                            option['displayName'])
                    elif 'psk:DisplayName' in option and len(option['psk:DisplayName']) > 0:
                        originOptionName = printer.sanitizeText(option['psk:DisplayName'])
                    else:
                        originOptionName = printer.sanitizeText(option['name'])
                    internalOptionName = \
                        printer.getInternalName(option, 'option', capability['name'], addedOptions)
                    addedOptions.append(internalOptionName)
                    if 'default' in option and option['default']:
                        ppd += '*Default%s: %s\n' % (internalCapabilityName, internalOptionName)
                    ppd += '*%s %s:%s\n' % \
                        (internalCapabilityName, internalOptionName, internalOptionName)
                    # translation of option, allows use of 8
                    # bit chars
                    ppd += '*%s.%s %s/%s: ""\n' % \
                        (language, internalCapabilityName, internalOptionName, originOptionName)

                ppd += '*CloseUI: *%s\n' % internalCapabilityName
            elif capability['type'] == 'ParameterDef':
                pass

    ppd += __ppd_template_foot
    return ppd


def doCat():
    """Prints a PPD to stdout, per argv arguments."""
    ppdname = sys.argv[2]
    ppdparts = ppdname.split(":")
    if len(ppdparts) < 3:
        sys.stderr.write("ERROR: PPD name is invalid\n")
        sys.exit(1)

    accountName = ppdparts[1]
    printers = printer.getPrinters(accountName=accountName)

    if printers is None or len(printers) == 0:
        # still can't find printer specifically, try all accounts
        printers = printer.getPrinters()

    if printers is None:
        sys.stderr.write("ERROR: No Printers Found\n")
        sys.exit(1)

    # find printer
    for foundprinter in printers:
        foundppdname = 'cupscloudprint:%s:%s-%s.ppd' % (
            foundprinter['account'].encode('ascii', 'replace').replace(' ', '-'),
            foundprinter['name'].encode('ascii', 'replace').replace(' ', '-'),
            foundprinter['id'].encode('ascii', 'replace').replace(' ', '-'))
        if ppdname == foundppdname:
            print generatePPD(accountName, foundprinter)
            sys.exit(0)

    # no printers found
    sys.stderr.write("ERROR: PPD %s Not Found\n" % ppdname)
    sys.exit(1)


def showUsage():
    sys.stderr.write("ERROR: Usage: %s [list|version|cat drivername]\n" % sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':  # pragma: no cover
    import locale
    import logging

    libpath = "/usr/local/share/cloudprint-cups/"
    if not os.path.exists(libpath):
        libpath = "/usr/share/cloudprint-cups"
    sys.path.insert(0, libpath)

    from auth import Auth
    from printer import Printer
    from ccputils import Utils
    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140331 215708"
    Utils.ShowVersion(CCPVersion)

    requestors, storage = Auth.SetupAuth(False)
    if not requestors:
        sys.stderr.write("ERROR: config is invalid or missing\n")
        logging.error("backend tried to run with invalid config")
        sys.exit(1)

    printer = Printer(requestors)

    if (len(sys.argv) < 2):
        showUsage()

    elif sys.argv[1] == 'list':
        doList(sys, printer)

    elif sys.argv[1] == 'cat':
        if len(sys.argv) == 2 or sys.argv[2] == "":
            showUsage()
        doCat()
