#! /usr/bin/python
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

import sys, os, subprocess
progname = sys.argv[0]
progname = 'cloudprint'

if len(sys.argv) == 1:
  print "network " + progname + " \"Unknown\" \"Google Cloud Print\""
  sys.exit(0)
  
if len(sys.argv) < 6 or len(sys.argv) > 7:
    sys.stderr.write("ERROR: Usage: " + progname +" job-id user title copies options [file]\n")
    sys.exit(0)

printFile = None
if len(sys.argv) == 7:
  prog, jobID, userName, jobTitle, copies, printOptions, printFile = sys.argv
else:
  prog, jobID, userName, jobTitle, copies, printOptions = sys.argv

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
if uri == None:
  sys.stdout.write("URI must be \"cloudprint:/<cloud printer name>\"!\n")
  sys.exit(255)

logfile = open('/var/log/cups/cloudprint_log', 'a')
logfile.write("Printing file " + printFile + "\n")

pdfFile = printFile+".pdf"

subprocess.call(["ps2pdf", printFile, pdfFile])
submitjobpath = "/usr/lib/cloudprint-cups/" + "submitjob.py"
if not os.path.exists( submitjobpath  ):
	submitjobpath = "/usr/local/lib/cloudprint-cups/" + "submitjob.py"
	
logfile.write("Running " +  submitjobpath  + "\n")
logfile.write("Converted to PDF as "+ pdfFile + "\n")
logfile.write("Sending "+ pdfFile + " to cloud\n")
subprocess.call([submitjobpath, pdfFile, uri])
logfile.write(pdfFile + " sent to cloud print, deleting\n")
os.unlink( printFile )
logfile.write("Deleted "+ printFile + "\n")
os.unlink( pdfFile )
logfile.write("Deleted "+ pdfFile + "\n")
logfile.close()
