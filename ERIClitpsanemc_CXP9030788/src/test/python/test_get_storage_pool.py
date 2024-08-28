'''
Created on 14 Oct 2014

@author: reenind
'''
import unittest
from vnxcommonapi import VnxCommonApi
from sanapiexception import *
from mock import patch, Mock, MagicMock
import logging
import testfunclib


class Test(unittest.TestCase):

    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"
        self.timeout = "50"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.INFO)

    def setUpVnx(self):
        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope, vcheck = False)

    ''' Get by spid'''

    def test_getstoragepool_withnonexistingid(self):
        ''' test getstoragepoolbyname_withnonexistingid tries to get a non existing storage pool'''
        print self.shortDescription()
        fakestoragepoolid = "55"

        vnxCommAPIObj = VnxCommonApi(self.logger)
        testfunclib.prepare_mocked_popen(
            "../data/non_existing_storagepoolbyid.xml")
        vnxCommAPIObj.initialise((self.spa, self.spb),
                                 self.adminuser, self.adminpasswd, self.scope, vcheck=False)

        testfunclib.myassert_raises_regexp(self, SanApiEntityNotFoundException, "Could not retrieve the specified \(Storagepool\)", vnxCommAPIObj.get_storage_pool, sp_id=fakestoragepoolid)

    def test_getstoragepool_withexistingid(self):
        ''' test getstoragepool_withnexistingid tries to get an storage pool'''
        print self.shortDescription()
        existing_storagepoolname = "5"

        testfunclib.prepare_mocked_popen(
            "../data/storage_pool_getbyid_ok_response.xml")

        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj.initialise((self.spa, self.spb),
                                 self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        storage_pool_info = vnxCommApiObj.get_storage_pool(
            sp_id=existing_storagepoolname)

        self.assertEqual("5", storage_pool_info.id,
                         "Storage pool info id' must match")

    def test_getstoragepool_by_id_and_by_name_must_match(self):
        ''' test_getstoragepool_by_id_and_by_name_must_match '''
        print self.shortDescription()
        existing_storagepoolname = "5"

        testfunclib.prepare_mocked_popen(
            "../data/storage_pool_getbyid_ok_response.xml")

        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj.initialise((self.spa, self.spb),
                                 self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        storage_pool_info_from_id = vnxCommApiObj.get_storage_pool(
            sp_id=existing_storagepoolname)

        existing_storagepoolname = "TORD7"

        testfunclib.prepare_mocked_popen(
            "../data/storage_pool_getbyname_ok_response.xml")

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        storage_pool_info_from_name = vnxCommAPIObj.get_storage_pool(
            sp_name=existing_storagepoolname)

        self.assertEqual(storage_pool_info_from_id.id,
                         storage_pool_info_from_name.id, "Ids must be equal")
        self.assertEqual(storage_pool_info_from_id.name,
                         storage_pool_info_from_name.name,
                         "Names must be equal")

    ''' Get by name'''

    def test_getstoragepool_withnonexistingname(self):
        ''' test getstoragepool_withnonexistingname tries to get a non existing storage pool'''
        print self.shortDescription()
        fakestoragepoolname = "fake123"

        testfunclib.prepare_mocked_popen(
            "../data/storage_pool_getbyname_error_response.xml")

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb),
                                 self.adminuser, self.adminpasswd, self.scope, vcheck=False)

        testfunclib.myassert_raises_regexp(self, SanApiEntityNotFoundException, "Could not retrieve the specified \(Storagepool\)", vnxCommAPIObj.get_storage_pool, sp_name=fakestoragepoolname)

    def test_getstoragepool_withexistingname(self):
        ''' test getstoragepool_withnexistingname tries to get an storage pool'''
        print self.shortDescription()
        existining_storagepoolname = "TORD7"

        testfunclib.prepare_mocked_popen(
            "../data/storage_pool_getbyname_ok_response.xml")

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)

        storage_pool_info = vnxCommAPIObj.get_storage_pool(
            sp_name=existining_storagepoolname)

        self.assertEqual("TORD7", storage_pool_info.name,
                         "Names of the storage pool info must be equal")

    def test_get_storage_pool(self):
        """test_get_storage_pool - names with spaces are handled correctly"""
        print self.shortDescription()

        self.setUpVnx()

        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)

        # Mock called functions as we are not interested in them, only the cmd string structure
        self.vnx.parser.create_dict = MagicMock(name = 'create_dict', return_value=None)
        self.vnx.parser.create_spinfo_from_dict = MagicMock(name = 'create_spinfo_from_dict', return_value=None)

        name="space here"
        cmd_string = "storagepool -list -name \"%s\"" % name
        print "Verifying navisec is called with: %s" % cmd_string 
        self.vnx.get_storage_pool(sp_name=name)
        self.vnx._navisec.assert_called_once_with(cmd_string)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
