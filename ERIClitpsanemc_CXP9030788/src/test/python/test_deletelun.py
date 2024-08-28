'''
Created on 17 Sept 2014

@author: edavmax
'''

import unittest
from mock import patch, Mock, MagicMock
import sys
from vnxcommonapi import VnxCommonApi
from sanapiinfo import LunInfo
from sanapiexception import (SanApiCriticalErrorException,
    SanApiOperationFailedException, SanApiCommandException,
    SanApiConnectionException, SanApiException)
import logging
import logging.handlers
import testfunclib
import sanapilib
from emctest import TestSanEMC


class Test(TestSanEMC):

    def setUp(self):
        self.ref_navicmd="/opt/Navisphere/bin/naviseccli"
        self.spa="1.2.3.4"
        self.spb="1.2.3.5"
        self.adminuser="admin"
        self.adminpasswd="shroot12"
        self.createluncmdok="../data/createluninsp.xml.cmdok"
        self.getluncmdok="../data/getlun.xml.cmdok"
        self.listluncmdok="../data/lunlist.xml.cmdok"
        self.scope = "global"
        self.timeout="60" 
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)

    def setUpCommon(self):
        print self.shortDescription()
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        self.vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)

    def test_delete_splun_pos(self):
        """
        test delete storage pool LUN with specified LUN id
        """

        self.setUpCommon()
        lunid_to_delete="45"
        linfo=LunInfo(lunid_to_delete, "LITP_TORD2_bootvg_2_LUN_28", "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "StoragePool", "5")
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=linfo)
        ret_bool=self.vnx.delete_lun(lun_id=lunid_to_delete)
        self.assertTrue(ret_bool)
        self.vnx.get_lun.assert_called_once_with(lun_id=lunid_to_delete)
        self.assertEquals(self.vnx._navisec.call_count, 1)
        self.vnx._navisec.assert_called_once_with("lun -destroy -l " + lunid_to_delete + " -o")

    def test_delete_splun_xtraargs_pos(self):
        """
        test delete storage pool LUN with specified lun id using array specific options
        """

        self.setUpCommon()
        lunid_to_delete="45"
        linfo=LunInfo(lunid_to_delete, "LITP_TORD2_bootvg_2_LUN_28", "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "StoragePool", "5")
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=linfo)
        ret_bool=self.vnx.delete_lun(lun_id=lunid_to_delete, array_specific_options="-destroySnapshots -forceDetach")
        self.assertTrue(ret_bool)
        self.vnx.get_lun.assert_called_once_with(lun_id=lunid_to_delete)
        self.assertEquals(self.vnx._navisec.call_count, 1)
        self.vnx._navisec.assert_called_once_with("lun -destroy -l " + lunid_to_delete + " -destroySnapshots -forceDetach -o")

    def test_delete_rglun_pos(self):
        """
        test delete raid group LUN with specified LUN id
        """

        self.setUpCommon()
        lunid_to_delete="22"
        linfo=LunInfo(lunid_to_delete, "oss_fen1", "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "12", "1000", "RaidGroup", "5")
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=linfo)
        ret_bool=self.vnx.delete_lun(lun_id=lunid_to_delete)
        self.assertTrue(ret_bool)
        self.vnx.get_lun.assert_called_once_with(lun_id=lunid_to_delete)
        self.assertEquals(self.vnx._navisec.call_count, 1)
        self.vnx._navisec.assert_called_once_with("unbind " + lunid_to_delete + " -o")

    def test_delete_splun_with_badlunid(self):
        """
        test delete_lun with bad lun_id
        """

        self.setUpCommon()
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid LUN id:" , self.vnx.delete_lun, lun_id="foobar")

    def test_delete_splun_with_noparams(self):
        """
        test delete_lun with no params raises exception
        """

        self.setUpCommon()
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Neither lun name nor lun id were specified" , self.vnx.delete_lun)

    def test_delete_splun_with_bothparams(self):
        """
        test delete_lun with both lun_name and lun_id params raises exception
        """

        self.setUpCommon()
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Both lun name and lun id were specified" , self.vnx.delete_lun, lun_id="1", lun_name="zombie_apocolypse")

    def test_delete_splun_with_non_existinglunid(self):
        """
        test delete_lun with non-existing lunid
        """

        self.setUpCommon()
        self.vnx.get_lun = MagicMock(name="get_lun", side_effect=SanApiCommandException("Navisec cmd failed with error code 1", 1))
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Unable to get information on LUN",self.vnx.delete_lun, lun_id="1")
        
    def test_delete_splun_by_id_with_badcontainertype(self):
        """
        test delete_lun with LUN with bad container type
        """

        self.setUpCommon()
        bad_linfo=LunInfo("1", "LITP_TORD2_bootvg_2_LUN_28", "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "StoragePool", "6")
        bad_linfo._type="PackOFags"
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=bad_linfo)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Unrecognised LUN container", self.vnx.delete_lun, lun_id="1")

if __name__ == "__main__":
    unittest.main()
