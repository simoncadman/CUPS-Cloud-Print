#! /usr/bin/env python2.7

import cups
from auth import Auth
from printer import Printer

while True:
  requestors, storage = Auth.SetupAuth(True)
  print "You currently have these accounts configured: "
  for requestor in requestors:
    print requestor.getAccount()
  answer = raw_input("Add more accounts? ")
  if not ( answer.startswith("Y") or answer.startswith("y") ):
    break
  else:
    Auth.AddAccount(storage)
      

for requestor in requestors:
  addedCount = 0
  answer = raw_input("Add all Google Cloud Print printers to local CUPS install from " + requestor.getAccount() + " ? ")
  if not ( answer.startswith("Y") or answer.startswith("y") ):
    print("Not adding printers automatically")
    continue

  prefix = raw_input("Use a prefix for names of created printers ( e.g. GCP- )? ")
  if prefix == "":
    print("Not using prefix")

  connection = cups.Connection()
  cupsprinters = connection.getPrinters()

  printer = Printer(requestor)
  printers = printer.getPrinters()
  if printers == None:
    print("No Printers Found")
    continue
    
  for ccpprinter in printers:
    uri = printer.printerNameToUri(ccpprinter['account'], ccpprinter['name'].encode('ascii', 'replace'))
    found = False
    for cupsprinter in cupsprinters:
      if cupsprinters[cupsprinter]['device-uri'] == uri:
	found = True
    
    if found == False:
      printername = prefix + ccpprinter['name'].encode('ascii', 'replace')
      
      # check if printer name already exists
      foundbyname = False
      for ccpprinter2 in cupsprinters:
	if cupsprinters[ccpprinter2]['printer-info'].replace(' ', '_') == printername.replace(' ', '_'):
	  foundbyname = True
      if ( foundbyname ) :
	answer = raw_input("Printer " + printername + " already exists, supply another name? ")
	if ( answer.startswith("Y") or answer.startswith("y") ):
	  printername = raw_input("New printer name? ")
	else:
	  answer = raw_input("Overwrite " + printername + " with new printer? ")
	  if ( answer.startswith("N") or answer.startswith("n") ):
	    printername = ""
      
      if printername != "":
	printer.addPrinter(printername, uri, connection)
	addedCount+=1
      
  if addedCount > 0:
    print("Added " + str(addedCount) + " new printers to CUPS")
  else:
    print("No new printers to add")

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
  print("Found " + str(len( prunePrinters )) + " printers which no longer exist on cloud print:")
  for printer in prunePrinters:
    print(printer)
  answer = raw_input("Remove? ")
  if answer.startswith("Y") or answer.startswith("y"):
    for printer in prunePrinters:
      connection.deletePrinter(printer)
      print("Deleted",printer)
  else:
    print("Not removing old printers")
