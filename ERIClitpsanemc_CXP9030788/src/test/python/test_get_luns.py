'''
Created on 16 June 2014

@author: edavmax
'''
import unittest
import mock
import logging
from sanapiinfo import LunInfo
from sanapiexception import SanApiCommandException, \
    SanApiOperationFailedException
import sanapilib
from vnxcommonapi import VnxCommonApi
from sanapiinfo import StorageGroupInfo
from testfunclib import *


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
        self.logger.setLevel(logging.DEBUG)

        self.vnxCommApiObj = VnxCommonApi(self.logger)
        self.vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                      self.adminpasswd, self.scope, vcheck = False)

    # Used by old get-SG-luns TCs
    def setUpVnx(self):
        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope, vcheck = False)

    def __created_mocked_luns_in_vnxCommApiObj(self):
        '''
        Private method to create a mocked list of LUNS and return it on the get_luns method
        '''
        self.vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        luns = [LunInfo("28", "LITP_TORD2_bootvg_2_LUN_28", "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "TORD2", "174080", "StoragePool", "6", "A"), \
                LunInfo("29", "myfavlun", "69:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "atpool", "174080", "StoragePool", "6", "A"), \
                LunInfo("30", "myfavlun", "61:06:01:22:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "13", "174080", "RaidGroup", "6", "A"), \
                LunInfo("31", "myfavlun", "61:06:01:12:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "14", "174080", "RaidGroup", "6", "A"), \
                LunInfo("32", "foolun", "13:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "mypool", "174080", "StoragePool", "6", "A"),\
                ]
        self.vnxCommApiObj._get_luns = mock.Mock(return_value=luns)

    ''' GET_LUN() '''
    def test_get_lun_with_existing_id(self):
        ''' testing get_lun() with existing ID '''
        print self.shortDescription() 
        self.__created_mocked_luns_in_vnxCommApiObj()
        lun = self.vnxCommApiObj.get_lun(lun_id="28")
        self.assertEqual(lun.id, "28", "The lun id must be equal")

    def test_get_lun_with_unexisting_id(self):
        ''' testing get_lun() with non-existing ID '''
        print self.shortDescription() 
        self.__created_mocked_luns_in_vnxCommApiObj()
        self.assertRaises(SanApiEntityNotFoundException, self.vnxCommApiObj.get_lun, lun_id="66")

    def test_get_lun_with_existing_name(self):
        ''' testing get_lun() with existing name'''
        print self.shortDescription() 
        self.__created_mocked_luns_in_vnxCommApiObj()
        lun = self.vnxCommApiObj.get_lun(lun_name="LITP_TORD2_bootvg_2_LUN_28")
        self.assertEqual(lun.name, "LITP_TORD2_bootvg_2_LUN_28", "Names must be equal")

    def test_get_lun_with_unexisting_name(self):
        ''' testing get_lun() with non-existing name '''
        print self.shortDescription() 
        self.__created_mocked_luns_in_vnxCommApiObj()
        self.assertRaises(SanApiEntityNotFoundException, self.vnxCommApiObj.get_lun, lun_name="foobar")

    ''' GET_LUNS() '''
    def test_get_luns_in_storage_pools(self):
        ''' testing get_luns() in Storage Pools'''
        print self.shortDescription() 
        prepare_mocked_popen(
            "../data/luns_get_ok_response.xml")
        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        luns = vnxCommApiObj.get_luns(container_type=sanapilib.CONTAINER_STORAGE_POOL)

        lun_info = LunInfo("28", "LITP_TORD2_bootvg_2_LUN_28",
                           "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                           "TORD2", "174080", "StoragePool", "6", "A",
                           "None", "N/A", "N/A", "0", "181602")

        self.assertEqual(len(luns), 33, "The length of the list must be 33")
        myassert_in(self, lun_info, luns, "Lun list must contain lun_info object")

    def test_get_luns_in_a_storage_pool(self):
        ''' testing get_luns() with given storage pool name'''
        print self.shortDescription()
        prepare_mocked_popen(
            "../data/luns_get_ok_response.xml")
        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        luns = vnxCommApiObj.get_luns(container_type=sanapilib.CONTAINER_STORAGE_POOL, container="TORD2")
        lun_info = LunInfo("28", "LITP_TORD2_bootvg_2_LUN_28",
                           "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                           "TORD2", "174080", "StoragePool", "6", "A", "None",
                           "N/A", "N/A", "0", "181602")

        self.assertEqual(len(luns), 5, "The length of the list must be 5")
        myassert_in(self, lun_info, luns, "Lun list must contain lun_info object")

    def test_get_luns_in_raid_groups(self):
        ''' testing get_luns() in Raid Groups'''
        print self.shortDescription() 
        prepare_mocked_popen(
            "../data/getlun_small.xml")
        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        luns = vnxCommApiObj.get_luns(container_type=sanapilib.CONTAINER_RAID_GROUP)
        lun_info = LunInfo("73", "xb2257_58_OSSDG_73",
                           "60:06:01:60:6F:D0:2E:00:BD:E0:3B:E4:72:A6:E1:11",
                           "6", "460800", "RaidGroup", "5", "A")

        self.assertEqual(len(luns), 5, "The length of the list must be 5")
        myassert_in(self, lun_info, luns, "Lun list must contain lun_info object")


    def test_get_luns_in_a_raid_group(self):
        ''' testing get_luns() for specified RG '''
        print self.shortDescription() 
        prepare_mocked_popen(
            "../data/getlun_small.xml")
        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        luns = vnxCommApiObj.get_luns(container_type=sanapilib.CONTAINER_RAID_GROUP, container=6)
        lun_info = LunInfo("73", "xb2257_58_OSSDG_73",
                           "60:06:01:60:6F:D0:2E:00:BD:E0:3B:E4:72:A6:E1:11",
                           "6", "460800", "RaidGroup", "5", "A")

        self.assertEqual(len(luns), 2, "The length of the list must be 2")
        myassert_in(self, lun_info, luns, "Lun list must contain lun_info object")


    ''' From test_get_raid_group_luns '''
    def test_get_raid_group_luns_ok(self):
        """test_get_raid_group_luns_ok where all raid group luns are returned"""
        print self.shortDescription()

        self.setUpVnx()
        luns = self.getBigLunList()
        self.vnx._get_luns = MagicMock(name = "_get_luns", return_value = luns) 

        # Execute the Tested Method
        res_luns=self.vnx.get_luns(container_type="RaidGroup")

        for l in res_luns:
            if l.type != 'RaidGroup':
                self.fail("Non Raid group LUN %s found " % l.id) 

        self.assertEqual (len(res_luns), 43, "Expected 43 luns, got %s" % len(res_luns) ) 


    #@skip
    def test_get_raid_group_luns_by_rg_ok(self):
        """test_get_raid_group_luns_ok where all raid group luns for specific raid group are returned"""
        print self.shortDescription()

        self.setUpVnx()
        luns = self.getBigLunList()
        self.vnx._get_luns = MagicMock(name = "_get_luns", return_value = luns)

        # Execute the Tested Method
        res_luns=self.vnx.get_luns(container_type="RaidGroup", container="2")

        for l in res_luns:
            if l.type != 'RaidGroup':
                self.fail("Non Raid group LUN %s found " % l.id)

        self.assertEqual (len(res_luns), 4, "Expected 43 luns, got %s" % len(res_luns) )


    #@skip
    def test_get_raid_group_luns_none(self):
        """test_get_raid_group_luns where there are no raid group luns"""
        print self.shortDescription()

        self.setUpVnx()
        luns = self.getBigSPLunList()
        self.vnx._get_luns = MagicMock(name = "_get_luns", return_value = luns)

        # Execute the Tested Method
        res_luns=self.vnx.get_luns(container_type="RaidGroup")

        if res_luns:
            self.fail("Should be no LUNs returned") 


    #@skip
    def test_get_raid_group_luns_by_id_none(self):
        """test_get_raid_group_luns by id where there are no raid group luns"""
        print self.shortDescription()

        self.setUpVnx()
        luns = self.getBigSPLunList()
        self.vnx._get_luns = MagicMock(name = "_get_luns", return_value = luns)

        # Execute the Tested Method
        res_luns=self.vnx.get_luns(container_type="RaidGroup", container="2")

        if res_luns:
            self.fail("Should be no LUNs returned")



    def getBigSPLunList(self):
        """ List has no raid group luns and 12 storage pool luns."""
        l = []

        l.append( LunInfo("42", "gerrylun", "60:06:01:60:97:D0:35:00:61:31:E3:10:2D:22:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("61", "sharedlun1", "60:06:01:60:97:D0:35:00:B7:54:43:36:BC:2E:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("67", "data001", "60:06:01:60:97:D0:35:00:C7:46:B3:60:87:2F:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("48", "lun1", "60:06:01:60:97:D0:35:00:38:CD:C0:71:57:24:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("46", "fedepool_1", "60:06:01:60:97:D0:35:00:90:29:C5:6C:E3:22:E4:11", "fedepool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("44", "gerrylun2", "60:06:01:60:97:D0:35:00:2D:A0:87:5C:32:22:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("41", "davemaxwellisaniceguy_1", "60:06:01:60:97:D0:35:00:5D:55:E1:19:C4:23:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("49", "lun2", "60:06:01:60:97:D0:35:00:BE:78:58:83:57:24:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("63", "MaxwellHouse", "60:06:01:60:97:D0:35:00:F7:A0:AF:22:C9:23:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("91", "LUN", "60:06:01:60:97:D0:35:00:92:7D:C5:99:D2:38:E4:11", "eadapar_pool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("53", "richards_pool", "60:06:01:60:97:D0:35:00:03:6D:77:A9:6E:24:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("32", "gerrylun1", "60:06:01:60:97:D0:35:00:74:4A:3E:89:0F:22:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        return l 

    def getBigLunList(self):
        """ List has 43 raid group LUNs and 12 storage pool luns.  4 luns belong to RG 2 """
        l = []
        l.append( LunInfo("42", "gerrylun", "60:06:01:60:97:D0:35:00:61:31:E3:10:2D:22:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("29", "GEO_LUN_6", "60:06:01:60:97:D0:35:00:22:7B:0F:E8:3A:1E:E4:11", "3", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("61", "sharedlun1", "60:06:01:60:97:D0:35:00:B7:54:43:36:BC:2E:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("35", "GEO_LUN_13", "60:06:01:60:97:D0:35:00:D4:6C:07:9E:3B:1E:E4:11", "4", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("67", "data001", "60:06:01:60:97:D0:35:00:C7:46:B3:60:87:2F:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("24", "GEO_LUN_1", "60:06:01:60:97:D0:35:00:36:AE:B9:9C:3A:1E:E4:11", "2", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("25", "GEO_LUN_2", "60:06:01:60:97:D0:35:00:23:D6:05:A8:3A:1E:E4:11", "2", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("26", "GEO_LUN_3", "60:06:01:60:97:D0:35:00:28:7B:7D:B8:3A:1E:E4:11", "2", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("27", "GEO_LUN_4", "60:06:01:60:97:D0:35:00:C2:85:66:C6:3A:1E:E4:11", "2", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("20", "xb947_fencing_3", "60:06:01:60:97:D0:35:00:E6:C6:5E:13:3A:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("21", "xb947_fencing_4", "60:06:01:60:97:D0:35:00:3F:93:1A:2C:3A:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("48", "lun1", "60:06:01:60:97:D0:35:00:38:CD:C0:71:57:24:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("23", "xb947_fencing_6", "60:06:01:60:97:D0:35:00:29:B9:02:4D:3A:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("46", "fedepool_1", "60:06:01:60:97:D0:35:00:90:29:C5:6C:E3:22:E4:11", "fedepool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("44", "gerrylun2", "60:06:01:60:97:D0:35:00:2D:A0:87:5C:32:22:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("45", "rgLUN3", "60:06:01:60:97:D0:35:00:8A:FE:65:27:E2:34:E4:11", "7", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("28", "GEO_LUN_5", "60:06:01:60:97:D0:35:00:AD:29:3D:D9:3A:1E:E4:11", "3", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("43", "rgLUN1", "60:06:01:60:97:D0:35:00:6A:4E:6C:0E:E2:34:E4:11", "7", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("40", "GEO_LUN_17", "60:06:01:60:97:D0:35:00:86:A7:60:00:3C:1E:E4:11", "5", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("41", "davemaxwellisaniceguy_1", "60:06:01:60:97:D0:35:00:5D:55:E1:19:C4:23:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("1", "xb1392_OSSDG_2", "60:06:01:60:97:D0:35:00:C1:CB:43:27:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("0", "xb1392_OSSDG_1", "60:06:01:60:97:D0:35:00:91:92:B5:B4:37:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("3", "xb1392_SYBASEDG_2", "60:06:01:60:97:D0:35:00:C3:A4:96:66:39:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("2", "xb1392_SYBASEDG_1", "60:06:01:60:97:D0:35:00:F9:6F:9E:3B:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("5", "xb1392_fencing_2", "60:06:01:60:97:D0:35:00:5D:0F:14:7F:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("4", "xb1392_fencing_1", "60:06:01:60:97:D0:35:00:02:BD:B5:6B:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("7", "xb1392_fencing_4", "60:06:01:60:97:D0:35:00:C4:B0:ED:AC:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("6", "xb1392_fencing_3", "60:06:01:60:97:D0:35:00:F7:A2:C7:96:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("9", "xb1392_fencing_6", "60:06:01:60:97:D0:35:00:D8:34:64:DD:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("8", "xb1392_fencing_5", "60:06:01:60:97:D0:35:00:70:9C:39:C5:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("49", "lun2", "60:06:01:60:97:D0:35:00:BE:78:58:83:57:24:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("63", "MaxwellHouse", "60:06:01:60:97:D0:35:00:F7:A0:AF:22:C9:23:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("39", "GEO_LUN_16", "60:06:01:60:97:D0:35:00:60:5B:9E:EC:3B:1E:E4:11", "5", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("12", "xb947_OSSDG_1", "60:06:01:60:97:D0:35:00:D4:96:5C:8F:39:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("91", "LUN", "60:06:01:60:97:D0:35:00:92:7D:C5:99:D2:38:E4:11", "eadapar_pool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("95", "rgLUN2", "60:06:01:60:97:D0:35:00:A6:7F:22:19:E2:34:E4:11", "7", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("14", "xb947_SYBASEDG_1", "60:06:01:60:97:D0:35:00:90:D7:E1:B0:39:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("11", "xb1392_pri", "60:06:01:60:97:D0:35:00:71:50:B0:09:39:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("10", "xb1392_sec", "60:06:01:60:97:D0:35:00:6C:26:C8:F3:38:1E:E4:11", "0", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("13", "xb947_OSSDG_2", "60:06:01:60:97:D0:35:00:2D:65:FC:70:3A:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("38", "GEO_LUN_15", "60:06:01:60:97:D0:35:00:F1:28:D8:DB:3B:1E:E4:11", "5", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("15", "xb947_SYBASEDG_2", "60:06:01:60:97:D0:35:00:68:9D:7D:C8:39:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("22", "xb947_fencing_5", "60:06:01:60:97:D0:35:00:37:77:36:3D:3A:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("17", "xb947_sec", "60:06:01:60:97:D0:35:00:F3:E5:D8:E1:39:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("16", "xb947_pri", "60:06:01:60:97:D0:35:00:6F:C8:97:D3:39:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("33", "GEO_LUN_10", "60:06:01:60:97:D0:35:00:44:74:58:5C:3B:1E:E4:11", "4", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("18", "xb947_fencing_1", "60:06:01:60:97:D0:35:00:80:33:C0:F4:39:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("31", "GEO_LUN_8", "60:06:01:60:97:D0:35:00:03:79:05:0D:3B:1E:E4:11", "3", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("30", "GEO_LUN_7", "60:06:01:60:97:D0:35:00:D8:1C:A4:FF:3A:1E:E4:11", "3", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("37", "GEO_LUN_14", "60:06:01:60:97:D0:35:00:A7:1C:7D:B5:3B:1E:E4:11", "5", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("36", "GEO_LUN_12", "60:06:01:60:97:D0:35:00:B0:AC:6E:8B:3B:1E:E4:11", "4", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("53", "richards_pool", "60:06:01:60:97:D0:35:00:03:6D:77:A9:6E:24:E4:11", "atpool", "10Gb", "StoragePool", "5", "A"))
        l.append( LunInfo("34", "GEO_LUN_11", "60:06:01:60:97:D0:35:00:59:64:28:6B:3B:1E:E4:11", "4", "10Gb", "RaidGroup", "1", "A"))
        l.append( LunInfo("19", "xb947_fencing_2", "60:06:01:60:97:D0:35:00:FB:24:B5:02:3A:1E:E4:11", "1", "10Gb", "RaidGroup", "5", "A"))
        l.append( LunInfo("32", "gerrylun1", "60:06:01:60:97:D0:35:00:74:4A:3E:89:0F:22:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
        return l


    #@skip
    def test_get_luns_in_a_storage_group(self):
        ''' testing get_luns() in specified SG'''
        print self.shortDescription() 
        prepare_mocked_popen(
            "../data/list_sg_atsfs43_44.xml")
        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        all_luns = [LunInfo("28", "LITP_TORD2_bootvg_2_LUN_28", "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "TORD2", "174080", "StoragePool", "6", "A"), \
                LunInfo("29", "myfavlun", "69:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "atpool", "174080", "StoragePool", "6", "A"), \
                LunInfo("30", "myfavlun", "61:06:01:22:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "13", "174080", "RaidGroup", "6", "A"), \
                LunInfo("31", "myfavlun", "61:06:01:12:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "14", "174080", "RaidGroup", "6", "A"), \
                LunInfo("32", "foolun", "13:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "mypool", "174080", "StoragePool", "6", "A"),\
                ]
        vnxCommApiObj._get_luns = mock.Mock(return_value=all_luns)

        luns = vnxCommApiObj.get_luns(sg_name="atsfs43_44")
        lun_info = LunInfo("29", "myfavlun", "69:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11", 
                "atpool", "174080", "StoragePool", "6", "A")

        self.assertEqual(len(luns), 3, "The length (%s) of the list must be 3" % str(len(luns)))
        myassert_in(self, lun_info, luns, "Lun list must contain lun_info object")



    ''' From test_get_storage_group_luns.py '''

    #@skip
    def test_get_storage_group_luns(self):
        """test_get_storage_group_luns"""
        print self.shortDescription()

        self.setUpVnx()

        hbl = getHbaList2()
        hll = getHluList2()
        sgname='xb947_949'
        sg = StorageGroupInfo(sgname, '1B:ED:5D:17:3E:1E:E4:11:B4:8F:00:60:16:5D:22:25', True, hbl, hll)

        luns = getLunList()

        self.vnx.get_storage_group = MagicMock(name = "get_storage_group", return_value = sg) 
        self.vnx._get_luns = MagicMock(name = "_get_luns", return_value = luns) 

        # Execute the Tested Method
        res_luns=self.vnx.get_luns(sg_name=sgname)

        lun_ids = []
        for i in res_luns:
            lun_ids.append(i.id)

        alu_ids = []
        for i in hll:
            alu_ids.append(i.alu)

        # verify that the lun ids in the returned lun list match the ALU no from the storage group
        lun_ids.sort()
        alu_ids.sort()

        self.assertEqual (lun_ids, alu_ids, "Returned luns are incorrect, expected:\n%s\nGot:\n%s" %(alu_ids, lun_ids) )


    #@skip
    def test_get_storage_group_luns_no_alu(self):
        """test_get_storage_group_luns_no_alu"""
        print self.shortDescription()

        self.setUpVnx()

        hbl = getHbaList2()
        hll = None 
        sgname='xb947_949'
        sg = StorageGroupInfo(sgname, '1B:ED:5D:17:3E:1E:E4:11:B4:8F:00:60:16:5D:22:25', True, hbl, hll)

        luns = getLunList()

        self.vnx.get_storage_group = MagicMock(name = "get_storage_group", return_value = sg)
        self.vnx._get_luns = MagicMock(name = "_get_luns", return_value = luns)

        # Execute the Tested Method
        res_luns=self.vnx.get_luns(sg_name=sgname)
        self.assertEqual (res_luns, [], "There should be no luns returned, we got %s:\n" %(res_luns ))


    #@skip
    def test_get_storage_group_luns_no_sg(self):
        """test_get_storage_group_luns_no_sg"""
        print self.shortDescription()

        self.setUpVnx()

        hbl = getHbaList2()
        hll = None
        sgname='nonexistent'

        luns = getLunList()

        self.vnx.get_storage_group = MagicMock(name = "get_storage_group", side_effect=SanApiCommandException("Error: storagegroup command failed", 1))
        self.vnx._get_luns = MagicMock(name = "_get_luns", return_value = luns)
        #self.vnx.get_luns(sg_name=sgname)

        # Execute the Tested Method
        self.assertRaises(SanApiCommandException, self.vnx.get_luns, sg_name=sgname)

        
    def test_get_lun_by_name(self):
        """test_get_lun_by_name - names with spaces are handled correctly"""
        print self.shortDescription()

        self.setUpVnx()

        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)

        # Mock called functions as we are not interested in them, only the cmd string structure
        self.vnx.parser.create_dicts = MagicMock(name = 'create_dicts', return_value={})

        luns=getLunList()
        self.vnx.parser.create_object_list = MagicMock(name = 'create_object_list', return_value=luns)

        name="space here"
        cmd_string = "lun -list"

        #call('getlun')
        #call('lun -list')

        print "Verifying navisec is called with: %s" % cmd_string
        lun = self.vnx.get_lun(lun_name=name)

        self.assertEquals(lun.name, name)

        call1=str(self.vnx._navisec.mock_calls[0]) 
        call2=str(self.vnx._navisec.mock_calls[1])
        self.assertEquals(call1, 'call(\'getlun\')')
        self.assertEquals(call2, 'call(\'lun -list\')')


    #@skip
    def test_get_storage_pool_luns(self):
        """test_get_storage_pool_luns - names with spaces are handled correctly"""
        print self.shortDescription()

        self.setUpVnx()

        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)

        # Mock called functions as we are not interested in them, only the cmd string structure
        self.vnx.parser.create_dicts = MagicMock(name = 'create_dicts', return_value=None)
        luns=getLunList()
        self.vnx.parser.create_object_list = MagicMock(name = 'create_object_list', return_value=luns)

        name="space here"
        cmd_string = "lun -list"

        print "Verifying navisec is called with: %s" % cmd_string
        self.vnx.get_luns(container_type="StoragePool", container=name)
        self.vnx._navisec.assert_called_once_with(cmd_string)
        

    def test_get_lun_without_info(self):
        """Test _get_luns fails with correct exception when missing info"""
        self.setUpVnx()
        self.vnx.parser.create_dicts = MagicMock(name="create_dicts",
                return_value={"a":{}})

        self.assertRaises(SanApiMissingInformationException,
                self.vnx._get_luns)

    #@skip
    def test_get_storage_group_luns_spaces(self):
        """test_get_storage_group_luns - names with spaces are handled correctly"""
        print self.shortDescription()

        self.setUpVnx()
        
        sgname="mysg"
        uid = 'C4:0C:E5:04:2F:08:E4:11:BC:CB:00:60:16:54:1A:87'
        shareable = True
        hbasp = None
        hlualu = None
        reference_sg = StorageGroupInfo(sgname, uid, shareable, hbasp, hlualu)

        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)

        # Mock called functions as we are not interested in them, only the cmd string structure
        self.vnx.parser.create_sg_list = MagicMock(name = 'create_sg_list', return_value=[reference_sg])

        luns=getLunList()
        name="space here"
        cmd_string = "storagegroup -list -gname \"%s\"" % name

        print "Verifying navisec is called with: %s" % cmd_string
        self.vnx.get_luns(sg_name=name)
        self.vnx._navisec.assert_called_once_with(cmd_string, logmsg=True)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
