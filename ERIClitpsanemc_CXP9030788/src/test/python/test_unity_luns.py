
import unittest

from sanapiinfo import LunInfo
import sanapilib
from sanapiexception import SanApiOperationFailedException, \
                     SanApiEntityNotFoundException, SanApiCriticalErrorException

from unitytest import TestUnity


class TestUnityLuns(TestUnity):
    """
    Test class contains methods to get/create/delete LUNs
    """

    def test_get_lun_by_id(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/sv_1?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test_lun',
                    'sizeTotal': 1048576,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test_pool'
                }
            }
        )

        test_lun = self.unityapi.get_lun("1", None)

        self.assertIsInstance(test_lun, LunInfo)
        self.assertEqual(test_lun.name, "test_lun", "Unexpected value for lun name")
        self.assertEqual(test_lun.container, "test_pool", "Unexpected value for lun pool")

    def test_get_lun_by_name(self):
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test_lun',
                    'sizeTotal': 1048576,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test_pool'
                }
            }
        )

        test_lun = self.unityapi.get_lun(None, "test_lun")

        self.assertIsInstance(test_lun, LunInfo)
        self.assertEqual(test_lun.name, "test_lun", "Unexpected value for lun name")
        self.assertEqual(test_lun.container, "test_pool", "Unexpected value for lun pool")

    def test_get_lun_no_args(self):
        ''' get_lun without id or name '''
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.get_lun, None, None)

    def test_get_lun_not_exists(self):
        ''' get_lun that doesn't exist '''
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/sv_1?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
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
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.get_lun, "1", None)

    def test_get_luns(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/lun/instances?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'sv_1',
                            'currentNode': 0,
                            'name': 'test1_lun',
                            'sizeTotal': 1048576,
                            'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'pool': {
                                'id': 'pool_1'
                            }
                        }
                    },
                    {
                        'content': {
                            'id': 'sv_2',
                            'currentNode': 1,
                            'name': 'test2_lun',
                            'sizeTotal': 1048576,
                            'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:FF',
                            'pool': {
                                'id': 'pool_2'
                            }
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test1_pool'
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_2?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_2',
                    'name': 'test2_pool'
                }
            }
        )

        test_luns = self.unityapi.get_luns()
        index = 1
        for test_lun in test_luns:
            lun_name = "test%s_lun" % index
            lun_id = str(index)
            lun_pool = "test%s_pool" % index
            self.assertIsInstance(test_lun, LunInfo)
            self.assertEqual(test_lun.name, lun_name, "Unexpected value for lun name")
            self.assertEqual(test_lun.container, lun_pool, "Unexpected value for lun pool")
            self.assertEqual(test_lun.id, lun_id, "Unexpected value for lun id")
            index = index + 1

    def test_get_luns_for_sg(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test_sg?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1',
                    'name': 'test_sg',
                    'fcHostInitiators': [
                        {
                            'id': 'HostInitiator_1'
                        }
                    ],
                    'hostLUNs': [
                        {
                            'id':'Host_1_sv_1_prod'
                        }
                    ]
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostLUN/instances?filter=id IN ( "Host_1_sv_1_prod" )&fields=id,lun,hlu,type,host',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'Host_1_sv_1_prod',
                            'type': 1,
                            'hlu': 0,
                            'host': {
                                'id': 'Host_1'
                            },
                            'lun': {
                                'id': 'sv_1'
                            }
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/lun/instances?filter=id IN ( "sv_1" )&fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'sv_1',
                            'currentNode': 0,
                            'name': 'test1_lun',
                            'sizeTotal': 1048576,
                            'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'pool': {
                                'id': 'pool_1'
                            },
                            'hostAccess': [
                                {
                                    'accessMask': 1,
                                    'productionAccess': 1,
                                    'snapshotAccess': 0,
                                    'hlu': 0,
                                    'host': {
                                        'id': 'Host_1'
                                    }
                                },
                                {
                                    'accessMask': 1,
                                    'productionAccess': 1,
                                    'snapshotAccess': 0,
                                    'hlu': 0,
                                    'host': {
                                        'id': 'Host_2'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        )


        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test1_pool'
                }
            }
        )

        test_luns = self.unityapi.get_luns(None, None, "test_sg")

        self.assertTrue(len(test_luns) == 1, "Unexpected number of LunInfos returned by get_luns, expected 1, got %s" % len(test_luns))
        self.assertIsInstance(test_luns[0], LunInfo)
        self.assertEqual(test_luns[0].name, "test1_lun", "Unexpected value for lun name")
        self.assertEqual(test_luns[0].container, "test1_pool", "Unexpected value for lun pool")

    def test_get_luns_for_non_existent_sg(self):
        ''' get_luns without id or name '''
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test_sg?fields=id,name,fcHostInitiators,hostLUNs',
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

        test_luns = self.unityapi.get_luns(None, None, "test_sg")
        self.assertTrue(len(test_luns) == 0, "Unexpected number of LunInfos returned by get_luns")

    def test_get_luns_for_sg_empty(self):
        ''' get_luns without id or name '''
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test_sg?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1',
                    'name': 'test_sg',
                    'fcHostInitiators': [
                        {
                            'id': 'HostInitiator_1'
                        }
                    ]
                }
            }
        )

        test_luns = self.unityapi.get_luns(None, None, "test_sg")
        self.assertTrue(len(test_luns) == 0, "Unexpected number of LunInfos returned by get_luns")

    def test_get_luns_for_container(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:test1_pool?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test1_pool'
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/lun/instances?filter=pool.id eq "pool_1"&fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'sv_1',
                            'currentNode': 0,
                            'name': 'test1_lun',
                            'sizeTotal': 1048576,
                            'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'pool': {
                                'id': 'pool_1'
                            },
                            'hostAccess': [
                                {
                                    'accessMask': 1,
                                    'productionAccess': 1,
                                    'snapshotAccess': 0,
                                    'hlu': 0,
                                    'host': {
                                        'id': 'Host_1'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        )

        test_luns = self.unityapi.get_luns(sanapilib.CONTAINER_STORAGE_POOL , "test1_pool")

        self.assertTrue(len(test_luns) == 1, "Unexpected number of LunInfos returned by get_luns, expected 1, got %s" % len(test_luns))
        self.assertIsInstance(test_luns[0], LunInfo)
        self.assertEqual(test_luns[0].name, "test1_lun", "Unexpected value for lun name")
        self.assertEqual(test_luns[0].container, "test1_pool", "Unexpected value for lun pool")

    def test_get_luns_for_non_existant_container(self):
        ''' get_luns for non-existant pool  '''
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:test1_pool?fields=id',
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

        test_luns = self.unityapi.get_luns(sanapilib.CONTAINER_STORAGE_POOL , "test1_pool")
        self.assertTrue(len(test_luns) == 0, "Unexpected number of LunInfos returned by get_luns")
 
    def test_get_luns_invalid_args(self):
        ''' get_luns with invalid args  '''
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.get_luns,
                          sanapilib.CONTAINER_STORAGE_POOL , "test1_pool", "test1_sg")

    def test_create_lun(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:test_pool?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1'
                }
            }
        )

        self.addRequest(
            'POST',
            '/api/types/storageResource/action/createLun',
            {
                'lunParameters': {
                    'isDataReductionEnabled': True,
                    'isThinEnabled': True,
                    'pool': {
                        'id': 'pool_1'
                    },
                    'size': 1048576,
                    'defaultNode': 0
                },
                'name': 'test_lun',
            },
            200,
            {
                'content': {
                    'storageResource': {
                        'id': 'sv_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/lun/sv_1?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test_lun',
                    'sizeTotal': 1048576,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test_pool'
                }
            }
        )

        # Assigns the built navisec command to "test_sg"
        test_lun = self.unityapi.create_lun("test_lun",
                                           1,
                                           sanapilib.CONTAINER_STORAGE_POOL,
                                           "test_pool")

        self.assertIsInstance(test_lun, LunInfo)
        self.assertEqual(test_lun.name, "test_lun", "Unexpected value for lun name")
        self.assertEqual(test_lun.container, "test_pool", "Unexpected value for lun pool")

    def test_create_lun_invalid_container_type(self):
        ''' create_lun specifying RAID Group container  '''
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiOperationFailedException, self.unityapi.create_lun,
                          "test_lun", "1", sanapilib.CONTAINER_RAID_GROUP, "test1_rg", raid_type="5")

    def test_create_lun_non_existent_container(self):
        ''' create_lun specifying non-existent pool'''
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/pool/name:test1_pool?fields=id',
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

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.create_lun,
                          "test_lun", "1", sanapilib.CONTAINER_STORAGE_POOL, "test1_pool")

    def test_create_lun_invalid_lun_id(self):
        ''' create_lun specifying value for lun_id '''
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiOperationFailedException, self.unityapi.create_lun,
                          "test_lun", "1", sanapilib.CONTAINER_STORAGE_POOL, "test1_pool",
                          lun_id="1")

    def test_delete_lun_by_name(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test_lun?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1'
                }
            }
        )
        self.addRequest(
            'DELETE',
            '/api/instances/storageResource/sv_1',
            None,
            204,
            None
        )

        self.unityapi.delete_lun("test_lun")

    def test_delete_lun_by_id(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'DELETE',
            '/api/instances/storageResource/sv_1',
            None,
            204,
            None
        )

        self.unityapi.delete_lun(None, "1")

    def test_delete_lun_no_args(self):
        ''' delete_lun without id or name '''
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.delete_lun, None, None)

    def test_delete_lun_both_args(self):
        ''' delete_lun without id or name '''
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.delete_lun, "lun_name", "1")

    def test_expand(self):
        print self.shortDescription()

        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test_lun',
                    'sizeTotal': 1048576,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'POST',
            '/api/instances/storageResource/sv_1/action/modifyLun',
            {
                'lunParameters': {
                    'size': 2097152
                }
            },
            204,
            None
        )

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test_lun',
                    'sizeTotal': 2097152,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test_pool'
                }
            }
        )

        test_lun = self.unityapi.expand_pool_lun("test_lun", "2m")

        self.assertIsInstance(test_lun, LunInfo)
        self.assertEqual(test_lun.name, "test_lun", "Unexpected value for lun name")
        self.assertEqual(test_lun.size, "2", "Unexpected value for lun size")

    def test_expand_same_size(self):
        """ expand where LUN is already the requested size """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test_lun',
                    'sizeTotal': 1048576,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test_lun',
                    'sizeTotal': 1048576,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test_pool'
                }
            }
        )
        test_lun = self.unityapi.expand_pool_lun("test_lun", "1m")

        self.assertIsInstance(test_lun, LunInfo)
        self.assertEqual(test_lun.name, "test_lun", "Unexpected value for lun name")
        self.assertEqual(test_lun.size, "1", "Unexpected value for lun size")

    def test_expand_non_existent(self):
        ''' create_lun specifying RAID Group container  '''
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
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

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.expand_pool_lun, "test_lun", "2m")

    def test_lun_exists_positive(self):
        """lun_exists where it does exist
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test1_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
            None,
            200,
            {
                'content': {
                    'id': 'sv_1',
                    'currentNode': 0,
                    'name': 'test1_lun',
                    'sizeTotal': 1048576,
                    'wwn': '00:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                    'pool': {
                        'id': 'pool_1'
                    }
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/pool/pool_1?fields=name',
            None,
            200,
            {
                'content': {
                    'id': 'pool_1',
                    'name': 'test_pool'
                }
            }
        )

        result = self.unityapi.lun_exists("test1_lun")
        self.assertTrue(result, "Unexpected value for result")

    def test_lun_exists_negative(self):
        """lun_exists where it does not exist
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/lun/name:test1_lun?fields=id,name,wwn,sizeTotal,currentNode,pool,hostAccess',
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

        result = self.unityapi.lun_exists("test1_lun")
        self.assertFalse(result, "Unexpected value for result")


if __name__ == "__main__":
    unittest.main()
