'''
Created on 14 Jul 2014

@author: esteved
'''
import unittest

from mock import patch, Mock, MagicMock
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

    """ METHODS TO SET UP TEST DATA """
    def setUpVnx(self):
        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        self.vnx.initialise((self.spa, self.spb), self.adminuser,
                       self.adminpasswd, self.scope, vcheck = False)

    def setUp(self):
        # create a VnxCommonApi object
        #self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"
        self.timeout = "60"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)

    def test_rename_lun_ok(self):
        """
        test_rename_lun_ok where all raid group luns are returned
        """

        print self.shortDescription()
        self.setUpVnx()
        lun = self.getLun()
        self.vnx.get_lun = MagicMock(name = "get_lun", return_value = lun) 
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        # Execute the Tested Method
        self.vnx.rename_lun(lun.id, lun.name)
        self.vnx._navisec.assert_called_once_with("chglun -l %s -name \"%s\"" % (lun.id, lun.name))


    def test_rename_lun_invalid_id_object(self):
        """
        test_rename_lun_ where invalid lun id object is passed
        """

        print self.shortDescription()
        self.setUpVnx()
        # Execute the Tested Method
        self.assertRaises(SanApiOperationFailedException, self.vnx.rename_lun, ['x','y'], 'i wanna fail')

    def getLun(self):
        return LunInfo("42", "renamed", "60:06:01:60:97:D0:35:00:61:31:E3:10:2D:22:E4:11", "lepool", "10Gb", "StoragePool", "5")


if __name__ == "__main__":
    unittest.main()
