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
    CCPVersion = "20140202 015558"
    print "CUPS Cloud Print Delete Account Script Version " + CCPVersion
    sys.exit(0)

logpath = '/var/log/cups/cloudprint_log'
try:
    logging.basicConfig(filename=logpath,level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    logging.error("Unable to write to log file "+ logpath)

while True:
  result = Auth.SetupAuth(False)
  if not result:
    print "No accounts are currently setup"
    break
  else:
    requestors, storage = result
    print "You currently have these accounts configured: "
    i=0
    accounts = []
    for requestor in requestors:
        i+=1
        accounts.append(requestor.getAccount())
        print str(i) + ") " + requestor.getAccount()
    print "0) Exit"
    answer = raw_input("Which account to delete (1-" + str(i) + ") ? ")
    if ( answer.isdigit() and int(answer) <= i and int(answer) >= 1 ):
        if ( Auth.DeleteAccount(accounts[int(answer)-1]) == None ):
            print accounts[int(answer)-1] + " deleted."
            deleteprintersanswer = raw_input("Also delete associated printers? ")
            if deleteprintersanswer.startswith("Y") or deleteprintersanswer.startswith("y"):
                printer = Printer(requestors)
                printers, connection = printer.getCUPSPrintersForAccount(accounts[int(answer)-1])
                if len(printers) == 0:
                    print "No printers to delete"
                else:
                    for cupsPrinter in printers:
                        print "Deleting " + cupsPrinter['printer-info']
                        deleteReturnValue = connection.deletePrinter(cupsPrinter['printer-info'])
                        if deleteReturnValue != None:
                            print "Error deleting printer: " + str(deleteReturnValue)
            else:
                print "Not deleting associated printers"
        else:
            print "Error deleting stored credentials, perhaps /etc/cloudprint.conf is not writable?"
    elif ( answer == "0" ):
        break
    else:
        print "Invalid response, use '0' to exit"