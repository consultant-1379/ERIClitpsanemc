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
from emctest import TestSanEMC


class Test(TestSanEMC):
    """
    Test class for Storage Group
    """

    """METHODS TO SET UP TEST DATA"""
    def setUpVnx(self):
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope)

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

    def _compare_sg(self, sg1, sg2):
        """
        Compare Storage Groups
        """

        self.assertEquals(sg1, sg2, "Storage Groups Differ") 
        return

    def test_create_sg_ok(self):
        """
        VNX create SG: Mock navisec & get storage group, validate navisec called correctly and returned object is correct
        """

        print self.shortDescription()
        self.setUpVnx()
        refSG = getPairsSG()
        self.vnx._navisec = MagicMock(name = "_navisec")
        self.vnx.get_storage_group = MagicMock(name = "get_storage_group", return_value = refSG)
        sg = self.vnx.create_storage_group(refSG.name)
        self.assertIsInstance(sg, StorageGroupInfo)
        self.assertEqual(sg.name, refSG.name, "Storage Group Name %s incorrect, should be %s" % (sg.name, refSG.name))
        self._compare_sg(sg, refSG)

    def test_create_sg_nok_sg_exists(self):
        """
        VNX create SG: Navisec call raises SanApiEntityAlreadyExistsException if group already exists
        """

        print self.shortDescription()
        self.setUpVnx()
        outfile = '../data/sg_create_name_exists.xml'
        errfile = None
        retcode = 0
        mock_popen = prepare_mocked_popen(outfile, errfile, retcode)
        sgname = 'atsfs43_44'
        self.assertRaises(SanApiEntityAlreadyExistsException, self.vnx.create_storage_group, sgname)

    def test_create_storage_group_none_string_arg(self):
        """
        Test create storage group where none-string is passed as argument
        """

        print self.shortDescription()
        self.setUpVnx()
        self.vnx._navisec = MagicMock(name = "_navisec")
        sgname = [ 1, 2, 3 ]
        self.assertRaises(SanApiOperationFailedException, self.vnx.create_storage_group, sgname)

    """MOCK NAVISEC TO TEST THE TWO EXCEPTIONS IT CAN RAISE"""
    def test_create_sg_nok_connection(self):
        """
        VNX create SG: Navisec call raises SanApiConnectionException
        """

        print self.shortDescription()
        self.setUpVnx()
        refSG = getSG()
        self.vnx._navisec = MagicMock(name = "_navisec", side_effect=SanApiConnectionException("Connection Failed", 1) )
        self.vnx.get_storage_group = MagicMock(name = "get_storage_group", return_value = refSG)
        self.assertRaises(SanApiConnectionException, self.vnx.create_storage_group, refSG.name)

    def test_create_sg_nok_command(self):
        """
        VNX create SG: Navisec call raises SanApiCommandException
        """

        print self.shortDescription()
        self.setUpVnx()
        refSG = getSG()
        self.vnx._navisec = MagicMock(name = "_navisec", side_effect=SanApiCommandException("Command Failed", 1) )
        self.vnx.get_storage_group = MagicMock(name = "get_storage_group", return_value = refSG)
        self.assertRaises(SanApiCommandException, self.vnx.create_storage_group, refSG.name)

    def test_create_storage_group(self):
        """
        test_create_storage_group - names with spaces are handled correctly
        """

        print self.shortDescription()
        self.setUpVnx()
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        self.vnx.get_storage_group = MagicMock(name = 'get_storage_group', return_value=None)
        name="space here"
        print "Verifying navisec is called with: %s in cmd string" % name
        self.vnx.create_storage_group(name)
        self.assertTrue(name in self.vnx._navisec.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
