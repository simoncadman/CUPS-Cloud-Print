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

import cups, os, json, sys, logging
from auth import Auth
from printer import Printer

if len(sys.argv) == 2 and sys.argv[1] == 'version':
    # line below is replaced on commit
    CCPVersion = "20140202 210315"
    print "CUPS Cloud Print Setup Script Version " + CCPVersion
    sys.exit(0)

logpath = '/var/log/cups/cloudprint_log'
try:
    logging.basicConfig(filename=logpath,level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    logging.error("Unable to write to log file "+ logpath)

unattended = False
answer = ""

if len(sys.argv) == 2 and sys.argv[1] == 'unattended':
    print "Running unattended, setting up all printers"
    unattended = True

if os.path.exists(Auth.config):
  try:
    content_file = open(Auth.config, 'r')
    content = content_file.read()
    data = json.loads(content)
  except:
    # remove old config file
    print "Deleting old configuration file: " + Auth.config
    os.remove(Auth.config)

while True:
  requestors, storage = Auth.SetupAuth(True)
  print "You currently have these accounts configured: "
  for requestor in requestors:
    print requestor.getAccount()
  if unattended:
      break
  answer = raw_input("Add more accounts (Y/N)? ")
  if not ( answer.startswith("Y") or answer.startswith("y") ):
    break
  else:
    Auth.AddAccount(storage)

for requestor in requestors:
  addedCount = 0
  connection = cups.Connection()
  cupsprinters = connection.getPrinters()
  prefix = ""
  printer = Printer(requestor)
  printers = printer.getPrinters()
  if printers == None:
    print "Sorry, no printers were found on your Google Cloud Print account."
    continue
  
  if unattended:
    answer = "Y"
  else:
    answer = raw_input("Add all Google Cloud Print printers to local CUPS install from " + requestor.getAccount() + " (Y/N)? ")
    
  if not ( answer.startswith("Y") or answer.startswith("y") ):
    answer = 1
    print "Not adding printers automatically"
    
    while int(answer) != 0:
        i=0
        for printeritem in printers:
            i+=1
            print str(i) + ") " + printeritem['displayName']
        maxprinterid = i
        answer = raw_input("Add printer (1-" + str(maxprinterid) + ", 0 to cancel)? ")
        try:
            answer = int(answer)
        except ValueError:
            answer = 0
        if answer != 0:
            if answer >= 1 and answer <= maxprinterid:
                ccpprinter = printers[answer-1]
                print "Adding " + printers[answer-1]['displayName']
                prefixanswer = raw_input("Use a prefix for name of printer (Y/N)? ")
                if ( prefixanswer.startswith("Y") or prefixanswer.startswith("y") ):
                    prefix = raw_input("Prefix ( e.g. GCP- )? ")
                    if prefix == "":
                        print "Not using prefix"
                
                printername = prefix + ccpprinter['name'].encode('ascii', 'replace')
                uri = printer.printerNameToUri(ccpprinter['account'], ccpprinter['name'].encode('ascii', 'replace'))
                found = False
                for cupsprinter in cupsprinters:
                    if cupsprinters[cupsprinter]['device-uri'] == uri:
                        found = True
                if found == True:
                    print "\nPrinter with " + printername +" already exists\n"
                else:
                    printer.addPrinter(printername, uri, connection)
            else:
                print "\nPrinter " + str(answer) + " not found\n"
    continue
  
  prefixanswer = ""
  if unattended:
    prefixanswer = "Y"
  else:
    prefixanswer = raw_input("Use a prefix for names of created printers (Y/N)? ")
    
  if ( prefixanswer.startswith("Y") or prefixanswer.startswith("y") ):
      prefix = ""
      if unattended:
        prefix = "GCP-"
      else:
        prefix = raw_input("Prefix ( e.g. GCP- )? ")
        
      if prefix == "":
        print "Not using prefix"
    
  for ccpprinter in printers:
    uri = printer.printerNameToUri(ccpprinter['account'], ccpprinter['name'].encode('ascii', 'replace'))
    found = False
    for cupsprinter in cupsprinters:
      if cupsprinters[cupsprinter]['device-uri'] == uri:
	found = True
    
    if found == False:
      printername = prefix + ccpprinter['name']
      
      # check if printer name already exists
      foundbyname = False
      for ccpprinter2 in cupsprinters:
	if printer.sanitizePrinterName(cupsprinters[ccpprinter2]['printer-info']) == printer.sanitizePrinterName(printername):
	  foundbyname = True
      if ( foundbyname and not unattended ) :
	answer = raw_input("Printer " + printer.sanitizePrinterName(printername) + " already exists, supply another name (Y/N)? ")
	if ( answer.startswith("Y") or answer.startswith("y") ):
	  printername = raw_input("New printer name? ")
	else:
	  answer = raw_input("Overwrite " + printer.sanitizePrinterName(printername) + " with new printer (Y/N)? ")
	  if ( answer.startswith("N") or answer.startswith("n") ):
	    printername = ""
      elif foundbyname and unattended:
          print "Not adding printer " + printername + ", as already exists"
          printername = ""
      
      if printername != "":
	printer.addPrinter(printername, uri, connection)
	addedCount+=1
      
  if addedCount > 0:
    print "Added " + str(addedCount) + " new printers to CUPS"
  else:
    print "No new printers to add"

printeruris = []
printer = Printer(requestors)
printers = printer.getPrinters()
for foundprinter in printers:
  printeruris.append(printer.printerNameToUri(foundprinter['account'], foundprinter['name'].encode('ascii', 'replace')))

# check for printers to prune
prunePrinters = []
connection = cups.Connection()
cupsprinters = connection.getPrinters()

for cupsprinter in cupsprinters:
  if cupsprinters[cupsprinter]['device-uri'].startswith( printer.PROTOCOL ):
    if cupsprinters[cupsprinter]['device-uri'] not in printeruris:
      prunePrinters.append(cupsprinter)

if len( prunePrinters ) > 0 :
  print "Found " + str(len( prunePrinters )) + " printers which no longer exist on cloud print:"
  for printer in prunePrinters:
    print printer
  answer = raw_input("Remove (Y/N)? ")
  if answer.startswith("Y") or answer.startswith("y"):
    for printer in prunePrinters:
      connection.deletePrinter(printer)
      print "Deleted",printer
  else:
    print "Not removing old printers"
