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

import sys, os, locale

if len(sys.argv) == 2 and sys.argv[1] == 'version':
    # line below is replaced on commit
    CCPVersion = "20140126 180729"
    print "CUPS Cloud Print Dynamic PPD Generator Version " + CCPVersion
    sys.exit(0)

libpath = "/usr/local/share/cloudprint-cups/"
if not os.path.exists( libpath  ):
    libpath = "/usr/share/cloudprint-cups"
sys.path.insert(0, libpath)

from auth import Auth
from printer import Printer

def showUsage():
    sys.stderr.write("ERROR: Usage: " + sys.argv[0] + " [list|version|cat drivername]\n")
    sys.exit(1)
        
requestors, storage = Auth.SetupAuth(False)
printer = Printer(requestors)

if ( len(sys.argv) < 2 ):
    showUsage()

if sys.argv[1] == 'list':
    printers = printer.getPrinters(True)
    if printers == None:
        print "ERROR: No Printers Found"
        sys.exit(1)
    for foundprinter in printers:
        print '"cupscloudprint:' + foundprinter['account'].encode('ascii', 'replace').replace(' ', '-') +':' + foundprinter['name'].encode('ascii', 'replace').replace(' ', '-') + '.ppd" en "Google" "' + foundprinter['name'].encode('ascii', 'replace') + ' (' + foundprinter['account'] + ')" "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:' + printer.printerNameToUri( foundprinter['account'], foundprinter['name'] ) +';"'
        
