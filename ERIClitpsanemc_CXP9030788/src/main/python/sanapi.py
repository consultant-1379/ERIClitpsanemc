"""
File_name: sanapi.py
Version: ${project.version}

Includes the base class for a SanApi object which acts as an interface
definition. The non-class function api_builder is used to return an
instantiated object of one of the available derived classes implementing
the API functionality

"""

import os.path
from ConfigParser import NoOptionError

from sanapicfg import SANAPICFG
from sanapiexception import SanApiException, \
                            SanApiCriticalErrorException


def api_builder(array_type, logger=None):
    """
    Function to return an instantiated object representing the appropriate
    array type, currently Vnx1 or Vnx2. Hard coded values currently as
    the types are not expected to change.  In the future it may be beneficial
    to make this dynamic, iterating through a list of arrays (perhaps loaded
    from ini file) and creating the appropriate object.

    :param array_type: The type of array, currently either Vnx1 or Vnx2.
    :type array_type: :class:`str`
    :param logger: The logger object, if supplied.
    :type logger: :class:`logger`
    :returns: The return an instantiated object representing the appropriate
        array type.
    :rtype: :class:`apiObj`

    Example 1: Default logging:

        .. code-block:: python

            apiObj = api_builder("Vnx1")

    Example 2: Custom logger:

        .. code-block:: python

            vnx = api_builder("Vnx1", customLogger)

    """

    try:
        cfg = SANAPICFG

    except SanApiException, exce:
        raise SanApiCriticalErrorException("Failed to load config file: " \
                                                    + str(exce), 1)

    except Exception, exce:
        raise SanApiCriticalErrorException("Failed to load config file: " \
                                                    + str(exce), 1)

    try:
        supported_arrays = cfg.get('General', \
                                   'SupportedArrays').strip().split(',')

    except NoOptionError, exce:
        # print "Failed to get option %s " % str(e)
        raise SanApiCriticalErrorException(str(exce), 1)

    if array_type:
        array_type = array_type.lower().strip()
    else:
        raise SanApiCriticalErrorException("Array type not specified", 1)

    if not array_type in (cmpat.lower().strip() for cmpat in supported_arrays):
        msg = "Unknown array type, %s " % array_type
        raise SanApiCriticalErrorException(msg, 1)

    if array_type == "vnx1":
        from vnx1api import Vnx1Api
        apiObj = Vnx1Api(logger)
    elif array_type == "vnx2":
        from vnx2api import Vnx2Api
        apiObj = Vnx2Api(logger)
    elif array_type == "unity":
        from unityapi import UnityApi
        apiObj = UnityApi(logger)
    else:
        msg = "Unable to import module for array type %s" % array_type
        raise SanApiCriticalErrorException(msg, 1)

#     arrayFile = array_type + 'api'
#     arrayClassName = array_type.capitalize() + 'Api'
#
#     module = __import__(arrayFile)
#     arrayClass = getattr(module, arrayClassName)
#     apiObj = arrayClass(logger)

    return apiObj


def get_api_version():
    """
    Returns the SAN API Version, this is the same as the RPM version.

    :returns: The SAN API Version.
    :rtype: :class:`str`

    """

    if "${project.version}".startswith("$"):
        return "unknown version"
    return "${project.version}"


