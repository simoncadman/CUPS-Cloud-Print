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

import subprocess
import os
import logging
import sys
import grp
import mimetypes
import base64


class Utils:
    logpath = '/var/log/cups/cloudprint_log'

    # Countries where letter sized paper is used, according to:
    # http://en.wikipedia.org/wiki/Letter_(paper_size)
    _LETTER_COUNTRIES = set(('US', 'CA', 'MX', 'BO', 'CO', 'VE', 'PH', 'CL'))

    @staticmethod
    def FixFilePermissions(filename):
        filePermissions = True
        fileOwnerships = True
        currentStat = None
        if os.path.exists(filename):
            currentStat = os.stat(filename)

        if currentStat is None or currentStat.st_mode != 0o100660:
            try:
                os.chmod(filename, 0o100660)
            except:
                filePermissions = False
                sys.stderr.write(
                    "DEBUG: Cannot alter " +
                    filename +
                    " file permissions\n")
                pass

        if currentStat is None or currentStat.st_gid != Utils.GetLPID():
            try:
                os.chown(filename, -1, Utils.GetLPID())
            except:
                fileOwnerships = False
                sys.stderr.write(
                    "DEBUG: Cannot alter " +
                    filename +
                    " file ownership\n")
                pass

        return filePermissions, fileOwnerships

    @staticmethod
    def SetupLogging(logpath=None):
        returnValue = True
        logformat = "%(asctime)s|%(levelname)s|%(message)s"
        dateformat = "%Y-%m-%d %H:%M:%S"
        if logpath is None:
            logpath = Utils.logpath
        try:
            logging.basicConfig(
                filename=logpath,
                level=logging.INFO,
                format=logformat,
                datefmt=dateformat)
            Utils.FixFilePermissions(logpath)
        except:
            logging.basicConfig(
                level=logging.INFO,
                format=logformat,
                datefmt=dateformat)
            logging.error("Unable to write to log file " + logpath)
            returnValue = False
        return returnValue

    @staticmethod
    def fileIsPDF(filename):
        """Check if a file is or isnt a PDF

        Args:
        filename: string, name of the file to check
        Returns:
        boolean: True = is a PDF, False = not a PDF.
        """
        p = subprocess.Popen(["file", filename.lstrip('-')], stdout=subprocess.PIPE)
        output = p.communicate()[0]
        return "PDF document" in output

    @staticmethod
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    @staticmethod
    def which(program):
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if Utils.is_exe(exe_file):
                return exe_file
        return None

    @staticmethod
    def GetLPID(default='lp', alternative='cups', useFiles=True,
                blacklistedGroups=None,
                useFilesOnly=False):
        if blacklistedGroups is None:
            blacklistedGroups = ['adm', 'wheel', 'root']
        
        blacklistedGroupIds = []
        for group in blacklistedGroups:
            try:
                blacklistedGroupIds.append(grp.getgrnam(group).gr_gid)
            except:
                logging.debug("Group " + group + " not found")

        if useFiles:
            # check files in order
            for cupsConfigFile in ['/var/log/cups/access_log',
                                   '/etc/cups/ppd',
                                   '/usr/local/etc/cups/ppd']:
                if os.path.exists(cupsConfigFile):
                    configGid = os.stat(cupsConfigFile).st_gid
                    if configGid not in blacklistedGroupIds:
                        return configGid
                    else:
                        logging.debug(
                            "Group " +
                            group +
                            " excluded as blacklisted")

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
        if lpgrp is None:
            return None
        else:
            return lpgrp.gr_gid

    @staticmethod
    def ShowVersion(CCPVersion):
        if len(sys.argv) == 2 and sys.argv[1] == 'version':
            print "CUPS Cloud Print Version " + CCPVersion
            sys.exit(0)
        return False

    @staticmethod
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
        except IOError as e:
            print 'ERROR: Error opening %s\n%s', pathname, e
            return None

    @staticmethod
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
        except IOError as e:
            status = False

        return status

    @staticmethod
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
        file_type = mimetypes.guess_type(
            pathname)[0] or 'application/octet-stream'
        data = Utils.ReadFile(pathname)
        if data is None:
            return None

        # Convert binary data to base64 encoded data.
        header = 'data:%s;base64,' % file_type
        b64data = header + base64.b64encode(data)

        if Utils.WriteFile(b64_pathname, b64data):
            return b64_pathname
        else:
            return None

    @staticmethod
    def GetLanguage(locale):
        language = 'en'
        if len(locale) < 1 or locale[0] is None:
            return language
        defaultlocale = locale[0]
        language = defaultlocale
        if '_' in language:
            language = language.split("_")[0]
        return language

    @staticmethod
    def GetDefaultPaperType(locale):
        defaultpapertype = "Letter"
        if len(locale) < 1 or locale[0] is None:
            return defaultpapertype
        if len(locale[0].split('_')) > 1 and locale[0].split('_')[1] not in Utils._LETTER_COUNTRIES:
            defaultpapertype = "A4"
        return defaultpapertype
