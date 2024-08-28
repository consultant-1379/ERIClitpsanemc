"""
File name: sanapilib.py
Version: ${project.version}
Contains general purpose functions used by San API
"""


import re
from sanapiexception import (SanApiOperationFailedException,
SanApiEntityAlreadyExistsException, SanApiCriticalErrorException,
SanApiEntityNotFoundException, SanApiCommandException, SanApiException)
from sanapicfg import SANAPICFG


"""CONSTANTS"""
STORAGE_PROCESSOR_A = 'A'
STORAGE_PROCESSOR_B = 'B'
CONTAINER_RAID_GROUP = 'RaidGroup'
CONTAINER_STORAGE_POOL = 'StoragePool'
LUNID_AUTO = 'auto'
MIN_NAME_LEN = 2
MAX_NAME_LEN = 255

"""GENERIC FUNCTIONS
For manipulating and validating data such as ints and strings etc
"""
def raise_ex(errmsg='SAN API PSL Error', ex=SanApiOperationFailedException,
             logger=None):
    """
    Generic exception raiser.

    :param errmsg: The error message.
    :type  errmsg: :class:`str`
    :param ex: The exception to raise.
    :type ex: :class:`SanApiOperationFailedException`
    :param logger: A logger object.
    :type logger: :class:`logger`
    :raises Exception: Raised if an exception encountered.
    """
    if logger:
        logger.error(str(errmsg))
    raise ex(errmsg, 1)

def raise_critical_ex(errmsg, logger=None):
    """
    Raises an SanApiCriticalErrorException with the provided error message
    :param errmsg: an error message
    :type errmsg: :class:`basestring`
    """
    raise_ex(errmsg, SanApiCriticalErrorException, logger)


def shell_escape(raw_string):
    """
    Sanitizes a string by inserting escape characters to make it
    shell-safe.

    :param raw_string: The string to sanitise
    :type raw_string: string

    :returns: The escaped string
    :rtype: string
    """
    spec_chars = '''"`$'(\\)!~#<>&*;| '''
    escaped = ''.join([c if c not in spec_chars else '\\' + c
                       for c in raw_string])
    return escaped


def is_int(num):
    """
    Returns true if num is an integer, stored either as int or as string.

    :param num: The number being checked.
    :type num: :class:`int`, :class:`long` or :class:`str`
    :returns: True if num is an integer, stored either as int or as string,
        else false.
    :rtype: :class:`boolean`
    """
    if isinstance(num, (int, long)):
        return True
    if isinstance(num, basestring):
        return num.isdigit()
    return False


def is_float(num):
    """
    Returns true if num is a float, stored either as int or as string.

    :param num: The number being checked.
    :type num: :class:`float` or :class:`str`
    :returns: True if num is a float, stored either as a float or as string,
        else false.
    :rtype: :class:`boolean`
    """
    if isinstance(num, (float)):
        return True

    try:
        float(num)
        return True
    except ValueError:
        return False


def is_positive_int(num):
    """
    Returns true if num is => 0 and is an integer, stored either as int or
        string.

    :param num: The number being checked.
    :type  num: :class:`int` or :class:`str`
    :returns: True if the num is positive, else False.
    :rtype: :class:`boolean`
    """
    if is_int(num) and int(num) == abs(int(num)):
        return True
    return False


def is_proper_fraction(fraction):
    """
    True if fraction is proper fraction in form numerator/denominator e.g. 2/9

    :param fraction: The fraction being checked.
    :type fraction: :class:`str`
    :returns: True if a proper fraction, else false.
    :rtype: :class:`boolean`
    """

    # fraction must be string
    if not isinstance(fraction, basestring):
        return False

    # get numerator and denominator if in num/denom format
    nums = fraction.split('/')
    if len(nums) != 2:
        return False

    numerator = nums[0]
    denominator = nums[1]

    # ensure the numerator and denominator are ints
    if not is_int(numerator) or not is_int(denominator):
        return False

    # proper fraction so numerator must be less than denominator
    if int(numerator) >= int(denominator):
        return False

    return True


def validate_float_and_make_string(number):
    """
    Method to validate that number is a float if not raise exception.
    If it is a float return it as a string.

    :param number: The number to be checked.
    :type  number: :class:`float` or :class:`str`
    :returns: The number as a string if it is actually an float
    :rtype: :class:`str`
    """
    if is_float(number):
        return str(number)
    else:
        err = "Parameter is not a float {0}".format(number)
        raise_ex(err)


