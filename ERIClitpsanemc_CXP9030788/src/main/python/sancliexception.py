"""
File name: sancliexception.py
Version: ${project.version}
SAN CLI Exceptions
"""

import sys


class SanCliException(Exception):
    """
    SANCLI Exception base class.  Constructor takes a descriptive message and a
    return code (typically used for error / return info from naviseccli
    command)
    """

    def __init__(self, message, ReturnCode):
        """
        Constructor.
        """
        Exception.__init__(self, message)
        self.ReturnCode = ReturnCode


class SanCliCommandException(SanCliException):
    """
    SANCLI Command Exception for naviseccli (or equivalent) command failures,
    e.g. when creating a lun which already exists.
    """

    pass


class SanCliConnectionException(SanCliException):
    """
    SANCLI Connection Exception for naviseccli (or equivalent) connection
    failures, such as incorrect login credentials, IP information, or
    network issues
    """

    pass


class SanCliOperationFailedException(SanCliException):
    """
    SANCLI Operation Failed Exception - for SAN CLI internal use, if
    non-critical failure occurs, this will be thrown, and caught and
    dealt with appropriately.
    """

    pass


class SanCliCriticalErrorException(SanCliException):
    """
    SANCLI Critical error which should be handled by the program using
    the SAN CLI
    """

    pass


class SanCliEntityAlreadyExistsException(SanCliException):
    """
    This exception gets thrown by SANCLI when it detects
    that an object with same id/name already exists on the
    array as the object we are trying to create
    """
    pass


class SanCliEntityNotFoundException(SanCliException):
    """
    This exception gets thrown by SANCLI when an entity
    e.g LUN, storage pool etc cannot be found on the
    array.
    """
    pass
