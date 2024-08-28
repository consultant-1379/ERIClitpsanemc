'''
Created on 4 Aug 2014

@author: edavmax
'''
import unittest
from mock import patch, Mock, MagicMock
import sys
#sys.path.append(".")
from vnxcommonapi import VnxCommonApi
from sanapiinfo import LunInfo
from sanapiexception import SanApiCriticalErrorException, SanApiOperationFailedException, SanApiCommandException
import logging
import logging.handlers
import testfunclib
import xml.etree.ElementTree as ET


class Test(unittest.TestCase):


    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd="/opt/Navisphere/bin/naviseccli"
        self.spa="1.2.3.4"
        self.spb="1.2.3.5"
        self.adminuser="admin"
        self.adminpasswd="shroot12"
        self.scope="Global"
        self.cmdokxml1="../data/hba_port_list.xml.cmdok"
        self.empty_port_list_xml="../data/hba_port_list.xml.empty_port_list"
        self.hba_without_port="../data/hba_port_list.xml.hba_without_ports"
        #self.cmdokxml1="../data/foo.xml"
        
        # setup logging with threshold of WARG
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)

    def tearDown(self):
        pass

    #@testfunclib.skip
    def test_get_hba_port_info_pos(self):
        ''' postitive tests for get_hba_port_info  '''
        print self.shortDescription() 
        tree = ET.parse(self.cmdokxml1)
        etree = tree.getroot()
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        
        # get all hbas
        hbainfos=vnxCommAPIObj.get_hba_port_info()
        self.assertEquals(len(hbainfos), 158)
        
        myhost="atrcxb2262"
        myhost_ip="10.45.225.254"
        atrcxb2262_wwn1="50:01:43:80:16:7D:C3:D9:50:01:43:80:16:7D:C3:D8"
        atrcxb2262_wwn2="50:01:43:80:16:7D:C3:DB:50:01:43:80:16:7D:C3:DA"
        
        # search by host name
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost)
        self.assertEquals(len(hbainfos), 8)
        
        # search by host ip
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost_ip)
        self.assertEquals(len(hbainfos), 8)
        
        # search by host and storage processor
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost, storage_processor="A")
        self.assertEquals(len(hbainfos), 4)
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost_ip, storage_processor="B")
        self.assertEquals(len(hbainfos), 4)
        
        # search by host and sp_port
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost, sp_port="1")
        self.assertEquals(len(hbainfos), 2)
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost_ip, sp_port="1")
        self.assertEquals(len(hbainfos), 2)
        
        # search by host and storage processor and port
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost, storage_processor="A", sp_port="0")
        self.assertEquals(len(hbainfos), 1)
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=myhost, storage_processor="B", sp_port="0")
        self.assertEquals(len(hbainfos), 1)
        hbainfo=hbainfos[0]
        self.assertEqual(hbainfo.hbauid, atrcxb2262_wwn1)
        self.assertEqual(hbainfo.spname, "B")
        self.assertEqual(hbainfo.spport, "0")
        self.assertEqual(hbainfo.hbaname, myhost)
        self.assertEqual(hbainfo.hbaip, myhost_ip)
        
        # search by wwn
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=atrcxb2262_wwn1)
        self.assertEquals(len(hbainfos), 4)
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=atrcxb2262_wwn2)
        self.assertEquals(len(hbainfos), 4)
        
        # search by wwn and sp
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=atrcxb2262_wwn1, storage_processor="A")
        self.assertEquals(len(hbainfos), 2)
        
        # search by wwn and sp_port
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=atrcxb2262_wwn1, sp_port="0")
        self.assertEquals(len(hbainfos), 2)
        
        # search by wwn and host and sp and sp_port
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=atrcxb2262_wwn1, storage_processor="A", sp_port="0")
        self.assertEquals(len(hbainfos), 1)
        hbainfo=hbainfos[0]
        self.assertEqual(hbainfo.hbauid, atrcxb2262_wwn1)
        self.assertEqual(hbainfo.spname, "A")
        self.assertEqual(hbainfo.spport, "0")
        self.assertEqual(hbainfo.hbaname, myhost)
        self.assertEqual(hbainfo.hbaip, myhost_ip)
        
        
        my_nonexistinghost="chaos_manor"
        my_nonexisting_wwn="50:01:43:80:16:7D:C3:D9:50:01:43:80:16:7D:99:99"
        
        # search for non-existing host
        hbainfos=vnxCommAPIObj.get_hba_port_info(host=my_nonexistinghost)
        self.assertEquals(len(hbainfos), 0)
        
        # search for non-existing wwn
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=my_nonexisting_wwn)
        self.assertEquals(len(hbainfos), 0)
        
        # existing wwn with non-existing port
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=atrcxb2262_wwn1, sp_port="7")
        self.assertEquals(len(hbainfos), 0)
        
        
        
    #@testfunclib.skip   
    def test_get_hba_port_info_badargs(self):
        ''' test behaviour of get_hba_port_info when passed invalid parameters '''
        print self.shortDescription() 
        myhost="atrcxb2262"
        invalid_wwn="50:01:43:80::C3:DB:50:01:43:80:16:7D:C3:DA"
        
        tree = ET.parse(self.cmdokxml1)
        etree = tree.getroot()
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid WWN:", vnxCommAPIObj.get_hba_port_info, wwn=invalid_wwn) 
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid storage processor", vnxCommAPIObj.get_hba_port_info, host=myhost, storage_processor="C") 
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid storage processor port:", vnxCommAPIObj.get_hba_port_info, host=myhost, sp_port="BAD") 
        
    #@testfunclib.skip   
    def test_get_hba_port_info_invalid_combination(self):
        ''' test behaviour of get_hba_port_info when invalid combination of parameters is given'''
        print self.shortDescription() 
        myhost="atrcxb2262"
        mywwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        tree = ET.parse(self.cmdokxml1)
        etree = tree.getroot()
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException,  \
                                           "Invalid combination of parameters to get_hba_port_info", \
                                           vnxCommAPIObj.get_hba_port_info, wwn=mywwn, host=myhost) 
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException,  \
                                           "Invalid combination of parameters to get_hba_port_info", \
                                           vnxCommAPIObj.get_hba_port_info, storage_processor="A") 
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException,  \
                                           "Invalid combination of parameters to get_hba_port_info", \
                                           vnxCommAPIObj.get_hba_port_info, sp_port="0") 
        
    #@testfunclib.skip   
    def test_get_hba_port_info_empty_port_list(self):
        ''' test behaviour of get_hba_port_info when no port list info in xml '''
        print self.shortDescription() 
        tree = ET.parse(self.empty_port_list_xml)
        etree = tree.getroot()
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        hbainfos=vnxCommAPIObj.get_hba_port_info()
        self.assertEquals(len(hbainfos), 0)
        
    #@testfunclib.skip   
    def test_get_hba_port_info_hba_without_portinfo(self):
        ''' test behaviour of get_hba_port_info when hba record exists without associated port info '''
        print self.shortDescription() 
        mywwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        tree = ET.parse(self.hba_without_port)
        etree = tree.getroot()
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj._navisec = MagicMock(name="_navisec", return_value=etree)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        hbainfos=vnxCommAPIObj.get_hba_port_info(wwn=mywwn)
        self.assertEquals(len(hbainfos), 0)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