def validate_int_and_make_string(number):
    """
    Method to validate that number is an int, if not raise exception.
    If it is an int, return it as a string.

    :param number: The number to be checked.
    :type  number: :class:`int`, :class:`long` or :class:`str`
    :returns: The number as a string if it is actually an int.
    :rtype: :class:`str`
    """
    if is_int(number):
        return str(number)
    else:
        raise_ex("Parameter is not an integer %s " % number)


def validate_int_and_make_int(number):
    """
    Method to validate that number is an int, if not raise an exception.

    :parameter number: The number being checked.
    :type number: :class:`int`, :class:`long` or :class:`str`
    :returns: The number as an int.
    :rtype: :class:`int`
    """
    return int(validate_int_and_make_string(number))


def validate_string(string_param, logger=None):
    """
    Method to validate that the given parameter is a string. Returns True
    on success, and on failure throws a SanApiOperationFailedException.

    :parameter string_param: The parameter being checked.
    :type string_param: :class:`str`
    :parameter logger: An optional logger.
    :type logger: :class:`logger`
    :returns: True if a string.
    :rtype: :class:`boolean`
    :raises SanApiOperationFailedException: Raised if string_param not a
        string.
    """
    if not isinstance(string_param, basestring):
        raise_ex("Not a string %s " % type(string_param), logger=logger)
    return True


def low_case_strip_space(paramstr):
    """
    Lower case and strip ALL space from string.

    :param paramstr: The string to perform the operation on.
    :type paramstr: :class:`str`
    :returns: paramstr converted to lower case with all space removed.
    :rtype: :class:`str`
    """
    if not isinstance(paramstr, basestring):
        raise_ex("Param must be a string")
    paramstr = paramstr.lower()
    paramstr = "".join(paramstr.split())
    return paramstr


def validate_snap_duration(duration, logger=None):
    """
    Method to validate if duration is a valid string that represents a SAN
    duration. It must be in the form of string composed by a number followed
    with no space by 'h', 'd', 'm' or 'y'. E.g.: "1h"

    :param duration: The duration being passed.
    :type duration: :class:`str`
    :param logger: An optional logger.
    :type logger: :class:`logger`
    :returns: True if the duration is valid.
    :rtype: :class:`boolean`
    """
    if not isinstance(duration, basestring) or \
            not(duration[-1:] in ['h', 'd', 'm', 'y']):
        raise_ex("Must be a string formed by a number followed by " +
                 "'h', 'd','m','y'. E.g 1y", logger=logger)
    keep_int = duration[0:-1]
    try:
        int(keep_int)
    except ValueError:
        raise_ex("Must be a string formed by an int followed by " +
                 "one of 'h', 'd', 'm' or 'y'. E.g 1y", logger=logger)
    return True


