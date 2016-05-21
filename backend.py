#! /bin/sh
"true" '''\'
if command -v python2 > /dev/null; then
  exec python2 "$0" "$@"
else
  exec python "$0" "$@"
fi
exit $?
'''

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

if __name__ == '__main__':  # pragma: no cover
    import sys
    import os
    import subprocess
    import logging
    import platform

    libpaths = [
                 "/Library/cloudprint-cups/",
                 "/usr/local/share/cloudprint-cups/",
                 "/usr/share/cloudprint-cups"
               ]
    addedPath = False
    for libpath in libpaths:
        if os.path.exists(libpath):
            libpath = "/usr/share/cloudprint-cups"
            sys.path.insert(0, libpath)
            addedPath = True
            break

    if not addedPath:
        sys.stderr.write("ERROR: Could not find any valid path for python files\n")
        sys.exit(1)

    from auth import Auth
    from printermanager import PrinterManager
    from ccputils import Utils

    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140814.2 000000"
    Utils.ShowVersion(CCPVersion)

    if len(sys.argv) != 1 and len(sys.argv) < 6 or len(sys.argv) > 7:
        sys.stderr.write(
            "ERROR: Usage: %s job-id user title copies options [file]\n" % sys.argv[0])
        sys.exit(0)

    if len(sys.argv) >= 4 and sys.argv[3] == "Set Default Options":
        sys.stderr.write("ERROR: Unimplemented command: " + sys.argv[3] + "\n")
        logging.error("Unimplemented command: " + sys.argv[3])
        sys.exit(0)

    printFile = None

    if len(sys.argv) == 7:
        sys.stderr.write("ERROR: Sorry, CUPS Cloud Print no longer supports printing\
                          files directly for security reasons\n")
        sys.exit(1)
    if len(sys.argv) == 6:
        prog, jobID, userName, jobTitle, copies, printOptions = sys.argv
        printFile = jobTitle

    requestors, storage = Auth.SetupAuth(False)
    if not requestors:
        sys.stderr.write("ERROR: config is invalid or missing\n")
        logging.error("backend tried to run with invalid config")
        sys.exit(1)
    printer_manager = PrinterManager(requestors)

    if len(sys.argv) == 1:
        print 'network ' + Utils._PROTOCOL_NAME + ' "Unknown" "Google Cloud Print"'

        printers = printer_manager.getPrinters()
        if printers is not None:
            try:
                for printer in printers:
                    print printer.getCUPSBackendDescription()
            except Exception as error:
                sys.stderr.write("ERROR: " + error)
                logging.error(error)
                sys.exit(1)
        sys.exit(0)

    filedata = ""
    for line in sys.stdin:
        filedata += line

    # Backends should only produce multiple copies if a file name is
    # supplied (see CUPS Software Programmers Manual)
    copies = 1

    uri = os.getenv('DEVICE_URI')
    cupsprintername = os.getenv('PRINTER')
    if uri is None:
        message = 'URI must be "' + Utils._PROTOCOL + '<account name>/<cloud printer id>"!\n'
        sys.stdout.write(message)
        sys.exit(255)

    logging.info("Printing file " + str(printFile))
    optionsstring = ' '.join(["'%s'" % option for option in sys.argv])
    logging.info("Device is %s , printername is %s, params are: %s" %
                 (uri, cupsprintername, optionsstring))

    # setup
    useTempFile = False
    convertToPDFParams = ["ps2pdf", "-dPDFSETTINGS=/printer",
                          "-dUseCIEColor", "-", "-"]
    if Utils.which("ps2pdf") is None:
        convertToPDFParams = [Utils.which("pstopdf"), "-", "-o", "-"]
        if platform.system() == 'Darwin':
            useTempFile = True
    else:
        convertToPDFParams[0] = Utils.which("ps2pdf")

    logging.debug('is this a pdf? ' + str(printFile))
    result = 0

    if not Utils.fileIsPDF(filedata):
        tempFileNameIn = None
        tempFileNameOut = None
        if useTempFile:
            tempFileNameIn = Utils.GetTempFileName()
            if not Utils.WriteFile(tempFileNameIn, filedata):
                sys.stderr.write("ERROR: Failed to write file %s \n" % tempFileNameIn)
                sys.exit(1)
            convertToPDFParams[1] = tempFileNameIn

            tempFileNameOut = Utils.GetTempFileName()
            convertToPDFParams[2] = '-o'
            convertToPDFParams[3] = tempFileNameOut
            sys.stderr.write("INFO: Using temp files: %s %s\n" % (tempFileNameIn, tempFileNameOut))
            sys.stderr.write("INFO: Command is: %s\n" % (" ".join(convertToPDFParams)))

        # read file as pdf
        sys.stderr.write("INFO: Converting print job to PDF\n")
        p=subprocess.Popen(convertToPDFParams, stdout=subprocess.PIPE,
                           stdin=subprocess.PIPE, stderr=subprocess.PIPE, env={'PATH': Utils.getPath()})
        processdata=p.communicate(filedata)
        if useTempFile:
            filedata=Utils.ReadFile(tempFileNameOut)
            if filedata is None:
                sys.stderr.write("ERROR: Failed to read file %s\n" % tempFileNameOut)
                sys.exit(1)
        else:
            filedata=processdata[0]
        if p.returncode != 0:
            sys.stderr.write("ERROR: Failed to convert file to pdf, returncode: %s\n" %
                             str(p.returncode))
            logging.error("Using these params %s", " ".join(convertToPDFParams))
            logging.error("Error from converting file to pdf: %s" % processdata[1])
            result=1
        else:
            logging.info("Converted to PDF - %s bytes" % str(len(filedata)))

        if useTempFile:
            os.unlink(tempFileNameIn)
            os.unlink(tempFileNameOut)
    else:
        # read file normally
        logging.info("Using %s as is already PDF - %s bytes" % (printFile, len(filedata)))

    # send pdf data to GCP
    if result == 0:
        sys.stderr.write("INFO: Sending document to Cloud Print\n")
        logging.info("Sending %s to cloud" % printFile)

        printer=printer_manager.getPrinterByURI(uri)
        if printer is None:
            sys.stderr.write("ERROR: PrinterManager '%s' not found\n" % uri)
            result=1
        elif printer.submitJob('pdf', printFile, filedata, jobTitle, cupsprintername, printOptions):
            sys.stderr.write("INFO: Successfully printed\n")
            result=0
        else:
            sys.stderr.write("ERROR: Failed to submit job to cloud print\n")
            result=1

        logging.info(str(printFile) + " sent to cloud print")

        if result != 0:
            sys.stderr.write("INFO: Printing Failed\n")
            logging.info("Failed printing")
        else:
            sys.stderr.write("INFO: Printing Successful\n")
            logging.info("Completed printing")

    sys.exit(result)
