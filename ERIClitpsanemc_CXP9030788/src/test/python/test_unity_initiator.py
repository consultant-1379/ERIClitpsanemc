import unittest
from sanapiinfo import StorageGroupInfo, HbaInitiatorInfo
from sanapilib import STORAGE_PROCESSOR_A, STORAGE_PROCESSOR_B
from unitytest import TestUnity
from sanapiexception import SanApiEntityNotFoundException, SanApiCriticalErrorException


class TestUnityInitiator(TestUnity):
    """
    Test class contains tests for initiator related methods
    """

    def test_get_hba_port_info_all(self):
        """Get all HBA visible on array
        """
        print self.shortDescription()
        self.setUpUnity()


        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?fields=id,initiatorId,paths,isIgnored',
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
            '/api/types/hostInitiatorPath/instances?fields=id,fcPort',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1_00:00:00:01_0',
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

        expected_hbasp_list = [
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_B, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10", STORAGE_PROCESSOR_A, 4),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:10", STORAGE_PROCESSOR_B, 4)
        ]

        test_hbasp_list = self.unityapi.get_hba_port_info()
        self.assertEqual(len(test_hbasp_list), len(expected_hbasp_list), "Unexpected number of entries in hbasp_list")
        if len(test_hbasp_list) == len(expected_hbasp_list):
            for index, expected_hbasp in enumerate(expected_hbasp_list, 0):
                test_hbasp = test_hbasp_list[index]
                self.assertEqual(expected_hbasp, test_hbasp,
                                 "Unexpected value hbasp %s, expected %s actual %s" % (index, expected_hbasp, test_hbasp))

    def test_get_hba_port_info_www(self):
        """Get HBA with specified wwn
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=initiatorId eq "FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F"&fields=id,initiatorId,paths,isIgnored',
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
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiatorPath/instances?filter=id IN ( "HostInitiator_1_00:00:00:01_0","HostInitiator_1_00:00:00:02_0" )&fields=id,fcPort',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1_00:00:00:01_0',
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
                    }
                ]
            }
        )

        expected_hbasp_list = [
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_B, 0),
        ]

        test_hbasp_list = self.unityapi.get_hba_port_info("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F")
        self.assertEqual(len(test_hbasp_list), len(expected_hbasp_list), "Unexpected number of entries in hbasp_list")
        if len(test_hbasp_list) == len(expected_hbasp_list):
            for index, expected_hbasp in enumerate(expected_hbasp_list, 0):
                test_hbasp = test_hbasp_list[index]
                self.assertEqual(expected_hbasp, test_hbasp,
                                 "Unexpected value hbasp %s, expected %s actutal %s" % (
                                 index, expected_hbasp, test_hbasp))

    def test_get_hba_port_info_wwn_sp_port(self):
        """Get HBA with for given SP/port
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=initiatorId eq "FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F"&fields=id,initiatorId,paths,isIgnored',
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
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiatorPath/instances?filter=id IN ( "HostInitiator_1_00:00:00:01_0","HostInitiator_1_00:00:00:02_0" )&fields=id,fcPort',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1_00:00:00:01_0',
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
                    }
                ]
            }
        )

        expected_hbasp_list = [
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A, 0)
        ]

        test_hbasp_list = self.unityapi.get_hba_port_info(wwn="FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F",
                                                          storage_processor=STORAGE_PROCESSOR_A, sp_port="0")
        self.assertEqual(len(test_hbasp_list), len(expected_hbasp_list), "Unexpected number of entries in hbasp_list")
        if len(test_hbasp_list) == len(expected_hbasp_list):
            for index, expected_hbasp in enumerate(expected_hbasp_list, 0):
                test_hbasp = test_hbasp_list[index]
                self.assertEqual(expected_hbasp, test_hbasp,
                                 "Unexpected value hbasp %s, expected %s actutal %s" % (index, expected_hbasp, test_hbasp))

    def test_get_hba_port_info_wwn_invalid(self):
        """Get HBA with invalid wwn """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.get_hba_port_info, wwn="invalid")

    def test_get_hba_port_info_sp_invalid(self):
        """Get HBA with invalid sp """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.get_hba_port_info, storage_processor="c")

    def test_get_hba_port_info_sp_port_invalid(self):
        """Get HBA with invalid sp port """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.get_hba_port_info, sp_port="c")

    def test_get_hba_port_info_both_wwn_host(self):
        """Get HBA with both wwn and host """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.get_hba_port_info,
                          wwn="FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F",
                          host="test1_host"
                          )

    def test_get_hba_port_info_sp_wthout_www_host(self):
        """Get HBA with both wwn and host """
        print self.shortDescription()
        self.setUpUnity()
        self.assertRaises(SanApiCriticalErrorException, self.unityapi.get_hba_port_info,
                          storage_processor="a"
                          )

    def test_create_host_initiators(self):
        """Create initiators
        """
        print self.shortDescription()
        self.setUpUnity()

        # create_host_initiator calls
        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,description',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1'
                }
            }
        )

        self.addRequest(
            'POST',
            '/api/instances/host/Host_1/action/modify',
            {
                'description': 'test1_host'
            },
            204,
            None
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=initiatorId eq "FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F"&fields=id,parentHost,failoverMode,isLunZEnabled',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'paths': [
                                {
                                    'id': 'HostInitiator_1_00:00:00:01_0'
                                },
                                {
                                    'id': 'HostInitiator_1_00:00:00:02_0'
                                }
                            ]
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'POST',
            '/api/instances/hostInitiator/HostInitiator_1/action/modify',
            {
                'isLunZEnabled': True,
                'host': {
                    'id': 'Host_1',
                },
                'failoverMode': 4,
                'initiatorSourceType': 3
            },
            204,
            None
        )

        # get_storage_group
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
                    }
                ]
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiatorPath/instances?filter=id IN ( "HostInitiator_1_00:00:00:01_0","HostInitiator_1_00:00:00:02_0" )&fields=id,fcPort',
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
                    }
                ]
            }
        )

        test_sg = self.unityapi.create_host_initiators("test1_sg", 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F', 'test1_host', '1.2.3.4')
        self.assertIsInstance(test_sg, StorageGroupInfo)
        self.assertEqual(test_sg.name, "test1_sg", "Unexpected value for name")

        expected_hbasp_list = [
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A, 0),
            HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_B, 0)
        ]
        self.assertEqual(len(test_sg.hbasp_list), len(expected_hbasp_list), "Unexpected number of entries in hbasp_list")
        if len(test_sg.hbasp_list) == len(expected_hbasp_list):
            for index, expected_hbasp in enumerate(expected_hbasp_list, 0):
                test_hbasp = test_sg.hbasp_list[index]
                self.assertEqual(expected_hbasp, test_hbasp, "Unexpected value hbasp %s, expected %s actutal %s" % (index, expected_hbasp, test_hbasp))

    def test_create_host_initiators_invalid_sg(self):
        """create_host_initiators invalid storage group
        """
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiCriticalErrorException, self.unityapi.create_host_initiators,
                          None, 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F')

    def test_create_host_initiators_non_existent_sg(self):
        """create_host_initiators non_existent storage group
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,description',
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
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.create_host_initiators,
                          "test1_sg", 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F')

    def test_create_host_initiators_invalid_wwn(self):
        """create_host_initiators invalid wwn
        """
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiCriticalErrorException, self.unityapi.create_host_initiators,
                          "test1_sg", wwn='zzz')

    def test_create_host_initiators_invalid_arraycommpath(self):
        """create_host_initiators invalid arraycommpath
        """
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiCriticalErrorException, self.unityapi.create_host_initiators,
                          'test1_sg', 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F', arraycommpath="invalid")

    def test_create_host_initiators_invalid_init_type(self):
        """create_host_initiators invalid init_type
        """
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiCriticalErrorException, self.unityapi.create_host_initiators,
                          'test1_sg', 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F', init_type=None)

    def test_create_host_initiators_invalid_failovermode(self):
        """create_host_initiators invalid failovermode
        """
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiCriticalErrorException, self.unityapi.create_host_initiators,
                          'test1_sg', 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F', failovermode="invalid")

    def test_create_host_initiator(self):
        """Create initiator
        """
        print self.shortDescription()
        self.setUpUnity()

        # create_host_initiator calls
        self.addRequest(
            'GET',
            '/api/instances/host/name:test1_sg?fields=id,description',
            None,
            200,
            {
                'content': {
                    'id': 'Host_1',
                    'description': 'test1_host'
                }
            }
        )

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=initiatorId eq "FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F"&fields=id,parentHost,failoverMode,isLunZEnabled',
            None,
            200,
            {
                'entries': [
                ]
            }
        )

        self.addRequest(
            'POST',
            '/api/types/hostInitiator/instances',
            {
                'isLunZEnabled': True,
                'host': {
                    'id': 'Host_1',
                },
                'failoverMode': 4,
                'initiatorSourceType': 3,
                'initiatorType': 1,
                'initiatorWWNorIqn': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F'
            },
            201,
            {
                'id': 'HostInitiator_1'
            }
        )

        test_hbaii = self.unityapi.create_host_initiator("test1_sg",
                                                         'test1_host',
                                                         '1.2.3.4',
                                                         'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                                                         STORAGE_PROCESSOR_A,
                                                         0)
        self.assertIsInstance(test_hbaii, HbaInitiatorInfo)

        expected_hbaii = HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A, 0, 'test1_host', '1.2.3.4')
        self.assertEqual(expected_hbaii, test_hbaii, "Unexpected value hbasp expected %s actual %s" % (expected_hbaii, test_hbaii))

    def test_host_initiator_ignored(self):
        """ Host initiator ignored
        """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?fields=id,initiatorId,paths,isIgnored',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1',
                            'initiatorId': 'FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F',
                            'isIgnored': True,
                            'paths': [
                                {
                                    'id': 'HostInitiator_1_00:00:00:01_0'
                                },
                                {
                                    'id': 'HostInitiator_1_00:00:00:02_0'
                                }
                            ]
                        }
                    }
                ]
            }
        )
        self.addRequest(
            'GET',
            '/api/types/hostInitiatorPath/instances?fields=id,fcPort',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1_00:00:00:01_0',
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
                    }
                ]
            }
        )

        expected_hbasp_list = [HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_A,
                                                0, isignored=True),
                               HbaInitiatorInfo("FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F", STORAGE_PROCESSOR_B,
                                                0, isignored=True)
                               ]

        test_hbasp_list = self.unityapi.get_hba_port_info()
        for index, expected_hbasp in enumerate(expected_hbasp_list, 0):
            test_hbasp = test_hbasp_list[index]
            self.assertEqual(expected_hbasp, test_hbasp)

    def test_deregister_hba_uid(self):
        """ Deregister initiator
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=initiatorId eq "FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F"&fields=id',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'id': 'HostInitiator_1',
                        }
                    }
                ]
            }
        )

        self.addRequest(
            'DELETE',
            '/api/instances/hostInitiator/HostInitiator_1',
            None,
            204,
            None
        )

        result = self.unityapi.deregister_hba_uid('FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F'),
        self.assertTrue(result, "Unexpected result")

    def test_deregister_hba_uid_invalid_wwn(self):
        """create_host_initiators invalid wwn
        """
        print self.shortDescription()
        self.setUpUnity()

        self.assertRaises(SanApiCriticalErrorException, self.unityapi.deregister_hba_uid,
                          wwn='zzz')

    def test_deregister_hba_uid_non_existent_wwn(self):
        """create_host_initiators invalid wwn
        """
        print self.shortDescription()
        self.setUpUnity()

        self.addRequest(
            'GET',
            '/api/types/hostInitiator/instances?filter=initiatorId eq "FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F"&fields=id',
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

        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.deregister_hba_uid,
                          wwn='FF:01:02:03:04:05:06:07:08:09:0A:0B:0C:0D:0E:0F')


if __name__ == "__main__":
    unittest.main()
