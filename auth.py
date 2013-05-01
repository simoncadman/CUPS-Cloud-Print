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

import json, os, grp, sys
from oauth2client import client
from oauth2client import multistore_file
from cloudprintrequestor import cloudprintrequestor 

class Auth:
  
  clientid = "843805314553.apps.googleusercontent.com"
  clientsecret = 'MzTBsY4xlrD_lxkmwFbBrvBv'
  config = '/etc/cloudprint.conf'
  
  def DeleteAccount(userid=None): # pragma: no cover 
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
  
  def AddAccount(storage, userid=None): # pragma: no cover 
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
				    scope='https://www.googleapis.com/auth/cloudprint',
				    user_agent=userid)
      auth_uri = flow.step1_get_authorize_url()
      print("Open this URL, grant access to CUPS Cloud Print, then provide the code displayed : \n\n" + auth_uri + "\n")
      code = raw_input('Code from Google: ')
      try:
	print("")
	credentials = flow.step2_exchange(code)
	storage.put(credentials)
	return credentials
      except:
	print("\nThe code does not seem to be valid, please try again.\n")
	
  AddAccount = staticmethod(AddAccount)
  
  def SetupAuth(interactive=False):
    """Sets up requestors with authentication tokens

    Args:
      interactive: boolean, when set to true can prompt user, otherwise returns False if authentication fails
      
    Returns:
      requestor, storage: Authenticated requestors and an instance of storage
    """
    modifiedconfig = False
    filedetails = os.stat(__file__)
    lpid = filedetails.st_gid
    
    # parse config file and extract useragents, which we use for account names
    userids = []
    if os.path.exists( Auth.config ):
      content_file = open(Auth.config, 'r')
      content = content_file.read()
      data = json.loads(content)
      for user in data['data']:
        userids.append(str(user['credential']['user_agent']))
    
    if len(userids) == 0:
      userids = [ None ]
    
    requestors = []
    for userid in userids:
      storage = multistore_file.get_credential_storage(
	    Auth.config,
	    Auth.clientid,
	    userid,
	    ['https://www.googleapis.com/auth/cloudprint'])
      credentials = storage.get()

      if not credentials and interactive: # pragma: no cover
	credentials = Auth.AddAccount(storage, userid)
	modifiedconfig = True
	if userid == None:
	  userid = credentials.user_agent
      elif not interactive and not credentials:
	return False
	
      # renew if expired
      requestor = cloudprintrequestor()
      if credentials.access_token_expired: # pragma: no cover 
	credentials.refresh(requestor)
	modifiedconfig = True
      
      requestor = credentials.authorize(requestor)
      requestor.setAccount(userid)
      requestors.append(requestor)
    
    # fix permissions
    if modifiedconfig: # pragma: no cover 
      try:
        os.chmod(Auth.config, 0640)
        os.chown(Auth.config, 0, lpid)
      except:
        sys.stderr.write("DEBUG: Cannot alter file permissions\n")
        pass

    return requestors, storage
  
  SetupAuth = staticmethod(SetupAuth)
