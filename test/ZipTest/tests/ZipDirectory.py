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

import sys, unittest, logging, zipfile, re
from os.path import normpath

# Add main library directory to python path
sys.path.append("../..")
from MiscLib.ScanFiles import *

class ZipDirectory(unittest.TestCase):

    def setUp(self):
        self.testpath = "."
        self.testpatt = re.compile("^.*$(?<!\.zip)")
        return

    def tearDown(self):
        return

    def doZip(self):
        files = CollectFiles(self.testpath,self.testpatt)
        z = zipfile.ZipFile('test.zip','w')
        for i in files: 
            n = joinDirName(i[0], i[1])
            z.write(n)
        z.close()
        z = zipfile.ZipFile('test.zip')
        z.testzip()
        z.printdir()
        z.close()

def getTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(ZipDirectory("doZip"))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(getTestSuite())