def validate_ipv4(addr):
    """
    Method to validate an ipv4 address.

    :param addr: An IPV4 address.
    :type addr: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not addr:
        return False
    octets = addr.split('.')
    if len(octets) != 4:
        return False
    for num in octets:
        if not num.isdigit():
            return False
        num = int(num)
        if num < 0 or num > 255:
            return False
    return True


def isBusEncDisk(bed):
    """
    Validates that the string is in valid BED format.

    Example:

    .. code-block:: python

        0_0_1

    :param bed: Bus enclosure disk entry for a SAN disk, e.g. 2_3_1; in bus 2,
        enclosure 3, disk num 1.
    :type bed: :class:`str`
    :returns: True if valid, else False
    :rtype: :class:`boolean`
    """

    if not bed:
        return False

    if re.search("\d+_\d+_\d+", bed) is None:
        return False

    individual_components = bed.split('_')

    if len(individual_components) != 3:
        return False

    bus = int(individual_components[0])
    enc = int(individual_components[1])
    disk = int(individual_components[2])

    if not is_int(bus):
        return False
    if not is_int(enc):
        return False
    if not is_int(disk):
        return False

    max_disk_id = int(SANAPICFG.get('General', 'MaxIDOfDAEDisks'))
    if bus < 0 or bus > 99:
        return False
    elif enc < 0 or enc > 99:
        return False
    elif disk < 0 or disk > max_disk_id:
        return False

    return True


"""SAN CLI specific functions"""


def is_valid_len(arg_name, arg_val):
    """
    Validate length of an argument

    :param arg_name: The name of the argument.
    :type arg_name: :class:`str`
    :param arg_val: The value of the argument.
    :type arg_val: :class:`str`
    :returns: A list of errors.
    :rtype: :class:`list`
    """
    errors = []

    if len(arg_val) < MIN_NAME_LEN or len(arg_val) > MAX_NAME_LEN:
        err = "{0} needs to be between {1} and {2} " \
            "characters long".format(arg_name, MIN_NAME_LEN, MAX_NAME_LEN)
        errors.append(err)
    return errors


def is_valid_action(action, args):
    """
    Method to validate the San Cli action.

    :param action: The action being validated.
    :type action: :class:`str`
    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: Any errors.
    :rtype: :class:`list`
    """
    errors = []
    valid_actions = ('create_snap',)

    if action:
        if args[action] not in valid_actions:
            errors.append("Action " + args[action] + " is not " \
              "valid. Valid action is," + " create_snap")

    return errors


def is_valid_lun_name(lun_name, args):
    """
    Method to validate the lun name.

    :param lun_name: The lun name being validated.
    :type lun_name: :class:`str`
    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors.
    :rtype: :class:`list`
    """
    errors = []
    if lun_name:
        if args[lun_name] is not None:
            errors = is_valid_len(lun_name, args[lun_name])
        else:
            errors.append("lun_name or lun_id is a mandatory argument")
    return errors


def is_valid_lun_id(lun_id, args):
    """
    Method to validate the lun id.

    :param lun_id: The lun id being validated.
    :type lun_id: :class:`str`
    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors.
    :rtype: :class:`list`
    """
    errors = []

    if lun_id:
        if args[lun_id]:
            if not is_positive_int(args[lun_id]):
                errors.append("lun_id must be a positive integer")
        else:
            errors.append("lun_name or lun_id is a mandatory argument")
    return errors


def is_valid_snap_name(snap_name, args):
    """
    Method to validate the snap name.

    :param snap_name: The snap name being validated.
    :type snap_name: :class:`str`
    :param args: dict if args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors.
    :rtype: :class:`list`
    """
    errors = []

    if args[snap_name] is not None:
        errors += is_valid_len(snap_name, args[snap_name])
    else:
        errors.append("snap_name is a mandatory argument ")
    return errors


def is_valid_user(user, args):
    """
    Method to validate the user. User is a mandatory argument.

    :param user: The user being validated.
    :type user: :class:`str`
    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors.
    :rtype: :class:`list`
    """
    errors = []
    if args[user]:
        errors = is_valid_len(user, args[user])
    # temporary error until we decide if user is mandatory
    else:
        errors.append("user is a mandatory argument ")

    return errors


def is_valid_password(password, args):
    """
    Method to validate the password. Password is a mandatory argument

    :param password: The password being validated.
    :type password: :class:`str`
    :param args: dict of args passed to sancli
    :type args: :class:`dict`
    :returns: List of errors.
    :rtype: :class:`list`
    """
    errors = []
    if args[password] is None:
        errors.append("password is a mandatory argument")
    else:
        errors = is_valid_len(password, args[password])

    return errors


def is_valid_scope(scope, args):
    """
    Method to validate the scope. Scope is Global by default.

    :param scope: The scope being validated.
    :type scope: :class:`str`
    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors
    :rtype: :class:`list`
    """
    errors = []
    match = False
    valid_scopes = ('global', 'local')
    scope_in = args[scope]
    for valid_scope in valid_scopes:
        if re.match(valid_scope, scope_in, re.IGNORECASE):
            match = True
    if not match:
        errors.append("%s is not valid. " \
        "Valid scopes are: (%s)" % (scope_in, ', '.join(valid_scopes)) \
        + " ")
    return errors


def is_valid_array(array, args):
    """
    Method to validate the array. Array is vnx1 by default.

    :param array: The array being validated.
    :type array: :class:`str`
    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors
    :rtype: :class:`list`
    """
    errors = []
    match = False
    valid_arrays = ('vnx1', 'vnx2', 'unity')

    get_array = args[array]
    if get_array:
        for valid_array in valid_arrays:
            if re.match(valid_array, get_array, re.IGNORECASE):
                match = True
    if not match:
        errors.append("%s is not valid.  Valid arrays are: (%s)" % \
                                 (get_array, ', '.join(valid_arrays)) + " ")
    return errors


def is_valid_ips(args):
    """
    Method to validate the IPs. Either ipa or ipb must be present.

    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors
    :rtype: :class:`list`
    """
    errors = []
    if args['ip_spa'] is None and args['ip_spb'] is None:
        errors.append("One or both of ipa and ipb must be supplied")
        return errors

    ip_a = args['ip_spa']
    if ip_a is not None:
        if not validate_ipv4(ip_a):
            errors.append("%s is not a valid IPV4 address" % ip_a)

    ip_b = args['ip_spb']
    if ip_b is not None:
        if not validate_ipv4(ip_b):
            errors.append("%s is not a valid IPV4 address" % ip_b)

    return errors


def is_valid_log(args):
    """
    Method to validate the log level. Argument log level is Info by default.

    :param args: dict of args passed to sancli.
    :type args: :class:`dict`
    :returns: List of errors
    :rtype: :class:`list`
    """
    errors = []
    match = False
    match2 = False
    valid_logs = ('Debug', 'Info')
    valid_dests = ('system', 'none')

    for valid_log in valid_logs:
        if re.match(valid_log, args['log_level'], re.IGNORECASE):
            match = True
    if not match:
        errors.append("log_level='%s' is not valid.  Valid log levels are: "\
                        "(%s)" % (args['log_level'], ', '.join(valid_logs)))
    for valid_dest in valid_dests:
        if re.match(valid_dest, args['log_dest'], re.IGNORECASE):
            match2 = True
    if not match2:
        errors.append("log_dest='%s' is not valid.  Valid log destinations \
                       are: (%s)" % (args['log_dest'], ','\
                                     .join(valid_dests)))
    return errors


"""VNX specific functions"""


def is_valid_raidtype(raid_type):
    """
    Method to validate that the passed raid_type is in the list of
    valid raid types from the config file

    :param raid_type: The RAID type being validated.
    :type raid_type: :class:`str`
    :returns: True if valid RAID type, else False.
    :rtype: :class:`boolean`
    """
    try:
        raid_type = str(raid_type)
    except:
        return False
    supported_rts = SANAPICFG.get('VNX', 'SupportedRaidTypes')

    return raid_type.lower().strip() in \
        (rt.lower().strip() for rt in supported_rts.split(","))


def is_valid_size(size):
    """
    Method to validate that  the passed size is in the list of
    valid sizes from the config file

    :param size: The size being validated.
    :type size: :class:`str`
    :returns: True if valid size, else False.
    :rtype: :class:`boolean`
    """
    try:
        size = str(size)
    except:
        return False
    supported_units = SANAPICFG.get('General', 'SupportedSizeUnits')
    matchobj = re.search(r'(\d+\.?\d*|\.\d+)(.*)', size)
    if matchobj:
        size_units = matchobj.group(2)
        return size_units.lower() in \
            (unit.lower() for unit in supported_units.split(","))
    else:
        return False


def is_valid_lunname(lunname):
    """
    Checks passed lun name is valid.
    TODO: figure out what max and min lengths are allowed and tet for them.

    :param lunname: The name of the LUN being validated.
    :type lunname: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not isinstance(lunname, basestring):
        return False
    if len(lunname) < 1:
        return False
    return True


