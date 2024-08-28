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
                       self.adminpasswd, self.scope,vcheck=False)

        self.sg = self.get_sg()
        self.vnx.get_storage_group = MagicMock(name = 'get_storage_group', return_value=self.sg)
        self.cmd = 'storagegroup -removehlu -o -gname "' + self.sg.name + '" -hlu '
        #self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)

    def setUpPopen(self, outfile, retcode = 0, errfile = None):
        self.outfile = outfile
        self.errfile = errfile
        self.retcode = retcode
        self.mock_popen = prepare_mocked_popen(outfile, errfile, retcode)

    def setUp(self):

        # create a VnxCommonApi object
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

    def get_sg(self):
        sgname = 'stephensg'
        uid = 'C4:0C:E5:04:2F:08:E4:11:BC:CB:00:60:16:54:1A:87'
        shareable = True
        hbasp = None
        hlualu = None
        sg = StorageGroupInfo(sgname, uid, shareable, hbasp, hlualu)
        return sg

    def _compare_sg(self, sg1, sg2):
        """
        Compare Storage Groups - only really to ensure that method returns sg on +ve tests
        """
        self.assertEquals(sg1, sg2, "Storage Groups Differ") 
        return

    #@skip
    def test_rm_luns_from_sg_ok_int(self):
        """ Test rm luns from sg ok with int """
        print self.shortDescription()
        self.setUpVnx()
        hlu = 1
        expected_cmd = self.cmd + str(hlu)
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        res_sg=self.vnx.remove_luns_from_storage_group(self.sg.name, hlu)
        self.vnx._navisec.assert_called_once_with(expected_cmd)
        self._compare_sg(self.sg, res_sg)

    #@skip
    def test_rm_luns_from_sg_ok_str(self):
        """ Test rm luns from sg ok with str"""
        print self.shortDescription()
        self.setUpVnx()
        hlu = '2'
        expected_cmd = self.cmd + str(hlu)
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        res_sg=self.vnx.remove_luns_from_storage_group(self.sg.name, hlu)
        self.vnx._navisec.assert_called_once_with(expected_cmd)
        self._compare_sg(self.sg, res_sg)

    #@skip
    def test_rm_luns_from_sg_ok_mixed_list(self):
        """ Test rm luns from sg ok with list of integers str and int"""
        print self.shortDescription()
        self.setUpVnx()
        hlu = [ 1, '2', 3, '4' ] 
        expected_cmd = self.cmd + '1 2 3 4'
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        res_sg=self.vnx.remove_luns_from_storage_group(self.sg.name, hlu)
        self.vnx._navisec.assert_called_once_with(expected_cmd)
        self._compare_sg(self.sg, res_sg)

    #@skip
    def test_rm_luns_from_sg_ok_hlu_alu_pairs(self):
        """ Test rm luns from sg ok with list of hlu alu pairs"""
        print self.shortDescription()
        self.setUpVnx()
        hlualu1 = HluAluPairInfo(1,2) 
        hlualu2 = HluAluPairInfo(3,4)
        hlu = [ hlualu1, hlualu2 ]
        expected_cmd = self.cmd + '1 3'
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)
        res_sg=self.vnx.remove_luns_from_storage_group(self.sg.name, hlu)
        self.vnx._navisec.assert_called_once_with(expected_cmd)
        self._compare_sg(self.sg, res_sg)


    #@skip
    def test_rm_luns_from_sg_fail_str_list(self):
        """ Test rm luns from sg fail with list of non-numeric strings"""
        print self.shortDescription()
        self.setUpVnx()
        hlu = [ 'hello', 'goodbye' ]

        self.assertRaises(SanApiOperationFailedException,
                            self.vnx.remove_luns_from_storage_group,
                              self.sg.name, hlu)


    #@skip
    def test_rm_luns_from_sg_fail_list_bad_element(self):
        """ Test rm luns from sg fail with list ints but final element is string"""
        print self.shortDescription()
        self.setUpVnx()
        hlu = [ 1, 2, 3, 4, 'are ya gonna work' ]

        self.assertRaises(SanApiOperationFailedException,
                            self.vnx.remove_luns_from_storage_group,
                              self.sg.name, hlu)


    #@skip
    def test_rm_luns_from_sg_fail_no_sg(self):
        """Test rm luns from sg when sg does not exist"""

        print self.shortDescription()
        self.setUpVnx()
        self.setUpPopen('../data/rm_hlu_no_sg.xml')

        expected_cmd = '/opt/Navisphere/bin/naviseccli -h 1.2.3.4 -User "admin" -Password shroot12 -timeout 50 -Scope global -xml  ' + self.cmd +  '1 2'
        hlu = [1,2]

        result = self.vnx.remove_luns_from_storage_group(self.sg.name, hlu)
        self.assertTrue(result)
        self.mock_popen.assert_called_once_with(expected_cmd, shell=True, stderr=-1, stdout=-1, stdin=-1)



    #@skip
    def test_rm_luns_from_sg_fail_no_hlu(self):
        """Test rm luns from sg when hlus doe not exist on sg"""

        print self.shortDescription()
        self.setUpVnx()
        self.setUpPopen('../data/rm_hlu_no_hlu.xml')

        expected_cmd = '/opt/Navisphere/bin/naviseccli -h 1.2.3.4 -User "admin" -Password shroot12 -timeout 50 -Scope global -xml  ' + self.cmd +  '1 2'
        hlu = [1,2]

        result = self.vnx.remove_luns_from_storage_group(self.sg.name, hlu)
        self.assertTrue(result)

        self.mock_popen.assert_called_once_with(expected_cmd, shell=True, stderr=-1, stdout=-1, stdin=-1)


 

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
