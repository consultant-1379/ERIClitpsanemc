'''
Created on 27 Jun 2014

@author: edavmax
'''
import unittest
from sanapi import api_builder, SanApi, get_api_version
from mock import patch, Mock
from vnxcommonapi import VnxCommonApi
from sanapiinfo import LunInfo
from sanapiexception import SanApiException, SanApiConnectionException, \
    SanApiCommandException, SanApiCriticalErrorException
import logging
import xml.etree.ElementTree as ET
from vnxparser import VnxParser
from testfunclib import *
import mock
import sanapilib
import sanapicfg
import time
import os
import os.path
import glob
from testfunclib import *
import datetime
import subprocess


class Test(unittest.TestCase):

    def setUp(self):
        # create a VnxCommonApi object
        self.ref_navicmd = "/opt/Navisphere/bin/naviseccli"
        self.spa = "1.2.3.4"
        self.spb = "1.2.3.5"
        self.adminuser = "admin"
        self.adminpasswd = "shroot12"
        self.cmdokxml1 = "../data/rglun.xml.cmdok"
        self.cmdokxml2 = "../data/splun.xml.cmdok"
        self.cmdnokxml1 = "../data/rglun.xml.cmdnok"
        self.cmdbadxml1 = "../data/rglun.xml.badxml"
        self.cmdbadxmlnoprops = "../data/rglun.xml.badxmlnoprops"
        self.cmdbadxmlnoparams = "../data/rglun.xml.badxmlnoparams"
        self.scope = "global"
        self.timeout = "50"
        self.logger = logging.getLogger("sanapitest")
        self.logger.setLevel(logging.DEBUG)
        self.parser = VnxParser()
        self.apilogdir = "/var/log/sanapi"
        self.apilogfile = 'sanapi' + "." + time.strftime("%Y_%m_%d") + ".log"
        self.apilogfilepath = self.apilogdir + "/" + self.apilogfile

    def tearDown(self):
            # deletes each file in the apidir    
            r = glob.glob(self.apilogdir + "\*")
            for i in r:
                try:
                    os.remove(i)
                    print "apilogfile: " + i + " removed"
                except:
                    print "*Warning* - unable to delete tmp file", i

    def test_navicmdcheckinitgoodargs(self):
        ''' test vnxcommon initialise with valid args '''
        print self.shortDescription()
        vnx_common = VnxCommonApi(self.logger)

        vnx_common.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                          self.scope, getcert = False, vcheck = False)
        
        vnx_common.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                          "local", getcert = False, vcheck = False)
        
        vnx_common.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                          "0", getcert = False, vcheck = False)
        
        vnx_common.initialise((self.spa, self.spb), self.adminuser, self.adminpasswd,
                          "1", getcert = False, vcheck = False)

        vnx_common.initialise((self.spa, ), self.adminuser, self.adminpasswd,
                          "0", getcert=False, vcheck=False)
     
        vnx_common.initialise((self.spa, ), self.adminuser, self.adminpasswd,
                          "0", getcert=False, vcheck=False, esc_pwd=True)

    
    def test_navicmdcheckinitbadargs(self):
        ''' test vnxcommon constructor checks bad arguments properly '''
        print self.shortDescription()
        vnx_common = VnxCommonApi(self.logger)

        # bad spa ip
        self.assertRaises(SanApiException, vnx_common.initialise, ("0.0.0",
                          self.spb), self.adminuser, self.adminpasswd,
                          self.scope, getcert = False, vcheck = False)
        # bad spb ip
        self.assertRaises(SanApiException, vnx_common.initialise,
                          (self.spa, "foobar"), self.adminuser,
                          self.adminpasswd, self.scope, getcert = False, vcheck = False)
        # blank username
        self.assertRaises(SanApiException, vnx_common.initialise,
                          (self.spa, self.spb), "", self.adminpasswd, self.scope, getcert = False, vcheck = False)
        # blank password
        self.assertRaises(SanApiException, vnx_common.initialise,
                          (self.spa, self.spb), self.adminuser, "", self.scope, getcert = False, vcheck = False)
        
        # invalid scope
        self.assertRaises(SanApiException, vnx_common.initialise,
                          (self.spa, self.spb), self.adminuser, self.adminpasswd, "foo", getcert = False, vcheck = False)

    def test_navicmdsucceeded(self):
        ''' test navicmd can handle XML resp from naviseccli indicating \
        cmd succeeded '''
        print self.shortDescription()

        mock_popen = prepare_mocked_popen(self.cmdokxml1, None, 0)
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck = False)
        navi_subcmd = "getlun 5"

        expected_cmd = self.ref_navicmd + " -h " + self.spa + " -User " + \
            "\"" + self.adminuser + "\"" + " -Password " + self.adminpasswd + \
            " -timeout " + self.timeout + " -Scope " + self.scope + \
            " -xml  " + navi_subcmd

        vnxCommAPIObj._navisec(navi_subcmd)
        mock_popen.assert_called_with(expected_cmd, shell=True,
                                      stderr=-1, stdout=-1, stdin=-1)

    def test_navicmdfailedwithconnerr(self):
        ''' test navicmd raises SanApiConnectionException when connection fails'''
        print self.shortDescription()
        popen_patcher = patch('vnxcommonapi.subprocess.Popen')
        mock_popen = popen_patcher.start()
        # communicate() returns [STDOUT, STDERR]
        mock_rv = Mock()
        mock_rv.communicate.return_value = ["navi error occured", ""]
        mock_popen.return_value = mock_rv
        mock_popen.return_value.returncode = 255
        navi_subcmd = "getlun 5"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = mock.Mock(return_value=0)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)
        self.assertRaises(SanApiConnectionException, vnxCommAPIObj._navisec,
                          navi_subcmd)
        mock_popen = popen_patcher.stop()

    def test_navicmdfailednonconnerr(self):
        ''' test navicmd raises SanApiOperationFailedException
        when navicmd fails to an unexpected error (not an 
        connection issue)'''
        print self.shortDescription()
        popen_patcher = patch('vnxcommonapi.subprocess.Popen')
        mock_popen = popen_patcher.start()
        # communicate() returns [STDOUT, STDERR]
        mock_rv = Mock()
        mock_rv.communicate.return_value = ["command not found", ""]
        mock_popen.return_value = mock_rv
        mock_popen.return_value.returncode = 127
        navi_subcmd = "getlun 9"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = mock.Mock(return_value=0)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)
        self.assertRaises(SanApiOperationFailedException, vnxCommAPIObj._navisec,
                          navi_subcmd)
        mock_popen = popen_patcher.stop()
        
    def test_navicmdfailedwithcmderr(self):
        ''' test navicmd can handle XML resp from naviseccli indicating cmd\
         failed '''
        print self.shortDescription()
        popen_patcher = patch('vnxcommonapi.subprocess.Popen')
        mock_popen = popen_patcher.start()
        with open(self.cmdnokxml1, "r") as myfile:
            data = myfile.read()
        mock_rv = Mock()
        # communicate() returns [STDOUT, STDERR]
        mock_rv.communicate.return_value = [data, "stderr\n"]
        mock_popen.return_value = mock_rv
        mock_popen.return_value.returncode = 0
        navi_subcmd = "getlun 5"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)
        self.assertRaises(SanApiCommandException, vnxCommAPIObj._navisec,
                          navi_subcmd)

    def test_navicmdhandlebadxmlresp(self):
        ''' test navicmd can handle manformed XML resp from naviseccli '''
        print self.shortDescription()
        popen_patcher = patch('vnxcommonapi.subprocess.Popen')
        mock_popen = popen_patcher.start()
        with open(self.cmdbadxml1, "r") as myfile:
            data = myfile.read()
        mock_rv = Mock()
        # communicate() returns [STDOUT, STDERR]
        mock_rv.communicate.return_value = [data, "stderr\n"]
        mock_popen.return_value = mock_rv
        mock_popen.return_value.returncode = 0
        navi_subcmd = "getlun 5"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)
        self.assertRaises(SanApiCommandException, vnxCommAPIObj._navisec,
                          navi_subcmd)

    def test_navicmdhandlebadxmlnoprops(self):
        ''' test navicmd can handle valid XML but without <PROPERTY> tags '''
        print self.shortDescription()
        popen_patcher = patch('vnxcommonapi.subprocess.Popen')
        mock_popen = popen_patcher.start()
        with open(self.cmdbadxmlnoprops, "r") as myfile:
            data = myfile.read()
        mock_rv = Mock()
        # communicate() returns [STDOUT, STDERR]
        mock_rv.communicate.return_value = [data, "stderr\n"]
        mock_popen.return_value = mock_rv
        mock_popen.return_value.returncode = 0
        navi_subcmd = "getlun 5"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope, vcheck=False)
        self.assertRaises(SanApiCommandException, vnxCommAPIObj._navisec,
                          navi_subcmd)

    def test_create_dict_goodxml(self):
        ''' test create_xml can handle valid XML '''
        print self.shortDescription()

        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = Mock(return_value=0)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope,vcheck=False)

        tree = ET.parse(self.cmdokxml1)
        etree = tree.getroot()
        lun_name = "sfs29342936_ci_free_15"
        rg_id = "17"

        # TODO: changed for parser - to test
        # parsed_dictio = vnxCommAPIObj._VnxCommonApi__create_dict(etree)
        parsed_dictio = self.parser.create_dict(etree)

        self.assertEqual(parsed_dictio["Name"], lun_name)
        self.assertEqual(parsed_dictio["RAIDGroup ID"], rg_id)

    def test_create_dict_noparams(self):
        ''' test create_dict can handle valid XML but without <PARAMVALUE>\
         tags '''
        print self.shortDescription()
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = mock.Mock(return_value=0)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope,vcheck=False)
        tree = ET.parse(self.cmdbadxmlnoparams)
        etree = tree.getroot()

        # TODO: changed for parser - to test
        # created_dictio = vnxCommAPIObj._VnxCommonApi__create_dict(etree)
        created_dictio = self.parser.create_dict(etree)
        self.assertEqual(len(created_dictio.keys()), 0,
                         "unexpected created_dictio size")

    def test_createvnxobject_with_invalid_scope(self):
        vnx_common_api = VnxCommonApi(self.logger)
        self.assertRaises(SanApiCriticalErrorException,
                          vnx_common_api.initialise, (self.spa, self.spb),
                          self.adminuser, self.adminpasswd, "invalid scope", vcheck = False)

    def test_initialise_vnxobject_with_invalid_ips(self):
        vnx_common_api = VnxCommonApi(self.logger)
        self.assertRaises(SanApiCriticalErrorException,
                          vnx_common_api.initialise, "ip_spa", "ipb",
                          "username", "password", "scope", vcheck = False)

    def test_initialise_vnxobject_with_invalid_scope(self):
        vnx_common_api = VnxCommonApi(self.logger)
        self.assertRaises(SanApiCriticalErrorException,
                          vnx_common_api.initialise, (self.spa, self.spb),
                          "username", "password", "scope", vcheck = False)

    @patch('subprocess.Popen')
    @patch.object(VnxCommonApi, '_navisec')

    def test_get_hw_san_navisec_exception(self, mock_navisec, mock_popen):
        mock_process = Mock()
        mock_process.communicate.return_value = (b'05/29/2024\n',b'')
        mock_popen.return_value = mock_process
        mock_navisec.side_effect = SanApiException("Test Exception message", 1)
        checker = VnxCommonApi()
        result = checker.get_hw_san_alerts()
        msg = "Error checking if anything on the SAN has Hardware Errors," \
              " please check manually through the GUI"
        self.assertEqual(result, msg)

    @patch('subprocess.Popen')
    @patch.object(VnxCommonApi, '_navisec')

    def test_get_hw_san_alerts__onlyHwerrmon(self, mock_navisec, mock_popen):
        mock_process = Mock()
        mock_process.communicate.return_value = (b'05/29/2024\n',b'')
        mock_popen.return_value = mock_process
        with open("../data/test_hw_san_alerts_onlyHwerrmon.txt",'r') as file:
            output=file.read()
        mock_navisec.return_value = output
        checker = VnxCommonApi()
        result = checker.get_hw_san_alerts()
        self.assertIsNone(result)

    @patch('subprocess.Popen')
    @patch.object(VnxCommonApi, '_navisec')

    def test_no_errors_after_reboot(self, mock_navisec, mock_popen):
        mock_process = Mock()
        mock_process.communicate.return_value = (b'05/29/2024\n',b'')
        mock_popen.return_value = mock_process
        with open("../data/test_no_errors_after_reboot.txt",'r') as file:
            output=file.read()
        mock_navisec.return_value = output
        checker = VnxCommonApi()
        result = checker.get_hw_san_alerts()
        self.assertIsNone(result)

    @patch('subprocess.Popen')
    @patch.object(VnxCommonApi, '_navisec')

    def test_without_spreboot_output(self, mock_navisec, mock_popen):
        mock_process = Mock()
        mock_process.communicate.return_value = (b'05/29/2024\n',b'')
        mock_popen.return_value = mock_process
        with open("../data/test_without_spreboot.txt",'r') as file:
            output=file.read()
        mock_navisec.return_value = output
        checker = VnxCommonApi()
        result = checker.get_hw_san_alerts()
        with open("../data/test_without_spreboot_output.txt",'r') as file:
            o=file.read()
        actual_res = o.split('\n')
        self.assertEqual(result,actual_res)

    @patch('subprocess.Popen')
    @patch.object(VnxCommonApi, '_navisec')

    def test_get_hw_san_alerts_success(self, mock_navisec, mock_popen):
        mock_process = Mock()
        mock_process.communicate.return_value = (b'05/29/2024\n',b'')
        mock_popen.return_value = mock_process
        with open("../data/test_get_hw_san_alerts_log1.txt",'r') as file:
            output=file.read()
        mock_navisec.return_value = output
        checker = VnxCommonApi()
        result = checker.get_hw_san_alerts()
        with open("../data/test_get_hw_san_alerts_test1.txt",'r') as file:
            o=file.read()
        actual_res = o.split('\n')
        self.assertEqual(result,actual_res)

    def test_get_hw_san_alerts(self):
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = Mock(return_value=0)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                            self.adminpasswd, self.scope, vcheck=False)
        date_str= "05/13/2024"
        original_date = datetime.datetime.strptime(date_str, "%m/%d/%Y")
        one_day = datetime.timedelta(days=1)
        two_weeks= datetime.timedelta(weeks=2)
        before_date = original_date - two_weeks
        after_date = original_date + one_day
        before_date_str = before_date.strftime("%m/%d/%Y")
        after_date_str = after_date.strftime("%m/%d/%Y")
        self.assertEqual(before_date_str, "04/29/2024")
        self.assertEqual(after_date_str, "05/14/2024")
        self.assertEqual(one_day, datetime.timedelta(1))
        self.assertEqual(two_weeks, datetime.timedelta(14))
        self.assertEqual(before_date, datetime.datetime(2024, 4, 29, 0, 0))
        self.assertEqual(after_date, datetime.datetime(2024, 5, 14, 0, 0))

    def test_get_hw_san_alerts_no_errors_before_reboot(self):
        with open("../data/test_no_errors_before_reboot.txt",'r') as file:
            output=file.read()
        lines = output.split('\n')
        target_keyword = 'RebootSP'
        last_occurrence_index = -1
        for index, line in enumerate(lines):
            if target_keyword.lower() in line.lower():
                last_occurrence_index = index
        if last_occurrence_index != -1:
            output_lines = lines[last_occurrence_index:]
        else:
            output_lines = lines
        res = [line for line in output_lines if ('HwErrMon' in line and 'DIMM_ECC' in line)]
        self.assertEqual(res,[])

    def test_etree_from_ouptut_raises_appropriate_exception(self):
        ''' test _etree_from_ouptut raises appropriate exception '''
        print self.shortDescription()
        splun_name_already_exists_xml = "../data/splunnamealreadyexists.xml"
        splun_id_already_exists_xml = "../data/splunidalreadyexists.xml"
        rg_lun_already_exists_xml = "../data/rglunalreadyexists.xml"
        rg_lun_non_existing_xml = "../data/non_existing_lun_getlun.xml"
        sp_lun_non_existing_xml_by_name = "../data/non_existing_lun_lunlistbyname.xml"
        sp_lun_non_existing_xml_by_id = "../data/non_existing_lun_lunlistbyid.xml"
        sg_non_existing = "../data/non_existing_sg_by_name.xml"
        rg_non_existing = "../data/non_existing_rg.xml"
        sp_non_existing_by_name = "../data/non_existing_storagepoolbyname.xml"
        sp_non_existing_by_id = "../data/non_existing_storagepoolbyid.xml"
        sp_already_exists = "../data/storagepool_already_exists.xml"
        sg_already_exists = "../data/storagegroup_already_exists.xml"
        sg_hlu_already_exists = "../data/storagegroup_hlu_already_exists.xml"
        rg_already_exists = "../data/raidgroup_already_exists.xml"
        sg_hlu_non_existing = "../data/storagegroup_nonexisting_hlu.xml"
        snap_name_already_exists = "../data/snapshot_name_already_exists.xml"
        snap_lun_not_existing = "../data/snapshot_resource_not_existing.xml"
        
        outdata1 = get_test_file_data(splun_name_already_exists_xml)
        errormsg1 = "Unable to create the LUN because the specified name is already in use"
        vnxCommAPIObj = VnxCommonApi(self.logger)
        vnxCommAPIObj._accept_and_store_cert = mock.Mock(return_value=0)
        vnxCommAPIObj.initialise((self.spa, self.spb), self.adminuser,
                                 self.adminpasswd, self.scope,vcheck=False)
        # sp lun with name already exists
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg1, \
                    vnxCommAPIObj._etree_from_output, outdata1)
        
        # sp lun with id already exists
        outdata2 = get_test_file_data(splun_id_already_exists_xml)
        errormsg2 = "Physical unit already exists"
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg2, \
                    vnxCommAPIObj._etree_from_output, outdata2)
        
        # rg lun with id already exists
        outdata3 = get_test_file_data(rg_lun_already_exists_xml)
        errormsg3 = "bind command failed\nLUN already exists"
       
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg3, \
                    vnxCommAPIObj._etree_from_output, outdata3)
        
        
        # rg LUN does not exist
        outdata4 = get_test_file_data(rg_lun_non_existing_xml)
        errormsg4 = "Error: getlun command failed\nInvalid LUN number\nLUN does not exist"
        
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg4, \
                    vnxCommAPIObj._etree_from_output, outdata4)
        
        # sp LUN by name does not exist
        outdata5 = get_test_file_data(sp_lun_non_existing_xml_by_name)
        errormsg5 = "Could not retrieve the specified \(pool lun\). The \(pool lun\) may not exist"
       
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg5, \
                    vnxCommAPIObj._etree_from_output, outdata5)
        
        # sp LUN by id does not exist
        outdata6 = get_test_file_data(sp_lun_non_existing_xml_by_id)
        errormsg6 = "Could not retrieve the specified \(pool lun\). The \(pool lun\) may not exist"
       
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg6, \
                    vnxCommAPIObj._etree_from_output, outdata6)
        
        # storage group does not exist
        outdata7 = get_test_file_data(sg_non_existing)
        errormsg7 = "Error: storagegroup command failed\nThe group name or UID does not match any storage groups for this array"
       
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg7, \
                    vnxCommAPIObj._etree_from_output, outdata7)
        
        # raid group does not exist
        outdata8 = get_test_file_data(rg_non_existing)
        errormsg8 = "Error: getrg command failed\nRAIDGroup Not Found"
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg8, \
                    vnxCommAPIObj._etree_from_output, outdata8)
        
        # sp by name does not exist
        outdata9 = get_test_file_data(sp_non_existing_by_name)
        errormsg9 = "Could not retrieve the specified \(Storagepool\). The \(Storagepool\) may not exist"
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg9, \
                    vnxCommAPIObj._etree_from_output, outdata9)
        
        # sp by id does not exist
        outdata10 = get_test_file_data(sp_non_existing_by_id)
        errormsg10 = "Could not retrieve the specified \(Storagepool\). The \(Storagepool\) may not exist"
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg10, \
                    vnxCommAPIObj._etree_from_output, outdata10)
        
        # storage pool already exists
        outdata11 = get_test_file_data(sp_already_exists)
        errormsg11 = "Pool name is already used"
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg11, \
                    vnxCommAPIObj._etree_from_output, outdata11)
        
        # storage group already exists
        outdata12 = get_test_file_data(sg_already_exists)
        errormsg12 = "Error: storagegroup command failed\nError returned from Agent\nStorage Group name already in use"
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg12, \
                    vnxCommAPIObj._etree_from_output, outdata12)
        
        # storage group HLU already exists
        outdata13 = get_test_file_data(sg_hlu_already_exists)
        errormsg13 = "Error: storagegroup command failed\nError returned from Agent\nRequested LUN has already been added to this Storage Group"
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg13, \
                    vnxCommAPIObj._etree_from_output, outdata13)
        
        # raid group already exists
        outdata14 = get_test_file_data(rg_already_exists)
        errormsg14 = "Error: createrg command failed\nError returned from Agent\nRAID Group by that ID already exists"
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg14, \
                    vnxCommAPIObj._etree_from_output, outdata14)
        
        # storage group hlu does not exist
        outdata15 = get_test_file_data(sg_hlu_non_existing)
        #vnxCommAPIObj._etree_from_output( outdata15)
        errormsg15 = "Error: storagegroup command failed\nError returned from Agent\nLUN 99 : No such Host LUN in this Storage Group"
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg15, \
                    vnxCommAPIObj._etree_from_output, outdata15)
        
        # snapshot by name already exists
        outdata16 = get_test_file_data(snap_name_already_exists)
        errormsg16 = "The specified snapshot name is already in use"
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, errormsg16, \
                    vnxCommAPIObj._etree_from_output, outdata16)
        
        # snapshot lun resource does not exist
        outdata17 = get_test_file_data(snap_lun_not_existing)
        errormsg17 = "Cannot create the snapshot. The specified resource does not exist"
        #vnxCommAPIObj._etree_from_output( outdata17)
        myassert_raises_regexp(self, SanApiEntityNotFoundException, errormsg17, \
                    vnxCommAPIObj._etree_from_output, outdata17)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
        
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
