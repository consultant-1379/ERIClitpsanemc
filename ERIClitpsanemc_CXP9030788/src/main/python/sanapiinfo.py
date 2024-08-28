"""
File name: sanapiinfo.py
Version: ${project.version}
Base class SanApiInfo no longer serves a purpose.
"""

import sanapilib
from sanapiexception import SanApiCriticalErrorException, \
    SanApiOperationFailedException
from sanapicfg import SANAPICFG
import logging
import socket


class SanApiInfo(object):
    """
    SanApiInfo base class.
    Sub classes exist for each SAN 'component' such as LUN, storage group, etc.
    Sub classes call the base class constructor to load the API config file,
    set up logging if needed and provide an implementation of eq and neq
    operators.
    This base class also provides a size formatter method which sub classes
    uses to format size information for overloaded __str__ methods.
    Where possible, sub classes only implement getter methods (using @property
    decorators to provide attribute style access, i.e. obj.value instead of
    obj.value()).
    Instead of relying on setters, classes here rely on all attributes being
    set at construction. The LunInfo class is the exception here, with some
    setters being implemented because the vnxcommon / vnxparser components
    do not have all the data needed at construction time.
    """

    def __init__(self, logger=None):
        """
        Constructor for sanapi info. Uses existing logger singleton or
        initialises logging if it is not set up.
        == and != are overloaded by the implementation of__eq__ and __ne__
        methods which allow derived class objects to be compared.
        _size_formatter method can be used by derived classes to format size
        output in their __str__ methods.

        :param logger: An optional :class:`logger` object.
        :type logger: :class:`logger`
        """

        self.logger = logger or logging.getLogger(socket.gethostname())
        self.cfg = SANAPICFG

    def __eq__(self, other):
        """
        Allows for == comparison of info objects.

        :param other: The other object to compare to.
        :type other: :class:`object`
        :returns: True if other of same class and attributes.
        :rtype: :class:`boolean`
        """
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        """
        Allows for != comparison of info objects.

        :param other: The other object to compare to.
        :type other: :class:`object`
        :returns: True if other not of same class and attributes.
        :rtype: :class:`boolean`
        """
        return not self.__eq__(other)

    def _size_formatter(self, megabytes):
        """
        Used by __str__ methods to give human readable string of size
        e.g. 2048 (mb) will be 2Gb.

        :param megabytes: The size in megabytes.
        :type megabytes: :class:`int` or :class:`str`
        :returns: The size in a readable string.
        :rtype: :class:`str`
        """
        try:
            megabytes = int(megabytes)
        except ValueError:
            try:
                megabytes = float(megabytes)
            except ValueError:
                return "Unknown"  # Should never get here

        bytes_ = megabytes * 1024 * 1024
        bytes_ = int(bytes_)
        for x in ['bytes', 'Kb', 'Mb', 'Gb']:
            if bytes_ < 1024.0 and bytes_ > - 1024.0:
                return "%3.3f%s" % (bytes_, x)
            bytes_ /= 1024.0

        return "%3.3f%s" % (bytes_, 'Tb')


