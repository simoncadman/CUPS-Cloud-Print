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

import json, os, sys
from oauth2client import client
from oauth2client import multistore_file
from cloudprintrequestor import cloudprintrequestor
from ccputils import Utils

class Auth:

    clientid = "843805314553.apps.googleusercontent.com"
    clientsecret = 'MzTBsY4xlrD_lxkmwFbBrvBv'
    config = '/etc/cloudprint.conf'

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

    DeleteAccount = staticmethod(DeleteAccount)

    def AddAccount(storage, userid=None, permissions=['https://www.googleapis.com/auth/cloudprint']):
        """Adds an account to the configuration file

        Args:
          storage: storage, instance of storage to store credentials in.
          userid: string, reference for the account

        Returns:
          credentials: A credentials instance with the account details
        """
        if userid == None:
            userid = raw_input("Name for this user account ( eg something@gmail.com )? ")

        while True:
            flow = client.OAuth2WebServerFlow(client_id=Auth.clientid,
                                          client_secret=Auth.clientsecret,
                                          scope=permissions,
                                          user_agent=userid)
            auth_uri = flow.step1_get_authorize_url()
            print "Open this URL, grant access to CUPS Cloud Print, then provide the code displayed : \n\n" + auth_uri + "\n"
            code = raw_input('Code from Google: ')
            try:
                print ""
                credentials = flow.step2_exchange(code)
                storage.put(credentials)

                # fix permissions
                Utils.FixFilePermissions(Auth.config)

                return credentials
            except Exception as e:
                print "\nThe code does not seem to be valid ( " + str(e) + " ), please try again.\n"

    AddAccount = staticmethod(AddAccount)

    def SetupAuth(interactive=False, permissions=['https://www.googleapis.com/auth/cloudprint']):
        """Sets up requestors with authentication tokens

        Args:
          interactive: boolean, when set to true can prompt user, otherwise returns False if authentication fails

        Returns:
          requestor, storage: Authenticated requestors and an instance of storage
        """
        modifiedconfig = False

        # parse config file and extract useragents, which we use for account names
        userids = []
        if os.path.exists( Auth.config ):
            content_file = open(Auth.config, 'r')
            content = content_file.read()
            data = json.loads(content)
            for user in data['data']:
                userids.append(str(user['credential']['user_agent']))
        else:
            modifiedconfig = True

        if len(userids) == 0:
            userids = [ None ]

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
                if userid == None:
                    userid = credentials.user_agent

            if credentials:
                # renew if expired
                requestor = cloudprintrequestor()
                if credentials.access_token_expired:
                    from oauth2client.client import AccessTokenRefreshError
                    try:
                        credentials.refresh(requestor)
                    except AccessTokenRefreshError as e:
                        sys.stderr.write("Failed to renew token (error: "+ str(e)  +"), if you have revoked access to CUPS Cloud Print in your Google Account, please delete /etc/cloudprint.conf and re-run /usr/share/cloudprint-cups/setupcloudprint.py\n")
                        sys.exit(1)

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

    SetupAuth = staticmethod(SetupAuth)

    def GetAccountNames ( requestors ):
        requestorAccounts = []
        for requestor in requestors:
            requestorAccounts.append(requestor.getAccount())
        return requestorAccounts
    
    GetAccountNames = staticmethod(GetAccountNames)