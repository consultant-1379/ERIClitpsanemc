import unittest
from mock import MagicMock
import logging
import logging.handlers

from vnxcommonapi import VnxCommonApi
from sanapiexception import SanApiOperationFailedException, SanApiEntityNotFoundException
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

    def test_get_pool_lun_name_from_lun_id(self):

        ''' testing _get_pool_lun_name_from_lun_id with all parameters ok'''
        print self.shortDescription()

        self.setUpVnx()
        prepare_mocked_popen("../data/lunlist_id.xml")

        self.assertEqual(self.vnx._get_pool_lun_name_from_lun_id(1), "Vandals_test_lun1")

    def test_get_pool_lun_name_from_lun_id_invalid_lunId(self):

        ''' testing _get_pool_lun_name_from_lun_id with invalid lunId'''
        print self.shortDescription()

        self.setUpVnx()

        self.assertRaises(SanApiOperationFailedException, self.vnx._get_pool_lun_name_from_lun_id, "One")

    def test_get_pool_lun_name_from_lun_id_resource_not_found(self):

        ''' testing _get_pool_lun_name_from_lun_id, navisec command returns lun not found '''
        print self.shortDescription()

        prepare_mocked_popen("../data/non_existing_lun_lunlistbyname.xml")
        self.setUpVnx()

        self.assertRaises(SanApiEntityNotFoundException,
                           self.vnx._get_pool_lun_name_from_lun_id, "1")

if __name__ == "__main__":
    unittest.main()