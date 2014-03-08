#! /usr/bin/env python2
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

if __name__ == '__main__': # pragma: no cover
    import sys, os, subprocess, mimetypes, logging

    progname = 'cloudprint'

    if len(sys.argv) == 2 and sys.argv[1] == 'version':
        # line below is replaced on commit
        CCPVersion = "20140308 173250"
        print "CUPS Cloud Print CUPS Backend Version " + CCPVersion
        sys.exit(0)

    libpath = "/usr/local/share/cloudprint-cups/"
    if not os.path.exists( libpath  ):
        libpath = "/usr/share/cloudprint-cups"
    sys.path.insert(0, libpath)

    from auth import Auth
    from printer import Printer
    from ccputils import Utils
    
    Utils.SetupLogging()
    
    requestors, storage = Auth.SetupAuth(False)
    if requestors == False:
        sys.stderr.write("ERROR: config is invalid or missing\n")
        logging.error("backend tried to run with invalid config");
        sys.exit(1)
    printer = Printer(requestors)
    printers = printer.getPrinters()

    if len(sys.argv) == 1:
        print printer.getBackendDescription()

        try:
            if printers != None:
                for foundprinter in printers:
                    print "network " + printer.printerNameToUri(foundprinter['account'], foundprinter['id']) + " " + "\"" + foundprinter['name'] + "\" \"Google Cloud Print\"" + " \"MFG:Google;MDL:Cloud Print;DES:GoogleCloudPrint;\""
        except Exception as error:
            print error
            pass
        sys.exit(0)

    if len(sys.argv) < 6 or len(sys.argv) > 7:
        sys.stderr.write("ERROR: Usage: " + progname +" job-id user title copies options [file]\n")
        sys.exit(0)

    printFile = None
    if len(sys.argv) == 7:
        prog, jobID, userName, jobTitle, copies, printOptions, printFile = sys.argv
    else:
        prog, jobID, userName, jobTitle, copies, printOptions = sys.argv

    if sys.argv[3] == "Set Default Options":
        print "ERROR: Unimplemented command: " + sys.argv[3]
        logging.error("Unimplemented command: " + sys.argv[3]);
        sys.exit(0)
    else:
        # if no printfile, put stdin to a temp file
        tempFile = None
        if printFile == None:
            tmpDir = os.getenv('TMPDIR')
            if not tmpDir:
                tmpDir = "/tmp"
            tempFile = tmpDir + '/' + jobID + '-' + userName + '-cupsjob-' + str(os.getpid())

            OUT = open (tempFile, 'w')

            if OUT == False:
                print "ERROR: Cannot write " + tempFile
                sys.exit(1)

            for line in sys.stdin:
                OUT.write(line)

            OUT.close()

            printFile = tempFile

            # Backends should only produce multiple copies if a file name is
            # supplied (see CUPS Software Programmers Manual)
            copies = 1

        uri = os.getenv('DEVICE_URI')
        printername = os.getenv('PRINTER')
        if uri == None:
            sys.stdout.write("URI must be \"cloudprint:/<cloud printer name>\"!\n")
            sys.exit(255)

        logging.info("Printing file " + printFile)
        optionsstring = ""
        for option in sys.argv:
            optionsstring += " '" + option + "'"
        logging.info("Device is " + uri + " , printername is " + printername + ", Params are: " + optionsstring)

        pdfFile = printFile+".pdf"
        ps2PdfName = "ps2pdf"
        convertToPDFParams = [ps2PdfName, "-dPDFSETTINGS=/printer", "-dUseCIEColor", printFile, pdfFile]
        if Utils.which(ps2PdfName) == None:
            ps2PdfName = "pstopdf"
            convertToPDFParams = [ps2PdfName, printFile, pdfFile]

        result = 0
        
        if not Utils.fileIsPDF( printFile  ):
            sys.stderr.write( "INFO: Converting print job to PDF\n")
            if ( subprocess.call(convertToPDFParams) != 0 ):
                sys.stderr.write( "ERROR: Failed to convert file to pdf\n")
                result = 1
            else:
                logging.info("Converted to PDF as "+ pdfFile)
        else:
            pdfFile = printFile + '.pdf'
            os.rename(printFile,pdfFile)
            logging.info("Using " + pdfFile  + " as is already PDF")
            
        if result == 0:
            sys.stderr.write( "INFO: Sending document to Cloud Print\n")
            logging.info("Sending "+ pdfFile + " to cloud")

            printerid, requestor = printer.getPrinterIDByURI(uri)
            printer.requestor = requestor
            if printerid == None:
                print "ERROR: Printer '" + uri + "' not found"
                result = 1
            else:
                if printer.submitJob(printerid, 'pdf', pdfFile, jobTitle, printername, printOptions ):
                    print "INFO: Successfully printed"
                    result = 0
                else:
                    print "ERROR: Failed to submit job to cloud print"
                    result = 1

            logging.info(pdfFile + " sent to cloud print, deleting")
            if os.path.exists( printFile ):
                os.unlink( printFile )
            sys.stderr.write("INFO: Cleaning up temporary files\n")
            logging.info("Deleted "+ printFile)
            if os.path.exists( pdfFile ):
                os.unlink( pdfFile )
            logging.info("Deleted "+ pdfFile)
            if result != 0:
                sys.stderr.write("INFO: Printing Failed\n")
                logging.info("Failed printing")
            else:
                sys.stderr.write("INFO: Printing Successful\n")
                logging.info("Completed printing")
            sys.exit(result)
        else:
            sys.exit(result)