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
from oauth2client import client
from oauth2client import multistore_file
from cloudprintrequestor import CloudPrintRequestor
from ccputils import Utils
from oauth2client.client import AccessTokenRefreshError


class Auth:
    clientid = "843805314553.apps.googleusercontent.com"
    clientsecret = 'MzTBsY4xlrD_lxkmwFbBrvBv'
    config = '/etc/cloudprint.conf'

    @staticmethod
    def RenewToken(interactive, requestor, credentials, storage, userid):
        try:
            credentials.refresh(requestor)
        except AccessTokenRefreshError as e:
            if not interactive:
                    message = "ERROR: Failed to renew token "
                    message += "(error: "
                    message += str(e)
                    message += "), "
                    message += "please re-run "
                    message += "/usr/share/cloudprint-cups/"
                    message += "setupcloudprint.py\n"
                    sys.stderr.write(message)
                    sys.exit(1)
            else:
                    message = "Failed to renew token (error: "
                    message += str(e) + "), "
                    message += "authentication needs to be "
                    message += "setup again:\n"
                    sys.stderr.write(message)
                    Auth.AddAccount(storage, userid)
                    credentials = storage.get()
        return credentials

    @staticmethod
    def DeleteAccount(userid=None):
        """Delete an account from the configuration file

        Args:
          storage: storage, instance of storage to store credentials in.
          userid: string, reference for the account

        Returns:
          deleted: boolean , true on success
        """
        storage = multistore_file.get_credential_storage(
            Auth.config,
            Auth.clientid,
            userid,
            ['https://www.googleapis.com/auth/cloudprint'])
        return storage.delete()

    @staticmethod
    def AddAccount(storage, userid=None,
                   permissions=None):
        """Adds an account to the configuration file

        Args:
          storage: storage, instance of storage to store credentials in.
          userid: string, reference for the account

        Returns:
          credentials: A credentials instance with the account details
        """
        if permissions is None:
            permissions = ['https://www.googleapis.com/auth/cloudprint']
        
        if userid is None:
            userid = raw_input(
                "Name for this user account ( eg something@gmail.com )? ")

        while True:
            flow = client.OAuth2WebServerFlow(client_id=Auth.clientid,
                                              client_secret=Auth.clientsecret,
                                              scope=permissions,
                                              user_agent=userid)
            auth_uri = flow.step1_get_authorize_url()
            message = "Open this URL, grant access to CUPS Cloud Print,"
            message += "then provide the code displayed : \n\n"
            message += auth_uri + "\n"
            print message
            code = raw_input('Code from Google: ')
            try:
                print ""
                credentials = flow.step2_exchange(code)
                storage.put(credentials)

                # fix permissions
                Utils.FixFilePermissions(Auth.config)

                return credentials
            except Exception as e:
                message = "\nThe code does not seem to be valid ( "
                message += str(e) + " ), please try again.\n"
                print message

    @staticmethod
    def SetupAuth(interactive=False,
                  permissions=None):
        """Sets up requestors with authentication tokens

        Args:
          interactive: boolean, when set to true can prompt user, otherwise
                       returns False if authentication fails

        Returns:
          requestor, storage: Authenticated requestors and an instance
                              of storage
        """
        if permissions is None:
            permissions = ['https://www.googleapis.com/auth/cloudprint']
        
        modifiedconfig = False

        # parse config file and extract useragents, which we use for account
        # names
        userids = []
        if os.path.exists(Auth.config):
            content_file = open(Auth.config, 'r')
            content = content_file.read()
            data = json.loads(content)
            for user in data['data']:
                userids.append(str(user['credential']['user_agent']))
        else:
            modifiedconfig = True

        if len(userids) == 0:
            userids = [None]

        requestors = []
        for userid in userids:
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
