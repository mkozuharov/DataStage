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

# $Id: TestNetUtils.py 1047 2009-01-15 14:48:58Z graham $
#
# Unit testing for WebBrick library functions (Functions.py)
# See http://pyunit.sourceforge.net/pyunit.html
#

import sys
import os
import unittest

# Adjust this to match test environment:
#testAllNetMasks = ["10.0.0.0/8", "193.123.195.0/24", "193.123.216.64/26" ]
testAllNetMasks = ["193.123.216.64/26" ]

sys.path.append("../..")
from MiscLib.NetUtils import *

class TestNetUtils(unittest.TestCase):
    def setUp(self):
        return

    def tearDown(self):
        return

    # Actual tests follow

    def testIpAdrStrToInt(self):
        self.assertEqual( ipAdrStrToInt( "1.2.3.4" ), 16909060 )

    def testAddBroadcastBits(self):
        self.assertEqual( addBroadcastBits( 0x01020304, 24 ), 0x010203FF )

    def testGetBroadcastAddressI(self):
        self.assertEqual( getBroadcastAddressI( "1.2.3.4","16"), 0x0102FFFF )

    def testGetBroadcastAddress1(self):
        self.assertEqual( getBroadcastAddress( "1.2.3.4/16"), "1.2.255.255" )

    def testGetBroadcastAddress2(self):
        self.assertEqual( getBroadcastAddress( "1.2.3.4/20"), "1.2.15.255" )

    # Tests for methods representing addresses as integer lists

    def testParseIpAdrs(self):
        self.assertEqual(parseIpAdrs("193.123.216.121"), [193,123,216,121])

    def testParseNetAdrs(self):
        self.assertEqual(parseNetAdrs("193.123.216.64/26"), ([193,123,216,64],26))

    def testMkNetMask1(self):
        n = parseNetAdrs("193.123.216.64/26")
        self.assertEqual(mkNetMask(*n), [255,255,255,192])

    def testMkNetMask2(self):
        n = parseNetAdrs("193.123.216.64/26")
        self.assertEqual(mkNetMask(n), [255,255,255,192])

    def testMkBroadcastAddress1(self):
        n = parseNetAdrs("193.123.216.64/26")
        self.assertEqual(mkBroadcastAddress(*n), [193,123,216,127])

    def testMkBroadcastAddress2(self):
        n = parseNetAdrs("193.123.216.64/26")
        self.assertEqual(mkBroadcastAddress(n), [193,123,216,127])
        
    def testFormatIpAdrs(self):
        self.assertEqual(formatIpAdrs([193,123,216,64]), "193.123.216.64")
        
    def testIpInNetwork1(self):
        n = parseNetAdrs("193.123.216.64/26")
        i = parseIpAdrs("193.123.216.121")
        b = mkBroadcastAddress(*n)
        x = parseIpAdrs("193.123.216.200")
        assert ipInNetwork(i,*n)
        assert ipInNetwork(b,*n)
        assert not ipInNetwork(x,*n)
        
    def testIpInNetwork2(self):
        n = parseNetAdrs("193.123.216.64/26")
        i = parseIpAdrs("193.123.216.121")
        b = mkBroadcastAddress(n)
        x = parseIpAdrs("193.123.216.200")
        assert ipInNetwork(i,n)
        assert ipInNetwork(b,n)
        assert not ipInNetwork(x,n)

    def testParseMacAdrs(self):
        self.assertEqual(parseMacAdrs("01:34:67:9a:BC:eF"), [1,52,103,154,188,239])
        
    def testFormatMacAdrs(self):
        self.assertEqual(formatMacAdrs([1,52,103,154,188,239],sep='-'), "01-34-67-9A-BC-EF")
        
    def testGetHostIpsAndMask(self):
        # getHostIpsAndMask doesn't work for networks witjh non-standard netmasks
        results = getHostIpsAndMask()
        for v in testAllNetMasks:
            self.assert_( v in results, "Not found: %s in %s"%(v,results) )

# Code to run unit tests directly from command line.
# Constructing the suite manually allows control over the order of tests.
def getTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(TestNetUtils("testIpAdrStrToInt"))
    suite.addTest(TestNetUtils("testAddBroadcastBits"))
    suite.addTest(TestNetUtils("testGetBroadcastAddressI"))
    suite.addTest(TestNetUtils("testGetBroadcastAddress1"))
    suite.addTest(TestNetUtils("testGetBroadcastAddress2"))
    suite.addTest(TestNetUtils("testParseIpAdrs"))
    suite.addTest(TestNetUtils("testParseNetAdrs"))
    suite.addTest(TestNetUtils("testMkNetMask1"))
    suite.addTest(TestNetUtils("testMkNetMask2"))
    suite.addTest(TestNetUtils("testMkBroadcastAddress1"))
    suite.addTest(TestNetUtils("testMkBroadcastAddress2"))
    suite.addTest(TestNetUtils("testFormatIpAdrs"))
    suite.addTest(TestNetUtils("testIpInNetwork1"))
    suite.addTest(TestNetUtils("testIpInNetwork2"))
    suite.addTest(TestNetUtils("testParseMacAdrs"))
    suite.addTest(TestNetUtils("testFormatMacAdrs"))
    # suite.addTest(TestNetUtils("testGetHostIpsAndMask"))
    return suite

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # unittest.main()
    runner = unittest.TextTestRunner()
    runner.run(getTestSuite())
    