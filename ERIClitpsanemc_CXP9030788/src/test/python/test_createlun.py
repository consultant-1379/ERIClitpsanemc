'''
Created on 9 Jul 2014

@author: edavmax
'''
import unittest
from mock import patch, MagicMock
from vnxcommonapi import VnxCommonApi
from sanapiinfo import LunInfo
from sanapiexception import (SanApiCriticalErrorException,
        SanApiOperationFailedException,
        SanApiEntityAlreadyExistsException)
import logging
import logging.handlers
from sanapilib import *
from emctest import TestSanEMC
import re


class Test(TestSanEMC):

    def setUp(self):
        # create a VnxCommonApi object
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.createluncmdok = "../data/createluninsp.xml.cmdok"
        self.getluncmdok = "../data/getlun.xml.cmdok"
        self.listluncmdok = "../data/lunlist.xml.cmdok"
        self.scope = "global"
        # setup logging with threshold of WARNING
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)
        self.luns = [
        LunInfo("1", "LITP_TORD2_bootvg_2_LUN_28",
            "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
            "TORD2", "174080", "StoragePool", "6"),
        LunInfo("2", "LITP_TORD2_bootvg_2_LUN_28",
            "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
            "TORD2", "174080", "StoragePool", "6"),
        LunInfo("3", "LITP_TORD2_bootvg_2_LUN_28",
            "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
            "TORD2", "174080", "StoragePool", "6"),
        LunInfo("4", "LITP_TORD2_bootvg_2_LUN_28",
            "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
            "TORD2", "174080", "StoragePool", "6"),
        LunInfo("5", "LITP_TORD2_bootvg_2_LUN_28",
            "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
            "TORD2", "174080", "StoragePool", "6"),
             ]
        self.setup_vnx()

    def setup_vnx(self):
        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(
                name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser,
                       self.adminpasswd, self.scope, vcheck=False)

    def replace_lunids(self, new_ids):
        for ii in range(len(new_ids)):
            self.luns[ii]._id = new_ids[ii]

    def test_create_lun_specified_id(self):
        ''' test create_lun with specified lun id'''
        print self.shortDescription()
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun")
        # Test function call with specified  lun_id
        self.vnx.create_lun("lun123", "500Gb", "Storage Pool",
                "sp123", "A", lun_id="123")
        self.vnx.get_lun.assert_called_with(lun_name="lun123")
        self.vnx._navisec.assert_called_with("lun -create -type"\
                " nonThin -capacity 500 -sq gb -poolName \"sp123\" "\
                "-sp a -name \"lun123\" -l 123")

    def test_create_lun_thin(self):
        '''test create_lun with lun_type=nonThin passed'''
        print self.shortDescription()
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun")
        # Test function call with specified  lun_id
        self.vnx.create_lun("lun123", "500Gb", "Storage Pool",
                "sp123", "A", lun_id="123", lun_type="thin")
        self.vnx.get_lun.assert_called_with(lun_name="lun123")
        self.vnx._navisec.assert_called_with("lun -create -type"\
                " Thin -capacity 500 -sq gb -poolName \"sp123\" "\
                "-sp a -name \"lun123\" -l 123") 

    def test_create_lun_auto_lunid(self):
        ''' test create_lun with an unspecified lun id'''
        # Test function call with unspecified lun_id
        print self.shortDescription()
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun")
        self.vnx.create_lun("lun123", "500Gb",
                "Storage Pool", "sp123", "A")
        self.vnx.get_lun.assert_called_with(lun_name="lun123")
        self.vnx._navisec.assert_called_with("lun -create -type"\
                " nonThin -capacity 500 -sq gb -poolName \"sp123\" "\
                "-sp a -name \"lun123\" -aa 1")

    def test_create_lun_xtra_args(self):
        ''' test create_lun with xtra args passed '''
        print self.shortDescription()

        xtra_args = "-initialTier optimizePool"
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun")
        self.vnx.create_lun("lun123", "500Gb", "Storage Pool", "sp123", "A",
                array_specific_options=xtra_args)
        self.vnx.get_lun.assert_called_with(lun_name="lun123")
        self.assertTrue(xtra_args in str(self.vnx._navisec.call_args[0]))

    def test_create_lun_sp_with_ig_thresh(self):
        """test_create_lun - storage pool lun with ignore thresholds"""
        print self.shortDescription()
        lun_name = "ignorant_lun"
        self.vnx._navisec = MagicMock(name="_navisec")
        self.vnx.get_lun = MagicMock(name="get_lun")
        self.vnx.create_lun(lun_name, "500Gb",
                "Storage Pool", "sp123", "A", ignore_thresholds=True)
        self.vnx._navisec.assert_called_with("lun -create -type"\
                " nonThin -capacity 500 -sq gb -poolName \"sp123\" "\
                "-sp a -name \"{0}\" -aa 1 -ignoreThresholds"
                .format(lun_name))
        self.vnx.create_lun(lun_name, "500Gb",
                "Storage Pool", "sp123", "A", ignore_thresholds=False)
        self.vnx._navisec.assert_called_with("lun -create -type"\
                " nonThin -capacity 500 -sq gb -poolName \"sp123\" "\
                "-sp a -name \"{0}\" -aa 1"
                .format(lun_name))

    def test_create_lun_badparams(self):
        ''' test createlun with bad parameters  '''
        print self.shortDescription()

        # bad lun name
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid LUN name", self.vnx.create_lun, 123, "500tb",
                "Storage Pool", "sp123", "B")
        # bad lun type
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid LUN type", self.vnx.create_lun, "lun123",
                "500tb", "Storage Pool", "sp123", "B", lun_type="mejium")
        # bad lun id
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid LUN id", self.vnx.create_lun, "lun123", "500tb",
                "Storage Pool", "sp123", "B", lun_type="thin", lun_id="123a")
        # bad size
        self.assertRaisesRegexp(SanApiOperationFailedException, "Invalid size",
                self.vnx.create_lun, "lun123", "500xb",
                "Storage Pool", "sp123", "A")
        # bad container type
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid container type", self.vnx.create_lun, "lun123",
                "500gb", "badcont", "sp123", "A")
        # bad sp
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid storage processor", self.vnx.create_lun,
                "lun123", "500tb", "Storage Pool", "sp123", "C")
        # no raid_type in create_lun on raid group
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid RAID Type provided:", self.vnx.create_lun,
                "lun123", "500tb", "Raid Group", "sp123", "A")
        # bad ignore_thresholds 
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid ignore_thresholds setting:", self.vnx.create_lun,
                "lun123", "500tb", "Raid Group", "sp123", "A",
                ignore_thresholds="true")
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid ignore_thresholds setting:", self.vnx.create_lun,
                "lun123", "500tb", "Raid Group", "sp123", "A",
                ignore_thresholds=0)
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Invalid ignore_thresholds setting:", self.vnx.create_lun,
                "lun123", "500tb", "Raid Group", "sp123", "A",
                ignore_thresholds="0")

    def test_create_sp_lun_fail_lun_already_exists(self):
        '''Test that create_lun for SG fails with
        SanApiEntityNotFoundException exception if LUN already exists '''
        print self.shortDescription()

        self.vnx._navisec = MagicMock(name="_navisec",
                side_effect=self.side_effects_retry_fail_sp)
        self.assertRaises(SanApiEntityAlreadyExistsException,
                self.vnx.create_lun, "lun123", "500tb", "Storage Pool",
                "sp123", "A")

    def side_effects_retry_fail_sp(self, arg):
        raise SanApiEntityAlreadyExistsException("Oops LUN already exists!", 1)

    def test_get_next_available_lunids(self):
        ''' test get_next_available_lunids returns
        correct number of free LUN IDs '''
        print self.shortDescription()

        # Replaces the LUN IDs in the setup method with the contents
        self.replace_lunids([0, 2, 3, 4, 5])

        self.vnx._get_luns = MagicMock(name="get_luns",
                return_value=self.luns)

        # check 5 free lun ids get returned if enough available
        lunids = self.vnx.get_next_available_lunids(randomise=False)
        self.assertEqual(lunids, [1, 6, 7, 8, 9])

        #  check number of free luns returned if not enough available
        lunids = self.vnx.get_next_available_lunids(7, randomise=False)
        self.assertEqual(lunids, [1, 6])

        # check except gets thrown if no free lun ids available
        self.replace_lunids([0, 1, 2, 3, 4])

        self.vnx._get_luns = MagicMock(name="get_luns",
                return_value=self.luns)
        self.assertRaisesRegexp(SanApiOperationFailedException,
                "No free LUN ID available", self.vnx.get_next_available_lunids,
                "5", randomise=False)

    def test_get_next_available_lunids_bad_params(self):
        ''' test get_next_available_lunids throws
        exception when given bad parameters '''
        print self.shortDescription()

        # Replaces the LUN IDs in the setup method with the contents
        self.replace_lunids([0, 2, 3, 4, 5])

        self.vnx._get_luns = MagicMock(name="get_luns",
                return_value=self.luns)

        self.assertRaisesRegexp(SanApiOperationFailedException,
                "Parameter is not an integer banana ",
                self.vnx.get_next_available_lunids, high_lun="banana")
        self.assertRaisesRegexp(SanApiOperationFailedException,
                "Parameter is not an integer prune ",
                self.vnx.get_next_available_lunids,
                req_num_free_lunids="prune")
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Randomise parameter must be a boolean",
                self.vnx.get_next_available_lunids, randomise="melon")

    @patch("vnxcommonapi.random.shuffle")
    def test_create_lun1_with_auto_lunid(self, mock_shuffle):
        '''Creates a LUN(#1) on a Raid Group. The LUN ID is not
        specified in the create_lun command'''
        print self.shortDescription()

        self.vnx._navisec = MagicMock(name="_navisec")

        # Replaces the LUN IDs in the setup method with the contents
        self.replace_lunids([0, 2, 3, 4, 5])

        ret_lun = LunInfo("1", "autoLUN1",
                "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "RaidGroup", "6")
        # Configures Mocking for test
        self.vnx._get_luns = MagicMock(name="grumpygrant",
                return_value=self.luns)
        self.vnx.get_lun = MagicMock(name="get_lun",
                return_value=ret_lun)

        # Creates LUN
        newlun = self.vnx.create_lun("autoLUN1", "5Gb",
                CONTAINER_RAID_GROUP, "6", raid_type="5")

        # Asserts that get_lun was called once with correct parameter.
        self.vnx.get_lun.assert_called_with(lun_id="1")

    @patch("vnxcommonapi.random.shuffle")
    def test_create_lun3_with_auto_lunid(self, mock_shuffle):
        '''Creates a LUN(#3) on a Raid Group.
        The LUN ID is not specified in the create_lun command'''
        print self.shortDescription()

        self.vnx._navisec = MagicMock(name="_navisec")
        self.replace_lunids([0, 1, 2, 5, 6])

        ret_lun = LunInfo("1", "autoLUN1",
                "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "RaidGroup", "6")

        # Configures Mocking for test
        self.vnx._get_luns = MagicMock(name="grumpygrant",
                return_value=self.luns)
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=ret_lun)

        # Creates LUN
        newlun = self.vnx.create_lun("autoLUN2", "50Tb",
                "Raid Group", "64", raid_type="10")

        # Asserts that get_lun was called once with correct parameter.
        self.vnx.get_lun.assert_called_with(lun_id="3")

    @patch("vnxcommonapi.random.shuffle")
    def test_create_lun5_with_specified_lunid(self, mock_shuffle):
        '''Creates a LUN(#5) on a Raid Group.
        The LUN ID is specified in the create_lun command'''
        print self.shortDescription()

        self.vnx._navisec = MagicMock(name="_navisec")
        ret_lun = LunInfo("5", "specified_LUN1",
                "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
        "TORD2", "174080", "RaidGroup", "10")

        # Configures Mocking for test
        self.vnx._get_luns = MagicMock(name="grumpygrant",
                return_value=self.luns)
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=ret_lun)

        # Creates LUN
        self.vnx.create_lun("specified_LUN1", "53Mb", "Raid Group", "24",
                raid_type="10", lun_id="5")

        # Asserts that get_lun was called once with correct parameter.
        self.vnx.get_lun.assert_called_with(lun_id="5")

    @patch("vnxcommonapi.random.shuffle")
    def test_create_lun_with_no_lunid_specified(self, mock_shuffle):
        '''Creates a LUN(#4) on a Raid Group.
        The LUN ID is not specified in the create_lun command'''
        print self.shortDescription()

        self.vnx._navisec = MagicMock(name="_navisec")
        # Replaces the LUN IDs in the setup method with the contents
        self.replace_lunids([0, 1, 2, 3, 5])

        ret_lun = LunInfo("4", "autoLUN1",
                "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "RaidGroup", "6")

        # Configures Mocking for test
        self.vnx._get_luns = MagicMock(name="grumpygrant",
                return_value=self.luns)
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=ret_lun)

        # Creates LUN
        self.vnx.create_lun("no_LUN_name1", "50Tb", "Raid Group",
                "64", raid_type="6")

        # Asserts that get_lun was called once with correct parameter.
        self.vnx.get_lun.assert_called_once_with(lun_id="4")

    def test_no_lunid_available(self):
        '''Attempts to determine next available LUN ID
        when there is none available'''
        print self.shortDescription()

        ret_lun = LunInfo("4", "autoLUN1",
                "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "RaidGroup", "6")

        # Configures Mocking for test
        self.vnx._get_luns = MagicMock(name="grumpygrant",
                return_value=self.luns)
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=ret_lun)
        self.vnx._navisec = MagicMock(name="_navisec")

        # Replaces the LUN IDs in the setup method with the contents
        self.replace_lunids(range(5))

        self.assertRaisesRegexp(SanApiOperationFailedException,
                "No free LUN ID available",
                self.vnx.get_next_available_lunids, "2", randomise=False)

    @patch("vnxcommonapi.random.shuffle")
    def test_create_rg_lun_retry_succeed(self, mock_shuffle):
        '''Test that create_lun for RG retries if LunAlreadyExists Exception
        results when lun_id is auto'''
        print self.shortDescription()

        self.vnx._navisec = MagicMock(name="_navisec",
                side_effect=self.side_effects_retry_succeed)

        self.replace_lunids(range(5))

        ret_lun = LunInfo("4", "autoLUN1",
                "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "RaidGroup", "6")

        # Configures Mocking for test

        self.vnx._get_luns = MagicMock(name="get_luns",
                return_value=self.luns)
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=ret_lun)
        self.vnx.create_lun("autoLUN1", "50Tb", "RaidGroup", "64",
                raid_type="6")

        # Asserts that both commands were called at least once
        self.assertEqual(self.vnx._navisec.call_count, 6)

    def side_effects_retry_succeed(self, arg):
        if re.search("^bind", arg)\
                and arg != "bind r6 9 -rg 64 -cap 50 -sp a -sq tb":
            raise SanApiEntityAlreadyExistsException(
                    "Oops LUN already exists!", 1)

    @patch("vnxcommonapi.random.shuffle")
    def test_create_rg_lun_retry_fail(self, mock_shuffle):
        '''Test that create_lun for RG fails and
        raises exception after default #retries '''
        print self.shortDescription()

        self.vnx._navisec = MagicMock(name="_navisec",
                side_effect=self.side_effects_retry_fail)
        self.replace_lunids(range(5))
        ret_lun = LunInfo("4", "autoLUN1",
                "60:06:01:60:3F:20:33:00:7E:0C:2E:EA:42:0C:E4:11",
                "TORD2", "174080", "RaidGroup", "6")

        # Configures Mocking for test

        self.vnx._get_luns = MagicMock(name="get_luns",
                return_value=self.luns)
        self.vnx.get_lun = MagicMock(name="get_lun", return_value=ret_lun)
        self.assertRaises(SanApiEntityAlreadyExistsException, self.vnx.create_lun,
                "autoLUN1", "50Tb", "RaidGroup", "64", raid_type="6")

        self.assertEqual(self.vnx._navisec.call_count, 5)

    def side_effects_retry_fail(self, arg):
        raise SanApiEntityAlreadyExistsException("Oops LUN already exists!", 1)

    def test_create_lun_sp(self):
        """test_create_lun - storage pool lun
        - names with spaces are handled correctly"""
        print self.shortDescription()

        name = "space here"
        luninfoobj = [LunInfo("12", name,
            "60:06:01:60:6F:D0:2E:00:BD:E0:3B:E4:72:A6:E1:11",
                           "11", "20mb", "StoragePool", '1')]

        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name='_navisec', return_value=0)

        # Mock called functions
        self.vnx.get_lun = MagicMock(name='get_lun', return_value=luninfoobj)

        # Assert the name is called in its original format
        self.vnx.create_lun(name, '20mb', 'StoragePool', '11')
        self.assertTrue(name in str(self.vnx._navisec.call_args[0]))

    
    def test_create_lun_rg(self):
        """test_create_lun
        - raid group lun - names with spaces are handled correctly"""
        print self.shortDescription()

        name = "space here"
        luninfoobj = [LunInfo("12", name,
                "60:06:01:60:6F:D0:2E:00:BD:E0:3B:E4:72:A6:E1:11",
                "11", "20mb", "RaidGroup", '1')]

        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name='_navisec', return_value=0)

        # Mock called functions
        self.vnx.get_lun = MagicMock(name='get_lun', return_value=luninfoobj)

        self.vnx.create_lun(name, '20mb', 'RaidGroup', '11',
                lun_id='12', raid_type="5")

        call2 = str(self.vnx._navisec.mock_calls[1])
        self.assertTrue(name in call2)
    

if __name__ == "__main__":
    unittest.main()
