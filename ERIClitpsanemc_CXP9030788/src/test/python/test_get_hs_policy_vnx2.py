'''
Created on 26 August 2014

@author: EMICFAH
'''
import logging
import unittest

from mock import patch, Mock, MagicMock
from sanapiexception import *
from sanapiinfo import HsPolicyInfo
import testfunclib
from vnx2api import Vnx2Api
from testfunclib import *
import xml.etree.ElementTree as ET
from vnx2api import *
from vnxparser import VnxParser


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

    # @testfunclib.skip
    def test_get_hs_policy_by_disk_type(self):
        ''' check get_hs_policy can retrieve a hot spare policy
            by supplying the disk type only
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger) 
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck=False)
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree)
        hs_policy_info_ob = vnx2ApiObj.get_hs_policy(disk_type="SAS Flash")
        testfunclib.myassert_is_instance(self, hs_policy_info_ob, HsPolicyInfo)
        self.assertEquals(hs_policy_info_ob.policy_id, '2')
        self.assertEquals(hs_policy_info_ob.disk_type, 'SAS Flash')
        self.assertEquals(hs_policy_info_ob.ratio_of_keep_unused, '0')
        self.assertEquals(hs_policy_info_ob.number_to_keep_unused, '0')

    # @testfunclib.skip
    def test_get_hs_policy_by_policy_id(self):
        ''' check get_hs_policy can retrieve a hot spare policy
            by specifying the policy ID only
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger) 
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck=False)
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree)
        hs_policy_info_ob = vnx2ApiObj.get_hs_policy(policy="1")
        testfunclib.myassert_is_instance(self, hs_policy_info_ob, HsPolicyInfo)
        self.assertEquals(hs_policy_info_ob.policy_id, '1')
        self.assertEquals(hs_policy_info_ob.disk_type, 'SAS')
        self.assertEquals(hs_policy_info_ob.ratio_of_keep_unused, '1/25')
        self.assertEquals(hs_policy_info_ob.number_to_keep_unused, '3')

    # @testfunclib.skip
    def test_get_hs_policy_when_passed_both_policyid_and_disktype(self):
        ''' check get_hs_policy throws an exception when passed both a valid policy id 
            and a valid disk type
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger) 
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck=False)
        myassert_raises_regexp(self, SanApiCriticalErrorException, "You can only supply one parameter either policy id", vnx2ApiObj.get_hs_policy, \
                               policy='1', disk_type='SAS Flash')

    # @testfunclib.skip
    def test_get_hs_policy_without_parameters(self):
        ''' check get_hs_policy throws an exception when passed no parameters
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger) 
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck=False)
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Please supply either a policy id or disk_type!", vnx2ApiObj.get_hs_policy, )



    # @testfunclib.skip
    def test_get_hs_valid_policy_id_but_doesnt_exist(self):
        ''' check get_hs_policy can handle a valid but not existing policy ID
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger) 
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck=False)
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Unknown Policy ID", vnx2ApiObj.get_hs_policy, \
                                policy="79")

    # @testfunclib.skip
    def test_get_hs_with_invalid_policy(self):
        ''' check get_hs_policy can handle an invalid policy ID
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger)
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree) 
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck = False)
        self.logger = None
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid policy ID", vnx2ApiObj.get_hs_policy, \

                                policy="-3")

    # @testfunclib.skip
    def test_get_hs_with_invalid_disk_type(self):
        ''' check get_hs_policy can handle an invalid disk_type
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger)
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree) 
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck = False)
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Unknown disk type", vnx2ApiObj.get_hs_policy, \
                                disk_type="AdamsMcgibbers")

    # @testfunclib.skip
    def test_get_hs_policy_list(self):
        ''' check get_hs_policy_list can retrieve a list of hot spare policies
        '''
        print self.shortDescription()
        tree = ET.parse(self.getcmdokxml1)
        etree = tree.getroot()
        vnx2ApiObj = Vnx2Api(self.logger) 
        vnx2ApiObj.initialise((self.spa, self.spb),
                              self.adminuser, self.adminpasswd,
                              self.scope, False, vcheck=False)
        vnx2ApiObj._navisec = MagicMock(name="_navisec", return_value=etree)
        hs_policy_info_ob_list = vnx2ApiObj.get_hs_policy_list()
        for hs_policy_info_ob in hs_policy_info_ob_list:
            testfunclib.myassert_is_instance(self, hs_policy_info_ob, HsPolicyInfo)
        # Assert the correct values for each object in the list
        self.assertEquals(hs_policy_info_ob_list[0].policy_id, '1')
        self.assertEquals(hs_policy_info_ob_list[0].disk_type, 'SAS')
        self.assertEquals(hs_policy_info_ob_list[0].ratio_of_keep_unused, '1/25')
        self.assertEquals(hs_policy_info_ob_list[0].number_to_keep_unused, '3')

        self.assertEquals(hs_policy_info_ob_list[1].policy_id, '2')
        self.assertEquals(hs_policy_info_ob_list[1].disk_type, 'SAS Flash')
        self.assertEquals(hs_policy_info_ob_list[1].ratio_of_keep_unused, '0')
        self.assertEquals(hs_policy_info_ob_list[1].number_to_keep_unused, '0')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
