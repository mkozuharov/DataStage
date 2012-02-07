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

import TestTestUtils
import TestFunctions
import TestCombinators
import TestDomHelpers
import TestScanFiles
import TestNetUtils
import TestSuperGlobal

# Code to run unit tests from all library test modules
def getTestSuite(select="unit"):
    suite = unittest.TestSuite()
    suite.addTest(TestTestUtils.getTestSuite(select=select))
    suite.addTest(TestFunctions.getTestSuite())
    suite.addTest(TestCombinators.getTestSuite())
    suite.addTest(TestDomHelpers.getTestSuite())
    suite.addTest(TestScanFiles.getTestSuite())
    suite.addTest(TestNetUtils.getTestSuite())
    suite.addTest(TestSuperGlobal.getTestSuite())
    return suite

from MiscLib import TestUtils

if __name__ == "__main__":
    TestUtils.runTests("TestAll", getTestSuite, sys.argv)

# End.
