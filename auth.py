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

import urllib

class Auth():
  SERVICE = 'cloudprint'
  CLIENT_NAME = 'CUPS Cloud Print'
  LOGIN_URL = 'https://www.google.com/accounts/ClientLogin'
  
  @staticmethod
  def GetAuthTokens(email, password):
      """Assign login credentials from GAIA accounts service.

      Args:
	email: Email address of the Google account to use.
	password: Cleartext password of the email account.
      Returns:
	dictionary containing Auth token.
      """
      tokens = {}

      # We still need to get the Auth token.    
      params = {'accountType': 'GOOGLE',
		'Email': email,
		'Passwd': password,
		'service': Auth.SERVICE,
		'source': Auth.CLIENT_NAME}
      stream = urllib.urlopen(Auth.LOGIN_URL, urllib.urlencode(params))

      success = False
      for line in stream:
	if line.strip().startswith('Auth='):
	  tokens['Auth'] = line.strip().replace('Auth=', '')
	  success = True
      
      if not success:
	return None
      
      return tokens
