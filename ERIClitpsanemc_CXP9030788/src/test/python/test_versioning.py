'''
Created on 21/10/2014

@author: eadapar
'''
import unittest
import logging
from mock import MagicMock, patch
from testfunclib import prepare_mocked_popen, ListHandler
from sanapilib import *
from vnxcommonapi import VnxCommonApi
from sanapiexception import (SanApiOperationFailedException,
SanApiCriticalErrorException)
from sanapicfg import *
from emctest import TestSanEMC
from sanapiinfo import SanInfo

class TestVersioning(TestSanEMC):

    def setUp(self):
        # create a VnxCommonApi object
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)
        self.list_handler = ListHandler()
        self.logger.addHandler(self.list_handler)
        self.console_handler = logging.StreamHandler()
        self.logger.addHandler(self.console_handler)
        self.san_api_cfg = SANAPICFG

    def setup_vnx(self):
        self.vnx = VnxCommonApi(self.logger)
        self.vnx.initialise((self.spa, self.spb), self.adminuser,
                       self.adminpasswd, self.scope, False, vcheck=False)

    def setup_versions(self, flare=None, host=None, platform='linux'):
        self.vnx._get_platform_information = MagicMock(
                name="_get_platform_information",
                return_value=platform)
        fakeobj = SanInfo(flare, "VNX5400", "CKM00190502296")
        if flare is not None:
            self.vnx.get_san_info = MagicMock(
                    name="get_san_info", return_value=fakeobj)
        if host is not None:
            self.vnx._get_host_naviseccli_version = MagicMock(
                    name="_get_host_naviseccli_version",
                    return_value=host)

    def tearDown(self):
        super(TestVersioning, self).tearDown()
        self.list_handler.reset()
        self.logger.removeHandler(self.console_handler)

    def test_check_host_naviseccli_version_valid_version(self):
        """
        Test _check_host_naviseccli_version() returns True on successful valid version match
        """

        print self.shortDescription()
        val = "7.33.1.0.33"
        self.setup_vnx()
        self.setup_versions(host=val)
        result = self.vnx._check_host_naviseccli_version()
        self.assertTrue(result)
        self.msginfo = "Valid NaviCLI version being used 7.33.1.0.33"
        self.assertTrue(self.msginfo  in self.list_handler.all_levels)

    def test_check_newer_flare_version_invalid(self):
        """
        Check if _check_flare_version() returns False when version is newer than configured
        """

        print self.shortDescription()
        val = "25.41.309.8.999"
        self.setup_vnx()
        self.setup_versions(flare=val)
        result = self.vnx._check_flare_version()
        self.assertFalse(result)
        self.msginfo = "Unsupported FLARE/OE version 25.41.309.8.999 detected"

        self.assertTrue(self.msginfo  in self.list_handler.all_levels)

    def test_check_flare_version_valid_version(self):
        """
        Check if _check_flare_version() returns True on successful valid version match
        """

        print self.shortDescription()
        val = "05.33.009.5.184"
        self.setup_vnx()
        self.setup_versions(flare=val)
        result = self.vnx._check_flare_version()
        self.assertTrue(result)
        self.msginfo = "Valid FLARE/OE version being used 05.33.009.5.184"
        self.assertTrue(self.msginfo  in self.list_handler.all_levels)

    def test_check_host_navisecceli_version_invalid_version(self):
        """
        Check if _check_host_naviseccli_version() returns False on unsuccessful naviseccli version match
        """

        # Should return False when naviseccli version is unsupported
        print self.shortDescription()
        val = "00.00.00.00.33"
        self.setup_vnx()
        self.setup_versions(host=val)
        result = self.vnx._check_host_naviseccli_version()
        self.assertFalse(result)
        self.msgwarn = "Unsupported version of NaviCLI being used"\
                " 00.00.00.00.33."
        print "THE WARNING! %s"%self.list_handler.warning
        self.assertTrue(self.msgwarn  in self.list_handler.warning)

    def test_check_flare_version_invalid_versions(self):
        """
        Check if _check_flare_version() returns False on unsuccessful naciseccli version match
        """

        # Should return False when FLARE / OE version is unsupported
        print self.shortDescription()
        val = "00.00.000.0.1"
        self.setup_vnx()
        self.setup_versions(flare=val)
        result = self.vnx._check_flare_version()
        self.assertFalse(result)
        self.msgwarn = "Unsupported FLARE/OE version"

        self.assertTrue(self.msgwarn  in "".join(self.list_handler.all_levels))

    def test_check_host_navisecceli_version_no_version_provided(self):
        '''Check if _check_host_naviseccli_version() raises Exception
        on unsuccessful naviseccli version match'''

        # Should return False when naviseccli version is unsupported
        print self.shortDescription()

        self.setup_vnx()
        self.vnx._get_platform_information = MagicMock(
                name="_get_platform_information", return_value='linux')
        self.vnx._get_host_naviseccli_version = MagicMock(
                name="_get_host_naviseccli_version",
                side_effect=SanApiOperationFailedException(
                    "Unable to get host NaviCLI version", 1))
        self.assertRaisesRegexp(SanApiOperationFailedException,
                "Unable to get host NaviCLI version",
                self.vnx._check_host_naviseccli_version)

    def test_check_host_navisecceli_version_no_version_in_sanapi_ini(self):
        """Check if _check_host_naviseccli_version() returns False when no navisec versions specified in ini file"""

        # Should return False when naviseccli version is unsupported
        print self.shortDescription()

        self.setup_vnx()
        self.setup_versions(host="7.33.1.0.33", platform='solaris')
        result = self.vnx._check_host_naviseccli_version()
        self.assertFalse(result)

    def test_check_host_navisecceli_version_invalid_platform(self):
        """
        Check if _check_host_naviseccli_version() raises Exception is unsupported platform
        """

        # Should return False when naviseccli version is unsupported
        print self.shortDescription()
        self.setup_vnx()
        self.setup_versions(host="7.33.1.0.33", platform="RedHat")
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Unable to retrieve platform information from config file",
                self.vnx._check_host_naviseccli_version)

    def test_get_host_naviseccli_valid_version(self):
        """
        Check if _check_host_naviseccli_version() returns version on successful naciseccli version match
        """

        print self.shortDescription()
        self.setup_vnx()
        outlist = '../data/naviseccli_help_output_valid.txt'
        errfile = None
        retcode = 0
        self.vnx._navisec = prepare_mocked_popen(outlist, errfile, retcode)
        result = self.vnx._get_host_naviseccli_version()
        self.assertEqual(result, '7.33.1.0.33')

    def test_get_host_naviseccli_invalid_version(self):
        """
        Check if _check_host_naviseccli_version() returns False on unsuccessful naciseccli version match
        """

        print self.shortDescription()
        self.setup_vnx()
        outlist = '../data/naviseccli_help_output_invalid.txt'
        errfile = None
        retcode = 0
        self.vnx._navisec = prepare_mocked_popen(outlist, errfile, retcode)
        self.assertRaisesRegexp(SanApiOperationFailedException,
                 "Unable to get host NaviCLI version",
                 self.vnx._get_host_naviseccli_version)

    def test_get_san_info_valid_version(self):
        """Check if get_san_info() returns valid OE version match
        """

        print self.shortDescription()
        self.setup_vnx()
        vflare = '                      '\
                 'Revision:            05.33.000.5.052     '\
                 'Model:               VNX5400        ' \
                 'Serial No:           CKM00190502296     '\
                 '                                      '\
                 '                                    '
        self.vnx._navisec = MagicMock(name="_navisec", return_value=vflare)
        result = self.vnx.get_san_info()
        oe = result._oe_version
        model = result._san_model
        self.assertEqual(oe, '05.33.000.5.052')
        self.assertEqual(model, 'VNX5400')

    def test_get_san_info_invalid_oe_version(self):
        """Check if get_san_info() handles invalid OE version match
        """

        print self.shortDescription()
        self.setup_vnx()
        vflare = '                      \n' \
                 'Serial No:           CKM00190502296     \n'\
                 'Revision:            0gshy5.5.052     \n'\
                 'Model:               VNX5400        \n'\
                 '                                      \n'\
                 '                                    '
        self.vnx._navisec = MagicMock(name="_navisec", return_value=vflare)
        self.assertRaisesRegexp(SanApiOperationFailedException,
                "Unable to get VNX OE version",
                self.vnx.get_san_info)

    def test_get_san_info_reverse_order_output(self):
        """Check if get_san_info() handles invalid navisec output in reverse order
        """

        print self.shortDescription()
        self.setup_vnx()
        vflare = '                      \n' \
                 'Serial No:           CKM00190502296       '\
                 'Model:               VNX5400        \n'\
                 'Revision:            05.33.000.5.052     \n'\
                 '                                      \n'\
                 '                                    '
        self.vnx._navisec = MagicMock(name="_navisec", return_value=vflare)
        result = self.vnx.get_san_info()
        oe = result._oe_version
        model = result._san_model
        self.assertEqual(oe, '05.33.000.5.052')
        self.assertEqual(model, 'VNX5400')

    def test_get_san_info_reverse_extra_output(self):
        """Check if get_san_info() handles invalid navisec output (extra output)
        """

        print self.shortDescription()
        self.setup_vnx()
        vflare = 'Signature:           3526807\n'\
                 'Peer Signature:      3608610\n'\
                 'Revision:            05.33.000.5.052\n'\
                 'SCSI Id:             0\n'\
                 'Model:               VNX5400\n'\
                 'Model Type:          Rackmount\n'\
                 'Prom Rev:            33.40.00\n' \
                 'Serial No:           CKM00190502296\n'

        self.vnx._navisec = MagicMock(name="_navisec", return_value=vflare)
        result = self.vnx.get_san_info()
        oe = result._oe_version
        model = result._san_model
        serial = result._san_serial
        self.assertEqual(oe, '05.33.000.5.052')
        self.assertEqual(model, 'VNX5400')
        self.assertEqual(serial, 'CKM00190502296')

    def test_get_san_info_invalid_san_model(self):
        """Check if get_san_info() handles invalid SAN model match
        """

        print self.shortDescription()
        self.setup_vnx()
        vflare = '                      '\
                 'Revision:            05.33.000.5.052     '\
                 '                                      '\
                 '                                    '
        self.vnx._navisec = MagicMock(name="_navisec", return_value=vflare)
        self.assertRaisesRegexp(SanApiOperationFailedException,
                "Unable to get VNX Model information",
                self.vnx.get_san_info)

    def test_check_flare_version_version_empty_version_list(self):
        """
        Check if check_flare_version_version() returns False and handles being passed no flare/oe from get_san_info()
        """

        print self.shortDescription()
        self.setup_vnx()
        self.setup_versions(flare='')
        result = self.vnx._check_flare_version()
        self.assertFalse(result)
        #self.msgwarn = "The FlARE / OE version is lower than the required "
        self.msgwarn = "Unsupported FLARE/OE version"
        # EDDERS
        self.assertTrue(self.msgwarn  in "".join(self.list_handler.all_levels))

    def test_check_host_navisecceli_version_item_missing_in_sanapi_ini(self):
        """
        Check if _check_host_naviseccli_version() raises exception when no navisec versions item is present in ini file
        """

        print self.shortDescription()
        orig_cfg = self.san_api_cfg
        test_cfg = SanApiCfg()
        test_cfg.load_file('../data/faulty_sanapi.ini')
        self.setup_vnx()
        self.setup_versions(host="7.33.1.0.33", platform="solaris")
        self.vnx._cfg = test_cfg
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Couldn't retrieve navisec_versions from config file",
                self.vnx._check_host_naviseccli_version)
        self.vnx._cfg = orig_cfg

    def test_check_host_navisecceli_version_tokens_missing_in_sanapi_ini(self):
        """
        Check if _check_host_naviseccli_version() raises exception when no navisec SW tokens to check item is present in ini file
        """

        print self.shortDescription()
        orig_cfg = self.san_api_cfg
        test_cfg = SanApiCfg()
        test_cfg.load_file('../data/faulty_sanapi.ini')
        self.setup_vnx()
        self.setup_versions(host="7.33.1.0.33")
        self.vnx._cfg = test_cfg
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Couldn't retrieve Number of tokens to check from config file",
                self.vnx._check_host_naviseccli_version)
        self.vnx._cfg = orig_cfg

    def test_check_flare_version_item_missing_in_sanapi_ini(self):
        """
        Check if _check_host_naviseccli_version() raises exception when no OE SW tokens item is present in ini file
        """

        print self.shortDescription()
        orig_cfg = self.san_api_cfg
        test_cfg = SanApiCfg()
        test_cfg.load_file('../data/faulty_sanapi.ini')
        self.setup_vnx()
        self.setup_versions(flare="05.33.000.5.052")
        self.vnx._cfg = test_cfg
        self.assertRaisesRegexp(SanApiCriticalErrorException,
                "Couldn't retrieve flare_versions from config file",
                self.vnx._check_flare_version)
        self.vnx._cfg = orig_cfg


if __name__ == "__main__":
    unittest.main()
