"""
File name: sanapiexception.py
Version: ${project.version}
SAN API Exceptions
"""

import sys


class SanApiException(Exception):
    """
    SANAPI Exception base class.  Constructor takes a descriptive message and a
    return code (typically used for error / return info from naviseccli
    command).

    :ivar Exception: An Exception.
    :vartype Exception: :class:`Exception`
    """

    def __init__(self, message, ReturnCode):
        """
        Constructor.
        """
        Exception.__init__(self, message)
        self.ReturnCode = ReturnCode


class SanApiCommandException(SanApiException):
    """
    SANAPI Command Exception for naviseccli (or equivalent) command failures,
    e.g. when creating a lun which already exists.

    :ivar SanApiException: The SAN API Exception object.
    :vartype SanApiException: :class:`Exception`
    """

    pass


class SanApiConnectionException(SanApiException):
    """
    SANAPI Connection Exception for naviseccli (or equivalent) connection
    failures, such as incorrect login credentials, IP information, or
    network issues.

    :ivar SanApiException: The SAN API Exception object.
    :vartype SanApiException: :class:`Exception`
    """

    pass


class SanApiOperationFailedException(SanApiException):
    """
    SANAPI Operation Failed Exception - for SAN API internal use, if
    non-critical failure occurs, this will be thrown, and caught and
    dealt with appropriately.

    :ivar SanApiException: The SAN API Exception object.
    :vartype SanApiException: :class:`Exception`
    """

    pass


class SanApiCriticalErrorException(SanApiException):
    """
    SANAPI Critical error which should be handled by the program using
    the SAN API.

    :ivar SanApiException: The SAN API Exception object.
    :vartype SanApiException: :class:`Exception`
    """

    pass


class SanApiEntityAlreadyExistsException(SanApiException):
    """
    This exception gets thrown by SANAPI when it detects
    that an object with same id/name already exists on the
    array as the object we are trying to create.

    :ivar SanApiException: The SAN API Exception object.
    :vartype SanApiException: :class:`Exception`
    """
    pass


class SanApiEntityNotFoundException(SanApiException):
    """
    This exception gets thrown by SANAPI when an entity
    e.g LUN, storage pool etc cannot be found on the
    array.

    :ivar SanApiException: The SAN API Exception object.
    :vartype SanApiException: :class:`Exception`
    """
    pass

class SanApiMissingInformationException(SanApiException):
    """
    This exception gets thrown by SANAPI when an entity
    e.g LUN, storage pool etc has missing information that
    is required to finish an operation.

    :ivar SanApiException: The SAN API Exception object.
    :vartype SanApiException: :class:`Exception`
    """
    pass