def is_valid_sp(sp):
    """
    Check passed storage pool is valid.

    :param sp: The storage pool being validated.
    :type sp: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not isinstance(sp, basestring):
        return False
    try:
        normalise_storage_processor(sp)
    except SanApiOperationFailedException:
        return False
    return True


def is_valid_lun_type(luntype):
    """
    Method to validate that the LUN type is valid.

    :param luntype: The LUN type being validated.
    :type luntype: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not isinstance(luntype, basestring):
        return False
    luntypes = SANAPICFG.get('VNX', 'Luntypes')
    return luntype.lower().strip() in \
        (lt.lower().strip() for lt in luntypes.split(","))


def is_valid_lunid(lunid):
    """
    Method to validate that the LUN ID is valid.

    :param lunid: The LUN ID being validated.
    :type lunid: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not isinstance(lunid, basestring):
        return False
    return lunid.lower() == LUNID_AUTO or is_positive_int(lunid)


def normalise_container_type(cont):
    """
    Give standard name for raid group/storage pool.

    :param cont: The container name being normalised.
    :type cont: :class:`str`
    :returns: CONTAINER_STORAGE_GROUP or CONTAINER_RAID_GROUP
    :rtype: :class:`str`
    """
    if not isinstance(cont, basestring):
        raise_ex("Invalid container type" + cont)
    teststr = low_case_strip_space(cont)

    if teststr == "sp" or teststr == "storagepool":
        return CONTAINER_STORAGE_POOL
    elif teststr == "rg" or teststr == "raidgroup":
        return CONTAINER_RAID_GROUP
    else:
        raise_ex("Unknown container type" + cont)


def normalise_storage_processor(sp):
    """
    Give standard name storage processor

    :param sp: The storage processor name being normalised.
    :type sp: :class:`str`
    :returns: STORAGE_PROCESSOR_A or STORAGE_PROCESSOR_B
    :rtype: :class:`str`
    """
    if not isinstance(sp, basestring):
        raise_ex("Invalid storage processor" + sp)
    teststr = low_case_strip_space(sp)

    if teststr == "a" or teststr == "spa":
        return STORAGE_PROCESSOR_A
    elif teststr == "b" or teststr == "spb":
        return STORAGE_PROCESSOR_B
    else:
        raise_ex("Unknown storage processor" + sp)


def normalise_raid_group_for_vnx(raid):
    """
    Normalises the raid value.
    info object store raid as 0,1,10,5,6 (& N/A). navisec returns this info as
    r_X or RAIDX and for create lun operations expects format to be r_X.
    This function will convert r_X or RAIDX or just X, to plain X.

    :param raid: The raid value string.
    :type raid: :class:`str`
    :returns: The raid value normalised.
    :rtype: :class:`str`
    """
    raid = str(raid)
    raid = raid.replace('Hot Spare', 'HS')
    raid = raid.replace('RAID', '')
    raid = raid.replace('r_', '')
    raid = raid.replace('r', '')
    raid = raid.replace('1/0', '10')
    raid = raid.replace('1_0', '10')

    if not is_valid_raidtype(raid):
        #raise_ex("Invalid raid type " + raid)
        raid = "UNKNOWN"

    return raid


def is_valid_sp_port(port):
    """
    Method to validate that the storage processor port nr. is valid.
    Allowing any postive int (including 0) to be valid.

    :param port: The port being checked.
    :type port: :class:`int`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not is_positive_int(port):
        return False
    return True


