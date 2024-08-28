'''
Created on 15 Jul 2014

Common functions for unit test code

@author: edavmax
'''
from mock import patch, Mock, MagicMock
import re
import unittest
import logging
from sanapiinfo import *
from sanapiexception import *
import os

# -----------------------------------------------------
# CLASSES



class MockProc():
    # Use this class when Popen/proc  needs to be mocked
    # and several different xml outputs need to be 
    # returned (e.g. get_luns calls Popen twice and expects
    # output from both getlun and lun -list.
    # 
    # Here's how to use it:
    # 1) The constructor takes three list arguments:
    #   a) a list of files representing stdout
    #   b) a list of files representing stderr
    #   c) a list of exit codes for each call 
    # 2) Create a MockProc object with these lists
    # 3) Mock subprocess.Popen to return this object
    # 
    # Example:
    # We want to test get_luns, and we know that this will
    # perform a getlun, then a lun -list.
    # Let's assume we already have the xml output for the 
    # commands.  Also, there's no stderr and the exit code 
    # is 0... 
    #
    # outlist = [ './getlun.xml', './lunlist.xml' ]
    # errlist = [ './empty.txt', './empty.txt' ]
    # extlist = [ 0, 0 ] 
    # mokproc = MockProc(outlist, errlist, extlist) 
    # subprocess.Popen = mock.Mock(return_value=mokproc)
    # 
    # And that's it.  The get_luns can be tested with:
    # vnx.initialise(spa, spb, user, pass, scope, getcert=False, vcheck=False)
    # result = vnx.get_luns()
    #
    # NOTE: remember by default navisec will handle certificates, which will 
    # result in calls to Popen you might not have catered for in your xml.
    # so ensure you initialise the api with getcert=False. 
    # For more examples look in test_empty_vnx.py.

    def __init__(self, stdoutfiles, stderrfiles, rets ):
        self.returncode = 0
        self.outs = stdoutfiles
        self.errs = stderrfiles
        self.rets = rets
        self.count = -1

    def communicate(self):
        self.count += 1

        self.returncode = self.rets[self.count]
        output = self._read_file(self.outs[self.count])
        err    = self._read_file(self.errs[self.count])
        return (output, err)

    def _read_file(self, filename):
        with open(filename, "r") as outfile:
            outdata = outfile.read()
        return outdata



# -----------------------------------------------------
# DECORATORS


# Decorator for 2.6 to implement unittest.skip @unittest.skip("")
def skip(func):
    return



def singleton(cls):
    '''
    :param cls:
    '''

    def getinstance():
        '''
        getinstance()
        '''
        if cls not in singleton.instances:
            singleton.instances[cls] = cls()
        return singleton.instances[cls]
    return getinstance

singleton.instances = {}


# -----------------------------------------------------
# FUNCTIONS

def two_args_function(param1,param2):
    pass

def get_test_file_data(filename=None):
        """
        load test file into a string 
        """
        if filename:
            with open(filename, "r") as outfile:
                outdata = outfile.read()
        else:
            outdata = ""

        return outdata


def prepare_mocked_popen(stdout_file, stderr_file=None, ret_code=0):
        '''Prepares a mocked vnxCommApiObj. filename_with_path must be a
        filename path to the expected response e.g. data/storage_pool_getbyid_error_response.xml
        Returns the mocked object to use for assertions'''
        popen_patcher = patch('vnxcommonapi.subprocess.Popen')
        mock_popen = popen_patcher.start()

        mock_rv = Mock()

        outdata = get_test_file_data(stdout_file)
        errdata = get_test_file_data(stderr_file)
        # communicate() returns [STDOUT, STDERR]
        mock_rv.communicate.return_value = [outdata, errdata]
        mock_popen.return_value = mock_rv
        mock_popen.return_value.returncode = ret_code

        return mock_popen

def myassert_raises_regexp(tstobj, exceptiontype, message, function, *args, **kwargs):
    '''
    implementation of AssertRaisesRegexp for 2.6 (AssertRaisesRegexp was added to 2.7)
    
    '''
    try:
        function(*args, **kwargs)
    except exceptiontype as e:
        if not re.search(message, e.args[0]):
            tstobj.fail("Exception " + str(exceptiontype) + " does not contain expected message " + message + \
                           ". Contents of exception:" + e.args[0])
    except Exception as e:
        tstobj.fail("No Exception of type " + str(exceptiontype) + " raised," +
                "Exception '" + str(e) + "' raised instead.")
    else:
        tstobj.fail("No Exception of any type raised")



