#! /bin/sh
"true" '''\'
if command -v python2 > /dev/null; then
  exec python2 "$0" "$@"
else
  exec python "$0" "$@"
fi
exit $?
'''

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

def getDriveFiles(requestors):
    returnValue = []
    for requestor in requestors:
        responseobj = requestor.doRequest(
            'files', endpointurl="https://www.googleapis.com/drive/v2")
        if 'error' in responseobj:
            print "Errored fetching files from drive"
        else:
            for item in responseobj['items']:
                returnValue.append(item)
    if len(returnValue) == 0:
        return None
    return returnValue

if __name__ == '__main__':  # pragma: no cover
    import sys
    import logging
    sys.path.insert(0, ".")

    from auth import Auth
    from ccputils import Utils
    Utils.SetupLogging()

    # line below is replaced on commit
    CCPVersion = "20140501 203545"
    Utils.ShowVersion(CCPVersion)

    requestors, storage = Auth.SetupAuth(True,
        permissions=['https://www.googleapis.com/auth/cloudprint', 'https://www.googleapis.com/auth/drive.readonly'])
    files = getDriveFiles(requestors)
    if files is None:
        print "No Files Found"
        sys.exit(1)

    for drivefile in files:
        if len(sys.argv) == 2 and drivefile['title'] == sys.argv[1] + '.pdf':
            print drivefile['fileSize']
            sys.exit(0)
        elif len(sys.argv) != 2:
            print drivefile['title']
