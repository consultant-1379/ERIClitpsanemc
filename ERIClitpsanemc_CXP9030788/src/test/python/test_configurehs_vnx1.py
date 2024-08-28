'''
Created on 16 Jul 1934

@author: esteved
'''
import unittest
from vnxcommonapi import VnxCommonApi
from vnx1api import Vnx1Api
from sanapiexception import (SanApiCommandException,
SanApiOperationFailedException)
import logging
from testfunclib import *
from sanapiinfo import LunInfo
import mock


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
        self.vnxCommApiObj = Vnx1Api(self.logger)
        self.vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        self.vnxCommApiObj.initialise((self.spa, self.spb), self.adminuser,
                                      self.adminpasswd, self.scope, vcheck=False)

    def setUpVnx1(self):
        # Setup array object
        self.vnx = Vnx1Api(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope, vcheck=False)

    def test_configurehs_no_name_ok(self):
        """
        configure hs with no name supplied. OK
        """

        print self.shortDescription()
        self.setUp()
        lun = LunInfo('40', 'ste1', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:11',
                        '2', '549407', 'RaidGroup', 'HS')
        self.vnxCommApiObj._get_luns = mock.Mock(return_value=[].append(lun))
        self.vnxCommApiObj.get_lun = MagicMock(name = 'get_lun', return_value=lun)
        self.vnxCommApiObj.get_next_available_lunids = MagicMock(name = 'get_next_available_lunids', return_value=['40'])
        self.vnxCommApiObj._navisec = MagicMock(name = '_navisec', return_value=0)
        retLun = self.vnxCommApiObj.configure_hs('2')  
        self.assertEqual(lun, retLun, "LUNs do not match")
        self.vnxCommApiObj.get_lun.assert_called_once_with(lun_id="40")
        self.vnxCommApiObj._navisec.assert_any_call("bind hs 40 -rg 2") 
        self.vnxCommApiObj = None

    def test_configurehs_with_name_ok(self):
        """
        configure hs with name supplied. OK
        """

        print self.shortDescription()
        self.setUp()
        lun = LunInfo('40', 'ste1', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:11',
                        '2', '549407', 'RaidGroup', 'HS')
        self.vnxCommApiObj._get_luns = mock.Mock(return_value=[].append(lun))
        self.vnxCommApiObj.get_lun = MagicMock(name = 'get_lun', return_value=lun)
        self.vnxCommApiObj.get_next_available_lunids = MagicMock(name = 'get_next_available_lunids', return_value=['40'])
        self.vnxCommApiObj._navisec = MagicMock(name = '_navisec', return_value=0)
        retLun = self.vnxCommApiObj.configure_hs('2', 'ste1')
        self.assertEqual(lun, retLun, "LUNs do not match")
        self.vnxCommApiObj.get_lun.assert_called_once_with(lun_id="40")
        self.vnxCommApiObj._navisec.assert_any_call("bind hs 40 -rg 2")
        self.vnxCommApiObj._navisec.assert_any_call("chglun -l 40 -name \"ste1\"")
        self.vnxCommApiObj = None

    def test_configurehs_no_name_invalid_rg(self):
        """
        configure hs with no name supplied.  bind fails, invalid RG
        """

        print self.shortDescription()
        self.setUp()
        outfile = '../data/configurehs_vnx1_bind_fail.xml'
        errfile = None
        retcode = 0
        mock_popen = prepare_mocked_popen(outfile, errfile, retcode)
        expected_cmd = '/opt/Navisphere/bin/naviseccli -h 1.2.3.4 -User "admin" -Password shroot12 -timeout 50 -Scope global -xml  bind hs 40 -rg 20'
        self.vnxCommApiObj.get_next_available_lunids = MagicMock(name = 'get_next_available_lunids', return_value=['40'])
        self.assertRaises(SanApiCommandException, self.vnxCommApiObj.configure_hs, '20')
        mock_popen.assert_any_call(expected_cmd, shell=True, stderr=-1, stdout=-1, stdin=-1)


    def test_configurehs_with_name_invalid_rg(self):
        """
        configure hs with name supplied.  bind fails, invalid RG
        """
        print self.shortDescription()
        self.setUp()
        outfile = '../data/configurehs_vnx1_bind_fail.xml'
        errfile = None
        retcode = 0
        mock_popen = prepare_mocked_popen(outfile, errfile, retcode)
        expected_cmd = '/opt/Navisphere/bin/naviseccli -h 1.2.3.4 -User "admin" -Password shroot12 -timeout 50 -Scope global -xml  bind hs 40 -rg 20'
        self.vnxCommApiObj.get_next_available_lunids = MagicMock(name = 'get_next_available_lunid', return_value=['40'])
        self.assertRaises(SanApiCommandException, self.vnxCommApiObj.configure_hs, '20', 'ste1')
        mock_popen.assert_any_call(expected_cmd, shell=True, stderr=-1, stdout=-1, stdin=-1)

    def test_configurehs_with_name_ok(self):
        """
        test_configure hs vnx1 - names with spaces are handled correctly
        """

        print self.shortDescription()
        self.setUpVnx1()
        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        lun = LunInfo('40', 'space here', '60:06:01:60:A9:A0:2E:00:55:55:92:E1:B9:32:E4:11',
                        '2', '549407', 'RaidGroup', 'HS')
        self.vnx.get_luns = Mock(return_value=lun)
        self.vnx.get_lun = MagicMock(name = 'get_lun', return_value=lun)
        self.vnx.get_next_available_lunids = MagicMock(name = 'get_next_available_lunids', return_value=['40'])
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        retLun = self.vnx.configure_hs('2', 'space here')
        self.assertEqual(lun, retLun, "LUNs do not match")
        self.vnx.get_lun.assert_called_once_with(lun_id="40")
        self.vnx._navisec.assert_any_call("bind hs 40 -rg 2")
        self.vnx._navisec.assert_any_call("chglun -l 40 -name \"space here\"")


if __name__ == "__main__":
    unittest.main()
