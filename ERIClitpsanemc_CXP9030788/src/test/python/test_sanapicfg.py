'''
Created on 16 Jul 2014

@author: frepetto
'''
import unittest
from sanapicfg import SanApiCfg
from sanapiexception import (SanApiCriticalErrorException,
SanApiOperationFailedException)
from mock import Mock, patch, MagicMock
import sanapilib
import os
import testfunclib
from emctest import TestSanEMC
from ConfigParser import Error as ConfigParserError
from ConfigParser import ConfigParser


class Test(TestSanEMC):

    def setUp(self):
        self.sanapicfg = SanApiCfg()

    def tearDown(self):
        self.sanapicfg = None

    @patch("sanapicfg.os.path.exists")
    def test_load_file_raises_exception(self,  mock_os_path_exists):
        mock_os_path_exists.return_value = False
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                            "SAN API configuration file not found: not_a_file",
                            self.sanapicfg.load_file, "not_a_file")

    @patch.object(ConfigParser, "read", side_effect=ConfigParserError)
    @patch("sanapicfg.os.path.exists", return_value=True)
    def test_config_parser_error_thrown_bad_config(self, mock_os_exists,
                                                   mock_parser_read):
        """
        test config parser throws error on bad config
        """

        self.assertRaises(ConfigParserError, self.sanapicfg.load_file,
                          "NotAFile")

    def test_sanapicfg_raises_exception_when_no_cfg_file_is_provided(self):
        """
        test config parser throws error on no config
        """

        self.assertRaises(SanApiCriticalErrorException,
                          self.sanapicfg.load_file, "nonexistingfilename")
        self.assertRaises(TypeError, self.sanapicfg.load_file, None)

    def test_has_config_returns_true_when_config_provided(self):
        """
        test has config returns true when config provided
        """
        patched_os_call = patch('os.path.exists')
        started_patch = patched_os_call.start()
        started_patch.exists.return_value = True
        self.sanapicfg.config = Mock(return_value=True)
        self.sanapicfg.load_file("cfg_file")
        self.assertTrue(self.sanapicfg.has_config(),
                        "A configuration file must be provided")
        patched_os_call.stop()

    def test_get_item_with_no_configuration_provided(self):
        """
        test error thrown on get item if no config provided
        """
        self.assertRaises(SanApiCriticalErrorException, self.sanapicfg.get,
                          "a section", "an item")

    def test_get_non_existent_item(self):
        """
        test error thrown on get item if item not exist
        """

        patched_os_call = patch('os.path.exists')
        patched_os_call.start()
        self.sanapicfg.load_file("cfg_file")
        self.assertRaises(SanApiOperationFailedException, self.sanapicfg.get,
                          "a section", "an item")
        patched_os_call.stop()

    def test_get_cfg_path(self):
        """
        positive test for get_cfg_path
        """

        print self.shortDescription()
        self.assertTrue(os.path.isfile(self.sanapicfg.get_cfg_path()))

    @patch('sanapicfg.os.path')
    @patch('sanapicfg.os')
    def test_get_cfg_path_not_found(self, mock_os, mock_path):
        """
        test get_cfg_path throws exception if cfg file not found
        """

        print self.shortDescription()
        mock_path.isfile.return_value = False
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                                "API config file not found",
                                self.sanapicfg.get_cfg_path)


if __name__ == "__main__":
    unittest.main()
