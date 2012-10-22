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

#

import os
import sys
import httplib,base64
import urllib2
import unittest
import subprocess
import re,zipfile
import time
import uuid

from sword2 import Connection, HttpLayer, HttpResponse, UrlLib2Layer, Entry
import urllib2

sys.path.append("..")
sys.path.append("../..")
from TestConfig import TestConfig
from MiscLib.ScanFiles import CollectFiles, joinDirName

class PreemptiveBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
    def https_request(self, request):
        credentials = self.passwd.find_user_password(None, request.get_full_url())
        if all(credentials):
            request.add_header(self.auth_header, 'Basic %s' % base64.b64encode(':'.join(credentials)))
        return request
    http_request = https_request

class TestDatasetSubmission(unittest.TestCase):

    def setUp(self):
        self.opener = None
        self.username="admin" 
        self.password="1779admin"
        self.repository_URL = "http://databank-test/"
        self.sword2_sd_url = "http://databank-test/swordv2/service-document/"      
        self.dataset_identifier="TestDatasetSubmission"  
        self.retry_limit=3
        self.retry_delay=2
        self.testpath = "TestDatasetSubmission"
        self.testpatt = re.compile("^.*$(?<!\.zip)")
        self.zipFileName = 'TestDatasetSubmission.zip'
        return

    def tearDown(self):
        return

    # Test cases
    def testNull(self):
        assert (True), "True expected"
        return
    
    def create_zip(self):
        files = CollectFiles(self.testpath,self.testpatt)
        z = zipfile.ZipFile(self.zipFileName,'w')
        for i in files: 
            n = joinDirName(i[0], i[1])
            z.write(n)
        z.close()
       

    def get_opener(self):
        if self.opener:
            return self.opener
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None,
                                          self.repository_URL,
                                          self.username,
                                          self.password)
    
        basic_auth_handler = PreemptiveBasicAuthHandler(password_manager)
        self.opener = urllib2.build_opener(basic_auth_handler)
        # Does opener need a close ?
        return self.opener
    
    def testServiceDocumentAccess(self):
        opener = self.get_opener()
        for i in range(10):
            conn = Connection(self.sword2_sd_url, error_response_raises_exceptions=False, http_impl=UrlLib2Layer(opener))
            conn.get_service_document()        
            self.assertIsNotNone(conn.sd, "Service document None (loop %d)"%(i))
            self.assertIsNotNone(conn.sd.workspaces, "Service document workspace None (loop %d)"%(i))
            self.assertNotEqual(len(conn.sd.workspaces),0, "Service document worksoacxe count %d (loop %d)"%(len(conn.sd.workspaces),i))
        return

    # Sentinel/placeholder tests

    def testUnits(self):
        assert (True)

    def testComponents(self):
        assert (True)

    def testIntegration(self):
        assert (True)

    def testPending(self):
        assert (False), "No pending test"

# Assemble test suite

from MiscLib import TestUtils

def getTestSuite(select="unit"):
    """
    Get test suite

    select  is one of the following:
            "unit"      return suite of unit tests only
            "component" return suite of unit and component tests
            "all"       return suite of unit, component and integration tests
            "pending"   return suite of pending tests
            name        a single named test to be run
    """
    testdict = {
        "unit": 
            [ "testUnits"
            , "testNull"
            ,"testServiceDocumentAccess"
            ],
        "component":
            [ "testComponents"
            ],
        "integration":
            [ "testIntegration"
            ],
        "pending":
            [ 

            ]
        }
    return TestUtils.getTestSuite(TestDatasetSubmission, testdict, select=select)

# Run unit tests directly from command line
if __name__ == "__main__":
    TestUtils.runTests("TestDatasetSubmission", getTestSuite, sys.argv)

# End.


