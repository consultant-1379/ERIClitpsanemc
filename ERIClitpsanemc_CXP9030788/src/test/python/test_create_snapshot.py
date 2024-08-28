import unittest
from mock import MagicMock
from vnxcommonapi import VnxCommonApi
from sanapiinfo import SnapshotInfo
from sanapiexception import SanApiOperationFailedException, SanApiEntityAlreadyExistsException, SanApiEntityNotFoundException
import logging
import logging.handlers
from testfunclib import prepare_mocked_popen

class Test(unittest.TestCase):

    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "****"
        self.scope = "global"
        self.timeout = "60"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.DEBUG)
        self.logger.addHandler(self.ch)
        self.setUpVnx()

    def tearDown(self):
        self.logger.removeHandler(self.ch)

    def setUpVnx(self):
        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser,
                       self.adminpasswd, self.scope, vcheck = False)

    def test_create_snapshot(self):

        ''' testing test_create_snapshot with all parameters ok'''
        print self.shortDescription()

        self.setUpVnx()
        prepare_mocked_popen("../data/navisec_response_success.xml")
        self.vnx._get_pool_lun_id_from_lun_name = MagicMock(return_value="28")

        snapshotInfoObj = SnapshotInfo("28", "snapshotUnitTest", "04/14/15 16:12:37", "Ready", "lunUnitTest")
        self.vnx.get_snapshot = MagicMock(return_value=snapshotInfoObj)

        # Ensure assertEqual is checking object values and not just object address
        snapshotInfoObj2 = SnapshotInfo("28", "snapshotUnitTest", "04/14/15 16:12:37", "Ready", "lunUnitTest")

        self.assertEqual(self.vnx.create_snapshot("lunUnitTest", "snapshotUnitTest"), snapshotInfoObj2)

    def test_create_snapshot_invalid_lun_name(self):

        ''' testing test_create_snapshot_invalid_lun_name with an invalid Lun name'''
        print self.shortDescription()

        self.setUpVnx()
        self.assertRaises(SanApiOperationFailedException, self.vnx.create_snapshot, 1, "snapshotUnitTest")

    def test_create_snapshot_snap_name_alreay_in_use(self):

        ''' testing test_create_snapshot_snap_name_alreay_in_use '''
        print self.shortDescription()

        self.setUpVnx()
        prepare_mocked_popen("../data/snapshot_error_response_name_already_exists.xml")
        self.vnx._get_pool_lun_id_from_lun_name = MagicMock(return_value="28")
        self.assertRaises(SanApiEntityAlreadyExistsException,
                           self.vnx.create_snapshot, "lunUnitTest", "snapshotUnitTest")

    def test_create_snapshot_resource_does_not_exist(self):

        ''' testing test_create_snapshot_resource_does_not_exist '''
        print self.shortDescription()

        self.setUpVnx()
        prepare_mocked_popen("../data/create_snapshot_error_resource_not_exists.xml")
        self.vnx._get_pool_lun_id_from_lun_name = MagicMock(return_value="28")
        self.assertRaises(SanApiEntityNotFoundException,
                           self.vnx.create_snapshot, "lunUnitTest", "snapshotUnitTest")

if __name__ == "__main__":
    unittest.main()