elif sys.argv[1] == 'cat':
    if len(sys.argv) == 2 or sys.argv[2] == "":
        showUsage()
    else:
        ppdname = sys.argv[2]
        ppdparts = ppdname.split(":")
        if len(ppdparts) < 3:
            print "ERROR: PPD name is invalid"
            sys.exit(1)
        
        accountName = ppdparts[1]
        printers = printer.getPrinters(True, accountName )
        
        if printers == None or len(printers) == 0:
            # still cant find printer specifically, try all accounts
            printers = printer.getPrinters(True)
            
        if printers == None:
            print "ERROR: No Printers Found"
            sys.exit(1)
        
        # find printer
        for foundprinter in printers:
            if ppdname == 'cupscloudprint:' + foundprinter['account'].encode('ascii', 'replace').replace(' ', '-') +':' + foundprinter['name'].encode('ascii', 'replace').replace(' ', '-') + '.ppd':
                capabilities = []
                # generate and output ppd
                language = "en"
                defaultpapertype = "Letter"
                defaultlocal = locale.getdefaultlocale()[0]
                if defaultlocal != None:
                    language = defaultlocal
                    
                    # taken from wikipedia 
                    lettercountries = [ 'US', 'CA', 'MX', 'BO', 'CO', 'VE', 'PH', 'CL' ]
                    if len(language.split('_')) > 1:
                        if language.split('_')[1] not in lettercountries:
                            defaultpapertype = "A4"
                
                if '_' in language and language.split("_")[0] != "en":
                    language = language.split("_")[0]
                
                ppddetails = """*PPD-Adobe: "4.3"
*%%%% PPD file for Cloud Print with CUPS.
*FormatVersion: "4.3"
*FileVersion: "1.0"
*LanguageVersion: English
*LanguageEncoding: ISOLatin1
*cupsLanguages: \"""" + language +"""\"
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
*% Driver-defined attributes...
*1284DeviceID: "MFG:GOOGLE;DRV:GCP;CMD:POSTSCRIPT;MDL:""" + printer.printerNameToUri( foundprinter['account'], foundprinter['name'] ) + """;"
*OpenUI *PageSize/Media Size: PickOne
*""" + language + """.Translation PageSize/Media Size: ""
*OrderDependency: 10 AnySetup *PageSize
*DefaultPageSize: """ + defaultpapertype + """.Fullbleed
*PageSize Letter.Fullbleed/US Letter: "<</PageSize[612 792]/ImagingBBox null>>setpagedevice"
*""" + language + """.PageSize Letter.Fullbleed/US Letter: ""
*PageSize Legal.Fullbleed/US Legal: "<</PageSize[612 1008]/ImagingBBox null>>setpagedevice"
*""" + language + """.PageSize Legal.Fullbleed/US Legal: ""
*PageSize A4.Fullbleed/A4: "<</PageSize[595 842]/ImagingBBox null>>setpagedevice"
*""" + language + """.PageSize A4.Fullbleed/A4: ""
*CloseUI: *PageSize
*OpenUI *PageRegion/Page Region: PickOne
*""" + language + """.Translation PageRegion/Page Region: ""
*OrderDependency: 10 AnySetup *PageRegion
*DefaultPageRegion: """ + defaultpapertype + """.Fullbleed
*PageRegion Letter.Fullbleed/US Letter: "<</PageSize[612 792]/ImagingBBox null>>setpagedevice"
*""" + language + """.PageRegion Letter.Fullbleed/US Letter: ""
*PageRegion Legal.Fullbleed/US Legal: "<</PageSize[612 1008]/ImagingBBox null>>setpagedevice"
*""" + language + """.PageRegion Legal.Fullbleed/US Legal: ""
*PageRegion A4.Fullbleed/A4: "<</PageSize[595 842]/ImagingBBox null>>setpagedevice"
*""" + language + """.PageRegion A4.Fullbleed/A4: ""
*CloseUI: *PageRegion
*DefaultImageableArea: """ + defaultpapertype + """.Fullbleed
*ImageableArea Letter.Fullbleed/US Letter: "0 0 612 792"
*ImageableArea Legal.Fullbleed/US Legal: "0 0 612 1008"
*ImageableArea A4.Fullbleed/A4: "0 0 595 842"
*DefaultPaperDimension: """ + defaultpapertype + """.Fullbleed
*PaperDimension Letter.Fullbleed/US Letter: "612 792"
*PaperDimension Legal.Fullbleed/US Legal: "612 1008"
*PaperDimension A4.Fullbleed/A4: "595 842"
"""
                if len(sys.argv) > 3 and sys.argv[3] == "testmode" and os.path.exists('test-capabilities.serial'):
                    with file("test-capabilities.serial") as f:
                        import ast
                        foundprinter['fulldetails'] = ast.literal_eval(f.read())
                        
                if 'capabilities' in foundprinter['fulldetails']:
                    addedCapabilities = []
                    
                    for capability in foundprinter['fulldetails']['capabilities']:
                        originCapabilityName = None
                        internalcapabilityName = printer.getInternalName(capability, 'capability', None, addedCapabilities)
                        addedCapabilities.append(internalcapabilityName)
                        
                        if 'displayName' in capability and len(capability['displayName']) > 0:
                            originCapabilityName = printer.sanitizeText(capability['displayName'])
                        elif 'psk:DisplayName' in capability and len(capability['psk:DisplayName']) > 0:
                            originCapabilityName = printer.sanitizeText(capability['psk:DisplayName'])
                        else:
                            originCapabilityName = printer.sanitizeText(capability['name'])
                            
                        engCapabilityName = printer.sanitizeText(capability['name'])
                        if capability['type'] == 'Feature':
                            ppddetails += '*OpenUI *' + internalcapabilityName + '/' + internalcapabilityName +': PickOne' + "\n"
                            
                            # translation of capability, allows use of 8 bit chars
                            ppddetails += '*' + language + '.Translation' + ' ' + internalcapabilityName + '/' + originCapabilityName + ": \"\"\n"
                            
                            addedOptions = []
                            
                            for option in capability['options']:
                                originOptionName = None
                                if 'displayName' in option and len(option['displayName']) > 0:
                                    originOptionName = printer.sanitizeText(option['displayName'])
                                elif 'psk:DisplayName' in option and len(option['psk:DisplayName']) > 0:
                                    originOptionName = printer.sanitizeText(option['psk:DisplayName'])
                                else:
                                    originOptionName = printer.sanitizeText(option['name'])
                                engOptionName = printer.sanitizeText(option['name'])
                                internalOptionName = printer.getInternalName(option, 'option', capability['name'], addedOptions)
                                addedOptions.append(internalOptionName)
                                if 'default' in option and option['default'] == True:
                                    ppddetails += '*Default' + internalcapabilityName + ': ' + internalOptionName + "\n"
                                ppddetails += '*' + internalcapabilityName + ' ' + internalOptionName + ':' + internalOptionName + "\n"
                                
                                # translation of option, allows use of 8 bit chars
                                ppddetails += '*' + language + '.' + internalcapabilityName + ' ' + internalOptionName + "/" + originOptionName + ": \"\"\n"
                                
                            ppddetails += '*CloseUI: *' + internalcapabilityName + "\n"
                        elif capability['type'] == 'ParameterDef':
                            pass
                        
                ppddetails += """*DefaultFont: Courier
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
                print ppddetails
                sys.exit(0)
                
        # no printers found
        print "ERROR: PPD " + ppdname +" Not Found"
        sys.exit(1)