class LunInfo(SanApiInfo):
    """
    Class representing a LUN.  It has the following attributes:

    :ivar LunInfo.lun_id: UID of the LUN - a positive integer that will be
        stored as a string.
    :vartype LunInfo.lun_id: :class:`str`
    :ivar LunInfo.name: Name of the LUN.
    :vartype LunInfo.name: :class:`str`
    :ivar LunInfo.uid: UID of LUN, 16 colon separated hex pairs, e.g.
        50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E
    :vartype LunInfo.uid: :class:`str`
    :ivar LunInfo.container: String, either a storage group name or raid group
        ID.
    :vartype LunInfo.container: :class:`str`
    :ivar LunInfo.size: Size of the LUN. If the value is just a number then it
        will be interpreted as Mb.  Otherwise the parameter can be a number
        with a size quotient of Mb, Gb, or Tb (or represented as m, g, t).
    :vartype LunInfo.size: :class:`int` or :class:`str`
    :ivar LunInfo.container_type: RaidGroup or StorageGroup.
    :vartype LunInfo.container_type: :class:`str`
    :ivar LunInfo.raid: RAID type of the LUN, one of: 0, 1, 10, 5, 6, HS.
    :vartype LunInfo.raid: :class:`str`
    :ivar LunInfo.controller: String representing controller (VNX == SP)
    :vartype LunInfo.controller: :class:`str`

    **LUN attributes that are only returned from "lun -list"**

    :ivar LunInfo.current_op: Current operation.
    :vartype LunInfo.current_op: :class:`str`
    :ivar LunInfo.current_op_state: Current operation state.
    :vartype LunInfo.current_op_state: :class:`str`
    :ivar current_op_status: Current operation status.
    :vartype LunInfo.current_op_status: :class:`str`
    :ivar LunInfo.percent_complete: State of current operation [0-100%].
    :variable LunInfo.percent_complete: :class:`int`
    """

    def __init__(self, lun_id, name, uid, container, size, container_type,
                 raid, controller=None, current_op="",
                 current_op_state="",
                 current_op_status="",
                 percent_complete="", consumed=None):
        super(LunInfo, self).__init__()

        if consumed is None:
            consumed = size
        # validate lun_id
        try:
            lun_id = sanapilib.validate_int_and_make_string(lun_id)
        except SanApiOperationFailedException, exce:
            #errmsg = "Invalid lunid parameter: " + str(exce)
            errmsg = "LunInfo attribute, lun_id is not valid" + str(lun_id)

            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        # validate name
        if not sanapilib.is_valid_lunname(name):
            errmsg = "LunInfo attribute, name is not valid: " + str(name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        # validate uid
        if not sanapilib.is_valid_uuid(uid):
            errmsg = "LunInfo attribute, uid is not valid: " + str(uid)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        # container validation is done when attribute is set,
        # using the setter method

        # validate size
        try:
            sizemb = sanapilib.convert_size_to_mb(size)

        except SanApiCriticalErrorException:
            errmsg = "LunInfo attribute, size is not valid: " + str(size)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        # validate consumed size
        try:
            consumedmb = sanapilib.convert_size_to_mb(consumed)

        except SanApiCriticalErrorException:
            errmsg = "LunInfo attribute, consumed is not valid: {0}"\
                     .format(consumed)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        # container type validation is done when attribute is set,
        # using the setter method

        # raid validation is done when attribute is set,
        # using the setter method

        self._id = lun_id
        self._name = name
        self._uid = uid
        self.container = container  # use setter
        self._size = sizemb
        self.type = container_type  # use setter
        self.raid = str(raid)  # use setter
        self._controller = str(controller)
        self._current_op = current_op
        self._current_op_state = current_op_state
        self._current_op_status = current_op_status
        self._percent_complete = percent_complete
        self._consumed = consumedmb

    def __str__(self):
        """
        Override __str__ method to control printing.

        :returns: A reformatted string of LUN info.
        :rtype: :class:`str`
        """

        output = ''
        output += "lun id:         %s\n" % self._id
        output += "name:           %s\n" % self._name
        output += "uid:            %s\n" % self._uid
        output += "container:      %s\n" % self._container
        output += "size:           %s\n" % self._size_formatter(self._size)
        output += "container type: %s\n" % self._type
        output += "raid:           %s\n" % self._raid
        output += "controller:     %s\n" % self._controller
        return output

    # Getters
    @property
    def id(self):
        """
        The ID of the LUN.

        :getter: Returns the ID of the LUN.
        :type: :class:`str`
        """
        return self._id

    @property
    def name(self):
        """
        The name of the LUN.

        :getter: Returns the name of the LUN.
        :type: :class:`str`
        """
        return self._name

    @property
    def uid(self):
        """
        The UID of the LUN.

        :getter: Returns the UID of the LUN.
        :type: :class:`str`
        """
        return self._uid

    @property
    def container(self):
        """
        The container of the LUN.

        :getter: Returns the container of the LUN.
        :setter: Sets the container of the LUN.
        :type: :class:`str`
        """
        return self._container

    @property
    def size(self):
        """
        The size of the LUN.

        :getter: Returns the size of the LUN.
        :type: :class:`str`
        """
        return self._size

    @property
    def type(self):
        """
        The type of the LUN.

        :getter: Returns the LUN's type.
        :setter: Sets the LUN's type.
        :type: :class:`str`
        """
        return self._type

    @property
    def raid(self):
        """
        The RAID of the LUN.

        :getter: Returns the RAID of the LUN.
        :setter: Sets the RAID of the LUN.
        :type: :class:`str`
        """
        return self._raid

    @property
    def controller(self):
        """
        The controller that owns the LUN

        :getter: Returns the controller
        :setter: Sets the controller
        :type: str
        """
        return self._controller

    @property
    def current_op(self):
        """
        The current operation of the LUN.

        :getter: Returns the current operation of the LUN.
        :setter: Sets the current operation of the LUN.
        :type: :class:`str`
        """
        return self._current_op

    @property
    def current_op_state(self):
        """
        The state of the current operation of the LUN.

        :getter: Returns the state of the LUN's current operation.
        :setter: Sets the state of the LUN's current operation.
        :type: :class:`str`
        """
        return self._current_op_state

    @property
    def current_op_status(self):
        """
        The status of the current operation of the LUN.

        :getter: Returns the status of the LUN's current operation.
        :setter: Sets the status of the LUN's current operation.
        :type: :class:`str`
        """
        return self._current_op_status

    @property
    def percent_complete(self):
        """
        The percent complete of the LUN.

        :getter: Returns the LUN's ID.
        :setter: Sets the LUN's ID.
        :type: :class:`str`
        """
        return self._percent_complete

    @property
    def consumed(self):
        """
        The consumed capacity of the LUN
        """
        return self._consumed

    # Setters - these are required because when vnxparser / vnxcommon
    #           initially constructs a LunInfo object it does not have
    #           all the information at that point to pass to the
    #           constructor.  The setters are used to add this information
    #           later in vnxcommon's processing.

    @container.setter
    def container(self, val):
        sanapilib.validate_string(val)
        self._container = val

    @type.setter
    def type(self, val):
        # validate container type
        try:
            val = sanapilib.normalise_container_type(val)
        except SanApiOperationFailedException:
            errmsg = "LunInfo attribute, container_type is not valid: " + \
                str(val)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)
        self._type = val

    @raid.setter
    def raid(self, val):
        if not sanapilib.is_valid_raidtype(val):
            errmsg = "LunInfo attribute, raid is not valid: " + str(val)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)
        self._raid = str(val)

    @current_op.setter
    def current_op(self, val):
        self._current_op = str(val)

    @current_op_state.setter
    def current_op_state(self, val):
        self._current_op_state = str(val)

    @current_op_status.setter
    def current_op_status(self, val):
        self._current_op_status = str(val)

    @percent_complete.setter
    def percent_complete(self, val):
        self._percent_complete = str(val)

    @consumed.setter
    def consumed(self, val):
        self._consumed = str(val)


