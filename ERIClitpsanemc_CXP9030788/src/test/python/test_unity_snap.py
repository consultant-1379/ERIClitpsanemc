
import unittest

from sanapiinfo import SnapshotInfo
from sanapiexception import SanApiOperationFailedException, \
                     SanApiEntityNotFoundException, SanApiCriticalErrorException

from unitytest import TestUnity


class TestUnitySnap(TestUnity):
    """
    Test class contains methods to test snap methods
    """

    def test_get_snapshots_all(self):
        """Get all snapshots
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/snap/instances?fields=id,name,lun,description,creationTime,state',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': '1',
                            'state': 2,
                            'name':'test1_snap',
                            'description':'',
                            'creationTime':'2019-01-29T13:46:22.005Z',
                            'lun': {
                                'id':'sv_1'
                            }
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/lun/instances?filter=id IN ( "sv_1" )&fields=id,name',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'sv_1',
                            'name': 'test1_lun'
                        }
                    }
                ]
            }
        )

        test_snapshots = self.unityapi.get_snapshots()
        self.assertEqual(len(test_snapshots), 1)
        test_snapshot = test_snapshots[0]
        self.assertIsInstance(test_snapshot, SnapshotInfo)
        self.assertEqual(test_snapshot.snap_name, "test1_snap")
        self.assertEqual(test_snapshot.resource_id, "1")
        self.assertEqual(test_snapshot.resource_name, "test1_lun")
        self.assertEqual(test_snapshot.state, "Ready")
        self.assertEqual(test_snapshot.description, '')

    def test_get_snapshots_for_lun(self):
        """Get all snapshots for a LUN
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test1_lun?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1'
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/snap/instances?filter=lun.id eq "sv_1"&fields=id,name,lun,description,creationTime,state',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': '1',
                            'state': 2,
                            'name':'test1_snap',
                            'description':'',
                            'creationTime':'2019-01-29T13:46:22.005Z',
                            'lun': {
                                'id':'sv_1'
                            }
                        }
                    }
                ]
            }
        )

        test_snapshots = self.unityapi.get_snapshots("test1_lun")
        self.assertEqual(len(test_snapshots), 1)
        test_snapshot = test_snapshots[0]
        self.assertIsInstance(test_snapshot, SnapshotInfo)
        self.assertEqual(test_snapshot.snap_name, "test1_snap")
        self.assertEqual(test_snapshot.resource_id, "1")
        self.assertEqual(test_snapshot.resource_name, "test1_lun")
        self.assertEqual(test_snapshot.state, "Ready")

    def test_get_snapshots_for_lun_id(self):
        """Get all snapshots for a LUN ID
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/snap/instances?filter=lun.id eq "sv_1"&fields=id,name,lun,description,creationTime,state',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': '1',
                            'state': 2,
                            'name':'test1_snap',
                            'description':'',
                            'creationTime':'2019-01-29T13:46:22.005Z',
                            'lun': {
                                'id':'sv_1'
                            }
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/lun/instances?filter=id IN ( "sv_1" )&fields=id,name',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'sv_1',
                            'name': 'test1_lun'
                        }
                    }
                ]
            }
        )

        test_snapshots = self.unityapi.get_snapshots(lun_id=1)
        self.assertEqual(len(test_snapshots), 1)
        test_snapshot = test_snapshots[0]
        self.assertIsInstance(test_snapshot, SnapshotInfo)
        self.assertEqual(test_snapshot.snap_name, "test1_snap")
        self.assertEqual(test_snapshot.resource_id, "1")
        self.assertEqual(test_snapshot.resource_name, "test1_lun")
        self.assertEqual(test_snapshot.state, "Ready")

    def test_get_snapshots_for_lun_non_existent(self):
        """Get all snapshots for a LUN where the LUN does not exist """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/instances/lun/name:test1_lun?fields=id',
            None,
            404,
            {
                'error': {
                    'errorCode': 131149829,
                    'httpStatusCode': 404,
                    'messages': [
                        {
                            'en-US':'The requested resource does not exist. (Error Code:0x7d13005)'
                        }
                    ]
                }
            }
        )
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.get_snapshots,
                          "test1_lun")

    def test_get_snapshot(self):
        """Get named snapshot
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/snap/name:test1_snap?fields=id,name,lun,description,creationTime,state',
            None,
            200,
            {
                'content': {
                    'id': '1',
                    'state': 2,
                    'name': 'test1_snap',
                    'description': '',
                    'creationTime': '2019-01-29T13:46:22.005Z',
                    'lun': {
                        'id': 'sv_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/lun/sv_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'name': 'test1_lun'
                }
            }
        )

        test_snapshot = self.unityapi.get_snapshot("test1_snap")
        self.assertIsInstance(test_snapshot, SnapshotInfo)
        self.assertEqual(test_snapshot.snap_name, "test1_snap")
        self.assertEqual(test_snapshot.resource_id, "1")
        self.assertEqual(test_snapshot.resource_name, "test1_lun")
        self.assertEqual(test_snapshot.state, "Ready")

    def test_get_snapshot_invalid_args(self):
        """get_snapshot with None for snap_name """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.get_snapshot,
                          snap_name=None)

    def test_get_snapshot_non_existent(self):
        """Get all snapshots for a LUN where the LUN does not exist """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/instances/snap/name:test1_snap?fields=id,name,lun,description,creationTime,state',
            None,
            404,
            {
                'error': {
                    'errorCode': 131149829,
                    'httpStatusCode': 404,
                    'messages': [
                        {
                            'en-US':'The requested resource does not exist. (Error Code:0x7d13005)'
                        }
                    ]
                }
            }
        )
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.get_snapshot,
                          "test1_snap")

    def test_create_snapshot(self):
        """Create snapshot
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test1_lun?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1'
                }
            }
        )

        self.addRequest(
            'POST',
            '/api/types/snap/instances',
            {
                'storageResource': {
                    'id': 'sv_1',
                },
                'name': 'test1_snap'
            },
            201,
            {
                'content': {
                    'id': 1
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/snap/1?fields=id,name,lun,description,creationTime,state',
            None,
            200,
            {
                'content': {
                    'id': '1',
                    'state': 2,
                    'name': 'test1_snap',
                    'description': '',
                    'creationTime': '2019-01-29T13:46:22.005Z',
                    'lun': {
                        'id': 'sv_1'
                    }
                }
            }
        )

        test_snapshot = self.unityapi.create_snapshot("test1_lun", "test1_snap")
        self.assertIsInstance(test_snapshot, SnapshotInfo)
        self.assertEqual(test_snapshot.snap_name, "test1_snap")
        self.assertEqual(test_snapshot.resource_id, "1")
        self.assertEqual(test_snapshot.resource_name, "test1_lun")
        self.assertEqual(test_snapshot.state, "Ready")
        self.assertEquals(test_snapshot.description, '')

    def test_create_snapshot_with_description(self):
        """Create snapshot with description
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test1_lun?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1'
                }
            }
        )

        self.addRequest(
            'POST',
            '/api/types/snap/instances',
            {
                'storageResource': {
                    'id': 'sv_1',
                },
                'name': 'test1_snap',
                'description': 'test1_snap description'
            },
            201,
            {
                'content': {
                    'id': 1
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/snap/1?fields=id,name,lun,description,creationTime,state',
            None,
            200,
            {
                'content': {
                    'id': '1',
                    'state': 2,
                    'name': 'test1_snap',
                    'description': 'test1_snap description',
                    'creationTime': '2019-01-29T13:46:22.005Z',
                    'lun': {
                        'id': 'sv_1'
                    }
                }
            }
        )

        test_snapshot = self.unityapi.create_snapshot("test1_lun", "test1_snap", 'test1_snap description')
        self.assertIsInstance(test_snapshot, SnapshotInfo)
        self.assertEqual(test_snapshot.snap_name, "test1_snap")
        self.assertEqual(test_snapshot.resource_id, "1")
        self.assertEqual(test_snapshot.resource_name, "test1_lun")
        self.assertEqual(test_snapshot.state, "Ready")
        self.assertEquals(test_snapshot.description, 'test1_snap description')

    def test_create_snapshot_lun_non_existent(self):
        """Create snapshot where LUN doesn't exist """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/instances/lun/name:test1_lun?fields=id',
            None,
            404,
            {
                'error': {
                    'errorCode': 131149829,
                    'httpStatusCode': 404,
                    'messages': [
                        {
                            'en-US':'The requested resource does not exist. (Error Code:0x7d13005)'
                        }
                    ]
                }
            }
        )
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.create_snapshot,
                          "test1_lun", "test1_snap")

    def test_restore_snapshot_keep_backup(self):
        """Restore snapshot keeping the backup
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'POST',
            '/api/instances/snap/name:test1_snap/action/restore',
            {
                'copyName': 'restore_test1_snap'
            },
            200,
            {
                'content': {
                    'backup': {
                        'id': 2
                    }
                }
            }
        )

        result = self.unityapi.restore_snapshot("test1_lun", "test1_snap", False)
        self.assertTrue(result, "Unexpected value for result")

    def test_restore_snapshot_delete_backup(self):
        """Restore snapshot deleting the backup
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'POST',
            '/api/instances/snap/name:test1_snap/action/restore',
            {
                'copyName': 'restore_test1_snap'
            },
            200,
            {
                'content': {
                    'backup': {
                        'id': 2
                    }
                }
            }
        )

        self.addRequest(
            'DELETE',
            '/api/instances/snap/2',
            None,
            204,
            None
        )

        result = self.unityapi.restore_snapshot("test1_lun", "test1_snap", True)
        self.assertTrue(result, "Unexpected value for result")

    def test_delete_snapshot(self):
        """Restore snapshot deleting the backup
        """
        print self.shortDescription()
        self.setUpUnity()


        self.addRequest(
            'DELETE',
            '/api/instances/snap/name:test1_snap',
            None,
            204,
            None
        )

        result = self.unityapi.delete_snapshot("test1_snap")
        self.assertTrue(result, "Unexpected value for result")


if __name__ == "__main__":
    unittest.main()
