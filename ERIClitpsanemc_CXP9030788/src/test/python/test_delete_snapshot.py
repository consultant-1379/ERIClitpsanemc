''''
Created on the 27th of April 2015

@author: xbobobo
'''

import unittest
from mock import MagicMock
from vnxcommonapi import VnxCommonApi
from sanapiexception import SanApiEntityNotFoundException, \
                            SanApiCommandException
import logging
import logging.handlers
from testfunclib import prepare_mocked_popen

class Test(unittest.TestCase):

    '''
    Test class containing Test Cases designed to test the
    SAN Delete Snapshot functionality.
    Uses Unittest.
    '''

    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "****"
        self.scope = "global"
        self.timeout = "60"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)

        self.changehandler = logging.StreamHandler()
        self.changehandler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.changehandler)

        self.setUpVnx()

    def setUpVnx(self):

        ''' setup a VNX with MagicMock'''

        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(
                                                name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope, vcheck=False)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.logger.removeHandler(self.changehandler)


    def test_delete_snapshot_ok(self):

        ''' testing test_delete_snapshot_ok succeeds with all parameters ok'''

        print self.shortDescription()

        prepare_mocked_popen("../data/navisec_response_success.xml")

        self.assertTrue(self.vnx.delete_snapshot(
                                    snap_name="testingDeletingSnapshot"),
                                        "delete_snapshot does not return True")


    def test_delete_nonexisting_snapshot(self):

        ''' testing test_delete_nonexisting_snapshot where the snapshot\
         does NOT exist'''

        print self.shortDescription()

        prepare_mocked_popen("../data/delete_snapshot_nonexisting.xml")

        result = self.vnx.delete_snapshot("testingDeletingSnapshot")
        self.assertTrue(result)

    def test_delete_snapshot_YorN_prompt_failure(self):

        ''' testing test_delete_snapshot_YorN_prompt_failure Naviseccli\
         command missing '-o' option'''

        print self.shortDescription()

        prepare_mocked_popen("../data/delete_snapshot_YorN_prompt_failure.xml")

        self.assertRaises(SanApiCommandException,
                           self.vnx.delete_snapshot, "testingDeletingSnapshot")


if __name__ == "__main__":
    unittest.main()