def myassert_is_instance(tstobj, objtotest, classname):
    """
    Implementation of assertIsInstance (which is available in 2.7)
    """
    cname = classname.__name__
    oname = objtotest.__class__.__name__

    if oname != cname:
        tstobj.fail("Object is type %s, should be %s" % (oname, cname))

def myassert_in(tstobj, first, second, msg):
    """
    Implementation of assertIn from 2.7
    """
    success = False
    for item in second:
        if first == item:
            success = True
            break

    if success == False:
        tstobj.fail(msg)

def getSP():
    name = 'test1'
    poolid = '3'
    raid = '5'
    size = '1100.022'
    # to give in Mbs to be consistent with get_lun
    size = str(int(float(size) * 1024))
    available = '926.042'
    # to give in Mbs to be consistent with get_lun
    available = str(int(float(available) * 1024))
    full = "49.171"
    subscribed = "49.335"
    return StoragePoolInfo (name, poolid, raid , size, available, full, subscribed)


def getSG():
    sgname = "atsfs43_44"
    sguid = 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25'
    sgshare = True
    sghbasp = None
    sghlualu = None
    return StorageGroupInfo(sgname, sguid, sgshare, sghbasp, sghlualu)


def getPairsSG():
    sgname = "atsfs43_44"
    sguid = 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25'
    sgshare = True

    sghbasp = getHbaList()
    sghlualu = getHluList()
    return StorageGroupInfo(sgname, sguid, sgshare, sghbasp, sghlualu)


def getHbaList():

    hb1 = HbaInitiatorInfo('50:01:43:80:12:0B:33:61:50:01:43:80:12:0B:33:60', 'A', 0)
    hb2 = HbaInitiatorInfo('50:01:43:80:12:0B:33:61:50:01:43:80:12:0B:33:60', 'A', 1)
    hb3 = HbaInitiatorInfo('50:01:43:80:12:0B:33:61:50:01:43:80:12:0B:33:60', 'B', 0)
    hb4 = HbaInitiatorInfo('50:01:43:80:12:0B:33:61:50:01:43:80:12:0B:33:60', 'B', 1)
    hb5 = HbaInitiatorInfo('50:01:43:80:12:0B:36:09:50:01:43:80:12:0B:36:08', 'A', 0)
    hb6 = HbaInitiatorInfo('50:01:43:80:12:0B:36:09:50:01:43:80:12:0B:36:08', 'A', 1)
    hb7 = HbaInitiatorInfo('50:01:43:80:12:0B:36:09:50:01:43:80:12:0B:36:08', 'B', 0)
    hb8 = HbaInitiatorInfo('50:01:43:80:12:0B:36:09:50:01:43:80:12:0B:36:08', 'B', 1)

    hbl = []
    hbl.append(hb1)
    hbl.append(hb2)
    hbl.append(hb3)
    hbl.append(hb4)
    hbl.append(hb5)
    hbl.append(hb6)
    hbl.append(hb7)
    hbl.append(hb8)

    return hbl

def getHbaList2():
    hsp0 = HbaInitiatorInfo('50:01:43:80:04:BF:48:19:50:01:43:80:04:BF:48:18', 'A', '1')
    hsp1 = HbaInitiatorInfo('50:01:43:80:04:BF:48:19:50:01:43:80:04:BF:48:18', 'B', '1')
    hsp2 = HbaInitiatorInfo('50:01:43:80:04:BF:57:59:50:01:43:80:04:BF:57:58', 'A', '1')
    hsp3 = HbaInitiatorInfo('50:01:43:80:04:BF:57:59:50:01:43:80:04:BF:57:58', 'B', '1')
    hspl = [ hsp0, hsp1, hsp2, hsp3 ]
    return hspl


def getHluList():
    hl1 = HluAluPairInfo(5, 24)
    hl2 = HluAluPairInfo(4, 34)
    hl3 = HluAluPairInfo(3, 3)
    hl4 = HluAluPairInfo(2, 32)
    hl5 = HluAluPairInfo(1, 29)
    hl6 = HluAluPairInfo(0, 30)

    hll = []
    hll.append(hl1)
    hll.append(hl2)
    hll.append(hl3)
    hll.append(hl4)
    hll.append(hl5)
    hll.append(hl6)
    return hll

