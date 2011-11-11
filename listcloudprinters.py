#! /usr/bin/python
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

import sys
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
  print "ERROR: Invalid username/password"
  sys.exit(1)

printers = Printer.GetPrinters(tokens)
if printers == None:
  print "No Printers Found"
  sys.exit(1)

for printer in printers:
  print printer['name'] + ' - ' + Printer.printerNameToUri(printer['name'])