class StoragePoolInfo(SanApiInfo):
    """
    Class representing a Storage Pool.  It has the following mandatory
    attributes:

    :ivar StoragePoolInfo.name: Name of the Storage Pool.
    :vartype StoragePoolInfo.name: :class:`str`
    :ivar StoragePoolInfo.id_: ID of the Storage Pool.
    :vartype StoragePoolInfo.id_: :class:`str`
    :ivar StoragePoolInfo.raid: RAID type of the Storage Pool.
    :vartype StoragePoolInfo.raid: :class:`str`
    :ivar StoragePoolInfo.size: Size of the Storage Pool in known units, Mb,
        Gb, or Tb. A number without a unit will be interpreted as Mb.
    :vartype StoragePoolInfo.size: :class:`str`
    :ivar StoragePoolInfo.available: Available size of the Storage Pool in
        known units, Mb, Gb, or Tb.  A number without a unit will be
        interpreted as Mb.
    :vartype StoragePoolInfo.available: :class:`str`
    :ivar StoragePoolInfo.full: Percent full of Storage Pool
    :vartype StoragePoolInfo.full:class:`str`
    :ivar StoragePoolInfo.subscribed: Percent subscribed of Storage Pool
    :vartype StoragePoolInfo.subscribed:class:`str`
    """

    def __init__(self, name, id, raid, size, available, perc_full=None, perc_sub=None, disks=None):
        super(StoragePoolInfo, self).__init__()

        try:
            id = sanapilib.validate_int_and_make_string(id)
        except SanApiOperationFailedException, exce:
            errmsg = "Invalid id parameter: " + str(exce)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        if not sanapilib.is_valid_storage_pool_name(name):
            errmsg = "StoragePoolInfo attribute, name is not valid: " + \
                str(name)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        if not sanapilib.is_valid_raidtype(raid):
            errmsg = "StoragePoolInfo attribute, raid is not valid: " + \
                str(raid)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        try:
            sizemb = sanapilib.convert_size_to_mb(size)
        except SanApiCriticalErrorException:
            errmsg = "StoragePoolInfo attribute, size is not valid: " + \
                str(size)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        try:
            availmb = sanapilib.convert_size_to_mb(available)
        except SanApiCriticalErrorException:
            errmsg = "StoragePoolInfo attribute, available is not valid: " + \
                str(size)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        if perc_full:
            try:
                perc_full = sanapilib.validate_float_and_make_string(perc_full)
            except SanApiOperationFailedException, exce:
                errmsg = "Invalid id parameter: " + str(exce)
                self.logger.error(errmsg)
                raise SanApiOperationFailedException(errmsg, 1)

        if perc_sub:
            try:
                perc_sub = sanapilib.validate_float_and_make_string(perc_sub)
            except SanApiOperationFailedException, exce:
                errmsg = "Invalid id parameter: " + str(exce)
                self.logger.error(errmsg)
                raise SanApiOperationFailedException(errmsg, 1)

        self._id = id
        self._name = name
        self._raid = str(raid)
        self._size = sizemb
        self._available = availmb
        self._full = perc_full
        self._subscribed = perc_sub
        self._disks = str(disks)


    def __str__(self):
        """
        Override __str__ method to control printing.

        :returns: A reformatted string of Storage Pool info.
        :rtype: :class:`str`
        """

        output = ''
        output += "pool id:               %s\n" % self._id
        output += "pool name:             %s\n" % self._name
        output += "raid type:             %s\n" % self._raid
        output += "size:                  %s\n" % \
            self._size_formatter(self._size)
        output += "available size:        %s\n" % \
            self._size_formatter(self._available)

        if self._full:
            output += "percent full:          %s\n" % self._full

        if self._subscribed:
            output += "percent subscribed:    %s\n" % self._subscribed

        if self._disks:
            output += "number of disks:       %s\n" % self._disks
        return output

    @property
    def id(self):
        """
        The ID of the Storage Pool.

        :getter: Returns the ID of the Storage Pool.
        :type: :class:`str`
        """
        return self._id

    @property
    def name(self):
        """
        The name of the Storage Pool.

        :getter: Returns the name of the Storage Pool.
        :type: :class:`str`
        """
        return self._name

    @property
    def raid(self):
        """
        The RAID of the Storage Pool.

        :getter: Returns the RAID of the Storage Pool.
        :type: :class:`str`
        """
        return self._raid

    @property
    def size(self):
        """
        The size of the Storage Pool.

        :getter: Returns the size of the Storage Pool.
        :type: :class:`str`
        """
        return self._size

    @property
    def available(self):
        """
        The availability of the Storage Pool.

        :getter: Returns the availability of the Storage Pool.
        :type: :class:`str`
        """
        return self._available

    @property
    def full(self):
        """
        Percent full of the Storage Pool

        :getter: Returns the percent full of the Storage Pool.
        :type: :class:`str`
        """
        return self._full

    @property
    def subscribed(self):
        """
        Percent subscribed of the Storage Pool

        :getter: Returns the percent subscribed of the Storage Pool.
        :type: :class:`str`
        """
        return self._subscribed

    @property
    def disks(self):
        """
        The Number of disks in the Storage Pool.

        :getter: Returns the number of disks in the Storage Pool.
        :type: :class:`str`
        """
        return self._disks


