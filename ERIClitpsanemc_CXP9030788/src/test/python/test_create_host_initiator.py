'''
Created on 9 Jul 2014

@author: edavmax
'''
import unittest
from mock import patch, Mock, MagicMock
import sys
#sys.path.append(".")
from vnxcommonapi import VnxCommonApi
from sanapiinfo import LunInfo, HbaInitiatorInfo, HluAluPairInfo, StorageGroupInfo
from sanapiexception import SanApiException, SanApiConnectionException, SanApiCommandException, \
                    SanApiCriticalErrorException, SanApiOperationFailedException
import logging
import logging.handlers
import xml.etree.ElementTree as ET
import testfunclib


class Test(unittest.TestCase):


    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd="/opt/Navisphere/bin/naviseccli"
        self.spa="1.2.3.4"
        self.spb="1.2.3.5"
        self.adminuser="admin"
        self.adminpasswd="shroot12"
        self.createluncmdok="../data/createluninsp.xml.cmdok"
        self.getluncmdok="../data/getlun.xml.cmdok"
        self.listluncmdok="../data/lunlist.xml.cmdok"
        self.scope = "global"
        self.timeout="60" 
        # setup logging with threshold of WARNING
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)
        self.validhba="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        
    def setUpVnx(self):
        # Setup array object
        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")

        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope, vcheck = False)
    
    #@unittest.skip("") 
    def test_create_host_init_with_goodparams(self):
        ''' test create_host_initiator with good parameters '''
        print self.shortDescription() 
        vnxCommAPIObj = VnxCommonApi(self.logger)  
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck = False)
        vnxCommAPIObj.create_host_initiator("sg123", "atrcxb2112", "1.2.3.4", self.validhba, "a", "0")
        self.assertEquals(vnxCommAPIObj._navisec.call_count, 1)
        vnxCommAPIObj._navisec.assert_called_once_with("storagegroup -setpath -o -gname \"sg123\" -hbauid " +  self.validhba + " -sp a -spport 0 -type 3 -host atrcxb2112 -ip 1.2.3.4 -failovermode 4 -arraycommpath 1")
        
    #@unittest.skip("")     
    def test_create_host_init_returns_hbainfo(self):
        ''' tests create_host_init returns HbaInitiatorInfo object '''
        print self.shortDescription() 
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck = False)
        hbainfo=vnxCommAPIObj.create_host_initiator("sg123", "atrcxb2112", "1.2.3.4", self.validhba, "a", "0")
        testfunclib.myassert_is_instance(self, hbainfo, HbaInitiatorInfo)
        self.assertEquals(hbainfo.hbauid, self.validhba)
       
    #@unittest.skip("")        
    def test_create_host_init_with_badparams(self):
        ''' test create_host_initiator with bad parameters  '''
        print self.shortDescription() 
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._navisec = MagicMock(name="_navisec")
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck = False)
      
        # bad sg name
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid storage group name", \
                                           vnxCommAPIObj.create_host_initiator, None, "atrcxb2112", "1.2.3.4", self.validhba, "a", "0")
        # bad host name
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid host name", \
                                           vnxCommAPIObj.create_host_initiator, "sg123", None, "1.2.3.4", self.validhba, "a", "0")
        # bad ip address
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid ip address", \
                                           vnxCommAPIObj.create_host_initiator, "sg123", "atrcxb2112", "1.2.3.", self.validhba, "a", "0")
        # bad wwn
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid HBA WWN", \
                                           vnxCommAPIObj.create_host_initiator, "sg123", "atrcxb2112", "1.2.3.4", None, "a", "0")
        # bad storage processor
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid storage processor", \
                                        vnxCommAPIObj.create_host_initiator, "sg123", "atrcxb2112", "1.2.3.4", self.validhba, "C", "0")
        # bad sp port
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid SP Port Number", \
                                        vnxCommAPIObj.create_host_initiator, "sg123", "atrcxb2112", "1.2.3.4", self.validhba, "B", "BAD")
        # bad arraycommpath
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid arraycommpath value", \
                                        vnxCommAPIObj.create_host_initiator, "sg123", "atrcxb2112", "1.2.3.4", self.validhba, "B", "6", arraycommpath="3")
        # bad type
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid host initiator type", \
                                        vnxCommAPIObj.create_host_initiator, "sg123", "atrcxb2112", "1.2.3.4", self.validhba, "B", "6", init_type=None)
        # bad failover mode
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid failover mode", \
                                        vnxCommAPIObj.create_host_initiator, "sg123", "atrcxb2112", "1.2.3.4", self.validhba, "B", "6", failovermode="99")
        
    #@unittest.skip("")     
    def test_create_host_initiators_positive(self):
        ''' test create_host_initiators - positive '''
        print self.shortDescription() 
        wwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        arraycommpath='1'
        init_type='3'
        failovermode='4'
        array_specific_opts=''
        hba_init_list=[]
        hba_init_list.append(HbaInitiatorInfo(wwn, "A", "0", "atrcxb123", "10.45.224.252"))
        hba_init_list.append(HbaInitiatorInfo(wwn, "A", "1", "atrcxb123", "10.45.224.252"))
        hba_init_list.append(HbaInitiatorInfo(wwn, "B", "0", "atrcxb123", "10.45.224.252"))
        hba_init_list.append(HbaInitiatorInfo(wwn, "B", "1", "atrcxb123", "10.45.224.252"))
       
        hba_alupair_list = []
        hba_alupair_list.append(HluAluPairInfo("1", "1"))
        hba_alupair_list.append(HluAluPairInfo("2", "34"))
        
        sg_name = "sg123"

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_hba_port_info = MagicMock(name="get_hba_port_info", return_value=hba_init_list)
        vnxCommAPIObj.create_host_initiator = MagicMock(name="create_host_initiator")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck = False)
        storage_group_info = StorageGroupInfo(sg_name, "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", \
                                              True, hba_init_list, hba_alupair_list)
        vnxCommAPIObj.get_storage_group = MagicMock(name="get_storage_group", return_value=storage_group_info)
       
        storage_group_info = vnxCommAPIObj.create_host_initiators(sg_name, wwn)
        vnxCommAPIObj.get_storage_group.assert_called_once_with(sg_name)
        self.assertEquals(vnxCommAPIObj.create_host_initiator.call_count, 4)
      
        vnxCommAPIObj.create_host_initiator.assert_any_call('sg123', 'atrcxb123', '10.45.224.252', wwn, 'A', '1', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)
        vnxCommAPIObj.create_host_initiator.assert_any_call('sg123', 'atrcxb123', '10.45.224.252', wwn, 'A', '0', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)
        vnxCommAPIObj.create_host_initiator.assert_any_call('sg123', 'atrcxb123', '10.45.224.252', wwn, 'B', '1', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)
        vnxCommAPIObj.create_host_initiator.assert_any_call('sg123', 'atrcxb123', '10.45.224.252', wwn, 'B', '0', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)
        
        testfunclib.myassert_is_instance(self, storage_group_info, StorageGroupInfo)
        
    def test_create_host_initiators_with_badparams(self):
        ''' test create_host_initiators with bad parameters  '''
        print self.shortDescription() 
        
        wwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        my_host_name = "atrcxb123"
        my_host_ip = "1.2.3.4"
        sg_name = "sg_123"
        
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck = False)
        
        # bad sg name
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid storage group name", \
                                           vnxCommAPIObj.create_host_initiators, None, "atrcxb2112", wwn)
        
        # bad wwn
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, "Invalid HBA WWN", \
                                           vnxCommAPIObj.create_host_initiators, "sg123", "AA:BB:CC")
        
        # specify host name but not host ip
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, \
                                    "Cannot specify host name without host ip", 
                                     vnxCommAPIObj.create_host_initiators, sg_name, self.validhba, host_name=my_host_name)
        
        # specify host ip but not host name
        testfunclib.myassert_raises_regexp(self, SanApiCriticalErrorException, \
                                    "Cannot specify host ip without host name", 
                                     vnxCommAPIObj.create_host_initiators, sg_name, self.validhba, host_ip=my_host_ip)
        
    def test_create_host_initiators_no_port_list_info(self):
        ''' test create_host_initiators - wwn not in port list '''
        print self.shortDescription() 
        wwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        
        sg_name = "sg123"

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_hba_port_info = MagicMock(name="get_hba_port_info", return_value=None)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck = False)
        
        testfunclib.myassert_raises_regexp(self, SanApiOperationFailedException, \
                                    wwn + " does not appear in port list on VNX", 
                                     vnxCommAPIObj.create_host_initiators, sg_name, self.validhba)
        
    def test_create_host_initiators_bad_port_list(self):
        ''' test create_host_initiators - invalid port data returned '''
        print self.shortDescription() 
        wwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"

        hba_init_list=[]
        hba_init_list.append(HbaInitiatorInfo(wwn, None, "0", "atrcxb123", "10.45.224.252"))
       
       
        sg_name = "sg123"

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        vnxCommAPIObj.get_hba_port_info = MagicMock(name="get_hba_port_info", return_value=hba_init_list)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        
        testfunclib.myassert_raises_regexp(self, SanApiOperationFailedException, \
                                    "Invalid storage processor: None", 
                                     vnxCommAPIObj.create_host_initiators, sg_name, self.validhba)
        hba_init_list=[]
        hba_init_list.append(HbaInitiatorInfo(wwn, "B", "3", None, "10.45.224.252"))
        vnxCommAPIObj.get_hba_port_info.return_value = hba_init_list
        testfunclib.myassert_raises_regexp(self, SanApiOperationFailedException, \
                                    "Invalid host name:None", 
                                     vnxCommAPIObj.create_host_initiators, sg_name, self.validhba)
        
    def test_create_host_initiator(self):
        """test_create_host_initiator - names with spaces are handled correctly"""
        print self.shortDescription()

        self.setUpVnx()

        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)

        # Mock called functions as we are not interested in them, only the cmd string structure
        self.vnx.parser.create_sg_list = MagicMock(name = 'create_sg_list', return_value=None)


        name = "space here"
        host = "host1"
        ip = '1.2.3.4'
        hba = "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        sproc = 'a'
        sport = '0' 

        cmd_string = "storagegroup -setpath -o -gname \"%s\" -hbauid %s -sp %s -spport %s -type 3 -host %s -ip %s -failovermode 4 -arraycommpath 1" % \
                                 ( name, hba, sproc, sport, host, ip) 

        print "Verifying navisec is called with: %s" % cmd_string
        self.vnx.create_host_initiator(name, host, ip, hba, sproc, sport)
        self.vnx._navisec.assert_called_once_with(cmd_string)

    def test_create_host_initiators(self):
        """test_create_host_initiators - names with spaces are handled correctly"""
        print self.shortDescription()

        self.setUpVnx()
        # Mock navisec to check the cmd string constructed
        self.vnx._navisec = MagicMock(name = '_navisec', return_value=0)

        wwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E"
        arraycommpath='1'
        init_type='3'
        failovermode='4'
        array_specific_opts=''
        hba_init_list=[]
        hba_init_list.append(HbaInitiatorInfo(wwn, "A", "0", "atrcxb123", "10.45.224.252"))
        hba_init_list.append(HbaInitiatorInfo(wwn, "A", "1", "atrcxb123", "10.45.224.252"))
        hba_init_list.append(HbaInitiatorInfo(wwn, "B", "0", "atrcxb123", "10.45.224.252"))
        hba_init_list.append(HbaInitiatorInfo(wwn, "B", "1", "atrcxb123", "10.45.224.252"))

        hba_alupair_list = []
        hba_alupair_list.append(HluAluPairInfo("1", "1"))
        hba_alupair_list.append(HluAluPairInfo("2", "34"))

        name = "space here"

        self.vnx.get_hba_port_info = MagicMock(name="get_hba_port_info", return_value=hba_init_list)
        self.vnx.create_host_initiator = MagicMock(name="create_host_initiator")
        self.vnx.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd, self.scope, vcheck=False)
        storage_group_info = StorageGroupInfo(name, "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E", \
                                              True, hba_init_list, hba_alupair_list)
        self.vnx.get_storage_group = MagicMock(name="get_storage_group", return_value=storage_group_info)

        self.vnx.create_host_initiators(name, wwn)
        self.vnx.get_storage_group.assert_called_once_with(name)
        self.assertEquals(self.vnx.create_host_initiator.call_count, 4)

        self.vnx.create_host_initiator.assert_any_call(name, 'atrcxb123', '10.45.224.252', wwn, 'A', '1', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)
        self.vnx.create_host_initiator.assert_any_call(name, 'atrcxb123', '10.45.224.252', wwn, 'A', '0', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)
        self.vnx.create_host_initiator.assert_any_call(name, 'atrcxb123', '10.45.224.252', wwn, 'B', '1', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)
        self.vnx.create_host_initiator.assert_any_call(name, 'atrcxb123', '10.45.224.252', wwn, 'B', '0', \
                                                            arraycommpath, init_type, failovermode, array_specific_opts)

        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
