"""
Created on 18 Jul 2014

@author: frepetto
"""

import unittest
import logging
from mock import patch, Mock, MagicMock
import os
import sanapilib
from sanapi import *
from sanapiexception import (SanApiException, SanApiCriticalErrorException)
from sanapicfg import SANAPICFG
from testfunclib import *
from ConfigParser import NoOptionError, NoSectionError
from emctest import TestSanEMC

class Test(TestSanEMC):

    def setUp(self):
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)
        self.sanapicfg = SANAPICFG

    def tearDown(self):
        self.sanapicfg = None

    def test_api_builder_nonexisting_type(self):
        """
        call api builder with valid array type
        """

        print self.shortDescription()
        self.assertRaises(SanApiCriticalErrorException, api_builder,
                          "nonexistingType", self.logger)

    def test_api_builder_existing_type_mixed_case(self):
        """
        testing case insensitive array type
        """

        print self.shortDescription()
        api_obj = api_builder("vNx1", self.logger)
        self.assertEqual(api_obj.__class__.__name__, "Vnx1Api",
                         "Class names must match")

    def test_api_builder_array_type_none(self):
        """
        test api builder where array type is None
        """

        print self.shortDescription()
        self.assertRaises(SanApiCriticalErrorException, api_builder,
                          None, self.logger)

    @patch('sanapi.SANAPICFG')
    def test_api_builder_load_file_sanapi_exception(self, mock_SANAPICFG):
        """
        test api_builder when load_def_file fails with sanapi exception
        """

        print self.shortDescription()
        cfg = mock_SANAPICFG
        cfg.load_file = MagicMock (name="load_file", side_effect=SanApiCriticalErrorException("mock file load failed", 1))
        self.assertRaises(SanApiCriticalErrorException, api_builder, "Vnx1", self.logger)

    @patch('sanapi.SANAPICFG')
    def test_api_builder_load_file_general_exception(self, mock_SANAPICFG):
        """
        test api_builder when load_def_file fails with sanapi exception
        """

        print self.shortDescription()
        cfg = mock_SANAPICFG
        cfg.load_file = MagicMock (name="load_file", side_effect=Exception("mock file load failed", 1))
        self.assertRaises(SanApiCriticalErrorException, api_builder, "Vnx1", self.logger)

    @patch('sanapi.SANAPICFG')
    def test_api_builder_no_option_error(self, mock_SANAPICFG):
        """
        test api_builder when get supported arrays fails
        """

        cfg = mock_SANAPICFG
        cfg.return_value.get = MagicMock (name="get", side_effect=NoOptionError("mock failed get arrays", 1))
        self.assertRaises(SanApiCriticalErrorException, api_builder, "Vnx1", self.logger)

    @patch('sanapi.SANAPICFG')
    def test_sanapi_not_implemented(self, mock_SANAPICFG):
        """
        test san api methods raise not implemented error exception
        """

        cfg = mock_SANAPICFG
        cfg.load_file = MagicMock (name="load_file")
        sanapi = SanApi()

        self.assertRaises(NotImplementedError, sanapi.initialise, "1.2.3.4", "1.2.3.4", 'a', 'b', 'global')
        self.assertRaises(NotImplementedError, sanapi.get_lun, lun_id='1')
        self.assertRaises(NotImplementedError, sanapi.get_luns)
        self.assertRaises(NotImplementedError, sanapi.create_lun, 'a', '10', 'RaidGroup', '3')
        self.assertRaises(NotImplementedError, sanapi.create_host_initiator, 'a', 'host', '1.2.3.4', '22', 'a', '1')
        self.assertRaises(NotImplementedError, sanapi.add_lun_to_storage_group, "a", "1", "2")
        self.assertRaises(NotImplementedError, sanapi.create_storage_group, "a")
        self.assertRaises(NotImplementedError, sanapi.get_storage_group, "a")
        self.assertRaises(NotImplementedError, sanapi.get_storage_groups)
        self.assertRaises(NotImplementedError, sanapi.get_storage_pool, sp_name="mypool")
        self.assertRaises(NotImplementedError, sanapi.get_storage_pool, sp_id="23")
        self.assertRaises(NotImplementedError, sanapi.get_snapshots)
        self.assertRaises(NotImplementedError, sanapi.get_snapshot, snap_name="fuego")
        self.assertRaises(NotImplementedError, sanapi.create_snapshot, lun_name="spLUN1", snap_name="fuego")
        self.assertRaises(NotImplementedError, sanapi.restore_snapshot, lun_name="spLUN1", snap_name="tine")
        self.assertRaises(NotImplementedError, sanapi.delete_snapshot, snap_name="tine")

    @patch('sanapi.SANAPICFG')
    def test_config_file_cannot_get_support_array_types(self, mock_sanapicfg):
        """
        check exception is raised if config file does not contain supported array types
        """

        print self.shortDescription()
        cfgobj = mock_sanapicfg
        errmsg = "cannot get config file option!"
        cfgobj.get.side_effect = NoOptionError(errmsg, 1)
        self.assertRaisesRegexp(Exception, errmsg, api_builder, "vnx1", self.logger)

    @patch('sanapi.SANAPICFG')
    def test_get_api_version(self, mock_sanapicfg):
        """
        Return the API version number
        """

        print self.shortDescription()
        api_version = get_api_version()
        self.assertEqual(api_version, "unknown version", "When maven resources hasn't run the version will be set to unknown")


if __name__ == "__main__":
    unittest.main()
