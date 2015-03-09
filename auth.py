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

import json
import os
import sys
import subprocess
# workaround for ubuntu 12.04 / older python-six version
try:
    from six.moves import urllib
except ImportError:
    import six
    import urllib
    import urlparse
    six.moves.urllib = urllib
    six.moves.urllib.parse = urlparse
    six.moves.urllib.parse.urlencode = urllib.urlencode

from oauth2client import client
from oauth2client import multistore_file
from cloudprintrequestor import CloudPrintRequestor
from ccputils import Utils
from oauth2client.client import AccessTokenRefreshError


class Auth(object):
    clientid = "843805314553.apps.googleusercontent.com"
    clientsecret = 'MzTBsY4xlrD_lxkmwFbBrvBv'
    config = '/etc/cloudprint.conf'
    normal_permissions = 'https://www.googleapis.com/auth/cloudprint'
    http_thread = None
    httpd = None
    code = None

    @staticmethod
    def RenewToken(interactive, requestor, credentials, storage, userid):
        try:
            credentials.refresh(requestor)
        except AccessTokenRefreshError as e:
            if not interactive:
                message = "ERROR: Failed to renew token for " + str(userid)
                message += " (error: "
                message += str(e)
                message += "), "
                message += "please re-run "
                message += "/usr/share/cloudprint-cups/"
                message += "setupcloudprint.py\n"
                sys.stderr.write(message)
                sys.exit(1)
            else:
                message = "Failed to renew token for " + str(userid) + " (error: "
                message += str(e) + "), "
                message += "authentication needs to be "
                message += "setup again:\n"
                sys.stderr.write(message)
                Auth.AddAccount(storage, userid)
                credentials = storage.get()
        return credentials

    @staticmethod
    def DeleteAccount(userid):
        """Delete an account from the configuration file

        Args:
          userid: string, reference for the account

        Returns:
          deleted: boolean , true on success
        """
        storage = multistore_file.get_credential_storage(
            Auth.config,
            Auth.clientid,
            userid,
            Auth.normal_permissions)
        return storage.delete()

    @staticmethod
    def SetupHttpReturnServer():
        import BaseHTTPServer
        import random
        import SocketServer
        from threading import Thread
        handler = BaseHTTPServer.BaseHTTPRequestHandler

        def do_GET(self):
            self.send_response(200)
            if "code=" in self.path:
                Auth.code = self.path[self.path.index('code=') + 5:]
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write("<html><head></head><body>Thank you !" +
                                 " Your Google printers will be added, you can " +
                                 "now close this window</body></html>")
        handler.do_GET = do_GET
        while (Auth.httpd is None):
            try:
                port = random.randint(12000, 20000)
                Auth.httpd = SocketServer.TCPServer(("", port), handler)
            except Exception:
                pass

        def http_server():
            Auth.httpd.serve_forever(0.5)
        Auth.http_thread = Thread(target=http_server)
        Auth.http_thread.start()
        return "http://localhost:%d/" % port

    @staticmethod
    def AddAccount(storage, userid=None, permissions=None):
        """Adds an account to the configuration file with an interactive dialog.

        Args:
          storage: storage, instance of storage to store credentials in.
          userid: string, reference for the account
          permissions: string or iterable of strings, scope(s) of the credentials being requested

        Returns:
          credentials: A credentials instance with the account details
        """
        if permissions is None:
            permissions = Auth.normal_permissions

        if userid is None:
            userid = raw_input(
                "Name for this user account ( eg something@gmail.com )? ")

            # setup storage again if just got userid now
            storage = multistore_file.get_credential_storage(
                Auth.config,
                Auth.clientid,
                userid,
                permissions)
        url = None
        while True:
            if Utils.hasGUI():
                url = Auth.SetupHttpReturnServer()
            Auth.code = None
            flow, auth_uri = Auth.AddAccountStep1(userid, permissions, url)
            message = "Open this URL if it doesn't, grant access to CUPS Cloud Print "
            message += "( for the " + userid + " account ), "
            message += "then provide the code displayed : \n\n"
            message += auth_uri + "\n"
            print message
            Utils.openBrowserWithUrl(auth_uri)
            if url is not None:
                from select import select
                print 'Code from Google: '
                while (Auth.code is None):
                    result, _, _ = select([sys.stdin], [], [], 0.5)
                    if result and Auth.code is None:
                        s = sys.stdin.readline()
                        if s != "":
                            Auth.code = s
                Auth.httpd.shutdown()
            else:
                Auth.code = raw_input('Code from Google: ')

            try:
                credentials = Auth.AddAccountStep2(userid, flow, Auth.code, storage, permissions)
                return credentials
            except Exception as e:
                message = "\nThe code does not seem to be valid ( "
                message += str(e) + " ), please try again.\n"
                print message

    @staticmethod
    def AddAccountStep1(userid, permissions=None, redirect_uri=None):
        """Executes step 1 of OAuth2WebServerFlow, without interaction.

        Args:
          userid: string, reference for the account
          permissions: string or iterable of strings, scope(s) of the credentials being requested

        Returns:
          tuple of:
            OAuth2WebServerFlow instance
            string auth_uri for user to visit
        """
        if redirect_uri is None:
            redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        if permissions is None:
            permissions = Auth.normal_permissions
        flow = client.OAuth2WebServerFlow(
            client_id=Auth.clientid,
            client_secret=Auth.clientsecret,
            scope=permissions,
            user_agent=userid,
            redirect_uri=redirect_uri)
        auth_uri = flow.step1_get_authorize_url()
        return flow, auth_uri

    @staticmethod
    def AddAccountStep2(userid, flow, code, storage=None, permissions=None):
        """Executes step 2 of OAuth2WebServerFlow, without interaction.

        Args:
          userid: string, reference for the account
          permissions: string or iterable of strings, scope(s) of the credentials being requested
          storage: storage, instance of storage to store credentials in.
          flow: OAuth2WebServerFlow, flow instance
          code: string, code representing user granting CCP permission to call GCP API for user

        Returns:
          credentials: A credentials instance with the account details
        """
        if permissions is None:
            permissions = Auth.normal_permissions

        if storage is None:
            storage = multistore_file.get_credential_storage(
                Auth.config,
                Auth.clientid,
                userid,
                permissions)

        credentials = flow.step2_exchange(code)
        storage.put(credentials)

        Utils.FixFilePermissions(Auth.config)

        return credentials

    @staticmethod
    def SetupAuth(interactive=False, permissions=None, testUserIds=None):
        """Sets up requestors with authentication tokens

        Args:
          interactive: boolean, when set to true can prompt user, otherwise
                       returns False if authentication fails

        Returns:
          requestor, storage: Authenticated requestors and an instance
                              of storage
        """
        if permissions is None:
            permissions = Auth.normal_permissions
        modifiedconfig = False

        # parse config file and extract useragents, which we use for account
        # names
        userids = []
        if testUserIds is not None:
            userids = testUserIds
        if os.path.exists(Auth.config):
            data = json.loads(Utils.ReadFile(Auth.config))
            if 'data' in data:
                for user in data['data']:
                    userids.append(str(user['credential']['user_agent']))
        else:
            Utils.WriteFile(Auth.config, '{}')
            Utils.FixFilePermissions(Auth.config)
            modifiedconfig = True

        if len(userids) == 0:
            userids = [None]

        requestors = []
        storage = None
        credentials = None
        for userid in userids:
            if userid is not None:
                storage = multistore_file.get_credential_storage(
                    Auth.config,
                    Auth.clientid,
                    userid,
                    permissions)
                credentials = storage.get()

            if not credentials and interactive:
                credentials = Auth.AddAccount(storage, userid, permissions)
                modifiedconfig = True
                if userid is None:
                    userid = credentials.user_agent

            if credentials:
                # renew if expired
                requestor = CloudPrintRequestor()
                if credentials.access_token_expired:
                    Auth.RenewToken(interactive, requestor, credentials, storage, userid)
                requestor = credentials.authorize(requestor)
                requestor.setAccount(userid)
                requestors.append(requestor)

        # fix permissions
        if modifiedconfig:
            Utils.FixFilePermissions(Auth.config)

        if not credentials:
            return False, False
        else:
            return requestors, storage

    @staticmethod
    def GetAccountNames(requestors):
        requestorAccounts = []
        for requestor in requestors:
            requestorAccounts.append(requestor.getAccount())
        return requestorAccounts
