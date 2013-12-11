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

import sys, os, subprocess, mimetypes
progname = 'cloudprint'

if len(sys.argv) == 2 and sys.argv[1] == 'version':
    # line below is replaced on commit
    CCPVersion = "20131211 135444"
    print "CUPS Cloud Print CUPS Backend Version " + CCPVersion
    sys.exit(0)

def fileIsPDF ( filename ) :
  """Check if a file is or isnt a PDF

  Args:
    filename: string, name of the file to check
  Returns:
    boolean: True = is a PDF, False = not a PDF.
  """
  result = 0
  p = subprocess.Popen(["file", filename], stdout=subprocess.PIPE)
  output = p.communicate()[0]
  result = p.returncode
  if result != 0:
      return False
  else:
      return "PDF document" in output

def which(program):
  import os
  def is_exe(fpath): # pragma: no cover
      return os.path.exists(fpath) and os.access(fpath, os.X_OK)

  fpath, fname = os.path.split(program)
  if fpath:
      if is_exe(program): # pragma: no cover
          return program
  else:
      for path in os.environ["PATH"].split(os.pathsep):
          exe_file = os.path.join(path, program)
          if is_exe(exe_file): # pragma: no cover
              return exe_file
  return None

def getBackendDescription ( ) :
  return "network cloudprint \"Unknown\" \"Google Cloud Print\""

if __name__ == '__main__': # pragma: no cover 
    
  if len(sys.argv) == 1:
    print(getBackendDescription())
  
    try:
      libpath = "/usr/local/lib/cloudprint-cups/"
      if not os.path.exists( libpath  ):
          libpath = "/usr/lib/cloudprint-cups"
      sys.path.insert(0, libpath)
      from auth import Auth
      from printer import Printer
      requestors, storage = Auth.SetupAuth(False)
      printer = Printer(requestors)
      printers = printer.getPrinters()
      if printers != None:
        for foundprinter in printers:
	  print("network " + printer.printerNameToUri(foundprinter['account'], foundprinter['name']) + " " + "\"" + foundprinter['name'] + "\" \"Google Cloud Print\"" + " \"MFG:Google;MDL:Cloud Print;DES:GoogleCloudPrint;\"" )
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

  try:
    logfile = open('/var/log/cups/cloudprint_log', 'a')
  except:
    logfile = sys.stdout
    logfile.write("Unable to write to log file /var/log/cups/cloudprint_log")

  if sys.argv[3] == "Set Default Options":
    print "ERROR: Unimplemented command: " + sys.argv[3]
    logfile.write("ERROR: Unimplemented command: " + sys.argv[3]);
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
        print("ERROR: Cannot write " + tempFile)
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
  
    logfile.write("Printing file " + printFile + "\n")
    optionsstring = ""
    for option in sys.argv:
      optionsstring += " '" + option + "'"
    logfile.write("Device is " + uri + " , printername is " + printername + ", Params are: " + optionsstring + "\n")

    pdfFile = printFile+".pdf"
    ps2PdfName = "ps2pdf"
    convertToPDFParams = [ps2PdfName, "-dPDFSETTINGS=/printer", printFile, pdfFile]
    if which(ps2PdfName) == None:
      ps2PdfName = "pstopdf"
      convertToPDFParams = [ps2PdfName, printFile, pdfFile]

    submitjobpath = "/usr/lib/cloudprint-cups/" + "submitjob.py"
    if not os.path.exists( submitjobpath  ):
	submitjobpath = "/usr/local/lib/cloudprint-cups/" + "submitjob.py"

    if not fileIsPDF( printFile  ):
  	sys.stderr.write( "INFO: Converting print job to PDF\n")
	subprocess.call(convertToPDFParams)
	logfile.write("Running " +  submitjobpath  + "\n")
	logfile.write("Converted to PDF as "+ pdfFile + "\n")
    else:
	pdfFile = printFile + '.pdf'
	os.rename(printFile,pdfFile)
	logfile.write("Using " + pdfFile  + " as is already PDF\n")

    sys.stderr.write( "INFO: Sending document to Cloud Print\n")
    logfile.write("Sending "+ pdfFile + " to cloud\n")
    result = 0
    p = subprocess.Popen([submitjobpath, pdfFile, jobTitle, uri, printername, printOptions], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    result = p.returncode
    sys.stderr.write(output)
    logfile.write(output)
    logfile.write(pdfFile + " sent to cloud print, deleting\n")
    if os.path.exists( printFile ):
       os.unlink( printFile )
    sys.stderr.write("INFO: Cleaning up temporary files\n")
    logfile.write("Deleted "+ printFile + "\n")
    if os.path.exists( pdfFile ):
       os.unlink( pdfFile )
    logfile.write("Deleted "+ pdfFile + "\n")
    logfile.close()
    sys.stderr.write("INFO: Printing Successful\n")
    sys.exit(result)
