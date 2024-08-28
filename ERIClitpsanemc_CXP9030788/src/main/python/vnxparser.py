"""
File name: vnxparser.py
Version: ${project.version}

Singleton to provide parsing methods to convert lists, dictionaries, etc
for use in vnxcommon to convert naviseccli etree into usable objects
"""

import sys
import os
import types
import inspect
import subprocess
import time
import re
import xml.etree.ElementTree as ET
import ConfigParser

from sanapi import api_builder, SanApi
from sanapiinfo import  SanApiInfo, LunInfo, StoragePoolInfo, \
                        StorageGroupInfo, HbaInitiatorInfo, HluAluPairInfo,\
                        SnapshotInfo
from sanapiexception import SanApiException, SanApiCommandException, \
                            SanApiConnectionException, \
                            SanApiOperationFailedException, \
                            SanApiCriticalErrorException

from sanapiinfo import HsPolicyInfo
import sanapilib
import socket
import logging


DelimGetLun = "LOGICAL UNIT NUMBER"
DelimLunList = delim = "LOGICAL UNIT NUMBER "


class VnxParser:
    """
    Class to provide parsing methods to convert lists, dictionaries, etc
    for use in vnxcommon to convert naviseccli etree into usable objects.
    """

    def __init__(self, logger=None):
        """
        Sets up logging.

        :param logger: The logger object to use for logging.
        :type logger: :class:`logger`
        """
        self.logger = logger or logging.getLogger(socket.gethostname())

    def create_dict(self, etree):
        """
        Creates a dictionary from element tree representing naviseccli output.

        :param etree: An element tree representing the naviseccli output.
        :type etree: :class:`xml.etree.ElementTree`
        """
        self.logger.debug("Entered create_dict")

        navi_dict = dict()
        try:
            for san_param in etree.findall('.//PARAMVALUE'):
                san_value = san_param.find('VALUE')
                navi_dict[san_param.attrib['NAME']] = san_value.text
        except AttributeError:
            self.logger.debug("Failed to create dictionary from ETree")
            raise SanApiOperationFailedException("Invalid XML stream", 1)

        self.logger.debug("Dictionary constructed from Element Tree okay")

        return navi_dict

    def create_dicts(self, etree, delim):
        """
        Create a dictionary of dictionaries from element tree when the
        naviseccli output consists of multiple items (e.g. all luns).
        Arguments are the element tree and a delimiter to indicate when
        the element tree has reached a new item.

        :param etree: The element tree to create the dictionaries from.
        :type etree: :class:`xml.etree.ElementTree`
        :param delim: The delimeter to indicate when the element tree has
            reached a new item.
        :type delim: :class:`str`
        """
        self.logger.debug("Entered create_dicts")

        meta_dict = dict()
        sub_dict = dict()
        dictkey = None
        try:
            for param in etree.findall('.//PARAMVALUE'):
                if param.attrib['NAME'] == delim:
                    # If sub_dict already exists then we add to meta
                    # with previous sub dict before creating new sub dict
                    if sub_dict is not None and dictkey is not None:
                        meta_dict[dictkey] = sub_dict
                    sub_dict = None

                    # Identifier (delim) will be used as key to put sub_dict
                    # into meta_dict.  But we only put sub_dict into
                    # meta_dict once sub_dict has been fully populated
                    # which is when the next 'delim' is found, above.

                    dictkey = param.find('VALUE').text
                    meta_dict[dictkey] = None
                    sub_dict = dict()
                    sub_dict[param.attrib['NAME']] = dictkey

                else:
                    # sub dict created when delim is matched so now just add
                    # attributes to it
                    sub_dict[param.attrib['NAME']] = param.find('VALUE').text

            # sub dict is added to meta_dict only when delimiter is found. For
            # last entry, delimiter won't be found so need to add it explicitly
            # also test sub_dict has key matching 'delim' if not then this
            # subdict and the metadict is empty so throw exception
            if delim in sub_dict.keys():
                meta_dict[dictkey] = sub_dict
            else:
                errmsg = "Empty dictionary created from etree. \
                Probably this item does not exist on the VNX"
                self.logger.info(errmsg)

        except AttributeError:
            self.logger.debug("Failed to parse Element Tree")
            raise SanApiOperationFailedException("Invalid XML stream", 1)

        self.logger.debug(
                  "Dictionary of dictionaries created from ETree okay")
        return meta_dict

    def create_object_list(self, meta_dict, create_object):
        """
        From a meta dictionary representing multiple SAN 'objects' we create
        instantiate an object for each one, and append it to a list that is
        returned. The meta dictionary is passed as an argument, as is the
        classname determing what class the objects will be instantiated to.

        :param meta_dict: A meta dict representing multiple SAN objects,
        :type meta_dict: :class:`dict`
        :param create_object: The classname to instantiate the objects as.
        :type create_object: :class:`str`
        :returns: The list of objects.
        :rtype: :class:`list`
        :raises SanApiOperationFailedException: Raised if a non function
            passed as a parameter, raised if unable to create the object list.
        """
        self.logger.debug("Entered create_object_list")

        if not isinstance(create_object, types.FunctionType) and \
              not inspect.ismethod(create_object):
            errmsg = "Non-function passed as parameter \
                %s" % type(create_object)
            self.logger.error(errmsg)
            raise SanApiOperationFailedException(errmsg, 1)

        try:
            obj_list = []
            for dictkey in meta_dict:
                sub_dict = meta_dict[dictkey]
                obj = create_object(sub_dict)
                obj_list.append(obj)

        except Exception, exce:
            self.logger.error("Failed to create object list: " + str(exce))
            raise SanApiOperationFailedException(
                         "Failed to create object list: " + str(exce), 1)

        self.logger.debug("create_object_list completed ok")
        return obj_list

    def create_lun_from_get_lun_dict(self, navi_dict):
        """
        Creates a LUN from the dict returned from get_lun.

        :param navi_dict: The dictionary from get_lun.
        :type navi_dict: :class:`dict`
        :returns: The created LUN.
        :rtype: :class:`LunInfo`
        :raises SanApiOperationFailedException: Raised if parameter passed as
            navi_dict not a dict, raised if failed to get lun info from dict.
        """
        self.logger.debug("Entered create_lun_from_get_lun_dict")

        if type(navi_dict) is not dict:
            msg = "Parameter navi_dict is not a dict: %s " % type(navi_dict)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:
            lunid = navi_dict[DelimGetLun]
            name = navi_dict['Name']
            uid = navi_dict['UID']
            container = navi_dict['RAIDGroup ID']
            size = navi_dict['LUN Capacity(Megabytes)']
            raid = navi_dict['RAID Type']
            raid = sanapilib.normalise_raid_group_for_vnx(raid)
            cont = navi_dict['Default Owner']
            controller = sanapilib.normalise_storage_processor(cont)
        except Exception, exce:
            msg = "Failed to get lun info from dictionary " + str(exce)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        if container == 'N/A':
            container_type = sanapilib.CONTAINER_STORAGE_POOL
        else:
            container_type = sanapilib.CONTAINER_RAID_GROUP

        self.logger.debug("Creating %s lun info object: %s (%s) %s" % \
                                     (container_type, lunid, name, uid))

        lun = LunInfo(lunid, name, uid, container, size, container_type,
                                                        raid, controller)
        return lun

    def create_lun_from_lunlist_dict(self, navi_dict):
        """
        Creates a LUN from the dict returned from listlun.

        :param navi_dict: The dictionary from listlun.
        :type navi_dict: :class:`dict`
        :returns: The created LUN.
        :rtype: :class:`LunInfo`
        :raises SanApiOperationFailedException: Raised if parameter passed as
            navi_dict not a dict, raised if failed to get lun info from dict.
        """

        self.logger.debug("Entered create_lun_from_lunlist_dict")

        if type(navi_dict) is not dict:
            msg = "Parameter navi_dict is not a dict: %s " % type(navi_dict)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:

            # DelimLunList = delim = "LOGICAL UNIT NUMBER "

            lunid = navi_dict[DelimLunList]
            name = navi_dict['Name']
            uid = navi_dict['UID']
            container = navi_dict['Pool Name']
            raid = navi_dict['Raid Type']
            raid = sanapilib.normalise_raid_group_for_vnx(raid)
            controller = navi_dict['Default Owner']
            controller = sanapilib.normalise_storage_processor(controller)
            size = navi_dict['User Capacity (GBs)']
            consumed = navi_dict['Consumed Capacity (GBs)']
            current_op = navi_dict['Current Operation']
            current_op_state = navi_dict['Current Operation State']
            current_op_status = navi_dict['Current Operation Status']
            percent_complete = navi_dict['Current Operation Percent Completed']

            # to give in Mbs to be consistent with get_lun
            size = str(int(float(size) * 1024))
            consumed = str(int(float(consumed) * 1024))
        except Exception, exce:
            msg = "Failed to get lun info from dictionary " + str(exce)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        if container == 'N/A':
            container_type = sanapilib.CONTAINER_RAID_GROUP

        else:
            container_type = sanapilib.CONTAINER_STORAGE_POOL

        lun = LunInfo(lunid, name, uid, container, size, container_type, raid,
                      controller, current_op, current_op_state,
                      current_op_status, percent_complete, consumed)
        return lun

    def create_spinfo_from_dict(self, navi_dict):
        """
        Dictionary is from storagepool -list

        Creates a StoragePoolInfo object from the dict returned from
        storagepool -list

        :param navi_dict: The dict returned from storagepool -list
        :type navi_dict: :class:`dict`
        :returns: The new storage pool.
        :rtype: :class:`StoragePoolInfo`
        :raises SanApiOperationFailedException: Raised if parameter passed as
            navi_dict not a dict, raised if failed to get storage pool info
            from dict.
        """
        self.logger.debug("Entered create_spinfo_from_dict")

        if type(navi_dict) is not dict:
            msg = "Parameter navi_dict is not a dict: %s " % type(navi_dict)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:
            name = navi_dict['Pool Name']
            dictkey = navi_dict['Pool ID']
            raid = navi_dict['Raid Type']
            raid = sanapilib.normalise_raid_group_for_vnx(raid)
            size = navi_dict['User Capacity (GBs)']
            # to give in Mbs to be consistent with get_lun
            size = str(int(float(size) * 1024))
            available = navi_dict['Available Capacity (GBs)']
            # to give in Mbs to be consistent with get_lun
            available = str(int(float(available) * 1024))
            full = navi_dict['Percent Full']
            subscribed = navi_dict['Percent Subscribed']

        except Exception, exce:
            msg = "Failed to get storage pool info from dictionary " +\
             str(exce)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        self.logger.debug("Creating StoragePoolInfo object %s" % name)

        newsp = StoragePoolInfo(name, dictkey, raid, size, available,
                                full, subscribed)

        return newsp

    def create_sg_list(self, sgtree):
        """
        From Etree, create and return a list of StorageGroupInfo objects.

        :param sgtree: The ETree describinf the StorageGroupInfo objects.
        :type sgtree: :class:`xml.etree.ElementTree`
        :returns: A list of StorageGroupInfo objects.
        :rtype: :class:`StorageGroupInfo`
        :raises SanApiOperationFailedException: Raised if sgtree not an
            element tree.
        """
        self.logger.debug("Entered create_sg_list")

        paramclass = sgtree.__class__.__name__
        if paramclass != "ElementTree" and paramclass \
                != "_ElementInterface" and paramclass != "Element":

            msg = "Parameter sgtree is not an Element Tree: %s " % paramclass
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        hbaspentry = \
        "  HBA UID                                          SP Name     SPPort"
        hlualuentry = "  HLU Number     ALU Number"
        hbasplist = []
        hlualulist = []
        sgdict = dict()
        sglist = []

        for param in sgtree.findall('.//PARAMVALUE'):
            key = param.attrib['NAME']
            val = param.find('VALUE').text
            self.logger.debug("Dealing with key %s and value %s" %
                                 (key, val))

            if key == "Storage Group Name":
                self.logger.debug("New storage group found in tree: %s "
                                     % val)

                # If we have dict from previous iteration then create object
                # and put onto list
                if sgdict:
                    self.logger.debug("Previous storage group will be " +
                                         "appended to list")
                    sgnew = self.create_sginfo_from_dict(sgdict)
                    sglist.append(sgnew)
                    sgdict = dict()

                sgdict[key] = val

            elif key == hbaspentry:
                key = 'HBA SP Pairs'
                hbasplist = val.split()
                hbauid = hbasplist[0]
                spname = hbasplist[2]
                spport = hbasplist[3]

                hbasp = HbaInitiatorInfo(hbauid, spname, spport)
                sgdict.setdefault(key, []).append(hbasp)

            elif key == hlualuentry:
                key = 'HLU ALU Pairs'
                hlualulist = val.split()
                hlu = hlualulist[0]
                alu = hlualulist[1]

                hlualu = HluAluPairInfo(hlu, alu)
                sgdict.setdefault(key, []).append(hlualu)

            elif key == "Shareable" or key == "Storage Group UID":
                sgdict[key] = val

        if sgdict:
            self.logger.debug("Final storage group will be appended " +
                                 "to list")
            sgnew = self.create_sginfo_from_dict(sgdict)
            sglist.append(sgnew)

        return sglist

    def create_sginfo_from_dict(self, sgdict):
        """
        Extract known keys from sgdict and use these as parameters
        to call StorageGroupInfo constructor and return the object.

        :param sgdict: A dict containing keys relating to storage groups.
        :type sgdict: :class:`dict`
        :returns: StorageGroupInfo object from the keys.
        :rtype: :class:`StorageGroupInfo`
        :raises SanApiOperationFailedException: Raised if a storage group key
            (Name, UID or Shareable) not found.
        """

        self.logger.debug("Entered create_sginfo_from_dict")

        if type(sgdict) is not dict:
            msg = "Parameter sgdict is not a dict: %s " % type(sgdict)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:
            name = sgdict['Storage Group Name']
        except KeyError:
            msg = "Error creating StorageGroupInfo Object 'Name' Key not found"
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:
            uid = sgdict['Storage Group UID']
        except KeyError:
            msg = "Error creating StorageGroupInfo Object 'UID' Key not found"
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:
            if sgdict['Shareable'] == 'YES':
                shareable = True
            else:
                shareable = False
        except KeyError:
            msg = "Error creating StorageGroupInfo Object 'Shareable' Key " + \
                   "not found"

            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:
            hbasp = sgdict['HBA SP Pairs']
        except KeyError:
            hbasp = None

        try:
            hlualu = sgdict['HLU ALU Pairs']
        except KeyError:
            hlualu = None

        self.logger.debug("Calling StorageGroupInfo constructor: " + \
                               "%s, %s, %s, %s, %s" %
                              (name, uid, shareable, hbasp, hlualu))

        sgnew = StorageGroupInfo(name, uid, shareable, hbasp, hlualu)
        return sgnew

    def create_policy_dicts(self, etree):
        """
        Creates a dict of dicts.

        :param etree: An element tree to create the dicts from.
        :type etree: :class:`xml.etree.ElementTree`
        :returns: The dict of dicts from the element tree.
        :rtype: :class:`dict`
        :raises SanApiOperationFailedException: Raised if the element tree
            could not be parsed.
        """
        self.logger.debug("Entered create_policy_dicts")
        policy_dict = {}
        sub_dict = None
        policy_id = None

        try:
            for param in etree.findall('.//PARAMVALUE'):
                if param.attrib['NAME'] == "CLASSIC CLI":
                    policy_data = param.find('VALUE').text

                '''
                    Takes the XML output, parses it and
                    retrieves the output associated with each policy id
                '''
                result = re.findall(r'(^Policy ID:).*(Recommended:)',
                                     policy_data)

                for each_line in policy_data.split('\n'):
                    if re.search("(^Policy).*ID:.*(\Z)", each_line)\
                                     is not None:
                        if sub_dict:
                            policy_dict[policy_id] = sub_dict
                        result = re.search("(^Policy).*ID:.*(.)", each_line)
                        # Strip removes the white spaces either side
                        policy_id = result.group(2).strip()
                        sub_dict = dict()
                        sub_dict['Policy Id:'] = policy_id

                    if re.search("(^Disk).*Type:.*(\Z)", each_line)\
                                 is not None:
                        result = re.search("(^Disk).*Type:(.*)", each_line)
                        disk_type = result.group(2).strip()
                        sub_dict['Disk Type:'] = disk_type

                    if re.search("(^Ratio of Keep).*Unused:.*(\Z)",
                                  each_line) is not None:
                        result = re.search("(^Ratio of Keep).*Unused:(.*)",
                                            each_line)
                        r_o_k_u = result.group(2).strip()
                        sub_dict['Ratio To Keep Unused:'] = r_o_k_u

                    if re.search("(^Number to Keep).*Unused:.*(\Z)",
                                  each_line) is not None:
                        result = re.search("(^Number to Keep).*Unused:(.*)",
                                            each_line)
                        n_t_k_u = result.group(2).strip()
                        sub_dict['Number to Keep Unused:'] = n_t_k_u

                if sub_dict:
                        policy_dict[policy_id] = sub_dict
                        self.logger.debug("Create Policy Dicts Completed Ok")
                        return policy_dict

        except AttributeError:
            self.logger.error("Failed to parse Element Tree")
            raise SanApiOperationFailedException("Invalid XML stream", 1)

    def create_HsPolicyInfo_object(self, policy_dictionary):
        """
        Takes a dictionary containing hot spare policy information
        and parses the information to create a HsPolicyInfo object.

        :param policy_dictionary: A dictionary containing hot spare policy
            information.
        :type policy_dictionary: :class:`dict`
        :returns: A HsPolicyInfo object.
        :rtype: :class:`HsPolicyInfo`
        :raises SanApiOperationFailedException: Raised if unable to get hot
            spare info from the dictionary.
        """
        try:
            return HsPolicyInfo(policy_dictionary['Policy Id:'],
                                policy_dictionary["Disk Type:"],
                                policy_dictionary["Ratio To Keep Unused:"],
                                policy_dictionary["Number to Keep Unused:"])

        except KeyError, exce:
            msg = "Failed to get hot spare info from dictionary " + str(exce)
            raise SanApiOperationFailedException(msg, 1)

    def get_sub_etree_list(self, etree, delimiter):
        """
        Takes an etree and a delimiter and splits the etree on the delimiter
        to return a list of sub-etrees.

        :param etree: The element tree.
        :type etree: :class:`xml.etree.ElementTree`
        :param delimiter: The delimiter.
        :type delimiter: :class:`str`
        :returns: List of sub-etrees.
        :rtype: :class:`list`
        :raises SanApiOperationFailedException: Raised if unable to parse the
            element tree.
        """
        sub_etree_list = []
        count = 0
        first_delim_match = False
        sub_root = ET.Element("sub_root0")
        try:

            for param in etree.findall('.//PARAMVALUE'):
                # skip all the cruft before we find the first matching delim
                if param.attrib['NAME'] != delimiter and not first_delim_match:
                    continue
                if param.attrib['NAME'] == delimiter:
                    first_delim_match = True
                    if len(sub_root.getchildren()) > 0:
                        sub_tree = ET.ElementTree(sub_root)
                        sub_etree_list.append(sub_tree)
                        count = count + 1
                        # create a new root object
                        sub_root = ET.Element("sub_root" + str(count))

                sub_root.append(param)

            if len(sub_root.getchildren()) > 0:
                sub_tree = ET.ElementTree(sub_root)
                sub_etree_list.append(sub_tree)

            return sub_etree_list

        except AttributeError, ex:
            self.logger.error("Failed to parse Element Tree")
            raise SanApiOperationFailedException("Invalid XML stream", 1)

    def create_hba_init_info_list(self, etree):
        """
        Takes an etree containing hba port list into and returns a list of
        HbaInitiatorInfo.

        :param etree: The element tree.
        :type etree: :class:`xml.etree.ElementTree`
        :returns: A list of HbaInitiatorInfo objects.
        :rtype: :class:`list` of :class:`HbaInitiatorInfo` objects.
        :raises SanApiOperationFailedException: Raised if unable recognise
            storage processor name, raised if invalid storage processor port,
            raised if failed to get hba port info from dictionary, raised if
            invalid WWN.
        """

        hba_sub_etrees = self.get_sub_etree_list(etree, "HBA UID")
        hba_init_info_list = []

        for hba_sub_etree in hba_sub_etrees:
            try:
                hba_dict = self.create_dict(hba_sub_etree)
                hbauid = hba_dict['HBA UID']
                if not sanapilib.is_valid_wwn(hbauid):
                    errmsg = "Invalid WWN ", hbauid
                    self.logger.error(errmsg)
                    raise SanApiOperationFailedException(errmsg, 1)
                server_name = hba_dict['Server Name']
                server_ip = hba_dict['Server IP Address']
            except Exception, exce:
                msg = "Failed to get hba info from dictionary " + str(exce)
                self.logger.error(msg)
                raise SanApiOperationFailedException(msg, 1)

            hba_port_sub_etrees = self.get_sub_etree_list(hba_sub_etree, \
                                                          "    SP Name")
            for hba_port_sub_etree in hba_port_sub_etrees:
                try:
                    hba_port_dict = self.create_dict(hba_port_sub_etree)
                    spname = hba_port_dict['    SP Name']
                    if spname == "SP A":
                        spname = sanapilib.STORAGE_PROCESSOR_A
                    elif spname == "SP B":
                        spname = sanapilib.STORAGE_PROCESSOR_B
                    else:
                        errmsg = "Unrecognised storage processor name", spname
                        self.logger.error(errmsg)
                        raise SanApiOperationFailedException(errmsg, 1)
                    spport = hba_port_dict['    SP Port ID']
                    if not sanapilib.is_valid_sp_port(spport):
                        errmsg = "Invalid storage processor port", spport
                        self.logger.error(errmsg)
                        raise SanApiOperationFailedException(errmsg, 1)
                    # print "hba", hbauid, "sp", spname, "port", spport, \
                    #     "server_name", server_name, "server ip", server_ip
                    hba_init_info_list.append(HbaInitiatorInfo(
                                                hbauid, spname,
                                                spport, server_name,
                                                server_ip))
                except Exception, exce:
                    msg = "Failed to get hba port info from dictionary " \
                                                 + str(exce)
                    self.logger.error(msg)
                    raise SanApiOperationFailedException(msg, 1)

        return hba_init_info_list

    def create_snap_from_get_snapshot_dict(self, navi_dict):
        """
        Dictionary is from _get_snapshots

        :param navi_dict: The dict retrieved from _get_snapshots.
        :type navi_dict: :class:`dict`
        :returns: A snapshot info object.
        :rtype: :class:`SnapshotInfo`
        :raises SanApiOperationFailedException: Raised if navi_dict not a
            dict, raised if failed to get snapshot info from dictionary.
        """
        self.logger.debug("Entered create_snap_from_get_snapshot_dict")

        if type(navi_dict) is not dict:
            msg = "Parameter navi_dict is not a dict: %s " % type(navi_dict)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        try:
            resource_lun_id = navi_dict["Source LUN(s)"]
            snapshot_name = navi_dict["Name"]
            created_time = navi_dict["Creation time"]
            snap_state = navi_dict["State"]
            resource_lun_name = navi_dict["Lun name"]
            description = navi_dict["Description"]

        except Exception, exce:
            msg = "Failed to get snapshot info from dictionary " + str(exce)
            self.logger.error(msg)
            raise SanApiOperationFailedException(msg, 1)

        self.logger.debug(("Creating snapshot info object: " +\
                        "lun_id=%s, snapshot name=%s, created time=%s, " +\
                        "snapshot state=%s, lun_name=%s") % \
                             (resource_lun_id, snapshot_name, created_time,
                              snap_state, resource_lun_name))

        snapshot = SnapshotInfo(resource_lun_id=resource_lun_id,
                                snapshot_name=snapshot_name,
                                created_time=created_time,
                                snap_state=snap_state,
                                resource_lun_name=resource_lun_name,
                                description=description)

        return snapshot