def is_valid_arraycommpath(value):
    """
    Method that validates that arraycommpath value is valid, e.g. (0 or 1)

    :param value: The value of arraycommpath.
    :type value: :class:`int`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not is_int(value):
        return False
    return int(value) in (0, 1)


def is_valid_failover_mode(value):
    """
    Checks for valid host initiator failover mode

    :param value: The value of the host initiator failover mode.
    :type value: :class:`int`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not is_int(value):
        return False
    return int(value) in (0, 1, 2, 3, 4)


def convert_size_to_mb(size):
    """
    Converts size from 3Mb, 1.2Tb etc to number in Mb

    :param size: The size to convert into MB.
    :type size: :class:`str`
    :returns: Size in MB as string.
    :rtype: :class:`str`
    """
    # If just number with no unit, assume Mb so just return
    try:
        float(size)
        return size
    except ValueError:
        pass

    sizenum, sizeq = convert_size_to_vnx(size)  # this forces int
    if sizeq == 'mb':
        multiplier = 1
    elif sizeq == 'gb':
        multiplier = 1024
    elif sizeq == 'tb':
        multiplier = 1024 * 1024

    return str(float(sizenum) * multiplier)


def convert_size_to_vnx(size):
    """
    Converts size string in format e.g. 500Gb to VNX compatible format
    i.e. size and size_qualifier
    Returns tuple size, size_qualifier

    :param size: The size to convert.
    :type size: :class:`str`
    :returns: A tuple of size, size_qualifier
    :rtype: :class:`tuple`
    """
    # First check if just number then assume megabytes
    if is_int(size):
        size = "%sMb" % size

    if not is_valid_size(size):
        raise_ex("Invalid size " + size)

    matchobj = re.search(r'(\d+\.?\d*|\.\d+)(.*)', size)
    sizenum = matchobj.group(1)
    size_qual = matchobj.group(2).lower()

    # To allow for single digit size qualifiers, e.g. m, g, t
    if len(size_qual) == 1:
        size_qual = size_qual + 'b'

    if not is_int(sizenum):
        raise_ex("Numeric component of size must be integer " + size)

    return (sizenum, size_qual.lower())


