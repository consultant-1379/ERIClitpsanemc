"""
File name: unity.py
"""

from unityrest import UnityREST
from sanapi import SanApi, get_api_version

from sanapiexception import SanApiOperationFailedException, SanApiCriticalErrorException, \
    SanApiEntityNotFoundException, SanApiCommandException
from sanapiinfo import LunInfo, StorageGroupInfo, HbaInitiatorInfo, HluAluPairInfo, SanInfo, \
    StoragePoolInfo, SnapshotInfo, SanAlert, SanHwAlert
import sanapilib

import logging
import socket


# noinspection SpellCheckingInspection
class UnityApi(SanApi):
    """
    Implementation of SanApi interface for Unity Array.
    """

    DUMMY_UID = "00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00"

    """ Fields requested from the end points """
    LUN_FIELDS = ['id', 'name', 'wwn', 'sizeTotal', 'currentNode', 'pool', 'hostAccess']
    HOST_INITATOR_FIELDS = ['id', 'initiatorId', 'paths', 'isIgnored']
    HOST_INITATOR_MODIFY_FIELDS = ['id', 'parentHost', 'failoverMode', 'isLunZEnabled']
    HOST_INITATOR_PATH_FIELDS = ['id', 'fcPort']
    HOST_LUN_FIELDS = ['id', 'lun', 'hlu', 'type', 'host']
    HOST_FIELDS = ['id', 'name', 'fcHostInitiators', 'hostLUNs']
    HOST_DESCRIPTION_FIELDS = ['id', 'description']
    SYSTEM_FIELDS = ['id', 'model', 'serialNumber']
    INSTSW_FIELDS = ['id', 'version']
    POOL_FIELDS = ['id', 'name', 'raidType', 'sizeTotal', 'sizeFree', 'sizeSubscribed', 'tiers']
    SNAP_FIELDS = ['id', 'name', 'lun', 'description', 'creationTime', 'state']
    ALERT_FIELDS = ['severity', 'message', 'description', 'state']
    HW_ALERT_FIELDS =['id', 'health']
    DISK_GROUP_FIELDS = ['id', 'totalDisks', 'diskTechnology']

    HOST_MANUAL = 1

    # logging_initialised = False

    SNAP_STATES = {
        2: 'Ready',
        3: 'Faulted',
        6: 'Offline',
        7: 'Invalid',
        8: 'Initializing',
        9: 'Destroying'
    }

    def __init__(self, logger=None):
        """
        Set up logging and parser. Use initialise to set up navisec
        connection credentials.
        """
        parent_logger = logger or logging.getLogger(socket.gethostname())
        self.logger = logging.getLogger("%s.unityapi" % parent_logger.name)

        # TODO  # pylint: disable=fixme
        # Disabled /tmp logging, other story to follow to fix logging properly
        # if not UnityApi.logging_initialised:
        #    self.logger.setLevel(logging.DEBUG)
        #    fh = logging.FileHandler('/tmp/unity.log')
        #    fh.setLevel(logging.DEBUG)
        #    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #    fh.setFormatter(formatter)
        #    self.logger.addHandler(fh)
        #    UnityApi.logging_initialised = True

        self._initialised = False

        self._sp_ips = None
        self._username = None
        self._password = None
        self._scope = None
        self.rest = UnityREST(self.logger)

        super(UnityApi, self).__init__()

    def initialise(self, sp_ips, username, password, scope,
                   getcert=True, vcheck=True, esc_pwd=False):
        """
        Initialises the SP IPs, username and password parameters needed to
        call comminicate with a Unity array.

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
        :param vcheck: Optional, check version of Unity. Default; True.
        :type vcheck: :class:`boolean`
        :param esc_pwd: Optional, escape special chars in password string.
            currently unused in the Unity API.
        :type esc_pwd: :class:`boolean`
        """

        self._sp_ips = sp_ips
        self._username = username
        self._password = password

        if len(self._sp_ips) == 0:
            raise SanApiCriticalErrorException("At least one IP must be defined", 1)

        for ip in self._sp_ips:
            if not sanapilib.validate_ipv4(ip):
                raise SanApiCriticalErrorException("Invalid IP Address: " + ip, 1)
        if username == '' or password == '':
            raise SanApiCriticalErrorException("Invalid login credentials - check username and/or password", 1)

        self.logger.debug("Validated constructor arguments")
        self.logger.info("San Api Version: " + get_api_version())

        self.rest.login(self._sp_ips[0], self._username, self._password)

        self._initialised = True

    """ LUN API Functions """

    def get_lun(self, lun_id=None, lun_name=None, logmsg=True):
        """
        Unity implementation of get_lun.
        It fetches info about the LUN from the array
        specified with the parameters and returns a LunInfo object.
        It has two modes. To retrieve by LUN id or LUN name.

        .. note::

            Retrieve by name ONLY works for Storage Pools!

        :param lun_id: The ID of the LUN to retrieve.
        :type lun_id: :class:`str`
        :param lun_name: The name of the LUN to retrieve.
        :type lun_name: :class:`str`
        :param logmsg: boolean to determine whether messages should be logged.
            Default; True
        :returns: A LunInfo object.
        :rtype: :class:`LunInfo`
        """
        self.logger.debug("Entered get_lun with lun_id=%s, lun_name=%s", lun_id, lun_name)

        instance = None
        if logmsg:
            ex_logger = self.logger
        else:
            ex_logger = None
        if lun_id is not None and lun_name is None:
            ''' GET LUN BY ID '''
            unity_lun_id = 'sv_%s' % lun_id
            instance = self.rest.get_type_instance_for_id("lun", unity_lun_id, self.LUN_FIELDS)
        elif lun_name is not None and lun_id is None:
            instance = self.rest.get_type_instance_for_name("lun", lun_name, self.LUN_FIELDS)
        else:
            sanapilib.raise_ex("Specify lun_id OR lun_name",
                               logger=self.logger)

        if instance is None:
            sanapilib.raise_ex("LUN not found: " + (lun_id if lun_id else lun_name), SanApiEntityNotFoundException,
                               logger=ex_logger)

        return self.__make_lun_info(instance)

    def get_luns(self, container_type=None, container=None, sg_name=None):
        """
        Unity implementation of get_luns to return a LunInfo list of all luns.

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
        self.logger.debug("Entered get_luns with container_type=%s, container=%s, sg_name=%s" % (container_type,
                                                                                                 container, sg_name))

        lun_filter = None
        pools = {}
        if sg_name:
            ''' GET STORAGE GROUP LUNS '''
            if container_type is not None or container is not None:
                sanapilib.raise_ex("Faulty parameters. If specifying " +
                                   "'sg_name', no other param should be used.",
                                   logger=self.logger)

            # Get the host
            host_content = self.rest.get_type_instance_for_name("host", sg_name, self.HOST_FIELDS)
            if host_content is None:
                self.logger.debug('get_luns: No host found with name "%s"' % sg_name)
                return []
            # If the host has
            if 'hostLUNs' in host_content and len(host_content['hostLUNs']) > 0:
                host_lun_ids = []
                for host_lun in host_content['hostLUNs']:
                    host_lun_ids.append(host_lun['id'])
                host_lun_response = self.rest.get_type_instances(
                    "hostLUN",
                    self.HOST_LUN_FIELDS,
                    [self.rest.make_id_filter(host_lun_ids)]
                )
                lun_ids = []
                for entry in host_lun_response.json()['entries']:
                    lun_ids.append(entry['content']['lun']['id'])
                lun_filter = [self.rest.make_id_filter(lun_ids)]
            else:
                self.logger.debug("get_luns: host %s has no host_luns", sg_name)
                return []
        elif container is not None:
            pool_id = self.rest.get_id_for_name("pool", container)
            if pool_id is None:
                self.logger.debug('get_luns: No pool found with name "%s"' % container)
                return []
            pools[pool_id] = container
            lun_filter = ['pool.id eq "%s"' % pool_id]

        response = self.rest.get_type_instances('lun', self.LUN_FIELDS, lun_filter)
        lun_list = []

        for entry in response.json()['entries']:
            lun_list.append(self.__make_lun_info(entry['content'], pools))

        self.logger.debug("get_luns: returning %s luns", len(lun_list))

        return lun_list

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
        self.logger.debug("Entered expand_pool_lun: lun_name=%s size=%s", lun_name, size)

        sanapilib.validate_string(lun_name, self.logger)
        sanapilib.validate_string(size, self.logger)

        try:
            new_size = int(float(sanapilib.convert_size_to_mb(size))) * (1024 * 1024)
        except SanApiCriticalErrorException:
            errmsg = "Invalid size: " + str(size)
            self.logger.error(errmsg)
            raise SanApiCommandException(errmsg, 1)

        lun_content = self.rest.get_type_instance_for_name("lun", lun_name, self.LUN_FIELDS)
        if lun_content is None:
            sanapilib.raise_ex("LUN %s not found" % lun_name, SanApiEntityNotFoundException)

        self.logger.debug("expand_pool_lun: new_size=%s current size=%s", new_size, lun_content['sizeTotal'])

        # Not really sure what this code is for, just copied from vnxcommonapi.is_nearly
        variance = float(new_size) / 100
        if int(new_size - variance) <= lun_content['sizeTotal'] <= int(new_size + variance):
            self.logger.info("LUN : \"{0}\" size is \"{1}\". Requested size"
                             "is \"{2}\". This is considered already"
                             " expanded. The LUN expand task below will do"
                             "nothing.".format(lun_name, lun_content['sizeTotal'] / (1024 * 1024),
                                               size))
        else:
            modify_data = {
                'lunParameters': {
                    'size': new_size
                }
            }
            self.rest.action('storageResource', lun_content['id'], 'modifyLun', modify_data)

        self.logger.debug("Exiting expand_pool_lun")

        return self.get_lun(lun_name=lun_name)

    def create_lun(self, lun_name, size, container_type, container,
                   storage_processor="a", raid_type="", lun_type="thick",
                   lun_id="auto", ignore_thresholds=False,
                   array_specific_options=""):
        """
        Implementation of create_lun.

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

        msg = 'create_lun: lun_name=%s size=%s container_type=%s container=%s storage_processor=%s lun_type=%s'
        self.logger.debug(msg, lun_name, size, container_type, container, storage_processor, lun_type)

        lun_params = sanapilib.validate_lun_create(lun_name, size,
                                                   container_type, container, storage_processor,
                                                   raid_type, lun_type, lun_id, ignore_thresholds,
                                                   array_specific_options, self.logger)

        if sanapilib.normalise_storage_processor(storage_processor) == 'A':
            sp = 0
        else:
            sp = 1

        if lun_params["container_type"] != sanapilib.CONTAINER_STORAGE_POOL:
            sanapilib.raise_ex("Unsupported container_type %s" % str(container_type))

        if lun_params["lun_id"] != "auto":
            sanapilib.raise_ex("Only auto allowed for lun_id")

        pool_id = self.rest.get_id_for_name("pool", lun_params['container'])
        if pool_id is None:
            sanapilib.raise_ex("Could not find pool %s" % lun_params['container'], SanApiEntityNotFoundException)

        request_data = {
            'name': lun_name,
            'lunParameters': {
                'size': int(float(sanapilib.convert_size_to_mb(size))) * (1024 * 1024),
                'pool': {'id': pool_id},
                'isThinEnabled': True,
                'isDataReductionEnabled': True,
                'defaultNode': sp
            }
        }

        response = self.rest.create_post("/api/types/storageResource/action/createLun", request_data)
        unity_lun_id = response.json()['content']['storageResource']['id']
        self.logger.info("LUN " + lun_name + " successfully created with id %s" % unity_lun_id)
        return self.get_lun(str(self.__unity_lun_num(unity_lun_id)))

    def delete_lun(self, lun_name=None, lun_id=None,
                   array_specific_options=""):
        """
        Unity implementation of the delete LUN API function.

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

        if not lun_name and not lun_id:
            errmsg = "Neither lun name nor lun id were specified"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if lun_name and lun_id:
            errmsg = "Both lun name and lun id were specified"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if lun_name:
            unity_lun_id = self.rest.get_id_for_name("lun", lun_name)
        else:
            unity_lun_id = "sv_%s" % lun_id

        self.rest.delete_instance("storageResource", unity_lun_id)

        infomsg = "Successfully deleted LUN: "
        infomsg += lun_name if lun_name else lun_id
        self.logger.info(infomsg)
        self.logger.debug("Leaving function delete_lun")
        return True

    def rename_lun(self, lun_id, lun_name):
        """
        Rename a LUN. Returns a LunInfo object representing the renamed LUN.

        :param lun_id: LUN ID of LUN to rename.
        :type lun_id: :class:`str`
        :param lun_name: New name of LUN.
        :type lun_name: :class:`str`
        :returns: :class:`LunInfo` object
        :raises SanApiEntityNotFoundException: if LUN not found.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            rename_lun('23', 'Admland')
        """
        raise NotImplementedError()

    def lun_exists(self, lun_name):
        """
        Checks if a named LUN exists.

        :param lun_name: The name of the LUN to check for.
        :type lun_name: :class:`str`
        :returns: True if the LUN exists.
        """
        self.logger.debug("Entered lun_exists with lun_name=%s", lun_name)
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

    """ Host Initiator API Functions """

    def get_hba_port_info(self, wwn=None, host=None,
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
        self.logger.debug("Entered get_hba_port_info: www=%s host=%s storage_processor=%s sp_port=%s", wwn, host,
                          storage_processor, sp_port)

        initiator_filter = []
        # some parameter checking
        if wwn:
            if not sanapilib.is_valid_wwn(wwn):
                errmsg = "Invalid WWN: " + str(wwn)
                self.logger.error(errmsg)
                raise SanApiCriticalErrorException(errmsg, 1)
            else:
                initiator_filter.append('initiatorId eq "%s"' % wwn)

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
        if [wwn, host].count(None) == 2 and [storage_processor, sp_port].count(None) != 2:
            errmsg = "Invalid combination of parameters to get_hba_port_info"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        hba_init_info_list = self.__get_hba_for_initiators(initiator_filter)

        # List is already filtered by wwn

        if storage_processor:
            hba_init_info_list = [hbainfo for hbainfo in hba_init_info_list if hbainfo.spname == storage_processor]

        if sp_port:
            hba_init_info_list = [hbainfo for hbainfo in hba_init_info_list if hbainfo.spport == sp_port]

        if host:
            hba_init_info_list = [hbainfo for hbainfo in hba_init_info_list
                                  if (hbainfo.hbaname == host or hbainfo.hbaip == host)]

        self.logger.debug("get_hba_port_info completed successfully")
        return hba_init_info_list

    def create_host_initiators(self, sg_name, wwn, host_name=None,
                               host_ip=None, arraycommpath="1",
                               init_type="3", failovermode="4",
                               array_specific_options=""):
        """
        Examines port list and registers given wwn using all the
        sp and sp ports currently in the port list, in the given
        storage group/Host

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param wwn: The WWN.
        :type wwn: :class:`str`
        :param host_name: The host name.
        :type host_name: :class:`str`
        :param host_ip: The host IP.
        :type host_ip: :class:`str`
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
        self.logger.debug("Entered create_host_initiator: sg_name=%s, www=%s, host_name=%s, host_ip=%s",
                          sg_name, wwn, host_name, host_ip)
        self.__connect_hbas_to_host(sg_name, host_name, wwn, init_type, failovermode, arraycommpath)
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
        self.__connect_hbas_to_host(sg_name, host_name, wwn, init_type, failovermode, arraycommpath)
        hbaii = HbaInitiatorInfo(wwn, storage_processor, sp_port, host_name, host_ip)
        self.logger.debug("create_host_initiator: completed returning: %s", str(hbaii))
        return hbaii

    def remove_host_access_to_san(self, sg_name):
        """
        Disconnects node from storage group(unity host).

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        """
        self.logger.debug("remove_host_access_to_san: sg_name={0}", sg_name)
        host_lun_response = self.rest.get_type_instance_for_name(
            "host", sg_name, self.HOST_FIELDS
        )
        try:
            response = host_lun_response["fcHostInitiators"]
        except KeyError:
            self.logger.info("Host {0} has no associated Initiators"
                             .format(sg_name))
            return True
        initiators = []
        if response:
            for ini in response:
                initiators.append(ini['id'])
        self.logger.info("Host {0} has {1}  Initiator(s)"
                         .format(sg_name, len(initiators)))
        if initiators:
            self.create_storage_group("TempHost")
            host_response = self.rest.get_type_instance_for_name(
                "host", "TempHost", self.HOST_FIELDS
            )
            temp_host_id = host_response["id"]
            request_data = {
                'host': {'id': temp_host_id}
            }
            for ini in initiators:
                self.logger.info("Deleting initiator {0}".format(ini))
                endpoint = '/api/instances/hostInitiator/%s/action/modify' % (ini)
                self.rest.create_post(endpoint, request_data)
            self.rest.delete_instance("host", temp_host_id)
        self.logger.info("Removed SAN access for {0}".format(sg_name))
        return True

    def disconnect_host(self, sg_name, host):
        """
        Disconnects host from storage group.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param host: The host IP address.
        :type host: :class:`str`
        """
        self.logger.debug("disconnect_host: sg_name=%s, host=%s", sg_name, host)

        if not isinstance(sg_name, basestring):
            errmsg = "SG Name is not a string %s " % type(sg_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        host_data = self.rest.get_type_instance_for_name("host", sg_name, self.HOST_FIELDS)
        if host_data is None:
            sanapilib.raise_ex("Storage Group %s not found: " % sg_name, SanApiEntityNotFoundException)

        if 'hostLUNs' in host_data and len(host_data['hostLUNs']) > 0:
            # Get id of any LUN attached to this host
            host_lun_ids = []
            for host_lun in host_data['hostLUNs']:
                host_lun_ids.append(host_lun['id'])
            host_lun_response = self.rest.get_type_instances(
                "hostLUN",
                self.HOST_LUN_FIELDS,
                [self.rest.make_id_filter(host_lun_ids)]
            ).json()
            lun_ids = []
            for entry in host_lun_response['entries']:
                lun_ids.append(entry['content']['lun']['id'])

            if len(lun_ids) > 0:
                # For each attached LUN, remove this host from the hostAccess
                lun_search_response = self.rest.get_type_instances(
                    'lun',
                    self.LUN_FIELDS,
                    [self.rest.make_id_filter(lun_ids)]
                ).json()
                for entry in lun_search_response['entries']:
                    lun_data = entry['content']
                    host_access = []
                    for one_host_access in lun_data['hostAccess']:
                        if one_host_access['host']['id'] != host_data['id']:
                            block_host_access_param = {
                                'host': {'id': one_host_access['host']['id']},
                                'accessMask': one_host_access['accessMask']
                            }
                            host_access.append(block_host_access_param)
                    modify_data = {
                        'lunParameters': {
                            'hostAccess': host_access
                        }
                    }
                    self.rest.action("storageResource", lun_data['id'], "modifyLun", modify_data)

        return True

    def deregister_hba_uid(self, wwn):
        """
        Deregisters HBA UID from  the SAN.

        :param wwn: The HBA UID.
        :type wwn: :class:`str`
        """
        self.logger.debug("deregister_hba_uid: wwn=%s", wwn)

        if not sanapilib.is_valid_wwn(wwn):
            errmsg = "Invalid HBA WWN:" + str(wwn)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        search_response = self.rest.get_type_instances(
            'hostInitiator',
            ['id'],
            ['initiatorId eq "%s"' % wwn]
        ).json()
        if 'entries' not in search_response or len(search_response['entries']) == 0:
            sanapilib.raise_ex("No initiator not found for WWN %s" % wwn, SanApiEntityNotFoundException)

        for entry in search_response['entries']:
            self.rest.delete_instance('hostInitiator', entry['content']['id'])

        return True

    """ Storage Group API Functions """

    def get_storage_group(self, sg_name):
        """
        get individual storage group object
        """
        self.logger.debug("Entered get_storage_group with %s " % sg_name)

        if not isinstance(sg_name, basestring):
            errmsg = "SG Name is not a string %s " % type(sg_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        host_data = self.rest.get_type_instance_for_name("host", sg_name, self.HOST_FIELDS)
        if host_data is None:
            errmsg = "Storage Group %s not found: " % sg_name
            sanapilib.raise_ex(errmsg, SanApiEntityNotFoundException,
                               logger=self.logger)
        sg = self.__sg_from_content(host_data)

        self.logger.debug("get_storage_group completed ok")
        self.logger.info("get_storage_group completed successfully")
        return sg

    def get_storage_groups(self):
        """
        Gets of hosts registered on the Unity, these are mapped to "Storage Groups"

        :returns: The list of storage group objects.
        :rtype: :class:`list` of :class:`StorageGroupInfo`
        """
        self.logger.debug("Entered get_storage_groups")

        response = self.rest.get_type_instances('host', self.HOST_FIELDS)
        json = response.json()
        sglist = []
        for entry in json['entries']:
            sglist.append(self.__sg_from_content(entry['content']))

        self.logger.debug("get_storage_groups completed ok")
        self.logger.info("get_storage_groups completed successfully")
        return sglist

    def create_storage_group(self, sg_name):
        """
        Unity doesn't have a storage group so here we create the host

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

        self.rest.create_instance("host", {'type': self.HOST_MANUAL, 'name': sg_name})

        self.logger.debug("create_storage_group completed ok")
        self.logger.info("create_storage_group completed successfully")

        return self.get_storage_group(sg_name)

    def delete_storage_group(self, sg_name):
        """
        Unity doesn't have a storage group so here we delete the host

        :param sg_name: The name of the storage group to delete
        :type sg_name: :class:`str`
        :returns: :class:`StorageGroupInfo`
        :raises SanApiOperationFailedException: Raised if the storage group
            name is not a string.
        """
        self.logger.debug("Entered delete_storage_group with %s " % sg_name)

        if not isinstance(sg_name, basestring):
            errmsg = "SG Name is not a string %s " % type(sg_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        self.rest.delete_instance("host", "name:%s" % sg_name)
        return True

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

        self.logger.info("Entering add_lun_to_storage_group sg_name=%s, hlu=%s, alu=%s", sg_name, hlu, alu)

        errmsg = None
        if not sg_name:
            errmsg = "Invalid storage group name: " + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        try:
            errmsg = "Invalid ALU: " + str(alu)
            alu = sanapilib.validate_int_and_make_string(alu)
            errmsg = "Invalid HLU: " + str(hlu)
            hlu = sanapilib.validate_int_and_make_string(hlu)
        except SanApiOperationFailedException:
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        host_id = self.rest.get_id_for_name("host", sg_name)
        if host_id is None:
            raise SanApiEntityNotFoundException("Cannot get host for sg %s" % sg_name, 1)

        self.logger.info("Attempting to add LUN(%s) to Storage Group(%s) with HLU(%s)", alu, sg_name, hlu)

        unity_lun_id = 'sv_%s' % alu
        lun_data = self.rest.get_type_instance_for_id("lun", unity_lun_id, self.LUN_FIELDS)
        if lun_data is None:
            raise SanApiEntityNotFoundException("Cannot lun for id %s" % alu, 1)

        # First modify the lun to has the host
        host_access = []
        if 'hostAccess' in lun_data:
            for one_host_access in lun_data['hostAccess']:
                if one_host_access['host']['id'] != host_id:
                    block_host_access_param = {
                        'host': {'id': one_host_access['host']['id']},
                        'accessMask': one_host_access['accessMask']
                    }
                    host_access.append(block_host_access_param)
        block_host_access_param = {
            'host': {'id': host_id},
            'accessMask': 1  # Production LUNs
        }
        host_access.append(block_host_access_param)
        modify_data = {
            'lunParameters': {
                'hostAccess': host_access
            }
        }
        self.rest.action("storageResource", unity_lun_id, "modifyLun", modify_data)

        # Now update the hostLUN and set the HLU
        search_filter = [
            'host.id eq "%s"' % host_id,
            'lun.id eq "%s"' % unity_lun_id
        ]
        search_response = self.rest.get_type_instances("hostLUN", self.HOST_LUN_FIELDS, search_filter).json()
        host_lun_data = search_response['entries'][0]['content']

        modify_host_lun_param = {
            'hostLunModifyList': [
                {
                    'hostLUN': {
                        'id': host_lun_data['id']
                    },
                    'hlu': hlu
                }
            ]
        }
        self.rest.action('host', host_id, 'modifyHostLUNs', modify_host_lun_param)

        sginfo = self.__sg_from_content(self.rest.get_type_instance_for_id("host", host_id, self.HOST_FIELDS))
        self.logger.debug("add_lun_to_storage_group: returning %s", self.__info2str(sginfo))
        return sginfo

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

        self.logger.info("Entering remove_luns_from_storage_group sg_name=%s hlus=%s", sg_name, hlus)

        if not sg_name:
            errmsg = "Invalid storage group name:" + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        if not hlus:
            errmsg = "hlus parameter must be number or list"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        hlu_list = []

        # If hlus parameter is a list, see if we can parse it
        if type(hlus) is list:
            # if it is list of HluAluPairs, then extract hlus
            if type(hlus[0]) is HluAluPairInfo:
                self.logger.debug(
                    "Getting HLU info from HluAluPairInfo list")
                for h in hlus:
                    hlu_list.append(str(h.hlu))

            # if it is list of numbers then concatenate
            elif type(hlus[0]) is int or type(hlus[0]) is str:
                self.logger.debug(
                    "Getting HLU info from list of %s" % type(hlus[0]))
                for h in hlus:
                    hlu_list.append(str(h))

            # Unmanageable list
            else:
                errmsg = "Unknown objects in list of HLU objects"
                self.logger.error(errmsg)
                raise SanApiOperationFailedException(errmsg, 1)

            self.logger.debug("List items processed okay")

        # Not dealing with a list, so it should be a single str or int
        elif type(hlus) is int or type(hlus) is str:
            hlu_list.append(str(hlus))
        else:
            errmsg = "Invalid HLU parameter"
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        self.logger.debug("remove_luns_from_storage_group: hlu_list=%s" % str(hlu_list))

        host_id = self.rest.get_id_for_name("host", sg_name)
        if host_id is None:
            raise SanApiEntityNotFoundException("Cannot get host for sg %s" % sg_name, 1)

        # Now update the hostLUN and set the HLU
        search_filter = [
            'host.id eq "%s"' % host_id,
            'hlu IN ( %s )' % ','.join(hlu_list)
        ]
        host_lun_response = self.rest.get_type_instances("hostLUN", self.HOST_LUN_FIELDS, search_filter).json()
        if 'entries' not in host_lun_response or len(host_lun_response['entries']) != len(hlu_list):
            msg = "Failed to get hostLUN entries for sg %s hlu %s" % (sg_name, ','.join(hlu_list))
            raise SanApiEntityNotFoundException(msg, 1)
        lun_ids = []
        for entry in host_lun_response['entries']:
            host_lun_data = entry['content']
            lun_ids.append(host_lun_data['lun']['id'])

        lun_response = self.rest.get_type_instances("lun", self.LUN_FIELDS, [self.rest.make_id_filter(lun_ids)]).json()
        for entry in lun_response['entries']:
            lun_data = entry['content']
            host_access = []
            if 'hostAccess' in lun_data:
                for one_host_access in lun_data['hostAccess']:
                    if one_host_access['host']['id'] != host_id:
                        block_host_access_param = {
                            'host': {'id': one_host_access['host']['id']},
                            'accessMask': one_host_access['accessMask']
                        }
                        host_access.append(block_host_access_param)
            modify_data = {
                'lunParameters': {
                    'hostAccess': host_access
                }
            }
            self.logger.debug("remove_luns_from_storage_group: Removing host access from lun %s" % lun_data['name'])
            self.rest.action('storageResource', lun_data['id'], 'modifyLun', modify_data)

        sginfo = self.__sg_from_content(self.rest.get_type_instance_for_id("host", host_id, self.HOST_FIELDS))
        self.logger.debug("remove_luns_from_storage_group: returning %s", self.__info2str(sginfo))
        return sginfo

    def storage_group_exists(self, sg_name):
        """
        Checks if a named storage group exists.

        :param sg_name: The name of the storage group to check for.
        :type sg_name: :class:`str`
        :returns: True if it exists, else False.
        :rtype: :class:`boolean`
        """
        self.logger.debug("storage_group_exists: sg_name=%s " % sg_name)
        result = self.rest.get_id_for_name("host", sg_name) is not None
        self.logger.debug("storage_group_exists: result=%s " % result)
        return result

    """ Storage Pool API Functions """

    def check_storage_pool_exists(self, sp_name):
        """
        Checks if a named storage pool already exists.

        :param sp_name: The name of the storage pool to check for.
        :type sp_name: :class:`str`
        :returns: True if it exists, else False.
        :rtype: :class:`boolean`
        """
        self.logger.debug("Entered check_storage_pool_exists with Storage Pool: %s " % sp_name)
        spinfo = self.rest.get_type_instance_for_name("pool", sp_name, self.POOL_FIELDS)
        if spinfo is None:
            return False
        else:
            msg = "Storage Pool {0} already exists.".format(sp_name)
            self.logger.debug(msg)
            return True

    def get_storage_pool(self, sp_name=None, sp_id=None):
        """
        Unity implementation of get_storage_pool.

        :param sp_name: The storage pool name.
        :type: :class:`str`
        :param sp_id: The storage pool ID.]
        :type: :class:`str`
        :returns: :class:`StoragePoolInfo`
        """
        self.logger.debug("Entered get_storage_pool with sp_name=%s and sp_id=%s", sp_name, sp_id)
        pool_content = None
        if sp_name is not None and sp_id is None:
            pool_content = self.rest.get_type_instance_for_name("pool", sp_name, self.POOL_FIELDS)
        elif sp_id is not None and sp_name is None:
            pool_content = self.rest.get_type_instance_for_id("pool", "pool_%s" % sp_id, self.POOL_FIELDS)
        else:
            sanapilib.raise_ex("Must specify either 'name' or 'spid' param", logger=self.logger)

        if pool_content is None:
            sanapilib.raise_ex("Pool not found: " + (sp_name if sp_name else sp_id), SanApiEntityNotFoundException)

        raid = 'UNKNOWN'
        if pool_content['raidType'] == 1:
            raid = '5'
        spinfo = StoragePoolInfo(
            pool_content['name'],
            int(pool_content['id'].split("_")[-1]),
            raid,
            str(pool_content['sizeTotal'] / (1024 * 1024)),
            str(pool_content['sizeFree'] / (1024 * 1024)),
            ((pool_content['sizeTotal'] - pool_content['sizeFree']) * 100) / float(pool_content['sizeTotal']),
            (pool_content['sizeSubscribed'] * 100) / float(pool_content['sizeTotal']),
            disks = str(pool_content['tiers'][0]['diskCount'])
        )
        self.logger.debug("get_storage_pool returning spinfo=%s", self.__info2str(spinfo))
        return spinfo

    def create_storage_pool(self, sp_name, disks, raid_type, array_specific_options=""):
        """
        Creates a new storage pool using the specified disks.

        :param sp_name: Name of the storage pool.
        :type sp_name: :class:`str`
        :param disks: The disks to use.
        :type disks: :class:`str`
        :param raid_type: The raid type.
        :type raid_type: :class:`str`
        :param array_specific_options: Optional parameters to be passed
        :type array_specific_options: :class:`str`
        :returns: A StoragePoolInfo object on successful pool creation.
        :rtype: :class:`StoragePoolInfo` object
        :raises SanApiEntityAlreadyExistsException: Raised if pool with same
            name already exists.
        :raises NotImplementedError: Function currently unimplemented.

        Example: Create a storage pool called 'SPone' of RAID 5 using
        disks 0_0_5, 0_0_6, 0_0_7, 0_0_8, 0_0_9:

        .. code-block:: python

            new_sp = create_storage_pool("SPone",
                                         "0_0_5 0_0_6 0_0_7 0_0_8 0_0_9","5")
        """

        raise NotImplementedError()

    def get_suitable_disk_group(self, number_of_disks, drive_type):
        """
        Finds an appropriate disk group

        :param number_of_disks: The number of disks desired for the pool
        :type number_of_disks: :class:`int`
        :param drive_type: The disk technology used.
              (This is hard-coded to SAS Flash 4 in the create_pool_with_disks function for now)
        :type drive_type: :class:`int`
        :raises SanApiEntityNotFoundException: Raised if no suitable disk group found
        """
        dg_response = self.rest.get_type_instances("diskGroup", self.DISK_GROUP_FIELDS)
        if dg_response is None:
            sanapilib.raise_ex("No Disk Group found", SanApiEntityNotFoundException)
        for entry in dg_response.json()['entries']:
            dg_content = entry['content']
            if dg_content['diskTechnology'] == drive_type \
                    and dg_content['totalDisks'] >= number_of_disks:
                self.logger.debug("dg_id is :\"{0}\"".format(dg_content['id']))
                return dg_content['id']
        sanapilib.raise_ex("Suitable Disk Group not found", SanApiEntityNotFoundException)

    def create_pool_with_disks(self, sp_name, number_of_disks, raid_type):
        """
        Creates the storage pool using the number of disks, name and raid type required.

        :param sp_name: The name of the new storage pool.
        :type sp_name: :class:`str`
        :param number_of_disks: The number of disks in the pool.
        :type number_of_disks: :class:`int`
        :param raid_type: The raid type of the storage pool.
        :type raid_type: :class:`str`
        :raises SanApiOperationFailedException: Raised if the storage pool already exists
        """
        stripe_length = 0
        raid_type = int(raid_type)
        number_of_disks = int(number_of_disks)
        drive_type = 8
        raid_types_to_min_disks = {
            1: 3,
            5: 6,
            10: 3,
            6: 7
        }
        if number_of_disks < raid_types_to_min_disks.get(raid_type):
            errmsg = "Number of disks chosen(\"{0}\") is less than the minimum:(\"{1}\")" \
                     "for RAID (\"{2}\")".format(number_of_disks, raid_types_to_min_disks.get(raid_type), raid_type)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        # The stripe length is calculated assuming the raid level is 5, which is hard-coded for now.
        if number_of_disks <= 9:
            stripe_length = 5
        elif 10 <= number_of_disks < 14:
            stripe_length = 9
        elif number_of_disks >= 14:
            stripe_length = 13

        self.logger.debug("Attempting to create Storage Pool:(\"{0}\") with RAID:(\"{1}\")"
                          "using disks:(\"{2}\")".format(sp_name, raid_type, number_of_disks))
        converted_raid_type = sanapilib.convert_raid_type_to_unity(raid_type, "pool")
        self.logger.debug("converted raid type: \"{0}\"".format(converted_raid_type))
        request_data = {
            'name': sp_name,
            'description': "SAN storage pool for ENM",
            'addRaidGroupParameters': [{
                "dskGroup": {"id": self.get_suitable_disk_group(number_of_disks, drive_type)},
                "numDisks": number_of_disks,
                "raidType": converted_raid_type,
                "stripeWidth": stripe_length
            }],
        }

        try:
            self.rest.create_instance("pool", request_data)
        except SanApiOperationFailedException:
            errmsg = "Creation of storage pool: \"{0}\" failed".format(sp_name)
            self.logger.debug(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        return self.get_storage_pool(sp_name)

    def delete_storage_pool(self, sp_name):
        """
        Delete a storage pool.

        :param sp_name: The name of the storage pool.
        :type sp_name: :class:`str`
        """
        if not sp_name:
            errmsg = "Storage Pool name was not specified"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)
        sp_id = self.rest.get_id_for_name("pool", sp_name)
        self.rest.delete_instance("pool", sp_id)
        return True

    def modify_storage_pool(self, sp_name, hwm_value):
        """
        Modify a storage pool.

        :param sp_name: The name of the storage pool.
        :type sp_name: :class:`str`
        :param hwm_value: The value for snapPoolFullHWM
        :type hwm_value: :class:`int`
        """
        self.logger.debug(" NotImplementedError()")
        pass


    """ Hot Spare API Functions """

    def configure_hs(self, args):
        raise NotImplementedError()

    def get_hs_policy(self, policy, disk_type):
        raise NotImplementedError()

    def get_hs_policy_list(self):
        raise NotImplementedError()

    def get_hs_luns(self):
        raise NotImplementedError()

    """ Snapshot API Functions """

    def get_snapshots(self, lun_name=None, lun_id=None):
        """
        Returns a list of SnapshotInfo objects, one for each Snapshot found
        in array. If lun_name is provided, a list of SnapshotInfo objects is
        returned for all Snapshots associated with that LUN.
        If no snapshots are found, then an empty list is returned.

        :param lun_name: Optional, a string containing a LUN name, used for
                filtering the snapshots to only those related to that LUN.
        :type lun_name: :class:`str`
        :param lun_id: Optional, a string or int containing a LUN ID, used for
                filtering the snapshots to only those related to that LUN.
        :type lun_id: :class:`str` or :class:`int`
        :returns: A list of SnapshotInfo objects, one for each Unity Snapshot
                found on array.
        :rtype: list of :class:`SnapshotInfo`
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Get all snapshots:

        .. code-block:: python

            get_snapshots()

        Example 2: Get all snapshots from Lun 'abcde':

        .. code-block:: python

            get_snapshots('abcde')
        """
        self.logger.debug("Entered get_snapshots lun_name=%s, lun_id=%s", lun_name, lun_id)

        if lun_name and lun_id:
            errmsg = "Both lun name and lun id were specified"
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        search_filter = None
        lun_id_map = {}
        if lun_name is not None:
            unity_lun_id = self.rest.get_id_for_name("lun", lun_name)
            if unity_lun_id is None:
                sanapilib.raise_ex("LUN not found: %s" % lun_name, SanApiEntityNotFoundException)
            search_filter = ['lun.id eq "%s"' % unity_lun_id]
            lun_id_map[unity_lun_id] = lun_name
        elif lun_id is not None:
            search_filter = ['lun.id eq "sv_%s"' % lun_id]

        snap_response = self.rest.get_type_instances('snap', self.SNAP_FIELDS, search_filter)

        # First we need to get the name of any "owning" lun
        if lun_name is None:
            lun_ids = []
            for entry in snap_response.json()['entries']:
                snap_content = entry['content']
                if "lun" in snap_content.keys():
                    if snap_content['lun']['id'] not in lun_ids:
                        lun_ids.append(snap_content['lun']['id'])
            if len(lun_ids) > 0:
                lun_name_response = self.rest.get_type_instances(
                    'lun',
                    ['id', 'name'],
                    [self.rest.make_id_filter(lun_ids)]
                )
                for entry in lun_name_response.json()['entries']:
                    lun_id_map[entry['content']['id']] = entry['content']['name']

        results = []
        for entry in snap_response.json()['entries']:
            snap_content = entry['content']
            if "lun" in snap_content.keys():
                snapinfo = SnapshotInfo(
                    snap_content['lun']['id'].split('_')[-1],
                    snap_content['name'],
                    snap_content['creationTime'],
                    self.SNAP_STATES[snap_content['state']],
                    lun_id_map[snap_content['lun']['id']],
                    snap_content['description']
                )
                self.logger.debug("get_snapshots: snapinfo=%s", self.__info2str(snapinfo))
                results.append(snapinfo)

        self.logger.debug("get_snapshots: returns %s SnapshotInfos", len(results))

        return results

    def get_snapshot(self, snap_name):
        """
        Returns a SnapshotInfo object.
        snap_name must be provided, a SnapshotInfo Object is returned for the
        specified  Snapshot.
        If no snapshot is found, then an exception is raised.

        :param snap_name: A string containing the name of a snapshot.
        :type snap_name: str
        :returns: A SnapshotInfo object or None if no snapshot is found.
        :rtype: :class:`SnapshotInfo`
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Get snapshot 'fuego':

        .. code-block:: python

            get_snapshot('fuego')
        """
        self.logger.debug("Entered get_snapshot with %s", snap_name)

        if not isinstance(snap_name, basestring):
            errmsg = "Snapshot name is not a string %s " % type(snap_name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        snap_content = self.rest.get_type_instance_for_name("snap", snap_name, self.SNAP_FIELDS)
        if snap_content is None:
            sanapilib.raise_ex("Snap not found: %s" % snap_name, SanApiEntityNotFoundException)

        snapinfo = None
        if "lun" in snap_content.keys():
            lun_content = self.rest.get_type_instance_for_id("lun", snap_content['lun']['id'], ['name'])
            snapinfo = SnapshotInfo(
                snap_content['lun']['id'].split('_')[-1],
                snap_content['name'],
                snap_content['creationTime'],
                self.SNAP_STATES[snap_content['state']],
                lun_content['name'],
                snap_content['description']
            )
            self.logger.debug("get_snapshot: snapinfo=%s", self.__info2str(snapinfo))

        return snapinfo

    def create_snapshot_with_id(self, lun_id, snap_name, description=None):
        """
        Creates a snapshot and returns a SnapshotInfo object
        representing the snapshot created.

        :param lun_id: A string containing the ID of the LUN to snap.
        :type lun_id: :class:`str`
        :param snap_name: A string containing the name of the snapshot.
        :type snap_name: :class:`str`
        :param description: The snapshot description.
        :type description: :class:`str`
        :returns: A SnapshotInfo object representing the snapshot created.
        :rtype: :class:`SnapshotInfo`
        :raises SanApiEntityAlreadyExistsException: Raised if a snapshot with
            the same name already exists for the LUN.
        :raises SanApiEntityNotFoundException: Raised if a LUN with the
            lun_name is not found.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: For LUN '231', create a snapshot called 'fuego':

        .. code-block:: python

            create_snapshot('231','fuego')
            #The snapshot name on the SAN will be 'fuego'

        """
        lun_id = sanapilib.validate_int_and_make_string(lun_id)
        lun = self.get_lun(lun_id=lun_id)
        lun_name = lun.name
        lun_id = self.rest.get_id_for_name("lun", lun_name)

        self.logger.debug("Entering create_snapshot lun_name=%s snap_name=%s description=%s",
                          lun_name, snap_name, description)

        create_args = {
            'storageResource': {
                'id': lun_id,
            },
            'name': snap_name
        }
        if description is not None:
            create_args['description'] = description

        create_response = self.rest.create_instance("snap", create_args).json()

        snap_content = self.rest.get_type_instance_for_id("snap", create_response['content']['id'], self.SNAP_FIELDS)
        snapinfo = SnapshotInfo(
            snap_content['lun']['id'].split('_')[-1],
            snap_content['name'],
            snap_content['creationTime'],
            self.SNAP_STATES[snap_content['state']],
            lun_name,
            snap_content['description']
        )
        self.logger.debug("create_snapshot: snapinfo=%s", self.__info2str(snapinfo))
        return snapinfo

    def create_snapshot(self, lun_name, snap_name, description=None):
        """
        Creates a snapshot and returns a SnapshotInfo object
        representing the snapshot created.

        :param lun_name: A string containing the name of the LUN to snap.
        :type lun_name: :class:`str`
        :param snap_name: A string containing the name of the snapshot.
        :type snap_name: :class:`str`
        :param description: The snapshot description.
        :type description: :class:`str`
        :returns: A SnapshotInfo object representing the snapshot created.
        :rtype: :class:`SnapshotInfo`
        :raises SanApiEntityAlreadyExistsException: Raised if a snapshot with
            the same name already exists for the LUN.
        :raises SanApiEntityNotFoundException: Raised if a LUN with the
            lun_name is not found.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: For LUN 'spLUN1', create a snapshot called 'fuego':

        .. code-block:: python

            create_snapshot('spLUN1','fuego')
            #The snapshot name on the SAN will be 'fuego'

        """
        self.logger.debug("Entering create_snapshot lun_name=%s snap_name=%s description=%s",
                          lun_name, snap_name, description)

        sanapilib.validate_string(lun_name)
        sanapilib.validate_string(snap_name)

        lun_id = self.rest.get_id_for_name("lun", lun_name)
        if lun_id is None:
            sanapilib.raise_ex("LUN not found: %s" % lun_name, SanApiEntityNotFoundException)

        create_args = {
            'storageResource': {
                'id': lun_id,
            },
            'name': snap_name
        }
        if description is not None:
            create_args['description'] = description

        create_response = self.rest.create_instance("snap", create_args).json()

        snap_content = self.rest.get_type_instance_for_id("snap", create_response['content']['id'], self.SNAP_FIELDS)
        snapinfo = SnapshotInfo(
            snap_content['lun']['id'].split('_')[-1],
            snap_content['name'],
            snap_content['creationTime'],
            self.SNAP_STATES[snap_content['state']],
            lun_name,
            snap_content['description']
        )
        self.logger.debug("create_snapshot: snapinfo=%s", self.__info2str(snapinfo))
        return snapinfo

    def restore_snapshot(self, lun_name, snap_name,
                         delete_backupsnap=True, backup_name=None):
        """
        Restores a snapshot and returns True if successful.
        A unique backup snapshot name is created by combining "restore\_"
        and snap_name. This will enable easy location of created backups.

        :param lun_name: A string containing the name of the LUN to snap.
        :type lun_name: :class:`str`
        :param snap_name: A string containing the name of the snapshot.
        :type snap_name: :class:`str`
        :param delete_backupsnap: A boolean signifying whether to delete
            the backup snapshot created by the command or to keep it.
        :type  delete_backupsnap: :class:`boolean`
        :param backup_name: A string for the name of the backup snapshot.
        :type backup_name: :class:`str`
        :returns: True if snapshot restore successful, otherwise False.
        :rtype: :class:`boolean`
        :raises SanApiEntityAlreadyExistsException: Raised if a snapshot with
            the same backup name already exists for the LUN.
        :raises SanApiEntityNotFoundException: Raised if a LUN with the
            lun_name is not found.
        :raises SanApiEntityNotFoundException: Raised if a snapshot with the
            same snap_name is not found.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: For LUN 'spLUN1', restore a snapshot called 'spLUN1_tine'
        and keep the created backup snapshot:

        .. code-block:: python

            create_snapshot('spLUN1','fuego')
            restore_snapshot('spLUN1','tine', False)
            #The snapshot will be restored and a backup snapshot with the name
            #'restore_spLUN1_tine' will be kept.
        """

        self.logger.debug("restore_snapshot; lun_name=%s snap_name=%s delete_backupsnap=%s", lun_name, snap_name,
                          delete_backupsnap)

        sanapilib.validate_string(lun_name)
        sanapilib.validate_string(snap_name)

        if backup_name:
            backup_snapshot_name = backup_name
        else:
            backup_snapshot_name = "_".join(["restore", snap_name])

        restore_data = {
            'copyName': backup_snapshot_name
        }
        restore_response = self.rest.action('snap', 'name:%s' % snap_name, 'restore', restore_data)
        if delete_backupsnap:
            self.rest.delete_instance('snap', restore_response.json()['content']['backup']['id'])

        return True

    def restore_snapshot_by_id(self, lun_id, snap_name,
                               delete_backupsnap=True, backup_name=None):
        """
        Restores a snapshot and returns True if successful.
        A unique backup snapshot name is created by combining "restore\_"
        and snap_name. This will enable easy location of created backups.

        :param lun_id: A string containing the name of the LUN to snap.
        :type lun_id: :class:`str`
        :param snap_name: A string containing the name of the snapshot.
        :type snap_name: :class:`str`
        :param delete_backupsnap: A boolean signifying whether to delete
            the backup snapshot created by the command or to keep it.
        :type  delete_backupsnap: :class:`boolean`
        :param backup_name: A string for the name of the backup snapshot.
        :type backup_name: :class:`str`
        :returns: True if snapshot restore successful, otherwise False.
        :rtype: :class:`boolean`
        :raises SanApiEntityAlreadyExistsException: Raised if a snapshot with
            the same backup name already exists for the LUN.
        :raises SanApiEntityNotFoundException: Raised if a LUN with the
            lun_name is not found.
        :raises SanApiEntityNotFoundException: Raised if a snapshot with the
            same snap_name is not found.
        :raises NotImplementedError: Function currently unimplemented.
        """
        lun = self.get_lun(lun_id=lun_id)
        return self.restore_snapshot(lun.name,
                                     snap_name,
                                     delete_backupsnap=delete_backupsnap,
                                     backup_name=backup_name)

    def delete_snapshot(self, snap_name):
        """
        Deletes a snapshot and returns True if successful.

        :param snap_name: A string containing the name of the snapshot.
        :type snap_name: :class:`str`
        :returns: True if snapshot successfully deleted, otherwise False.
        :rtype: :class:`boolean`
        :raises SanApiEntityNotFoundException: Raised if a snapshot with the
            same snap_name is not found.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Delete a snapshot called 'spLUN1_tine':

        .. code-block:: python

            create_snapshot('spLUN1','fuego')
            delete_snapshot('spLUN1_tine')
            #The snapshot will then be deleted.
        """
        self.logger.debug("delete_snapshot; snap_name=%s", snap_name)
        self.rest.delete_instance('snap', 'name:%s' % snap_name)
        return True

    """ SAN Info API Function """

    def get_san_info(self):
        """
        Gets SAN information

        :return: SanInfo object
        :raises SanApiOperationFailedException: Raised if the method fails at any point.
        """
        debug_message = ("Entering method {0}.get_san_info"
                         .format(self.__class__.__name__))
        self.logger.debug(debug_message)

        system_response = self.rest.get_type_instances("system", self.SYSTEM_FIELDS).json()
        instsw_response = self.rest.get_type_instances("installedSoftwareVersion", self.INSTSW_FIELDS).json()

        return SanInfo(
            instsw_response['entries'][0]['content']['version'],
            system_response['entries'][0]['content']['model'],
            system_response['entries'][0]['content']['serialNumber']
        )

    """ SAN Alerts API Functions """

    def get_san_alerts(self):
        """
        Gets all SAN alerts.
        Returned alert fields are 'severity', 'message', 'description', 'state'.

        :return: SanAlert object
        :raises: SanApiOperationFailedException: Raised if the method fails at any point.
        """
        debug_message = ("Entering menthod {0}.get_san_alerts"
                         .format(self.__class__.__name__))
        self.logger.debug(debug_message)

        alert_response = self.rest.get_type_instances("alert", self.ALERT_FIELDS).json()

        unity_alerts = []

        for alert in alert_response['entries']:
            unity_alerts.append(SanAlert(alert['content']['message'],
                                         alert['content']['description'],
                                         alert['content']['severity'],
                                         alert['content']['state']))

        return unity_alerts

    def get_hw_san_alerts(self):
        """Gets all SAN DIMM alerts
        Returned hw alert fields are 'id', 'health'.

        :return: SanAlert object
        :raises: SanApiOperationFailedException: Raised if the method fails at any point.
        """
        debug_message = ("Entering method {0}.get_hw_san_alerts"
                         .format(self.__class__.__name__))
        self.logger.debug(debug_message)

        alert_response = self.rest.get_type_instances("memoryModule",self.HW_ALERT_FIELDS).json()

        hw_alert_filter = 5
        hw_minor_alert_filter = [7, 0]
        san_hw_alerts_list = []

        for alert in alert_response['entries']:
            san_hw_alerts_list.append(SanHwAlert(alert['content']['id'],
                                    alert['content']['health']['value'],
                                    alert['content']['health']['descriptionIds'],
                                    alert['content']['health']['descriptions']))
        unity_hw_alert = []
        unity_hw_alert = [alert for alert in san_hw_alerts_list if alert.value != hw_alert_filter]
        unity_hw_alerts = []
        if unity_hw_alert:
            for alert in unity_hw_alert:
                if alert.value in hw_minor_alert_filter:
                    msg = ""
                    msg += str(alert.value) + "" + str(alert.id) + "" + str(alert.descriptions)
                else:
                    msg = ""
                    msg += str(alert.id) + "" + str(alert.descriptions)
                unity_hw_alerts.append(msg)

        return unity_hw_alerts

    def get_filtered_san_alerts(self, alert_filter):
        """
        Get SAN alerts that match a filter.
        Filtering is performed by the server, the query response contains matching alerts only.
        Returned alert fields are 'severity', 'message', 'description', 'state'.

        :return: SanAlert object
        :raises: SanApiOperationFailedException: Raised if the method fails at any point.
        """
        debug_message = ("Entering method {0}.get_san_alerts"
                         .format(self.__class__.__name__))
        self.logger.debug(debug_message)
        self.logger.info('alert_filter: %s' % alert_filter)

        alert_response = self.rest.get_type_instances("alert", self.ALERT_FIELDS, alert_filter)

        if alert_response.status_code == 200:
            unity_alerts = []

            for alert in alert_response.json()['entries']:
                unity_alerts.append(SanAlert(alert['content']['message'],
                                             alert['content']['description'],
                                             alert['content']['severity'],
                                             alert['content']['state']))
            return unity_alerts
        else:

            errmsg = 'alerts query failed with http_error={0}; reason={1}' \
                .format(alert_response.status_code, alert_response.reason)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

    """ Internal Functions """

    def __get_hba_for_initiators(self, initiator_filter):
        hbasp_list = []

        self.logger.debug("__get_hba_for_initiators: filter=%s", initiator_filter)

        initiator_response = self.rest.get_type_instances('hostInitiator', self.HOST_INITATOR_FIELDS, initiator_filter)
        path_id_list = []
        path_to_initiator = {}
        path_to_is_ignored = {}
        for entry in initiator_response.json()['entries']:
            initiator_content = entry['content']
            if 'paths' in initiator_content and 'initiatorId' in initiator_content:
                for path in initiator_content['paths']:
                    path_id_list.append(path['id'])
                    path_to_initiator[path['id']] = initiator_content['initiatorId']
                    path_to_is_ignored[path['id']] = initiator_content['isIgnored']

        if len(path_id_list) > 0:
            if len(initiator_filter) > 0:
               path_response = self.rest.get_type_instances(
                    'hostInitiatorPath',
                    self.HOST_INITATOR_PATH_FIELDS,
                    [self.rest.make_id_filter(path_id_list)]
               )
            else:
               path_response = self.rest.get_type_instances(
                    'hostInitiatorPath',
                    self.HOST_INITATOR_PATH_FIELDS
               )

            for entry in path_response.json()['entries']:
                path_content = entry['content']
                if 'fcPort' in path_content:
                    fc_port_id = path_content['fcPort']['id']
                    fc_port_id_parts = fc_port_id.split('_')
                    sp = fc_port_id_parts[0]
                    if sp == 'spa':
                        sp = sanapilib.STORAGE_PROCESSOR_A
                    else:
                        sp = sanapilib.STORAGE_PROCESSOR_B
                    port_num = fc_port_id_parts[-1][2:]
                    self.logger.debug("__get_hba_for_initiators fc_port_id=%s sp=%s port_num=%s",
                                      fc_port_id, sp, port_num)
                    if entry['content']['id'] in path_to_initiator:
                        hbauid = path_to_initiator[path_content['id']]
                        isignored = path_to_is_ignored[path_content['id']]
                        self.logger.debug("__get_hba_for_initiators: adding hbasp hbauid=%s sp=%s port_num=%s "
                                          "isignored=%s", hbauid, sp, port_num, isignored)
                        hbasp_list.append(HbaInitiatorInfo(hbauid, sp, port_num, isignored=isignored))

        self.logger.debug("__get_hba_for_initiators: returning %s HbaInitiatorInfos", len(hbasp_list))

        return hbasp_list

    def __sg_from_content(self, host_content):
        hbasp_list = None
        if 'fcHostInitiators' in host_content:
            initiatorid_list = []
            for fcHostInitiator in host_content['fcHostInitiators']:
                initiatorid_list.append(fcHostInitiator['id'])
            hbasp_list = self.__get_hba_for_initiators([self.rest.make_id_filter(initiatorid_list)])

        hlualu_list = None
        if 'hostLUNs' in host_content:
            hlualu_list = []
            host_lun_id_list = []
            for hostLUN in host_content['hostLUNs']:
                host_lun_id_list.append(hostLUN['id'])
            host_lun_response = self.rest.get_type_instances(
                'hostLUN',
                self.HOST_LUN_FIELDS,
                [self.rest.make_id_filter(host_lun_id_list)]
            )
            for entry in host_lun_response.json()['entries']:
                host_lun_content = entry['content']
                alu = int(host_lun_content['lun']['id'][3:])
                self.logger.debug("sg_from_content lun id=%s hlu=%s alu=%s", host_lun_content['lun']['id'],
                                  host_lun_content['hlu'], alu)
                hlualu_list.append(HluAluPairInfo(host_lun_content['hlu'], alu))

        sgi = StorageGroupInfo(host_content['name'], self.DUMMY_UID, False, hbasp_list, hlualu_list)
        self.logger.debug("sg_from_content: StorageGroupInfo=%s", self.__info2str(sgi))
        return sgi

    def __connect_hbas_to_host(self, sg_name, host_name, wwn, init_type, failovermode, arraycommpath):
        # First we check if the host_name has a value, if so we make sure the description field in the host_content
        # matches

        if not sg_name:
            errmsg = "Invalid storage group name:" + str(sg_name)
            self.logger.error(errmsg)
            raise SanApiCriticalErrorException(errmsg, 1)

        if not sanapilib.is_valid_wwn(wwn):
            errmsg = "Invalid HBA WWN:" + str(wwn)
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

        host_content = self.rest.get_type_instance_for_name('host', sg_name, self.HOST_DESCRIPTION_FIELDS)
        if host_content is None:
            raise SanApiEntityNotFoundException("Cannot get host for sg %s" % sg_name, 1)

        if host_name is not None:
            if 'description' not in host_content or host_name != host_content['description']:
                self.rest.action('host', host_content['id'], 'modify', {'description': host_name})

        request_data = {
            'host': {'id': host_content['id']},
            'initiatorSourceType': int(init_type),
            'failoverMode': int(failovermode),
            'isLunZEnabled': arraycommpath == '1'
        }
        search_response = self.rest.get_type_instances(
            "hostInitiator",
            self.HOST_INITATOR_MODIFY_FIELDS,
            ['initiatorId eq "%s"' % wwn]
        ).json()
        if 'entries' not in search_response or len(search_response['entries']) == 0:
            request_data['initiatorType'] = 1  # FC
            request_data['initiatorWWNorIqn'] = wwn
            self.rest.create_instance("hostInitiator", request_data)
        else:
            # Initiator already exists
            initiator_content = search_response['entries'][0]['content']
            modify_required = (
                'parentHost' not in initiator_content or
                initiator_content['parentHost']['id'] != host_content['id'] or
                'failoverMode' not in initiator_content or
                initiator_content['failoverMode'] != request_data['failoverMode'] or
                'isLunZEnabled' not in initiator_content or
                initiator_content['isLunZEnabled'] != request_data['isLunZEnabled']
            )
            if modify_required:
                self.rest.action('hostInitiator', initiator_content['id'], 'modify', request_data)

        self.logger.info("create_host_initiator completed successfully")

    def __make_lun_info(self, lun_data, pools=None):
        lunid = int(lun_data['id'][3:])
        name = lun_data['name']
        uid = lun_data['wwn']
        size = lun_data['sizeTotal'] / (1024 * 1024)
        raid = 1
        if lun_data['currentNode'] == 0:
            controller = sanapilib.STORAGE_PROCESSOR_A
        else:
            controller = sanapilib.STORAGE_PROCESSOR_B
        container_type = sanapilib.CONTAINER_STORAGE_POOL

        self.logger.debug("make_lun_info: Creating %s lun info object: %s (%s) %s", container_type, lunid, name,
                          id)

        pool_id = lun_data['pool']['id']
        if pools is not None and pool_id in pools:
            pool_name = pools[pool_id]
        else:
            pool_content = self.rest.get_type_instance_for_id("pool", pool_id, ['name'])
            pool_name = pool_content['name']
            if pools is not None:
                pools[pool_id] = pool_name
        container = pool_name

        luninfo = LunInfo(lunid, name, uid.encode('ascii'), container, str(size), container_type, raid, controller)
        self.logger.debug("make_lun_info: returning %s", self.__info2str(luninfo))
        return luninfo

    def __unity_lun_num(self, unity_id):
        lun_num = int(unity_id[3:])
        self.logger.debug("unity_lun_num: unity_id=%s lun_num=%s" % (unity_id, lun_num))
        return lun_num

    @staticmethod
    def __info2str(info):
        return ' '.join(str(info).replace("\n", ", ").split())
