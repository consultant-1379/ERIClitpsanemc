"""
File name: sanapicfg.py
Version: ${project.version}

Contains general purpose functions used by San API
"""

import os
import ConfigParser

from sanapiexception import (SanApiException, SanApiCriticalErrorException,
SanApiOperationFailedException)
from ConfigParser import NoOptionError, NoSectionError
from pdb import set_trace

class SanApiCfg(object):

    def __init__(self):
        self.config = None

    def load_file(self, cfg_file):
        """
        Loads the config file.

        :param cfg_file: The path to the config file.
        :type cfg_file: :class:`str`
        :raises SanApiCriticalErrorException: Raised if no file found at
            config file path.
        """

        if self.config is not None:
            return

        if not os.path.exists(cfg_file):
            except_msg = "SAN API configuration file not found: %s" % cfg_file
            raise SanApiCriticalErrorException(except_msg, 1)

        self.config = ConfigParser.ConfigParser()
        self.config.read(cfg_file)

    def has_config(self):
        """
        Verifies if config exists.

        :returns: True if config exists, otherwise False.
        :rtype: :class:`boolean`
        """

        return self.config is not None

    def get(self, section, item):
        """
        Gets an item at the specified section.

        :param section: The section of the config.
        :type section: :class:`str`
        :param item: The item being retrieved.
        :type item: :class:`str`
        :returns: The value of the item retrieved.
        :rtype: :class:`str`
        :raises SanApiOperationFailedException: Raised if
            :class:`NoOptionError` or :class:`NoSectionError` caught.
        """

        if not self.has_config():
            raise SanApiCriticalErrorException(
                "Tried to get section: " + section + " item: " + item +
                " from configuration file, but no configuration was found", 1)

        try:
            value = self.config.get(section, item)

        except (NoOptionError, NoSectionError), e:
            # print "Failed to get option %s " % str(e)
            raise SanApiOperationFailedException(str(e), 1)

        return value

    def load_def_file(self):
        """
        Loads the default sanapi.ini file.
        """

        def_file = self.get_cfg_path()
        self.load_file(def_file)

    def get_cfg_path(self):
        """
        Function to return the path to the SANAPI config file
        Reason for search path: packaging puts files in ./etc
        rather than ../etc

        :returns: The full path.
        :rtype: :class:`str`
        :raises SanApiCriticalErrorException: Raised if config file not found.
        """
        cfg_file = 'sanapi.ini'
        cfg_search_path = ('../etc', 'etc')
        sanapi_dir = os.path.dirname(os.path.realpath(__file__))
        for path in cfg_search_path:
            full_path = os.path.normpath(sanapi_dir + "/" + path + "/"
                                        + cfg_file)
            if os.path.isfile(full_path):
                return full_path
        # if we reach here, cfg file has not been found
        raise SanApiCriticalErrorException("API config file not found", 1)

# Currently the only cfg file loaded is the default file.
# If, in the future we want to use a different cfg file we can pass a path
# and if it is not none, use load_file else load_def_file
try:
    SANAPICFG = SanApiCfg()
    SANAPICFG.load_def_file()
except SanApiException, exce:
    raise SanApiCriticalErrorException(str(exce), 1)
except Exception, exce:
    raise SanApiCriticalErrorException(str(exce), 1)