def convert_raid_type_to_vnx(raid_type, context):
    """
    Converts raid type string in format
    e.g. 10 to VNX compatible format r1_0
    10 -> 1_0
    HS -> hs

    :param raid_type: The RAID type to convert.
    :type raid_type: :class:`str`
    :param context: Either LUN or pool.
    :type context: :class:`str`
    :returns: The converted RAID type.
    :rtype: :class:`str`
    """
    if not is_valid_raidtype(raid_type):
        raise_ex("Invalid RAID Type provided: " + str(raid_type),
                 SanApiCriticalErrorException)

    if context.lower() == "lun":
        raid_type = "r" + raid_type
        raid_type = raid_type.replace('rHS', 'hs')
        raid_type = raid_type.replace('10', '1_0')
    elif context.lower() == "pool":
        raid_type = "r_" + raid_type
    else:
        raise_ex("Unrecognized context argument " + str(context))
    return raid_type


def convert_lun_type_to_vnx(lun_type):
    """
    Converts lun type string in format e.g. thick to VNX compatible format
    e.g. nonThin

    :param lun_type: The type of LUN to convert, e.g. thick.
    :type lun_type: :class:`str`
    :returns: Converted LUN type.
    :rtype: :class:`str`
    """
    lun_type = lun_type.lower()
    if not is_valid_lun_type(lun_type):
        raise_ex("Invalid LUN type " + lun_type, SanApiCriticalErrorException)

    if not is_valid_lun_type(lun_type):
        vnx_lun_type = "UNKNOWN"
    if lun_type == "thin":
        vnx_lun_type = "Thin"
    else:
        vnx_lun_type = "nonThin"
    return vnx_lun_type


def is_valid_storage_pool_name(sp):
    """
    Method to validate the storage pool name.
    TODO: other validations - max length, invalid chars.

    :param sp: Storage Pool name to validate.
    :type sp: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not isinstance(sp, basestring):
        return False
    return True


def is_valid_policyid(p_id):
    """
    Method to validate passed policy id.

    :param p_id: The policy ID to validate.
    :type p_id: int, long or str
    :returns: True if valid and not less than 1, else False.
    :rtype: boolean
    """
    try:
        p_id = validate_int_and_make_string(p_id)
    except:
        return False

    if int(p_id) < 1:
        return False
    return True


def is_valid_policy_ratio(ratio):
    """
    Method to validate passed ratio.

    :param ratio: The policy ratio to validate.
    :type ratio: :class:`int` or :class:`str`
    :returns: True if an int and valid, else False.
    :rtype: :class:`boolean`
    """
    if not is_int(ratio):
        return False
    return ratio > 0


def is_valid_wwn(wwn):
    """
    Method to validate a wwn.
    Valid wwn regarded as 16 pairs of Hex Digits separated
    by ':' e.g.

        .. code-block:: python

            50:01:43:80:18:70:94:89:50:01:43:80:18:70:94:88

    :param wwn: The wwn to validate.
    :type wwn: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not isinstance(wwn, basestring):
        return False

    if re.search(r'^([0-9A-F]{2}[:-]){15}([0-9A-F]{2})$', wwn, re.I):
        return True

    return False


def is_valid_uuid(uuid):
    """
    Method to validate a UUID.
    Valid UUID regarded as 16 pairs of Hex Digits separated
    by ':' e.g.

        .. code-block:: python

            50:01:43:80:18:70:94:89:50:01:43:80:18:70:94:88

    :param uuid: The UUID to validate.
    :type uuid: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """

    if not isinstance(uuid, basestring):
        return False

    if re.search(r'^([0-9A-F]{2}[:-]){15}([0-9A-F]{2})$', uuid, re.I) or \
       re.search(r'^[0-9A-F-]{36}$', uuid, re.I):
        return True

    return False


