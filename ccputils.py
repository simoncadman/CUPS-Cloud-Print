#    CUPS Cloudprint - Print via Google Cloud Print
#    Copyright (C) 2014 Simon Cadman
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

import subprocess, os, logging, sys, grp

class Utils:
    
    logpath = '/var/log/cups/cloudprint_log'

    def FixFilePermissions(filename):
        filePermissions = True
        fileOwnerships = True
        currentStat = None
        if os.path.exists(filename):
            currentStat = os.stat(filename)

        if currentStat == None or currentStat.st_mode != 0100660:
            try:
                os.chmod(filename, 0100660)
            except:
                filePermissions = False
                sys.stderr.write("DEBUG: Cannot alter "+ filename +" file permissions\n")
                pass
            
        if currentStat == None or currentStat.st_gid != Utils.GetLPID():  
            try:
                os.chown(filename, -1, Utils.GetLPID())
            except:
                fileOwnerships = False
                sys.stderr.write("DEBUG: Cannot alter "+ filename +" file ownership\n")
                pass
            
        return filePermissions, fileOwnerships

    FixFilePermissions = staticmethod(FixFilePermissions)

    def SetupLogging(logpath=None):
        returnValue = True
        logformat = "%(asctime)s|%(levelname)s|%(message)s"
        dateformat = "%Y-%m-%d %H:%M:%S"
        if logpath == None:
            logpath = Utils.logpath
        try:
            logging.basicConfig(filename=logpath,level=logging.INFO,format=logformat,datefmt=dateformat)
            Utils.FixFilePermissions(logpath)
        except:
            logging.basicConfig(level=logging.INFO,format=logformat,datefmt=dateformat)
            logging.error("Unable to write to log file "+ logpath)
            returnValue = False
        return returnValue

    SetupLogging = staticmethod(SetupLogging)
    
    def fileIsPDF ( filename ) :
        """Check if a file is or isnt a PDF

        Args:
        filename: string, name of the file to check
        Returns:
        boolean: True = is a PDF, False = not a PDF.
        """
        result = 0
        p = subprocess.Popen(["file", filename.lstrip('-')], stdout=subprocess.PIPE)
        output = p.communicate()[0]
        result = p.returncode
        if result != 0:
            return False
        else:
            return "PDF document" in output

    fileIsPDF = staticmethod(fileIsPDF)
    
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    is_exe = staticmethod(is_exe)
    
    def which(program):
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if Utils.is_exe(exe_file):
                return exe_file
        return None
    
    which = staticmethod(which)
    
    def GetLPID(default='lp', alternative='cups', useFiles=True):
        if useFiles:
            # check files in order
            for cupsConfigFile in [ '/etc/cups/cupsd.conf', '/usr/local/etc/cups/cupsd.conf' ]:
                if os.path.exists(cupsConfigFile):
                    return os.stat(cupsConfigFile).st_gid 
        
        # try lp first, then cups
        lpgrp = None
        try:
            lpgrp = grp.getgrnam(default)
        except:
            try:
                lpgrp = grp.getgrnam(alternative)
            except:
                pass
        if lpgrp == None:
            return None
        else:
            return lpgrp.gr_gid

    GetLPID = staticmethod(GetLPID)
