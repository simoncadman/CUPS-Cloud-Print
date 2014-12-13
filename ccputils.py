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
import base64
import fcntl
import termios
import struct


class Utils(object):
    logpath = '/var/log/cups/cloudprint_log'

    # Countries where letter sized paper is used, according to:
    # http://en.wikipedia.org/wiki/Letter_(paper_size)
    _LETTER_COUNTRIES = set(('US', 'CA', 'MX', 'BO', 'CO', 'VE', 'PH', 'CL'))
    PROTOCOL_NAME = 'gcp'
    PROTOCOL = PROTOCOL_NAME + '://'
    OLD_PROTOCOL_NAME = 'cloudprint'
    OLD_PROTOCOL = OLD_PROTOCOL_NAME + '://'
    _MIMETYPES_JOBTYPES = {'pdf': 'application/pdf',
                           'other': 'application/octet-stream',
                           'jpg': 'image/jpeg',
                           'png': 'image/png'}

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
            except Exception:
                filePermissions = False
                sys.stderr.write(
                    "DEBUG: Cannot alter " +
                    filename +
                    " file permissions\n")

        if currentStat is None or currentStat.st_gid != Utils.GetLPID():
            try:
                os.chown(filename, -1, Utils.GetLPID())
            except Exception:
                fileOwnerships = False
                sys.stderr.write(
                    "DEBUG: Cannot alter " +
                    filename +
                    " file ownership\n")

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
        except Exception:
            logging.basicConfig(
                level=logging.INFO,
                format=logformat,
                datefmt=dateformat)
            logging.error("Unable to write to log file " + logpath)
            returnValue = False
        return returnValue

    @staticmethod
    def fileIsPDF(filedata):
        """Check if a file is or isnt a PDF

        Args:
        filename: string, name of the file to check
        Returns:
        boolean: True = is a PDF, False = not a PDF.
        """
        p = subprocess.Popen(["file", '-'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        output = p.communicate(filedata)[0]
        logging.debug("File output was: " + output)
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
            except Exception:
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
                            str(configGid) +
                            " excluded as blacklisted")

        if useFilesOnly:
            return None

        # try lp first, then cups
        lpgrp = None
        try:
            lpgrp = grp.getgrnam(default)
        except Exception:
            try:
                lpgrp = grp.getgrnam(alternative)
            except Exception:
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
        except IOError:
            status = False

        return status

    @staticmethod
    def Base64Encode(data, jobtype):
        """Convert a file to a base64 encoded file.

        Args:
          pathname: data to base64 encode
          jobtype: job type being encoded - pdf, jpg etc
        Returns:
          string, base64 encoded string.
        For more info on data urls, see:
          http://en.wikipedia.org/wiki/Data_URI_scheme
        """
        # Convert binary data to base64 encoded data.
        mimetype = Utils._MIMETYPES_JOBTYPES['other']
        if jobtype in Utils._MIMETYPES_JOBTYPES:
            mimetype = Utils._MIMETYPES_JOBTYPES[jobtype]
        header = 'data:%s;base64,' % mimetype
        return header + base64.b64encode(data)

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

    @staticmethod
    def GetWindowSize(winsize=None):
        """Gets window height and width.

        Gets window (aka terminal, console) height and width using IOCtl Get WINdow SiZe
        method.

        Returns:
            The tuple (height, width) of the window as integers, or None if the
            windows size isn't available.
        """
        try:
            structbytes = struct.pack('HHHH', 0, 0, 0, 0)
            if winsize is None:
                winsize = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, structbytes)
            height, width = struct.unpack('HHHH', winsize)[:2]
        except Exception:
            return None

        if height > 0 and width > 0:
            return height, width
        return None

    @staticmethod
    def StdInToTempFile(jobID, userName, stdin=None):
        if stdin is None:
            stdin = sys.stdin

        tmpDir = os.getenv('TMPDIR')
        if not tmpDir:
            tmpDir = "/tmp"
        tempFile = '%s/%s-%s-cupsjob-%s' % \
            (tmpDir, jobID, userName, str(os.getpid()))
        OUT = open(tempFile, 'w')

        if not OUT:
            logging.error("Cannot write temp file: %s", tempFile)
            print "ERROR: Cannot write " + tempFile
            sys.exit(1)

        for line in stdin:
            OUT.write(line)

        OUT.close()
        return tempFile