def raise_appropriate_exception(navi_errmsg, my_errmsg,
                                default_except_type=SanApiException,
                                include_navi_errmsg=False,
                                logger=None, errcode=1):
    """
    This function examines the error message from navisec and
    raise the appropriate exception type based on this.
    If the navisec error does not match any of the known
    errors then the user-supplied exception type will be
    raised.

    :param navi_errmsg: The original error message from navisec.
    :type navi_errmsg: :class:`str`
    :param my_errmsg: The error message to be included in new exception.
    :type my_errmsg: :class:`str`
    :param default_except_type: Optional, default type of exception to raise
        if navisec error does not match known errors.
    :type default_except_type: :class:`Exception`
    :param include_navi_errmsg: Optional, include the original navi error.
    :type include_navi_errmsg: :class:`boolean`
    :param logger: Optional, SANAPI logger object.
    :type logger: :class:`logger`
    :raises Exception: Raised depending on the passed params.
    """
    if not navi_errmsg:
        raise_ex("NavisecCLI error message not specified",
                  SanApiCriticalErrorException, logger)

    if not my_errmsg:
        raise_ex("SANAPI error message not specified",
                  SanApiCriticalErrorException, logger)

    navisec_errormsg_exceptions_mapping = {
        "Unable to create the LUN because the specified name " +
        "is already in use":
            SanApiEntityAlreadyExistsException,
        "Physical unit already exists":
            SanApiEntityAlreadyExistsException,
        "Error: bind command failed\nLUN already exists":
            SanApiEntityAlreadyExistsException,
        "Pool name is already used":
            SanApiEntityAlreadyExistsException,
        "Error: storagegroup command failed\nError returned from" +
        " Agent\nStorage Group name already in use":
            SanApiEntityAlreadyExistsException,
        "Error: storagegroup command failed\nError returned from" +
        " Agent\nRequested LUN has already been added to this Storage Group":
            SanApiEntityAlreadyExistsException,
        "Error: createrg command failed\nError returned from Agent\n" +
        "RAID Group by that ID already exists":
            SanApiEntityAlreadyExistsException,
        "The specified snapshot name is already in use":
            SanApiEntityAlreadyExistsException,
        "Error: getlun command failed\nInvalid LUN number\nLUN does not exist":
            SanApiEntityNotFoundException,
        "Could not retrieve the specified \(pool lun\). " +
        "The \(pool lun\) may not exist":
            SanApiEntityNotFoundException,
        "Error: storagegroup command failed\nThe group name or UID does " +
        "not match any storage groups for this array":
            SanApiEntityNotFoundException,
        "Error: getrg command failed\nRAIDGroup Not Found":
            SanApiEntityNotFoundException,
        "Could not retrieve the specified \(Storagepool\)." +
        " The \(Storagepool\) may not exist":
            SanApiEntityNotFoundException,
        "Error: storagegroup command failed\nError returned" +
        " from Agent\nLUN [0-9]+ : No such Host LUN in this Storage Group":
            SanApiEntityNotFoundException,
        "Cannot create the snapshot. The specified resource does not exist":
            SanApiEntityNotFoundException,
        "Could not retrieve the specified Snapshot. The Snapshot may not "\
        "exist":
            SanApiEntityNotFoundException,
        "Could not retrieve the specified (Snapshot). The (Snapshot) may not "\
        "exist\n":
            SanApiEntityNotFoundException,
        "Cannot restore the LUN. LUN does not exist.":
            SanApiEntityNotFoundException,
        "Cannot destroy the snapshot. The specified snapshot does not exist.":
            SanApiEntityNotFoundException,
        "Are you sure you want to perform this operation?(y/n):":
            SanApiCommandException,
    }
    # not used at the moment but may switch to using codes
    # to map
    navisec_errorcode_exceptions_mapping = {
        "1898810628": SanApiEntityAlreadyExistsException,
        "1610614036": SanApiEntityAlreadyExistsException,
        "31": SanApiEntityAlreadyExistsException,
        "1": SanApiEntityAlreadyExistsException,
        "66": SanApiEntityAlreadyExistsException,
        "1903001605": SanApiEntityAlreadyExistsException,
        "30": SanApiEntityNotFoundException,
        "19721": SanApiEntityNotFoundException,
        "83": SanApiEntityNotFoundException,
        "72": SanApiEntityNotFoundException,
        "35090": SanApiEntityNotFoundException
    }

    exe_type = None
    for key in navisec_errormsg_exceptions_mapping:
        if re.match(key, navi_errmsg) or key == navi_errmsg:
            exe_type = navisec_errormsg_exceptions_mapping[key]
            break

    if exe_type is None:
        exe_type = default_except_type

    if include_navi_errmsg:
        my_errmsg += " Original NavisecCLI error: " + navi_errmsg
    raise exe_type(my_errmsg, int(errcode))


