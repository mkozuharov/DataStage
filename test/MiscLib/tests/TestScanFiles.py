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

# $Id: TestScanFiles.py 1058 2009-01-26 10:39:19Z graham $
#
# Unit testing for WebBrick library functions (Functions.py)
# See http://pyunit.sourceforge.net/pyunit.html
#

import sys
import unittest
import re
from os.path import normpath

sys.path.append("../..")
from MiscLib.ScanFiles import *
from MiscLib.Functions import compareLists

class TestScanFiles(unittest.TestCase):
    def setUp(self):
        self.testpath = "resources/"
        self.testpatt = re.compile( r'^TestScanFiles.*\.txt$' )
        return

    def tearDown(self):
        return

    # Actual tests follow

    def testCollectShallow(self):
        files    = CollectFiles(self.testpath,self.testpatt,recursive=False)
        expected = [ (self.testpath,"TestScanFiles1.txt")
                   , (self.testpath,"TestScanFiles2.txt")
                   ]
        assert files == expected, "Wrong file list: "+repr(files)

    def testCollectRecursive(self):
        files    = CollectFiles(self.testpath,self.testpatt)
        expected = [ (self.testpath,"TestScanFiles1.txt")
                   , (self.testpath,"TestScanFiles2.txt")
                   , (self.testpath+"TestScanFilesSubDir","TestScanFiles31.txt")
                   , (self.testpath+"TestScanFilesSubDir","TestScanFiles32.txt")
                   ]
        c = compareLists(files, expected)
        assert c == None, "Wrong file list: "+repr(c)

    def testJoinDirName(self):
        # normpath used here to take care of dir separator issues.
        n = joinDirName("/root/sub","name")
        assert n==normpath("/root/sub/name"), "JoinDirName failed: "+n
        n = joinDirName("/root/sub/","name")
        assert n==normpath("/root/sub/name"), "JoinDirName failed: "+n
        n = joinDirName("/root/sub/","/name")
        assert n==normpath("/name"), "JoinDirName failed: "+n

    def testReadDirNameFile(self):
        assert readDirNameFile(self.testpath,"TestScanFiles1.txt"), "Read dir,file 'TestScanFiles1.txt' failed"

    def testReadFile(self):
        assert readFile(self.testpath+"TestScanFiles1.txt"), "Read file 'TestScanFiles1.txt' failed"


# Code to run unit tests directly from command line.
# Constructing the suite manually allows control over the order of tests.
def getTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(TestScanFiles("testCollectShallow"))
    suite.addTest(TestScanFiles("testCollectRecursive"))
    suite.addTest(TestScanFiles("testJoinDirName"))
    suite.addTest(TestScanFiles("testReadDirNameFile"))
    suite.addTest(TestScanFiles("testReadFile"))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(getTestSuite())
    