import unittest
from sanapiinfo import StorageGroupInfo, HluAluPairInfo, HbaInitiatorInfo
from sanapiexception import SanApiEntityNotFoundException, SanApiCriticalErrorException, SanApiOperationFailedException
from sanapilib import STORAGE_PROCESSOR_A, STORAGE_PROCESSOR_B
from unitytest import TestUnity

class TestUnitySG(TestUnity):
    """
    Test class contains tests for storage group related methods
    """

    def test_get_storage_group(self):
        """Get the StorageGroupInfo for the host identified by sgname
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'content': {
                    'id':'Host_1',
                    'name': 'test1_sg',
                    'fcHostInitiators': [
                        {
                            'id': 'HostInitiator_1'
                        },
                        {
                            'id':'HostInitiator_2'
                        }
                    ],
                    'hostLUNs': [
                        {
                            'id':'Host_1_sv_1_prod'
                        },
                    ]
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=id IN ( "HostInitiator_1","HostInitiator_2" )&fields=id,initiatorId,paths,isIgnored',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'isIgnored': False,
                            'paths': [
                                {
                                    'id': 'HostInitiator_1_00:00:00:01_0'
                                },
                                {
                                    'id': 'HostInitiator_1_00:00:00:02_0'
                                }
                            ]
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10',
                            'isIgnored': False,
                            'paths': [
                                {
                                    'id': 'HostInitiator_2_00:00:00:01_0'
                                },
                                {
                                    'id': 'HostInitiator_2_00:00:00:02_0'
                                }
                            ]
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiatorPath/instances?filter=id IN ( "HostInitiator_1_00:00:00:01_0","HostInitiator_1_00:00:00:02_0","HostInitiator_2_00:00:00:01_0","HostInitiator_2_00:00:00:02_0" )&fields=id,fcPort',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id':'HostInitiator_1_00:00:00:01_0',
                            'fcPort': {
                                'id': 'spa_iom_0_fc0'
                            }
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_1_00:00:00:02_0',
                            'fcPort': {
                                'id': 'spb_iom_0_fc0'
                            }
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2_00:00:00:01_0',
                            'fcPort': {
                                'id': 'spa_fc4'
                            }
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2_00:00:00:02_0',
                            'fcPort': {
                                'id': 'spb_fc4'
                            }
                        }
                    }
                ]
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

        test_sg = self.unityapi.get_storage_group('test1_sg')
        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.name, "test1_sg", "Unexpected value for name")
        self.assertEqual(test_sg.hlualu_list, [HluAluPairInfo('0', '1')], "Unexpected value in hlualu_list")

        expected_hbasp_list = [
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_B, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10", STORAGE_PROCESSOR_A, 4),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10", STORAGE_PROCESSOR_B, 4)
        ]
        self.assertEqual(len(test_sg.hbasp_list), len(expected_hbasp_list), "Unexpected number of entries in hbasp_list")
        if len(test_sg.hbasp_list) == len(expected_hbasp_list):
            for index, expected_hbasp in enumerate(expected_hbasp_list, 0):
                test_hbasp = test_sg.hbasp_list[index]
                self.assertEqual(expected_hbasp, test_hbasp, "Unexpected value hbasp %s, expected %s actutal %s" % (index, expected_hbasp, test_hbasp))

    def test_get_storage_group_invalid_sg(self):
        """get_storage_group with invalid_name """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.get_storage_group,
                          sg_name=None)

    def test_get_storage_group_non_existent_sg(self):
        """create_storage_group with invalid_name
        """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,name,fcHostInitiators,hostLUNs',
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
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.get_storage_group,
                          sg_name="test1_sg")


    def test_get_storage_groups(self):
        """Get the StorageGroupInfo for all hosts
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/host/instances?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'Host_1',
                            'name': 'test1_sg',
                            'fcHostInitiators': [
                                {
                                    'id': 'HostInitiator_1'
                                },
                                {
                                    'id': 'HostInitiator_2'
                                }
                            ],
                            'hostLUNs': [
                                {
                                    'id': 'Host_1_sv_1_prod'
                                },
                            ]
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=id IN ( "HostInitiator_1","HostInitiator_2" )&fields=id,initiatorId,paths,isIgnored',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'isIgnored': False,
                            'paths': [
                                {
                                    'id': 'HostInitiator_1_00:00:00:01_0'
                                },
                                {
                                    'id': 'HostInitiator_1_00:00:00:02_0'
                                }
                            ]
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10',
                            'isIgnored': False,
                            'paths': [
                                {
                                    'id': 'HostInitiator_2_00:00:00:01_0'
                                },
                                {
                                    'id': 'HostInitiator_2_00:00:00:02_0'
                                }
                            ]
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiatorPath/instances?filter=id IN ( "HostInitiator_1_00:00:00:01_0","HostInitiator_1_00:00:00:02_0","HostInitiator_2_00:00:00:01_0","HostInitiator_2_00:00:00:02_0" )&fields=id,fcPort',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id':'HostInitiator_1_00:00:00:01_0',
                            'fcPort': {
                                'id': 'spa_iom_0_fc0'
                            }
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_1_00:00:00:02_0',
                            'fcPort': {
                                'id': 'spb_iom_0_fc0'
                            }
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2_00:00:00:01_0',
                            'fcPort': {
                                'id': 'spa_fc4'
                            }
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2_00:00:00:02_0',
                            'fcPort': {
                                'id': 'spb_fc4'
                            }
                        }
                    }
                ]
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

        test_sg_list = self.unityapi.get_storage_groups()
        self.assertEqual(len(test_sg_list), 1, "Unexpected number of StorageGroupInfo returned")

        test_sg = test_sg_list[0]
        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.name, "test1_sg", "Unexpected value for name")
        self.assertEqual(test_sg.hlualu_list, [HluAluPairInfo('0', '1')], "Unexpected value in hlualu_list")

        expected_hbasp_list = [
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_B, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10", STORAGE_PROCESSOR_A, 4),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10", STORAGE_PROCESSOR_B, 4)
        ]
        self.assertEqual(len(test_sg.hbasp_list), len(expected_hbasp_list), "Unexpected number of entries in hbasp_list")
        if len(test_sg.hbasp_list) == len(expected_hbasp_list):
            for index, expected_hbasp in enumerate(expected_hbasp_list, 0):
                test_hbasp = test_sg.hbasp_list[index]
                self.assertEqual(expected_hbasp, test_hbasp, "Unexpected value hbasp %s, expected %s actutal %s" % (index, expected_hbasp, test_hbasp))

    def test_create_storage_group(self):
        """Create a host with a name matching the storage group name
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'POST',
            '/api/types/host/instances',
            {
                'type': 1,
                'name': 'test1_sg'
            },
            201,
            {
                'content': {
                    'id': 'Host_1'
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1',
                    'name': 'test1_sg'
                }
            }
        )

        test_sg = self.unityapi.create_storage_group('test1_sg')
        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.name, "test1_sg", "Unexpected value for name")
        self.assertEqual(test_sg.hlualu_list, None)
        self.assertEqual(test_sg.hbasp_list, None)

    def test_create_storage_group_invalid_name(self):
        """create_storage_group with invalid_name
        """
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiOperationFailedException, self.unityapi.create_storage_group,
                          sg_name=None)

    def test_add_lun_to_storage_group_hlu(self):
        """Add LUN to empty storage group
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1'
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
                    },
                    'hostAccess': [
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
        )

        self.addRequest(
            'POST',
            '/api/instances/storageResource/sv_1/action/modifyLun',
            {
                'lunParameters': {
                    'hostAccess': [
                        {
                            'host': {
                                 'id': 'Host_2'
                             },
                            'accessMask': 1
                        },
                        {
                            'host': {
                                'id': 'Host_1'
                            },
                            'accessMask': 1
                        }
                    ]
                }
            },
            204,
            None
        )

        self.addRequest(
            'GET',
            '/api/types/hostLUN/instances?filter=host.id eq "Host_1" and lun.id eq "sv_1"&fields=id,lun,hlu,type,host',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'Host_1_sv_1_prod',
                            'type': 1,
                            'hlu': 1,
                            'host': {
                                'id': 'Host_1'
                            },
                            'lun': {
                                'id':'sv_1'
                            }
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'POST',
            '/api/instances/host/Host_1/action/modifyHostLUNs',
            {
                'hostLunModifyList': [
                    {
                        'hlu': '0',
                        'hostLUN': {
                            'id': 'Host_1_sv_1_prod'
                        }
                    }
                ]
            },
            204,
            None
        )

        # Requests to get the StorageGroupInfo
        self.addRequest(
            'GET',
            '/api/instances/host/Host_1?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'content': {
                    'id':'Host_1',
                    'name':'tesg1_sg',
                    'fcHostInitiators': [
                        {
                            'id': 'HostInitiator_1'
                        },
                        {
                            'id':'HostInitiator_2'
                        }
                    ],
                    'hostLUNs': [
                        {
                            'id':'Host_1_sv_1_prod'
                        },
                    ]
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=id IN ( "HostInitiator_1","HostInitiator_2" )&fields=id,initiatorId,paths,isIgnored',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'isIgnored': False,
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10',
                            'isIgnored': False,
                        }
                    }
                ]
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
                                'id':'sv_1'
                            }
                        }
                    }
                ]
            }
        )

        test_sg = self.unityapi.add_lun_to_storage_group('test1_sg', "0", "1")

        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.hlualu_list, [HluAluPairInfo('0', '1')], "Unexpected value in hlualu_list")

    def test_add_lun_to_storage_group_invalid_sg(self):
        """ add_lun_to_storage_group_with invalid sg name"""
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.add_lun_to_storage_group,
                          sg_name=None, hlu="0", alu="1")

    def test_add_lun_to_storage_group_non_existent_sg(self):
        """create_storage_group with invalid_name
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
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

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.add_lun_to_storage_group,
                          sg_name="test1_sg", hlu="0", alu="1")

    def test_add_lun_to_storage_group_invalid_alu(self):
        """ add_lun_to_storage_group_with invalid alu"""
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.add_lun_to_storage_group,
                          sg_name="test1_sg", hlu="0", alu="invalid")

    def test_add_lun_to_storage_group_non_existent_lun(self):
        """create_storage_group with invalid_name
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1'
                }
            }
        )

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

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.add_lun_to_storage_group,
                          sg_name="test1_sg", hlu="0", alu="1")

    def test_remove_luns_from_storage_group_simple_hlu(self):
        """Remove only LUN from SG where the hlu is a simple number"""
        print self.shortDescription()
        self.setUpUnity()

        self.__addRequestsForRemove()

        test_sg = self.unityapi.remove_luns_from_storage_group('test1_sg', "0")

        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.hlualu_list, None, "Unexpected value in hlualu_list, expecting none")

    def test_remove_luns_from_storage_group_list_hlu_str(self):
        """Remove only LUN from SG where the hlu is a list of simple numbers"""
        print self.shortDescription()
        self.setUpUnity()

        self.__addRequestsForRemove()

        test_sg = self.unityapi.remove_luns_from_storage_group('test1_sg', ["0"])

        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.hlualu_list, None, "Unexpected value in hlualu_list, expecting none")

    def test_remove_luns_from_storage_group_list_hlupair(self):
        """Remove only LUN from SG where the hlu is a list of simple numbers"""
        print self.shortDescription()
        self.setUpUnity()

        self.__addRequestsForRemove()

        test_sg = self.unityapi.remove_luns_from_storage_group('test1_sg', [HluAluPairInfo('0', '1')])

        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.hlualu_list, None, "Unexpected value in hlualu_list, expecting none")

    def test_remove_luns_from_storage_group_list_invalid(self):
        """Remove only LUN from SG where the hlu is a list of simple numbers"""
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiOperationFailedException, self.unityapi.remove_luns_from_storage_group,
                          sg_name="test1_sg", hlus=[None])

    def test_remove_luns_from_storage_group_invalid_sg(self):
        """remove_luns_from_storage_group with invalid storage group"""
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiOperationFailedException, self.unityapi.remove_luns_from_storage_group,
                          sg_name=None, hlus="0")

    def test_remove_luns_from_storage_group_non_existent_sg(self):
        """remove_luns_from_storage_group with non existent storage group"""
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
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

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.remove_luns_from_storage_group,
                          sg_name="test1_sg", hlus="0")

    def test_remove_luns_from_storage_group_non_existent_hlu(self):
        """remove_luns_from_storage_group where host has no matching hlu"""
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
            None,
            200,
            {
                'content': {
                    'id':'Host_1',
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostLUN/instances?filter=host.id eq "Host_1" and hlu IN ( 0 )&fields=id,lun,hlu,type,host',
            None,
            200,
            {
                'entries': [
                ]
            }
        )

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.remove_luns_from_storage_group,
                          sg_name="test1_sg", hlus="0")


    def test_remove_luns_from_storage_group_invalid_hlus_None(self):
        """remove_luns_from_storage_group with None for hlus"""
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.remove_luns_from_storage_group,
                          sg_name="test1_sg", hlus=None)

    def test_remove_luns_from_storage_group_invalid_hlus_hlupair(self):
        """remove_luns_from_storage_group with None for hlus"""
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.remove_luns_from_storage_group,
                          sg_name="test1_sg", hlus=HluAluPairInfo('0', '1'))

    def test_storage_group_exists_true(self):
        """Check for non-existant sg
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1',
                }
            }
        )

        result = self.unityapi.storage_group_exists("test1_sg")
        self.assertTrue(result, "Unexpected value for result")

    def test_storage_group_exists_false(self):
        """Check for non-existant sg
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
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

        result = self.unityapi.storage_group_exists("test1_sg")
        self.assertFalse(result, "Unexpected value for result")

    def test_delete_storage_group(self):
        """Delete storage groyp
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'DELETE',
            '/api/instances/host/name:test1_sg',
            None,
            204,
            None
        )

        result = self.unityapi.delete_storage_group("test1_sg")
        self.assertTrue(result, "Unexpected value for result")

    def test_delete_storage_group_invalid_sg(self):
        """delete_storage_group with invalid_name """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiOperationFailedException, self.unityapi.delete_storage_group,
                          sg_name=None)

    def test_disconnect_host(self):
        """Disconnect host from storage group
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'content': {
                    'id':'Host_1',
                    'name': 'test1_sg',
                    'fcHostInitiators': [
                        {
                            'id': 'HostInitiator_1'
                        },
                        {
                            'id':'HostInitiator_2'
                        }
                    ],
                    'hostLUNs': [
                        {
                            'id':'Host_1_sv_1_prod'
                        },
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
            'POST',
            '/api/instances/storageResource/sv_1/action/modifyLun',
            {
                'lunParameters': {
                    'hostAccess': [
                        {
                            'host': {
                                 'id': 'Host_2'
                             },
                            'accessMask': 1
                        }
                    ]
                }
            },

            204,
            None
        )

        result = self.unityapi.disconnect_host("test1_sg", "test1_host")
        self.assertTrue(result, "Unexpected value for result")

    def test_disconnect_host_invalid_sg(self):
        """Disconnect host from storage group with invalid storage group"""
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiOperationFailedException, self.unityapi.disconnect_host,
                          sg_name=None, host=None)

    def test_disconnect_host_non_existent_sg(self):
        """Disconnect host from storage group with non-existent storage group"""
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,name,fcHostInitiators,hostLUNs',
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

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.disconnect_host,
                          sg_name="test1_sg", host=None)

    def __addRequestsForRemove(self):
        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1'
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostLUN/instances?filter=host.id eq "Host_1" and hlu IN ( 0 )&fields=id,lun,hlu,type,host',
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
                            'name': 'test_lun',
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
            'POST',
            '/api/instances/storageResource/sv_1/action/modifyLun',
            {
                'lunParameters': {
                    'hostAccess': [
                        {
                            'host': {
                                 'id': 'Host_2'
                             },
                            'accessMask': 1
                        }
                    ]
                }
            },
            204,
            None
        )

        # Requests to get the StorageGroupInfo
        self.addRequest(
            'GET',
            '/api/instances/host/Host_1?fields=id,name,fcHostInitiators,hostLUNs',
            None,
            200,
            {
                'content': {
                    'id':'Host_1',
                    'name':'tesg1_sg',
                    'fcHostInitiators': [
                        {
                            'id': 'HostInitiator_1'
                        },
                        {
                            'id':'HostInitiator_2'
                        }
                    ],
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=id IN ( "HostInitiator_1","HostInitiator_2" )&fields=id,initiatorId,paths,isIgnored',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'isIgnored': False,
                        }
                    },
                    {
                        'content': {
                            'id': 'HostInitiator_2',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10',
                            'isIgnored': False,
                        }
                    }
                ]
            }
        )


if __name__ == "__main__":
    unittest.main()
