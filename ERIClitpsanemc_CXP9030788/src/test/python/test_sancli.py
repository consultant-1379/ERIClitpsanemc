'''
Created Apr 2015

@author: MR + LC
'''
import unittest
from sancli import SanCli
import logging
import logging.handlers
from sanapi import api_builder
import sys
from sanapilib import *
from HTMLParser import incomplete
from nose.plugins.skip import Skip
from nose import SkipTest

class Test(unittest.TestCase):

    def setUp(self):
        self.logger = None

    def create_valid_create_snap(self):
        sancli = SanCli()
        sancli.args['action'] = "create_snap"
        sancli.args['lun_name'] = "lun1"
        sancli.args['user'] = "admin"
        sancli.args['password'] = "pass"
        sancli.args['scope'] = "Global"
        sancli.args['snap_name'] = "snap1"
        sancli.args['array'] = "vnx1"
        sancli.args['log_level'] = "Info"
        sancli.args['log_dest'] = "system"
        sancli.args['ip_spa'] = "1.1.1.1"
        return sancli

    def test_create_snapshot(self):
        '''testing sancli_create_snap() with all parameters ok '''
        emsg1 = "1 Operation failed for create snapshot Not a string"
        sancli = self.create_valid_create_snap()
        san = api_builder(sancli.args['array'], self.logger)
        errors = sancli.sancli_create_snap(san)
        self.assertFalse(emsg1 in errors)

    """ EDDERS
    def test_create_snapshot_exception(self):
        '''
        testing sancli_create_snap() with lun_name, lun_id & snap_name None
        '''
        emsg1 = \
        "PSL Operation failed : Not a string <type 'NoneType'> "
        sancli = self.create_valid_create_snap()
        sancli.args['lun_name'] = None
        sancli.args['snap_name'] = None
        sancli.args['lun_id'] = None
        san = api_builder(sancli.args['array'], self.logger)
        errors = sancli.sancli_create_snap(san)
        self.assertTrue(emsg1 in errors)
        exitCode = sancli._error_show(errors, 1, False)
        self.assertEquals(exitCode, 1)
   """

    def test_validate_action(self):
        '''
        testing is_valid_action() fails when action is invalid_action
        '''
        sancli = self.create_valid_create_snap()
        sancli.args['action'] = "invalid_action"
        errors = is_valid_action(sancli.action, sancli.args)
        emsg = \
        "Action invalid_action is not valid. Valid action is, create_snap"
        exitCode = sancli._error_show([errors], 1, False)
        self.assertEquals(exitCode, 1)
        self.assertTrue(emsg in errors)

    def test_validate_len(self):
        '''
        testing is_valid_len() fails when arg is too short
        '''
        sancli = self.create_valid_create_snap()
        sancli.args['snap_name'] = "s"
        self.assertTrue(is_valid_len(sancli.snap_name, \
                                            sancli.args['snap_name']))

    def test_usage(self):
        '''
        testing _usage() prints usage information
        '''
        sancli = SanCli()
        sancli._usage()

    def test_set_default_values(self):
        '''
        testing _set_default_values() sets defaults for log, scope, array
        '''
        sancli = SanCli()
        sancli._set_default_values()
        self.assertEqual("Info", sancli.args['log_level'])
        self.assertEqual("Global", sancli.args['scope'])
        self.assertEqual("vnx1", sancli.args['array'])
        
    def test_set_log_info1(self):
        '''
        testing _set_log_info(). Input --log_dest=system.
        '''
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass",\
        "--ip_spa=1.1.1.1", "--log_dest=none"
        sancli = self.create_valid_create_snap()                                                      
        sancli.args['log_dest'] = "none"
        sancli._set_log_info()
        self.assertEqual("none", sancli.args['log_dest'])        

    def test_set_log_info2(self):
        '''
        testing _set_log_info(). Input --log_dest=system.
        '''
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass",\
        "--ip_spa=1.1.1.1", "--log_dest=system"
        sancli = self.create_valid_create_snap()                                                      
        sancli._set_log_info()
        self.assertEqual("system", sancli.args['log_dest'])   

    def test_set_log_info3(self):
        '''
        testing _set_log_info(). Input --log_level=Debug.
        '''
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass",\
        "--ip_spa=1.1.1.1", "--log_level=debug"
        sancli = self.create_valid_create_snap()                                                      
        sancli._set_log_info()
        self.assertEqual("Debug", sancli.args['log_level'])
        
    def test_set_log_info4(self):
        '''
        testing _set_log_info(). Input --log_level=Info.
        '''
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass",\
        "--ip_spa=1.1.1.1", "--log_level=Info"
        sancli = self.create_valid_create_snap()                                                      
        sancli._set_log_info()
        self.assertEqual("Info", sancli.args['log_level'])
       
    def test_run_cli_success(self):
        '''
        testing run_cli() call initialise SAN connection when cmd is valid
        '''
        sancli = self.create_valid_create_snap()
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass",\
        "--ip_spa=1.1.1.1","--log=default"

        exitCode = sancli.run_cli()
        self.assertEquals(exitCode, 1)

    def test_run_cli_fail_incorrectlog(self):
        '''
        testing run_cli() fails when log is invalid
        '''
        sancli = self.create_valid_create_snap()
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass",\
        "--ip_spa=1.1.1.1","--log=def"

        exitCode = sancli.run_cli()
        self.assertEquals(exitCode, 1)

    def test_run_cli_success(self):
        '''
        testing run_cli() fails when log is invalid
        '''
        sancli = self.create_valid_create_snap()
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass",\
        "--ip_spa=1.1.1.1","--log_dest=none"
        exitCode = sancli.run_cli()
        self.assertEquals(exitCode, 1)

    def test_run_cli_validationfailure(self):
        '''
        testing run_cli() call initialise SAN connection when cmd is
        valid but validation of lun_name fails.
        '''
        sancli = self.create_valid_create_snap()
        sys.argv = "sancli.py", "create_snap", "--lun_name=l",\
        "--snap_name=snap1","--user=admin","--password=pass","--ip_spa=1.1.1.1"
        exitCode = sancli.run_cli()
        self.assertEquals(exitCode, 1)

    def test_run_cli_fails(self):
        '''
        testing run_cli() returns 1 when command is invalid
        '''
        sancli = self.create_valid_create_snap()
        sys.argv = ""
        exitCode = sancli.run_cli()
        self.assertEquals(exitCode, 1)

    def test_run_cli_help(self):
        '''
        testing run_cli() returns 0 when help command is entered
        '''
        sancli = self.create_valid_create_snap()
        sys.argv = "sancli.py", "help"

        exitCode = sancli.run_cli()
        self.assertEquals(exitCode, 0)

    def test_parse_arguments_None(self):
        '''
        testing _parse_arguments() fails: no command, no args entered
        '''
        sancli = SanCli()
        sys.argv = ""
        errors = sancli._parse_arguments()
        emsg = "Arguments required"
        self.assertTrue(emsg in errors[0])

    def test_parse_arguments_help(self):
        '''
        testing _parse_arguments() prints usage when command is help
        '''
        sancli = SanCli()
        sys.argv = "sancli.py", "help"
        errors = sancli._parse_arguments()
        emsg = "help"
        self.assertTrue(emsg in errors)

    def test_parse_arguments_help1(self):
        '''
        testing _parse_arguments() prints help usage when help entered
        '''
        sancli = SanCli()
        sys.argv = "sancli.py", "help"
        errors = sancli._parse_arguments()
        emsg = "help"
        self.assertTrue(emsg in errors)

    def test_parse_arguments_help2(self):
        '''
        testing _parse_arguments() prints help usage when h entered
        '''
        sancli = SanCli()
        sys.argv = "sancli.py", "-h"
        errors = sancli._parse_arguments()
        emsg = "help"
        self.assertTrue(emsg in errors)

    def test_parse_arguments_help3(self):
        '''
        testing _parse_arguments() prints usage when --help entered
        '''

        sancli = SanCli()
        sys.argv = "sancli.py", "--help"
        errors = sancli._parse_arguments()
        emsg = "help"
        self.assertTrue(emsg in errors)

    def test_parse_arguments_valid_arg_format(self):
        '''
        testing _parse_arguments() success. Correct command and args
        '''

        sancli = SanCli()
        sys.argv = "sancli.py", "create_snap", "--lun_name=lun1",\
        "--snap_name=snap1","--user=admin","--password=pass","--ip_spa=1.1.1.1"
        errors = sancli._parse_arguments()
        self.assertEquals(errors, [])

    def test_parse_arguments_invalid_arg_format(self):
        '''
        testing _parse_arguments(self) with arg missing prefix --
        '''

        sancli = SanCli()
        sys.argv = "sancli.py", "create_snap", "snap_name"
        errors = sancli.run_cli()
        self.assertEquals(errors, 1)

    def test_parse_arguments_invalid_arg_spelling(self):
        '''
        testing _parse_arguments(self) arg with wrong spelling
        '''

        sancli = SanCli()
        sys.argv = "sancli.py", "create_snap", "--snap_nae=snap1"
        errors = sancli._parse_arguments()
        emsg = "snap1 is not a valid argument"
        self.assertTrue(emsg in errors[0])

    def test_parse_arguments_invalid_arg(self):
        '''
        testing _parse_arguments(self) with arg name missing a value
        '''

        sancli = SanCli()
        sys.argv = "sancli.py", "create_snap", "--snap_name= "
        errors = sancli._parse_arguments()
        emsg = "requires a value"
        self.assertTrue(emsg in errors[0])

    def test_validate_lun_name(self):
        '''
        testing is_valid_lun_name() with invalid lun name
        '''

        sancli = SanCli()
        sys.argv = "sancli.py", "create_snap", "--lun_name=l",\
        "--snap_name=s","--user=admin","--password=pass","--ip_spa=1.1.1.1"

        errors2 = sancli.run_cli()
        self.assertEquals(errors2, 1)

    def test_validate_lun_name_lun_name_missing(self):
        '''
        testing is_valid_lun_name() with lun name missing
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['lun_name'] = None

        errors = is_valid_lun_name(sancli.lun_name, sancli.args)
        emsg = "lun_name or lun_id is a mandatory argument"
        self.assertTrue(emsg in errors)

    def test_validate_snap_name(self):
        '''
        testing is_valid_snap_name() with invalid snap name
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['snap_name'] = "s"
        errors = is_valid_snap_name(sancli.snap_name, sancli.args)
        emsg = "snap_name needs to be between 2 and 255 "\
        "characters long"
        self.assertTrue(emsg in errors)

    def test_validate_snap_name_snap_name_missing(self):
        '''
        testing is_valid_snap_name() with snap name missing
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['snap_name'] = None
        errors = is_valid_snap_name(sancli.snap_name, sancli.args)
        emsg = "snap_name is a mandatory argument "
        self.assertTrue(emsg in errors)

    def test_validate_user(self):
        '''
        testing is_valid_user() with user arg invalid
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['user'] = "a"

        errors = is_valid_user(sancli.user, sancli.args)
        emsg = 'user needs to be between 2 and 255 characters long'
        self.assertTrue(emsg in errors[0])

    def test_validate_user_user_missing(self):
        '''
        testing is_valid_user() with user arg missing
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['user'] = None

        errors = is_valid_user(sancli.user, sancli.args)
        emsg = 'user is a mandatory argument'
        self.assertTrue(emsg in errors[0])

    def test_validate_password(self):
        '''
        testing is_valid_password() with password arg invalid
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['password'] = "p"

        errors = is_valid_password(sancli.password, sancli.args)
        emsg = "password needs to be between 2 and 255 "
        self.assertTrue(emsg in errors[0])

    def test_validate_password_password_missing(self):
        '''
        testing is_valid_password() with password arg missing
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['password'] = None

        errors = is_valid_password(sancli.password, sancli.args)
        emsg = "password is a mandatory argument"
        self.assertTrue(emsg in errors[0])

    def test_validate_scope(self):
        '''
        testing is_valid_scope() with invalid scope arg
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['scope'] = "glob"

        errors = is_valid_scope(sancli.scope, sancli.args)
        emsg = "glob is not valid. Valid scopes are: (global, local) "
        self.assertTrue(emsg in errors)

    def test_validate_array(self):
        '''
        testing is_valid_array() with invalid array arg
        '''
        sancli = self.create_valid_create_snap()
        sancli.args['array'] = "v"
        sancli.args['password'] = None
        errors = []
        errors += is_valid_array(sancli.array, sancli.args)
        errors += is_valid_log(sancli.args)
        errors += is_valid_password('password', sancli.args )
        exitCode = sancli._error_show(errors, 1, False)
        self.assertEquals(exitCode, 1)
        emsg = "Valid arrays are: (vnx1, vnx2, unity)"
        self.assertTrue(emsg in errors[0])

    def test_validate_ipv4(self):
        '''
        testing validate_ipv4() with invalid IP arg
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['ip_spa'] = "1.1.1"
        errors = validate_ipv4(sancli.args['ip_spa'])
        self.assertEquals(errors, False)

    def test_validate_ips(self):
        '''
        testing is_valid_ips() with no IP arg
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['ip_spa'] = None

        errors = is_valid_ips(sancli.args)
        emsg = "One or both of ipa and ipb must be supplied"
        self.assertTrue(emsg in errors[0])

    def test_validate_ips2(self):
        '''
        testing is_valid_ips() with IPa arg invalid
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['ip_spa'] = '1.1.1'

        errors = is_valid_ips(sancli.args)
        emsg = "1.1.1 is not a valid IPV4 address"
        self.assertTrue(emsg in errors[0])

    def test_validate_ips3(self):
        '''
        testing is_valid_ips() with IPb arg invalid
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['ip_spb'] = '1.1.1.1.1.1'

        errors = is_valid_ips(sancli.args)
        emsg = "1.1.1.1.1.1 is not a valid IPV4 address"
        self.assertTrue(emsg in errors[0])

    def test_validate_log(self):
        '''
        testing is_valid_log(sancli.args) with invalid log arg
        '''
        sancli = self.create_valid_create_snap()
        sancli.args['log_level'] = "def"
        errors = is_valid_log(sancli.args)
        emsg = "Valid log levels are"
        self.assertTrue(emsg in errors[0])

    def test_validate_arguments_log_level_error(self):
        '''
        testing _validate_arguments() with log_level = def. Return error
        '''
        sancli = self.create_valid_create_snap()
        sancli.args['log_level'] = "def"
        errors = sancli._validate_arguments()
        emsg = "Valid log levels are"
        self.assertTrue(emsg in errors[0])

    def test_validate_arguments(self):
        '''
        testing _validate_arguments() with correct command. No error
        '''
        sancli = self.create_valid_create_snap()
        errors = sancli._validate_arguments()
        self.assertEquals(errors, [])

    def test_validate_arguments_invalidAction(self):
        '''
        testing _validate_arguments() with invalid action
        '''

        sancli = self.create_valid_create_snap()
        sancli.args['action'] = "invalid_action"
        errors = sancli._validate_arguments()

        emsg = "Action invalid_action is not valid. Valid " \
                     "action is, create_snap"
        self.assertTrue(emsg in errors)

    def test_sancli_initialise_connection(self):
        '''
        testing sancli_initialise_connection() with correct cmd. No error
        '''
        sancli = SanCli()
        sancli.args['array'] = "vnx1"
        san = sancli.sancli_initialise_connection()
        self.assertNotEquals(san, None)

    def test_sancli_psl_command_operation1failed(self):
        '''
        testing _sancli_psl_command() with SAN set to None
        Error = 1 Operation failed for {0} {1}
        '''
        sancli = self.create_valid_create_snap()
        sancli.args['array'] = "vnx1"
        empty_error = True
        san_function = 'create_snapshot'
        error_text = "create snapshot"
        function_args = {'lun_name': sancli.args['lun_name'],
                         'snap_name': sancli.args['snap_name']}
        snap_object = sancli._sancli_psl_command(san_function, error_text,
                            empty_error, None, **function_args)
        self.assertNotEquals(snap_object, None)

    def test_sancli_psl_command_CLIbug(self):
        '''
        testing _sancli_psl_command()
        Error = CLI TypeError bug create_snapshot()
        '''
        pass
        #sancli = self.create_valid_create_snap()
        #sancli.args['array'] = "vnx1"
        #sancli.args['lun_name'] = " "
        #san = sancli.sancli_initialise_connection()

        #empty_error = True

        #return_error = "PSL Operation failed : create_snapshot() "\
        #               "takes at least 3 non-keyword arguments (2 given)"

        #san_function = 'create_snapshot'
        #error_text = "create snapshot"
        #function_args = {'lun_name': sancli.args['lun_name']}

        #snap_object = sancli._sancli_psl_command(san_function, error_text,
        #                    empty_error, san, **function_args)
        #self.assertTrue(return_error in snap_object[0])

if __name__ == "__main__":
    unittest.main()
