import unittest
from mock import MagicMock
from vnxcommonapi import VnxCommonApi
from sanapiexception import SanApiOperationFailedException, SanApiEntityNotFoundException
import logging
import logging.handlers
from testfunclib import prepare_mocked_popen


class Test(unittest.TestCase):

    def setUp(self):
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

    def test_get_pool_lun_id_from_lun_name(self):

        ''' testing _get_pool_lun_id_from_lun_name with all parameters ok'''
        print self.shortDescription()

        prepare_mocked_popen("../data/lunlist_name.xml")

        self.assertEqual(self.vnx._get_pool_lun_id_from_lun_name("Vandals_test_lun1"), "1")

    def test_get_pool_lun_id_from_lun_name_invalid_lunName(self):

        ''' testing _get_pool_lun_id_from_lun_name with an invalid Lun name'''
        print self.shortDescription()

        self.setUpVnx()

        self.assertRaises(SanApiOperationFailedException, self.vnx._get_pool_lun_id_from_lun_name, 1)

    def test_get_pool_lun_id_from_lun_name_resource_not_found(self):

        ''' testing _get_pool_lun_id_from_lun_name '''
        print self.shortDescription()

        prepare_mocked_popen("../data/non_existing_lun_lunlistbyname.xml")
        self.setUpVnx()

        self.assertRaises(SanApiEntityNotFoundException,
                           self.vnx._get_pool_lun_id_from_lun_name, "vandals_test_lun1")

if __name__ == "__main__":
    unittest.main()
