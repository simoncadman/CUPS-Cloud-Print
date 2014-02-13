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

import json, pytest
from cloudprintrequestor import cloudprintrequestor

global requestor

def setup_function(function):
    global requestor
    requestor = cloudprintrequestor()
    
def test_requestor():
    requestor.setAccount('testdetails')
    assert requestor.getAccount() == 'testdetails'
    
def test_request():
    assert requestor.doRequest(path="/test",testResponse=json.dumps("randomstring1233")) == "randomstring1233"
    with pytest.raises(ValueError):
        assert requestor.doRequest(path="/test",testResponse="")