class SanApi(object):
    """
    Base class declaring the generic interface for SAN API.
    Derived classes for specific array types (e.g. Vnx1) implement the methods
    declared in this base class to provide the necessary functionality to
    interact with the specific SAN array.
    When methods in the class fail they raise SanApiExceptions. Detailed
    failure information will be available in the exception string. All
    methods in the base class raise NotImplemented exceptions to indicate
    that the base class is not an implementation for any array (the
    exception being the __init__ constructor which handles reading the SAN
    API configuration file).

    """

    def __init__(self):
        """
        Constructor. Reads the configuration file. Derived classes will also
        set up logging, and a logging object is passed to the constructor.

        Example 1: Use the related 'builder' function to get a Vnx1 API
            object:

        .. code-block:: python

            apiObj = api_builder("Vnx1", logger)

        Example 2: Use the constructor of the derived Vnx1 class directly:

        .. code-block:: python

            apiObj = Vnx1Api(logger)

        Example 3: Use Vnx1 constructor with default logging:

        .. code-block:: python

            apiObj = Vxn1Api()

        """

        try:
            self._cfg = SANAPICFG
        except SanApiException, exce:
            raise SanApiCriticalErrorException(str(exce), 1)

        except Exception, exce:
            raise SanApiCriticalErrorException(str(exce), 1)

    def initialise(self, sp_ips, username, password, scope,
                   getcert=True,
                   vcheck=True):
        """
        Initialise the SAN API Object. The required parameters are defined
        for a VNX array. This may change when new array types are defined.

        :param sp_ips: A tuple containing IP addresses of the SAN, must
            contain at least one address.
        :type sp_ips: :class:`tuple`
        :param username: Username to connect to the SAN with.
        :type username: :class:`str`
        :param password: Password of the connecting user.
        :type password: :class:`str`
        :param scope: Scope of user, Global or Local.
        :type scope: :class:`str`
        :param getcert: Optional, defaults to True. If set to True then API
            contacts SAN to retrieve security certificate if needed.
        :type getcert: :class:`boolean`
        :param vcheck: Defaults to True. If set to True then API retrieves
            the FLARE/OE version of a VNX and the NAVISECCLI version of a
            host.
        :type vcheck: :class:`boolean`
        :raises NotImplementedError: Function currently unimplemented.

        Example: Initialise a Vnx1 API object returned from the builder
            function:

        .. code-block:: python

            vnx = api_builder("Vnx1", logger)
            vnx.initialise((spa_ip, spb_ip), user, passwd, 'Global')

        """

        raise NotImplementedError()

    """ LUN API Functions """

    def get_lun(self, lun_id=None, lun_name=None):
        """
        Searches for a LUN matching the given name or id on the SAN.
        Returns a LunInfo object corresponding to the matching LUN.

        .. note::

            Either lun_id or lun_name should be specified but not both.
            Only storage pool LUNs can be searched by name.

        :param lun_id: Optional, the ID of LUN to find.
        :type lun_id: :class:`str` or :class:`int`
        :param lun_name: Optional, the name of LUN to find.
        :type lun_name: :class:`str`
        :returns: LunInfo object corresponding to the matching LUN.
        :rtype: :class:`LunInfo`
        :raises SanApiEntityNotFoundException: Raised if no matching LUN is
            found.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Find LUN with id 47:

        .. code-block:: python

            LunInfoObj = get_lun(lun_id="47")

        Example 2: Find size of LUN with name bill:

        .. code-block:: python

            LunInfoObj = get_lun(lun_name="bill")
            lun_size = LunInfoObj.size

        """
        raise NotImplementedError()

    def get_luns(self, container_type=None, container=None, sg_name=None):
        """
        Returns a list of LUNs for the given container type. If the container
        is specified, the list is limited to that specific container.
        Returns a list of LunInfo objects.

        :param container_type: Optional, if specified limit the list of
            LUNs to that container type.
        :type container_type: :class:`str`
        :param container: Optional, if specified limit the list of
            LUNs to that specific container. If specifying this option,
            container_type must also be specified.
        :type container: :class:`str`
        :param sg_name: Optional, if specified, limit the list of LUNs
           returned to the given storage group. If specifying this option,
           container_type or container should not be specified.
        :type sg_name: :class:`str`
        :returns: List of LUNs
        :rtype: :class:`list`
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Get a list of all LUNs on the SAN:

        .. code-block:: python

            LunInfoObjList = get_luns()

        Example 2: Get a list of all LUNs in all storage pools:

        .. code-block:: python

            LunInfoObjList = get_luns(container_type="StoragePool")

        Example 3: Get a list of all LUNs in specific storage pool mypool:

        .. code-block:: python

            LunInfoObjList = get_luns(container_type="StoragePool",
                                      container="mypool")

        Example 4: Get a list of all LUNs all Raid Groups:

        .. code-block:: python

            LunInfoObjList = get_luns(container_type="RaidGroup")

        Example 5: Get a list of all LUNs in specific raid group id 4:

        .. code-block:: python

            LunInfoObjList = get_luns(container_type="RaidGroup",
                                      container="4")

        Example 6: Get a list of all LUNs in storage group mysg:

        .. code-block:: python

            LunInfoObjList = get_luns(sg_name="mysg")

        """
        raise NotImplementedError()

    def expand_pool_lun(self, lun_name, size):
        """
        Increase the size of a storage pool LUN.
        If the new size specified is higher than the existing
        size and the requirements for expansion are met,
        the LUN would expand. If the new size is less than
        the existing size, an error message will be displayed

        :param lun_name: The name of the pool LUN.
        :type lun_name: :class:`str`
        :param size: Size to expand LUN to.
        :type size: :class:`str`
        :raises SanAPiOperationFailedException: Raised if error
            occurred.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            expand_pool_lun(lun_name="lun123", size="200gb")

        """

        raise NotImplementedError()

    def create_lun(self, lun_name, size, container_type, container,
                   storage_processor="a", raid_type="", lun_type="thick",
                   lun_id="auto", ignore_thresholds=False,
                   array_specific_options=""):
        """
        Creates a LUN in a storage pool or raid group.

        :param lun_name: Name of LUN to create.
        :type lun_name: :class:`str`
        :param size: Size of LUN to create eg. 500Mb, 40Gb, 1Tb.
        :type size: :class:`str`
        :param container_type: The container type, StoragePool for storage
            pool or RaidGroup for raid group.
        :type container_type: :class:`str`
        :param container: ID of raid group or name of storage pool.
        :type container: :class:`str`
        :param storage_processor: A or B, default is A.
        :type storage_processor: :class:`str`
        :param raid_type: Raid type e.g. 1, 0, 5, 10.
            This parameter is only required for Raid Group LUNs.
        :type raid_type: :class:`str`
        :param lun_type: The LUN type, thin or thick. Default: thick.
        :type lun_type: :class:`str`
        :param lun_id: ID of LUN to create or 'auto' to automatically assign
            ID, default auto.
        :type lun_id: :class:`str`
        :param ignore_thresholds: ignore storage pool % full threshold
        :type ignore_thresholds: :class:`boolean`
        :param array_specific_options: Optional parameters to be passed.
        :type array_specific_options: :class:`str`
        :returns: :class: `LunInfo` object corresponding to newly created LUN.
        :raises SanApiEntityAlreadyExistsException: Raised if LUN with same
            name already exists.
        :raises NotImplementedError: Function currently unimplemented.

        Storage Pool LUN Creation Examples:

        Example 1: Create a LUN in storage pool mypool using automatic\
            lun id assignment:

        .. code-block:: python

            create_lun("spLUN1", "500Gb", "StoragePool", "mypool")

        Example 2: Create a LUN in storage pool mypool using specific lun id:

        .. code-block:: python

            create_lun("spLUN2", "500Gb", "StoragePool",
                       "mypool", lun_id="100")

        Example 3: Create a LUN in storage pool mypool using vnx specific
            options:

        .. code-block:: python

            create_lun("spLUN3", "500Gb", "StoragePool", "mypool",
                        array_specific_options="-initialTier optimizePool")

        *Raid Group LUN Creation Examples*:

        Example 1: Create a LUN in raid group ID=6 using using automatic lun\
            id assignment:

        .. code-block:: python

            create_lun("rgLUN1","1Gb","Raid Group","6", raid_type="5",
                        lun_id="auto")

        Example 2: Create a LUN in raid group ID=10 using specific lun id:

        .. code-block:: python

            create_lun("rglun1","1Gb","Raid Group","10", raid_type="5",
            lun_id="95")
        """
        raise NotImplementedError()

    def delete_lun(self, lun_name=None, lun_id=None,
                   array_specific_options=""):
        """
        Deletes a LUN with the specified ID or name from storage pool or raid
        group. Either lun_id or lun_name should be specified but not both.

        .. note::

            Only storage pool LUNs can be deleted by name.

        :param lun_name: Name of LUN to delete (storage pool LUN only).
        :type lun_name: :class:`str`
        :param lun_id: ID of the LUN to delete.
        :type lun_id: :class:`str`
        :param array_specific_options: Optional parameters to be passed.
        :type array_specific_options: :class:`str`

        :returns: True if deletion successful, otherwise throws
            SanApiException.
        :rtype: :class:`boolean`
        :raises SanApiException: Raised if deletion unsuccessful.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Delete pool LUN with name "fkruger":

        .. code-block:: python

            delete_lun(lun_name="fkruger")

        Example 2: Delete LUN with ID 23:

        .. code-block:: python

            delete_lun(lun_id="23")

        Example 3: Delete LUN with ID "24" and all associated snapshots and\
            snapshot mount points:

        .. code-block:: python

            delete_lun(lun_id="24",
            array_specific_options="-destroySnapshots -forceDetach")
        """
        raise NotImplementedError()

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
        Determines if a storage pool LUN exists.

        :param lun_name: Name of LUN to check.
        :type lun_name: :class:`str`
        :returns: True if Lun found, otherwise False.
        :rtype: :class:`boolean`
        :raises SanApiException: Raised if error occured while checking LUN.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            lun_exists("foobar")
        """
        raise NotImplementedError()

    """ Host Initiator API Functions """

    def get_hba_port_info(self, wwn=None, host=None, \
                          storage_processor=None, sp_port=None):
        """
        Queries the array for HBA/port information.
        Returns a list of HBAInitiatorInfo objects.
        List of objects can be filtered by:

        - wwn

        - wwn AND storage processor

        - wwn AND port

        - wwn AND storage processor AND port

        - host

        - host AND storage processor

        - host AND port

        - host AND storage processor AND port


        If no filter parameters are given, the function
        returns all HBA port information.

        :param wwn: Optional, WWN of the host.
        :type wwn: :class:`str`
        :param host: Optional, host name or IP address.
        :type host: :class:`str`
        :param storage_processor: Optional, storage processor.
        :type storage_processor: :class:`str`
        :param sp_port: Optional, storage processor port.
        :type sp_port: :class:`str`
        :returns: :class:`list` of :class:`HBAInitiatorInfo` objects.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Retrieve all HBA port info:

        .. code-block:: python

            hbainfo=get_hba_port_info()

        Example 2: Retrieve all HBA port info with specified WWN AND storage\
            processor:

        .. code-block:: python

            WWN AND storage processor:
            hbainfo=get_hba_port_info( \
                    wwn="50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E",
                    storage_processor="A")

        Example 3: Retrieve all HBA port info with specified host name AND\
            storage processor AND storage processor port:

        .. code-block:: python

            hbainfo=get_hba_port_info( \
                    host="atrcxb2112",
                    storage_processor="A", sp_port="0")

        Example 4: Retrieve all HBA port info with specified host (IP) AND\
            port:

        .. code-block:: python

            hbainfo=get_hba_port_info( \
                    host="10.24.53.19", sp_port="0")
        """
        raise NotImplementedError()

    def create_host_initiators(self, sg_name, wwn, host_name=None, \
                              host_ip=None, arraycommpath="1", \
                              init_type="3", failovermode="4", \
                              array_specific_options=""):
        """
        Assigns a storage group to a particular HBA in a host
        Examines port list and registers given WWN using all the
        storage processor and sp ports currently in the port list.
        Host name and host IP is also obtained from the information
        in the port list.

        :param sg_name: Storage group name to connect hba to.
        :type sg_name: :class:`str`
        :param wwn: WWN of the HBA to add.
        :type wwn: :class:`str`
        :param host_name: Optional, host name to associate with registration
                              If specified, host_ip must also be given.
        :type host_name: :class:`str`
        :param host_ip: Optional, host ip to associate with registration
                              If specified, host_name must also be given.
        :type host_ip: :class:`str`
        :param arraycommpath: Optional, arraycommpath value, 0 or 1.
        :type arraycommpath: :class:`str`
        :param type: Optional, initiator type, default=3.
        :type type: :class:`str`
        :param failovermode: Optional, failover mode.
        :param array_specific_options: optional parameters to be passed
                         directly to backend storage command, default blank.
        :type array_specific_options: :class:`str`
        :returns: :class: `StorageGroupInfo` object.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Connect HBA WWN to all storage_processors and sp ports
        mentioned in port list nd assign to storage group sg123:

        .. code-block:: python

            sginfo = create_host_initiators("sg123",  \
                 "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E")

        Example 2: Connect HBA WWN to all storage_processors and sp ports
        mentioned in port list nd assign to storage group sg123.
        Associate with host atrcxb123:

        .. code-block:: python

            sginfo = create_host_initiators("sg123", \
                 "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E",
                 "atrcxb123", "1.2.3.4")
        """
        raise NotImplementedError()

    def create_host_initiator(self, sg_name, host_name, host_ip, wwn, \
                              storage_processor, sp_port, arraycommpath="1", \
                              init_type="3", failovermode="4", \
                              array_specific_options=""):
        """
        Assigns a storage group to a particular HBA in a host.

        :param sg_name: Storage group name to connect hba to.
        :type sg_name: :class:`str`
        :param host_name: Name of host to add.
        :type host_name: :class:`str`
        :param host_ip: IP of host to add.
        :type host_ip: :class:`str`
        :param wwn: WWN of the HBA to add.
        :type wwn: :class:`str`
        :param storage_processor: Storage processor, A or B, default is A.
        :type storage_processor: :class:`str`
        :param sp_port: Storage processor port.
        :type sp_port: :class:`str`
        :param arraycommpath: Optional, arraycommpath value, 0 or 1.
        :type arraycommpath: :class:`str`
        :param type: Optional, initiator type, default=3.
        :type type: :class:`str`
        :param failovermode: Optional, failover mode.
        :type failovermode: :class:`str`
        :param array_specific_options: Optional parameters to be passed
            directly to backend storage command, default blank.
        :type array_specific_options: :class:`str`
        :returns: A HbaInitiatorInfo object.
        :rtype: :class:`HbaInitiatorInfo` object.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Connect HBA of host myhost to port 0 of
        storage processor A of VNX and assign to storage group sg123:

        .. code-block:: python

            hbainfo = create_host_initiator("sg123", "myhost", "1.2.3.4",
                        "50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E",
                         "A", "0")

        Example 2: Connect HBA of host myhost2 to port 0 of storage
        processor A of VNX and assign to storage group sg123,
        disabling arraycommpath:

        .. code-block:: python

            hba_info = create_host_initiator("sg123", "myhost2", "1.2.3.5",
                        "50:F1:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:CE",
                        "A", "0", arraycommpath="0")
        """
        raise NotImplementedError()

    """ Storage Group API Functions """

    def get_storage_group(self, sg_name):
        """
        Returns a StorageGroupInfo object representing a storage group which
        matches the name argument.

        :param sg_name: Name of storage group to retrieve.
        :type sg_name: :class:`str`
        :returns: A StorageGroupInfo object representing a storage group which
            matches the name argument.
        :rtype: :class:`StorageGroupInfo` object.
        :raises SanApiEntityNotFoundException: Raised if storage group not
            found.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            new_sg = vnx.get_storage_group("new_sg")
        """
        raise NotImplementedError()

    def get_storage_groups(self):
        """
        Returns a list of StorageGroupInfo objects representing all of
        the SAN's storage groups.

        :returns: A list of StorageGroupInfo objects representing all of
            the SAN's storage groups.
        :rtype: :class:`StorageGroupInfo` object.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            sgList = get_storage_groups()
        """
        raise NotImplementedError()

    def create_storage_group(self, sg_name):
        """
        Creates a storage group and returns a StorageGroupInfo object
        representing the storage group created.

        :param sg_name: Name of storage group to create.
        :type sg_name: :class:`str`
        :returns: A StorageGroupInfo object representing the storage group
            created.
        :rtype: :class:`StorageGroupInfo` object.
        :raises SanApiEntityAlreadyExistsException: Raised if storage group
            with same name already exists.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            create_storage_group("new_sg")
        """
        raise NotImplementedError()

    def delete_storage_group(self, sg_name):
        """
        Deletes a storage group.

        :param sg_name: Name of storage group to delete
        :type sg_name: :class:`str`
        :returns: True if snapshot successfully deleted, otherwise False.
        :rtype: :class:`str`
        :raises SanApiException: Raised if deletion unsuccessful.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            delete_storage_group("old_sg")
        """
        raise NotImplementedError()

    def add_lun_to_storage_group(self, sg_name, hlu, alu):
        """
        Assigns a LUN to a storage group.

        .. note::

            The host logical unit(HLU) & actual logical unit(ALU)
            are both mandatory.

        :param sg_name: Storage group name to add LUN to.
        :type sg_name: :class:`str`
        :param hlu: Host logical unit to be assigned to the LUN in storage
            group.
        :type hlu: :class:`str`
        :param alu: Actual logical unit of the LUN being added to storage
            group.
        :type alu: :class:`str`
        :raises SanApiEntityNotFoundException: Raised if ALU not found.
        :raises SanApiEntityAlreadyExistsException: Raised if HLU with same
            number already exists in the storage group.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            add_lun_to_storage_group("Storage_Group_Name","0","12")
        """
        raise NotImplementedError()

    def remove_luns_from_storage_group(self, sg_name, hlus):
        """
        Removes LUN associations from a storage group. The hlus parameter
        can be a single hlu value (string or int), or it can be a list of
        numbers (as strings or ints). It will also accept an hlu_alu_pairs
        list attribute (comprised of HluAluPairInfo objects) from a
        StorageGroupInfo object.

        :param sg_name: Storage group name to remove LUN from.
        :type sg_name: :class:`str`
        :param hlus: :class:`int`, :class:`str`, :class:`int` :class:`list`,
            :class:`str` :class:`list`, or :class:`HluAluPairInfo`
            :class:`list` containing HLU numbers of LUNs to remove.
        :type hlus: :class:`int`, :class:`str`, :class:`int` :class:`list`,
            :class:`str` :class:`list`, or :class:`HluAluPairInfo`
            :class:`list`
        :returns: A :class:`StorageGroupInfo` object is returned on success.
        :rtype: :class:`StorageGroupInfo`
        :raises SanApiEntityNotFoundException: Raised if HLU not found.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Remove individual LUN using HLU as string:

        .. code-block:: python

            remove_luns_from_storage_group('group1', '23')

        Example 2: Remove list of LUNs using list of ints:

        .. code-block:: python

            remove_luns_from_storage_group('group1', [1,3,5,7])

        Example 3: Remove All LUNs using HluAlu pairs information of storage
            group object (where sginfo is a storage group object):

        .. code-block:: python

            remove_luns_from_storage_group(sginfo.name, sginfo.hlu_alu_list)
        """

        raise NotImplementedError()

    def disconnect_host(self, sg_name, host):
        """
        Disconnects host from storage group.

        :param sg_name: The storage group name.
        :type sg_name: :class:`str`
        :param host: The host IP address.
        :type host: :class:`str`
        """
        raise NotImplementedError()

    def deregister_hba_uid(self, hba_uid):
        """
        Deregisters HBA UID from  the SAN.

        :param hba_uid: The HBA UID.
        :type hba_uid: :class:`str`
        """
        raise NotImplementedError()

    def storage_group_exists(self, sg_name):
        """
        Determines if a storage group exists.

        :param sg_name: Name of storage group to check.
        :type sg_name: :class:`str`
        :returns: Ture if storage group found, otherwise False.
        :rtype: :class:`boolean`
        :raises SanApiException: Raised if error occured while checking
            storage group.
        :raises NotImplementedError: Function currently unimplemented.

        Example:

        .. code-block:: python

            storage_group_exists("mysg")
        """
        raise NotImplementedError()

    """ Storage Pool API Functions """

    def get_storage_pool(self, sp_name=None, sp_id=None):
        """
        Returns a StoragePoolInfo object representing a storage pool
        on the SAN which matches the name|id argument.

        .. note::

            Either sp_id or sp_name should be specified but not both.

        :param sp_id: Optional, ID of pool to find.
        :type sp_id: :class:`int` or :class:`str`
        :param sp_name: Optional, name of pool to find.
        :type sp_name: :class:`str`
        :returns: A StoragePoolInfo object representing a storage pool on the
            SAN which matches the name|id argument.
        :rtype: :class:`StoragePoolInfo` object.
        :raises SanApiEntityNotFoundException: Raised if pool not found.
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Find pool with name mypool:

        .. code-block:: python

            SPInfoObj = get_storage_pool(sp_name="mypool")

        Example 2: Find pool with id 4:

        .. code-block:: python

            SPInfoObj = get_storage_pool(sp_id="4")

        """
        raise NotImplementedError()

    def create_storage_pool(self, sp_name, disks,
                            raid_type, array_specific_options=""):
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

    def modify_storage_pool(self, sp_name, hwm_value):
        """
        Modify a storage pool.

        :param sp_name: The name of the storage pool.
        :type sp_name: :class:`str`
        :param hwm_value: The value for snapPoolFullHWM
        :type hwm_value: :class:`int`
        """
        raise NotImplementedError()

    """ Hot Spare API Functions """
    def configure_hs(self, args):
        """
        This method differs for VNX1 and VNX2.  Each are described below:

        For VNX1:

        .. code-block:: python

            def configure_hs(self, rg_id, lun_name=None):

        Configures the hot spare by creating a LUN bound to an existing Raid
        Group.  It returns a LunInfo object representing the LUN.

        SanApiExceptions are thrown if the method fails at any point.

        :param rg_id: Raid Group ID
        :type rg_id: :class:`str`
        :param lun_name: Optional, name of LUN.
        :type lun_name: :class:`str`

        **VNX1 Examples**

        Example 1: Create LUN without providing name:

        .. code-block:: python

            hs_lun = configure_hs('23')

        Example 2: Create LUN and name it:

        .. code-block:: python

            hs_lun = configure_hs('23', 'hs_lun')

        For VNX2:

        .. code-block:: python

            def configure_hs(self, policy, ratio):

        Configure the hot spare policy by specifying the policy id and
        the ratio of disks to be used for each hot spare.
        It returns a hot spare info object representing the policy information
        for that policy id.

        :param policy_id: The policy ID you wish to configure.
        :type policy_id: :class:`str`
        :param ratio: Set the hot spare ratio for that policy where ratio
            is the number of disks to use per hot spare.
        :type ratio: :class:`str`
        :raises SanApiException: Raised if the method fails at any point.
        :raises NotImplementedError: Function currently unimplemented.

        **VNX2 Example**

        Example 1:
        Configure a hot spare policy for a policy id of 1 with a ratio of 25:

        .. code-block:: python

            configure_hs=configure_hs(policy='1',ratio='25')
            #returns a hot spare policy info object

        Example 2:
        Configure a hot spare policy for a policy id of 2 with a ratio of 30:

        .. code-block:: python

            configure_hs=configure_hs(policy='2',ratio='30')
            #returns a hot spare policy info object

        """

        raise NotImplementedError()

    def get_hs_policy(self, policy, disk_type):
        """
        Returns the current Hot Spare Policy of a VNX2 as a
        HsPolicyInfo object.

        .. note::

            VNX2 only. Either policy or disk type can be specified but not
            both.

        :param policy: Options, policy ID.
        :type policy: :class:`str`
        :param disk_type: Optional, disk type policy applies to.
        :type disk_type: :class:`str`
        :returns: The current Hot Spare Policy of a VNX2 as a
            HsPolicyInfo object.
        :rtype: :class:`HsPolicyInfo`
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Find the hot spare policy associated with policy id 1:

        .. code-block:: python

            hs_policy=get_hs_policy(policy='1')

        Example 2: Find the hot spare policy associated with the disk type SAS:

        .. code-block:: python

            hs_policy=get_hs_policy(disk_type="SAS")
        """
        raise NotImplementedError()

    def get_hs_policy_list(self):
        """
        .. note::

            VNX2 only.

        Returns a list of all hot spare policies on a VNX2.

        :returns: A list of hot spare policy info objects.
        :rtype: :class:`list` of :class:`HsPolicyInfo`
        :raises NotImplementedError: Function currently unimplemented.

        Example : Find all hot spare policies on a VNX2:

        .. code-block:: python

            hs_policies=get_hs_policy_list()

        """

        raise NotImplementedError()

    def get_hs_luns(self):
        """
        .. note::

            VNX1 only

        Returns a list of all hot spare LUNs.

        :returns: A list contains LunInfo Objects.
        :rtype: list of :class:`LunInfo`
        :raises NotImplementedError: Function currently unimplemented.
        """

    def get_snapshots(self, lun_name=None, lun_id=None):
        """
        Returns a list of SnapshotInfo objects, one for each VNX Snapshot found
        in array. If lun_name or lun_id is provided, a list of SnapshotInfo
        objects is returned for all VNX Snapshots associated with that LUN.
        If no snapshots are found, then an empty list is returned.

        :param lun_name: Optional, a string containing a LUN name, used for
                filtering the snapshots to only those related to that LUN.
        :type lun_name: :class:`str
        :param lun_id: Optional, a string or int containing a LUN ID, used for
                filtering the snapshots to only those related to that LUN.
        :type lun_id: :class:`str` or :class:`int`
        :returns: A list of SnapshotInfo objects, one for each VNX Snapshot
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
        raise NotImplementedError

    def get_snapshot(self, snap_name):
        """
        Returns a SnapshotInfo object.
        snap_name must be provided, a SnapshotInfo Object is returned for the
        specified VNX Snapshot.
        If no snapshot is found, then an exception is raised.

        :param snap_name: A string containing the name of a snapshot.
        :type snap_name: str
        :returns: A SnapshotInfo object.
        :rtype: :class:`SnapshotInfo`
        :raises NotImplementedError: Function currently unimplemented.

        Example 1: Get snapshot 'fuego':

        .. code-block:: python

            get_snapshot('fuego')
        """
        raise NotImplementedError

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

        raise NotImplementedError

    def restore_snapshot(self, lun_name, snap_name, delete_backupsnap=True):
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

        raise NotImplementedError

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

        raise NotImplementedError

    def get_san_info(self):
        """
        Gets SAN Information

        :return: SanInfo object
        :raises SanApiOperationFailedException: Raised if the method fails at any point.

        Example:
        saninfo = get_san_info()
        print saninfo.oe_version
        print saninfo.san_model
        """

        raise NotImplementedError

    def get_san_alerts(self):
        """
        Gets all SAN alerts.
        Returned alert fields are 'severity', 'message', 'description', 'state'.

        :return: SanAlert object
        :raises: SanApiOperationFailedException: Raised if the method fails at any point.
        """

        raise NotImplementedError

    def get_hw_san_alerts(self):
        """
        Gets all HwErrMon alerts.  :return:SanAlert object
        :raises:SanApiOperationFailedException: Raised if the method at any
        point.
        """
        raise NotImplementedError

    def get_filtered_san_alerts(self, alert_filter):
        """
        Get SAN alerts that match a filter.
        Filtering is performed by the server, the query response contains matching alerts only.
        Returned alert fields are 'severity', 'message', 'description', 'state'.

        :return: SanAlert object
        :raises: SanApiOperationFailedException: Raised if the method fails at any point.
        """

        raise NotImplementedError

