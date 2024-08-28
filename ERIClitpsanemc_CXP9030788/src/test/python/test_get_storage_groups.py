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




class Test(unittest.TestCase):
    """
    Test class for Storage Group
    """


    """ METHODS TO SET UP TEST DATA """

    def setUpVnx(self):
        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope, vcheck=False)

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

        #self.logger = None

    def tearDown(self):
        pass

    def test_get_storage_groups(self):
        """ Test get storage groups """
        print self.shortDescription()

        # Initialise test - prepare test objects, vnx and mock objects
        self.setUpVnx()
        self.setUpPopen('../data/list_sgs.xml')

        # Expected object returned by the get_storage_group method
        reference_sg = getPairsSG()

        expected_cmd = '/opt/Navisphere/bin/naviseccli -h 1.2.3.4 -User "admin" -Password shroot12 -timeout 50 -Scope global -xml  storagegroup -list'

        # Execute the Tested Method
        res_sgs=self.vnx.get_storage_groups()

        # Check the Results
        self.mock_popen.assert_called_once_with(expected_cmd, shell=True, stderr=-1, stdout=-1, stdin=-1)

        # Validate one of the SGs in the list
        for returnedSG in res_sgs:
            if returnedSG.name == reference_sg.name:
                break

        self.assertEqual (returnedSG,reference_sg, "Storage Group incorrect.  Showing test result group followed by expected storage group\n%s\n%s" \
                             % ( returnedSG, reference_sg) )

        # Check the correct number of SGs returned
        self.assertEqual(len(res_sgs), 8)


    """ NEGATIVE CONNECTION TESTS """
    def test_get_storage_groups_wrong_credentials(self):
        """ Test get storage groups where navisec is called with wrong credentials eg username/password/scope"""
        print self.shortDescription()

        # Initialise test - prepare test objects, vnx and mock objects
        self.setUpVnx()
        self.setUpPopen('../data/connection_wrong_credentials.xml', 255)

        # Check the results
        self.assertRaises(SanApiConnectionException, self.vnx.get_storage_groups)


    def test_get_storage_groups_timeout (self):
        """ Test get storage groups where navisec is called and navisec reports a timeout"""
        print self.shortDescription()

        # Initialise test - prepare test objects, vnx and mock objects
        self.setUpVnx()
        self.setUpPopen('../data/connection_timeout1.xml', 255)

        # Check the results
        self.assertRaises(SanApiConnectionException, self.vnx.get_storage_groups)

    def test_get_storage_groups_ms_not_running (self):
        """ Test get storage groups where navisec cannot communicate with server side ms"""
        print self.shortDescription()

        # Initialise test - prepare test objects, vnx and mock objects
        self.setUpVnx()
        self.setUpPopen('../data/connection_navi_ms_not_running.xml', 255)

        # Check the results
        self.assertRaises(SanApiConnectionException, self.vnx.get_storage_groups)




    """
    def test_get_storage_groups_with_wrong_xml(self):
        ""Test get storage groups where navisec returns wrong XML (god knows if this could happen!""
        print self.shortDescription()

        # Initialise test - prepare test objects, vnx and mock objects
        self.setUpVnx()
        self.setUpPopen('../data/rglun.xml.cmdok') 

        res_sgs=self.vnx.get_storage_groups()

        print "LOOOKA %s" % res_sgs
        for sg in res_sgs:
            print sg
        #self.assertRaises(SanApiOperationFailedException, self.vnx.get_storage_groups)
    """






if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
