"""
File name: Vnx2Api.py
Version:   ${project.version}
class that is vnx2 implementation of SanApi
"""

from vnxcommonapi import VnxCommonApi
from sanapiinfo import HsPolicyInfo
from vnxparser import VnxParser
from sanapilib import is_valid_policyid, is_valid_policy_ratio,\
validate_int_and_make_string
from sanapiexception import SanApiCriticalErrorException
from string import Template

HOTSPARE_POLICY_CMD = Template("hotsparepolicy -set -o $policy -keep1unusedper"
        " $ratio")
HOTSPARE_LIST_CMD = "hotsparepolicy -list"


class Vnx2Api (VnxCommonApi):
    """
    Implementation of SanApi interface for VNX1 Array.  As VNX1 & VNX2 are
    similar, most of the functionality is in the VnxCommonApi parent class
    to both
    """

    def configure_hs(self, policy, ratio):
        """
        Configures the hot spare policy with the given ID to use the given
            ratio.

        :param policy: The policy ID.
        :type policy: :class:`str`
        :param ratio: The ratio of the number of disks to be used for each
            hot spare.
        :rtype ratio: :class:`str`
        :returns: A hot spare policy info object..
        :rtype: :class:`HotSparePolicyInfo`
        """
        self.logger.debug("Entering configure_hs(%s,%s)" % (policy, ratio))

        # Initial checks to make sure mandatory parameters were given
        # TODO: These commmented out checks are not necessary, remove
        # if policy is None:
        #    msg = "No policy id has been specified %s. " % policy
        #    self.logger.error(msg)
        #    raise SanApiCriticalErrorException(msg, 1)

        # if ratio is None:
        #    msg = "No ratio has been specified %s. " % ratio
        #    self.logger.error(msg)
        #    raise SanApiCriticalErrorException(msg, 1)

        # Check that the policy id and ratio are valid
        if not is_valid_policyid(policy):
            msg = "Invalid policy ID " +\
                "%s. Policy ID must be an integer > 0" % policy
            self.logger.error(msg)
            raise SanApiCriticalErrorException(msg, 1)

        if not is_valid_policy_ratio(ratio):
            msg = "Invalid ratio %s. Ratio must be an integer >= 0 " % ratio
            self.logger.error(msg)
            raise SanApiCriticalErrorException(msg, 1)

        # Configure the hotspare policy using the ratio specified

        cmd_string = HOTSPARE_POLICY_CMD.substitute(policy=policy,
                ratio=ratio)

        self._navisec(cmd_string)
        self.logger.info("configure_hs completed successfully")
        return self.get_hs_policy(policy)

    def get_hs_policy(self, policy=None, disk_type=None):
        """
        Gets the hot spare policy info object for a given policy ID or disk
            type.

        :param policy: The policy ID.
        :type policy: :class:`str`
        :param disk_type: The disk type.
        :type disk_type: :class:`str`
        :returns: A hot spare policy info object associated with that policy
            id/disk type.
        :rtype: :class:`HotSparePolicyInfo`
        """
        self.logger.debug("Entering get_hs_policy()")
        # If no policy id or disk_type is supplied throw an exception
        if (policy is None and disk_type is None):
            msg = "Please supply either a policy id or disk_type!"
            self.logger.error(msg)
            raise SanApiCriticalErrorException(msg, 1)
        # If both policy id and disk_type is supplied throw an exception
        if (policy and disk_type) is not None:
            msg = "You can only supply one parameter either policy id \
            or disk type!"
            self.logger.error(msg)
            raise SanApiCriticalErrorException(msg, 1)

        # Run the hotspare list command and parse the
        # element tree into a dictionary
        parser = VnxParser()
        cmd_string = HOTSPARE_LIST_CMD
        etree = self._navisec(cmd_string)
        dict_list = parser.create_policy_dicts(etree)
        policy_found = False

        # If disk type is supplied than the policy to the one
        # associated with that disk type.
        # If disk type cant be found an unknown disk type exception occurs
        if disk_type:
            for policy_dict in dict_list:
                key = 'Disk Type:'
                policy_id = 'Policy Id:'
                if dict_list[policy_dict][key] == disk_type:
                    policy = dict_list[policy_dict][policy_id]
                    policy_found = True
                    break

            if policy_found is False:
                msg = "Unknown disk type %s." % disk_type
                self.logger.error(msg)
                raise SanApiCriticalErrorException(msg, 1)

        # If no disk type was supplied than the policy id is validated
        # Exception thrown if invalid policy Id
        elif policy:
            if not is_valid_policyid(int(policy)):
                msg = "Invalid policy ID %s. Policy ID " % policy
                msg += "must be an integer > 0 "
                self.logger.error(msg)
                raise SanApiCriticalErrorException(msg, 1)

        # Construct the dictionary from the element tree
        try:
                policy_dictionary = dict_list[str(policy)]
                self.logger.info(
                         "Dictionary constructed from Element Tree okay")
        except KeyError:
            self.logger.debug("Failed to find that Policy ID")
            raise SanApiCriticalErrorException("Unknown Policy ID %s. \
                                                " % policy, 1)
        self.logger.debug("get_hs_policy completed successfully")

        # Return the policy info as an object
        return parser.create_HsPolicyInfo_object(policy_dictionary)

    def get_hs_policy_list(self):
        """
        Gets the list of hot spare policy info objects.

        :returns: List of hot spare policy info objects.
        :rtype: :class:`list` of :class:`HotSparePolicyInfo`
        """
        self.logger.debug("Entering get_hs_policy_list()")

        parser = VnxParser()
        cmd_string = HOTSPARE_LIST_CMD
        etree = self._navisec(cmd_string)
        dict_list = parser.create_policy_dicts(etree)

        self.logger.debug(
              "Dictionaries parsed, now passing to create_object_list()")

        # Pass the meta dictionary dict_list  into the function below which
        # return a list of objects associated with the function supplied as
        # the argument

        return parser.create_object_list(dict_list,
                                         parser.create_HsPolicyInfo_object)
