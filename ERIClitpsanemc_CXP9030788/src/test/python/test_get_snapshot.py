import unittest
from mock import MagicMock
import logging
from sanapiinfo import LunInfo, SnapshotInfo
from sanapiexception import SanApiEntityNotFoundException
from sanapiexception import SanApiOperationFailedException
from sanapiexception import SanApiMissingInformationException
from vnxcommonapi import VnxCommonApi
from testfunclib import prepare_mocked_popen, data_file
from emctest import TestSanEMC


class TestGestSnapshot(TestSanEMC):

    def setUp(self):
        # create a VnxCommonApi object
        self.spa = "92.168.0.4"
        self.spb = "92.168.1.7"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)

        self.commapi = VnxCommonApi(self.logger)
        self.commapi._accept_and_store_cert = MagicMock(
                name="_accept_and_store_cert")

        self.commapi.initialise((self.spa, self.spb),
                self.adminuser, self.adminpasswd, self.scope, vcheck=False)

    # ======================================================================
    #        -Single Snapshot Tests
    # ======================================================================
    def test_get_snapshot_check_parameters(self):
        ''' testing get_snapshot() returns correct attributes'''
        print self.shortDescription()

        prepare_mocked_popen(data_file("snapshot_get_snapshot.cmdok.xml"))
        snapshot_name = "MySnapshotName"

        self.commapi._get_pool_lun_name_from_lun_id = MagicMock(
                return_value="Vandals_test_lun")

        mysnap = self.commapi.get_snapshot(snapshot_name)

        # Checks that the correct object type is returned
        self.assertIsInstance(mysnap, SnapshotInfo)

        # Checks attribute values are correct
        self.assertEqual(mysnap.snap_name, snapshot_name)
        self.assertEqual(mysnap.resource_id, "260")
        self.assertEqual(mysnap.creation_time, "02/27/15 13:32:37")
        self.assertEqual(mysnap.state, "Ready")
        self.assertEqual(mysnap.resource_name, "Vandals_test_lun")

    def test_get_snapshot_not_found(self):
        ''' testing get_snapshot() raises error for snapshot not found'''
        print self.shortDescription()

        prepare_mocked_popen(
                data_file("snapshot_get_snapshot_empty.cmdok.xml"))
        snapshot_name = "MySnapshotName"
        self.assertRaises(SanApiEntityNotFoundException,
                self.commapi.get_snapshot, snapshot_name)

    def test_get_snapshot_invalid_snap_name(self):
        ''' testing get_snapshot() raises exception
        if snap name not a string'''
        print self.shortDescription()

        self.assertRaises(SanApiOperationFailedException,
                self.commapi.get_snapshot, 1)

    def test_get_snapshot_failure_reading_from_dictionary(self):
        ''' testing get_snapshot() raises exception when
        fails to read from dictionary '''
        print self.shortDescription()

        prepare_mocked_popen(
                data_file("snapshot_get_snapshot.cmdok.xml"))
        self.commapi._get_pool_lun_name_from_lun_id = MagicMock(
                return_value="Vandals_test_lun")
        self.commapi.parser.create_dict = MagicMock(
                name="create_dict", return_value={'a': 'dictionary'})
        self.assertRaises(SanApiOperationFailedException,
                self.commapi.get_snapshot, "Vandals_test_lun")

    # ======================================================================
    #        -Multiple Snapshot Tests
    # ======================================================================

    def test_get_empty_snapshots(self):
        ''' testing get_snapshots() when the output is empty'''
        print self.shortDescription()

        prepare_mocked_popen("../data/snapshot_list_no_snapshots.cmdok.xml")
        snapshots = self.commapi.get_snapshots()

        self.assertEqual(len(snapshots), 0)

    def test_get_snapshots_can_filter_by_LUN_name(self):
        ''' testing get_snapshots() can filter by LUN name'''

        print self.shortDescription()

        self.commapi._get_pool_lun_id_from_lun_name = MagicMock(
                name="_get_pool_lun_id_from_lun_name", return_value='260')
        prepare_mocked_popen(
                data_file("snapshots_get_snapshots_for_lun.cmdok.xml"))

        get_snapshots = self.commapi.get_snapshots(lun_name="LUN_odara")

        # there are two items under the odara lun
        self.assertEqual(len(get_snapshots), 2)
        self.assertEqual([i.resource_id for i in get_snapshots],
                ["260", "260"])
        self.assertEqual([i.resource_name for i in get_snapshots],
                ["LUN_odara", "LUN_odara"])

    def test_get_snapshots_check_parameters(self):
        ''' testing get_snapshots() returns correct attributes'''
        print self.shortDescription()

        # Create SnapshotInfo objects to compare in Unit Tests
        lun260 = LunInfo(lun_id="260",
                      name="LUN_odara",
                      uid="50:01:43:80:18:70:94:89:50:01:43:80:18:70:94:88",
                      container="container_id",
                      size="100MB",
                      container_type="StoragePool",
                      raid="5")

        lun261 = LunInfo(lun_id="261",
                      name="LUN_odara2",
                      uid="50:01:43:80:18:70:94:89:50:01:43:80:18:70:94:89",
                      container="container_id",
                      size="100MB",
                      container_type="StoragePool",
                      raid="5")
        self.commapi._get_luns = MagicMock(
                name="_get_luns", return_value=[lun260, lun261])

        snapshots = self.commapi.get_snapshots()
        # Loop through Snapshot names and check corresponding attributes
        for snapshot in snapshots:
            if snapshot.resource_id == '260':
                self.assertEquals(snapshot.resource_name, 'LUN_odara')
            else:
                self.assertEquals(snapshot.resource_name, 'LUN_odara2')
                self.assertEquals(snapshot.resource_id, '261')

    def test_get_snapshots_failure_reading_from_dictionary(self):
        ''' testing get_snapshots() failure reading from dictionary'''

        print self.shortDescription()

        self.commapi.parser.create_dicts = MagicMock(
                name="create_dicts", return_value={'a': {'a': 'dictionary'}})
        self.assertRaises(SanApiMissingInformationException,
                self.commapi.get_snapshots)


if __name__ == "__main__":
    unittest.main()
