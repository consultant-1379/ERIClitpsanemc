''''
Created on the 23rd of April 2015

@author: xbobobo
'''

import unittest
from mock import MagicMock
from vnxcommonapi import VnxCommonApi
from sanapiexception import SanApiEntityAlreadyExistsException,\
                            SanApiEntityNotFoundException
import logging
import logging.handlers
from testfunclib import prepare_mocked_popen, data_file
from emctest import TestSanEMC


class TestRestoreSnapshot(TestSanEMC):
    '''
    Test class containing Test Cases designed to test the
    SAN Restore Snapshot functionality.
    Uses Unittest.
    '''

    def setUp(self):
        # create a VnxCommonApi object
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "****"
        self.scope = "global"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)

        self.changehandler = logging.StreamHandler()
        self.changehandler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.changehandler)

        self.setUpVnx()

    def setUpVnx(self):
        ''' setup a VNX with MagicMock'''

        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(
                name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser,
                       self.adminpasswd, self.scope, vcheck=False)

    def tearDown(self):
        super(TestRestoreSnapshot, self).tearDown()
        self.logger.removeHandler(self.changehandler)

    def test_restore_snapshot_keep_backup(self):
        ''' testing test_restore_snapshot_keep_backup with all parameters ok\
        while keeping the Backup'''
        print self.shortDescription()

        prepare_mocked_popen(data_file("navisec_response_success.xml"))

        lunid = "28"
        self.vnx._get_pool_lun_id_from_lun_name = MagicMock(return_value=lunid)

        self.assertTrue(self.vnx.restore_snapshot(lun_name="lunUnitTest",
            snap_name="testingRestoreSnapshot", delete_backupsnap=False),
                                "restore_snapshot does not return True")

    def test_restore_snapshot_delete_backup(self):
        ''' testing test_restore_snapshot_delete_backup with all parameters ok\
        while Deleting the Backup'''
        print self.shortDescription()

        prepare_mocked_popen(data_file("navisec_response_success.xml"))

        lunid = "28"
        self.vnx._get_pool_lun_id_from_lun_name = MagicMock(return_value=lunid)

        self.assertTrue(self.vnx.restore_snapshot(lun_name="lunUnitTest",
                                    snap_name="testingRestoreSnapshot"),
                                    "restore_snapshot does not return True")

    def test_restore_snapshot_incorrect_snap_name(self):
        ''' testing test_restore_snapshot_incorrect_snap_name with an\
        incorrect snap_name parameter'''
        print self.shortDescription()

        prepare_mocked_popen(
                data_file("snapshot_get_snapshot_empty.cmdok.xml"))
        self.assertRaises(SanApiEntityNotFoundException,
                           self.vnx.restore_snapshot, "lunUnitTest",
                           "testingRestoreSnapshot")

    def test_restore_snapshot_incorrect_lunid(self):
        ''' testing test_restore_snapshot_incorrect_lunid with an incorrect\
        lun_id parameter'''
        print self.shortDescription()

        prepare_mocked_popen(data_file("restore_snapshot_incorrect_lunid.xml"))

        lunid = "30"
        self.vnx._get_pool_lun_id_from_lun_name = MagicMock(return_value=lunid)

        self.assertRaises(SanApiEntityNotFoundException,
                           self.vnx.restore_snapshot, "lunUnitTest_incorrect",
                           "testingRestoreSnapshot")

    def test_restore_snapshot_backup_name_already_exists(self):
        ''' testing test_restore_snapshot_backup_name_already_exists where the\
        Backup name parameter passed to Naviseccli already exists'''
        print self.shortDescription()

        prepare_mocked_popen(data_file("snapshot_error_response_name_"
                             "already_exists.xml"))

        lunid = "28"
        self.vnx._get_pool_lun_id_from_lun_name = MagicMock(return_value=lunid)

        self.assertRaises(SanApiEntityAlreadyExistsException,
                           self.vnx.restore_snapshot, "lunUnitTest",
                           "testingRestoreSnapshot")


if __name__ == "__main__":
    unittest.main()
