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
# $Id: TestAll.py 1047 2009-01-15 14:48:58Z graham $
#
# Unit testing for WebBrick library functions (Functions.py)
# See http://pyunit.sourceforge.net/pyunit.html
#

import sys, unittest, logging

# Add main library directory to python path
sys.path.append("../..")
sys.path.append("..")

import TestConfig
import TestSubmitDataset
import TestSubmitDatasetHandler
import TestDirectoryListingHandler
import TestMetadataMerging
import TestGetDatasetMetadataHandler
import TestHttpSession

# Code to run unit tests from all library test modules
def getTestSuite(select="all"):
    suite = unittest.TestSuite()

    suite.addTest(TestSubmitDataset.getTestSuite(select=select))
    suite.addTest(TestSubmitDatasetHandler.getTestSuite(select=select))
    suite.addTest(TestDirectoryListingHandler.getTestSuite(select=select))
    suite.addTest(TestMetadataMerging.getTestSuite(select=select))
    suite.addTest(TestGetDatasetMetadataHandler.getTestSuite(select=select))
    suite.addTest(TestHttpSession.getTestSuite(select=select))
    return suite

from MiscLib import TestUtils
import junitxml

if __name__ == "__main__":
    print "============================================================"
    print "This test suite needs to run under a Linux operating system"
    print "Edit TestConfig.py to specify hostname and other parameters"
    print "Create test accounts on target system to match TestConfig.py"
    print "============================================================"
    TestConfig.setDatasetsBaseDir(".")
    
    
    if len(sys.argv) >= 2 and sys.argv[1] == "xml":
        with open('xmlresults.xml', 'w') as report:
            result = junitxml.JUnitXmlResult(report)
            result.startTestRun()
            getTestSuite().run(result)
            result.stopTestRun()
    else:
        TestUtils.runTests("TestAll", getTestSuite, sys.argv)

# End.