class HbaInitiatorInfo(SanApiInfo):
    """
    Class representing a pairing of HBA and SP.  It has the
    following mandatory attributes:

    :ivar HbaInitiatorInfo.hbauid: Host Bus Adapter UID, 16 colon separated
        hex pairs, e.g.
        50:01:43:80:16:7D:C4:5F:50:01:43:80:16:7D:C4:5E
    :vartype HbaInitiatorInfo.hbauid: :class:`str`
    :ivar HbaInitiatorInfo.spname: Storage Processor Name.
    :vartype HbaInitiatorInfo.spname: :class:`str`
    :ivar HbaInitiatorInfo.spport: Storage Processor Port.
    :vartype HbaInitiatorInfo.spport: :class:`str`

    **Optional attributes:**

    :ivar HbaInitiatorInfo.hbaname: Host Bus Adapter name.
    :vartype HbaInitiatorInfo.hbaname: :class:`str`
    :ivar HbaInitiatorInfo.hbaip: Host Bus Adapter IP, e.g. 192.168.0.2
    :vartype HbaInitiatorInfo.hbaip: :class:`str`

    All attributes are set in the constructor.

    """
    def __init__(self, hbauid, spname, spport, hbaname=None,
                 hbaip=None, isignored=False):
        super(HbaInitiatorInfo, self).__init__()

        # validate uid
        if not sanapilib.is_valid_uuid(hbauid):
            errmsg = "HbaInitiatorInfo attribute, uid is not valid: " +\
                 str(hbauid)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        # validate spname
        if not sanapilib.is_valid_sp(spname):
            errmsg = "HbaInitiator attribute spname is not valid: " +\
                 str(spname)

        # validate spport
        try:
            spport = sanapilib.validate_int_and_make_string(spport)
        except SanApiOperationFailedException, exce:
            errmsg = "Invalid spport parameter: " + str(exce)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        if not sanapilib.is_valid_sp_port(spport):
            msg = "HbaInitiatorInfo attribute, spport, is not valid %s " \
                % spport
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        if hbaip is not None:
            if not sanapilib.validate_ipv4(hbaip):
                errmsg = "Invalid IP address %s" % hbaip

        if hbaname is not None:
            sanapilib.validate_string(hbaname)

        self._hbauid = hbauid
        self._spname = spname
        self._spport = spport
        self._hbaname = hbaname
        self._hbaip = hbaip
        self._isignored = isignored

    # TODO: Check if the base class __eq__ operator will do this and if so
    #       we can remove this implementation
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.hbauid == other.hbauid and \
                   self.spname == other.spname and \
                   self.spport == other.spport and \
                   self.hbaname == other.hbaname and \
                   self.hbaip == other.hbaip and \
                   self.isignored == other.isignored
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def hbauid(self):
        """
        The UID of the HBA.

        :getter: Returns the UID of the HBA.
        :type: :class:`str`
        """
        return self._hbauid

    @property
    def spname(self):
        """
        The name of the Storage Pool.

        :getter: Returns the name of the Storage Pool.
        :type: :class:`str`
        """
        return self._spname

    @property
    def spport(self):
        """
        The port of the Storage Pool.

        :getter: Returns the port of the Storage Pool.
        :type: :class:`str`
        """
        return self._spport

    @property
    def hbaname(self):
        """
        The name of the HBA.

        :getter: Returns the name of the HBA.
        :type: :class:`str`
        """
        return self._hbaname

    @property
    def hbaip(self):
        """
        The IP of the HBA.

        :getter: Returns the IP of the HBA.
        :type: :class:`str`
        """
        return self._hbaip

    @property
    def isignored(self):
        """
        Value to determine if an initiator is set to ignored

        :getter: Returns the value of isignored
        :return: :class: `boolean`
        """
        return self._isignored

    def __str__(self):
        """
        Override __str__ method to control printing.

        :returns: A reformatted string of HBA Initiator info.
        :rtype: :class:`str`
        """
        output = ''
        output += "HBA UID:  %s\n" % self._hbauid
        output += "SP Name:  %s\n" % self._spname
        output += "SP Port:  %s\n" % self._spport

        if self.hbaname is not None:
            output += "HBA Name: %s\n" % self.hbaname

        if self.hbaip is not None:
            output += "HBA IP:   %s\n" % self.hbaip

        return output