def version_checker(check_version, reference_version, num_tokens, seperator):
    """
    Checks the version info from the array.

    :param check_version: The flare version from the SAN.
    :type check_version: :class:`str`
    :param reference_vision: The valid version from the config.
    :type reference_vision: :class:`str`
    :param num_tokens: The number of parts of the version to validate against.
    :type num_tokens: :class:`str`
    :param seperator: The part seperator.
    :type seperator: :class:`str`
    :returns: True if valid, else False.
    :rtype: :class:`boolean`
    """
    if not check_version:
        #print "No version provided to check"
        return False

    if not reference_version:
        #print "No version provided to check against"
        return False

    if not num_tokens:
        #print "I don't know how many sofware versions to check"
        return False

    if not reference_version:
        #print "No version seperator provided"
        return False

    if num_tokens == 'all':

        check_this_split = check_version.split(seperator)
        reference_version_split = reference_version.split(seperator)
    else:
        check_this_split = check_version.split(seperator)[:int(num_tokens)]
        reference_version_split = reference_version.split(
                                                seperator)[:int(num_tokens)]

    check_this_split = [int(i) for i in check_this_split]
    reference_version_split = [int(i) for i in reference_version_split]

    if check_this_split == reference_version_split:
        return True
    else: 
        return False


def validate_lun_create(lun_name, size, container_type, container,
           storage_processor, raid_type, lun_type,
           lun_id, ignore_thresholds, array_specific_options, logger):
    """
    Validates the parameters of the create_lun function and returns a
    dictionary with validated and formated items. If any of the items
    fail to validate and SanApiCriticalErrorException will be raised.

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

    params = {"lun_name": lun_name, "size": size,
            "container_type": container_type, "container": container,
            "storage_processor": storage_processor, "raid_type": raid_type,
            "lun_type": lun_type, "lun_id": lun_id, 
            "ignore_thresholds": ignore_thresholds,
            "array_specific_options": array_specific_options}

    # validate lun name
    if not is_valid_lunname(params["lun_name"]):
        raise_critical_ex("Invalid LUN name: %s"
                % lun_name, logger)
    # validate size
    try:
        size_num, size_q = convert_size_to_vnx(size)
    except SanApiCriticalErrorException:
        raise_critical_ex("Invalid size: %s " % size, logger)
    # add size_num and size_q parameters to the dictionary
    params["size_num"], params["size_q"] = size_num, size_q
    # format container type
    try:
        params["container_type"] = normalise_container_type(
                container_type)
    except SanApiOperationFailedException:
        raise_critical_ex("Invalid container type: %s"
                % container_type, logger)
    # validate storage_processor
    if not is_valid_sp(storage_processor.lower()):
        raise_critical_ex("Invalid storage processor: %s"
                % storage_processor, logger)
    # validate lun id
    if not is_valid_lunid(str(lun_id).lower()):
        raise_critical_ex("Invalid LUN id: %s"
                % lun_id, logger)
    # validate ignore_thresholds
    if not type(ignore_thresholds) is bool:
        raise_critical_ex("Invalid ignore_thresholds setting: %s"
                % str(ignore_thresholds), logger)
    # Format remaining parameters
    if params["container_type"] == CONTAINER_RAID_GROUP:
        params["raid_type"] = convert_raid_type_to_vnx(
                raid_type, "lun")
    params["lun_type"] = lun_type.lower()
    # add new parameter vnx_lun_type to the dictionary
    params["vnx_lun_type"] = convert_lun_type_to_vnx(
            params["lun_type"])
    params["storage_processor"] = storage_processor.lower()
    return params


"""Unity specific functions"""


def is_valid_unity_raidtype(raid_type):
    """
    Method to validate that the passed raid_type is in the list of
    valid raid types from the config file

    :param raid_type: The RAID type being validated.
    :type raid_type: :class:`str`
    :returns: True if valid RAID type, else False.
    :rtype: :class:`boolean`
    """
    try:
        raid_type = str(raid_type)
    except:
        return False
    supported_rts = SANAPICFG.get('UNITY', 'SupportedRaidTypes')

    return raid_type.lower().strip() in \
        (rt.lower().strip() for rt in supported_rts.split(","))


def convert_raid_type_to_unity(raid_type, context):
    """
    Converts raid type to Unity Rest api value (integer)
    e.g. 5 -> 1 (1 is the integer value for raid 5)

    :param raid_type: The RAID type to convert.
    :type raid_type: :class:`str`
    :param context: Either LUN or pool.
    :type context: :class:`str`
    :returns: The converted RAID type.
    :rtype: :class:`str`
    """
    if not is_valid_unity_raidtype(raid_type):
        raise_ex("Invalid RAID Type provided: " + str(raid_type),
                 SanApiCriticalErrorException)
    inputs = {5: 1, 10: 7, 1: 3, 6: 10}
    if context.lower() == "pool":
        converted_raid_type = inputs.get(raid_type)
    else:
        raise_ex("Unrecognized context argument " + str(context))
    return converted_raid_type

