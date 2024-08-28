'''
Created on 9 Jul 2014

@author: edavmax
'''
import unittest
import os
import sys
from sanapilib import *
from sanapicfg import *
from testfunclib import *
import logging


class Test(unittest.TestCase):

    def setUp(self):
        tst_dir=os.path.dirname(__file__)
        if tst_dir:
            tst_dir+="/"
        sanapi_inifile=tst_dir + "../../main/etc/sanapi.ini"
        if sys.platform == "win32":
            sanapi_inifile=os.path.normpath(sanapi_inifile)
        cfg=SanApiCfg()
        cfg.load_file(sanapi_inifile)

    def tearDown(self):
        pass


    #@skip
    def test_validate_ipv4(self):
        ''' test for validate_ipv4 utility function ()  '''
        print self.shortDescription()
        self.assertTrue(validate_ipv4("1.2.3.4"))
        self.assertFalse(validate_ipv4("1.2.3"))
        self.assertFalse(validate_ipv4("300.2.3.4"))
        self.assertFalse(validate_ipv4("300.2.3.4"))

    #@skip
    def test_is_valid_raidtype(self):
        ''' test for is_valid_raidtype() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_raidtype("0"))
        self.assertTrue(is_valid_raidtype("1"))
        self.assertTrue(is_valid_raidtype("10"))
        self.assertFalse(is_valid_raidtype("foo"))
        self.assertFalse(is_valid_raidtype(None))

    def test_is_valid_unity_raidtype(self):
        ''' test for is_valid__unity_raidtype() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_unity_raidtype("5"))
        self.assertTrue(is_valid_unity_raidtype("1"))
        self.assertTrue(is_valid_unity_raidtype("10"))
        self.assertFalse(is_valid_unity_raidtype("foo"))
        self.assertFalse(is_valid_unity_raidtype(None))

    #@skip
    def test_is_valid_size(self):
        ''' test for is_valid_size() utility function '''
        print self.shortDescription()

        self.assertTrue(is_valid_size("500mb"))
        self.assertTrue(is_valid_size("500Mb"))
        self.assertTrue(is_valid_size("500mB"))
        self.assertTrue(is_valid_size("500gb"))
        self.assertTrue(is_valid_size("500GB"))
        self.assertTrue(is_valid_size("1.5TB"))
        self.assertFalse(is_valid_size(500))
        self.assertFalse(is_valid_size("500"))
        self.assertFalse(is_valid_size("s500"))
        self.assertFalse(is_valid_size("-1"))
        self.assertFalse(is_valid_size("bananna"))
        self.assertFalse(is_valid_size("500euro"))
        self.assertFalse(is_valid_size("500 mb"))
        self.assertFalse(is_valid_size("500q"))
        self.assertFalse(is_valid_size("1..5TB"))
        self.assertFalse(is_valid_size(None))

    #@skip
    def test_is_valid_lunname(self):
        ''' test for is_valid_lunname() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_lunname("lun1"))
        self.assertTrue(is_valid_lunname("lun_tor123"))
        self.assertTrue(is_valid_lunname("lun 124"))

    #@skip
    def test_is_valid_sp(self):
        ''' test for is_valid_sp() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_sp("a"))
        self.assertTrue(is_valid_sp("A"))
        self.assertTrue(is_valid_sp("B"))
        self.assertTrue(is_valid_sp("b"))
        self.assertFalse(is_valid_sp(None))
        self.assertFalse(is_valid_sp("sdsfg dsd "))

    #@skip
    def test_is_valid_lun_type(self):
        ''' test for is_valid_lun_type() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_lun_type("Thin"))
        self.assertTrue(is_valid_lun_type("thick "))
        self.assertTrue(is_valid_lun_type("thin"))
        self.assertTrue(is_valid_lun_type("thick"))
        self.assertTrue(is_valid_lun_type("THIN"))
        self.assertTrue(is_valid_lun_type("THICK"))
        self.assertFalse(is_valid_lun_type(None))
        self.assertFalse(is_valid_lun_type("medium"))

    #@skip
    def test_is_valid_lunid(self):
        ''' test for is_valid_lunid() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_lunid("auto"))
        self.assertTrue(is_valid_lunid("Auto"))
        self.assertTrue(is_valid_lunid("AUTO"))
        self.assertTrue(is_valid_lunid("45"))
        self.assertTrue(is_valid_lunid("90"))
        self.assertFalse(is_valid_lunid(None))
        self.assertFalse(is_valid_lunid("90b"))
        self.assertFalse(is_valid_lunid("fred"))

    #@skip
    def test_is_valid_sp_port(self):
        ''' test for is_valid_sp_port() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_sp_port("0"))
        self.assertTrue(is_valid_sp_port("4"))
        self.assertTrue(is_valid_sp_port("7"))
        self.assertTrue(is_valid_sp_port(7))
        self.assertFalse(is_valid_sp_port("A"))
        self.assertFalse(is_valid_sp_port("-1"))
        self.assertFalse(is_valid_sp_port("fred"))

    #@skip
    def test_is_valid_arraycommpath(self):
        ''' test for is_valid_arraycommpath() utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_arraycommpath("0"))
        self.assertTrue(is_valid_arraycommpath("1"))
        self.assertFalse(is_valid_arraycommpath("33"))

    #@skip
    def test_is_valid_failover_mode(self):
        ''' test for is_valid_failover_mode utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_failover_mode("0"))
        self.assertTrue(is_valid_failover_mode("1"))
        self.assertTrue(is_valid_failover_mode("4"))
        self.assertFalse(is_valid_failover_mode("33"))
        self.assertFalse(is_valid_failover_mode("-1"))
        self.assertFalse(is_valid_failover_mode("fred"))


    #@skip
    def test_convert_size_to_vnx(self):
        ''' test for convert_size_to_vnx() utility function '''
        print self.shortDescription()
        size, size_q = convert_size_to_vnx("500Mb")
        self.assertEquals(size, "500")
        self.assertEquals(size_q, "mb")
        size, size_q = convert_size_to_vnx("500gB")
        self.assertEquals(size, "500")
        self.assertEquals(size_q, "gb")
        size, size_q = convert_size_to_vnx("500tb")
        self.assertEquals(size, "500")
        self.assertEquals(size_q, "tb")
        size, size_q = convert_size_to_vnx("500gb")
        self.assertEquals(size, "500")
        self.assertEquals(size_q, "gb")
        self.assertRaises(SanApiOperationFailedException, convert_size_to_vnx, "500 bytes")

    #@skip
    def test_convert_raid_type_to_vnx(self):
        ''' test for convert_raid_type_to_vnx() utility function '''
        print self.shortDescription()
        vnx_rt = convert_raid_type_to_vnx("1","pool")
        self.assertEquals(vnx_rt, "r_1")
        vnx_rt = convert_raid_type_to_vnx("10","pool")
        self.assertEquals(vnx_rt, "r_10")
        self.assertRaises(SanApiCriticalErrorException, convert_raid_type_to_vnx, "103", "pool")

        vnx_rt = convert_raid_type_to_vnx("1","lun")
        self.assertEquals(vnx_rt, "r1")
        vnx_rt = convert_raid_type_to_vnx("10","lun")
        self.assertEquals(vnx_rt, "r1_0")
        self.assertRaises(SanApiCriticalErrorException, convert_raid_type_to_vnx, "103", "lun")

    def test_convert_raid_type_to_unity(self):
        ''' test for convert_raid_type_to_unity() utility function '''
        print self.shortDescription()
        unity_rt = convert_raid_type_to_unity(5, "pool")
        self.assertEquals(unity_rt, 1)
        unity_rt = convert_raid_type_to_unity(10, "pool")
        self.assertEquals(unity_rt, 7)
        unity_rt = convert_raid_type_to_unity(1, "pool")
        self.assertEquals(unity_rt, 3)
        unity_rt = convert_raid_type_to_unity(6, "pool")
        self.assertEquals(unity_rt, 10)

    #@skip
    def test_convert_lun_type_to_vnx(self):
        ''' test for convert_lun_type_to_vnx() utility function '''
        print self.shortDescription()
        vnx_lt = convert_lun_type_to_vnx("thick")
        self.assertEquals(vnx_lt, "nonThin")
        vnx_lt = convert_lun_type_to_vnx("thin")
        self.assertEquals(vnx_lt, "Thin")
        vnx_lt = convert_lun_type_to_vnx("THICK")
        self.assertEquals(vnx_lt, "nonThin")
        self.assertRaises(SanApiCriticalErrorException, convert_lun_type_to_vnx, "medium")

    #@skip
    def test_is_valid_wwn(self):
        ''' test for test_is_valid_wwn utility function '''
        print self.shortDescription()
        self.assertTrue(is_valid_wwn("50:01:43:F0:18:70:94:89:50:01:43:80:18:D0:94:88"))
        self.assertTrue(is_valid_wwn("A0:01:43:80:18:f0:94:89:50:01:43:80:18:70:94:88"))
        #  not long enough
        self.assertFalse(is_valid_wwn("50:01:43:80:18:f0:94:89:50:01"))
        #  invalid characters
        self.assertFalse(is_valid_wwn("A0:01:43:80:18:X0:94:89:50:01:43:80:18:70:YY:88"))
        #  missing parts
        self.assertFalse(is_valid_wwn("A0:01:43:80::X0:94:89:50:01:43:80::70:YY:88"))
        #  trailing ':'
        self.assertFalse(is_valid_wwn("A0:01:43:80::X0:94:89:50:01:43:80::70:YY:88:"))
        # total garbage
        self.assertFalse(is_valid_wwn("fruity"))

    def test_is_valid_uuid(self):
        ''' test for is_valid_uuid utility function '''
        print self.shortDescription()
        data = [('5cbb0b9e-d50c-4076-be0e-cc5c77df3534', True),
                ('60:05:08:b1:00:1c:6b:f1:43:c5:d4:43:20:e4:c3:82', True),
                ('60:06:01:60:35:00:3D:00:E5:30:78:D4:EC:77:EE:11', True),
                ('60:06:01:60:35:00:3D:00:E5:30:78:D4:EC:77:EE:11:10', False),
                ('5cbb0b9e-d50c-4076-be0e-58a0-cc5c77df3534', False)]
        for (uuid, expected) in data:
            self.assertEqual(is_valid_uuid(uuid), expected)

    #@skip
    def test_validate_valid_string(self):
        '''Test to validate a valid string'''
        print self.shortDescription()
        try:
            validate_string("hello")
        except SanApiOperationFailedException:
            self.fail("Shouldn't throw an exception with a valid string")

    #@skip
    def test_validate_invalid_string_with_invalid_param(self):
        '''Test to validate an invalid string'''
        print self.shortDescription()
        self.assertRaises(SanApiOperationFailedException, validate_string, 1)


    #def test_validate_valid_int_or_string_with_int(self):
    #    '''Test to validate a valid string'''
    #    print self.shortDescription()
    #    validated = validate_int_or_string_as_string(123)
    #    self.assertEqual(validated, "123")

    #def test_validate_validate_int_or_string_with_string(self):
    #    '''Test to validate a valid string'''
    #    print self.shortDescription()
    #    validated = validate_int_or_string_as_string("123")
    #    self.assertEqual(validated, "123")

    #def test_validate_valid_int_or_string_with_invalid_param(self):
    #    '''Test to validate an invalid string'''
    #    print self.shortDescription()
    #    self.assertRaises(SanApiOperationFailedException, validate_int_or_string_as_string, ['aaa'])

    #def test_validate_valid_int_or_string_as_int(self):
    #    ''' Test validate_valid_int_or_string_as_int '''
    #    print self.shortDescription()
    #    self.assertEqual(validate_int_or_string_as_int(123), 123)
    #    self.assertEqual(validate_int_or_string_as_int("123"), 123)
    #    self.assertRaises(SanApiOperationFailedException, validate_int_or_string_as_int, "foo")


    #@skip
    def test_validate_param_duration_with_invalid_parameters(self):
        '''Test to validate a duration with an wrong parameters.'''
        print self.shortDescription()
        self.assertRaises(SanApiOperationFailedException, validate_snap_duration, 123)
        self.assertRaises(SanApiOperationFailedException, validate_snap_duration, "123")
        self.assertRaises(SanApiOperationFailedException, validate_snap_duration, "dddd")
        self.assertRaises(SanApiOperationFailedException, validate_snap_duration, "d123d")

    #@skip
    def test_validate_param_duration(self):
        ''' Test to validate a duration with some valid parameters '''
        self.assertTrue(validate_snap_duration("123d"))
        self.assertTrue(validate_snap_duration("123m"))
        self.assertTrue(validate_snap_duration("123h"))
        self.assertTrue(validate_snap_duration("123y"))

    #@testfunclib.skip
    #@skip
    def test_raise_appropriate_exception_pos(self):
        ''' test test_raise_appropriate_exception with various valid inputs '''
        print self.shortDescription()
        my_msg = "Oops LUN already exists!"

        # check known navi error raises exception
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, my_msg, \
                    raise_appropriate_exception, "Error: bind command failed\nLUN already exists", \
                    my_msg)

        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, my_msg, \
                    raise_appropriate_exception, "Unable to create the LUN because the specified name is already in use", \
                    my_msg)

        # check original error message can be included in new exception
        myassert_raises_regexp(self, SanApiEntityAlreadyExistsException, my_msg + " Original NavisecCLI error:", \
                    raise_appropriate_exception, "Unable to create the LUN because the specified name is already in use", \
                    my_msg, include_navi_errmsg=True)

        # check unknown navi error raises default exception
        myassert_raises_regexp(self, SanApiException, my_msg, \
                    raise_appropriate_exception, "Never before seen navi error!", \
                    my_msg)

        # check unknown navi error raises user-supplied default exception
        myassert_raises_regexp(self, SanApiCriticalErrorException, my_msg, \
                    raise_appropriate_exception, "Never before seen navi error!", \
                    my_msg, SanApiCriticalErrorException)

        # check similar but unknown navi error raises user-supplied default exception
        myassert_raises_regexp(self, SanApiCriticalErrorException, my_msg, \
                    raise_appropriate_exception, "bind command failed", \
                    my_msg, SanApiCriticalErrorException)

        # check unknown navi error raises user-supplied default exception
        myassert_raises_regexp(self, SanApiCriticalErrorException, my_msg, \
                    raise_appropriate_exception, "Never before seen navi error!", \
                    my_msg, SanApiCriticalErrorException)

    #@testfunclib.skip
    #@skip
    def test_raise_appropriate_exception_neg(self):
        ''' test test_raise_appropriate_exception with various invalid inputs '''
        print self.shortDescription()
        my_msg = "Oops LUN already exists!"

        class SanApiNonExistingExceptionType:
            pass

        # missing navi_error
        myassert_raises_regexp(self, SanApiCriticalErrorException, "NavisecCLI error message not specified", \
                    raise_appropriate_exception, None, my_msg)

        # missing sanapi error
        myassert_raises_regexp(self, SanApiCriticalErrorException, "SANAPI error message not specified", \
                    raise_appropriate_exception, "Error: bind command failed LUN already exists", None)

        # unknown default exception type
        myassert_raises_regexp(self, TypeError, "this constructor takes no arguments", \
                    raise_appropriate_exception, "Never before seen navi error", my_msg, SanApiNonExistingExceptionType)

    def test_validate_lun_create(self):
        "Test if the _validate_lun_create method returns formated params"
        print self.shortDescription()

        lun_params = validate_lun_create("lun123", "500tb",
                "Raid Group", "63", "B", "10",
                "thick", "auto", False, "", logging.getLogger("test"))
        params = ["lun_name", "size",
                "container_type", "container",
                "storage_processor", "raid_type",
                "lun_type", "lun_id", "ignore_thresholds",
                "array_specific_options"]
        for param in params:
            self.assertTrue(param in lun_params)
        self.assertEqual(lun_params["container_type"], "RaidGroup")
        self.assertEqual(lun_params["raid_type"], "r1_0")
        self.assertTrue(lun_params["size_num"])
        self.assertTrue(lun_params["size_q"])
        self.assertEqual(lun_params["vnx_lun_type"], "nonThin")

    def test_shell_escape(self):
        ''' Test strings are escaped correctly '''
        print self.shortDescription()
        test_str = '''hello"`$'(\\)!~#<>&*;| goodbye'''
        expected_escapes = '''hello\\"\\`\\$\\\'\\(\\\\\\)\\!\\~\\#\\<\\>\\&\\*\\;\\|\\ goodbye'''
        self.assertEqual(shell_escape(test_str), expected_escapes)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