class HluAluPairInfo(SanApiInfo):
    """

    Class representing a pairing of HLU and ALU.  It has the
    following attributes:

    :ivar HluAluPairInfo.hlu: Host Lun Unit.
    :vartype HluAluPairInfo.hlu: :class:`str`
    :ivar HluAluPairInfo.alu: Array Logical Unit.
    :vartype HluAluPairInfo.alu: :class:`str`

    All attributes are set in the constructor.
    """

    def __init__(self, hlu, alu):

        # Call constructor of base class for logging
        super(HluAluPairInfo, self).__init__()

        try:
            self._hlu = sanapilib.validate_int_and_make_string(hlu)
        except SanApiOperationFailedException, exce:
            errmsg = "Invalid hlu parameter: " + str(exce)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        try:
            self._alu = sanapilib.validate_int_and_make_string(alu)
        except SanApiOperationFailedException, exce:
            errmsg = "Invalid alu parameter: " + str(exce)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.hlu == other.hlu and self.alu == other.alu
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def hlu(self):
        """
        The HLU in the HLU/ALU pair.

        :getter: Returns the HLU in the HLU/ALU pair.
        :type: :class:`str`
        """
        return self._hlu

    @property
    def alu(self):
        """
        The ALU of the HLU/ALU pair.

        :getter: Returns the ALU of the HLU/ALU pair.
        :type: :class:`str`
        """
        return self._alu

    def __str__(self):
        """
        Override __str__ method to control printing.

        :returns: A reformatted string of HLU/ALU info.
        :rtype: :class:`str`
        """
        output = ''
        output += "HLU: %s " % self._hlu
        output += "ALU: %s\n" % self._alu

        return output


