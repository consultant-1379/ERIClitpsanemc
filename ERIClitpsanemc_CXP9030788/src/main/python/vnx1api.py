"""
File name: Vnx1Api.py
Version:   ${project.version}
class that is vnx1 implementation of SanApi
"""
import re

from vnxcommonapi import VnxCommonApi
import sanapilib

HOTSPARE_RAID_TYPE = 'HS'


class Vnx1Api (VnxCommonApi):
    """
    Implementation of SanApi interface for VNX1 Array. As VNX1 & VNX2 are
    similar, most of the functionality is in the VnxCommonApi parent
    class to both
    """

    def configure_hs(self, rg_id, lun_name=None):
        """
        Configure hot spare for VNX1. An existing RAID GROUP must be supplied
        and a LUN will be created using the next available LUN ID. The LUN's
        name will be set if it is supplied.

        """
        self.logger.debug(
          "Entered configurehs with raid group id = %s and name = %s " % \
              (rg_id, lun_name))
        sanapilib.validate_int_and_make_string(rg_id)
        if lun_name is not None:
            sanapilib.validate_string(lun_name)

        # Determine the next valid LUN ID
        lunid = self.get_next_available_lunids()[0]
        self.logger.debug("Using LUN ID of %s" % lunid)

        cmd_string = "bind hs %s -rg %s" % (lunid, rg_id)

        self._navisec(cmd_string)
        self.logger.info(
          "bind hs worked succesfully with LUN ID %s and RG ID %s " \
              % (lunid, rg_id))

        if lun_name is not None:
            # Builds naviseccli command to name LUN created on Raid Group
            cmd_string = "chglun -l " + str(lunid) + " -name " + "\"" +\
            lun_name + "\""
            self.logger.debug("Attempting to set LUN name to %s " % lun_name)
            self._navisec(cmd_string)
            self.logger.info("LUN id %s name set to %s successfully" \
                 % (lunid, lun_name))

        return self.get_lun(lun_id=lunid)

    def get_hs_luns(self):
        """
        Return a list of all hot spare LUNs.

        :returns: List of all hot spot LUNs.
        :rtype: :class:`list`
        """
        self.logger.debug("Entered get_hs_luns")
        all_luns = self.get_luns()

        hsluns = []
        if not all_luns:
            self.logger.debug("No LUNs found")
            return hsluns

        hsluns = [l for l in all_luns if l.raid == HOTSPARE_RAID_TYPE]

        self.logger.debug("Found %s Hot Spare LUNs" % len(hsluns))
        return hsluns