def getHluList2():
    hlu0 = HluAluPairInfo(0, 18)
    hlu1 = HluAluPairInfo(1, 19)
    hlu2 = HluAluPairInfo(2, 20)
    hlu3 = HluAluPairInfo(3, 21)
    hlu4 = HluAluPairInfo(4, 22)
    hlu5 = HluAluPairInfo(5, 23)
    hlu6 = HluAluPairInfo(6, 12)
    hlu7 = HluAluPairInfo(7, 13)
    hlu8 = HluAluPairInfo(8, 14)
    hlu9 = HluAluPairInfo(9, 15)
    hlul = [ hlu0, hlu1, hlu2, hlu3, hlu4, hlu5, hlu6, hlu7, hlu8, hlu9 ]
    return hlul

def getLunList():
    l = []
    l.append(LunInfo("37", "GEO_LUN_14", "60:06:01:60:97:D0:35:00:A7:1C:7D:B5:3B:1E:E4:11", "5", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("36", "GEO_LUN_12", "60:06:01:60:97:D0:35:00:B0:AC:6E:8B:3B:1E:E4:11", "4", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("35", "GEO_LUN_13", "60:06:01:60:97:D0:35:00:D4:6C:07:9E:3B:1E:E4:11", "4", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("66", "LUN", "60:06:01:60:97:D0:35:00:3D:B8:70:1A:D6:29:E4:11", "6", "1Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("67", "LUN", "60:06:01:60:97:D0:35:00:DF:67:08:21:D6:29:E4:11", "6", "1Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("24", "GEO_LUN_1", "60:06:01:60:97:D0:35:00:36:AE:B9:9C:3A:1E:E4:11", "2", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("25", "GEO_LUN_2", "60:06:01:60:97:D0:35:00:23:D6:05:A8:3A:1E:E4:11", "2", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("26", "GEO_LUN_3", "60:06:01:60:97:D0:35:00:28:7B:7D:B8:3A:1E:E4:11", "2", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("27", "space here", "60:06:01:60:97:D0:35:00:C2:85:66:C6:3A:1E:E4:11", "atpool", "130Gb", "StoragePool", "1", "A"))
    l.append(LunInfo("20", "xb947_fencing_3", "60:06:01:60:97:D0:35:00:E6:C6:5E:13:3A:1E:E4:11", "1", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("21", "xb947_fencing_4", "60:06:01:60:97:D0:35:00:3F:93:1A:2C:3A:1E:E4:11", "1", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("48", "lun1", "60:06:01:60:97:D0:35:00:38:CD:C0:71:57:24:E4:11", "atpool", "1Gb", "StoragePool", "5", "A"))
    l.append(LunInfo("23", "xb947_fencing_6", "60:06:01:60:97:D0:35:00:29:B9:02:4D:3A:1E:E4:11", "1", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("46", "fedepool_1", "60:06:01:60:97:D0:35:00:90:29:C5:6C:E3:22:E4:11", "fedepool", "1Gb", "StoragePool", "5", "A"))
    l.append(LunInfo("44", "gerrylun2", "60:06:01:60:97:D0:35:00:2D:A0:87:5C:32:22:E4:11", "gerryspool", "10Mb", "StoragePool", "5", "A"))
    l.append(LunInfo("42", "gerrylun", "60:06:01:60:97:D0:35:00:61:31:E3:10:2D:22:E4:11", "gerryspool", "10Mb", "StoragePool", "5", "A"))
    l.append(LunInfo("28", "GEO_LUN_5", "60:06:01:60:97:D0:35:00:AD:29:3D:D9:3A:1E:E4:11", "3", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("29", "GEO_LUN_6", "60:06:01:60:97:D0:35:00:22:7B:0F:E8:3A:1E:E4:11", "3", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("40", "GEO_LUN_17", "60:06:01:60:97:D0:35:00:86:A7:60:00:3C:1E:E4:11", "5", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("41", "davemaxwellisaniceguy_1", "60:06:01:60:97:D0:35:00:5D:55:E1:19:C4:23:E4:11", "atpool", "1Gb", "StoragePool", "5", "A"))
    l.append(LunInfo("1", "xb1392_OSSDG_2", "60:06:01:60:97:D0:35:00:C1:CB:43:27:38:1E:E4:11", "0", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("0", "xb1392_OSSDG_1", "60:06:01:60:97:D0:35:00:91:92:B5:B4:37:1E:E4:11", "0", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("3", "xb1392_SYBASEDG_2", "60:06:01:60:97:D0:35:00:C3:A4:96:66:39:1E:E4:11", "0", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("2", "xb1392_SYBASEDG_1", "60:06:01:60:97:D0:35:00:F9:6F:9E:3B:38:1E:E4:11", "0", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("5", "xb1392_fencing_2", "60:06:01:60:97:D0:35:00:5D:0F:14:7F:38:1E:E4:11", "0", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("4", "xb1392_fencing_1", "60:06:01:60:97:D0:35:00:02:BD:B5:6B:38:1E:E4:11", "0", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("7", "xb1392_fencing_4", "60:06:01:60:97:D0:35:00:C4:B0:ED:AC:38:1E:E4:11", "0", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("6", "xb1392_fencing_3", "60:06:01:60:97:D0:35:00:F7:A2:C7:96:38:1E:E4:11", "0", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("9", "xb1392_fencing_6", "60:06:01:60:97:D0:35:00:D8:34:64:DD:38:1E:E4:11", "0", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("8", "xb1392_fencing_5", "60:06:01:60:97:D0:35:00:70:9C:39:C5:38:1E:E4:11", "0", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("49", "lun2", "60:06:01:60:97:D0:35:00:BE:78:58:83:57:24:E4:11", "atpool", "1Gb", "StoragePool", "5", "A"))
    l.append(LunInfo("63933", "MaxwellHouse", "60:06:01:60:97:D0:35:00:F7:A0:AF:22:C9:23:E4:11", "atpool", "1Gb", "StoragePool", "5", "A"))
    l.append(LunInfo("39", "GEO_LUN_16", "60:06:01:60:97:D0:35:00:60:5B:9E:EC:3B:1E:E4:11", "5", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("12", "xb947_OSSDG_1", "60:06:01:60:97:D0:35:00:D4:96:5C:8F:39:1E:E4:11", "1", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("94", "LUN", "60:06:01:60:97:D0:35:00:08:FB:45:FE:69:28:E4:11", "6", "1Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("14", "xb947_SYBASEDG_1", "60:06:01:60:97:D0:35:00:90:D7:E1:B0:39:1E:E4:11", "1", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("11", "xb1392_pri", "60:06:01:60:97:D0:35:00:71:50:B0:09:39:1E:E4:11", "0", "150Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("10", "xb1392_sec", "60:06:01:60:97:D0:35:00:6C:26:C8:F3:38:1E:E4:11", "0", "150Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("13", "xb947_OSSDG_2", "60:06:01:60:97:D0:35:00:2D:65:FC:70:3A:1E:E4:11", "1", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("38", "GEO_LUN_15", "60:06:01:60:97:D0:35:00:F1:28:D8:DB:3B:1E:E4:11", "5", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("15", "xb947_SYBASEDG_2", "60:06:01:60:97:D0:35:00:68:9D:7D:C8:39:1E:E4:11", "1", "200Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("22", "xb947_fencing_5", "60:06:01:60:97:D0:35:00:37:77:36:3D:3A:1E:E4:11", "1", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("17", "xb947_sec", "60:06:01:60:97:D0:35:00:F3:E5:D8:E1:39:1E:E4:11", "1", "150Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("16", "xb947_pri", "60:06:01:60:97:D0:35:00:6F:C8:97:D3:39:1E:E4:11", "1", "150Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("33", "GEO_LUN_10", "60:06:01:60:97:D0:35:00:44:74:58:5C:3B:1E:E4:11", "4", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("18", "xb947_fencing_1", "60:06:01:60:97:D0:35:00:80:33:C0:F4:39:1E:E4:11", "1", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("31", "GEO_LUN_8", "60:06:01:60:97:D0:35:00:03:79:05:0D:3B:1E:E4:11", "3", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("30", "GEO_LUN_7", "60:06:01:60:97:D0:35:00:D8:1C:A4:FF:3A:1E:E4:11", "3", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("51", "LUN", "60:06:01:60:97:D0:35:00:E2:64:57:47:49:28:E4:11", "6", "1Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("50", "LUN", "60:06:01:60:97:D0:35:00:CA:49:A4:15:49:28:E4:11", "6", "1Gb", "RaidGroup", "5", "A"))
    l.append(LunInfo("53", "richards_pool", "60:06:01:60:97:D0:35:00:03:6D:77:A9:6E:24:E4:11", "atpool", "1Gb", "StoragePool", "5", "A"))
    l.append(LunInfo("34", "GEO_LUN_11", "60:06:01:60:97:D0:35:00:59:64:28:6B:3B:1E:E4:11", "4", "130Gb", "RaidGroup", "1", "A"))
    l.append(LunInfo("19", "xb947_fencing_2", "60:06:01:60:97:D0:35:00:FB:24:B5:02:3A:1E:E4:11", "1", "100Mb", "RaidGroup", "5", "A"))
    l.append(LunInfo("32", "gerrylun1", "60:06:01:60:97:D0:35:00:74:4A:3E:89:0F:22:E4:11", "gerryspool", "10Gb", "StoragePool", "5", "A"))
    return l


def getLunListDict():
    lundict = {
        'LOGICAL UNIT NUMBER ': '23',
        'Name': 'stelun',
        'UID': 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25',
        'Pool Name': 'pool1',
        'User Capacity (GBs)': '8',
        'Raid Type': '5',
        'Default Owner': 'A',
        'Current Operation': 'None',
        'Current Operation State': 'N/A',
        'Current Operation Status': 'N/A',
        'Current Operation Percent Completed': '0',
        'Consumed Capacity (GBs)': '0'
    }
    return lundict


def getLunListObject():
    lun = '23'
    name = 'stelun'
    uid = 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25'
    container = 'pool1'
    size = '8192'
    container_type = 'Storage Pool'
    raid = '5'
    default_owner = 'A'
    curr_op = 'None'
    curr_op_state = 'N/A'
    curr_op_status = 'N/A'
    curr_op_perc_complete = '0'
    consumed = '0'

    return LunInfo(lun, name, uid, container, size, container_type,
                   raid, default_owner, curr_op, curr_op_state,
                   curr_op_status, curr_op_perc_complete, consumed)


def getGetLunDict():
    lundict = {
        'LOGICAL UNIT NUMBER': '23',
        'Name': 'stelun',
        'UID': 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25',
        'RAIDGroup ID': '12',
        'LUN Capacity(Megabytes)': '8192',
        'RAID Type': '5',
        'Default Owner': 'A' 
    }
    return lundict

def getLunGetObject():
    lun = '23'
    name = 'stelun'
    uid = 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25'
    container = '12'
    size = '8192'
    container_type = 'RaidGroup'
    raid = '5'
    def_owner = 'A'
    return LunInfo (lun, name, uid, container, size, container_type, raid, def_owner)


def getSpDict():
    spdict = {
        'Pool Name': 'test1',
        'Pool ID': '3',
        'Raid Type': '5',
        'User Capacity (GBs)': '1100.022',
        'Available Capacity (GBs)': '926.042',
        'Percent Full':  '49.171',
        'Percent Subscribed':  '49.335'

    }
    return spdict

def getSgDict():

    hbaList = getHbaList()
    hluList = getHluList()

    sgdict = {
        'Shareable': 'YES',
        'HBA SP Pairs': hbaList,
        'HLU ALU Pairs': hluList,
        'Storage Group Name': 'atsfs43_44',
        'Storage Group UID': 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25'
    }
    return sgdict

def getSgDictWithoutLists():

    hbaList = None
    hluList = None

    sgdict = {
        'Shareable': 'YES',
        'HBA SP Pairs': hbaList,
        'HLU ALU Pairs': hluList,
        'Storage Group Name': 'atsfs43_44',
        'Storage Group UID': 'FE:57:91:5E:F4:DF:E3:11:B7:9A:00:60:16:5D:22:25'
    }

    return sgdict

def getHsPolicy():
    pass


class ListHandler(logging.Handler):

    debug = []
    warning = []
    info = []
    error = []

    def emit(self, record):
        getattr(self.__class__,
                record.levelname.lower()).\
                        append(record.getMessage())

    @property
    def all_levels(self):
        return self.debug + self.warning + self.info + self.error

    @classmethod
    def reset(cls):
        for attr in dir(cls):
            if isinstance(getattr(cls, attr), list):
                setattr(cls, attr, [])


def nose_skip_test_if_in_jenkins():
    try:
        os.environ["JENKINS_URL"]
        tskip=True
    except:
        tskip=False
       
    if tskip:
        from nose.plugins.skip import SkipTest
        raise SkipTest


def data_file(filename):
    test_dir = os.path.abspath(os.path.join(os.pardir))
    return os.path.join(test_dir, "data", filename)
