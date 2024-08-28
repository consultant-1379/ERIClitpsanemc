"""
Created on 14 Jul 2014

@author: esteved
"""

import unittest
from mock import (patch, Mock, MagicMock)
import sys
from testfunclib import *
from vnxcommonapi import VnxCommonApi
from sanapiinfo import *
from sanapiexception import *
import logging
import logging.handlers
import xml.etree.ElementTree as ET


class Test(unittest.TestCase):
    """
    Test class for Storage Group
    """

    """METHODS TO SET UP TEST DATA"""
    def setUpVnx(self):
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope,vcheck=False)

    def setUpPopen(self, outfile, retcode = 0, errfile = None):
        self.outfile = outfile
        self.errfile = errfile
        self.retcode = retcode
        self.mock_popen = prepare_mocked_popen(outfile, errfile, retcode)

    def setUp(self):
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"
        self.timeout = "60"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)

    def setUpCommon(self, popen_path=None, popen_retcode=None, sgname=None):
        print self.shortDescription()
        self.setUpVnx()
        if popen_path and popen_retcode:
            self.setUpPopen(popen_path, popen_retcode)
        elif popen_path:
            self.setUpPopen(popen_path)
        if sgname:
            self.sgname = sgname

    def _compare_sg(self, sg1, sg2):
        """
        Compare Storage Groups
        """

        self.assertEquals(sg1, sg2, "Storage Groups Differ") 
        return

    def test_get_storage_group(self):
        """
        Test get storage group with no HBA/SP or HLU/ALU pairs
        """

        self.setUpCommon('../data/sg_get_ok_basic.xml', None, 'ste.test')
        uid = 'C4:0C:E5:04:2F:08:E4:11:BC:CB:00:60:16:54:1A:87'
        shareable = True
        hbasp = None
        hlualu = None
        reference_sg = StorageGroupInfo(self.sgname, uid, shareable, hbasp, hlualu)
        res_sg=self.vnx.get_storage_group(self.sgname)
        self._compare_sg(reference_sg, res_sg)

    def test_get_storage_group_not_found(self):
        """
        Test get storage group where SG does not exist
        """

        self.setUpCommon('../data/sg_not_exist.xml', None, 'fake1')
        self.assertRaises(SanApiEntityNotFoundException, self.vnx.get_storage_group, self.sgname)

    def test_get_storage_group_none_string_arg(self):
        """
        Test get storage group where none-string is passed as argument
        """

        self.setUpCommon('../data/sg_get_ok_basic.xml', None, [ 1, 2, 3 ])
        self.assertRaises(SanApiOperationFailedException, self.vnx.get_storage_group, self.sgname)

    """ NEGATIVE CONNECTION TESTS """
    def test_get_storage_group_wrong_credentials(self):
        """
        Test get storage group where navisec is called with wrong credentials eg username/password/scope
        """

        self.setUpCommon('../data/connection_wrong_credentials.xml', 255, 'ste.test')
        self.assertRaises(SanApiConnectionException, self.vnx.get_storage_group, self.sgname)

    def test_get_storage_group_timeout (self):
        """ Test get storage group where navisec is called and navisec reports a timeout"""

        self.setUpCommon('../data/connection_timeout1.xml', 255, 'ste.test')
        self.assertRaises(SanApiConnectionException, self.vnx.get_storage_group, self.sgname)

    def test_get_storage_group_ms_not_running (self):
        """
        Test get storage group where navisec cannot communicate with server side MS
        """

        self.setUpCommon('../data/connection_navi_ms_not_running.xml', 255, 'ste.test')
        self.assertRaises(SanApiConnectionException, self.vnx.get_storage_group, self.sgname)

    def test_get_storage_group_spaces(self):
        """
        test_get_storage_group - names with spaces are handled correctly
        """

        print self.shortDescription()
        self.setUpVnx()
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        self.vnx.parser.create_sg_list = MagicMock(name = 'create_sg_list', return_value=["sg"])
        name="space here"
        print "Verifying navisec is called with: %s in cmd string" % name
        self.vnx.get_storage_group(name)
        self.assertTrue(name in self.vnx._navisec.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
