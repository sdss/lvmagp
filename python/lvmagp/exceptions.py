# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 12:19:32

from __future__ import absolute_import, division, print_function


class LvmagpError(Exception):
    """A custom core Lvmagp exception"""

    def __init__(self, message=None):

        message = "There has been an error" if not message else message

        super(LvmagpError, self).__init__(message)


class LvmagpNotImplemented(LvmagpError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = "This feature is not implemented yet." if not message else message

        super(LvmagpNotImplemented, self).__init__(message)


class LvmagpAPIError(LvmagpError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = "Error with Http Response from Lvmagp API"
        else:
            message = "Http response error from Lvmagp API. {0}".format(message)

        super(LvmagpAPIError, self).__init__(message)


class LvmagpApiAuthError(LvmagpAPIError):
    """A custom exception for API authentication errors"""

    pass


class LvmagpMissingDependency(LvmagpError):
    """A custom exception for missing dependencies."""

    pass


class LvmagpWarning(Warning):
    """Base warning for Lvmagp."""


class LvmagpUserWarning(UserWarning, LvmagpWarning):
    """The primary warning class."""

    pass


class LvmagpSkippedTestWarning(LvmagpUserWarning):
    """A warning for when a test is skipped."""

    pass


class LvmagpDeprecationWarning(LvmagpUserWarning):
    """A warning for deprecated features."""

    pass


class LvmagpActorMissing(LvmagpError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = (
            "Some of lower actors (lvmtan, lvmpwi, lvmcam) are missing.\
            Check these actors are running."
            if not message
            else message
        )

        super(LvmagpActorMissing, self).__init__(message)


class LvmagpNotExistingHardware(LvmagpError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = (
            "There does not exist hardware has this name." if not message else message
        )

        super(LvmagpNotExistingHardware, self).__init__(message)


class LvmagpFocuserError(LvmagpError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = (
            "Focuser failed. Check the focuser hardware." if not message else message
        )

        super(LvmagpFocuserError, self).__init__(message)


class LvmagpTelescopeError(LvmagpError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = (
            "Telescope(mount) failed. Check the mount hardware."
            if not message
            else message
        )

        super(LvmagpTelescopeError, self).__init__(message)


class LvmagpInterlockEngaged(LvmagpError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = "Interlock is engaged. Unlock the system." if not message else message

        super(LvmagpInterlockEngaged, self).__init__(message)
