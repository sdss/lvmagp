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
