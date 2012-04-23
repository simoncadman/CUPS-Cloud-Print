#! /usr/bin/env python2.7
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

import mimetools, time, sys
from config import Config
from auth import Auth
from printer import Printer

try:
  configuration = Config()
except IOError:
  print "ERROR: Unable to load configuration file, run", sys.path[0] + "/setupcloudprint.py within a terminal"
  sys.exit(1)
except Exception as error:
  print "ERROR: Unknown error when reading configuration file - ", error
  sys.exit(1)

email = configuration.get("Google", "Username")
password = configuration.get("Google", "Password")

tokens = Auth.GetAuthTokens(email, password)
if tokens == None:
  print "ERROR: Invalid username/password, run", sys.path[0] + "/setupcloudprint.py within a terminal"
  sys.exit(1)

printername = sys.argv[2].replace(Printer.PROTOCOL,'')

printerid = Printer.GetPrinter(printername, tokens)
if printerid == None:
  print "ERROR: Printer '" + printername + "' not found"
  sys.exit(1)

name = sys.argv[1]
if len(sys.argv) > 3:
  name = sys.argv[3]

if Printer.SubmitJob(printerid, 'pdf', sys.argv[1], name, tokens):
  print "INFO: Successfully printed"
  sys.exit(0)
else:
  print "ERROR: Failed to submit job to cloud print"
  sys.exit(1)
