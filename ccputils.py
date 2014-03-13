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

import subprocess, os, logging, sys, grp, mimetypes, base64

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
        if result != 0: # pragma: no cover
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
    
    def GetLPID(default='lp', alternative='cups', useFiles=True, blacklistedGroups=[ 'adm', 'wheel', 'root' ], useFilesOnly=False ):
        blacklistedGroupIds = []
        for group in blacklistedGroups:
            try:
                blacklistedGroupIds.append( grp.getgrnam(group).gr_gid )
            except:
                logging.debug("Group " + group + " not found" )
        
        if useFiles:
            # check files in order
            for cupsConfigFile in [ '/var/log/cups/access_log', '/etc/cups/ppd', '/usr/local/etc/cups/ppd' ]:
                if os.path.exists(cupsConfigFile):
                    if os.stat(cupsConfigFile).st_gid not in blacklistedGroupIds:
                        return os.stat(cupsConfigFile).st_gid
                    else:
                        logging.debug("Group " + group + " excluded as blacklisted" )
        
        if useFilesOnly:
             return None
        
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

    def ShowVersion(CCPVersion):
        if len(sys.argv) == 2 and sys.argv[1] == 'version':
            print "CUPS Cloud Print Version " + CCPVersion
            sys.exit(0)
        return False
    
    ShowVersion = staticmethod(ShowVersion)
    
    def ReadFile(pathname):
        """Read contents of a file and return content.

        Args:
          pathname: string, (path)name of file.
        Returns:
          string: contents of file.
        """
        try:
            f = open(pathname, 'rb')
            s = f.read()
            return s
        except IOError, e:
            print 'ERROR: Error opening %s\n%s', pathname, e
            return None
    
    ReadFile = staticmethod(ReadFile)

    def WriteFile(file_name, data):
        """Write contents of data to a file_name.

        Args:
          file_name: string, (path)name of file.
          data: string, contents to write to file.
        Returns:
          boolean: True = success, False = errors.
        """
        status = True

        try:
            f = open(file_name, 'wb')
            f.write(data)
            f.close()
        except IOError, e:
            status = False

        return status

    WriteFile = staticmethod(WriteFile)

    def Base64Encode(pathname):
        """Convert a file to a base64 encoded file.

        Args:
          pathname: path name of file to base64 encode..
        Returns:
          string, name of base64 encoded file.
        For more info on data urls, see:
          http://en.wikipedia.org/wiki/Data_URI_scheme
        """
        b64_pathname = pathname + '.b64'
        file_type = mimetypes.guess_type(pathname)[0] or 'application/octet-stream'
        data = Utils.ReadFile(pathname)
        if data == None:
            return None

        # Convert binary data to base64 encoded data.
        header = 'data:%s;base64,' % file_type
        b64data = header + base64.b64encode(data)

        if Utils.WriteFile(b64_pathname, b64data):
            return b64_pathname
        else:
            return None

    Base64Encode = staticmethod(Base64Encode)
    
    def GetDriveFiles ( requestors ):
        returnValue = []
        for requestor in requestors:
            responseobj = requestor.doRequest( 'files', endpointurl="https://www.googleapis.com/drive/v2" )
            if 'error' in responseobj:
                print "Errored fetching files from drive"
                pass
            else:
                for item in responseobj['items']:
                    returnValue.append( item )
        if len(returnValue) == 0:
            return None
        return returnValue

    GetDriveFiles = staticmethod(GetDriveFiles)