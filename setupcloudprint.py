#! /usr/bin/env python2.7

import sys, getpass, cups
from config import Config
from auth import Auth
from printer import Printer

useConfigDetails = True

configuration = Config(True)
if configuration.loadError:
  useConfigDetails = False
  
tokens = None
addedCount = 0
success = False
while success == False:
  if useConfigDetails:
    print "Using authentication details from configuration"
    username = configuration.get('Google', 'username')
    password = configuration.get('Google', 'password')
  else:
    print "Please enter your Google Credentials, or CTRL+C to exit: "
    username = raw_input("Username: ")
    password = getpass.getpass()
  
  tokens = Auth.GetAuthTokens(username, password)
  if tokens == None:
    print "Invalid username/password"
    success = False
    useConfigDetails = False
  else:
    print "Successfully connected"
    configuration.set('Google', 'username', username)
    configuration.set('Google', 'password', password)
    configuration.save()
    success = True
    
  
answer = raw_input("Add all Google Cloud Print printers to local CUPS install? ")
if not ( answer.startswith("Y") or answer.startswith("y") ):
  print "Not adding printers automatically"
  sys.exit(0)

prefix = raw_input("Use a prefix for names of created printers ( e.g. GCP- )? ")
if prefix == "":
  print "Not using prefix"

connection = cups.Connection()
cupsprinters = connection.getPrinters()

printers = Printer.GetPrinters(tokens)
if printers == None:
  print "No Printers Found"
  sys.exit(1)
  
printeruris = []

for printer in printers:
  uri = Printer.printerNameToUri(printer['name'])
  found = False
  printeruris.append(uri)
  for cupsprinter in cupsprinters:
    if cupsprinters[cupsprinter]['device-uri'] == uri:
      found = True
  if found == False:
    Printer.AddPrinter(prefix + printer['name'], uri, connection)
    addedCount+=1
    
if addedCount > 0:
  print "Added",addedCount,"new printers to CUPS"
else:
  print "No new printers to add"
  
# check for printers to prune
prunePrinters = []
cupsprinters = connection.getPrinters()

for cupsprinter in cupsprinters:
  if cupsprinters[cupsprinter]['device-uri'].startswith( Printer.PROTOCOL ):
    if cupsprinters[cupsprinter]['device-uri'] not in printeruris:
      prunePrinters.append(cupsprinter)

if len( prunePrinters ) > 0 :
  print "Found",len( prunePrinters ),"printers with no longer exist on cloud print:"
  for printer in prunePrinters:
    print printer
  answer = raw_input("Remove? ")
  if answer.startswith("Y") or answer.startswith("y"):
    for printer in prunePrinters:
      connection.deletePrinter(printer)
      print "Deleted",printer
  else:
    print "Not removing old printers"
