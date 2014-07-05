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

    libpath = "/usr/local/share/cloudprint-cups/"
    if not os.path.exists(libpath):
        libpath = "/usr/share/cloudprint-cups"
    sys.path.insert(0, libpath)

    from auth import Auth
    from printermanager import PrinterManager
    from ccputils import Utils

    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140705 153312"
    Utils.ShowVersion(CCPVersion)

    if len(sys.argv) != 1 and len(sys.argv) < 6 or len(sys.argv) > 7:
        sys.stderr.write(
            "ERROR: Usage: %s job-id user title copies options [file]\n" % sys.argv[0])
        sys.exit(0)

    if len(sys.argv) >= 4 and sys.argv[3] == "Set Default Options":
        print "ERROR: Unimplemented command: " + sys.argv[3]
        logging.error("Unimplemented command: %s", sys.argv[3])
        sys.exit(0)

    if len(sys.argv) == 7:
        prog, jobID, userName, jobTitle, copies, printOptions, printFile = sys.argv[0:7]
    if len(sys.argv) == 6:
        prog, jobID, userName, jobTitle, copies, printOptions = sys.argv[0:6]
        printFile = None

    requestors, storage = Auth.SetupAuth(False)
    if not requestors:
        sys.stderr.write("ERROR: config is invalid or missing\n")
        logging.error("backend tried to run with invalid config")
        sys.exit(1)
    printer_manager = PrinterManager(requestors)

    if len(sys.argv) == 1:
        print 'network ' + Utils.PROTOCOL_NAME + ' "Unknown" "Google Cloud Print"'

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

    # if no printfile, put stdin to a temp file
    if printFile is None:
        tmpDir = os.getenv('TMPDIR')
        if not tmpDir:
            tmpDir = "/tmp"
        tempFile = '%s/%s-%s-cupsjob-%s' % \
            (tmpDir, jobID, userName, str(os.getpid()))

        OUT = open(tempFile, 'w')

        if not OUT:
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
    cupsprintername = os.getenv('PRINTER')
    if uri is None:
        message = 'URI must be "' + Utils.PROTOCOL + '<account name>/<cloud printer id>"!\n'
        sys.stdout.write(message)
        sys.exit(255)

    logging.info("Printing file %s", printFile)
    optionsstring = ' '.join(["'%s'" % option for option in sys.argv])
    logging.info("Device is %s , printername is %s, params are: %s",
                 uri, cupsprintername, optionsstring)

    pdfFile = printFile + ".pdf"
    if Utils.which("ps2pdf") is None:
        convertToPDFParams = ["pstopdf", printFile, pdfFile]
    else:
        convertToPDFParams = ["ps2pdf", "-dPDFSETTINGS=/printer",
                              "-dUseCIEColor", printFile, pdfFile]

    result = 0

    logging.debug('is this a pdf? %s', printFile)
    if not os.path.exists(printFile):
        sys.stderr.write('ERROR: file "%s" not found\n', printFile)
        result = 1
    elif not Utils.fileIsPDF(printFile):
        sys.stderr.write("INFO: Converting print job to PDF\n")
        if subprocess.call(convertToPDFParams) != 0:
            sys.stderr.write("ERROR: Failed to convert file to pdf\n")
            result = 1
        else:
            logging.info("Converted to PDF as %s", pdfFile)
    else:
        pdfFile = printFile + '.pdf'
        os.rename(printFile, pdfFile)
        logging.info("Using %s as is already PDF", pdfFile)

    if result == 0:
        sys.stderr.write("INFO: Sending document to Cloud Print\n")
        logging.info("Sending %s to cloud", pdfFile)

        printer = printer_manager.getPrinterByURI(uri)
        if printer is None:
            print "ERROR: PrinterManager '%s' not found" % uri
            result = 1
        elif printer.submitJob('pdf', pdfFile, jobTitle, cupsprintername, printOptions):
            print "INFO: Successfully printed"
            result = 0
        else:
            print "ERROR: Failed to submit job to cloud print"
            result = 1

        logging.info("%s sent to cloud print, deleting", pdfFile)
        if os.path.exists(printFile):
            os.unlink(printFile)
        sys.stderr.write("INFO: Cleaning up temporary files\n")
        logging.info("Deleted %s", printFile)
        if os.path.exists(pdfFile):
            os.unlink(pdfFile)
        logging.info("Deleted %s", pdfFile)
        if result != 0:
            sys.stderr.write("INFO: Printing Failed\n")
            logging.info("Failed printing")
        else:
            sys.stderr.write("INFO: Printing Successful\n")
            logging.info("Completed printing")

    sys.exit(result)
