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

if __name__ == '__main__': # pragma: no cover
    import cups, os, json, sys, logging
    from auth import Auth
    from printer import Printer

    from ccputils import Utils
    Utils.SetupLogging()
    
    # line below is replaced on commit
    CCPVersion = "20140316 140738"
    Utils.ShowVersion(CCPVersion)
    
    while True:
        result, storage = Auth.SetupAuth(False)
        if not result:
            print "No accounts are currently setup"
            break
        else:
            requestors = result
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
