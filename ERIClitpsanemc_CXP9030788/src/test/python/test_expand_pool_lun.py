'''
Created on 08 June 2015

@author: emicfah
'''
import unittest
from mock import MagicMock
from vnxcommonapi import VnxCommonApi
from sanapiexception import (SanApiCommandException,
                             SanApiOperationFailedException)
import logging
import testfunclib


class Test(unittest.TestCase):

    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.createluncmdok = "../data/createluninsp.xml.cmdok"
        self.getluncmdok = "../data/getlun.xml.cmdok"
        self.listluncmdok = "../data/lunlist.xml.cmdok"
        self.scope = "global"
        self.timeout = "60"
        # setup logging with threshold of WARNING
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)

    def tearDown(self):
        pass

    # @testfunclib.skip
    def test_expand_pool_lun_positive(self):
        ''' test test_expand_pool_lun_positive()
            returns the LUN  if expansion succeeds
        '''
        print self.shortDescription()
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(
            name="_accept_and_store_cert")
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)
        vnxCommAPIObj.expand_pool_lun(lun_name="lun123", size="5gb")
        self.assertEquals(vnxCommAPIObj._navisec.call_count, 1)
        command = "lun -expand -name lun123 -capacity 5 -sq gb  -o"
        vnxCommAPIObj._navisec.assert_called_once_with(command)
        vnxCommAPIObj.get_lun.assert_called_with(
            lun_name="lun123", logmsg=True)

    # @testfunclib.skip
    def test_expand_pool_lun_bad_luname(self):
        ''' test test_expand_pool_lun_bad_luname
            throws SanApiOperationFailedException
        '''
        print self.shortDescription()
        vnxCommAPIObj = VnxCommonApi(self.logger)
        testfunclib.myassert_raises_regexp(self,
                                           SanApiOperationFailedException,
                                           "Not a string <type 'int'>",
                                           vnxCommAPIObj.expand_pool_lun,
                                           lun_name=1234, size="500gb")

    # @testfunclib.skip
    def test_expand_pool_lun_bad_size_quantifier(self):
        ''' test test_expand_pool_lun_bad_size_quantifier()
            throws SanApiOperationFailedException
        '''
        print self.shortDescription()
        vnxCommAPIObj = VnxCommonApi(self.logger)
        testfunclib.myassert_raises_regexp(self,
                                           SanApiOperationFailedException,
                                           "Invalid size 5tbb",
                                           vnxCommAPIObj.expand_pool_lun,
                                           lun_name="1234", size="5tbb")

    # @testfunclib.skip
    def test_expand_pool_lun_bad_size(self):
        ''' test test_expand_pool_lun_bad_size()
            throws SanApiOperationFailedException
        '''
        print self.shortDescription()
        vnxCommAPIObj = VnxCommonApi(self.logger)
        testfunclib.myassert_raises_regexp(self,
                                           SanApiOperationFailedException,
                                           "Invalid size -5",
                                           vnxCommAPIObj.expand_pool_lun,
                                           lun_name="lun123", size="-5")

    # @testfunclib.skip
    def test_expand_pool_lun_bad_int_size(self):
        ''' test test_expand_pool_lun_bad_int_size()
            throws SanApiOperationFailedException
        '''
        print self.shortDescription()
        vnxCommAPIObj = VnxCommonApi(self.logger)
        error = "Numeric component of size must be integer"
        testfunclib.myassert_raises_regexp(self,
                                           SanApiOperationFailedException,
                                           error,
                                           vnxCommAPIObj.expand_pool_lun,
                                           lun_name="lun123", size="500.500gb")

    # @testfunclib.skip
    def test_expand_pool_lun_negative(self):
        ''' test test_expand_pool_lun_negative()
            throws SanApiOperationFailedException
        '''
        print self.shortDescription()
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.expand_pool_lun = MagicMock(
            name="expand_pool_lun",
            side_effect=SanApiCommandException("Unable to expand LUN", 1))
        testfunclib.myassert_raises_regexp(self,
                                           Exception,
                                           "Unable to expand LUN",
                                           vnxCommAPIObj.expand_pool_lun,
                                           lun_name="lun123", size="500gb")

    def test_is_nearly(self):
        vnxCommAPIObj = VnxCommonApi(self.logger)
        self.assertTrue(vnxCommAPIObj.is_nearly(101,100))
        self.assertTrue(vnxCommAPIObj.is_nearly(100,101))
        self.assertFalse(vnxCommAPIObj.is_nearly(150,101))
