#!/usr/bin/python
"""
File name: sancli.py
Author: SE, MR, LC
"""
import base64
import sys
import re
import logging
from sanapilib import *
from sanapi import *
from sanapiexception import *
import socket

MIN_NAME_LEN = 2
MAX_NAME_LEN = 255

DEFAULT_LOG_LEVEL = 'Info'
DEFAULT_LOG = logging.INFO
NO_LOGGING = 'none'
DEFAULT_SCOPE = 'Global'
DEFAULT_ARRAY = 'vnx1'
DEFAULT_DEST = 'system'

ERROR_GENERAL = 1
ERROR_USAGE = 2
ERROR_VALIDATION = 3
ERROR_CONNECTION = 4
ERROR_NOT_FOUND = 5
ERROR_ALREADY_EXISTS = 6
ERROR_OPERATION_FAILED = 7
ERROR_PROGRAM = 8  # for failed imports or non-existent psl functions

USAGE = """
CLI tool to use the SAN API from the command line.  Current functionality
is limited to snapshot handling.

Usage: sancli [-h] | [action] [options]

actions:
    create_snap       Create a snapshot

arguments:

    --user=<user>            : Username to connect to SAN
    --password=<password>    : Password to connect to SAN
    --lun_id=<lun id>        : LUN id, either this or lun_name shoud be \
                               provided
    --lun_name=<lun name>    : Name of LUN, either this or lun_id should \
                               provided
    --snap_name=<snap name>  : Name of snapshot
    --ip_spa=<ipa addr>      : IP address of storage processor A  \
 (at least one of SP A or B must be present)
    --ip_spb=<ipb addr>      : IP address of storage processor B
    --log_level=<log level>  : Log Level (INFO by default). Valid options are:
                             : Debug: DEBUG level traces in /var/log/messages
                             : Info: INFO level traces in /var/log/messages
    --log_dest=<log dest>    : Log Destination.
                             : system: /var/log/messages and stdout (default)
                             : none: no logging at all
    --scope=<scope>          : Connection scope.  Valid options: Global, local
    --array=<san array>      : Type of SAN array.  Valid options: vnx1, vnx2,
                             : unity
    --description=<descr>    : Description of snapshot
    --enc=<enc>              : Optional password encoding.  Only b64 currently
                               supported and optional 2 alternative characters
                               to replace '+' and '/' e.g. --enc=b64:_

sancli create_snap --lun_name=lun1 --snap_name=snap1 --array=vnx2 \\
                   --user=admin --password=pass ip_spa=1.1.1.1

    -h --help                : Show this message then exit
"""


