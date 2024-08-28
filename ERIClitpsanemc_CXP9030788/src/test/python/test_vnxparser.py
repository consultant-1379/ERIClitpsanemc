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
from vnxparser import *


class Test(unittest.TestCase):
    """
    Test class for vnxparser
    """

    def setUpVnx(self):
        # Setup array object

        self.vnx = VnxCommonApi(self.logger)
        self.vnx._accept_and_store_cert = MagicMock(name="_accept_and_store_cert")
        self.vnx.initialise((self.spa, self.spb), self.adminuser, \
                       self.adminpasswd, self.scope, vcheck=False)

    def setUp(self):

        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.scope = "global"
        self.timeout = "60"
        self.luncmdokxml1 = '../data/lunlist.xml.cmdok'
        self.hbacmdokxml1="../data/hba_port_list.xml.cmdok"
        self.hbacmdokinvalidxml1="../data/hba_port_list.xml_invalid_wwn"
        self.hbacmdokinvalidxml2="../data/hba_port_list.xml_invalid_sp"
        self.hbacmdokinvalidxml3="../data/hba_port_list.xml_invalid_spport"
        
        #self.logger = None
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.WARN)

    def tearDown(self):
        pass

    """
    DICT CREATE TESTS
    """

    """
    def create_dict(self, etree): - TODO


    def create_dicts(self, etree, delim): - done
    """


    def get_meta_dict(self):
        """meta dict for create object list - used by several parser tests"""
        parser = VnxParser()
        delim = "LOGICAL UNIT NUMBER "
        et = ET.parse('../data/lunlist.xml.cmdok')
        meta_dict = parser.create_dicts(et, delim)
        return meta_dict

    #@skip
    def test_create_dict(self):
        """test create_dict ok"""   
        self.setUpVnx()
        parser = VnxParser()
        et = ET.parse('../data/storage_pool_getbyname_ok_response.xml')

        navi_dict = parser.create_dict(et)

        #print d
        try:
            name = navi_dict['Pool Name']
            spid = navi_dict['Pool ID']
            raid = navi_dict['Raid Type']
            size = navi_dict['User Capacity (GBs)']
            avail = navi_dict['Available Capacity (GBs)']
        except Exception, exce:
            self.fail("Exception %s while retrieving dictionary items" % exce)
 
        self.assertEqual(name, 'TORD7', "name incorrect") 
        self.assertEqual(spid, '5', "spid incorrect")
        self.assertEqual(raid, 'r_6', "raid incorrect")
        self.assertEqual(size, '3205.248', "size incorrect")
        self.assertEqual(avail, '1662.240', "avail incorrect")

    #@skip
    def test_create_dict_with_non_etree(self):
        """test_create_dict where non etree parameters are passed"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()

        self.assertRaises(SanApiOperationFailedException, parser.create_dict, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_dict, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_dict, [1,2,3])
 
    #@skip
    def test_create_object_list(self):
        """test_create_object_list ok"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        delim = "LOGICAL UNIT NUMBER "

        meta_dict = self.get_meta_dict()

        lunlist = parser.create_object_list(meta_dict, 
                                   parser.create_lun_from_lunlist_dict) 

        for item in lunlist:
            if item.id == '208':
                break

        self.assertEqual(item.uid, '60:06:01:60:6F:D0:2E:00:E8:D2:3F:04:00:9B:E3:11', "tested object attribute not correct")

        expected_len = 34
        actual_len = len(lunlist)
        self.assertEqual (expected_len, actual_len, "Number of objects in dict incorrect, should be %s, is %s " \
                                      % (expected_len, actual_len))
        
    def test_small_lun_handled(self):
        """ test LUN of small size is handled by parser """
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        delim = "LOGICAL UNIT NUMBER "

        et = ET.parse('../data/small_sp_lun.xml')
        meta_dict = parser.create_dicts(et, delim)

        lun = parser.create_object_list(meta_dict, 
                                   parser.create_lun_from_lunlist_dict) [0]
                                   
        self.assertEqual(lun.size, "10")

 
    #@skip
    def test_create_object_list_function_wrong_params(self):
        """test_create_object_list where passed function has wrong number of params"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        meta_dict = self.get_meta_dict()

        self.assertRaises(SanApiOperationFailedException, parser.create_object_list, meta_dict, two_args_function)
  
    #@skip
    def test_create_object_list_non_function_arg(self):
        """test_create_object_list where passed non function argument"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        meta_dict = self.get_meta_dict()

        self.assertRaises(SanApiOperationFailedException, parser.create_object_list, meta_dict, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_object_list, meta_dict, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_object_list, meta_dict, [1,2,3])


    #@skip
    def test_create_object_list_non_dict(self):
        """test_create_object_list where non dictionary is passed"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()

        self.assertRaises(SanApiOperationFailedException, parser.create_object_list, None, parser.create_lun_from_lunlist_dict)
        self.assertRaises(SanApiOperationFailedException, parser.create_object_list, "String", parser.create_lun_from_lunlist_dict)
        self.assertRaises(SanApiOperationFailedException, parser.create_object_list, [1,2,3], parser.create_lun_from_lunlist_dict)


    """
    LUN TESTS
    """

    #@skip
    def test_create_dicts_from_getlun(self):
        """test_create_dicts ok using getlun etree"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        delim = "LOGICAL UNIT NUMBER"
        et = ET.parse('../data/getlun.xml.cmdok')

        meta_dict = parser.create_dicts(et, delim) 

        obj_list = []
        for dictkey in meta_dict:
            sub_dict = meta_dict[dictkey]
            obj = parser.create_lun_from_get_lun_dict(sub_dict)
            obj_list.append(obj)

        expected_len = 214
        actual_len = len(obj_list) 
        self.assertEqual (expected_len, actual_len, "Number of objects in dict incorrect, should be %s, is %s " \
                                      % (expected_len, actual_len))

        for item in obj_list:
            if item.id == '4050':
                break

        self.assertEqual(item.uid, '60:06:01:60:6F:D0:2E:00:3E:0D:53:75:01:B5:E3:11', "tested object attribute not correct")
        #TODO: more validation once raid code is fixed, compare objects

    #@skip
    def test_create_dicts_from_listlun(self):
        """ test_create_dicts_from_listlun """
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        delim = "LOGICAL UNIT NUMBER "
        et = ET.parse('../data/lunlist.xml.cmdok')

        meta_dict = parser.create_dicts(et, delim)

        obj_list = []
        for dictkey in meta_dict:
            sub_dict = meta_dict[dictkey]
            obj = parser.create_lun_from_lunlist_dict(sub_dict)
            obj_list.append(obj)

        expected_len = 34
        actual_len = len(obj_list)
        self.assertEqual (expected_len, actual_len, "Number of objects in dict incorrect, should be %s, is %s " \
                                      % (expected_len, actual_len))

        for item in obj_list:
            if item.id == '208':
                break

        self.assertEqual(item.uid, '60:06:01:60:6F:D0:2E:00:E8:D2:3F:04:00:9B:E3:11', "tested object attribute not correct")
        #TODO: more validation once raid code is fixed, compare objects

    ''' todo fixme '''
    @skip
    def test_create_dicts_bad_delim(self):
        """test_create_dicts_bad_delim"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        delim = "THIS WILL NOT MATCH "
        et = ET.parse('../data/lunlist.xml.cmdok')

        self.assertRaises(SanApiOperationFailedException, parser.create_dicts, et, delim) 


    ''' todo fixme '''
    @skip
    def test_create_dicts_wrong_objects(self):
        """test_create_dicts_wrong_objects"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        delim = "LOGICAL UNIT NUMBER "
        et = ET.parse('../data/lunlist.xml.cmdok')
        

        #self.assertRaises(SanApiOperationFailedException, parser.create_dicts, et, delim)

        # Wrong delimiter type
        self.assertRaises(SanApiOperationFailedException, parser.create_dicts, et, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_dicts, et, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_dicts, et, [1,2,3])


        # Wrong etree type
        self.assertRaises(SanApiOperationFailedException, parser.create_dicts, None, delim)
        self.assertRaises(SanApiOperationFailedException, parser.create_dicts, "String", delim)
        self.assertRaises(SanApiOperationFailedException, parser.create_dicts, [1,2,3], delim)




    #@skip
    def test_create_lun_from_lunlist_dict(self):
        """test_create_lun_from_lunlist_dict OK"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        lundict = getLunListDict()
        reflun = getLunListObject()

        #
        retlun = parser.create_lun_from_lunlist_dict(lundict)
        self.assertEqual (retlun, reflun, "LUN incorrect. Showing test result LUN followed by expected LUN pool\n%s\n%s" \
                            % (retlun.consumed, reflun.consumed))

    #@skip
    def test_create_lun_from_lunlist_dict_missing_keys (self):
        """test_create_lun_from_lunlist_dict fails because of missing keys"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        lundict = getLunListDict()

        keylist = [ 'LOGICAL UNIT NUMBER ', 'Name', 'UID', 'Pool Name', 'User Capacity (GBs)', 'Raid Type' ]

        for key in keylist:
           test_dict = dict(lundict)
           del test_dict[key]
           self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_lunlist_dict, test_dict)

    #@skip
    def test_create_lun_from_lunlist_dict_wrong_object(self):
        """Attempt to create lun with non-dictionary objects"""
        print self.shortDescription()

        self.setUpVnx()
        parser = VnxParser()

        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_lunlist_dict, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_lunlist_dict, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_lunlist_dict, [1,2,3])

    #@skip
    def test_create_lun_from_lunlist_dict_using_getlun_dict(self):
        """test_create_lun_from_lunlist_dict using get lun dict"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        lundict = getGetLunDict()
        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_lunlist_dict, lundict)

    #@skip
    def test_create_lun_from_get_lun_dict(self):
        """test_create_lun_from_get_lun_dict OK"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        lundict = getGetLunDict()
        reflun = getLunGetObject()
        retlun = parser.create_lun_from_get_lun_dict(lundict)

        self.assertEqual (retlun, reflun, "LUN incorrect. Showing test result LUN followed by expected LUN pool\n%s\n%s" \
                            % (retlun, reflun))

    #@skip
    def test_create_lun_from_get_lun_dict_missing_keys (self):
        """test_create_lun_from_get_lun_dict fails because of missing keys"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        lundict = getGetLunDict()

        keylist =[ 'LOGICAL UNIT NUMBER', 'Name', 'UID', 'RAIDGroup ID', 'LUN Capacity(Megabytes)', 'RAID Type' ]

        for key in keylist:
           test_dict = dict(lundict)
           del test_dict[key]
           self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_get_lun_dict, test_dict)

    #@skip
    def test_create_lun_from_get_lun_dict_wrong_object(self):
        """Attempt to create lun with non-dictionary objects"""
        print self.shortDescription()

        self.setUpVnx()
        parser = VnxParser()

        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_get_lun_dict, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_get_lun_dict, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_get_lun_dict, [1,2,3])

    #@skip
    def test_create_lun_from_get_lun_dict_using_lunlist_dict(self):
        """test_create_lun_from_get_lun_dict using lun list dict"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        lundict = getLunListDict()
        self.assertRaises(SanApiOperationFailedException, parser.create_lun_from_get_lun_dict, lundict)


    """
    SP TESTS
    """

    #@skip
    def test_create_spinfo_from_dict(self):
        """Test create_sp_list_ok - converting dictionary into sginfo  """
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        sgp = getSpDict()
        referenceSP = getSP()

        # Tested method
        returnedSP = parser.create_spinfo_from_dict(sgp)

        self.assertEqual (returnedSP, referenceSP, "Storage Pool incorrect.  Showing test result pool followed by expected storage pool\n%s\n%s" \
                             % ( returnedSP, referenceSP) )

    # Negative tests
    #@skip
    def test_create_spinfo_from_dict_missing_keys(self):
        """Attempt to create spinfo with dictionary missing keys"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()
        spd = getSpDict()

        keylist = [ 'Pool Name', 'Pool ID', 'Raid Type', 'User Capacity (GBs)', 'Available Capacity (GBs)' ]

        for key in keylist:
           test_spd = dict(spd)
           del test_spd[key]
           self.assertRaises(SanApiOperationFailedException, parser.create_spinfo_from_dict, test_spd)

    #@skip
    def test_create_spinfo_from_dict_wrong_object(self):
        """Attempt to create spinfo with non-dictionary objects"""
        print self.shortDescription()

        self.setUpVnx()

        parser = VnxParser()

        self.assertRaises(SanApiOperationFailedException, parser.create_spinfo_from_dict, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_spinfo_from_dict, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_spinfo_from_dict, [1,2,3])

    """ 
    SG TESTS
    """

    """
    Test create_sginfo_from_dict
    """

    #@skip
    def test_create_sginfo_from_dict(self):
        """Test create_sg_info_from_dict OK  - converting dictionary into sginfo  """
        print self.shortDescription()

        self.setUpVnx()

        parser = VnxParser()

        sgd = getSgDict()

        referenceSG = getPairsSG() 

        # Tested method
        returnedSG = parser.create_sginfo_from_dict(sgd) 

        self.assertEqual (returnedSG,referenceSG, "Storage Group incorrect.  Showing test result group followed by expected storage group\n%s\n%s" \
                             % ( returnedSG, referenceSG) ) 



    #@skip
    def test_create_sginfo_from_dict_no_lists(self):
        """Test create_sg_info_from_dict OK - converting dictionary into sginfo where there are no hba/sp pairs or hlu/alu pairs  """
        print self.shortDescription()

        self.setUpVnx()

        parser = VnxParser()

        sgd = getSgDictWithoutLists()

        referenceSG = getSG()

        # Tested method
        returnedSG = parser.create_sginfo_from_dict(sgd)

        self.assertEqual (returnedSG,referenceSG, "Storage Group incorrect.  Showing test result group followed by expected storage group\n%s\n%s" \
                             % ( returnedSG, referenceSG) )


    # Negative tests
    #@skip
    def test_create_sginfo_from_dict_missing_keys(self):
        """Attempt to create sginfo with dictionary missing keys"""
        print self.shortDescription()

        self.setUpVnx()

        parser = VnxParser()

        sgd = getSgDict() 

        keylist = [ 'Storage Group Name', 'Storage Group UID', 'Shareable' ]
        for key in keylist:
            test_sgd = dict(sgd)
            del test_sgd[key]
            self.assertRaises(SanApiOperationFailedException, parser.create_sginfo_from_dict, test_sgd)


    #@skip
    def test_create_sginfo_from_dict_wrong_object(self):
        """Attempt to create sginfo with non-dictionary objects"""
        print self.shortDescription()

        self.setUpVnx()

        parser = VnxParser()

        self.assertRaises(SanApiOperationFailedException, parser.create_sginfo_from_dict, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_sginfo_from_dict, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_sginfo_from_dict, [1,2,3])

    """
    Test create_sg_list
    """
    #@skip
    def test_create_sg_list_ok_single_sg(self):
        """Create SG list for single SG"""
        print self.shortDescription()

        self.setUpVnx()

        parser = VnxParser()

        et = ET.parse('../data/list_sg_atsfs43_44.xml')

        referenceSG = getPairsSG()

   
        # Let's not mock the create_sginfo method 
        #parser.create_sginfo_from_dict = MagicMock(name = "create_sginfo_from_dict", return_value = referenceSG )
        sgl = parser.create_sg_list(et) 
      
        # list should only contain 1 object
        self.assertEqual(len(sgl), 1) 

        returnedSG = sgl[0] 

        self.assertEqual (returnedSG,referenceSG, "Storage Group incorrect.  Showing test result group followed by expected storage group\n%s\n%s" \
                             % ( returnedSG, referenceSG) )


    #@skip
    def test_create_sg_list_ok_multiple_sg(self):
        """Create SG list for single SG"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()

        et = ET.parse('../data/list_sgs.xml')

        sgl = parser.create_sg_list(et)

        # 8 Storage Groups in data file
        self.assertEqual(len(sgl), 8) 

        referenceSG = getPairsSG()

        for returnedSG in sgl:
            if returnedSG.name == referenceSG.name:
                break

        self.assertEqual (returnedSG,referenceSG, "Storage Group incorrect.  Showing test result group followed by expected storage group\n%s\n%s" \
                             % ( returnedSG, referenceSG) )


    #@skip
    def test_create_sg_list_from_wrong_xml(self):
        """Attempt Create SG list with wrong XML"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()

        et = ET.parse('../data/rglun.xml.cmdok')
        sglist=parser.create_sg_list(et)
        self.assertEqual(len(sglist), 0)
        #self.assertRaises(SanApiOperationFailedException, parser.create_sg_list, et)


    #@skip
    def test_create_sg_list_from_wrong_object(self):
        """Attempt Create SG list with wrong objects"""
        print self.shortDescription()
        self.setUpVnx()
        parser = VnxParser()

        self.assertRaises(SanApiOperationFailedException, parser.create_sg_list, None)
        self.assertRaises(SanApiOperationFailedException, parser.create_sg_list, "String")
        self.assertRaises(SanApiOperationFailedException, parser.create_sg_list, [1,2,3])
        
    #@skip   
    def test_get_sub_etree_good_xml(self):
        ''' test behaviour of get_sub_etree when xml which contains no instances of delim is passed '''
        print self.shortDescription() 
        delim="LOGICAL UNIT NUMBER "
        self.setUpVnx()
        parser = VnxParser()
        # pass in wrong xml - i.e. does not contain HBA UID delim
        tree = ET.parse(self.luncmdokxml1)
        etree = tree.getroot()
        sub_etrees=parser.get_sub_etree_list(etree, delim)
        self.assertEquals(len(sub_etrees), 34)
        sub_etree=sub_etrees[0]
        self.assertEquals(len(sub_etree.getroot().getchildren()), 30)
        param=sub_etree.findall('.//PARAMVALUE')[0]
        self.assertEquals(param.attrib['NAME'], delim)
        self.assertEquals(param.find('VALUE').text, '4063')
        
    #@skip   
    def test_get_sub_etree_good_xml_split_again(self):
        ''' check the output of get_sub_etree can itself be split on a delimiter  '''
        print self.shortDescription() 
        delim1="HBA UID"
        delim2="    SP Name"
        self.setUpVnx()
        parser = VnxParser()
        # pass in wrong xml - i.e. does not contain HBA UID delim
        tree = ET.parse(self.hbacmdokxml1)
        etree = tree.getroot()
        sub_etrees=parser.get_sub_etree_list(etree, delim1)
        self.assertEquals(len(sub_etrees), 52)
        sub_etree=sub_etrees[0]
        sub_sub_etrees=parser.get_sub_etree_list(sub_etree, delim2)
        self.assertEquals(len(sub_sub_etrees), 2)
        sub_sub_etree=sub_sub_etrees[0]
        param=sub_sub_etree.findall('.//PARAMVALUE')[0]
        self.assertEquals(param.attrib['NAME'], delim2)
        self.assertEquals(param.find('VALUE').text, 'SP A')
       
    #@skip   
    def test_get_sub_etree_no_delimiter(self):
        ''' test behaviour of get_sub_etree when xml containing no instances of delim is passed '''
        print self.shortDescription() 
        self.setUpVnx()
        parser = VnxParser()
        # pass in wrong xml - i.e. does not contain HBA UID delim
        tree = ET.parse(self.luncmdokxml1)
        etree = tree.getroot()
        sub_etrees=parser.get_sub_etree_list(etree, "HBA UID")
        self.assertEquals(len(sub_etrees), 0)
        #myassert_raises_regexp(self, SanApiOperationFailedException, "Invalid XML stream", parser.get_sub_etree_list, etree, "HBA UID") 

        
    #@skip   
    def test_get_sub_etree_list_blank_xml(self):
        ''' test behaviour of get_sub_etree when blank xml passed '''
        print self.shortDescription() 
        self.setUpVnx()
        parser = VnxParser()
        myassert_raises_regexp(self, SanApiOperationFailedException, "Invalid XML stream", parser.get_sub_etree_list, None, "HBA UID") 
        
    #@skip   
    def test_create_hba_init_info_list_good_xml(self):
        ''' test behaviour of create_hba_init_info_list when valid xml is passed '''
        print self.shortDescription() 
        self.setUpVnx()
        parser = VnxParser()
        tree = ET.parse(self.hbacmdokxml1)
        etree = tree.getroot()
        hba_info_list=parser.create_hba_init_info_list(etree)
        self.assertEquals(len(hba_info_list), 158)
        
    #@skip   
    def test_create_hba_init_info_list_bad_xml(self):
        ''' test behaviour of create_hba_init_info_list when xml with invalid wwn is passed '''
        print self.shortDescription() 
        self.setUpVnx()
        parser = VnxParser()
        tree = ET.parse(self.hbacmdokinvalidxml1)
        etree = tree.getroot()
        myassert_raises_regexp(self, SanApiOperationFailedException, "Invalid WWN", parser.create_hba_init_info_list, etree) 
        tree = ET.parse(self.hbacmdokinvalidxml2)
        etree = tree.getroot()
        myassert_raises_regexp(self, SanApiOperationFailedException, "Unrecognised storage processor name", parser.create_hba_init_info_list, etree) 
        tree = ET.parse(self.hbacmdokinvalidxml3)
        etree = tree.getroot()
        myassert_raises_regexp(self, SanApiOperationFailedException, "Invalid storage processor port", parser.create_hba_init_info_list, etree) 
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

