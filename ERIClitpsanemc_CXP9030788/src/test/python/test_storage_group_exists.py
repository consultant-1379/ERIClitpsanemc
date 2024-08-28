'''
Created on 22 May 2015

@author: edavmax
'''
import unittest
from mock import MagicMock
import sys
#sys.path.append(".")
from vnxcommonapi import VnxCommonApi
from sanapiinfo import LunInfo, StorageGroupInfo
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
    def test_storage_group_exists_true(self):
        ''' test storage_group_exists() returns True when the SG exists '''
        print self.shortDescription() 
        existing_sg="mysg"
        sginfo = StorageGroupInfo(existing_sg, "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", 
                                              True, None, None)

        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj.get_storage_group = MagicMock(name="get_storage_group", return_value=sginfo)
        ret_bool=vnxCommAPIObj.storage_group_exists(existing_sg)
        self.assertTrue(ret_bool)
        vnxCommAPIObj.get_storage_group.assert_called_once_with(existing_sg, logmsg=False)

    #@testfunclib.skip
    def test_storage_group_exists_false(self):
        ''' test storage_group_exists() returns True when the SG does not exist '''
        print self.shortDescription()
        non_existing_sg="mysg"
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj.get_storage_group = MagicMock(name="get_storage_group", side_effect=
                                SanApiEntityNotFoundException("SG not found", 1))
        ret_bool=vnxCommAPIObj.storage_group_exists(non_existing_sg)
        self.assertFalse(ret_bool)
        vnxCommAPIObj.get_storage_group.assert_called_once_with(non_existing_sg, logmsg=False)

    #@testfunclib.skip
    def test_storage_group_exists_navierr(self):
        ''' test storage_group_exists() handles navisec error when checking SG '''
        print self.shortDescription()
        existing_sg="mysg"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.get_storage_group = MagicMock(name="get_storage_group", side_effect=
                                SanApiException("EEEEEEEEEK!!!!", 1))
        testfunclib.myassert_raises_regexp(self, SanApiException, "Error occured determining existence of Storage Group", vnxCommAPIObj.storage_group_exists, existing_sg)
        vnxCommAPIObj.get_storage_group.assert_called_once_with(existing_sg, logmsg=False)


        
