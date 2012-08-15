#! /usr/bin/env python2.7

import sys, os, grp, getpass, cups
from auth import Auth
from printer import Printer

useConfigDetails = True

tokens = None
addedCount = 0
requestors = Auth.SetupAuth(True)

while True:
  print "You currently have these accounts configured: "
  for requestor in requestors:
    print requestor.getAccount()
  answer = raw_input("Add more accounts? ")
  if not ( answer.startswith("Y") or answer.startswith("y") ):
    break
  else:
    print "Adding account"
      
for requestor in requestors:
  answer = raw_input("Add all Google Cloud Print printers to local CUPS install from " + requestor.getAccount() + " ? ")
  if not ( answer.startswith("Y") or answer.startswith("y") ):
    print("Not adding printers automatically")
    sys.exit(0)

  prefix = raw_input("Use a prefix for names of created printers ( e.g. GCP- )? ")
  if prefix == "":
    print("Not using prefix")

  connection = cups.Connection()
  cupsprinters = connection.getPrinters()

  printer = Printer(requestor)
  printers = printer.getPrinters()
  if printers == None:
    print("No Printers Found")
    sys.exit(1)
    
  printeruris = []

  for ccpprinter in printers:
    uri = printer.printerNameToUri(ccpprinter['account'], ccpprinter['name'].encode('ascii', 'replace'))
    found = False
    printeruris.append(uri)
    for cupsprinter in cupsprinters:
      if cupsprinters[cupsprinter]['device-uri'] == uri:
	found = True
    if found == False:
      printer.AddPrinter(prefix + ccpprinter['name'].encode('ascii', 'replace'), uri, connection)
      addedCount+=1
      
  if addedCount > 0:
    print("Added",addedCount,"new printers to CUPS")
  else:
    print("No new printers to add")
    
  # check for printers to prune
  prunePrinters = []
  cupsprinters = connection.getPrinters()

  for cupsprinter in cupsprinters:
    if cupsprinters[cupsprinter]['device-uri'].startswith( Printer.PROTOCOL ):
      if cupsprinters[cupsprinter]['device-uri'] not in printeruris:
	prunePrinters.append(cupsprinter)

  if len( prunePrinters ) > 0 :
    print("Found",len( prunePrinters ),"printers with no longer exist on cloud print:")
    for printer in prunePrinters:
      print(printer)
    answer = raw_input("Remove? ")
    if answer.startswith("Y") or answer.startswith("y"):
      for printer in prunePrinters:
	connection.deletePrinter(printer)
	print("Deleted",printer)
    else:
      print("Not removing old printers")
