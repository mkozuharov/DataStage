# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

from __future__ import with_statement

import logging
import urlparse
import sys,os
import tempfile
import urllib
import urllib2
import zipfile
import unittest
import rdflib
import xattr
sys.path.append("../..")
from datastage.namespaces import OXDS, DCTERMS, RDF, FOAF, bind_namespaces
from datastage.dataset.base import Dataset
import datastage.util.serializers
from datastage.util.multipart import MultiPartFormData


logger = logging.getLogger(__name__)

class OXDSDataset(unittest.TestCase):
    logger.debug("Starting transfer to repository")
    def setUp(self):
    		return

    def tearDown(self):
    		return

    def get_opener(self):
			password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
			password_manager.add_password(None,urlparse.urlparse('http://databank/datastage/')._replace(path='/').geturl(),'admin','test')
			basic_auth_handler = PreemptiveBasicAuthHandler(password_manager)
			opener = urllib2.build_opener(basic_auth_handler)
			return opener
        
    def testMe(self):
            fname = "/tmp/a.txt" 
            stat_info = os.stat(fname)
            with open(fname, 'rb') as fileData:
					opener = self.get_opener()
					data = MultiPartFormData(files=[{'name': 'file','filename': fname,'stream': fileData,'mimetype': 'text/plain','size': stat_info.st_size}])
					#data = MultiPartFormData(files=[{'name': 'file','filename': fname,'stream': fileData,'mimetype': 'text/plain','size': stat_info.st_size,'Content-type': data.content_type,'Content-length': data.content_length}])
					opener.open('http://databank/datastage/'+ 'datasets/' + 'dd', data=data, method='POST',headers={'Content-type': data.content_type,'Content-length': data.content_length})
            return
            
class PreemptiveBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
    def https_request(self, request):
        credentials = self.passwd.find_user_password(None, request.get_full_url())
        if all(credentials):
            request.add_header(self.auth_header, 'Basic %s' % base64.b64encode(':'.join(credentials)))
        return request


# Assemble test suite

from MiscLib import TestUtils

def getTestSuite(select="unit"):
	testdict = {
		"unit": 
			[ 
			],
		"component":
			[ "testMe"
			],
		"integration":
			[ "testIntegration"
			],
		"pending":
			[ "testPending"
			]
		}
	return TestUtils.getTestSuite(OXDSDataset, testdict, select=select)

# Run unit tests directly from command line
if __name__ == "__main__":
	TestUtils.runTests("OXDSDataset", getTestSuite, sys.argv)

# End.


                   
