'''
Created on 26 Jun 2014

@author: edavmax
'''
import unittest
import sys
from sanapiinfo import HluAluPairInfo, HbaInitiatorInfo, StorageGroupInfo, HsPolicyInfo
import logging
from vnxparser import VnxParser
from sanapiinfo import LunInfo, SanApiInfo
from sanapiexception import SanApiOperationFailedException
from testfunclib import *
import re
from emctest import TestSanEMC



class TestSanApiInfo(TestSanEMC):
    '''
    test
    '''

    def setUp(self):
        self.navi_badop1={"Name":"myLun", "UID":"sdsd3435353" } # missing ID
        logger = logging.getLogger("sanapitest")
        logger.setLevel(logging.WARN)
        self.logger = logger
        

    def tearDown(self):
        pass

    def test_createluninfo(self):
        '''test to check creation of LunInfo object'''
        print self.shortDescription()
        lun_uid="60:06:01:60:6F:D0:2E:00:BD:E0:3B:E4:72:A6:E1:11"
        luninfoobj=LunInfo("123", "lun123", lun_uid, "sp123", "500", "StoragePool", "n/a")
        myassert_is_instance(self, luninfoobj, LunInfo)
        self.assertEqual(luninfoobj.name, "lun123")
        self.assertEqual(luninfoobj.id, "123")
        self.assertEqual(luninfoobj.uid, lun_uid)
        self.assertEqual(luninfoobj.type, "StoragePool")
        self.assertEqual(luninfoobj.container, "sp123")
        self.assertEqual(luninfoobj.raid, "n/a")
        self.assertEqual(luninfoobj.size, "500")

    def test_createluninfo_handles_bad_params(self):
        '''test to check creation of LunInfo object'''
        print self.shortDescription()
        lun_uid="60:06:01:60:6F:D0:2E:00:BD:E0:3B:E4:72:A6:E1:11"
        spname="sp123"
        bad_lunid="foo"
        myassert_raises_regexp(self, SanApiOperationFailedException, "LunInfo attribute, lun_id is not valid", LunInfo, \
                                bad_lunid, "lun123", lun_uid, spname, "500", "StoragePool", "n/a" )
        bad_lunname=""
        myassert_raises_regexp(self, SanApiOperationFailedException, "LunInfo attribute, name is not valid", LunInfo, \
                                "123", bad_lunname, lun_uid, spname, "500", "StoragePool", "n/a" )
        bad_size="200Gigawatts"

        self.assertRaises(SanApiOperationFailedException, LunInfo, "123", "lun123", lun_uid, spname, bad_size, "StoragePool", "n/a" )
        bad_cont_type="rustybucket"
        myassert_raises_regexp(self, SanApiOperationFailedException, "LunInfo attribute, container_type is not valid", LunInfo, \
                                "123", "lun123", lun_uid, spname, "500", bad_cont_type, "n/a" )

    def test_sanapiinfo_is_equal_to_itself(self):
        '''test sanapiinfo is equal to itself '''
        print self.shortDescription()
        san_api_info = SanApiInfo()
        self.assertTrue(san_api_info == san_api_info,
                        "SanApiInfo must be equal to itself")

    def test_sanapiinfo_is_equal_to_another(self):
        '''test identically constructed sanapi objects are equal  '''
        print self.shortDescription()
        san_api_info1 = SanApiInfo()
        san_api_info2 = SanApiInfo()
        self.assertTrue(san_api_info1 == san_api_info2,
                        "SanApiInfo objects must be equal")

    def test_create_storagepoolinfo(self):
        '''test to check creation of storagepoolinfo object'''
        print self.shortDescription()
        spinfo=StoragePoolInfo("sp123", "1", "5", "500000", "250000")
        myassert_is_instance(self, spinfo, StoragePoolInfo)
        self.assertEqual(spinfo.name, "sp123")
        self.assertEqual(spinfo.id, "1")
        self.assertEqual(spinfo.raid, "5")
        self.assertEqual(spinfo.size, "500000")
        self.assertEqual(spinfo.available, "250000")

    def test_HluAluPairInfo_are_equal(self):
        ''' test identically constructed HluAluPairInfo objects are equal '''
        print self.shortDescription()
        hlu_alu_pair_info1 = HluAluPairInfo("1", "2")
        hlu_alu_pair_info2 = HluAluPairInfo("1", "2")
        self.assertTrue(hlu_alu_pair_info1 == hlu_alu_pair_info2,
                        "Hlu objects must be equal")

    def test_HluAluPairInfo_are_not_equal(self):
        ''' test differently constructed HluAluPairInfo objects are equal '''
        print self.shortDescription()
        hlu_alu_pair_info1 = HluAluPairInfo("1", "2")
        hlu_alu_pair_info2 = HluAluPairInfo("2", "2")
        self.assertTrue(hlu_alu_pair_info1 != hlu_alu_pair_info2,
                        "Hlu objects must be different")

    def test_HluAluPairInfo_check_str(self):
        ''' check for expected string when HluAluPairInfo object is printed'''
        print self.shortDescription()
        hlu_alu_pair_info1 = HluAluPairInfo("1", "2")
        self.assertTrue(re.search("HLU:", hlu_alu_pair_info1.__str__()))
        self.assertTrue(re.search("ALU:", hlu_alu_pair_info1.__str__()))

    def test_instantiate_storage_group_info_with_no_shareable_fail(self):
        ''' test storagegroupinfo constructor with missing sharable raises exception '''
        print self.shortDescription()
        self.assertRaises(SanApiOperationFailedException, StorageGroupInfo,
                          "storage name", "1231", "maybe_shareable",
                          "hbasp_list", "hlualu_list")

    def test_instantiate_storage_group_info_with_invalid_hbasp_list_(self):
        ''' test storagegroupinfo constructor with invalid hbasp list raises exception '''
        print self.shortDescription()
        self.assertRaises(SanApiOperationFailedException, StorageGroupInfo,
                          "name", "uid", True, "hbasp_list", "hlualu_list")

    def test_validate_object_list_with_valid_HbaInitiator_list(self):
        ''' test storagegroupinfo constructor with valid hbainit list raises exception '''
        print self.shortDescription()
        storage_group_info = StorageGroupInfo('test', "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", \
                                              True, None, None)

        hba_initiator_info1 = HbaInitiatorInfo("50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", "spname1", "1")
        hba_initiator_info2 = HbaInitiatorInfo("50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", "spname2", "2")
        validation_result = storage_group_info._StorageGroupInfo__validate_object_list(
            [hba_initiator_info1, hba_initiator_info2],
            HbaInitiatorInfo)
        self.assertEqual(validation_result, None, "Validation result must be None")

    def test_validate_object_list_with_valid_HluAluPairInfo_list(self):
        ''' test storagegroupinfo constructor with valid hbainit info list raises exception '''
        print self.shortDescription()
        storage_group_info = StorageGroupInfo('test', "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", \
                                              True, None, None)

        hlu_alu_pair_info1 = HluAluPairInfo("1", "1")
        hlu_alu_pair_info2 = HluAluPairInfo("2", "2")

        validation_result = storage_group_info._StorageGroupInfo__validate_object_list(
            [hlu_alu_pair_info1, hlu_alu_pair_info2],
            HluAluPairInfo)
        self.assertEqual(validation_result, None, "Validation result must be None")

    def test_validate_object_list_with_valid_HluAluPairInfo_list_incorrect_type(self):
        ''' test storagegroupinfo constructor with valid hbainit info list raises exception '''
        print self.shortDescription()
        storage_group_info = StorageGroupInfo('test', "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", \
                                              True, None, None)

        hba_initiator_info1 = HbaInitiatorInfo("50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", "spname1", "1")
        hba_initiator_info2 = HbaInitiatorInfo("50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5A", "spname2", "2")
        hbalist = [hba_initiator_info1, hba_initiator_info2]
        self.assertRaises(
            SanApiOperationFailedException,
            storage_group_info._StorageGroupInfo__validate_object_list,
            hbalist, HluAluPairInfo)

    def test_hbainitinfo_good_params(self):
        ''' test HbaInitiatorInfo constructor with good parameters '''
        print self.shortDescription()
        hbainitinfo=HbaInitiatorInfo("50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", "A", "3" )
        self.assertTrue(re.search("HBA UID:", hbainitinfo.__str__()))

    def test_hbainitinfo_bad_params(self):
        ''' test HbaInitiatorInfo constructor raises when passed bad parameters '''
        print self.shortDescription()
        self.assertRaisesRegexp(SanApiOperationFailedException, "Invalid spport parameter", HbaInitiatorInfo, \
                                "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", "B", "BADPORT" )

    def test_HsPolicyInfo_good_params(self):
        ''' test HsPolicyInfo constructor with valid parameters '''
        print self.shortDescription()
        HsPolicyInfo_obj=HsPolicyInfo("1","SAS","1/25","3")
        self.assertEqual(HsPolicyInfo_obj.policy_id, "1")
        self.assertEqual(HsPolicyInfo_obj.disk_type, "SAS")
        self.assertEqual(HsPolicyInfo_obj.ratio_of_keep_unused, "1/25")
        self.assertEqual(HsPolicyInfo_obj.number_to_keep_unused, "3")

    def test_HsPolicyInfo__policy_id_is_not_an_integer(self):
        ''' test HsPolicyInfo constructor raises exception when policy id is not an integer '''
        print self.shortDescription()
        self.assertRaisesRegexp(SanApiOperationFailedException, "Policy ID must be an integer > 0", HsPolicyInfo, \
                                "abc","SAS","1/25","3" )   

    # TODO: determine if this needs to be skipped
    @skip
    def test_HsPolicyInfo_disk_type_is_of_unknown_type(self):
        ''' test HsPolicyInfo constructor raises exception when disk type is unknown '''
        print self.shortDescription()
        self.assertRaisesRegexp(
           SanApiOperationFailedException,"Unknown Disk Type",HsPolicyInfo, \
                                "1","SASS","1/25","3" )

    def test_HsPolicyInfo_ratio_to_keep_unused_is_not_valid(self):
        ''' test HsPolicyInfo constructor raises exception when ratio to keep unused is not a fraction'''
        print self.shortDescription()
        self.assertRaisesRegexp(
            SanApiOperationFailedException,"Ratio of keep unused",HsPolicyInfo, \
                                 "1","SAS","abc","3" )

    def test_HsPolicyInfo__number_of_disks_to_keep_unused_is_not_an_integer(self):
        ''' test HsPolicyInfo constructor raises exception when number of disks to keep is not an integer '''
        print self.shortDescription()
        self.assertRaisesRegexp(
            SanApiOperationFailedException,"Number of disks to keep unused",HsPolicyInfo, \
                                 "1","SAS","1/25","3a" )

    def test_saninfo___str__and_property_methods(self):
        """
        Check __str__ and @property methods for SanInfo
        """

        print self.shortDescription()
        fakeobj = SanInfo("05.33.008.5.119", "VNX5400", "CKM00190502296")
        vnx_fw = fakeobj._oe_version
        vnx_model = fakeobj._san_model
        vnx_serial = fakeobj._san_serial
        fakeout = "OE Version:           05.33.008.5.119\n" \
                  "Model:                VNX5400\n" \
                  "Serial:               CKM00190502296\n"

        self.assertEqual(vnx_fw, "05.33.008.5.119")
        self.assertEqual(vnx_model, "VNX5400")
        self.assertEqual(vnx_serial, "CKM00190502296")
        self.assertEqual(fakeout, str(fakeobj))

if __name__ == "__main__":
    print "info"
    unittest.main()
