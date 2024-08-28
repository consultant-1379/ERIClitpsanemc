'''
Created on 16 Jul 1934

@author: esteved
'''
import unittest
from vnxcommonapi import VnxCommonApi
from vnx1api import Vnx1Api
from sanapiexception import SanApiCommandException, SanApiOperationFailedException
import logging
from testfunclib import *
from sanapiinfo import LunInfo
import mock


class Test(unittest.TestCase):

    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"
        self.timeout = "50"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.INFO)
      
        self.vnxCommApiObj = Vnx1Api(self.logger)
        self.vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                      self.adminpasswd, self.scope)

    #@skip
    def test_get_hs_luns_ok(self):
        ''' get hs luns ok '''
        print self.shortDescription()
        self.setUp()
        lunlist = [ LunInfo('40', 'ste1', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:11',
                        '2', '549407', 'RaidGroup', 'HS'),
                    LunInfo('41', 'ste2', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:12',
                        '3', '549407', 'RaidGroup', '5') ] 

        expectedLuns = [ LunInfo('40', 'ste1', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:11',
                        '2', '549407', 'RaidGroup', 'HS')]

        self.vnxCommApiObj.get_luns = MagicMock(name = 'get_luns', return_value=lunlist)

        retLuns = self.vnxCommApiObj.get_hs_luns()
        self.assertEqual(retLuns[0], expectedLuns[0], "LUNs do not match")
        self.assertEqual(len(retLuns), 1, "Expected 1 LUN, got %s " % len(retLuns))

        self.vnxCommApiObj = None

    def test_get_hs_luns_no_hs(self):
        ''' get hs luns no hs - no HS luns'''
        print self.shortDescription()
        self.setUp()
        lunlist = [ LunInfo('40', 'ste1', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:11',
                        '2', '549407', 'RaidGroup', '5'),
                    LunInfo('41', 'ste2', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:12',
                        '3', '549407', 'RaidGroup', '5') ]

        expectedLuns = []

        self.vnxCommApiObj.get_luns = MagicMock(name = 'get_luns', return_value=lunlist)

        retLuns = self.vnxCommApiObj.get_hs_luns()
        self.assertEqual(retLuns, [], "Expected no LUNs - list should be empty")
        self.assertEqual(len(retLuns), 0, "Expected no LUN, got %s " % len(retLuns))

        self.vnxCommApiObj = None


    def test_get_hs_luns_no_luns(self):
        ''' get hs luns no luns '''
        print self.shortDescription()
        self.setUp()
        lunlist = []
        expectedLuns = []

        self.vnxCommApiObj.get_luns = MagicMock(name = 'get_luns', return_value=lunlist)

        retLuns = self.vnxCommApiObj.get_hs_luns()
        self.assertEqual(retLuns, [], "Expected no LUNs - list should be empty")
        self.assertEqual(len(retLuns), 0, "Expected no LUN, got %s " % len(retLuns))

        self.vnxCommApiObj = None




if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
