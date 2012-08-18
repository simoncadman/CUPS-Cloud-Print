#! /usr/bin/env python2.7

import sys, cups, subprocess

connection = cups.Connection()
cupsprinters = connection.getPrinters()

for device in cupsprinters:
  if ( cupsprinters[device]["device-uri"].find("cloudprint://") == 0 ):
    print "Updating " + cupsprinters[device]["printer-info"]
    
    p = subprocess.Popen(["lpadmin", "-p", cupsprinters[device]["printer-info"], "-m", "CloudPrint.ppd"], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    result = p.returncode
    sys.stderr.write(output)