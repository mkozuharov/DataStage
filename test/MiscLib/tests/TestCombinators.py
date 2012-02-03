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

# $Id: TestCombinators.py 1047 2009-01-15 14:48:58Z graham $
#
# Unit testing for WebBrick library combinators
# See http://pyunit.sourceforge.net/pyunit.html
#

import sys
import unittest

sys.path.append("../..")
from MiscLib.Combinators import *

class TestCombinators(unittest.TestCase):

    def setUp(self):
        return

    def tearDown(self):
        return

    # Test cases

    def testApply(self):
        # Is function application like BCPL?  (fn can be a variable)
        def ap(f,v): return f(v)
        def inc(n): return n+1
        assert ap(inc,2)==3

    def testCurry(self):
        def f(a,b,c): return a+b+c
        g = curry(f,1,2)
        assert g(3) == 6

    def testCompose(self):
        def f(a,b,c): return a+b+c
        def g(a,b):   return a*b
        h = compose(f,g,1000,200)
        assert h(3,4) == 1212, "h(3,4) is "+str(h(3,4))

# Code to run unit tests directly from command line.
def getTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(TestCombinators("testApply"))
    suite.addTest(TestCombinators("testCurry"))
    suite.addTest(TestCombinators("testCompose"))
    return suite

if __name__ == "__main__":
    # unittest.main()
    runner = unittest.TextTestRunner()
    runner.run(getTestSuite())