class SanCli(object):
    """
    The SanCli class provides a Command Line Interface to the psl functions
    contained in this module. This allows an alternative method of configuring
    San Storage through the command line. The psl functions provide wrapper
    functions to naviseccli commands.
    """
    def __init__(self):
        """
        Set San Cli parameters and command arguments to their default values
        """
        super(SanCli, self).__init__()

        self.errorInfo = ''
        self.action = 'action'
        self.lun_name = 'lun_name'
        self.lun_id = 'lun_id'
        self.snap_name = 'snap_name'
        self.user = 'user'
        self.password = 'password'
        self.ip_spa = 'ip_spa'
        self.ip_spb = 'ip_spb'
        self.scope = 'scope'
        self.array = 'array'
        self.log_level = 'log_level'
        self.log_dest = 'log_dest'
        self.description = 'description'
        self.alternatives = [self.lun_name, self.lun_id]
        self.enc = 'enc'

        self.DEFAULT_VALUES = {
                    self.scope: DEFAULT_SCOPE,
                    self.array: DEFAULT_ARRAY,
                    self.log_level: DEFAULT_LOG_LEVEL,
                    self.log_dest: DEFAULT_DEST
        }

        self.args = dict.fromkeys([self.action, self.lun_name, self.lun_id,
                                   self.snap_name, self.user, self.password,
                                   self.ip_spa, self.ip_spb, self.log_level,
                                   self.scope, self.array, self.log_dest,
                                   self.description, self.enc])


        loglevel = self._set_log_info()
        if (self.args[self.log_dest] == NO_LOGGING):
            self.logger = logging.getLogger(socket.gethostname())
            fh = logging.FileHandler('/dev/null')
            self.logger.addHandler(fh)
        else:
            self.logger = logging.getLogger(socket.gethostname())

    def _set_log_info(self):
        """
        Protected method to return the SAN CLI logging level.

        :returns: SAN CLI logging level
        :rtype: :class:`str`
        """
        param = None
        loglevel = DEFAULT_LOG
        cli_args = sys.argv[2:]  # IGNORE SCRIPT NAME AND action IN ARGV
        for arg in cli_args:
            try:
                param, value = arg.split('=', 1)
            except ValueError:
                return

            if param:
                param = param[2:]
                if param in self.args:
                    if param == self.log_level:
                        if re.match(value, 'Debug', re.IGNORECASE):
                            self.args[self.log_level] = 'Debug'
                            loglevel = logging.DEBUG
                    elif param == self.log_dest:
                        if re.match(value, 'None', re.IGNORECASE):
                            self.args[self.log_dest] = NO_LOGGING
        return loglevel

    def run_cli(self):
        """
        Main method to parse and validate user input and to call appropriate
        PSL methods.

        :returns: Exit code.
        :rtype: :class:`int`
        """
        self.logger.debug("Entering run_cli")
        errors = []
        exit_code = 0

        self._set_default_values()
        errors += self._parse_arguments()

        if errors == ['help']:
            return exit_code

        if errors:
            errors.append("Parsing of Arguments failed")
            self._error_show(errors, ERROR_USAGE, True)
            exit_code = 1
            return exit_code

        errors += self._validate_arguments()

        if errors:
            errors.append("Validation of Arguments failed")
            self._error_show(errors, ERROR_VALIDATION, False)
            exit_code = 1
            return exit_code

        SAN = self.sancli_initialise_connection()

        if SAN:
            method_name = "sancli_%s" % self.args['action']
            self.func = getattr(self, method_name, None)
            errors = self.func(SAN)

        if errors:
            errors.append("SAN initialise connection failed")
            self._error_show(errors, ERROR_GENERAL, False)
            exit_code = 1

        return exit_code

    def _error_show(self, errors, exit_code=ERROR_GENERAL, show_usage=False):
        """
        Error Handling method and usage display.

        :param errors: A list of errors
        :type errors: :class:`list`
        :param exit_code: The exit code, default: 1
        :type exit_code: :class:`int`
        :param show_usage: A boolean defining whether to show usage
            description.
        :type show_usage: :class:`boolean`
        :returns: Exit code.
        :rtype: :class:`int`
        """
        errors.append("Exit Code is %s" % exit_code)
        self.logger.error(errors)
        if self.args[self.log_dest] == DEFAULT_DEST:
            print >> sys.stderr, errors
        if show_usage == True:
            self._usage()
        else:
            return(exit_code)

    def _usage(self):
        """
        Method to display usage.
        Prints the usage description.
        """
        print USAGE

    def _set_default_values(self):
        """
        Method to set arguments log, scope and array to their default values.
        """
        for name in self.DEFAULT_VALUES:
            self.args[name] = self.DEFAULT_VALUES[name]

    def _parse_arguments(self):
        """
        Method to parse San Cli arguments. Checks that all arguments are
        in the correct format and are set to a value. If the help command
        is the input then the usage is printed.

        :returns: The action if found or a list of errors.
        :rtype: :class:`list`
        """
        errors = []
        param = None

        if len(sys.argv) < 2:
            errors.append("Arguments required")
            return errors

        get_action = sys.argv[1]
        if (get_action == 'help' or get_action == '--help'
            or get_action == '-h' or get_action == '-help'):
            self._usage()
            get_action = ['help']
            return get_action

        self.args[self.action] = get_action

        cli_args = sys.argv[2:]  # IGNORE SCRIPT NAME AND action IN ARGV
        for arg in cli_args:
            try:
                param, value = arg.split('=', 1)
            except ValueError:
                errors.append("Unable to parse arg: " +\
                    "{0} (arguments need to be in --arg=value format)".format(arg))
            if param:
                param = param[2:]
                if param not in self.args:
                    errors.append("{0} is not a valid argument".format(arg))
                if value == " " and param not in self.alternatives:
                    errors.append("{0} requires a value".format(arg))
                self.args[param] = value
            if self.args[self.alternatives[0]] == " " and self.args[self.alternatives[1]] == " ":
                errors.append("Either {0} or {1} must contain a value."
                              .format(self.alternatives[0],self.alternatives[1]))

        return errors

    def _validate_encoding(self):
        """
        Protected Method: Validates optional encoding methods,
        currently only b64 implemented

        :returns: A list of errors.
        :rtype: :class:`list`
        """
        errors = []

        if self.args[self.enc]:
            if not self.args[self.enc].startswith('b64'):
                errors.append("{0} is not a supported encoding format"
                          .format(self.args[self.enc]))

        return errors

    def _validate_arguments(self):
        """
        Protected Method: Validate all arguments.

        :returns: A list of errors.
        :rtype: :class:`list`
        """
        errors = []

        errors += is_valid_action(self.action, self.args)
        if errors:
            self._usage()
            return errors

        if self.args[self.lun_name]:
            errors += is_valid_lun_name(self.lun_name, self.args)
        else:
            errors += is_valid_lun_id(self.lun_id, self.args)

        errors += is_valid_snap_name(self.snap_name, self.args)

        errors += is_valid_user(self.user, self.args)

        errors += is_valid_password(self.password, self.args)

        if self.args[self.scope] is not None:
            errors += is_valid_scope(self.scope, self.args)

        if self.args[self.array] is not None:
            errors += is_valid_array(self.array, self.args)

        errors += is_valid_ips(self.args)

        errors += self._validate_encoding()

        errs = is_valid_log(self.args)
        if errs:
            errors += errs
        return errors

    def sancli_initialise_connection(self):
        """
        Connect to SAN storage.
        Call vnxcommonapi method api_builder to setup SAN array type object.
        Initialise the SAN parameters; ips, username and password, to be able
        call and connect to naviseccli.

        :returns: SAN API object. Either Vnx1Api or Vnx2Api.
        :rtype: :class:`SanApi`
        """
        SAN = None
        errors = []
        ips = []
        for ip in (self.args[self.ip_spa], self.args[self.ip_spb]):
            # fix ENMInst to handle spa/spb better
            # for unity TODO  # pylint: disable=fixme

            if ip is not None and ip is not "127.0.0.1":
                ips.append(ip)
        ips = tuple(ips)

        try:
            SAN = api_builder(self.args[self.array], self.logger)

            ips = []
            for ip in (self.args[self.ip_spa], self.args[self.ip_spb]):
                if ip is not None and ip is not "127.0.0.1":
                    ips.append(ip)
            ips = tuple(ips)

            # TODO sort out ip_spb for unity O  # pylint: disable=fixme
            # ips = (self.args[self.ip_spa])

            password = self.args[self.password]
            encoding = self.args[self.enc]

            if encoding:
                if encoding.startswith('b64'):
                    if len(encoding) == 5:
                        self.args[self.password] = base64.b64decode(password,
                                                         [encoding[3],
                                                         encoding[4]])
                    else:
                        self.args[self.password] = base64.b64decode(password)


            SAN.initialise(ips, self.args[self.user], self.args[self.password],
                           self.args[self.scope], False, False, True)
        except Exception, e:
            errors.append("Failed to initialise SAN : %s" % e)
            self._error_show(errors, \
                             ERROR_CONNECTION, False)
        return SAN

    def _sancli_psl_command(self, func_name, error_text, empty_list_is_error,
                                              SAN, **kwargs):
        """
        Protected method to call the appropriate PSL function.

        :param func_name: Name of the PSL Operation to run.
        :type func_name: :class:`str`
        :param error_text: The error text.
        :type error_text: :class:`str`
        :param empty_list_is_error: boolean to define if an empty list should
            throw an error.
        :type empty_list_is_error: :class:`boolean`
        :param SAN: The SAN object.
        :type SAN: :class:`SanApi`
        :param \**kwargs: The key value pair dict.
        :type \**kwargs: :class:`dict`
        :raises SanAPiOperationFailedException: Raised if an error occurs.
        """
        self.logger.debug("Entering _sancli_psl_command")
        errors = []
        if SAN:
            func = getattr(SAN, func_name)
            try:
                func(**kwargs)

            except Exception, e:
                errors.append("PSL Operation failed : %s" % e)
        return errors

    def sancli_create_snap(self, SAN):
        """
        Create snap by calling psl method create_snapshot() with arguments.

        :param lun_name: Name of the LUN to snap.
        :type lun_name: :class:`str`
        :param snap_name: Name of the snapshot.
        :type snap_name: :class:`str`
        :raises SanAPiOperationFailedException: Raised if an error occurs.
        """
        self.logger.debug("Entering sancli_create_snap")
        empty_error = True

        if self.args[self.lun_name]:
            san_function = 'create_snapshot'
            error_text = "create snapshot"
            function_args = {'lun_name': self.args[self.lun_name],
                             'snap_name': self.args[self.snap_name]}
        else:
            san_function = 'create_snapshot_with_id'
            error_text = "create snapshot"
            function_args = {'lun_id': self.args[self.lun_id],
                             'snap_name': self.args[self.snap_name]}

        if self.args[self.description]:
            function_args['description'] = self.args[self.description]

        errors = self._sancli_psl_command(san_function, error_text,
                         empty_error, SAN, **function_args)
        return errors

if __name__ == "__main__":
    exit(SanCli().run_cli())

