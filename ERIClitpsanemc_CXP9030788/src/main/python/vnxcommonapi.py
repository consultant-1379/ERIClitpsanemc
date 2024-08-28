"""
File name: vnxcommon.py
Version: 1.10.1
class that is derived from SanApi, and is used as the parent class for
vnx1 and vnx2 subclasses.
"""

import re
from re import IGNORECASE
import subprocess
import sys
import time
import datetime
import subprocess
import xml.etree.ElementTree as ET
import platform
import random
from token import EQUAL
from symbol import raise_stmt

from sanapi import api_builder, SanApi, get_api_version
from sanapiexception import SanApiException, SanApiCommandException, \
                     SanApiConnectionException, \
                     SanApiOperationFailedException, \
                     SanApiCriticalErrorException, \
                     SanApiEntityAlreadyExistsException, \
                     SanApiEntityNotFoundException, \
                     SanApiMissingInformationException

from sanapiinfo import  SanApiInfo, LunInfo, StoragePoolInfo, \
                        StorageGroupInfo, HbaInitiatorInfo, \
                        HluAluPairInfo, SanInfo

import sanapilib
from sanapilib import raise_critical_ex, validate_lun_create, shell_escape

import logging
from vnxparser import *
from sanapilib import normalise_container_type
import socket


class VnxCommonApi(SanApi):
    """
    Implementation of SanApi interface for common vnx functionality. This is a
    parent class to Vnx1Api and Vnx2Api and most of the functionality is here.
    """

    def __init__(self, logger=None, timeout=None, retries=None):
        """
        Set up logging and parser. Use initialise to set up navisec
        connection credentials.
        """
        self.logger = logger or logging.getLogger(socket.gethostname())

        self.parser = VnxParser()
        self._initialised = False

        self._username = None
        self._password = None
        self._scope = None
        self._navi_cmd = None
        self._navi_timeout = timeout
        self._navi_retries = retries
        self._navi_sleep = None

        super(VnxCommonApi, self).__init__()

    def initialise(self, sp_ips, username, password, scope,
                   getcert=True, vcheck=True, esc_pwd=False):
        """
        Initialises the SP IPs, username and password parameters needed to
        call naviseccli.

        :param sp_ips: List of SP IP addresses.
        :type sp_ips: :class:`list`
        :param username: The username used to connect.
        :type username: :class:`str`
        :param password: The password used to connect.
        :type password: :class:`str`
        :param scope: The scope of the navisec command, either global or
            local.
        :type scope: :class:`str`
        :param getcert: Optional, boolean to determine whether to get the
            cert. Default; True.
        :type  getcert: :class:`boolean`
        :param vcheck: Optional, check version of VNX. Default; True.
        :type vcheck: :class:`boolean`
        :param esc_pwd: Optional, escape special chars in password string.
        :type esc_pwd: :class:`boolean`
        """
        self._sp_ips = sp_ips
        self._username = username

        if esc_pwd:
            self._password = shell_escape(password)
        else:
            self._password = password

        self._scope = scope

        # Call constructor of base class aApi as it reads config
        # super(VnxCommonApi, self).__init__()

        if len(self._sp_ips) == 0:
                raise SanApiCriticalErrorException("At least one IP must be"\
                        " defined")

        for ip in self._sp_ips:
            if not sanapilib.validate_ipv4(ip):
                raise SanApiCriticalErrorException("Invalid IP Address: " \
                                                    + ip, 1)
        if username == '' or password == '':
            raise SanApiCriticalErrorException("Invalid VNX login " +
                            "credentials - check username and/or password", 1)

        valid_scopes = re.sub(r'\s+', '', self._cfg.get('VNX', \
                                                        'NavisecValidScopes'))
        if not str(scope).lower() in (cmpscope.lower() \
                                     for cmpscope in valid_scopes.split(",")):

            msg = "Invalid scope %s, must be one of %s" % (scope, valid_scopes)
            raise SanApiCriticalErrorException(msg, 1)

        self.logger.debug("Validated VnxCommonApi constructor arguments")
        self._navi_cmd = self._get_cfg_var('Navisec')
        self._navi_sleep = self._get_cfg_var('NavisecRetrySleep')
        if self._navi_timeout is None:
            self._navi_timeout = self._get_cfg_var('NavisecTimeout')
        if self._navi_retries is None:
            self._navi_retries = self._get_cfg_var('NavisecRetries')

        # Mandatory config items raise exception if not present
        self._navi_cmd = self._cfg.get('VNX', 'Navisec')
        self._navi_timeout = self._cfg.get('VNX', 'NavisecTimeout')
        self._navi_retries = self._cfg.get('VNX', 'NavisecRetries')
        self._navi_sleep = self._cfg.get('VNX', 'NavisecRetrySleep')

        self._navi_retries = int(self._navi_retries)
        self._navi_sleep = int(self._navi_sleep)

        self.logger.debug("Read config parameters for VnxCommonApi")
        self.logger.info("San Api Version: " + get_api_version())

        self._initialised = True

        if getcert is True:
            self._accept_and_store_cert()

        if vcheck:
            try:
                self._check_flare_version()
                self._check_host_naviseccli_version()
            except:
                pass

    """PROTECTED METHODS"""

    def _get_cfg_var(self, option, section='VNX'):
        var = self._cfg.get(section, option)
        return var

    def _navisec(self, navicmd, parse=False, cert=False, xml=True,
                 logmsg=True, log_output=False, timeout=0):
        """
        Runs the NaviCLI command, passes the command with arguments.

        :param navicmd: The naviCLI command.
        :type navicmd: :class:`str`
        :param parse: boolean to determine whether to parse the command to
            check if the syntax is correct. Default; True
        :type parse: :class:`boolean`
        :param cert: boolean to determine whether to retrieve the navisec
            security certificate. Default; True
        :type cert: :class:`boolean`
        :param xml: Optional, boolean to define whether to return XML output.
             Default; True
        :type xml: :class:`boolean`
        :param logmsg: boolean determining whether to log the message.
            Default; True
        :type logmsg: :class:`boolean`
        :returns: XML output from naviseccli in an element tree object.
        :rtype: :class:`xml.etree.ElementTree`
        :raises SanApiConnectionException: Raised if the command fails.
        """
        if self._initialised == False:
            msg = "API is not initialised"
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        parsestr = '-parse' if parse else ''
        completed = False

        for count in range(0, self._navi_retries):
            spinfo = 'Storage Processor A'
            for navi_ip in self._sp_ips:
                if xml:
                    xml = '-xml'
                else:
                    xml = ''
                if timeout == 0:
                    timeout = self._navi_timeout
                log_cmd = "%s -h %s " % (self._navi_cmd, navi_ip) + \
                  "-User \"%s\" -Password ****** " % (self._username) + \
                  "-timeout %s -Scope %s " % (timeout, self._scope)\
                  + "%s %s %s" % (xml, parsestr, navicmd)
                cmd = log_cmd.replace('******', self._password)

                self.logger.debug(
                     "Attempt %s, run navisec command on %s:" % ((int(count)
                                                                + 1), spinfo))
                self.logger.debug(log_cmd)

                try:
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            shell=True)
                except OSError, exce:
                    errmsg = "OS error when attempting to Popen navisec:" +\
                    " %s" % str(exce)
                    self.logger.error(errmsg)
                    raise SanApiCriticalErrorException(errmsg)
                except Exception, exce:
                    errmsg = "Error when attempting to Popen navisec:" +\
                    " %s" % str(exce)
                    self.logger.error(errmsg)
                    continue  # We don't know if this is fatal exception do we?

                if cert == False:
                    stdout, stderr = proc.communicate()
                    if log_output:
                        self.logger.debug(stdout.replace("\n\n", "\n"))
                        self.logger.debug(stderr.replace("\n\n", "\n"))
                    if proc.returncode == 0:
                        self.logger.debug("Command returned" +\
                                          " %s" % proc.returncode)
                        if xml:
                            return self._etree_from_output(stdout,
                                                           logmsg=logmsg)
                        else:
                            return stdout
                else:
                    # We are interacting with navisec to retrieve cert
                    try:
                        self._cert_interaction(proc)  # check return or
                                                      # something for loop
                                                      # behaviour
                        self.logger.debug("Certificate retrieval worked ok")
                        return
                    except SanApiConnectionException:
                        stdout = ""
                        stderr = ""
                spinfo = 'Storage Processor B'
            # we should only retry in connection failures
            if self._is_connection_failure(proc):
                errmsg = "Command ended with unexpected code %s %s" %\
                        (proc.returncode, stderr)
                raise SanApiOperationFailedException(errmsg, 1)
            self.logger.debug("Command returned %s, sleeping %s seconds" % \
                                      (proc.returncode, self._navi_sleep))
            time.sleep(self._navi_sleep)

        # We have exited loop so navisec command has failed with connection
        # issue
        self.logger.info("Executed %s, return code %s" % (log_cmd,
                                                          proc.returncode))
        self.logger.error("Navisec command failed with errorcode" +\
                          " %s " % proc.returncode)
        self.logger.error("%s %s" % (stdout, stderr))
        raise SanApiConnectionException(stdout + stderr, proc.returncode)

    def _is_connection_failure(self, proc):
        """
        Checks if the connection failed.

        :param proc: The procedure code to check.
        :type proc: :class:`int`
        :returns: True if connection failed, else False.
        :rtype proc: :class:`boolean`
        """

        return proc.returncode != 255

    def _etree_from_output(self, stdout, logmsg=True):
        """
        Creates an element tree from the xml output.

        :param stdout: The XML output.
        :type stdout: :class:`str`
        :param logmsg: boolean to determine whether to log any messages.
        :type logmsg: :class:`boolean`
        :returns: The element tree.
        :rtype: :class:`xml.etree.ElementTree`
        :raises SanApiCommandException: Raised if output could not be parsed.
        """

        try:
            root = ET.fromstring(stdout)
        except Exception, exce:
            errmsg = "Cannot parse XML response from naviseccli:" +\
                                                        " %s" % str(exce)
            self.logger.debug(stdout)
            self.logger.error(errmsg)
            raise SanApiCommandException(errmsg, 1)

        navi_dict = dict()
        for san_prop in root.findall('.//PROPERTY'):
            san_property = san_prop.find('VALUE')
            navi_dict[san_prop.attrib['NAME']] = san_property.text

        try:
            if navi_dict['success'] == 'false':
                err = navi_dict['errorCode']
                errmsg = "Navisec cmd failed with error code %s:" % err

                # may not want to log message in all situations
                if logmsg:
                    self.logger.error(errmsg)
                    self.logger.error(navi_dict['why'])

                sanapilib.raise_appropriate_exception(navi_dict['why'],
                                                      navi_dict['why'],
                                                      SanApiCommandException,
                                                      True,
                                                      errcode=err)
            else:
                self.logger.debug("Navisec command succeeded")
        except KeyError:
            raise SanApiCommandException("Bad XML response from naviseccli", 1)

        return root

    def _restore_snapshot(self, lun_id, snap_name, delete_backup_snap,
                          backup_name=None):
        """
        Creates the Naviseccli command to restore a snapshot.

        :param lun_id: ID of the LUN which was snapped.
        :type lun_id: :class:`str`
        :param snap_name: Name of the snapshot.
        :type snap_name: :class:`str`
        :param delete_backup_snap: Optional, indication to delete
            automatically.
        :type delete_backup_snap: :class:`boolean`
        :returns: True if successful (no Naviseccli errors handled by
            _navisec())
        :rtype: :class:`boolean`
        :raises SanApiOperationFailedException: Raised if an error occurs.
        Uses following Naviseccli command to restore a snapshot:

        .. code-block:: python

            'snap -restore -id <snap_name> -bakName <backup_snap_name>
            -res <lun_id> -o'
        """

        self.logger.debug("Entered restore_snapshot; lun_id=\"{0}\", "
                        "snapshot_name=\"{1}\", delete_backup_snapshot=\"{2}\""
                       .format(lun_id, snap_name, delete_backup_snap))

        sanapilib.validate_string(lun_id, self.logger)
        sanapilib.validate_string(snap_name, self.logger)

        if backup_name:
            backup_snapshot_name = backup_name
        else:
            backup_snapshot_name = "_".join(["restore", snap_name])

        cmd_string = "snap -restore -id \"{0}\" -bakName \"{1}\" -res \"{2}\""\
                        .format(snap_name, backup_snapshot_name, lun_id)
        cmd_string += " -o"

        self._navisec(cmd_string)

        self.logger.info("snapshot restored with lun id:" + lun_id +
                             ", unique snapshot name:" + snap_name)

        self.logger.debug("Finished _restore_snapshot with lun id:" + lun_id +
                             ", unique snapshot name:" + snap_name)

        if delete_backup_snap:
            self._delete_snapshot(backup_snapshot_name)

        return True

    def _delete_snapshot(self, snap_name):
        """
        Creates the Naviseccli command to delete a snapshot.

        :param snap_name: Name of the snapshot.
        :type snap_name: :class:`str`
        :returns: True if successful (no Naviseccli errors handled by
            _navisec())
        :rtype: :class:`boolean`
        :raises SanApiOperationFailedException: Raised if an error occurs.

        Uses following Naviseccli command to delete a snapshot:

        .. code-block:: python

            'snap -destroy -id <snap_name> -o'

        """
        self.logger.debug("Entered delete_snapshot; snapshot_name=\"{0}\""
                       .format(snap_name))

        sanapilib.validate_string(snap_name, self.logger)

        try:
            cmd_string = "snap -destroy -id \"{0}\" -o" .format(snap_name)
            self._navisec(cmd_string)

        except Exception as exce:
            if exce.ReturnCode == 35077:
                msg = "The snapshot {0} does not exist".format(snap_name)
                self.logger.warn(msg)
                return True
            else:
                raise

        self.logger.info("snapshot deleted with unique snapshot name:"
                            + snap_name)

        self.logger.debug("Finished _delete_snapshot with "
                          "unique snapshot name:" + snap_name)

        return True

    """PRIVATE METHODS"""

    def _accept_and_store_cert(self):
        """
        Checks if naviseccli is prompting for certificate acceptance. If so,
        the certificate is permanently stored on the host (option 2).
        """
        self.logger.info("Checking if certificate needs to be accepted")

        cmd_string = "systemtype"
        self._navisec(cmd_string, False, True)

    def _cert_interaction(self, proc):
        """
        Certificate interation with navicseccli.

        :param proc: The instance of the naviseccli subprocess.
        :type proc: :class:`SubProcess`
        :returns: None
        :rtype: :class:`None`
        :raises SanApiConnectionException: Raised if command fails or times
            out.
        """

        while True:
            try:
                line = proc.stdout.readline()
                if line == '':
                    break
                if re.search(r"Would you like to \[1\]Accept the " +
                               "certificate for this session, \[2\]" +
                               " Accept and store, \[3\] Reject the " +
                               "certificate\?", line):
                    self.logger.info("Certificate has been " + \
                                  "offered - permanently accepting.")
                    line = proc.stdout.readline()
                    if re.search(r"Please input your selection", line):
                        proc.communicate(input="2\n")

            except Exception, exce:
                self.logger.debug(
                    "Finished reading output from naviseccli %s " \
                                                % str(exce))
                break

        try:
            proc.communicate()
        except Exception:
            pass

        if proc.returncode != 0:
            msg = "Navisec command failed or timed out"
            self.logger.error(msg)
            raise SanApiConnectionException(msg, proc.returncode)

        self.logger.debug("Cerficate check completed ok")
        return None

    """LUN METHODS"""

    def get_lun(self, lun_id=None, lun_name=None, logmsg=True):
        """
        VNX implementation of get_lun.
        It  calls the _navisec function to retrieve info about the LUN
        specified with the parameters and returns a LunInfo object.
        It has two modes. To retrieve by LUN id or LUN name.

        .. note::

            Retrieve by name ONLY works for Storage Pools!
            I.e. method will not search for VNX Raid Group LUNs.

        :param lun_id: The ID of the LUN to retrieve.
        :type lun_id: :class:`str`
        :param lun_name: The name of the LUN to retrieve.
        :type lun_name: :class:`str`
        :param logmsg: boolean to determine whether messages should be logged.
            Default; True
        :returns: A LunInfo object.
        :rtype: :class:`LunInfo`
        """
        self.logger.debug("Entered get_lun with lun_id=%s, lun_name=%s," %
                             (lun_id, lun_name))

        if logmsg:
            ex_logger = self.logger
        else:
            ex_logger = None
        if lun_id is not None and lun_name is None:
            ''' GET LUN BY ID '''
            lun_id = sanapilib.validate_int_and_make_string(lun_id)

            # Running _get_luns then filtering out the one LUN we're interested
            # in so we don't need to write extra code doing the essentially
            # the same job.
            luns = self._get_luns()

            for lun in luns:
                if lun.id == lun_id:
                    self.logger.info("get_lun completed successfully. " +
                                        "Found LUN " + lun.name)
                    return lun

            sanapilib.raise_ex("LUN not found: " + lun_id,
                               SanApiEntityNotFoundException,
                               logger=ex_logger)

        elif lun_name is not None and lun_id is None:
            ''' GET LUN BY NAME '''
            luns = self._get_luns()

            # Search for LUN with matching name
            for lun in luns:
                if (lun.name == lun_name and
                        lun.type == sanapilib.CONTAINER_STORAGE_POOL):
                    self.logger.info("get_lun completed successfully. " +
                                        "Found LUN " + lun.id)
                    return lun

            sanapilib.raise_ex("LUN not found: %s" % lun_name,
                               SanApiEntityNotFoundException,
                               logger=ex_logger)

        else:
            sanapilib.raise_ex("Specify lun_id OR lun_name",
                               logger=self.logger)

    def lun_exists(self, lun_name):
        """
        Checks if a named LUN exists.

        :param lun_name: The name of the LUN to check for.
        :type lun_name: :class:`str`
        :returns: True if the LUN exists.
        """
        self.logger.debug("Entered lun_exists with lun_name="
                           + lun_name)
        try:
            luninfo = self.get_lun(lun_name=lun_name, logmsg=False)
            # not really necessary to do this check but...
            if luninfo.name == lun_name:
                msg = "LUN {0} exists.".format(lun_name)
                self.logger.debug(msg)
                return True
        except SanApiEntityNotFoundException:
            msg = "LUN {0} does not exist.".format(lun_name)
            self.logger.debug(msg)
            return False
        except:
            msg = "Error occured determining existence of LUN {0}" \
                 .format(lun_name)
            sanapilib.raise_ex(msg, SanApiException, logger=self.logger)

    def get_luns(self, container_type=None, container=None, sg_name=None):
        """
        VNX implementation of get_luns to return a LunInfo list of all luns.

        :param container_type: The type of LUN container. Either StoragePool
            or RaidGroup.
        :type container_type: :class:`str`
        :param container: The LUN container.
        :type container: :class:`str`
        :param sg_name: The Storage Group name.
        :type sg_name: :class:`str`
        :returns: The list of LUNs.
        :rtype: :class:`list`
        """
        self.logger.debug("Entered get_luns with container_type=" +
                             "%s, container=%s, sg_name=%s" %
                             (container_type, container, sg_name))

        if sg_name:
            ''' GET STORAGE GROUP LUNS '''
            if container_type is not None or container is not None:
                sanapilib.raise_ex("Faulty parameters. If specifying " +
                                   "'sg_name', no other param should be used.",
                                   logger=self.logger)
            sg = self.get_storage_group(sg_name)
            if sg is None:
                self.logger.debug("Storage group %s not found" % sg_name)
                return []

            if sg.hlualu_list is None:
                self.logger.debug("Storage group %s has no associated LUNs"
                                     % sg_name)
                return []
            luns = self._get_luns()
            sgluns = []
            for lun in luns:
                for hlualu in sg.hlualu_list:
                    if lun.id == hlualu.alu:
                        sgluns.append(lun)
            self.logger.info("get_luns Storage Group completed ok")
            return sgluns

        if container_type is None:
            ''' GET ALL LUNS '''
            return self._get_luns()

        container_type = sanapilib.normalise_container_type(container_type)
        if container_type == sanapilib.CONTAINER_STORAGE_POOL:
            ''' GET STORAGE POOL LUNS '''
            delim = DelimLunList  # "LOGICAL UNIT NUMBER "
            cmd_string = "lun -list"
            sp_etree = self._navisec(cmd_string)
            sp_dict = self.parser.create_dicts(sp_etree, delim)
            lun_list = self.parser.create_object_list(sp_dict,
                    self.parser.create_lun_from_lunlist_dict)
            # if storage pool is specified then only return LUNs in the pool
            filtered_lun_list = []
            if container:
                for lun in lun_list:
                    if lun.container == container:
                        filtered_lun_list.append(lun)
            else:
                filtered_lun_list = lun_list

            self.logger.info("get_luns Storage Pool completed ok")
            return filtered_lun_list

        elif container_type == sanapilib.CONTAINER_RAID_GROUP:
            ''' GET RAID GROUP LUNS '''
            luns = self._get_luns()

            rgluns = []
            if container is None:
                # get all raid group luns
                rgluns = [lun for lun in luns
                          if lun.type == sanapilib.CONTAINER_RAID_GROUP]
            else:
                # we need to match on raid group id
                container = sanapilib.validate_int_and_make_string(container)
                rgluns = [lun for lun in luns
                          if lun.container == container
                          and lun.type == sanapilib.CONTAINER_RAID_GROUP]
            if len(rgluns) == 0:
                self.logger.info("No Raid Group LUNs found")

            self.logger.debug("get_luns Raid Group completed ok")
            return rgluns

        else:
            sanapilib.raise_ex("Unknown container_type %" +
                               str(container_type), logger=self.logger)

    def _get_luns(self, retry=3, sleep_if_fail=5):
        """
        Internal method to launch the actual commands.

        .. note::

            We run getlun and lunlist and combine information from both.
            getlun returns information for all luns, lun -list returns storage
            pool LUN information, including storage pool specific information
            we need for any storage pool LUNs.

        :param retry: How many times it will retry the get lun command before
            giving up
        :type retry: :class: integer
        :param sleep_if_fail: How many seconds between each retry
        :type sleep_if_fail: :class: integer

        :returns: The list of LUNs.
        :rtype: :class:`list`
        """
        self.logger.debug("Entered _get_luns")

        lun_try = 0
        lun_obtained = False
        exception = None
        while not lun_obtained and lun_try < retry:
            try:
                lun_list, sp_dict = self._navisec_get_luns()
                for lun in lun_list:
                    try:
                        lundict = sp_dict.get(lun.id)
                    except KeyError:
                        pass
                    else:
                        self._update_lun_object(lun, lundict)
            except  Exception as exception:
                time.sleep(sleep_if_fail)
                lun_try += 1
            else:
                lun_obtained = True
        if lun_try == retry:
            raise SanApiMissingInformationException(str(exception), 1)
        self.logger.info("_get_luns completed successfully")
        return lun_list

    def _update_lun_object(self, lun, lundict):
        """
        A helper function that updates a lun object based
        on a lundict with new information.

        :param lun: a luninfo object
        :type lun: :class: LunInfo
        :param lundict: a lundict object that comes from the parsed xml
        :param lundict: :class: dict
        """
        if not lundict:
            return
        # Storage Pool LUN, so using info from lunlist sp_dict to set
        # info in lun object
        lun.container = lundict['Pool Name']
        lun.type = sanapilib.CONTAINER_STORAGE_POOL
        raid = lundict['Raid Type']
        lun.raid = sanapilib.normalise_raid_group_for_vnx(raid)
        lun.current_op = lundict['Current Operation']
        lun.current_op_state = lundict['Current Operation State']
        lun.current_op_status = lundict['Current Operation Status']
        lun.percent_complete = lundict[
                                    'Current Operation Percent Completed']
        consumed = lundict['Consumed Capacity (GBs)']
        try:
            consumed = str(int(float(consumed) * 1024))
        except ValueError as e:
            self.logger.info(
            "Failed to retrieve Consumed capacity information on lun {0}"
            .format(lun.id))
            raise e
        lun.consumed = consumed

    def _navisec_get_luns(self):
        """
        Runs the navisec commands necessary for the _get_luns function
        getlun and lun -list
        and return the parsed results.

        :returns: a tuple containing the lun_list and a dictionary
            with the content of the navisec commands
        """
        delim = DelimGetLun  # "LOGICAL UNIT NUMBER"
        cmd_string = "getlun"
        etree = self._navisec(cmd_string)
        navi_dict = self.parser.create_dicts(etree, delim)

        delim = DelimLunList  # "LOGICAL UNIT NUMBER "
        cmd_string = "lun -list"
        sp_etree = self._navisec(cmd_string)
        sp_dict = self.parser.create_dicts(sp_etree, delim)

        lun_list = self.parser.create_object_list(navi_dict,
                                    self.parser.create_lun_from_get_lun_dict)
        return lun_list, sp_dict

    def _get_pool_lun_id_from_lun_name(self, lun_name):
        """
        Fetches and returns the lun_id given the lun_name.
        Uses navisec command 'lun -list -name <lun_name> -default' to retrieve
        the lun_id from the VNX.

        :param lun_name: The LUN name to get the LUN ID for.
        :type lun_name: :class:`str`
        :returns: The lun_id as a string.
        :rtype: :class:`str`

        .. note::

            This function is for Pool Luns. It does not support RAID Luns.

        """

        self.logger.debug(
            "Entered _get_pool_lun_id_from_lun_name; lunName={0}".format(
                                                                lun_name))

        sanapilib.validate_string(lun_name, self.logger)
        cmd_string = "lun -list -name \"{0}\" -default".format(lun_name)
        etree = self._navisec(cmd_string)
        lun_list_dict = self.parser.create_dict(etree)
        lunId = lun_list_dict["LOGICAL UNIT NUMBER "]
        self.logger.info("_get_pool_lun_id_from_lun_name completed" +\
            " successfully; lunName={0}, lunId={1}".format(lun_name, lunId))
        return lunId

    def _get_pool_lun_name_from_lun_id(self, lun_id):
        """
        Fetches and returns the lun_name given the lun_id.
        Uses navisec command 'lun -list -l <lun_id> -default' to retrieve
        the lun_name from the VNX.

        :param lun_id: The LUN ID to get the LUN name for.
        :type lun_id: :class:`str`
        :returns: The lun_name as a string.
        :rtype: :class:`str`

        .. note::

            This function is for Pool Luns. It does not support RAID Luns.

        """

        self.logger.debug("Entered _get_pool_lun_name_from_lun_id;" +\
                          " lun_id={0}".format(lun_id))

        lun_id = sanapilib.validate_int_and_make_string(lun_id)
        cmd_string = "lun -list -l \"{0}\" -default".format(lun_id)
        etree = self._navisec(cmd_string)
        lun_list_dict = self.parser.create_dict(etree)
        lunName = lun_list_dict["Name"]
        self.logger.info("_get_pool_lun_name_from_lun_id completed" +\
            " successfully; lunId={0}, lunName={1}".format(lun_id, lunName))
        return lunName

    def get_snapshots(self, lun_name=None, lun_id=None):
        """
        Fetches VNX Snapshot information.
        If no argument is provided, then a list of SnapshotInfo objects
        is returned.
        If a lun_name or lun_id is provided, then a list of SnapshotInfo
        objects is returned for the VNX Snapshots associated with "lun_name".
        If no VNX Snapshots are found, then an empty list is returned.

        :param lun_name: Optional, the LUN name to get the list of
            SnapshotInfo objects for.
        :type lun_name: :class:`str`
        :param lun_id: Optional, the LUN ID to get the list of
            SnapshotInfo objects for.
        :type lun_id: :class:`str` or :class:`int`
        :returns: A list of SnapshotInfo objects if no argument provided, a
            list of SnapshotInfo objects for the VNX Snapshots associated with
            the lun_name if lun_name provided, an empty list if no VNX
            Snapshots found.
        :rtype: :class:`list` of :class:`SnapshotInfo` objects or empty
        """

        self.logger.debug("Entered get_snapshots")

        if lun_name and lun_id:
            errmsg = "Either lun_name or lun_id can be passed, not both"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if lun_id:
            lun_name = self._get_pool_lun_name_from_lun_id(lun_id)

        if lun_name:
            lun_id = self._get_pool_lun_id_from_lun_name(lun_name)

        if lun_id:
            cmd_string = "snap -list -res {0}".format(lun_id)

            try:
                etree = self._navisec(cmd_string)
            except SanApiEntityNotFoundException:
                return []

            snap_dict = self.parser.create_dicts(etree, "Name")
            for snap_dict_key in snap_dict:
                sub_dict = snap_dict[snap_dict_key]
                sub_dict["Lun name"] = lun_name
        else:
            cmd_string = "snap -list"
            etree = self._navisec(cmd_string)
            snap_dict = self.parser.create_dicts(etree, "Name")

            # get lun info
            lun_list = self._get_luns()
            lun_id_list = [lun.id for lun in lun_list]
            lun_dict = dict(zip(lun_id_list, lun_list))

            # add lun name
            for snap_dict_key in snap_dict:
                sub_dict = snap_dict[snap_dict_key]
                try:
                    sub_dict_lun_id = sub_dict["Source LUN(s)"]
                    sub_dict["Lun name"] = lun_dict[sub_dict_lun_id].name
                except KeyError, exce:
                    msg = "Failed to get snapshot info from dictionary " +\
                                str(exce)
                    self.logger.error(msg)
                    raise SanApiOperationFailedException(msg, 1)

        snap_object_list = self.parser.create_object_list(snap_dict,
                self.parser.create_snap_from_get_snapshot_dict)

        return snap_object_list

    def get_snapshot(self, snap_name):
        """
        Gets an individual VNX snapshot group object.

        :param snap_name:  The name of the snapshot to get the object for.
        :type snap_name: :class:`str`
        :returns: :class:`SnapshotInfo`
        :raises SanApiOperationFailedException: Raised if the snapshot could
            not be retrieved from the dictionary or if the snapshot name is
            not a string.
        """
        self.logger.debug("Entered get_snapshot with {0} ".format(snap_name))

        if not isinstance(snap_name, basestring):
            errmsg = "Snapshot name is not a string %s " % type(snap_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        cmd_string = "snap -list -id \"%s\"" % snap_name
        snapshotree = self._navisec(cmd_string)
        snapshot_dict = self.parser.create_dict(snapshotree)
        try:
            lunId = snapshot_dict["Source LUN(s)"]
        except KeyError, exce:
            msg = "Failed to get snapshot info from dictionary " + str(exce)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        snapshot_dict['Lun name'] = self._get_pool_lun_name_from_lun_id(lunId)

        snapshot_info_object = self.parser.\
            create_snap_from_get_snapshot_dict(snapshot_dict)

        self.logger.debug("get_snapshot completed ok")
        self.logger.info("get_snapshot completed successfully")
        return snapshot_info_object

    def _cmd_lun_storagepool(self, params):
        """
        Returns the cmd command for lun creation in a Storage Pool
        :param params: a dictionary containing the parameters of the new
            lun, formated by validate_lun_create
        :type params: :class:`dict`
        """
        cmd_string = "lun -create -type {vnx_lun_type} -capacity {size_num}"\
                " -sq {size_q} -poolName \"{container}\""\
                " -sp {storage_processor}"\
                " -name \"{lun_name}\"".format(**params)
        if params["lun_id"] == "auto":
            cmd_string += " -aa 1"
        else:
            cmd_string += " -l " + params["lun_id"]
        if params["ignore_thresholds"]:
            cmd_string += " -ignoreThresholds"
        if params["array_specific_options"]:
            cmd_string += " " + params["array_specific_options"]
        return cmd_string

    def _cmd_lun_raidgroup(self, params):
        """
        Returns the cmd command for lun creation in a Raid Group
        :param params: a dictionary containing the parameters of the new
            lun, formated by validate_lun_create
        :type params: :class:`dict`
        """
        cmd_string = "bind {raid_type} {lun_id} -rg {container}"\
                " -cap {size_num} -sp {storage_processor} -sq {size_q}".\
                format(**params)
        if params["array_specific_options"]:
            cmd_string += " " + params["array_specific_options"]
        return cmd_string

    def _retry_lun_creation(self, free_lunids, lun_params):
        """
        Try to create a Lun with the list of available lun ids,
        if none of lun ids works, it will raise an
        SanApiEntityAlreadyExistsException

        :param free_lunids: a list of free lun ids
        :type free_lunids: :class:`list`
        :param lun_params: a dictionary containing the parameters of the new
            lun, formated by validate_lun_create
        :type lun_params: :class:`dict`
        """
        for counter, free_lunid in enumerate(free_lunids):
            lun_params["lun_id"] = free_lunid
            cmd_string = self._cmd_lun_raidgroup(lun_params)
            try:
                self._navisec(cmd_string)
            except SanApiEntityAlreadyExistsException:
                msg = "Lun with ID=%s already exists" % (free_lunid)
                self.logger.warn(msg)
                if counter < len(free_lunids):
                    msg = "Will retry (attempt %s/%s)" % (counter,
                            len(free_lunids))
                    self.logger.warn(msg)
                    time.sleep(random.randint(1, 5))
            else:
                return free_lunid
        else:
            msg = "Failed to create LUN after %s attempts" % (
                    len(free_lunids))
            self.logger.error(msg)
            raise SanApiEntityAlreadyExistsException(msg, 1)

    def _check_randomise_lunid(self):
        """
        Checks in the configuration if the list of available lun ids should be
        randomized.
        """
        try:
            randomise = self._cfg.get('General',
                    'RandomiseNextAvailableLunIdList')
        except:
            self.logger.warn("Unable to determine "
                "RandomiseNextAvailableLunIdList setting. "
                "Using default: %s " % randomise_lunid_list)
            return True
        return randomise != "false"

    def _cmd_name_lun_raid_group(self, params):
        """
        Returns the cmd line for renaming a LUN in a Raid Group

        :param params: A dictionary containing the lun_id and lun_name
        :type params: :class:`dict`
        """
        return "chglun -l " + str(params["lun_id"]) + " -name " + \
                    "\"" + params["lun_name"] + "\""

    def create_lun(self, lun_name, size, container_type, container,
                   storage_processor="a", raid_type="", lun_type="thick",
                   lun_id="auto", ignore_thresholds=False,
                   array_specific_options=""):
        """
        VNX implementation of create_lun.

        :param lun_name: The name of the LUN.
        :type lun_name: :class:`str`
        :param size: The size of the LUN.
        :type size: :class:`int` or :class:`str`
        :param container_type: The LUN container type.
        :type container_type: :class:`str`
        :param container: The container.
        :type container: :class:`str`
        :param storage_processor: The storage processor. Default; "a"
        :type storage_processor: :class:`str`
        :param raid_type: The raid type.
        :type raid_type: :class:`str`
        :param lun_type: The type of LUN. Default; "thick"
        :type lun_type: :class:`str`
        :param lun_id: The LUN ID. Default; "auto"
        :type lun_id: :class:`str`
        :param ignore_thresholds: ignore storage pool % full threshold
        :type ignore_thresholds: :class:`boolean`
        :param array_specific_options: Options specific to the array.
        :type array_specific_options: :class:`str`
        """
        self.logger.debug("Entered create_lun")

        lun_params = validate_lun_create(lun_name, size,
                container_type, container, storage_processor,
                raid_type, lun_type, lun_id, ignore_thresholds,
                array_specific_options, self.logger)
        optargs = dict()

        if lun_params["container_type"] == sanapilib.CONTAINER_STORAGE_POOL:
            cmd_string = self._cmd_lun_storagepool(lun_params)
            optargs["lun_name"] = lun_name
            self._navisec(cmd_string)

        elif lun_params["container_type"] == sanapilib.CONTAINER_RAID_GROUP:
            # Create LUN in a Raid Group
            # handles automatically assigned LUN ID or specific LUN ID
            if lun_params["lun_id"] == "auto":
                randomise_lunid_list = self._check_randomise_lunid()
                # Determine the next valid LUN IDs
                free_lunids = self.get_next_available_lunids(
                            randomise=randomise_lunid_list)
                # Have retry in case concurrent lun create operation
                lun_id = self._retry_lun_creation(free_lunids, lun_params)
            else:
                cmd_string = self._cmd_lun_raidgroup(lun_params)
                self._navisec(cmd_string)

            # Builds naviseccli command to name LUN created on Raid Group
            cmd_string = self._cmd_name_lun_raid_group(lun_params)
            self._navisec(cmd_string)
            msg = "LUN renamed successfully"
            self.logger.debug(msg)
            optargs["lun_id"] = str(lun_id)

        self.logger.info("LUN " + lun_name + " successfully created.")
        return self.get_lun(**optargs)

    def get_next_available_lunids(self, high_lun=None,
                        req_num_free_lunids="5", randomise=True):
        """
        Determines the next N available LUN IDs where N is passed as a
        parameter.

        :param high_lun: Optional, the upper limit for LUN ID.
        :type high_lun: :class:`str` or :class:`int`
        :param req_num_free_lunids: The number of free LUN IDs.
        :type req_num_free_lunids: :class:`str`
        :param randomise: boolean determining whether to randomise the list
            of free LUN IDs returned.
        :type randomise: :class:`boolean`
        :returns: List of integers corresponding to free LUN IDs.
        :rtype: :class:`list` of :class:`int`

        """
        # Sets highest valid LUN ID
        if high_lun is None:
            try:
                high_lun = self._cfg.get('General', 'HighLun')
            except:
                errmsg = "Couldn't determine high_lun from config file"
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)
        else:
            high_lun = sanapilib.validate_int_and_make_int(high_lun)

        req_num_free_lunids = \
            sanapilib.validate_int_and_make_int(req_num_free_lunids)

        if not isinstance(randomise, bool):
            errmsg = "Randomise parameter must be a boolean:" + \
                         randomise
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        # Fetches currently used LUN IDs
        lun_list = self._get_luns()

        # Creates an empty list and appends the .id attribute
        # from each currently used LUN
        lunidlist = []
        for lun in lun_list:
            lunidlist.append(int(lun.id))

        # Creates a set from list of used LUN IDs
        lunidset = set(lunidlist)

        # Creates a set from list of valid LUN IDs
        fulllunidset = set(range(0, int(high_lun)))

        # Diffs the 2 lists created in previous steps
        diff = list(fulllunidset - lunidset)
        if len(diff) == 0:
            errmsg = "No free LUN ID available"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        diff.sort()
        if len(diff) > req_num_free_lunids:
            diff = diff[0:req_num_free_lunids]
        if randomise:
            random.shuffle(diff)

        return diff

    def rename_lun(self, lun_id, lun_name):
        """
        Renames the LUN with the given LUN ID or LUN name.

        :param lun_id: The ID of the LUN to rename.
        :type lun_id: :class:`str`
        :param lun_name: The name to rename the LUN as.
        :type lun_name: :class:`str`
        :returns: The LUN.
        :rtype: :class:`LunInfo`
        """
        self.logger.debug("Entered rename lun, id: %s, new name: %s"
                             % (lun_id, lun_name))

        lun_id = sanapilib.validate_int_and_make_string(lun_id)

        cmd_string = "chglun -l " + lun_id + " -name " + \
            "\"" + lun_name + "\""
        self._navisec(cmd_string)
        self.logger.debug("Lun renamed")
        return self.get_lun(lun_id=lun_id)

    """STORAGE POOL METHODS"""

    def __create_storage_pool_info_from_cmd_response(self, cmd_string):
        """
        From the parameter cmd_string a navisec CLI command it executes it,
        and returns the response in a storage pool info object.

        :param cmd_string: The navisec CLI command string.
        :type cmd_string: :class:`str`
        :returns: A StoragePoolInfo object representing the storage pool
            information retrieved from the SAN.
        :rtype: :class:`StoragePoolInfo`
        """
        self.logger.debug(
                    "Entered __create_storage_pool_info_from_cmd_response")

        sptree = self._navisec(cmd_string)
        spdict = self.parser.create_dict(sptree)
        newsp = self.parser.create_spinfo_from_dict(spdict)
        return newsp

    def get_storage_pool(self, sp_name=None, sp_id=None):
        """
        VNX implementation of get_storage_pool.

        :param sp_name: The storage pool name.
        :type: :class:`str`
        :param sp_id: The storage pool ID.]
        :type: :class:`str`
        :returns: :class:`StoragePoolInfo`
        """
        self.logger.debug("Entered get_storage_pool with " +\
                          "sp_name=%s and sp_id=%s" % (sp_name, sp_id))
        if sp_name is not None and sp_id is None:
            cmd_string = "storagepool -list -name \"%s\"" % sp_name
        elif sp_id is not None and sp_name is None:
            cmd_string = "storagepool -list -id %s" % sp_id
            sp_id = sanapilib.validate_int_and_make_string(sp_id)
        else:
            sanapilib.raise_ex("Must specify either 'name' or 'spid' param",
                               logger=self.logger)

        spinfo = self.__create_storage_pool_info_from_cmd_response(cmd_string)
        self.logger.info("get_storage_pool completed successfully")
        return spinfo

    """STORAGE GROUP METHODS"""

    def create_storage_group(self, sg_name):
        """
        Creates storage group and returns storage group object.

        :param sg_name: The name of the new storage group.
        :type sg_name: :class:`str`
        :returns: :class:`StorageGroupInfo`
        :raises SanApiOperationFailedException: Raised if the storage group
            name is not a string.
        """
        self.logger.debug("Entered create_storage_group with %s " % sg_name)

        if not isinstance(sg_name, basestring):
            errmsg = "SG Name is not a string %s " % type(sg_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        cmd_string = "storagegroup -create -gname \"%s\"" % sg_name
        self._navisec(cmd_string)
        self.logger.debug("create_storage_group completed ok")
        self.logger.info("create_storage_group completed successfully")

        return self.get_storage_group(sg_name)

    def get_storage_groups(self):
        """
        Gets list of storage group objects retrieved from navisec.

        :returns: The list of storage group objects.
        :rtype: :class:`list` of :class:`StorageGroupInfo`
        """
        self.logger.debug("Entered get_storage_groups")

        cmd_string = "storagegroup -list"
        sgtree = self._navisec(cmd_string)
        sglist = self.parser.create_sg_list(sgtree)
        self.logger.debug("get_storage_groups completed ok")
        self.logger.info("get_storage_groups completed successfully")
        return sglist

    def get_storage_group(self, sg_name, logmsg=True):
        """
        get individual storage group object
        """
        self.logger.debug("Entered get_storage_group with %s " % sg_name)

        if not isinstance(sg_name, basestring):
            errmsg = "SG Name is not a string %s " % type(sg_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        cmd_string = "storagegroup -list -gname \"%s\"" % sg_name
        sgtree = self._navisec(cmd_string, logmsg=logmsg)
        sglist = self.parser.create_sg_list(sgtree)
        if len(sglist) == 0:
            errmsg = "Storage Group %s not found: " % sg_name
            sanapilib.raise_ex(errmsg, SanApiEntityNotFoundException,
                               logger=self.logger)

        self.logger.debug("get_storage_group completed ok")
        self.logger.info("get_storage_group completed successfully")
        return sglist[0]

    def storage_group_exists(self, sg_name):
        """
        Checks if a named storage group exists.

        :param sg_name: The name of the storage group to check for.
        :type sg_name: :class:`str`
        :returns: True if it exists, else False.
        :rtype: :class:`boolean`
        """
        self.logger.debug("Entered storage_group_exists with SG %s " % sg_name)
        try:
            sginfo = self.get_storage_group(sg_name, logmsg=False)
            # not really necessary to do this check but...
            if sginfo.name == sg_name:
                msg = "Storage Group {0} exists.".format(sg_name)
                self.logger.debug(msg)
                return True
        except SanApiEntityNotFoundException:
            msg = "Storage Group {0} does not exist.".format(sg_name)
            self.logger.debug(msg)
            return False
        except:
            msg = "Error occured determining existence of Storage Group {0}" \
                 .format(sg_name)
            sanapilib.raise_ex(msg, SanApiException, logger=self.logger)

    def create_host_initiators(self, sg_name, wwn, host_name=None, \
                              host_ip=None, arraycommpath="1", \
                              init_type="3", failovermode="4", \
                              array_specific_options=""):
        """
        Examines port list and registers given wwn using all the
        sp and sp ports currently in the port list, in the given
        storage group.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param wwn: The WWN.
        :type wwn: :class:`str`
        :param host_name: The host name.
        :type host_name: :class:`str`
        :param arraycommpath: Optional, the array communication path, either 0
            or 1. Default; "1"
        :type arraycommpath: :class:`str`
        :param init_type: Optional, the initiator type. Default; "3"
        :type init_type: :class:`str`
        :param failovermode: Optional, the failover mode, 0-4. Default; "4"
        :type failovermode: :class:`str`
        :param array_specific_options: Other arguments to be passed to the
            naviseccli command.
        :type array_specific_options: :class:`str`
        :returns: The storage group for the given storage group name.
        :rtype: :class:`StorageGroupInfo`
        :raises SanApiCriticalErrorException: Raised if one of the parameters
            is invalid.
        :raises SanApiOperationFailedException: Raised if the wwn can not be
            registered for any reason.
        """
        if not sg_name:
            errmsg = "Invalid storage group name:" + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.is_valid_wwn(wwn):
            errmsg = "Invalid HBA WWN:" + str(wwn)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if host_name and not host_ip:
            errmsg = "Cannot specify host name without host ip"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if host_ip and not host_name:
            errmsg = "Cannot specify host ip without host name"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if host_ip and not sanapilib.validate_ipv4(host_ip):
            errmsg = "Invalid ip address:" + str(host_ip)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        hba_init_info_list = self.get_hba_port_info(wwn)

        if not hba_init_info_list:
            errmsg = "WWN: " + wwn + " does not appear in port list on VNX"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        for hbainfo in hba_init_info_list:
            try:
                if host_name and host_ip:
                    use_host_name = host_name
                    use_host_ip = host_ip
                else:
                    use_host_name = hbainfo.hbaname
                    use_host_ip = hbainfo.hbaip
                self.create_host_initiator(sg_name, use_host_name, \
                    use_host_ip, wwn, hbainfo.spname, \
                    hbainfo.spport, arraycommpath, init_type, \
                    failovermode, array_specific_options)
            except SanApiCriticalErrorException, ex:
                errmsg = "Failed to register WWN: " + wwn + ", SP: " \
                     + str(hbainfo.spname) + ", SP Port: " + \
                     str(hbainfo.spport) + ". Original Error: " + str(ex)
                self.logger.error(errmsg)
                raise SanApiOperationFailedException(errmsg, 1)

        return self.get_storage_group(sg_name)

    def create_host_initiator(self, sg_name, host_name, host_ip, wwn,
                              storage_processor, sp_port, arraycommpath="1",
                              init_type="3", failovermode="4",
                              array_specific_options=""):
        """
        Assigns a storage group to a particular HBA in a host.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param host_name: The name of the host.
        :type host_name: :class:`str`
        :param host_ip: The host IP.
        :type host_ip: :class:`str`
        :param wwn: The WWN.
        :type wwn: :class:`str`
        :param storage_processor: The storage processor.
        :type storage_processor: :class:`str`
        :param sp_port: The storage processor port.
        :type sp_port: :class:`str`
        :param arraycommpath: Optional, the array communication path, either 0
            or 1. Default; "1"
        :type arraycommpath: :class:`str`
        :param init_type: Optional, the initiator type. Default; "3"
        :type init_type: :class:`str`
        :param failovermode: Optional, the failover mode, 0-4. Default; "4"
        :type failovermode: :class:`str`
        :param array_specific_options: Other arguments to be passed to the
            naviseccli command.
        :type array_specific_options: :class:`str`
        """
        self.logger.debug("Entered create_host_initiator")

        if not sg_name:
            errmsg = "Invalid storage group name:" + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not host_name:
            errmsg = "Invalid host name:" + str(host_name)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.validate_ipv4(host_ip):
            errmsg = "Invalid ip address:" + str(host_ip)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.is_valid_wwn(wwn):
            errmsg = "Invalid HBA WWN:" + str(wwn)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.is_valid_sp(storage_processor):
            errmsg = "Invalid storage processor: " + str(storage_processor)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.is_valid_sp_port(sp_port):
            errmsg = "Invalid SP Port Number:" + str(sp_port)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.is_valid_arraycommpath(arraycommpath):
            errmsg = "Invalid arraycommpath value:" + str(arraycommpath)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not init_type:
            errmsg = "Invalid host initiator type:" + str(init_type)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.is_valid_failover_mode(failovermode):
            errmsg = "Invalid failover mode:" + str(failovermode)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        cmd_string = "storagegroup -setpath -o -gname " + "\"" + sg_name + \
            "\"" + " -hbauid " + wwn + " -sp " + storage_processor + \
            " -spport " + sp_port + " -type " + str(init_type) + \
            " -host " + host_name + " -ip " + host_ip + " -failovermode " + \
            str(failovermode) + " -arraycommpath " + str(arraycommpath)

        if array_specific_options:
            cmd_string += " " + array_specific_options

        self._navisec(cmd_string)
        self.logger.info("create_host_initiator completed successfully")

        return HbaInitiatorInfo(wwn, storage_processor, sp_port, \
                                host_name, host_ip)

    def add_lun_to_storage_group(self, sg_name, hlu, alu):
        """
        Assigns a single hlu-alu pair to a Storage Group.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param hlu: The HLU.
        :type hlu: :class:`str`
        :param alu: The ALU.
        :type alu: :class:`alu`
        """

        self.logger.info("Entering add_lun_to_storage_group")

        if not sg_name:
            errmsg = "Invalid storage group name: " + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        try:
            errmsg = "Invalid ALU: " + str(alu)
            alu = sanapilib.validate_int_and_make_string(alu)
            errmsg = "Invalid HLU: " + str(hlu)
            hlu = sanapilib.validate_int_and_make_string(hlu)
        except:
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        self.logger.info("Attempting to add LUN(" + alu +
                            ") to Storage Group(" + sg_name +
                            ")" + " with HLU(" + hlu + ")")

        cmd_string = "storagegroup -addhlu -gname " + "\"" + sg_name + "\"" \
         + " -hlu " + hlu + " -alu " + alu  # @IgnorePep8
        self._navisec(cmd_string)

        msg = "add_lun_to_storage_group call completed successfully"

        self.logger.debug(msg)
        self.logger.info(msg)

        return self.get_storage_group(sg_name)

    def add_luns_to_storage_group(self, sg_name, hlu_alu_pairs):
        """
        Assigns single or multiple hlu-alu pairs to a Storage Group.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param hlu_alu_pairs: The HLU ALU pairs.
        :type hlu_alu_pairs: :class:`list` of :class:`tuple`
        """
        self.logger.error("Entering add_luns_to_storage_group")

        if not sg_name:
            errmsg = "Invalid storage group name:" + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        for pair in hlu_alu_pairs:
            hlu = pair[0]
            alu = pair[1]

            if not sanapilib.is_positive_int(hlu):
                errmsg = "Invalid HLU: " + str(hlu)
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)

            if not sanapilib.is_positive_int(alu):
                errmsg = "Invalid ALU: " + str(alu)
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)

            self.logger.info("Attempting to add LUN(" + alu +
                                ") to Storage Group(" + sg_name +
                                ")" + " with HLU(" + hlu + ")")

            cmd_string = "storagegroup -addhlu -gname " +\
             "\"" + sg_name + "\"" \
             + " -hlu " + hlu + " -alu " + alu  # @IgnorePep8
            self._navisec(cmd_string)

        msg = "add_luns_to_storage_group call completed successfully"

        self.logger.debug(msg)
        self.logger.info(msg)

        return self.get_storage_group(sg_name)

    def remove_luns_from_storage_group(self, sg_name, hlus):
        """
        Removes LUN associations from a storage group. The hlus parameter
        can be a single hlu value (string or int), or it can be a list of
        numbers (as strings or ints).  It will also accept an hlu_alu_pairs
        list attribute (comprised of HluAluPairInfo objects) from a
        StorageGroupInfo object.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param hlus: The HLUs, either a single value or a list.
        :type hlus: :class:`str` or :class:`int` for a single value,
            :class:`list` of :class:`str` or :class:`int` for multiple
        """

        self.logger.info("Entering remove_luns_from_storage_group")

        if not sg_name:
            errmsg = "Invalid storage group name:" + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        hlu_list = None

        if not hlus:
            errmsg = "hlus parameter must be number or list"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg)

        # If hlus parameter is a list, see if we can parse it
        if type(hlus) is list:
            # if it is list of HluAluPairs, then extract hlus
            if type(hlus[0]) is HluAluPairInfo:
                self.logger.debug(
                        "Getting HLU info from HluAluPairInfo list")
                hlu_list = ' '.join(sanapilib.validate_int_and_make_string(
                                                         h.hlu) for h in hlus)

            # if it is list of numbers then concatenate
            elif type(hlus[0]) is int or type(hlus[0]) is str:
                self.logger.debug(
                        "Getting HLU info from list of %s" % type(hlus[0]))
                hlu_list = ' '.join(sanapilib.validate_int_and_make_string(h) \
                                                               for h in hlus)

            # Unmanageable list
            else:
                errmsg = "Unknown objects in list of HLU objects"
                self.logger.error(errmsg)
                raise SanApiOperationFailedException(errmsg, 1)

            self.logger.debug("List items processed okay")

        # Not dealing with a list, so it should be a single str or int
        elif type(hlus) is int or type(hlus) is str:
            hlu_list = sanapilib.validate_int_and_make_string(hlus)
        else:
            errmsg = "Invalid HLU parameter"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        cmd_string = 'storagegroup -removehlu -o -gname "{0}" -hlu {1}'\
                      .format(sg_name, hlu_list)

        try:
            self._navisec(cmd_string)
        except Exception as exce:
            if exce.ReturnCode == 83:
                msg = "The Storage Group does not exist".format(sg_name)
                self.logger.warn(msg)
                return True
            elif exce.ReturnCode == 66:
                msg = "Some LUNs don't exist on the Storage Group {0}"\
                      .format(sg_name)
                self.logger.warn(msg)
                return True
            else:
                raise

        msg = "remove_luns_from_storage_group completed successfully"
        self.logger.debug(msg)

        return self.get_storage_group(sg_name)

    def disconnect_host(self, sg_name, host):
        """
        Disconnects host from storage group.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param host: The host IP address.
        :type host: :class:`str`
        """

        if not sg_name:
            errmsg = "Storage group name must be supplied"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        if not host:
            errmsg = "Host must be supplied"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        cmd_string = "storagegroup -disconnecthost -o -host {0} -gname {1}"\
                     .format(host, sg_name)
        try:
            self._navisec(cmd_string)
        except Exception as exce:
            if exce.ReturnCode == 116:
                self.logger.warn("Host {0} is not connected".format(host))
                return True
            elif exce.ReturnCode == 102:
                self.logger.warn("Host {0} is not known".format(host))
                return True
            elif exce.ReturnCode == 372:
                self.logger.warn("Host {0} is not connected to sg {1}"\
                                 .format(host, sg_name))
                return True
            elif exce.ReturnCode == 83:
                msg = "The Storage Group does not exist".format(sg_name)
                self.logger.warn(msg)
                return True
            else:
                raise

        infomsg = "Successfully disconnected host {0} from {1}"\
                  .format(host, sg_name)
        self.logger.info(infomsg)
        return True

    def deregister_hba_uid(self, hba_uid):
        """
        Deregisters HBA UID from  the SAN.

        :param hba_uid: The HBA UID.
        :type hba_uid: :class:`str`
        """
        if not hba_uid:
            errmsg = "HBA UID must be supplied"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        cmd_string = "port -removeHBA -o -hbauid {0}".format(hba_uid)
        try:
            self._navisec(cmd_string)
        except Exception as exce:
            if exce.ReturnCode == 84:
                msg = "The HBA UID {0} does not exist".format(hba_uid)
                self.logger.warn(msg)
                return True
            else:
                raise

        infomsg = "Successfully removed HBA UID {0}".format(hba_uid)
        self.logger.info(infomsg)
        return True

    def delete_storage_group(self, sg_name):
        """
        Deletes a storage group.

        :param sg_name: Name of storage group to delete
        :type sg_name: :class:`str`
        :returns: True if snapshot successfully deleted, otherwise False.
        :rtype: :class:`str`
        """
        if not sg_name:
            errmsg = "Storage group name must be supplied"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        cmd_string = "storagegroup -destroy -o -gname {0}".format(sg_name)

        try:
            self._navisec(cmd_string)
        except Exception as exce:
            if exce.ReturnCode == 83:
                msg = "The Storage Group {0} does not exist".format(sg_name)
                self.logger.warn(msg)
                return True
            else:
                raise

        infomsg = "Successfully deleted storage group {0}".format(sg_name)
        self.logger.info(infomsg)
        return True

    def get_hba_port_info(self, wwn=None, host=None, \
                          storage_processor=None, sp_port=None):
        """
        Queries the array for HBA/port information.
        Returns a list of HBAInitiatorInfo objects
        List of objects can be filtered by:
        - wwn
        - wwn AND storage processor
        - wwn AND port
        - wwn AND storage processor AND port
        - host
        - host AND storage processor
        - host AND port
        - host AND storage processor AND port

        :param wwn: The WWN. Default; None.
        :type wwn: :class:`str`
        :param host: The host. Default; None.
        :type host: :class:`str`
        :param storage_processor: The storage processor. Default; None.
        :type storage_processor: :class:`str`
        :param sp_port: The storage processor port. Default; None.
        :type sp_port: :class:`int` :class:`str`
        """
        self.logger.debug("Entered get_hba_port_info")

        # some parameter checking
        if wwn:
            if not sanapilib.is_valid_wwn(wwn):
                errmsg = "Invalid WWN: " + str(wwn)
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)

        if storage_processor:
            if not sanapilib.is_valid_sp(storage_processor):
                errmsg = "Invalid storage processor: " + str(storage_processor)
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)

        if sp_port:
            if not sanapilib.is_valid_sp_port(sp_port):
                errmsg = "Invalid storage processor port: " + str(sp_port)
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)

        # Can only have wwn or host, or neither, BUT NOT both.
        if [wwn, host].count(None) == 0:
            errmsg = "Invalid combination of parameters to get_hba_port_info"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        # If wwn or host is not supplied, then storage_processor and sp_port
        # cannot be supplied.
        if [wwn, host].count(None) == 2 and \
                    [storage_processor, sp_port].count(None) != 2:
            errmsg = "Invalid combination of parameters to get_hba_port_info"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        cmd_string = "port -list -hba"

        #self.logger.debug("naviseccli output for port -list -hba")
        etree = self._navisec(cmd_string)  # log_output=True)

        hba_init_info_list = self.parser.create_hba_init_info_list(etree)

        if wwn:
            hba_init_info_list = [hbainfo for hbainfo in hba_init_info_list \
                                       if hbainfo.hbauid == wwn]
        if storage_processor:
            hba_init_info_list = [hbainfo for hbainfo in hba_init_info_list \
                                       if hbainfo.spname == storage_processor]

        if sp_port:
            hba_init_info_list = [hbainfo for hbainfo in hba_init_info_list \
                                       if hbainfo.spport == sp_port]

        if host:
            hba_init_info_list = [hbainfo for hbainfo in hba_init_info_list \
                                       if (hbainfo.hbaname == host \
                                           or hbainfo.hbaip == host)]

        self.logger.debug("get_hba_port_info completed successfully")
        return hba_init_info_list

    def get_san_info(self):
        """
        Gets SAN information

        :return: SanInfo object
        :raises SanApiOperationFailedException: Raised if the method fails at any point.
        """
        debug_message = ("Entering method {0}.get_san_info"
                         .format(self.__class__.__name__))
        self.logger.debug(debug_message)

        self.logger.info("Checking the Operating Environment (OE) "
                         "version of VNX")
        cmd_string = "getagent -rev -model -serial"
        cmd_result = self._navisec(cmd_string, xml=False)

        # Get OE
        oe_result = re.search(r'(\d+\.){4}\d+', unicode(cmd_result))
        if not oe_result:
            errmsg = "Unable to get VNX OE version"
            self.logger.debug(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)
        else:
            vnx_oe = oe_result.group(0)

        # Get Model
        model_result = re.search(r'Model:\s*(\S+)', unicode(cmd_result))
        if not model_result:
            errmsg = "Unable to get VNX Model information"
            self.logger.debug(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)
        else:
            vnx_model = model_result.group(1)

        # Get Serial No
        serial_result = re.search(r'Serial No:\s*(\S+)', unicode(cmd_result))
        if not serial_result:
            errmsg = "Unable to get the VNX Serial Number"
            self.logger.debug(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)
        else:
            vnx_serial_num = serial_result.group(1)

        return SanInfo(vnx_oe, vnx_model, vnx_serial_num)

    def get_san_alerts(self):
        """
        Gets SAN alerts severity and description.

        :return: None or fault error message(s)
        """
        errors = ['fractured', 'fault']
        cmd_string = "faults -list"
        try:
            output = self._navisec(cmd_string, xml=False)
        except SanApiException:
            msg = "Error checking if anything on the SAN is faulted," \
                   " please check manually through the GUI"
            return msg
        no_cap_output = output.lower()
        for error in errors:
            if error in no_cap_output:
                return output
        return None

    def get_hw_san_alerts(self):
        date_string = "date +'%m/%d/%Y'"
        date_str = subprocess.Popen(date_string, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        date_today , error = date_str.communicate()
        if date_today:
                date_today = str(date_today)
                output_clr = date_today.strip()
        if error:
                print("Error:", error)
        original_date = datetime.datetime.strptime(output_clr, "%m/%d/%Y")
        one_day = datetime.timedelta(days=1)
        two_weeks= datetime.timedelta(weeks=2)
        before_date = original_date - two_weeks
        after_date = original_date + one_day
        before_date_str = before_date.strftime("%m/%d/%Y")
        after_date_str = after_date.strftime("%m/%d/%Y")
        cmd_string = "getlog -date " + before_date_str + " " + after_date_str
        try:
            output = self._navisec(cmd_string, xml=False, timeout=600)
        except SanApiException:
            msg = "Error checking if anything on the SAN has Hardware Errors," \
              " please check manually through the GUI"
            return msg
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
        new_output = [line for line in output_lines
                       if ('HwErrMon' in line and 'DIMM_ECC' in line) ]
        if new_output:
            return new_output
        return None

    def _get_host_naviseccli_version(self):
        """
        Gets the naviseccli version of a host machine.

        :returns: The naviseccli version.
        :rtype: :class:`str`
        :raises SanApiCriticalErrorException: Raised if an error encountered
            while running the command.
        :raises SanApiOperationFailedException: Raised if unable to get
            naviseccli version.
        """
        self.logger.debug("Checking the naviseccli version")
        cmd = "%s -help" % (self._navi_cmd)
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
            stdout, stderr = proc.communicate()
        except OSError:
                    errmsg = "Error occurred while running command: " + cmd
                    self.logger.error(errmsg)
                    raise SanApiCriticalErrorException(errmsg)

        p = re.compile(r'(\d+\.){4}\d+')
        navisec_version = re.search(p, unicode(stdout))
        if not navisec_version:
            warnmsg = "Unable to get host NaviCLI version"
            self.logger.warn(warnmsg)
            raise SanApiOperationFailedException(warnmsg, 1)
        return str(navisec_version.group(0))

    def _check_flare_version(self):
        """
        Checks the FLARE/OE version of a VNX.

        :returns: True if a valid FLARE/OE version retrieved, else False.
        :rtype: :class:`boolean`
        :raises SanApiCriticalErrorException: Raised if unable to rerieve the
            FLARE/OE version.
        """
        array_san_info = self.get_san_info()
        array_flare_version = array_san_info.oe_version

        self.logger.debug("Checking if the FlARE/OE version" +\
                          " %s is a supported version " % array_flare_version)

        try:
            valid_flare_versions = self._cfg.get('General',
                                                 'ValidFlareVersions')\
                                                 .split(',')
            self.logger.debug("Flare_version list retrieved from config " +\
                              "file: %s " % valid_flare_versions)
        except:
                errMsg = "Couldn't retrieve flare_versions from config file"
                self.logger.error(errMsg)
                raise SanApiCriticalErrorException(errMsg, 1)

        try:
            num_tokens = self._cfg.get('General',
                                       'OESWTokensToCheck')
            self.logger.debug("Number of tokens to check retrieved from " +\
                              "config file: %s " % num_tokens)
        except:
                errMsg = "Couldn't retrieve Number of tokens to check from" +\
                " config file"
                self.logger.error(errMsg)
                raise SanApiCriticalErrorException(errMsg, 1)

        for valid_flare_version in valid_flare_versions:
            if sanapilib.version_checker(array_flare_version,
                                         valid_flare_version,
                                         num_tokens,
                                         seperator="."):
                self.logger.info("Valid FLARE/OE version being used %s"
                                    % array_flare_version)
                return True

        msg = "Unsupported FLARE/OE version %s detected" % array_flare_version

        self.logger.warn(msg)
        return False

    def _check_host_naviseccli_version(self):
        """
        Check if naviseccli version is a valid or unsupported version or
        cannot be found.

        :returns: True if valid naviseccli retrieved correctly and valid, else
            False.
        :raises SanApiCriticalErrorException: Raised if unable to retrieve
            platform information, raised navisec version unable to be
            retrieved from config file, raised if unable to retrieve number of
            tokens from file.
        """
        # Get a version of naviseccli and check if it is a supported version
        # as per the sanapi.ini fie, returns True if valid.
        host_naviseccli_version = self._get_host_naviseccli_version()

        self.logger.debug("checking if naviseccli version " +\
                    "%s is a supported version " % host_naviseccli_version)
        platform = self._get_platform_information()

        if re.search('linux', platform, IGNORECASE):
            platform_type = 'Linux'
            self.logger.debug("Platform information: %s"
                                 % platform)
        elif re.search('solaris', platform, IGNORECASE):
            platform_type = 'Solaris'
            self.logger.debug("Platform information: %s"
                                 % platform)
        else:
                self.logger.warn("Unable to retrieve platform information")
                errMsg = "Unable to retrieve platform information from " +\
                    "config file"
                self.logger.error(errMsg)
                raise SanApiCriticalErrorException(errMsg, 1)

        try:
            valid_naviseccli_versions = self._cfg.get('General',
                                             'Valid' + platform_type +
                                             'NaviseccliVersions').split(',')
            self.logger.debug("Navisec version list retrieved from config" +\
                              " file %s " % valid_naviseccli_versions)
        except:
                errMsg = "Couldn't retrieve navisec_versions from config file"
                self.logger.error(errMsg)
                raise SanApiCriticalErrorException(errMsg, 1)

        try:
            num_tokens = self._cfg.get('General',
                                       'NaviseccliSWTokensToCheck')
            self.logger.debug("Number of tokens to check retrieved from" +\
                              " config file: %s " % num_tokens)
        except:
                errMsg = "Couldn't retrieve Number of tokens to check from" +\
                " config file"
                self.logger.error(errMsg)
                raise SanApiCriticalErrorException(errMsg, 1)

        for valid_naviseccli_version in valid_naviseccli_versions:
            if sanapilib.version_checker(host_naviseccli_version,
                                         valid_naviseccli_version,
                                         num_tokens,
                                         seperator="."):
                self.logger.info("Valid NaviCLI version being used %s"
                                    % host_naviseccli_version)
                return True

        self.logger.warn("Unsupported version of NaviCLI being used %s."
                            % host_naviseccli_version)
        return False

    def _get_platform_information(self):
        """
        Gets the underlying platform/operating system information.

        :returns: The platform information.
        :rtype: :class:`str`
        """
        platform_info = platform.platform()
        self.logger.debug("Platform: %s" % platform_info)
        return platform_info

    def create_snapshot_with_id(self, lun_id, snap_name, description=None):
        """
        This function creates a snapshot. It will raise a
        SanAPiOperationFailedException if an error ocurred.

        :param lun_name: The id of the LUN to snap.
        :type lun_id :class:`str`
        :param snap_name: The name of the snapshot.
        :type snap_name: :class:`str`
        :param description: The snapshot description.
        :type description: :class:`str`
        """

        lun_id = sanapilib.validate_int_and_make_string(lun_id)
        sanapilib.validate_string(snap_name, self.logger)

        if description:
            sanapilib.validate_string(description, self.logger)

        cmd_string = "snap -create -res \"{0}\" -name \"{1}\""\
            .format(lun_id, snap_name)

        if description:
            cmd_string += ' -descr "{0}"'.format(description)

        self._navisec(cmd_string)

        self.logger.info("snapshot creation with lun id:" + lun_id +\
                          " snapshot name:" + snap_name + " returned ")
        self.logger.debug("Finished create_snapshot with lun id:" + lun_id +
                             " snapshot name:" + snap_name)

        return self.get_snapshot(snap_name)

    def create_snapshot(self, lun_name, snap_name, description=None):
        """
        This function creates a snapshot. It will raise a
        SanAPiOperationFailedException if an error ocurred.

        :param lun_name: The name of the LUN to snap.
        :type lun_name: :class:`str`
        :param snap_name: The name of the snapshot.
        :type snap_name: :class:`str`
        :param description: The snapshot description.
        :type description: :class:`str`
        """

        sanapilib.validate_string(lun_name, self.logger)
        sanapilib.validate_string(snap_name, self.logger)

        if description:
            sanapilib.validate_string(description, self.logger)

        lun_id = self._get_pool_lun_id_from_lun_name(lun_name)
        cmd_string = "snap -create -res \"{0}\" -name \"{1}\""\
            .format(lun_id, snap_name)

        if description:
            cmd_string += ' -descr "{0}"'.format(description)

        self._navisec(cmd_string)

        self.logger.info("snapshot creation with lun id:" + lun_id +\
                          " snapshot name:" + snap_name + " returned ")
        self.logger.debug("Finished create_snapshot with lun id:" + lun_id +
                             " snapshot name:" + snap_name)

        return self.get_snapshot(snap_name)

    def restore_snapshot(self, lun_name, snap_name, delete_backupsnap=True,
                         backup_name=None):
        """
        This function will send the relevant information to the protected
        restore snapshot function.

        :param lun_name: The name of the LUN which was snapped.
        :type lun_name: :class:`str`
        :param snap_name: The name of the snapshot.
        :type snap_name: :class:`str`
        :param delete_backupsnap: Optional, the indication to delete
            automatically created backup snap. Default; True.
        :type delete_backupsnap: :class:`boolean`
        :param backup_name: A string for the name of the backup snapshot.
        :type backup_name: :class:`str`
        """

        lun_id_from_name = self._get_pool_lun_id_from_lun_name(lun_name)

        return self._restore_snapshot(lun_id=lun_id_from_name,
                                      snap_name=snap_name,
                                      delete_backup_snap=delete_backupsnap,
                                      backup_name=backup_name)

    def restore_snapshot_by_id(self, lun_id, snap_name, delete_backupsnap=True,
                               backup_name=None):
        """
        This function will send the relevant information to the protected
        restore snapshot function.

        :param lun_id: The ID of the LUN which was snapped.
        :type lun_id: :class:`str`
        :param snap_name: The name of the snapshot.
        :type snap_name: :class:`str`
        :param delete_backupsnap: Optional, the indication to delete
            automatically created backup snap. Default; True.
        :type delete_backupsnap: :class:`boolean`
        :param backup_name: A string for the name of the backup snapshot.
        :type backup_name: :class:`str`
        """
        return self._restore_snapshot(lun_id=lun_id,
                                      snap_name=snap_name,
                                      delete_backup_snap=delete_backupsnap,
                                      backup_name=backup_name)

    def delete_snapshot(self, snap_name):
        '''
        This function will send the relevant information to the protected
        delete snapshot function
        :req param snap_name: Name of the snapshot. Type = string
        '''

        return self._delete_snapshot(snap_name=snap_name)

    def delete_lun(self, lun_name=None, lun_id=None,
                   array_specific_options=""):
        """
        VNX implementation of the delete LUN API function.

        :param lun_name: The name of the LUN. Default; None.
        :type lun_name: :class:`str`
        :param lun_id: The ID of the LUN. Default; None.
        :type lun_id: :class:`str`
        :param array_specific_options: Other arguments to be passed to the
            naviseccli command.
        :type array_specific_options: :class:`str`
        :returns: True if LUN successfully deleted.
        :rtype: :class:`boolean`
        :raises SanApiCriticalErrorException: Raised if neither LUN name or
            LUN ID specified, raised if both LUN name and LUN ID specified,
            raised if LUN ID invalid, raised if unable to get info on LUN,
            raised if LUN container unrecognised.
        """
        self.logger.debug("Entered delete_lun")

        optargs = dict()

        if not lun_name and not lun_id:
            errmsg = "Neither lun name nor lun id were specified"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if lun_name and lun_id:
            errmsg = "Both lun name and lun id were specified"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if lun_id:
            try:
                lun_id = sanapilib.validate_int_and_make_string(lun_id)
                optargs["lun_id"] = lun_id
            except:
                errmsg = "Invalid LUN id: " + lun_id
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)
        else:
            optargs["lun_name"] = lun_name

        # need to figure out if this is RG or Pool LUN
        try:
            linfo = self.get_lun(**optargs)
        except SanApiEntityNotFoundException as exce:
            msg = "The LUN does not exist"
            self.logger.warn(msg)
            return True
        except Exception:
            errmsg = "Unable to get information on LUN: "
            errmsg += lun_name if lun_name else lun_id
            errmsg += ". It may not exist."
            if lun_name:
                errmsg += " Note also Raid Group LUNs cannot " + \
                            "be deleted by name."
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if linfo.type == "StoragePool":
            self.logger.debug("This LUN is in a storage pool " + \
                                 linfo.container)
            cmd_string = "lun -destroy -l %s" % linfo.id
        elif linfo.type == "RaidGroup":
            self.logger.debug("This LUN is in a Raid Group")
            cmd_string = "unbind %s" % linfo.id
        else:
            errmsg = "Unrecognised LUN container type" + str(linfo.type)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)
        if array_specific_options:
            cmd_string += " " + array_specific_options
        cmd_string += " -o"
        self._navisec(cmd_string)
        infomsg = "Successfully deleted LUN: "
        infomsg += lun_name if lun_name else lun_id
        self.logger.info(infomsg)
        self.logger.debug("Leaving function delete_lun")
        return True

    def create_storage_pool(self, sp_name, disks,
                            raid_type, array_specific_options=""):
        """
        Creates a storage pool on VNX.

        :param sp_name: The name of the storage pool.
        :type sp_name: :class:`str`
        :param disks: A string containing the disks to add to the new storage
            pool.
        :type disks: :class:`str`
        :param raid_type: The raid type for the storage pool.
        :type raid_type: :class:`str`
        :param array_specific_options: Other arguments to be passed to the
            naviseccli command.
        :type array_specific_options: :class:`str`
        """
        self.logger.debug("Entering function create_storage_pool")
        if not sp_name:
            err_msg = "No storage pool name provided, this is a mandatory " +\
                    "argument"
            raise SanApiCriticalErrorException(err_msg, 1)

        if not disks:
            err_msg = "No disks provided, this is a mandatory argument"
            raise SanApiCriticalErrorException(err_msg, 1)

        sanapilib.validate_string(disks)

        # formats the raid type argument as required
        raid_type = sanapilib.convert_raid_type_to_vnx(raid_type, "pool")

        # Removes extra whiteapaces
        disks = ' '.join(disks.split())

        self.logger.info("Attempting to create Storage Pool(" +
                            str(sp_name) + ") with RAID(" +
                            str(raid_type) + ") using disks(" +
                            str(disks) + ")")

        # Splits 'disks' into seperate components
        disk_list = disks.split(" ")

        for individual_disk in disk_list:
            if not sanapilib.isBusEncDisk(individual_disk):
                err_msg = "Invalid Disk Information presented," \
                    + " disks should be in B_E_D format and be a valid" +\
                    " disk. " + str(disk_list)
                self.logger.error(err_msg)
                raise SanApiCriticalErrorException(err_msg, 1)

        cmd_string = "storagepool -create -disks " + str(disks) \
            + " -rtype " + str(raid_type) + " -name " \
            + "'" + str(sp_name) + "'"

        if array_specific_options:
            cmd_string += " " + array_specific_options

        cmd_string += " -o"
        self._navisec(cmd_string)

        self.logger.info("Successfully created Storage Pool(" +
                            str(sp_name) +
                            ") with RAID(" + str(raid_type) +
                            ") using disks(" + str(disks) + ")")

        self.logger.debug("Exiting function create_storage_pool")

        return self.get_storage_pool(sp_name=sp_name)

    def modify_storage_pool(self, sp_name, hwm_value):
        """
        Modify a storage pool on VNX.

        :param sp_name: The name of the storage pool.
        :type sp_name: :class:`str`
        :param hwm_value: The value for snapPoolFullHWM
        :type hwm_value: :class:`int`
        """
        self.logger.debug("Entering function modify_storage_pool")
        if not sp_name:
            err_msg = "No storage pool name provided, this is a mandatory " +\
                    "argument"
            raise SanApiCriticalErrorException(err_msg, 1)

        if not hwm_value or not isinstance(hwm_value, int):
            err_msg = "Invalid HWM value: {0}, Valid values are 1-99."\
                      .format(hwm_value)
            raise SanApiCriticalErrorException(err_msg, 1)

        cmd_string = "storagepool -modify -name " + "'" + str(sp_name) + "'"\
                     " -snapPoolFullThresholdEnabled On" +\
                     " -snapPoolFullHWM {0}" .format(hwm_value)

        cmd_string += " -o"
        self._navisec(cmd_string)

        self.logger.info("Successfully modified Storage Pool(" +
                          str(sp_name) +
                          ") with snapPoolFullHWM value({0})".format(hwm_value))

        self.logger.debug("Exiting function modify_storage_pool")

    def expand_pool_lun(self, lun_name, size):
        """
        Increase the size of a storage pool LUN.
        If the new size specified is higher than the existing
        size and the requirements for expansion are met,
        the LUN would expand. If the new size is less than
        the existing size, an error message will be displayed

        SanAPiOperationFailedException if an error ocurred.

        :param lun_name: The name of the pool LUN.
        :type lun_name: :class:`str`
        :param size: Size to expand LUN.
        :type size: :class:`str`
        :returns: The LunInfo object for the expanded LUN.
        :rtype: :class:`LunInfo`

        Usage example:

        .. code-block:: python

            expand_pool_lun(lun_name="lun123", size="200gb")

        """
        self.logger.debug("Entered expand_pool_lun")

        sanapilib.validate_string(lun_name, self.logger)
        sanapilib.validate_string(size, self.logger)

        try:
            size_num, size_q = sanapilib.convert_size_to_vnx(size)
        except SanApiCriticalErrorException:
            errmsg = "Invalid size: " + str(size)
            self.logger.error(errmsg)
            raise SanApiCommandException(errmsg, 1)

        try:
            # Try and expand the LUN
            luninfo = self.get_lun(lun_name=lun_name)
            if self.is_nearly(luninfo.size, size_num):
                self.logger.info("LUN : \"{0}\" size is \"{1}\". Requested size"
                                 "is \"{2}\". This is considered already"
                                 " expanded. The LUN expand task below will do"
                                 "nothing.".format(lun_name, luninfo.size,
                                                   size_num))
            else:
                cmd_string = ("lun -expand -name {0} -capacity {1} -sq {2} "
                          .format(lun_name, size_num, str(size_q)) + " -o")
                self._navisec(cmd_string)
                self.logger.info("LUN :  \"{0}\" expanded by \"{1}{2}\" "
                             .format(lun_name, size_num, str(size_q)))

        except Exception as e:
            self.logger.error(e.message)
            raise SanApiCommandException(e.message, 1)

        self.logger.debug("Exiting expand_pool_lun")

        return self.get_lun(lun_name=lun_name, logmsg=True)

    def is_nearly(self, actual_size, new_size):
        new_size, actual_size = int(actual_size), int(new_size)
        variance = float(new_size) / 100
        return (int(new_size - variance) <= actual_size <= int(new_size + variance))
