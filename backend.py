#! /usr/bin/python
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
logfile.write("Converted to PDF as "+ pdfFile + "\n")
os.unlink( printFile )
logfile.write("Deleted "+ printFile + "\n")
os.unlink( pdfFile )
logfile.write("Deleted "+ pdfFile + "\n")
logfile.close()