class StorageGroupInfo(SanApiInfo):
    """
    Class representing a storage group.  It has the
    following attributess:

    :ivar StorageGroupInfo.name: Name of storage group.
    :vartype StorageGroupInfo.name: :class:`str`
    :ivar StorageGroupInfo.uid: UID of storage group.
    :vartype StorageGroupInfo.uid: :class:`str`
    :ivar StorageGroupInfo.shareable: Boolean indicating if storage group is
        shareable.
    :vartype StorageGroupInfo.shareable: :class:`boolean`
    :ivar StorageGroupInfo.hbasp_list: List of HbaInitiatorInfo objects
        representing any HBA/SP pairs.
    :vartype StorageGroupInfo.hbasp_list: :class:`list`
    :ivar StorageGroupInfo.hlualu_list: List of HluAluInfo objects
        representing any HLU/ALU pairs.
    :vartype StorageGroupInfo.hlualu_list: :class:`list`

    All attributes are set in the constructor.
    """

    def __init__(self, name, uid, shareable, hbasp_list, hlualu_list):
        """
        Constructor taking name, UID, shareable arguments as strings.
        hbasp_list and hlualu list objects may be set to None.
        """
        super(StorageGroupInfo, self).__init__()

        sanapilib.validate_string(name)

        # validate uid
        if not sanapilib.is_valid_uuid(uid):
            errmsg = "StorageGroupInfo attribute, uid is not valid: " +\
                str(uid)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        if not isinstance(shareable, bool):
            msg = "StorageGroupInfo attribute, shareable, must be a boolean"
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        if hbasp_list is not None:
            self.__validate_object_list(hbasp_list, HbaInitiatorInfo)
            self._hbasp_list = hbasp_list
            self.__sort_hba_sp()
        else:
            self._hbasp_list = None

        if hlualu_list is not None:
            self.__validate_object_list(hlualu_list, HluAluPairInfo)
            self._hlualu_list = hlualu_list
            self.__sort_hlu_alu()
        else:
            self._hlualu_list = None

        self._name = name
        self._uid = uid
        self._shareable = shareable

        self.logger.debug("StorageGroupInfo __init__")

    def __str__(self):
        """
        Override __str__ method to control printing.

        :returns: A reformatted string of Storage Group info.
        :rtype: :class:`str`
        """
        output = ''
        output += "storage group name: %s\n" % self._name
        output += "storage group UID : %s\n" % self._uid
        output += "shareable:          %s\n" % self._shareable

        if self._hbasp_list is not None:
            output += "\nHBA/SP Pairs:\n"
            output += "  HBA UID                " + \
                "                         SP Name  SPPort\n"
            for item in self._hbasp_list:
                output += "  %s   %s        %s\n" \
                    % (item.hbauid, item.spname, item.spport)

        if self._hlualu_list is not None:
            output += "\nHLU/ALU Pairs:\n"
            output += "  HLU No.  ALU No.\n"

            for item in self._hlualu_list:
                output += " %4s      %4s\n" % (item.hlu, item.alu)

        return output

    def __validate_object_list(self, testlist, classname):
        """
        Validate list of objects
        """
        try:
            classstring = classname.__name__
            for item in testlist:
                objstring = item.__class__.__name__

                if classstring != objstring:
                    msg = "Incorrect object in list, %s, should be type %s" \
                        % (objstring, classstring)
                    self.logger.error(msg)
                    raise SanApiOperationFailedException(msg, 1)

        except Exception, exce:
            raise SanApiOperationFailedException(str(exce), 1)

    def __sort_hlu_alu(self):
        """
        Sort the hlu alu list
        """
        self.logger.debug("sorting HLU / ALU list")
        self._hlualu_list.sort(key=lambda x: (int(x.hlu)))

    def __sort_hba_sp(self):
        """
        Sort the hba sp list
        """
        self.logger.debug("Sorting HBA / SP list")
        self.hbasp_list.sort(key=lambda x: (str("%s:%s:%s"
                             % (x.hbauid, x.spname, x.spport))))

    @property
    def hbasp_list(self):
        """
        A list of HbaInitiatorInfo objects representing HBA/SP Pairs.

        :getter: Return list of HbaInitiatorInfo objects representing HBA/SP
            Pairs. If there are no pairs then None is returned.
        :type: :class:`list`
        """
        return self._hbasp_list

    @property
    def hlualu_list(self):
        """
        A list of HluAluInfo objects representing HLU/ALU Pairs.

        :getter: Return list of HluAluInfo objects representing HLU/ALU Pairs.
            If there are no pairs then None is returned.
        :type: :class:`list`
        """
        return self._hlualu_list

    @property
    def name(self):
        """
        The name of the Storage Group.

        :getter: Returns the name of the Storage Group.
        :type: :class:`str`
        """
        return self._name

    @property
    def uid(self):
        """
        The UID of the Storage Group.

        :getter: Returns the UID of the Storage Group.
        :type: :class:`str`
        """
        return self._uid

    @property
    def shareable(self):
        """
        A boolean describing if the Storage Group is shareable or not.

        :getter: Returns the value of the boolean.
        :type: :class:`boolean`
        """
        return self._shareable


