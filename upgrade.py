#! /usr/bin/env python2.7

import sys, cups, subprocess, os, json
from oauth2client import client
from oauth2client import multistore_file
from auth import Auth

connection = cups.Connection()
cupsprinters = connection.getPrinters()

try:
  for device in cupsprinters:
    if ( cupsprinters[device]["device-uri"].find("cloudprint://") == 0 ):
      print "Updating " + cupsprinters[device]["printer-info"]
      
      p = subprocess.Popen(["lpadmin", "-p", cupsprinters[device]["printer-info"], "-m", "CloudPrint.ppd"], stdout=subprocess.PIPE)
      output = p.communicate()[0]
      result = p.returncode
      sys.stderr.write(output)
except :
  sys.stderr.write("Error connecting to CUPS")

if os.path.exists(Auth.config):
  try:
    with open(Auth.config, 'r') as content_file:
	content = content_file.read()
	data = json.loads(content)
  except:
    sys.stderr.write("\n\nYou have an old CUPS Cloud Print configuration file, with plaintext login details, you will need to run /usr/lib/cupscloudprint/setupcloudprint.py to upgrade to the latest authentication method before you can print.\n\n")
    
else:
  sys.stderr.write("\n\nRun: /usr/lib/cloudprint-cups/setupcloudprint.py to setup your Google Credentials and add your printers to CUPS\n\n")
  