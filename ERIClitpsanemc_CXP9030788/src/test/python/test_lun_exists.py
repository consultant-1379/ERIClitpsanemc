'''
Created on 22 May 2015

@author: edavmax
'''
import unittest
from mock import MagicMock
import sys
#sys.path.append(".")
from vnxcommonapi import VnxCommonApi
from sanapiinfo import LunInfo
from sanapiexception import SanApiCriticalErrorException, SanApiCommandException, SanApiConnectionException, SanApiException, SanApiEntityNotFoundException
import logging
import logging.handlers
import testfunclib
import sanapilib


class Test(unittest.TestCase):


    def setUp(self):
        # create a VnxCommonApi object
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
        # setup logging with threshold of WARNING
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)
        
    def tearDown(self):
        pass

    #@testfunclib.skip
    def test_lun_exists_true(self):
        ''' test lun_exists() returns True when the LUN exists '''
        print self.shortDescription() 
        existing_lunname="LITP_TORD2_bootvg_2_LUN_28"
        linfo=LunInfo("22", existing_lunname, "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "TORD2", "174080", "StoragePool", "5")
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun", return_value=linfo)
        ret_bool=vnxCommAPIObj.lun_exists(existing_lunname)
        self.assertTrue(ret_bool)
        vnxCommAPIObj.get_lun.assert_called_once_with(lun_name=existing_lunname, logmsg=False)

    #@testfunclib.skip
    def test_lun_exists_false(self):
        ''' test lun_exists() returns True when the LUN does not exist '''
        print self.shortDescription()
        non_existing_lunname="LITP_TORD2_bootvg_2_LUN_28"
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun", side_effect=
                                SanApiEntityNotFoundException("lun not found", 1))
        ret_bool=vnxCommAPIObj.lun_exists(non_existing_lunname)
        self.assertFalse(ret_bool)
        vnxCommAPIObj.get_lun.assert_called_once_with(lun_name=non_existing_lunname, logmsg=False)

    #@testfunclib.skip
    def test_lun_exists_navierr(self):
        ''' test lun_exists() handles navisec error when checking LUN '''
        print self.shortDescription()
        existing_lunname="LITP_TORD2_bootvg_2_LUN_28"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun", side_effect=
                                SanApiException("Unexpected NAVI error", 1))
        testfunclib.myassert_raises_regexp(self, SanApiException, "Error occured determining existence of LUN", vnxCommAPIObj.lun_exists, existing_lunname)
        vnxCommAPIObj.get_lun.assert_called_once_with(lun_name=existing_lunname, logmsg=False)


        