class HsPolicyInfo(SanApiInfo):
    """
    Class representing a storage group. It has the
    following attributes:

    NAMES FOR ALL VARIABLES

    :ivar HsPolicyInfo.Policy_id: The policy ID number.
    :vartype HsPolicyInfo.Policy_id: :class:`str`
    :ivar HsPolicyInfo.Disk Type: The disk type.
    :vartype HsPolicyInfo.Disk Type: :class:`str`
    :ivar HsPolicyInfo.Ratio of keep unused: The ratio of disks to keep
        unused.
    :vartype HsPolicyInfo.Ratio of keep unused: :class:`str`
    :ivar HsPolicyInfo.Number to Keep Unused: The number of disks to keep
        unused.
    :vartype HsPolicyInfo.Number to keep Unused: :class:`str`

    These attributes are implemented which simply use the appropriate keys to
    retrieve the values from the dictionary.
    """

    def __init__(self, p_id, disk_type, ratio_of_keep_unused,
                 number_to_keep_unused):

        super(HsPolicyInfo, self).__init__()

        if not sanapilib.is_valid_policyid(p_id):
                msg = "Invalid policy ID %s. Policy ID must be an integer > 0 "
                self.logger.error(msg)
                raise SanApiOperationFailedException(msg, 1)

        # if disk_type != 'SAS':
                # msg = "Unknown Disk Type %s. for creating hot spare policy"
                # self.logger.errormsg(msg)
                # raise SanApiOperationFailedException(msg, 1)

        if not sanapilib.is_proper_fraction(ratio_of_keep_unused) \
           and not sanapilib.is_positive_int(ratio_of_keep_unused):
                msg = "Ratio of keep unused %s. hot spares is invalid" \
                    % ratio_of_keep_unused
                self.logger.error(msg)
                raise SanApiOperationFailedException(msg, 1)

        if not sanapilib.is_int(number_to_keep_unused)  \
           and not sanapilib.is_positive_int(number_to_keep_unused):
                msg = "Number of disks to keep unused %s. is invalid " \
                    % number_to_keep_unused
                self.logger.error(msg)
                raise SanApiOperationFailedException(msg, 1)

        self._policy_id = str(p_id)
        self._disk_type = disk_type
        self._ratio_of_keep_unused = ratio_of_keep_unused
        self._number_to_keep_unused = number_to_keep_unused

        self.logger.debug("StorageGroupInfo __init__")

    def __str__(self):
        """
            Override __str__ method to control printing.
        """
        output = ''
        output += "Policy ID:              %s\n" % self._policy_id
        output += "Disk Type:              %s\n" % self._disk_type
        output += "Ratio of Keep Unused:   %s\n" % self._ratio_of_keep_unused
        output += "Number to Keep Unused:  %s\n" % self._number_to_keep_unused

        return output

    @property
    def policy_id(self):
        """
        The policy ID of the HS policy.

        :getter: Returns the policy ID of the HS policy.
        :type: :class:`int`
        """
        return self._policy_id

    @property
    def disk_type(self):
        """
        The policy ID of the HS policy.

        :getter: Returns the policy ID of the HS policy.
        :type: :class:`str`
        """
        return self._disk_type

    @property
    def ratio_of_keep_unused(self):
        """
        The ratio of disks to keep unused.

        :getter: Returns the ratio of disks to keep unused.
        :type: :class:`str`
        """
        return self._ratio_of_keep_unused

    @property
    def number_to_keep_unused(self):
        """
        The number of disks to keep unused.

        :getter: Returns the number of disks to keep unused.
        :type: :class:`int`
        """
        return self._number_to_keep_unused

    """
    TODO: Verify these are not needed and if not, remove them
    @policy_id.setter
    def policy_id(self, val):
        self._policy_id = val

    @disk_type.setter
    def disk_type(self, val):
        self._disk_type = val

    @ratio_of_keep_unused.setter
    def ratio_of_keep_unused(self, val):
        self._ratio_of_keep_unused = val

    @number_to_keep_unused.setter
    def number_to_keep_unused(self, val):
        self._number_to_keep_unused = val
    """


class SnapshotInfo(SanApiInfo):
    """
        Class representing a a snapshot. It has the
        following attributes:

        :ivar SnapshotInfo.snap_name: The name of the snapshot.
        :vartype SnapshotInfo.snap_name: :class:`str`
        :ivar SnapshotInfo.resource_id: The LUN ID.
        :vartype SnapshotInfo.resource_id: :class:`str`
        :ivar SnapshotInfo.created_time: Time when snapshot was created.
        :vartype SnapshotInfo.created_time: :class:`str`
        :ivar SnapshotInfo.state: State of the snapshot.
        :vartype SnapshotInfo.state: :class:`str`
        :ivar SnapshotInfo.resource_name: The LUN name.
        :vartype SnapshotInfo.resource_name: :class:`str`
        :ivar SnapshotInfo.description: The optional description.
        :vartype SnapshotInfo.description: :class:`str`

    """

    def __init__(self, resource_lun_id, snapshot_name, created_time,
                 snap_state, resource_lun_name, description=None):
        super(SnapshotInfo, self).__init__()
        self._res_id = resource_lun_id
        self._snap_name = snapshot_name
        self._creation_time = created_time
        self._state = snap_state
        self._res_name = resource_lun_name
        self._description = description

    def __str__(self):
        """
        Override __str__ method to control printing.
        """
        output = ''
        output += "resource lun id:           %s\n" % self._res_id
        output += "snapshot name:             %s\n" % self._snap_name
        output += "snapshot creation time:    %s\n" % self._creation_time
        output += "snapshot state:            %s\n" % self._state
        output += "resource lun name:         %s\n" % self._res_name

        if self._description:
            output += "snapshot description:      %s\n" % self._description

        return output

    @property
    def resource_id(self):
        """
        The ID of the LUN.

        :getter: Returns the ID of the LUN.
        :type: :class:`str`
        """
        return self._res_id

    @property
    def snap_name(self):
        """
        The name of the snapshot.

        :getter: Returns the name of the snapshot.
        :type: :class:`str`
        """
        return self._snap_name

    @property
    def creation_time(self):
        """
        The time when the snapshot was created.

        :getter: Returns the time when the snapshot was created.
        :type: :class:`str`
        """
        return self._creation_time

    @property
    def state(self):
        """
        The state of the snapshot.

        :getter: Returns the state of the snapshot.
        :type: :class:`str`
        """
        return self._state

    @property
    def resource_name(self):
        """
        The name of the LUN.

        :getter: Returns the name of the LUN.
        :type: :class:`str`
        """
        return self._res_name

    @property
    def description(self):
        """
        The snapshot description.

        :getter: Returns the description.
        :type: :class:`str`
        """
        return self._description


