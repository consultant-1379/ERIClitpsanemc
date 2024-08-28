"""
Created on 24 Jul 2014

@author: eadapar
"""

import logging.handlers
import unittest
from testfunclib import *
from vnxcommonapi import VnxCommonApi
from emctest import TestSanEMC


class Test(TestSanEMC):
    """
    Test class contains methods to add a LUN or LUNs to a pre-existing
    Storage Group
    """

    def setUpVnx(self):
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(
                                                name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser,
                       self.adminpasswd, self.scope, vcheck=False)

    def setUp(self):
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

    def setUpMocks(self, sgname=None, mock_navisec=False, mock_get_sg=False):

        # Configures dummy storage group used in assertions tests
        uid = 'C4:0C:E5:04:2F:08:E4:11:BC:CB:00:60:16:54:1D:87'
        shareable = True
        hbasp_list = None
        hlualu_list = None

        if sgname is None:
            sgname="SGName"

        self.ref_sg = StorageGroupInfo(sgname, uid, shareable,
                                      hbasp_list, hlualu_list)
        if mock_navisec:
            self.vnx._navisec = MagicMock(name="_navisec")
        if mock_get_sg:
            self.vnx.get_storage_group = MagicMock(
                        name="get_storage_group", return_value=self.ref_sg)

    def test_add_lun_to_storage_group_hlu(self):
        """
        Test adding LUN to SG with HLU & ALU specified
        """

        print self.shortDescription()

        self.setUpVnx()
        self.setUpMocks('eadapar_single_sg_operation', True, True)

        # Assigns the built navisec command to "test_sg"
        test_sg = self.vnx.add_lun_to_storage_group(
                                "eadapar_single_sg_operation", "0", "23")

        # Asserts that each of the Storage Group calls in previous command
        # were called.
        self.vnx._navisec.assert_any_call("storagegroup -addhlu " +
                "-gname \"eadapar_single_sg_operation\" " + "-hlu 0 -alu 23")

        self.assertEquals(self.ref_sg, test_sg, "Storage Groups Differ")
        self.assertIsInstance(test_sg, StorageGroupInfo)

    def test_add_luns_to_storage_group_hlu(self):
        """
        Test adding LUN to Storage Group with HLU specified
        """

        print self.shortDescription()

        self.setUpVnx()
        self.setUpMocks('eadapar_multiple_sg_operation', True, True)

        # Assigns the built navisec command to "test_sg"
        test_sg = self.vnx.add_luns_to_storage_group(
                "eadapar_multiple_sg_operation", [["0", "23"], ["1", "24"]])

        # Asserts that each of the Storage Group calls in previous command
        # were called.
        self.vnx._navisec.assert_any_call("storagegroup -addhlu " +
                '-gname "eadapar_multiple_sg_operation" -hlu 0 -alu 23')
        self.vnx._navisec.assert_any_call("storagegroup -addhlu " +
                '-gname "eadapar_multiple_sg_operation" -hlu 1 -alu 24')

        self.assertEquals(self.ref_sg, test_sg, "Storage Groups Differ")
        self.assertIsInstance(test_sg, StorageGroupInfo)

    def test_add_lun_to_storage_group_with_badparams(self):
        """
        Test add_lun_to_storage_group with bad params
        """

        print self.shortDescription()

        # Mocks response to add_lun_to_storage_group commands
        self.setUpVnx()
        self.setUpMocks()
        self.refSG = getPairsSG()

        # =====================================================================
        #        Tests for adding single hlu_alu pair to storage group
        # =====================================================================

        # =====================================================================
        #        -Storage Group Tests
        # =====================================================================

        # 1. Invalid Storage Group Name(Blank)
        self.assertRaisesRegexp(SanApiCriticalErrorException,
            "Invalid storage group name",
            self.vnx.add_lun_to_storage_group, "", "0", "23")

        # 2. Invalid Storage Group Name(None)
        self.assertRaisesRegexp(SanApiCriticalErrorException,
            "Invalid storage group name",
            self.vnx.add_lun_to_storage_group, None, "0", "23")

        # =====================================================================
        #        -HLU Tests
        # =====================================================================

        # 3. Invalid  HLU(letter in field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_lun_to_storage_group,
            "eadapar_adding_single_hlu_alu_pair", "7425665c", "23")

        # 4. Invalid HLU(None)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_lun_to_storage_group,
            "eadapar_adding_single_hlu_alu_pair", None, "23")

        # 6. Invalid HLU(blank)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_lun_to_storage_group,
            "eadapar_adding_single_hlu_alu_pair", "", "23")

        # =====================================================================
        #        -ALU Tests
        # =====================================================================

        # 7. Invalid  ALU(letter in field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_lun_to_storage_group,
            "eadapar_adding_single_hlu_alu_pair", "0", "7425665d")

        # 8. Invalid ALU(None)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_lun_to_storage_group,
            "eadapar_adding_single_hlu_alu_pair", "0", None)

        # 9. Invalid ALU(Blank)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_lun_to_storage_group,
            "eadapar_adding_single_hlu_alu_pair", "0", "")

    def test_add_luns_to_storage_group_with_badparams(self):
        """
        Test add_luns_to_storage_group with bad params
        """

        print self.shortDescription()

        # Mocks response to add_lun_to_storage_group commands
        self.setUpVnx()
        self.setUpMocks(None, True, True)
        self.refSG = getPairsSG()

        # =====================================================================
        #        Tests for adding multiple hlu_alu pairs to storage group
        # =====================================================================

        # =====================================================================
        #        -Storage Group Tests
        # =====================================================================

        # 10. Invalid Storage group(Blank)
        self.assertRaisesRegexp(SanApiCriticalErrorException,
            "Invalid storage group name",
            self.vnx.add_luns_to_storage_group,
            "", [["0", "23"], ["1", "24"]])

        # 11. Invalid Storage group(None)
        self.assertRaisesRegexp(SanApiCriticalErrorException,
            "Invalid storage group name",
            self.vnx.add_luns_to_storage_group,
            None, [["0", "23"], ["1", "24"]])
        # =====================================================================
        #        -HLU Tests
        # =====================================================================

        # 1. Invalid HLU(letter in 1st HLU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["7425665e", "23"], ["1", "24"]])

        # 2. Invalid HLU(blank 1st HLU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["", "23"], ["1", "24"]])

        # 3. Invalid HLU(None in 1st HLU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [[None, "23"], ["1", "24"]])

        # 4. Invalid HLU(letter in 2st HLU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", "23"], ["7425665f", "24"]])

        # 5. Invalid HLU(blank 2st HLU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", "23"], ["", "24"]])

        # 6. Invalid HLU(None in 2st HLU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid HLU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", "23"], [None, "24"]])

        # =====================================================================
        #        -ALU Tests
        # =====================================================================

        # 7. Invalid ALU(letter in 1st ALU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", "7425665g"], ["1", "24"]])

        # 8. Invalid ALU(blank 1st ALU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", ""], ["1", "24"]])

        # 9. Invalid ALU(None in 1st ALU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", None], ["1", "24"]])

        # 10. Invalid ALU(letter in 2st ALU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", "23"], ["1", "7425665h"]])

        # 11. Invalid ALU(blank 2st ALU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", "23"], ["1", ""]])

        # 12. Invalid ALU(None in 2st ALU field)
        self.assertRaisesRegexp(SanApiCriticalErrorException, "Invalid ALU:",
            self.vnx.add_luns_to_storage_group,
            "eadapar_adding_multiple_hlu_alu_pair",
            [["0", "23"], ["1", None]])

    def test_add_luns_to_storage_group_hlu_already_exists(self):
        """
        Test adding HLU to SG raises exception when HLU already exists in SG
        """

        print self.shortDescription()
        mock_popen = prepare_mocked_popen(
            "../data/storagegroup_hlu_already_exists.xml", None, 0)

        self.setUpVnx()
        self.assertRaisesRegexp(SanApiEntityAlreadyExistsException,
            "Requested LUN has already been added to this Storage Group",
            self.vnx.add_lun_to_storage_group, "mysg", "1", "2")

    def test_add_lun_to_storage_group(self):
        """
        Test add LUN to SG - names with spaces are handled correctly
        """

        print self.shortDescription()

        self.setUpVnx()

        # Mock navisec to check the cmd string constructed
        self.setUpMocks(None, True, True)

        name = "space here"
        hlu = '0'
        alu = '0'

        print "Verifying navisec is called with '%s' in cmd string " % name
        self.vnx.add_lun_to_storage_group(name, hlu, alu)
        self.assertTrue(name in self.vnx._navisec.call_args[0][0])

    def test_add_luns_to_storage_group(self):
        """
        Test add LUNs to SG - names with spaces are handled correctly
        """

        print self.shortDescription()

        self.setUpVnx()

        # Mock navisec to check the cmd string constructed
        self.setUpMocks(None, True, True)

        name = "space here"
        hlu = '0'
        alu = '0'
        pair = [[hlu, alu]]

        print "Verifying navisec is called with: '%s' in cmd string " % name
        self.vnx.add_luns_to_storage_group(name, pair)
        self.assertTrue(name in self.vnx._navisec.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
