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

import json, os, grp
from oauth2client import client
from oauth2client import multistore_file
from cloudprintrequestor import cloudprintrequestor 

class Auth():
  
  clientid = "843805314553.apps.googleusercontent.com"
  clientsecret = 'MzTBsY4xlrD_lxkmwFbBrvBv'
  config = '/etc/cloudprint.conf'
  
  @staticmethod
  def AddAccount(storage, userid=None):
    if userid == None:
      userid = raw_input("Name for this user account? ")
      
    flow = client.OAuth2WebServerFlow(client_id=Auth.clientid,
				  client_secret=Auth.clientsecret,
				  scope='https://www.googleapis.com/auth/cloudprint',
				  user_agent=userid)
    auth_uri = flow.step1_get_authorize_url()
    print("Open this URL and provide the code: " + auth_uri)
    code = raw_input('Code from Google: ')
    credentials = flow.step2_exchange(code)
    storage.put(credentials)
    return credentials

  @staticmethod
  def SetupAuth(interactive=False):
    modifiedconfig = False
    
    # parse config file and extract useragents, which we use for account names
    userids = []
    if os.path.exists( Auth.config ):
      with open(Auth.config, 'r') as content_file:
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

      if not credentials and interactive:
	credentials = Auth.AddAccount(storage, userid)
	modifiedconfig = True
	if userid == None:
	  userid = credentials.user_agent
      elif not interactive and not credentials:
	return False
	
      # renew if expired
      requestor = cloudprintrequestor()
      if credentials.access_token_expired:
	credentials.refresh(requestor)
	modifiedconfig = False
      
      requestor = credentials.authorize(requestor)
      requestor.setAccount(userid)
      requestors.append(requestor)
    
    # fix permissions
    if modifiedconfig:
      os.chmod('/etc/cloudprint.conf', 0640)
      lpid = grp.getgrnam('lp').gr_gid
      os.chown('/etc/cloudprint.conf', 0, lpid)

    return requestors, storage