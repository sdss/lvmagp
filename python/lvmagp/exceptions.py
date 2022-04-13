# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 12:19:32


class LvmagpError(Exception):
    """A custom core Lvmagp exception"""

class LvmagpNotImplemented(LvmagpError):
    """A custom exception for not yet implemented features."""

class LvmagpAPIError(LvmagpError):
    """A custom exception for API errors"""


class LvmagpApiAuthError(LvmagpAPIError):
    """A custom exception for API authentication errors"""


class LvmagpMissingDependency(LvmagpError):
    """A custom exception for missing dependencies."""


class LvmagpWarning(Warning):
    """Base warning for Lvmagp."""


class LvmagpUserWarning(UserWarning, LvmagpWarning):
    """The primary warning class."""


class LvmagpSkippedTestWarning(LvmagpUserWarning):
    """A warning for when a test is skipped."""


class LvmagpDeprecationWarning(LvmagpUserWarning):
    """A warning for deprecated features."""


class LvmagpActorMissing(LvmagpError):
    """Some of lower actors (lvmtan, lvmpwi, lvmcam) are missing.\
    Check these actors are running."""


class LvmagpNotExistingHardware(LvmagpError):
    """There does not exist hardware which has this name."""


class LvmagpFocuserError(LvmagpError):
    """Focuser failed. Check the focuser hardware."""


class LvmagpIsNotIdle(LvmagpError):
    """Focusing not allowed while guiding."""


class LvmagpTelescopeError(LvmagpError):
    """Telescope(mount) failed. Check the mount hardware."""


class LvmagpInterlockEngaged(LvmagpError):
    """Interlock is engaged. Unlock the system."""


class LvmagpTargetOverTheLimit(LvmagpError):
    """Target is over the limit. Check the coordinates or set another target."""


class LvmagpAcquisitionFailed(LvmagpError):
    """A custom exception for not yet implemented features."""
