#!/usr/bin/python
import logging
import logging.handlers
from optparse import OptionParser
import os
import sys
import time

import sanapi
from sanapiexception import *
import sanapilib


def checkArgs(argoptions):
    """
    checkArgs checks command line args.

    :param argoptions: The arg options list.
    :type argoptions: :class:`list:`
    """
    if argoptions.version == True:
        print "SAN API Version: " + sanapi.get_api_version()
        exit(0)
    if argoptions.action == None:
        print "Error: an action must be specified"
        exit(1)
    if argoptions.adminuser == None or argoptions.adminpassword == None:
        print "Error: insufficient creds"
        exit(1)
    if argoptions.ip_spa == None or argoptions.ip_spb == None:
        print "Error: array IP(s) not specified"
        exit(1)


def printList(objlist, fail_on_empty=False):
    """
    Prints list of objects.

    :param objlist: The list of objects to print.
    :type objlist: :class:`list`
    :param fail_on_empty: boolean defining whether or not to fail on empty
        list.
    :type: :class:`boolean`
    """
    if len(objlist) == 0:
        print "sanapitest: Empty List !"
        if fail_on_empty:
            exit(1)

    for item in objlist:
        print item
        print '======================================'


def main():
    """
    Main function.
    Retrieves the args passed to the function and performs operations
    accordingly.
    """
    handleCert = True
    vcheck = True
    parser = OptionParser()
    parser.add_option("--action", action="store", dest="action", \
                                                 help="API action to perform")
    parser.add_option("--array_type", action="store", dest="array_type", \
                                   help="API plugin to use to perform action")
    parser.add_option("--rgid", action="store", dest="rgid", \
                                                         help="RAID Group ID")
    parser.add_option("--lunid", action="store", dest="lunid", help="LUN ID")
    parser.add_option("--lunname", action="store", dest="lunname", \
                                                              help="LUN Name")
    parser.add_option("--lunlist", action="store", dest="lunlist", \
                                         help="List of host LUN Ids (HLUs)")
    parser.add_option("--luntype", action="store", dest="luntype", \
                                                              help="LUN Type")
    parser.add_option("--container_type", action="store", \
                             dest="container_type", help="LUN Container Type")
    parser.add_option("--container", action="store", dest="container", \
                                    help="LUN Container i.e rg ID or sp Name")
    parser.add_option("--storage_processor", action="store", \
                           dest="storage_processor", help="Storage Processor")
    parser.add_option("--size", action="store", dest="lunsize", \
                                                              help="LUN Size")
    parser.add_option("--pipecmd", action="store", dest="pipecmd", \
                                         help="Unix command to filter output")
    parser.add_option("--disklist", action="store", dest="disklist", \
                                        help="List of disk in B_E_D Notation")
    parser.add_option("--raid_type", action="store", dest="raid_type", \
                                                             help="RAID Type")
    parser.add_option("--ip_spa", action="store", dest="ip_spa", \
                                               help="SPA IP Address of Array")
    parser.add_option("--ip_spb", action="store", dest="ip_spb", \
                                               help="SPB IP Address of Array")
    parser.add_option("--adminuser", action="store", dest="adminuser", \
                                                        help="Admin username")
    parser.add_option("--sgname", action="store", dest="sgname", \
                                                    help="Storage group name")
    parser.add_option("--hlu", action="store", dest="hlu", \
                                                    help="Host logical unit")
    parser.add_option("--alu", action="store", dest="alu", \
                                                    help="Actual logical unit")
    parser.add_option("--host_name", action="store", dest="host_name", \
                                                             help="Host name")
    parser.add_option("--host_ip", action="store", dest="host_ip",\
                                                             help="Host ip")
    parser.add_option("--wwn", action="store", dest="wwn", \
                                                              help="Host wwn")
    parser.add_option("--sp_port", action="store", dest="sp_port",\
                                                help="Storage processor port")
    parser.add_option("--arraycommpath", action="store", \
                                   dest="arraycommpath", help="arraycommpath")
    parser.add_option("--init_type", action="store", dest="init_type", \
                                                   help="host initiator type")
    parser.add_option("--failovermode", action="store", \
                     dest="failovermode", help="host initiator failover mode")
    parser.add_option("--adminpassword", action="store", \
                                  dest="adminpassword", help="Admin password")
    parser.add_option("--array_specific_options", action="store", \
                         dest="array_specific_options", help="Admin password")
    parser.add_option("--spname", action="store", dest="spname", \
                                                     help="Storage pool name")
    parser.add_option("--spid", action="store", dest="spid", \
                                                       help="Storage pool ID")

    parser.add_option("-v", "--version", action="store_true", dest="version",\
                      default=False, help="Displays SAN API version")

    parser.add_option("--certhandling", action="store", dest="certhandling", \
                                help="enable or disable cert request handling")
    parser.add_option("--versionchecks", action="store", \
        dest="versionchecks", help="enable or disable Flare and "\
         "NaviCLI version checks")

    parser.add_option("--policy", action="store", dest="policy", \
                                                       help="Policy ID")
    parser.add_option("--ratio", action="store", dest="ratio", \
                                                       help="Hot spare ratio")
    parser.add_option("--disk_type", action="store", dest="disk_type", \
                                                       help="Disk Type")
    parser.add_option("--disk_list", action="store", dest="disk_list", \
                      help="List of disks in b_e_d format")
    parser.add_option("--snap_name", action="store", dest="snap_name",
                      help="Snapshot name")
    parser.add_option("--snap_desc", action="store", dest="snap_desc",
                      help="Snapshot description")
    parser.add_option("--deletebackupsnap", action="store",
        dest="delete_backupsnap",
        help="Delete backup snapshot after restoring ('yes' or 'no')")
    parser.add_option("--allow_rw", action="store", dest="allow_rw",
                      help="Allow read write must be 'yes' or 'no'")
    parser.add_option("--keep_for", action="store", dest="keep_for",
                      help="Keep for h d m y. Ex 10d")
    parser.add_option("--fail_on_empty", action="store_true",\
            dest="fail_on_empty", default=False,
            help="If returned list is zero, exit script with status of 1")
    parser.add_option("--expand_pool_lun", action="store_true",\
        dest="expand_pool_lun", default=False,
        help="Expand a specified lun by the passed size")

    (options, args) = parser.parse_args()

    checkArgs(options)
    tstlogger = logging.getLogger("sanapitest")
    tstlogger.setLevel(logging.WARN)
    optargs = dict()

    if options.certhandling and options.certhandling == "disabled":
        handleCert = False

    if options.versionchecks and options.versionchecks == "disabled":
        vcheck = False

    apiObj = sanapi.api_builder(options.array_type, None)
    print "Got object of type %s " % options.array_type

    apiObj.initialise((options.ip_spa, options.ip_spb), options.adminuser,\
                                             options.adminpassword, 'Global', \
                                              handleCert, vcheck)
    print "%s initialised, using primary IP of %s" % (options.array_type,\
                                                       options.ip_spa)
    if options.action == "get_lun_by_id":
        luninfo = apiObj.get_lun(lun_id=options.lunid)
        print luninfo
    elif options.action == "get_lun_by_name" or \
        options.action == "get_pool_lun_by_name":
        luninfo = apiObj.get_lun(lun_name=options.lunname)
        print luninfo
    elif options.action == "get_storage_pool_luns":
        luns = apiObj.get_luns(container_type=sanapilib.CONTAINER_STORAGE_POOL,
                               container=options.spname)
        printList(luns, options.fail_on_empty)
    elif options.action == "get_raid_group_luns":
        luns = apiObj.get_luns(container_type=sanapilib.CONTAINER_RAID_GROUP,
                               container=options.rgid)
        printList(luns, options.fail_on_empty)
    elif options.action == "get_storage_group_luns":
        luns = apiObj.get_luns(sg_name=options.sgname)
        printList(luns, options.fail_on_empty)
    elif options.action == "get_luns":
        luns = apiObj.get_luns()
        printList(luns, options.fail_on_empty)
    elif options.action == "create_lun":
        mand_args = [options.lunname, options.lunsize,\
                      options.container_type, options.container]
        if options.luntype:
            optargs["lun_type"] = options.luntype
        if options.lunid:
            optargs["lun_id"] = options.lunid
        if options.array_specific_options:
            optargs["array_specific_options"] = options.array_specific_options
        if options.raid_type:
            optargs["raid_type"] = options.raid_type
        luninfo = apiObj.create_lun(*mand_args, **optargs)
        print luninfo
    elif options.action == "create_host_initiator":
        mand_args = [options.sgname, options.host_name, options.host_ip, \
                      options.wwn, options.storage_processor, options.sp_port]
        if options.arraycommpath:
            optargs["arraycommpath"] = options.arraycommpath
        if options.init_type:
            optargs["init_type"] = options.init_type
        if options.failovermode:
            optargs["failovermode"] = options.failovermode
        if options.array_specific_options:
            optargs["array_specific_options"] = options.array_specific_options
        hbainfo = apiObj.create_host_initiator(*mand_args, **optargs)
        print hbainfo
    elif options.action == "create_host_initiators":
        mand_args = [options.sgname, options.wwn]
        if options.host_name:
            optargs["host_name"] = options.host_name
        if options.host_ip:
            optargs["host_ip"] = options.host_ip
        if options.arraycommpath:
            optargs["arraycommpath"] = options.arraycommpath
        if options.init_type:
            optargs["init_type"] = options.init_type
        if options.failovermode:
            optargs["failovermode"] = options.failovermode
        if options.array_specific_options:
            optargs["array_specific_options"] = options.array_specific_options
        hbainfo = apiObj.create_host_initiator(*mand_args, **optargs)
        print hbainfo
    elif options.action == "get_storage_pool":
        if options.spname is not None:
            spinfoobj = apiObj.get_storage_pool(sp_name=options.spname)
        elif options.spid is not None:
            spinfoobj = apiObj.get_storage_pool(sp_id=options.spid)
        print spinfoobj
    elif options.action == "get_storage_group":
        sginfoobj = apiObj.get_storage_group(options.sgname)
        print sginfoobj
    elif options.action == "create_storage_group":
        sginfoobj = apiObj.create_storage_group(options.sgname)
        print sginfoobj
    elif options.action == "add_lun_to_storage_group":
        sginfoobj = apiObj.add_lun_to_storage_group(options.sgname, \
                                    options.hlu, options.alu)
        print sginfoobj
    elif options.action == "create_storage_pool":
        spinfoobj = apiObj.create_storage_pool(options.spname,
                                               options.disk_list,
                                               options.raid_type)
        print spinfoobj
    elif options.action == "get_storage_group_luns":
        luns = apiObj.get_luns(sg_name=options.sgname)
        printList(luns, options.fail_on_empty)

    elif options.action == "get_hba_port_info":
        if options.wwn:
            optargs["wwn"] = options.wwn
        if options.host_name:
            optargs["host"] = options.host_name
        if options.host_ip:
            optargs["host"] = options.host_ip
        if options.storage_processor:
            optargs["storage_processor"] = options.storage_processor
        if options.sp_port:
            optargs["spport"] = options.sp_port
        hba_sp_pair_info_list = apiObj.get_hba_port_info(**optargs)
        for hba_sp_pair_info in hba_sp_pair_info_list:
            print hba_sp_pair_info

    elif options.action == "configure_hs" and options.array_type.lower()\
        == "vnx2":
        if options.policy:
            optargs["policy"] = options.policy
        if options.ratio:
            optargs["ratio"] = options.ratio
        hs_policy_info_obj = apiObj.configure_hs(**optargs)
        print hs_policy_info_obj

    elif options.action == "configure_hs" and options.array_type.lower()\
        == "vnx1":
        if options.lunname:
            lun = apiObj.configure_hs(options.rgid, options.lunname)
        else:
            lun = apiObj.configure_hs(options.rgid)
        print lun

    elif options.action == "get_hs_policy" and options.array_type.lower()\
        == "vnx2":
        if options.policy:
            optargs["policy"] = options.policy
        if options.disk_type:
            optargs["disk_type"] = options.disk_type
        hs_policy_info_obj = apiObj.get_hs_policy(**optargs)
        print hs_policy_info_obj

    elif options.action == "get_hs_policy_list" and\
    options.array_type.lower() == "vnx2":
        get_hs_policy_list = apiObj.get_hs_policy_list()
        printList(get_hs_policy_list, options.fail_on_empty)

    elif options.action == "get_san_info":
        mysaninfo = apiObj.get_san_info()
        print mysaninfo.oe_version
        print mysaninfo.san_model

    elif options.action == "_get_host_naviseccli_version":
        _get_host_naviseccli_version = apiObj._get_host_naviseccli_version()
        print _get_host_naviseccli_version

    elif options.action == "_check_flare_version":
        _check_flare_version = apiObj._check_flare_version()
        return _check_flare_version

    elif options.action == "check_host_naviseccli_version":
        check_host_naviseccli_version = apiObj.check_host_naviseccli_version()
        return check_host_naviseccli_version

    elif options.action == "get_hs_luns" and options.array_type.lower()\
        == "vnx1":
        hs_luns = apiObj.get_hs_luns()
        printList(hs_luns, options.fail_on_empty)

    elif options.action == "rename_lun":
        lun = apiObj.rename_lun(options.lunid, options.lunname)
        print lun

    elif options.action == "create_snapshot":
        mand_args = [options.lunname, options.snap_name]
        print apiObj.create_snapshot(*mand_args, **optargs)

    elif options.action == "get_snapshots":
        mand_args = []
        if options.lunname:
            optargs["lun_name"] = options.lunname
        snapshots = apiObj.get_snapshots(*mand_args, **optargs)
        printList(snapshots, options.fail_on_empty)

    elif options.action == "get_snapshot":
        mand_args = [options.snap_name]
        print apiObj.get_snapshot(*mand_args, **optargs)

    elif options.action == "delete_lun":
        if options.array_specific_options:
            optargs["array_specific_options"] = options.array_specific_options
        if options.lunid:
            optargs["lun_id"] = options.lunid
        if options.lunname:
            optargs["lun_name"] = options.lunname
        if apiObj.delete_lun(**optargs):
            print "Deletion of LUN succeeded."

    elif options.action == "restore_snapshot":
        mand_args = [options.lunname, options.snap_name]
        if options.delete_backupsnap:
            optargs["delete_backupsnap"] = \
                (options.delete_backupsnap.lower() != 'no')
        print apiObj.restore_snapshot(*mand_args, **optargs)

    elif options.action == "delete_snapshot":
        mand_args = [options.snap_name]
        print apiObj.delete_snapshot(*mand_args, **optargs)

    elif options.action == "remove_luns_from_storage_group":
        lunlist = options.lunlist.split()
        sgroup = apiObj.remove_luns_from_storage_group(options.sgname, lunlist)
        print "Removal of LUN from Storage Group succeeded."
        print sgroup
    elif options.action == "expand_pool_lun":
        mand_args = [options.lunname, options.lunsize]
        print apiObj.expand_pool_lun(*mand_args)
    else:
        print "Unsupported API action", options.action
        exit(1)

if __name__ == "__main__":
    main()
