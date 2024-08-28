
import unittest

from sanapiinfo import StoragePoolInfo
from sanapiexception import SanApiOperationFailedException, \
                     SanApiEntityNotFoundException, SanApiCriticalErrorException

from unitytest import TestUnity


class TestUnityPool(TestUnity):
    """
    Test class contains methods to pool methods
    """

    def test_get_storage_pool_by_name(self):
        """Get StoragePool by name """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:test1_pool?fields=id,name,raidType,sizeTotal,sizeFree,sizeSubscribed,tiers',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test1_pool',
                    'raidType': 1,
                    'tiers': [
                        {
                            "diskCount": 7,
                        }
                    ],
                    'sizeTotal': 2147483648,
                    'sizeFree': 1073741824,
                    'sizeSubscribed': 1610612736
                }
            }
        )

        test_pool = self.unityapi.get_storage_pool(sp_name="test1_pool")
        self.assertIsInstance(test_pool, StoragePoolInfo)
        self.assertEqual(test_pool.name, "test1_pool")
        self.assertEqual(test_pool.id, "1")
        self.assertEqual(test_pool.raid, "5")
        self.assertEqual(test_pool.size, "2048")
        self.assertEqual(test_pool.available, "1024")
        self.assertEquals(test_pool.subscribed, '75.0')
        self.assertEquals(test_pool.full, '50.0')
        self.assertEqual(test_pool.disks, "7")

    def test_get_storage_pool_by_id(self):
        """Get StoragePool by id """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=id,name,raidType,sizeTotal,sizeFree,sizeSubscribed,tiers',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test1_pool',
                    'raidType': 1,
                    'tiers': [
                        {
                            "diskCount": 7,
                        }
                    ],
                    'sizeTotal': 2147483648,
                    'sizeFree': 1073741824,
                    'sizeSubscribed': 1610612736
                }
            }
        )

        test_pool = self.unityapi.get_storage_pool(sp_id="1")
        self.assertIsInstance(test_pool, StoragePoolInfo)
        self.assertEqual(test_pool.name, "test1_pool")
        self.assertEqual(test_pool.id, "1")
        self.assertEqual(test_pool.raid, "5")
        self.assertEqual(test_pool.size, "2048")
        self.assertEqual(test_pool.available, "1024")
        self.assertEquals(test_pool.subscribed, '75.0')
        self.assertEquals(test_pool.full, '50.0')
        self.assertEqual(test_pool.disks, "7")

    def test_get_storage_pool_invalid_args(self):
        """get_storage_group without name or id """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.get_storage_pool,
                          sp_name=None , sp_id=None)

    def test_get_storage_pool_non_existent(self):
        """get_storage_group for non existent pool """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/instances/pool/name:test1_pool?fields=id,name,raidType,sizeTotal,sizeFree,sizeSubscribed,tiers',
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
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.get_storage_pool,
                          sp_name="test1_pool")

    def test_check_storage_pool_exists_true(self):
        """Check if storage pool with name test1_pool exists"""
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:test1_pool?fields=id,name,raidType,sizeTotal,sizeFree,sizeSubscribed,tiers',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test1_pool',
                    'raidType': 1,
                    'tiers': [
                        {
                            "diskCount": 7,
                        }
                    ],
                    'sizeTotal': 2147483648,
                    'sizeFree': 1073741824,
                    'sizeSubscribed': 1610612736
                }
            }
        )

        test_pool = self.unityapi.check_storage_pool_exists("test1_pool")
        self.assertTrue(test_pool, "Unexpected value for test_pool")

    def test_check_storage_pool_exists_false(self):
        """Check if storage pool with name test1_pool exists"""
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:test1_pool?fields=id,name,raidType,sizeTotal,sizeFree,sizeSubscribed,tiers',
            None,
            404,
            {
                'error': {
                    'errorCode': 131149829,
                    'httpStatusCode': 404,
                    'messages': [
                        {
                            'en-US': 'The requested resource does not exist. (Error Code:0x7d13005)'
                        }
                    ]
                }
            }
        )

        test_pool = self.unityapi.check_storage_pool_exists("test1_pool")
        self.assertFalse(test_pool, "Unexpected value for test_pool")

    def test_delete_storage_pool(self):
        """Delete storage pool
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:pool_1?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                }
            }
        )

        self.addRequest(
            'DELETE',
            '/api/instances/pool/pool_1',
            None,
            204,
            None
        )

        result = self.unityapi.delete_storage_pool("pool_1")
        self.assertTrue(result, "Unexpected value for result")

    def test_delete_storage_pool_no_args(self):
        ''' delete_storage_pool without name '''
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.delete_storage_pool, None)

    def test_create_pool_with_disks(self):
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/diskGroup/instances?fields=id,totalDisks,diskTechnology',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'dg_40',
                            'totalDisks': 15,
                            'diskTechnology': 8
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'POST',
            '/api/types/pool/instances',
            {
                'name': 'pool_1',
                'description': "SAN storage pool for ENM",
                'addRaidGroupParameters': [{
                    "dskGroup": {"id": 'dg_40'},
                    "numDisks": 15,
                    "raidType": 1,
                    "stripeWidth": 13
                }],
            },
            201,
            {
                'content': {
                    'id': 'pool_1'
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/name:pool_1?fields=id,name,raidType,sizeTotal,sizeFree,sizeSubscribed,tiers',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'pool_1',
                    'raidType': 1,
                    'tiers': [
                        {
                            "diskCount": 7,
                        }
                    ],
                    'sizeTotal': 2147483648,
                    'sizeFree': 1073741824,
                    'sizeSubscribed': 1610612736
                }
            }
        )

        test_sp = self.unityapi.create_pool_with_disks('pool_1', 15, 5)
        self.assertIsInstance(test_sp, StoragePoolInfo)
        self.assertEqual(test_sp.name, "pool_1", "Unexpected value for name")


if __name__ == "__main__":
    unittest.main()