class SanInfo(SanApiInfo):
    """
        Class representing SAN Information. It has the
        following attributes:

        :ivar SanInfo.oe_version: The OE version.
        :vartype SanInfo.oe_version: :class:`str`
        :ivar SanInfo.san_model: The SAN model.
        :vartype SanInfo.san_model: :class:`str`

    """

    def __init__(self, oe_version, san_model, san_serial):
        super(SanInfo, self).__init__()
        self._oe_version = oe_version
        self._san_model = san_model
        self._san_serial = san_serial

    def __str__(self):
        """
        Override __str__ method to control printing.
        """
        output = ''
        output += "OE Version:           %s\n" % self._oe_version
        output += "Model:                %s\n" % self._san_model
        output += "Serial:               %s\n" % self._san_serial
        return output

    @property
    def oe_version(self):
        """
        The OE Version.

        :type: :class:`str`
        """
        return self._oe_version

    @property
    def san_model(self):
        """
        The SAN model

        :type: :class:`str`
        """
        return self._san_model

    @property
    def san_serial(self):
        """
        The SAN serial number

        :type: :class: `str`
        """
        return self._san_serial


class SanAlert(SanApiInfo):
    """
        Class representing SAN information. It has the
        following attributes:

        :ivar SanAlert.message: Alert message
        :vartype SanAlert.message: :class:`str`
        :ivar SanAlert.description: Alert description
        :vartype SanAlert.description: :class:`str`
        :ivar SanAlert.severity: Alert severity
        :vartype SanAlert.severity: :class:`int`
        :ivar SanAlert.state: Alert state
        :vartype SanAlert.state: :class:`int`
    """

    def __init__(self, message, description, severity, state):
        super(SanAlert, self).__init__()
        self._message = message
        self._description = description
        self._severity = severity
        self._state = state

    def __str__(self):
        """
        Override __str__ method to control printing.
        """
        output = ''
        output += "Message:                {0}\n".format(self._message)
        output += "Description:            {0}\n".format(self._description)
        output += "Severity:               {0}\n".format(self._severity)
        output += "State:                  {0}\n".format(self._state)
        return output

    @property
    def message(self):
        """
        The alert message

        :type :class: `str`
        """
        return self._message

    @property
    def description(self):
        """
        The alert description

        :type :class: `str`
        """
        return self._description

    @property
    def severity(self):
        """
        The alert severity

        :type :class: `int`
        """
        return self._severity

    @property
    def state(self):
        """
        The alert state

        :type :class: `int`
        """
        return self._state

class SanHwAlert(SanApiInfo):
    """
        Class representing SAN hw information. It has the
        following attributes:

        :ivar SanHwAlert.id: id
        :vartype SanHwAlert.id: :class:'str'
        :ivar SanHwAlert.health: Alert health
        :vartype SanHwAlert.health: :class:'str'
    """

    def __init__(self, id, value, health, descriptions):
        super(SanHwAlert, self).__init__()
        self._id = id
        self._value = value
        self._health = health
        self._descriptions = descriptions

    def __str__(self):
        """
        Override __str__ method to control printing.
        """
        output = ''
        output += "id:                {0}\n".format(self._id)
        output += "value:             {0}\n".format(self._value)
        output += "health:            {0}\n".format(self._health)
        output += "descriptions:      {0}\n".format(self._descriptions)
        return output

    @property
    def id(self):
        """
        The Dimm id

        :type :class: `str`
        """
        return self._id

    @property
    def value(self):
        """
        The Dimm value

        :type :class: 'int'
        """
        return self._value

    @property
    def health(self):
        """
        The Dimm health

        :type :class: `list`
        """
        return self._health

    @property
    def descriptions(self):
        """
        The Dimm descriptions

        :type :class: `list`
        """
        return self._descriptions