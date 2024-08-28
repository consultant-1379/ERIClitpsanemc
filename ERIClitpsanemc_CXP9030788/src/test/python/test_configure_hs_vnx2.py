'''
Created on 26 August 2014

@author: EMICFAH
'''
import logging
import unittest

from mock import patch, Mock, MagicMock
from sanapiexception import *
from sanapiinfo import HsPolicyInfo
from vnx2api import Vnx2Api
from testfunclib import *
import xml.etree.ElementTree as ET
import vnxparser 


class Test(unittest.TestCase):

    def setUp(self):
        '''Create a VnxCommonApi object'''
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "password"
        self.scope = "global"
        self.timeout = "50"
        self.setcmdokxml1 = "../data/set_hs_policy_goodnavi.xml"
        self.getcmdokxml1 = "../data/hs_policy_list.xml"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)

    #@skip
    def test_configure_hs_vnx2(self):
        ''' check configure_hs with valid policy id and ratio'''
        print self.shortDescription()
        vnx2ApiObj = Vnx2Api(self.logger)
        vnx2ApiObj._navisec = MagicMock(name="_navisec")
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck=False)
        hsinfo = HsPolicyInfo("1", "SAS", "1/25", "3")
        vnx2ApiObj.get_hs_policy = MagicMock(name="get_hs_policy", return_value=hsinfo)
        myhsinfo = vnx2ApiObj.configure_hs(policy=1, ratio=25)
        myassert_is_instance(self, myhsinfo, HsPolicyInfo)
        self.assertEquals(vnx2ApiObj._navisec.call_count, 1)
        vnx2ApiObj._navisec.assert_called_with("hotsparepolicy -set -o 1 -keep1unusedper 25")
        vnx2ApiObj.get_hs_policy.assert_called_with(1)


    #@skip
    def test_configure_hs_invalid_policy_id(self):
        ''' check configure_hs handles an invalid policy id and valid ratio'''
        print self.shortDescription()
        vnx2ApiObj = Vnx2Api(self.logger)
        vnx2ApiObj._navisec = MagicMock(name="_navisec")
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False,vcheck=False)
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid policy ID", vnx2ApiObj.configure_hs, \
                                policy="-5",ratio="25")

    #@skip
    def test_configure_hs_invalid_ratio(self):
        ''' check configure_hs handles a valid policy id and invalid ratio '''
        print self.shortDescription()
        vnx2ApiObj = Vnx2Api(self.logger)
        vnx2ApiObj._navisec = MagicMock(name="_navisec")
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False,vcheck=False)
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid ratio", vnx2ApiObj.configure_hs, \
                                policy=1, ratio="-1")

    #@skip
    def test_configure_hs_where_the_policy_is_set_to_none(self):
        ''' check configure_hs handles a policy id set to none and a valid ratio '''
        print self.shortDescription()
        vnx2ApiObj = Vnx2Api(self.logger)
        vnx2ApiObj._navisec = MagicMock(name="_navisec")
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck = False)
        #myassert_raises_regexp(self, SanApiCriticalErrorException, "No policy id has been specified", vnx2ApiObj.configure_hs, policy=None, ratio=30 )
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid policy ID", vnx2ApiObj.configure_hs, policy=None, ratio=30 )


    #@skip
    def test_configure_hs_where_the_ratio_is_set_to_none(self):
        ''' check configure_hs handles a valid policy id and ratio set to none '''
        print self.shortDescription()
        vnx2ApiObj = Vnx2Api(self.logger)
        vnx2ApiObj._navisec = MagicMock(name="_navisec")
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False,vcheck=False)
        #myassert_raises_regexp(self, SanApiCriticalErrorException, "No ratio has been specified", vnx2ApiObj.configure_hs, policy=1, ratio=None )
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid ratio", vnx2ApiObj.configure_hs, policy=1, ratio=None )

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
