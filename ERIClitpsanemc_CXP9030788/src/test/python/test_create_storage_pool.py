'''
Created on 07 Oct 2014

@author: eadapar
'''

from testfunclib import MagicMock, myassert_raises_regexp, unittest, prepare_mocked_popen, skip
from vnxcommonapi import VnxCommonApi
from sanapiinfo import StoragePoolInfo
from sanapilib import SanApiCriticalErrorException, SanApiEntityAlreadyExistsException
import logging.handlers


class Test(unittest.TestCase):
    """
    Test class for Storage Pool
    """

    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.createluncmdok = "./data/createluninsp.xml.cmdok"
        self.getluncmdok = "./data/getlun.xml.cmdok"
        self.listluncmdok = "./data/lunlist.xml.cmdok"
        self.scope = "global"
        self.timeout = "60"

        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        pass

    def test_create_storage_pool_positive(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        ret_spio = StoragePoolInfo("Storage Pool 1", "99", "5", "13", "12")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_storage_pool = MagicMock(sp_name="get_storage_pool", return_value=ret_spio)
        vnxCommAPIObj.create_storage_pool("Storage Pool 1", "0_1_2 0_2_3", "10")
        vnxCommAPIObj._navisec.assert_called_once_with("storagepool -create -disks 0_1_2 0_2_3 -rtype r_10 -name 'Storage Pool 1' -o")

    def test_create_storage_pool_whitespaces_in_disks_1(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        ret_spio = StoragePoolInfo("Storage Pool 1", "99", "5", "13", "12")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_storage_pool = MagicMock(sp_name="get_storage_pool_by_name", return_value=ret_spio)
        vnxCommAPIObj.create_storage_pool("Storage Pool 1", "     0_1_14      0_2_17   ", "5")
        vnxCommAPIObj._navisec.assert_called_once_with("storagepool -create -disks 0_1_14 0_2_17 -rtype r_5 -name 'Storage Pool 1' -o")

    def test_create_storage_pool_whitespaces_in_disks_2(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        ret_spio = StoragePoolInfo("Storage Pool 1", "99", "5", "13", "12")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_storage_pool = MagicMock(sp_name="get_storage_pool_by_name", return_value=ret_spio)
        vnxCommAPIObj.create_storage_pool("Storage Pool 1", "     0_1_14         1_2_6   0_2_17   ", "5")
        vnxCommAPIObj._navisec.assert_called_once_with("storagepool -create -disks 0_1_14 1_2_6 0_2_17 -rtype r_5 -name 'Storage Pool 1' -o")
        vnxCommAPIObj.get_storage_pool = MagicMock(sp_name="get_storage_pool", return_value=ret_spio)

    def test_create_storage_pool_invalid_B_E_D(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun")

        # 1. Invalid Bus in B_E_D
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid Disk Information presented, disks should be in B_E_D format and be a valid disk", vnxCommAPIObj.create_storage_pool, "Storage Pool 1", "0_1_2 100_2_255", "5" )
        # 2. Invalid Enclosure in B_E_D
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid Disk Information presented, disks should be in B_E_D format and be a valid disk", vnxCommAPIObj.create_storage_pool, "Storage Pool 1", "0_1_2 2_2_100_1", "5" )
        # 2. Invalid Enclosure in B_E_D
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid Disk Information presented, disks should be in B_E_D format and be a valid disk", vnxCommAPIObj.create_storage_pool, "Storage Pool 1", "0_1_2 2_2_100", "5" )

    def test_create_storage_pool_decimal_in_B_E_D(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun")
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid Disk Information presented, disks should be in B_E_D format and be a valid disk", vnxCommAPIObj.create_storage_pool, "Storage Pool 1", "1.2_1.2_1.2 1.2_1.2_1.2", "5" )

    def test_create_storage_pool_invalid_raid_type(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun")
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid RAID Type provided", vnxCommAPIObj.create_storage_pool, "Storage Pool 1", "0_1_2 0_1_3", "5A" )

    def test_create_storage_pool_no_sp_name(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun")
        myassert_raises_regexp(self, SanApiCriticalErrorException, "No storage pool name provided, this is a mandatory argument", vnxCommAPIObj.create_storage_pool, None, disks="0_1_2 0_1_3", raid_type="5A" )

    def test_create_storage_pool_no_disks(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun")
        myassert_raises_regexp(self, SanApiCriticalErrorException, "No disks provided, this is a mandatory argument", vnxCommAPIObj.create_storage_pool, sp_name="SPool", disks=None, raid_type="5A" )

    def test_create_storage_pool_no_raid_type(self):
        vnxCommAPIObj = VnxCommonApi(None)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_lun = MagicMock(name="get_lun")
        myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid RAID Type provided: None", vnxCommAPIObj.create_storage_pool, sp_name="SPool", disks="0_1_2 0_1_3", raid_type=None )

    def test_create_storage_pool_already_exists(self):
        ''' test that create storage pool raises exception if pool already exists '''
        print self.shortDescription()

    def test_create_sp_lun_fail_lun_already_exists(self):
        '''Test that create storage pool fails with SanApiEntityNotFoundException exception if pool already exists '''
        print self.shortDescription()
        mock_popen = prepare_mocked_popen("../data/storagepool_already_exists.xml", None, 0)

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        #vnxCommAPIObj.create_storage_pool( "Storage Pool 1", "0_1_2 0_2_3", "5")
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, "Pool name is already used", vnxCommAPIObj.create_storage_pool, "Storage Pool 1", "0_1_2 0_2_3", "5") 


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
