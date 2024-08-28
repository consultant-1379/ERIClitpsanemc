
import unittest

from sanapiinfo import SanInfo, SanAlert
from sanapiexception import SanApiEntityNotFoundException
from unitytest import TestUnity


class TestUnityMisc(TestUnity):
    """
    Test class contains methods to test misc methods in UnityAPI
    """

    def test_get_san_info(self):
        """ get_san_info """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/types/system/instances?fields=id,model,serialNumber',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'model': 'Unity 450F',
                            'serialNumber': 'CKM00190502296'
                        }
                    }
                ]
            }
        )
        self.addRequest(
            'GET',
            '/api/types/installedSoftwareVersion/instances?fields=id,version',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'version': '4.4.1'
                        }
                    }
                ]
            }
        )

        saninfo = self.unityapi.get_san_info()
        self.assertIsInstance(saninfo, SanInfo)
        self.assertEqual(saninfo.oe_version, "4.4.1")
        self.assertEqual(saninfo.san_model, "Unity 450F")
        self.assertEqual(saninfo.san_serial, "CKM00190502296")

    def test_get_san_alerts(self):
        """ get_san_alerts """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/types/alert/instances?fields=severity,message,description,state',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'message': "Host 5645-enm-db_cluster-db-1 does "
                                       "not have any initiators logged into the storage system.",
                            'description': "The host does not have any initiators logged into "
                                           "the storage system. Register one or more initiators "
                                           "on the host to the storage system. This may also "
                                           "require zoning changes on the switches.",
                            'severity': 2,
                            'state': 1
                        }
                    }
                ]
            }
        )
        valid_message = "Host 5645-enm-db_cluster-db-1 does not have any initiators logged into the storage system."
        valid_description = "The host does not have any initiators logged into the storage system. " \
                            "Register one or more initiators on the host to the storage system. This " \
                            "may also require zoning changes on the switches."

        san_alert = self.unityapi.get_san_alerts()
        self.assertIsInstance(san_alert[0], SanAlert)
        self.assertEqual(san_alert[0].message, valid_message)
        self.assertEqual(san_alert[0].description, valid_description)
        self.assertEqual(san_alert[0].severity, 2)
        self.assertEqual(san_alert[0].state, 1)

    def test_get_hw_san_alerts(self):
        """get_san_hw_alerts"""
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/types/memoryModule/instances?fields=id,health',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            "id":"spa_mm_0",
                            "health":{
                                "value":5,
                                "descriptionIds":["ALRT_COMPONENT_OK"],
                                "descriptions":["The component is operating normally. No action is required."]
                                }
                        }
                    }
                ]
            }
        )
        valid_msg = []

        san_hw_alert = self.unityapi.get_hw_san_alerts()
        self.assertEqual(san_hw_alert, valid_msg)

    def test_get_filtered_san_alerts(self):
        """ get_san_alerts """
        print self.shortDescription()
        self.setUpUnity()
        self.addRequest(
            'GET',
            '/api/types/alert/instances?filter=state ne 2 and (severity eq 2 or (messageId eq "14:60ed9" or messageId eq "14:60580"))&fields=severity,message,description,state',
            None,
            200,
            {
                'entries': [
                    {
                        'content': {
                            'message': "FSN port SP A FSN Port Ocp 0 1 link is down.",
                            'description': "An FSN port link is down. Identify the FSN port, and check the cabling" \
                                           "and network configuration of the Ethernet ports or link aggregations" \
                                           "included in this FSN. If the problem persists, contact your service provider.",
                            'severity': 2,
                            'state': 1
                        }
                    }
                ]
            }
        )
        valid_message = "FSN port SP A FSN Port Ocp 0 1 link is down."
        valid_description = "An FSN port link is down. Identify the FSN port, and check the cabling" \
                            "and network configuration of the Ethernet ports or link aggregations" \
                            "included in this FSN. If the problem persists, contact your service provider."

        alert_filter = ['state ne 2 and (severity eq 2 or (messageId eq "14:60ed9" or messageId eq "14:60580"))']
        san_alert = self.unityapi.get_filtered_san_alerts(alert_filter)
        self.assertIsInstance(san_alert[0], SanAlert)
        self.assertEqual(san_alert[0].message, valid_message)
        self.assertEqual(san_alert[0].description, valid_description)
        self.assertEqual(san_alert[0].severity, 2)
        self.assertEqual(san_alert[0].state, 1)

    def test_get_suitable_disk_group(self):
        """ get_disk_group """
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
        test_dg = self.unityapi.get_suitable_disk_group(15, 8)
        self.assertEqual(test_dg, "dg_40")

    def test_get_non_suitable_disk_group(self):
        """ get_disk_group """
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
                            'totalDisks': 6,
                            'diskTechnology': 6
                        }
                    }
                ]
            }
        )
        self.assertRaises(SanApiEntityNotFoundException, self.unityapi.get_suitable_disk_group,
                          number_of_disks=15, drive_type=8)


if __name__ == "__main__":
    unittest.main()
