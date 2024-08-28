'''
Created on 13 Oct 2014

@author: emicfah
'''
import unittest
from mock import patch, Mock, MagicMock
import sys
#sys.path.append(".")
from vnxcommonapi import VnxCommonApi
from vnx2api import Vnx2Api
from sanapiinfo import LunInfo
from sanapiexception import SanApiCriticalErrorException, SanApiOperationFailedException, SanApiCommandException, SanApiConnectionException, SanApiException
import logging
import logging.handlers
from testfunclib import *
import sanapilib
import mock
import subprocess

DATADIR = '../data/empty_vnx/'


class Test(unittest.TestCase):


    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd="/opt/Navisphere/bin/naviseccli"
        self.spa="1.2.3.4"
        self.spb="1.2.3.5"
        self.adminuser="admin"
        self.adminpasswd="shroot12"

        self.sp_list="../data/empty_vnx/storagepool_list.xml"

        self.scope = "global"
        self.timeout="60" 
        # setup logging with threshold of WARNING
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)
        self.logger = None

    def tearDown(self):
        pass

    #@skip
    def test_get_storage_groups_empty_vnx(self):
        ''' test get_storage_groups() on an empty vnx'''
        print self.shortDescription() 
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        prepare_mocked_popen("../data/empty_vnx/storagegroup_list.xml")
        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        result = vnxCommAPIObj.get_storage_groups()
        self.assertEquals(result, [])

    #@skip
    def test_get_storage_group_empty_vnx(self):
        ''' test get_storage_group(sg_name) '''
        print self.shortDescription() 
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        prepare_mocked_popen("../data/empty_vnx/storagegroup_list_gname_'isitsg'.xml")
        vnxCommApiObj = VnxCommonApi(self.logger)
        vnxCommApiObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        myassert_raises_regexp(self, SanApiEntityNotFoundException,
                               "storagegroup command failed",
                               vnxCommAPIObj.get_storage_group, "dmax")



    #@skip
    def test_get_storage_pool_empty_vnx(self):
        ''' test get_storage_pool(sp_name='sp_name') on an empty vnx '''
        print self.shortDescription()
        prepare_mocked_popen("../data/empty_vnx/storagepool_list_name_'adamsonzs'.xml")
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        myassert_raises_regexp(self, SanApiEntityNotFoundException,
                               "Could not retrieve the specified",
                               vnxCommAPIObj.get_storage_pool, sp_name="at_pool")



    # -----------------------------------------------------------
    # get_lun can do one of the following sequences of navisec calls:
    # * getlun, lun -list
    # * lun -list
    # Each are tested below.



    #@skip
    def test_get_lun_by_name(self):
        ''' test get_lun() on empty vnx using lun_name'''
        print self.shortDescription()

        # Set up mocking
        _accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        outlist = [ DATADIR + "getlun.xml", DATADIR + "lun_list.xml" ]
        errlist = [ DATADIR + './empty.err', DATADIR + './empty.err' ]
        extlist = [ 0, 0 ]

        mokproc = MockProc(outlist, errlist, extlist)
        subprocess.Popen = mock.Mock(return_value=mokproc)

        # Perform the test
        vnx = VnxCommonApi(self.logger)
        vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, 
                                    self.scope, getcert=False, vcheck=False)

        myassert_raises_regexp(self, SanApiEntityNotFoundException,
                               "LUN not found: hello",
                               vnx.get_lun, lun_name="hello")



    #@skip
    def test_get_lun_by_id(self):
        ''' test get_lun() on empty vnx using lun_id'''
        print self.shortDescription()

        # Set up mocking
        _accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        outlist = [ DATADIR + "getlun.xml", DATADIR + "lun_list.xml" ]
        errlist = [ DATADIR + './empty.err', DATADIR + './empty.err' ]
        extlist = [ 0, 0 ]

        mokproc = MockProc(outlist, errlist, extlist)
        subprocess.Popen = mock.Mock(return_value=mokproc)

        # Perform the test
        vnx = VnxCommonApi(self.logger)
        vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, 
                                    self.scope, getcert=False, vcheck=False)

        myassert_raises_regexp(self, SanApiEntityNotFoundException,
                               "LUN not found: 22",
                               vnx.get_lun, lun_id="22")


    # -----------------------------------------------------------
    # get_luns can do one of the following sequences of navisec calls:
    # * listsg, getlun, lun -list
    # * getlun, lun -list
    # * lun -list
    # Each are tested below.  

    #@skip
    def test_get_luns(self):
        ''' test get_luns() on empty vnx, with no arguments '''
        print self.shortDescription()

        # Set up mocking
        _accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        outlist = [ DATADIR + "getlun.xml",
                    DATADIR + "lun_list.xml" ] 
        errlist = [ DATADIR + './empty.err', 
                    DATADIR + './empty.err' ]
        extlist = [ 0, 0 ]

        mokproc = MockProc(outlist, errlist, extlist)
        subprocess.Popen = mock.Mock(return_value=mokproc)

        # Perform the test
        vnx = VnxCommonApi(self.logger)
        vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                                    self.scope, getcert=False, vcheck=False)

        luns = vnx.get_luns()
        self.assertEquals(luns, [])


    #@skip
    def test_get_luns_storage_pool(self):
        ''' test get_luns() on empty vnx, with container_type=storage_pool'''
        print self.shortDescription()

        # Set up mocking
        _accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        outlist = [ DATADIR + "lun_list.xml" ]
        errlist = [ DATADIR + './empty.err' ]
        extlist = [ 0 ]

        mokproc = MockProc(outlist, errlist, extlist)
        subprocess.Popen = mock.Mock(return_value=mokproc)

        # Perform the test
        vnx = VnxCommonApi(self.logger)
        vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                                    self.scope, getcert=False, vcheck=False)

        luns = vnx.get_luns(container_type='StoragePool')
        self.assertEquals(luns, [])

    #@skip
    def test_get_luns_with_sg_name1(self):
        ''' test get_luns() on empty vnx, supplying a sg name '''
        print self.shortDescription()

        # Set up mocking
        _accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        outlist = [ DATADIR + "storagegroup_list_gname_'isitsg'.xml",
                    DATADIR + "getlun.xml",
                    DATADIR + "lun_list.xml" ]
        errlist = [ DATADIR + './empty.err',
                    DATADIR + './empty.err',
                    DATADIR + './empty.err' ]
        extlist = [ 0, 0, 0 ]

        mokproc = MockProc(outlist, errlist, extlist)
        subprocess.Popen = mock.Mock(return_value=mokproc)

        # Perform the test
        vnx = VnxCommonApi(self.logger)
        vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                                    self.scope, getcert=False, vcheck=False)

        myassert_raises_regexp(self, SanApiEntityNotFoundException,
                               "storagegroup command failed",
                               vnx.get_luns, sg_name="'isitsg'")



    #@skip
    def test_get_luns_with_sg_name2(self):
        ''' test get_luns() on empty vnx, supplying a sg name, where sg exists but no luns '''
        print self.shortDescription()

        # Set up mocking
        _accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        outlist = [ DATADIR + "../list_sg_atsfs43_44.xml", 
                    DATADIR + "getlun.xml",
                    DATADIR + "lun_list.xml" ]
        errlist = [ DATADIR + './empty.err',
                    DATADIR + './empty.err',
                    DATADIR + './empty.err' ]
        extlist = [ 0, 0, 0 ]

        mokproc = MockProc(outlist, errlist, extlist)
        subprocess.Popen = mock.Mock(return_value=mokproc)

        # Perform the test
        vnx = VnxCommonApi(self.logger)
        vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                                    self.scope, getcert=False, vcheck=False)

        luns = vnx.get_luns(sg_name='atsfs43_44')
        self.assertEquals(luns, [])



    #@skip
    def test_get_hba_port_info(self):
        ''' test get_hba_port_info on empty vnx '''
        print self.shortDescription()

        # Set up mocking
        _accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        outlist = [ DATADIR + "./port_list_hba.xml" ]
        errlist = [ DATADIR + "./port_list_hba.err" ] 
        extlist = [ 0 ]

        mokproc = MockProc(outlist, errlist, extlist)
        subprocess.Popen = mock.Mock(return_value=mokproc)

        # Perform the test
        vnx = VnxCommonApi(self.logger)
        vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                                    self.scope, getcert=False, vcheck=False)

        hbas = vnx.get_hba_port_info(host='host1', sp_port='1')
        self.assertEquals(hbas, [])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
